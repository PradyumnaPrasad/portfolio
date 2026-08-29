// Theme toggle + game/text view switching.
(function () {
  var root = document.documentElement;

  var toggle = document.getElementById("theme-toggle");
  if (toggle) {
    toggle.addEventListener("click", function () {
      var next = root.getAttribute("data-theme") === "light" ? "dark" : "light";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("theme", next); } catch (e) {}
      window.dispatchEvent(new Event("themechange"));
    });
  }

  function setText(on) {
    root.classList.toggle("text", on);
    try { localStorage.setItem("view", on ? "text" : "game"); } catch (e) {}
    window.scrollTo(0, 0);
    window.dispatchEvent(new Event("viewchange"));
  }
  var toText = document.getElementById("to-text");
  var toGame = document.getElementById("to-game");
  if (toText) toText.addEventListener("click", function () { setText(true); });
  if (toGame) toGame.addEventListener("click", function () { setText(false); });
})();
