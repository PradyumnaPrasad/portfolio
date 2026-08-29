// Theme toggle with persistence. Dark is the default; respect a stored choice
// and fall back to the OS preference on first visit.
(function () {
  const root = document.documentElement;
  let stored = null;
  try {
    stored = localStorage.getItem("theme");
  } catch (_) {
    /* storage blocked — fine */
  }
  if (stored === "light" || stored === "dark") {
    root.setAttribute("data-theme", stored);
  } else if (window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches) {
    root.setAttribute("data-theme", "light");
  }

  const btn = document.getElementById("theme-toggle");
  if (btn) {
    btn.addEventListener("click", function () {
      const next = root.getAttribute("data-theme") === "light" ? "dark" : "light";
      root.setAttribute("data-theme", next);
      try {
        localStorage.setItem("theme", next);
      } catch (_) {
        /* ignore */
      }
    });
  }
})();
