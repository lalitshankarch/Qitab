var style = document.createElement("style");
style.innerHTML = `
body {
    font-family: 'C059', 'Georgia', 'Cambria', serif;
    max-width: min(75vw, 60em) !important;
    margin: 2.5em auto !important;
}
a {
    font-size: 0.75em !important;
}
`;
document.head.appendChild(style);
var zoomLevel = parseFloat(localStorage.getItem("zoomLevel")) || 1;
var zoomStep = 0.1;
var nightMode = JSON.parse(localStorage.getItem("nightMode")) || false;
function applyNightMode() {
  document.body.style.backgroundColor = nightMode ? "#333" : "#fff";
  document.body.style.color = nightMode ? "#fff" : "#000";
  var linkColor = nightMode ? "darkgray" : "gray";
  var visitedLinkColor = nightMode ? "gray" : "darkgray";
  var existingNightModeStyle = document.getElementById("nightModeStyle");
  if (existingNightModeStyle) {
    existingNightModeStyle.remove();
  }
  var nightModeStyle = document.createElement("style");
  nightModeStyle.id = "nightModeStyle";
  nightModeStyle.innerHTML = `
  a {
      color: ${linkColor} !important;
  }
  a:visited {
      color: ${visitedLinkColor} !important;
  }
  `;
  document.head.appendChild(nightModeStyle);
}
function updateZoom() {
  document.body.style.zoom = zoomLevel;
  localStorage.setItem("zoomLevel", zoomLevel);
}
applyNightMode();
updateZoom();
function toggleNightMode() {
  nightMode = !nightMode;
  localStorage.setItem("nightMode", JSON.stringify(nightMode));
  applyNightMode();
}
document.addEventListener("keydown", function (event) {
  if (event.ctrlKey) {
    if (event.key === "-" || event.key === "_") {
      zoomLevel = Math.max(0.1, zoomLevel - zoomStep);
      updateZoom();
      event.preventDefault();
    } else if (event.key === "+" || event.key === "=") {
      zoomLevel += zoomStep;
      updateZoom();
      event.preventDefault();
    }
  } else if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
    window.pywebview.api.keypress(event.key);
  } else if (event.key === "n") {
    toggleNightMode();
    event.preventDefault();
  }
});
document.addEventListener("click", function (event) {
  if (event.target.tagName === "a" && event.target.href.startsWith("http")) {
    event.preventDefault();
    window.pywebview.api.open_external_link(event.target.href);
  }
});
