/* 95guknow — progressive enhancement only.
   The page is fully readable and navigable with this file blocked. */

const THEMES = ["auto", "dark", "light"];
const LABELS = { auto: "Auto", dark: "Dunkel", light: "Hell" };

const root = document.documentElement;
const toggle = document.querySelector("[data-theme-toggle]");
const label = document.querySelector("[data-theme-label]");

function current() {
  const set = root.dataset.theme;
  return set === "dark" || set === "light" ? set : "auto";
}

function apply(theme) {
  if (theme === "auto") {
    delete root.dataset.theme;
    try {
      localStorage.removeItem("theme");
    } catch {
      /* storage blocked — the choice just won't persist */
    }
  } else {
    root.dataset.theme = theme;
    try {
      localStorage.setItem("theme", theme);
    } catch {
      /* same */
    }
  }
  if (label) label.textContent = LABELS[theme];
  if (toggle) toggle.setAttribute("aria-label", `Farbschema: ${LABELS[theme]} — wechseln`);
}

if (toggle) {
  apply(current());

  toggle.addEventListener("click", () => {
    const next = THEMES[(THEMES.indexOf(current()) + 1) % THEMES.length];

    // Cross-fade the swap where the browser supports it.
    if (document.startViewTransition && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
      document.startViewTransition(() => apply(next));
    } else {
      apply(next);
    }
  });
}

const year = document.querySelector("[data-year]");
if (year) year.textContent = String(new Date().getFullYear());
