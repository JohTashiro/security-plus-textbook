(() => {
  const SETTINGS_KEY = "spt-settings";
  const html = document.documentElement;

  function loadSettings() {
    try {
      return JSON.parse(localStorage.getItem(SETTINGS_KEY) || "{}");
    } catch {
      return {};
    }
  }

  function saveSettings(settings) {
    try {
      localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
    } catch {
      /* storage unavailable: setting applies to this page only */
    }
  }

  function currentLang() {
    if (html.classList.contains("lang-en")) return "en";
    if (html.classList.contains("lang-es")) return "es";
    return "ja";
  }

  const cards = [...document.querySelectorAll(".memo-card")];
  const revealAll = document.getElementById("reveal-all");

  function setRevealed(card, revealed) {
    card.classList.toggle("revealed", revealed);
    const btn = card.querySelector(".reveal-btn");
    if (btn) btn.setAttribute("aria-expanded", String(revealed));
  }

  function syncRevealAll() {
    if (!revealAll) return;
    const lang = currentLang();
    const allShown = cards.length > 0 && cards.every((c) => c.classList.contains("revealed"));
    const attr = allShown ? `data-hide-all-${lang}` : `data-show-all-${lang}`;
    const label = revealAll.getAttribute(attr);
    if (label) revealAll.textContent = label;
  }

  for (const card of cards) {
    const btn = card.querySelector(".reveal-btn");
    if (!btn) continue;
    btn.addEventListener("click", () => {
      setRevealed(card, true);
      syncRevealAll();
    });
  }

  if (revealAll) {
    revealAll.addEventListener("click", () => {
      const show = !cards.every((c) => c.classList.contains("revealed"));
      cards.forEach((c) => setRevealed(c, show));
      syncRevealAll();
    });
  }

  for (const input of document.querySelectorAll("[data-setting]")) {
    const name = input.dataset.setting;
    input.checked = html.classList.contains(name);
    input.addEventListener("change", () => {
      const settings = loadSettings();
      settings[name] = input.checked;
      saveSettings(settings);
      html.classList.toggle(name, input.checked);
      if (name === "memorize") {
        cards.forEach((c) => setRevealed(c, false));
        syncRevealAll();
        document.dispatchEvent(new CustomEvent("memorize-change"));
      }
    });
  }

  function applySearchPlaceholder() {
    const lang = currentLang();
    const searchInput = document.getElementById("term-search");
    if (searchInput) {
      const ph = searchInput.dataset["ph" + lang.charAt(0).toUpperCase() + lang.slice(1)];
      if (ph) searchInput.placeholder = ph;
    }
  }

  const langButtons = [...document.querySelectorAll("[data-lang-btn]")];

  function syncLangButtons() {
    const lang = currentLang();
    for (const btn of langButtons) {
      btn.classList.toggle("active", btn.dataset.langBtn === lang);
    }
  }

  function setLang(lang) {
    const settings = loadSettings();
    settings.lang = lang;
    saveSettings(settings);
    html.classList.toggle("lang-en", lang === "en");
    html.classList.toggle("lang-es", lang === "es");
    syncLangButtons();
    applySearchPlaceholder();
    syncRevealAll();
    document.dispatchEvent(new CustomEvent("lang-change", { detail: { lang } }));
  }

  for (const btn of langButtons) {
    btn.addEventListener("click", () => setLang(btn.dataset.langBtn));
  }

  syncLangButtons();
  applySearchPlaceholder();
  syncRevealAll();

  const input = document.getElementById("term-search");
  const terms = [...document.querySelectorAll(".term, .memo-card")];
  const empty = document.getElementById("empty-state");
  const toggle = document.getElementById("menu-toggle");
  const sidebar = document.getElementById("sidebar");

  if (toggle && sidebar) {
    toggle.addEventListener("click", () => {
      sidebar.classList.toggle("open");
    });
    document.addEventListener("click", (event) => {
      if (
        sidebar.classList.contains("open") &&
        !sidebar.contains(event.target) &&
        event.target !== toggle
      ) {
        sidebar.classList.remove("open");
      }
    });
  }

  if (!input || terms.length === 0) return;

  const filter = () => {
    const q = input.value.trim().toLowerCase();
    let visible = 0;
    for (const term of terms) {
      const hay = term.dataset.search || term.textContent.toLowerCase();
      const match = !q || hay.includes(q);
      term.hidden = !match;
      if (match) visible += 1;
    }
    if (empty) empty.classList.toggle("visible", visible === 0);
  };

  input.addEventListener("input", filter);
})();
