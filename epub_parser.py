import pathlib
import zipfile
from collections import OrderedDict
from typing import Any, Dict

import constants
from lxml import etree


class EpubParser:
    def is_valid_container(self, path: pathlib.Path) -> bool:
        """Checks if the given file is a valid EPUB container."""
        if (
            not path.exists()
            or path.suffix != ".epub"
            or path.stat().st_size == 0
            or not zipfile.is_zipfile(path)
        ):
            return False
        try:
            with zipfile.ZipFile(path, "r") as zip_ref:
                namelist = zip_ref.namelist()
                return (
                    "mimetype" in namelist
                    and zip_ref.read("mimetype").decode() == "application/epub+zip"
                    and constants.CONTAINER_PATH in namelist
                )
        except zipfile.BadZipFile as e:
            print(f"Invalid archive: {e}")
            return False

    def get_container_props(self, path: pathlib.Path) -> dict:
        """
        Extracts properties from the container.xml file in an EPUB container.

        Args:
            path: The path to container.xml.

        Returns:
            dict: A dictionary containing `full-path` and `media-type` of content.opf.
        """
        tree = etree.parse(path, None)
        root = tree.getroot()
        rootfiles = root.find("rootfiles", namespaces=root.nsmap)
        if rootfiles is None:
            raise ValueError("rootfiles element not found")
        rootfile = rootfiles.find("rootfile", namespaces=rootfiles.nsmap)
        if rootfile is None:
            raise ValueError("rootfile element not found")
        props = {}
        props["full-path"] = rootfile.get("full-path")
        props["media-type"] = rootfile.get("media-type")
        if props["full-path"] is None or props["media-type"] is None:
            raise ValueError("attribute(s) missing")
        if props["media-type"] != "application/oebps-package+xml":
            raise ValueError("media-type is unsupported")
        return props

    def get_content_props(self, path: pathlib.Path) -> Dict[str, Any]:
        """
        Extracts properties from the content.opf/package.opf file in an EPUB container.

        Args:
            path: The path to content.opf/package.opf.

        Returns:
            dict: A dictionary containing Dublin Core metadata, TOC, and cover image location.
        """
        tree = etree.parse(path, None)
        root = tree.getroot()
        metadata = root.find("metadata", namespaces=root.nsmap)
        if metadata is None:
            raise ValueError("No metadata available")
        spine = root.find("spine", namespaces=root.nsmap)
        if spine is None:
            raise ValueError("No spine available")
        manifest = root.find("manifest", namespaces=root.nsmap)
        if manifest is None:
            raise ValueError("No manifest available")
        props = {
            "metadata": {
                key: ["Unknown"]
                for key in [
                    "title",
                    "subject",
                    "creator",
                    "contributor",
                    "publisher",
                    "description",
                    "source",
                    "date",
                    "identifier",
                    "language",
                    "rights",
                    "type",
                    "format",
                    "relation",
                    "coverage",
                ]
            },
            "table_of_contents": OrderedDict(),
            "cover_image": "",
        }
        for key in props["metadata"]:
            elements = metadata.findall(f"dc:{key}", namespaces=metadata.nsmap)
            if len(elements) > 0:
                props["metadata"][key] = [
                    elem.text.strip() for elem in elements if elem.text
                ]
        idref_set = set()
        itemrefs = spine.findall("itemref", namespaces=spine.nsmap)
        for itemref in itemrefs:
            idref_set.add(itemref.get("idref"))
        ncx_path = ""
        hrefs_set = set()
        items = manifest.findall("item", namespaces=manifest.nsmap)
        for item in items:
            if item.get("id") in idref_set:
                hrefs_set.add(item.get("href"))
            elif item.get("properties") == "cover-image":
                props["cover_image"] = item.get("href")
            elif (item.get("id") == "ncx" or item.get("id") == "ncx2") and item.get(
                "media-type"
            ) == "application/x-dtbncx+xml":
                ncx_path = item.get("href")
            else:
                pass
        ncx_path = path.parent.joinpath(ncx_path)
        ncx_tree = etree.parse(ncx_path, None)
        ncx_root = ncx_tree.getroot()
        navmap = ncx_root.find("navMap", namespaces=ncx_root.nsmap)
        hrefs_name_set = {href.split("/")[-1] for href in hrefs_set}
        navpoints = navmap.findall("navPoint", namespaces=navmap.nsmap)
        for navpoint in navpoints:
            source = navpoint.find("content", namespaces=navpoint.nsmap).get("src")
            source_clean = source.split("#")[0]
            navlabel = navpoint.find("navLabel", namespaces=navpoint.nsmap)
            title = navlabel.find("text", namespaces=navlabel.nsmap).text.strip()
            if source_clean in hrefs_set:
                props["table_of_contents"][title] = source
            elif source_clean in hrefs_name_set:
                parent = next(iter(hrefs_set)).split("/")[0]
                props["table_of_contents"][title] = f"{parent}/{source}"
            else:
                pass
        return props
