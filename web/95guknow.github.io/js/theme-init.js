/* Runs synchronously in <head>: applies the stored theme before first paint
   so there is no flash of the wrong colour scheme. Keep this tiny. */
(function () {
  try {
    var stored = localStorage.getItem("theme");
    if (stored === "dark" || stored === "light") {
      document.documentElement.dataset.theme = stored;
    }
  } catch (e) {
    /* storage blocked — fall through to the OS preference */
  }
})();
