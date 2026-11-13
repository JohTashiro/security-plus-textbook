(() => {
  const root = document.getElementById("quiz");
  const dataNode = document.getElementById("quiz-data");
  if (!root || !dataNode) return;

  const questions = JSON.parse(dataNode.textContent);
  const letters = ["A", "B", "C", "D"];
  let score = 0;
  let answered = 0;

  const summary = document.createElement("div");
  summary.className = "quiz-summary";
  summary.innerHTML = `<span>正解 <strong id="quiz-score">0</strong> / <strong id="quiz-total">${questions.length}</strong></span>`;
  root.appendChild(summary);

  const list = document.createElement("div");
  list.className = "quiz-list";
  root.appendChild(list);

  questions.forEach((q, qi) => {
    const card = document.createElement("article");
    card.className = "quiz-card";
    card.dataset.term = q.term;

    const stem = document.createElement("p");
    stem.className = "quiz-stem";
    stem.innerHTML = `<span class="quiz-num">Q${qi + 1}</span>${escapeHtml(q.stem)}`;
    card.appendChild(stem);

    const choices = document.createElement("div");
    choices.className = "quiz-choices";

    q.choices.forEach((text, ci) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "quiz-choice";
      btn.innerHTML = `<span class="quiz-letter">${letters[ci]}</span><span>${escapeHtml(text)}</span>`;
      btn.addEventListener("click", () => {
        if (card.classList.contains("answered")) return;
        card.classList.add("answered");
        answered += 1;
        const correct = ci === q.answer;
        if (correct) {
          score += 1;
          btn.classList.add("correct");
        } else {
          btn.classList.add("wrong");
          const right = choices.children[q.answer];
          if (right) right.classList.add("correct");
        }
        [...choices.children].forEach((el) => {
          el.disabled = true;
        });
        const exp = document.createElement("p");
        exp.className = "quiz-explain";
        exp.textContent = q.explain;
        card.appendChild(exp);
        document.getElementById("quiz-score").textContent = String(score);
        if (answered === questions.length) {
          summary.classList.add("done");
          summary.insertAdjacentHTML(
            "beforeend",
            `<span class="quiz-done-msg">${score === questions.length ? "全問正解！" : "復習して再挑戦しよう"}</span>`
          );
        }
      });
      choices.appendChild(btn);
    });

    card.appendChild(choices);
    list.appendChild(card);
  });

  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
})();
