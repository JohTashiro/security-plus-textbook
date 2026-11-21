(() => {
  const root = document.getElementById("quiz");
  const dataNode = document.getElementById("quiz-data");
  if (!root || !dataNode) return;

  const questions = JSON.parse(dataNode.textContent);
  const letters = ["A", "B", "C", "D", "E", "F"];

  function normalizeAnswer(ans) {
    if (Array.isArray(ans)) return ans.map((a) => String(a).trim().toUpperCase()).sort();
    return String(ans || "")
      .split(/[,、]/)
      .map((a) => a.trim().toUpperCase())
      .filter(Boolean)
      .sort();
  }

  function sameSet(a, b) {
    const x = normalizeAnswer(a);
    const y = normalizeAnswer(b);
    return x.length === y.length && x.every((v, i) => v === y[i]);
  }

  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function render() {
    root.innerHTML = "";
    let score = 0;
    let answered = 0;

    const summary = document.createElement("div");
    summary.className = "quiz-summary";
    summary.innerHTML =
      '正解 <strong id="quiz-score">0</strong> / <strong id="quiz-total">' +
      questions.length +
      "</strong>";
    root.appendChild(summary);

    const list = document.createElement("div");
    list.className = "quiz-list";
    root.appendChild(list);

    questions.forEach((q, qi) => {
      const card = document.createElement("article");
      card.className = "quiz-card";
      if (q.vendor) card.dataset.vendor = q.vendor;

      const stem = document.createElement("p");
      stem.className = "quiz-stem";
      stem.innerHTML =
        '<span class="quiz-num">Q' +
        (qi + 1) +
        "</span>" +
        escapeHtml(q.stem) +
        (q.vendor === "cisco" ? ' <span class="chip chip-vendor">Cisco 固有</span>' : "") +
        (q.type === "multi" ? ' <span class="chip">複数選択</span>' : "") +
        (q.type === "text" ? ' <span class="chip">記述</span>' : "");
      card.appendChild(stem);

      const result = document.createElement("div");
      result.className = "quiz-result";

      function mark(ok, detail) {
        if (card.dataset.done === "1") return;
        card.dataset.done = "1";
        answered += 1;
        if (ok) score += 1;
        card.classList.add(ok ? "correct" : "wrong");
        result.innerHTML =
          (ok ? "正解。" : "不正解。") +
          (detail ? " " + escapeHtml(detail) : "") +
          (q.explain ? "<br>" + escapeHtml(q.explain) : "");
        document.getElementById("quiz-score").textContent = String(score);
        if (answered === questions.length) {
          const note = document.createElement("p");
          note.className = "quiz-finish";
          note.textContent =
            score === questions.length
              ? "全問正解！"
              : "復習して再挑戦しよう（再読込でリセット）";
          root.appendChild(note);
        }
      }

      if (q.type === "text") {
        const wrap = document.createElement("div");
        wrap.className = "quiz-text-wrap";
        const input = document.createElement("input");
        input.type = "text";
        input.className = "quiz-text-input";
        input.placeholder = "答えを入力";
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "btn btn-primary";
        btn.textContent = "判定";
        btn.addEventListener("click", () => {
          const got = input.value.trim();
          const answers = normalizeAnswer(q.answer).map((a) => a.toLowerCase());
          const ok =
            answers.length > 0 &&
            answers.some(
              (a) =>
                got.toLowerCase() === a.toLowerCase() ||
                got.toLowerCase().includes(a.toLowerCase()) ||
                a.toLowerCase().includes(got.toLowerCase())
            );
          mark(ok, "正解例: " + String(q.answer));
          input.disabled = true;
          btn.disabled = true;
        });
        wrap.appendChild(input);
        wrap.appendChild(btn);
        card.appendChild(wrap);
      } else if (q.type === "multi") {
        const box = document.createElement("div");
        box.className = "quiz-choices";
        (q.choices || []).forEach((text, ci) => {
          const label = document.createElement("label");
          label.className = "quiz-choice multi";
          label.innerHTML =
            '<input type="checkbox" value="' +
            letters[ci] +
            '"> <span>' +
            letters[ci] +
            ". " +
            escapeHtml(text) +
            "</span>";
          box.appendChild(label);
        });
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "btn btn-primary";
        btn.textContent = "回答する";
        btn.addEventListener("click", () => {
          const picked = [...box.querySelectorAll("input:checked")].map((el) => el.value);
          const ok = sameSet(picked, q.answer);
          mark(ok, "正解: " + normalizeAnswer(q.answer).join(", "));
          box.querySelectorAll("input").forEach((el) => (el.disabled = true));
          btn.disabled = true;
        });
        card.appendChild(box);
        card.appendChild(btn);
      } else {
        const box = document.createElement("div");
        box.className = "quiz-choices";
        (q.choices || []).forEach((text, ci) => {
          const letter = letters[ci];
          const btn = document.createElement("button");
          btn.type = "button";
          btn.className = "quiz-choice";
          btn.textContent = letter + ". " + text;
          btn.addEventListener("click", () => {
            if (card.dataset.done === "1") return;
            const ok = sameSet([letter], q.answer);
            [...box.children].forEach((el) => (el.disabled = true));
            mark(ok, "正解: " + normalizeAnswer(q.answer).join(", "));
          });
          box.appendChild(btn);
        });
        card.appendChild(box);
      }

      card.appendChild(result);
      list.appendChild(card);
    });
  }

  render();
})();
