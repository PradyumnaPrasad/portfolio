// Theme toggle + graph/list view switching.
(function () {
  var root = document.documentElement;

  var toggle = document.getElementById("theme-toggle");
  if (toggle) {
    toggle.addEventListener("click", function () {
      var next = root.getAttribute("data-theme") === "light" ? "dark" : "light";
      root.setAttribute("data-theme", next);
      try {
        localStorage.setItem("theme", next);
      } catch (e) {}
      window.dispatchEvent(new Event("themechange"));
    });
  }

  function setList(on) {
    root.classList.toggle("list", on);
    try {
      history.replaceState(null, "", on ? "#list" : "#graph");
    } catch (e) {}
    window.scrollTo(0, 0);
    window.dispatchEvent(new Event("viewchange"));
  }

  var toList = document.getElementById("to-list");
  var toGraph = document.getElementById("to-graph");
  if (toList) toList.addEventListener("click", function () { setList(true); });
  if (toGraph) toGraph.addEventListener("click", function () { setList(false); });
  if (location.hash === "#list") root.classList.add("list");
})();
