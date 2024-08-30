import argparse
import pathlib
import tempfile
import time
import webbrowser
import zipfile
from pprint import pprint

import webview

import constants
from epub_parser import EpubParser


def main():
    """
    Extracts an EPUB file and prints its container properties.

    Renders the EPUB on a system WebView instance.
    """
    start_time = time.time()
    parser = argparse.ArgumentParser(description="Extract EPUB file")
    parser.add_argument("EpubParser", help="Path to the EPUB file")
    args = parser.parse_args()
    epub_filepath = pathlib.Path(args.EpubParser)
    epub_parser = EpubParser()
    if not epub_parser.is_valid_container(epub_filepath):
        print("Invalid EPUB container")
        return
    print("EPUB archive seems valid")
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = pathlib.Path(temp_dir)
        print(f"Extract to {output_dir}")
        try:
            with zipfile.ZipFile(epub_filepath, "r") as zip_ref:
                zip_ref.extractall(output_dir)
        except zipfile.BadZipFile as e:
            print(f"Error extracting ZIP file: {e}")
            return
        print(f"Parse {constants.CONTAINER_PATH}")
        try:
            container_props = epub_parser.get_container_props(
                output_dir.joinpath(constants.CONTAINER_PATH)
            )
        except ValueError as e:
            print(e)
            return
        print(f"Parse {container_props['full-path']}")
        try:
            content_props = epub_parser.get_content_props(
                output_dir.joinpath(container_props["full-path"])
            )
            pprint(content_props["table_of_contents"])
            path = pathlib.Path(container_props["full-path"])
        except ValueError as e:
            print(e)
            return
        end_time = time.time()
        print(f"Parsed in {end_time - start_time:.3f} seconds")
        toc_headers = list(content_props["table_of_contents"].keys())
        root_path = path.parts[0] if len(path.parts) > 1 else path.parent
        file_path = output_dir.joinpath(
            root_path, content_props["table_of_contents"][toc_headers[0]]
        )
        file_path = f"file://{file_path}"
        print(f"Render {file_path}")
        js_file_path = pathlib.Path("script/user.js")

        def inject_js(window):
            try:
                with open(js_file_path, "r") as js_file:
                    js_src = js_file.read()
            except FileNotFoundError:
                print(f"JavaScript file not found: {js_file_path}")
                return
            window.evaluate_js(js_src)

        class WebviewAPI:
            def __init__(self) -> None:
                self.curr_idx = 0

            def keypress(self, key):
                try:
                    if key == "ArrowRight":
                        if self.curr_idx < len(toc_headers) - 1:
                            self.curr_idx += 1
                    elif key == "ArrowLeft":
                        if self.curr_idx > 0:
                            self.curr_idx -= 1
                    file_path = output_dir.joinpath(
                        root_path,
                        content_props["table_of_contents"][toc_headers[self.curr_idx]],
                    )
                    file_path = f"file://{file_path}"
                    print(f"Render {file_path}")
                    window.load_url(file_path)
                except Exception as e:
                    print(f"Error handling keypress: {e}")

            def open_external_link(self, url):
                webbrowser.open(url)

        window = webview.create_window(
            f'{content_props["metadata"]["title"][0]}'
            f' - {content_props["metadata"]["creator"][0]}',
            file_path,
            width=750,
            height=900,
            min_size=(800, 600),
            zoomable=True,
            text_select=True,
            js_api=WebviewAPI(),
        )
        window.events.loaded += lambda: inject_js(window)
        webview.start(private_mode=False)


if __name__ == "__main__":
    main()
