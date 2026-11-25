/* Apply a saved preference before CSS is loaded. No network or tracking. */
(() => {
  "use strict";
  try {
    if (localStorage.getItem("terminal-motion") === "paused") {
      document.documentElement.setAttribute("data-motion-paused", "");
    }
    const theme = localStorage.getItem("rufus-theme");
    if (theme === "dark" || theme === "light") {
      document.documentElement.dataset.theme = theme;
    }
  } catch (_) {
    // Private browsing / blocked storage: keep the system preference.
  }
})();
