(() => {
  const host = document.getElementById("mindmap");
  const dataNode = document.getElementById("mindmap-data");
  const panel = document.getElementById("term-panel");
  const panelTitle = document.getElementById("term-panel-title");
  const panelMeaning = document.getElementById("term-panel-meaning");
  const panelLink = document.getElementById("term-panel-link");
  const panelClose = document.getElementById("term-panel-close");
  const panelReveal = document.getElementById("term-panel-reveal");
  if (!host || !dataNode) return;

  function setPanelRevealed(revealed) {
    panel.classList.toggle("revealed", revealed);
    if (panelReveal) panelReveal.setAttribute("aria-expanded", String(revealed));
  }

  if (panelReveal) panelReveal.addEventListener("click", () => setPanelRevealed(true));
  document.addEventListener("memorize-change", () => setPanelRevealed(false));

  const data = JSON.parse(dataNode.textContent);
  const NS = "http://www.w3.org/2000/svg";

  const COL = {
    root: 56,
    chapter: 220,
    group: 360,
    term: 520,
  };
  const ROOT_Y_GAP = 0;
  const TERM_GAP = 34;
  const GROUP_PAD = 18;
  const CHAPTER_PAD = 36;

  function stripMarks(text) {
    return String(text || "").replace(/\*\*/g, "");
  }

  function richHtml(text) {
    return String(text || "")
      .split(/(\*\*.+?\*\*)/g)
      .map((part) => {
        const m = part.match(/^\*\*(.+)\*\*$/);
        if (m) {
          return `<span class="hl">${escapeHtml(m[1])}</span>`;
        }
        return escapeHtml(part);
      })
      .join("");
  }

  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  // Measure leaf counts to allocate vertical space
  function chapterHeight(ch) {
    let h = 0;
    ch.groups.forEach((g, i) => {
      h += g.terms.length * TERM_GAP;
      if (i < ch.groups.length - 1) h += GROUP_PAD;
    });
    return Math.max(h, TERM_GAP);
  }

  const chapterHeights = data.chapters.map(chapterHeight);
  const totalH =
    chapterHeights.reduce((a, b) => a + b, 0) +
    CHAPTER_PAD * Math.max(0, data.chapters.length - 1);
  const width = 920;
  const height = Math.max(640, totalH + 80);
  const rootY = height / 2;

  const svg = document.createElementNS(NS, "svg");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("class", "mindmap-svg");
  svg.setAttribute("role", "img");
  const domainCode = data.domain || "A";
  svg.setAttribute("aria-label", `Domain ${domainCode} 知識マップ`);

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

  function addHub(x, y, label, cls) {
    const g = document.createElementNS(NS, "g");
    g.setAttribute("class", `mm-hub ${cls}`);
    g.setAttribute("transform", `translate(${x}, ${y})`);
    const c = document.createElementNS(NS, "circle");
    c.setAttribute("r", cls === "mm-root" ? 28 : 18);
    g.appendChild(c);
    const t = document.createElementNS(NS, "text");
    t.setAttribute("text-anchor", "middle");
    t.setAttribute("dominant-baseline", "central");
    t.textContent = label;
    g.appendChild(t);
    nodes.appendChild(g);
    return g;
  }

  function addTerm(x, y, term, chapterId) {
    const g = document.createElementNS(NS, "g");
    g.setAttribute("class", "mm-term");
    g.setAttribute("transform", `translate(${x}, ${y})`);
    g.setAttribute("tabindex", "0");
    g.setAttribute("role", "button");
    g.dataset.id = term.id;
    g.dataset.ja = term.ja;
    g.dataset.meaning = term.one_liner;
    const slug = String(chapterId || "").toLowerCase();
    g.dataset.href = `${slug}.html#${term.id}`;

    const label = term.ja.replace(/コントロール$/, "").replace(/アプリケーション$/, "アプリ");
    const w = Math.max(88, label.length * 12.5 + 28);
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

    const open = () => showPanel(term, chapterId);
    g.addEventListener("click", (e) => {
      e.stopPropagation();
      open();
    });
    g.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        open();
      }
    });

    nodes.appendChild(g);
    return { g, w };
  }

  function showPanel(term, chapterId) {
    const slug = String(chapterId || "").toLowerCase();
    panelTitle.textContent = term.ja;
    panelMeaning.innerHTML = richHtml(term.one_liner);
    panelLink.href = `${slug}.html#${term.id}`;
    panelLink.textContent = `教科書で見る（${chapterId}）`;
    setPanelRevealed(false);
    panel.classList.add("open");
    panel.setAttribute("aria-hidden", "false");
  }

  function hidePanel() {
    panel.classList.remove("open");
    panel.setAttribute("aria-hidden", "true");
  }

  if (panelClose) panelClose.addEventListener("click", hidePanel);
  document.addEventListener("click", (e) => {
    if (!panel.classList.contains("open")) return;
    if (panel.contains(e.target)) return;
    if (e.target.closest && e.target.closest(".mm-term")) return;
    hidePanel();
  });

  // Root
  addHub(COL.root, rootY, domainCode, "mm-root");

  let cursorY = (height - totalH) / 2;
  data.chapters.forEach((ch, ci) => {
    const chH = chapterHeights[ci];
    const chY = cursorY + chH / 2;
    curve(COL.root + 28, rootY, COL.chapter - 18, chY);
    addHub(COL.chapter, chY, ch.id, "mm-chapter");

    let gCursor = cursorY;
    ch.groups.forEach((group, gi) => {
      const gH = group.terms.length * TERM_GAP;
      const gY = gCursor + gH / 2;
      curve(COL.chapter + 18, chY, COL.group, gY);

      // invisible group fork point (same hierarchy for sibling terms)
      const fork = document.createElementNS(NS, "circle");
      fork.setAttribute("cx", COL.group);
      fork.setAttribute("cy", gY);
      fork.setAttribute("r", 4);
      fork.setAttribute("class", "mm-fork");
      nodes.appendChild(fork);

      group.terms.forEach((term, ti) => {
        const ty = gCursor + TERM_GAP / 2 + ti * TERM_GAP;
        curve(COL.group, gY, COL.term, ty);
        addTerm(COL.term, ty, term, ch.id);
      });

      gCursor += gH;
      if (gi < ch.groups.length - 1) gCursor += GROUP_PAD;
    });

    cursorY += chH;
    if (ci < data.chapters.length - 1) cursorY += CHAPTER_PAD;
  });

  // suppress unused
  void ROOT_Y_GAP;
  void stripMarks;
})();
