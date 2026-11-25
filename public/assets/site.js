(() => {
  "use strict";

  const search = document.querySelector("#project-search");
  const filters = [...document.querySelectorAll("[data-filter]")];
  const cards = [...document.querySelectorAll(".project[data-category]")];
  const count = document.querySelector("#result-count");
  const empty = document.querySelector("#empty");
  const controls = document.querySelector("#project-controls");
  let category = "all";

  function normalize(value) {
    return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  }

  function filterProjects() {
    if (!search || !count || !empty) return;
    const query = normalize(search.value.trim());
    let visible = 0;
    for (const card of cards) {
      const match = (category === "all" || card.dataset.category === category)
        && normalize(card.textContent).includes(query);
      card.hidden = !match;
      if (match) visible += 1;
    }
    count.textContent = `${visible} / ${cards.length} projets et ressources`;
    empty.hidden = visible !== 0;
  }

  function selectCategory(value) {
    category = filters.some(button => button.dataset.filter === value) ? value : "all";
    for (const button of filters) {
      button.setAttribute("aria-pressed", String(button.dataset.filter === category));
    }
    filterProjects();
  }

  if (controls && search) {
    const params = new URLSearchParams(location.search);
    search.value = (params.get("q") || "").slice(0, 100);
    controls.hidden = false;
    search.addEventListener("input", filterProjects);
    for (const button of filters) {
      button.addEventListener("click", () => selectCategory(button.dataset.filter));
    }
    selectCategory(params.get("category") || "all");
  }

  const terminal = document.querySelector("#terminal-form");
  if (terminal) {
    const input = document.querySelector("#terminal-input");
    const output = document.querySelector("#terminal-output");
    const history = [];
    let cursor = 0;
    const destinations = new Map([
      ["home", "/"], ["accueil", "/"], ["about", "/a-propos/"],
      ["apropos", "/a-propos/"], ["skills", "/#competences"],
      ["competences", "/#competences"], ["projects", "/projets/"],
      ["projets", "/projets/"], ["apps", "/apps/"], ["applications", "/apps/"], ["games", "/jeux/"], ["jeux", "/jeux/"],
      ["guides", "/guides/"], ["devlog", "/devlog/"],
      ["contact", "/#streams"], ["stream", "/#streams"], ["streams", "/#streams"]
    ]);
    function append(value, isCommand = false) {
      const line = document.createElement("p");
      line.textContent = value;
      if (isCommand) line.className = "accent";
      output.append(line);
      while (output.children.length > 80) output.firstElementChild.remove();
      output.scrollTop = output.scrollHeight;
    }
    function run(raw) {
      const command = raw.toLowerCase();
      if (command === "clear") {
        output.replaceChildren();
        return;
      }
      append(`guest:~$ ${raw}`, true);
      if (command === "help") {
        append("help · whoami · ls · skills · projects · apps · games · guides · devlog · contact · github · clear\nsearch <mot> · filter <all|infra|security|dev|games|guides>");
      } else if (command === "whoami") {
        append("RufusTheDwarf : étudiant en informatique et développeur indépendant.");
      } else if (command === "ls") {
        append("a-propos/  projets/  apps/  jeux/  guides/  devlog/");
      } else if (command === "github") {
        const link = document.createElement("a");
        link.href = "https://github.com/RufusTheDwarf";
        link.textContent = "Ouvrir le profil GitHub ↗";
        output.append(link);
        output.scrollTop = output.scrollHeight;
      } else if (command.startsWith("search ")) {
        location.assign(`/projets/?${new URLSearchParams({ q: raw.slice(7).trim() })}`);
      } else if (command.startsWith("filter ")) {
        const value = command.slice(7).trim();
        if (!["all", "infra", "security", "dev", "games", "guides"].includes(value)) {
          append("Catégorie inconnue. Tape help.");
          return;
        }
        location.assign(`/projets/?${new URLSearchParams({ category: value })}`);
      } else if (destinations.has(command)) {
        location.assign(destinations.get(command));
      } else {
        append("Commande inconnue. Tape help.");
      }
    }
    terminal.addEventListener("submit", event => {
      event.preventDefault();
      const raw = input.value.trim();
      if (!raw) return;
      history.push(raw);
      if (history.length > 50) history.shift();
      cursor = history.length;
      input.value = "";
      run(raw);
    });
    input.addEventListener("keydown", event => {
      if (event.key !== "ArrowUp" && event.key !== "ArrowDown") return;
      event.preventDefault();
      cursor = Math.max(0, Math.min(history.length, cursor + (event.key === "ArrowUp" ? -1 : 1)));
      input.value = history[cursor] || "";
    });
    terminal.hidden = false;
  }

  // Pause the decorative background without affecting navigation or the terminal.
  const motionToggle = document.querySelector("#motion-toggle");
  if (motionToggle) {
    const root = document.documentElement;
    let paused = false;
    try {
      paused = localStorage.getItem("terminal-motion") === "paused";
    } catch (_) { /* Storage may be disabled. */ }
    function updateMotion() {
      root.toggleAttribute("data-motion-paused", paused);
      motionToggle.setAttribute("aria-pressed", String(paused));
      motionToggle.textContent = paused ? "Animer décor" : "Pause décor";
    }
    updateMotion();
    motionToggle.hidden = false;
    motionToggle.addEventListener("click", () => {
      paused = !paused;
      try { localStorage.setItem("terminal-motion", paused ? "paused" : "active"); }
      catch (_) { /* Keep the current page preference. */ }
      updateMotion();
    });
  }

  // The same preference applies to all pages on this origin.
  const themeSelect = document.querySelector("#theme-select");
  if (themeSelect) {
    const root = document.documentElement;
    const systemTheme = window.matchMedia("(prefers-color-scheme: light)");
    const themeMeta = document.querySelector('meta[name="theme-color"]');
    const syncThemeColor = () => {
      const light = root.dataset.theme === "light" || (!root.dataset.theme && systemTheme.matches);
      if (themeMeta) themeMeta.content = light ? "#d9ddc7" : "#15231e";
    };
    themeSelect.value = root.dataset.theme || "auto";
    themeSelect.closest(".theme-control").hidden = false;
    themeSelect.addEventListener("change", () => {
      const theme = themeSelect.value;
      if (theme === "auto") delete root.dataset.theme;
      else root.dataset.theme = theme;
      try {
        if (theme === "auto") localStorage.removeItem("rufus-theme");
        else localStorage.setItem("rufus-theme", theme);
      } catch (_) { /* The theme still works for this page. */ }
      syncThemeColor();
    });
    systemTheme.addEventListener("change", syncThemeColor);
    syncThemeColor();
  }
})();
