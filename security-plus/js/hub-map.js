(() => {
  const host = document.getElementById("mindmap");
  const dataNode = document.getElementById("hubmap-data");
  if (!host || !dataNode) return;

  const html = document.documentElement;
  const data = JSON.parse(dataNode.textContent);
  const NS = "http://www.w3.org/2000/svg";
  const domains = data.domains || [];

  const COL = { root: 72, domain: 260, chapter: 470 };
  const DOMAIN_GAP = 96;
  const CHAPTER_GAP = 30;
  const DOMAIN_PAD = 28;

  const UI = {
    mapLabel: { ja: "全体の知識マップ", en: "Full knowledge map", es: "Mapa de conocimiento completo" },
    domainTip: {
      ja: (title, n) => `${title}（用語 ${n}）→ 知識マップ`,
      en: (title, n) => `${title} (${n} terms) → knowledge map`,
      es: (title, n) => `${title} (${n} términos) → mapa de conocimiento`,
    },
  };
  const TITLE_MAX = { ja: 14, en: 22, es: 22 };

  function currentLang() {
    if (html.classList.contains("lang-en")) return "en";
    if (html.classList.contains("lang-es")) return "es";
    return "ja";
  }

  function titleOf(obj, lang) {
    return (lang !== "ja" && obj[`title_${lang}`]) || obj.title;
  }

  function domainHeight(d) {
    const n = (d.chapters || []).length;
    return Math.max(DOMAIN_GAP - 16, n * CHAPTER_GAP + 12);
  }

  function render() {
    const lang = currentLang();
    host.innerHTML = "";

    const heights = domains.map(domainHeight);
    const totalH =
      heights.reduce((a, b) => a + b, 0) + DOMAIN_PAD * Math.max(0, domains.length - 1);
    const width = 760;
    const height = Math.max(420, totalH + 80);
    const rootY = height / 2;

    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.setAttribute("class", "mindmap-svg");
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label", UI.mapLabel[lang]);

    const lines = document.createElementNS(NS, "g");
    lines.setAttribute("class", "mm-lines");
    const nodes = document.createElementNS(NS, "g");
    nodes.setAttribute("class", "mm-nodes");
    svg.appendChild(lines);
    svg.appendChild(nodes);
    host.appendChild(svg);

    function curve(x1, y1, x2, y2) {
      const mx = (x1 + x2) / 2;
      const path = document.createElementNS(NS, "path");
      path.setAttribute("d", `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`);
      path.setAttribute("class", "mm-link");
      lines.appendChild(path);
    }

    function addRoot(x, y, label) {
      const g = document.createElementNS(NS, "g");
      g.setAttribute("class", "mm-hub mm-root");
      g.setAttribute("transform", `translate(${x}, ${y})`);
      const c = document.createElementNS(NS, "circle");
      c.setAttribute("r", 34);
      g.appendChild(c);
      const t = document.createElementNS(NS, "text");
      t.setAttribute("text-anchor", "middle");
      t.setAttribute("dominant-baseline", "central");
      t.setAttribute("class", "mm-root-label");
      t.textContent = label;
      g.appendChild(t);
      nodes.appendChild(g);
    }

    function addDomain(x, y, domain) {
      const g = document.createElementNS(NS, "a");
      g.setAttribute("href", domain.map);
      g.setAttribute("class", "mm-domain");
      g.setAttribute("transform", `translate(${x}, ${y})`);

      const w = 168;
      const h = 52;
      const rect = document.createElementNS(NS, "rect");
      rect.setAttribute("x", 0);
      rect.setAttribute("y", -h / 2);
      rect.setAttribute("rx", 16);
      rect.setAttribute("ry", 16);
      rect.setAttribute("width", w);
      rect.setAttribute("height", h);
      g.appendChild(rect);

      const code = document.createElementNS(NS, "text");
      code.setAttribute("x", 16);
      code.setAttribute("y", -8);
      code.setAttribute("class", "mm-domain-code");
      code.textContent = `Domain ${domain.code}`;
      g.appendChild(code);

      const full = titleOf(domain, lang);
      const max = TITLE_MAX[lang];
      const title = document.createElementNS(NS, "text");
      title.setAttribute("x", 16);
      title.setAttribute("y", 12);
      title.setAttribute("class", "mm-domain-title");
      title.textContent = full.length > max ? `${full.slice(0, max - 1)}…` : full;
      g.appendChild(title);

      const meta = document.createElementNS(NS, "title");
      meta.textContent = UI.domainTip[lang](full, domain.terms);
      g.appendChild(meta);

      nodes.appendChild(g);
      return w;
    }

    function addChapter(x, y, chapter, domainSlug) {
      const g = document.createElementNS(NS, "a");
      g.setAttribute("href", `${domainSlug}/${chapter.slug}.html`);
      g.setAttribute("class", "mm-term mm-chapter-link");
      g.setAttribute("transform", `translate(${x}, ${y})`);

      const label = chapter.id;
      const w = Math.max(64, label.length * 9 + 28);
      const h = 26;
      const rect = document.createElementNS(NS, "rect");
      rect.setAttribute("x", 0);
      rect.setAttribute("y", -h / 2);
      rect.setAttribute("rx", 13);
      rect.setAttribute("ry", 13);
      rect.setAttribute("width", w);
      rect.setAttribute("height", h);
      g.appendChild(rect);

      const t = document.createElementNS(NS, "text");
      t.setAttribute("x", 14);
      t.setAttribute("y", 1);
      t.setAttribute("dominant-baseline", "central");
      t.textContent = label;
      g.appendChild(t);

      const tip = document.createElementNS(NS, "title");
      tip.textContent = `${chapter.id} ${titleOf(chapter, lang)}`;
      g.appendChild(tip);

      nodes.appendChild(g);
    }

    addRoot(COL.root, rootY, data.root || "SY0-701");

    let cursorY = (height - totalH) / 2;
    domains.forEach((domain, i) => {
      const h = heights[i];
      const y = cursorY + h / 2;
      const slug = String(domain.code || "").toLowerCase();
      curve(COL.root + 34, rootY, COL.domain, y);
      const dw = addDomain(COL.domain, y, domain);

      const chapters = domain.chapters || [];
      if (chapters.length) {
        const blockH = chapters.length * CHAPTER_GAP;
        let cy = y - blockH / 2 + CHAPTER_GAP / 2;
        chapters.forEach((ch) => {
          curve(COL.domain + dw, y, COL.chapter, cy);
          addChapter(COL.chapter, cy, ch, slug);
          cy += CHAPTER_GAP;
        });
      }

      cursorY += h;
      if (i < domains.length - 1) cursorY += DOMAIN_PAD;
    });
  }

  render();
  document.addEventListener("lang-change", render);
})();
