(() => {
  const root = document.getElementById("quiz");
  const dataNode = document.getElementById("quiz-data");
  if (!root || !dataNode) return;

  const html = document.documentElement;
  const questions = JSON.parse(dataNode.textContent);
  const letters = ["A", "B", "C", "D"];

  const UI = {
    score: { ja: "正解", en: "Score", es: "Aciertos" },
    allCorrect: { ja: "全問正解！", en: "All correct!", es: "¡Todo correcto!" },
    retry: {
      ja: "復習して再挑戦しよう",
      en: "Review and try again",
      es: "Repasa e inténtalo de nuevo",
    },
    speak: { ja: "問題を読み上げ", en: "Read question aloud", es: "Leer la pregunta en voz alta" },
    speakExplain: { ja: "解説を読み上げ", en: "Read explanation aloud", es: "Leer la explicación en voz alta" },
    stop: { ja: "読み上げを停止", en: "Stop reading", es: "Detener la lectura" },
    speed: { ja: "読み上げ速度", en: "Speech speed", es: "Velocidad de lectura" },
  };

  const ICON_SPEAK =
    '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9v6h4l5 4V5L8 9H4z" fill="currentColor"/>' +
    '<path d="M16 8.5a4.5 4.5 0 0 1 0 7M18.5 6a8 8 0 0 1 0 12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>';
  const ICON_STOP = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor"/></svg>';

  // ---- Text-to-speech (Web Speech API) ----
  const SETTINGS_KEY = "spt-settings";
  const RATES = [0.8, 1, 1.2];
  const SPEECH_LANG = { ja: ["ja-JP"], en: ["en-GB", "en-US"], es: ["es-ES", "es-MX", "es-US"] };
  // macOS novelty voices that sound odd for study material
  const NOVELTY = /^(Albert|Bad News|Bahh|Bells|Boing|Bubbles|Cellos|Good News|Jester|Organ|Superstar|Trinoids|Whisper|Wobble|Zarvox|Junior|Ralph|Fred|Kathy|Grandma|Grandpa|Rocko|Eddy|Flo|Reed|Sandy|Shelley)\b/;
  const synth = "speechSynthesis" in window && "SpeechSynthesisUtterance" in window ? window.speechSynthesis : null;
  let speakingBtn = null;
  let speakToken = 0;
  // Keep references so Chrome doesn't garbage-collect utterances and drop their end events
  let liveUtterances = [];

  function loadSettings() {
    try {
      return JSON.parse(localStorage.getItem(SETTINGS_KEY) || "{}");
    } catch {
      return {};
    }
  }

  function saveRate(rate) {
    const settings = loadSettings();
    settings.ttsRate = rate;
    try {
      localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
    } catch {
      /* storage unavailable */
    }
  }

  function currentRate() {
    const r = Number(loadSettings().ttsRate);
    return RATES.includes(r) ? r : 1;
  }

  function pickVoice(lang) {
    const voices = synth ? synth.getVoices() : [];
    const wanted = SPEECH_LANG[lang];
    const prefix = lang + "";
    let best = null;
    let bestScore = -Infinity;
    for (const v of voices) {
      const vl = (v.lang || "").replace("_", "-");
      if (!vl.toLowerCase().startsWith(prefix)) continue;
      const idx = wanted.findIndex((w) => w.toLowerCase() === vl.toLowerCase());
      let score = idx === -1 ? 0 : 10 - idx * 2;
      if (/Google|Premium|Enhanced|Siri|Natural|Online/i.test(v.name)) score += 1;
      if (NOVELTY.test(v.name)) score -= 20;
      if (score > bestScore) {
        best = v;
        bestScore = score;
      }
    }
    return best;
  }

  // Voices load asynchronously in Chrome; empty list means "unknown", not "unsupported".
  function speechAvailable(lang) {
    if (!synth) return false;
    return synth.getVoices().length === 0 || pickVoice(lang) !== null;
  }

  function splitSentences(text) {
    return String(text)
      .split(/(?<=[。！？!?])\s*|(?<=\.)\s+/)
      .map((s) => s.trim())
      .filter(Boolean);
  }

  function setBtnState(btn, speaking) {
    if (!btn) return;
    const lang = currentLang();
    btn.classList.toggle("speaking", speaking);
    btn.innerHTML = speaking ? ICON_STOP : ICON_SPEAK;
    const label = speaking ? UI.stop[lang] : UI[btn.dataset.labelKey][lang];
    btn.setAttribute("aria-label", label);
    btn.title = label;
  }

  function stopSpeaking() {
    speakToken += 1;
    if (synth) synth.cancel();
    liveUtterances = [];
    setBtnState(speakingBtn, false);
    speakingBtn = null;
  }

  // chunks: short strings, each spoken as its own utterance (avoids Chrome's long-utterance cutoff)
  function speak(btn, parts) {
    if (speakingBtn === btn) {
      stopSpeaking();
      return;
    }
    stopSpeaking();
    const lang = currentLang();
    const voice = pickVoice(lang);
    const rate = currentRate();
    const token = speakToken;
    const chunks = parts.filter(Boolean);
    if (chunks.length === 0) return;
    speakingBtn = btn;
    setBtnState(btn, true);
    chunks.forEach((text, i) => {
      const u = new SpeechSynthesisUtterance(text);
      u.lang = voice ? voice.lang : SPEECH_LANG[lang][0];
      if (voice) u.voice = voice;
      u.rate = rate;
      if (i === chunks.length - 1) {
        const done = () => {
          if (token !== speakToken) return;
          setBtnState(speakingBtn, false);
          speakingBtn = null;
          liveUtterances = [];
        };
        u.onend = done;
        u.onerror = done;
      }
      liveUtterances.push(u);
      synth.speak(u);
    });
  }

  function speakButton(labelKey, getParts) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "tts-btn";
    btn.dataset.labelKey = labelKey;
    setBtnState(btn, false);
    btn.addEventListener("click", () => speak(btn, getParts()));
    return btn;
  }

  function choiceLine(letter, text, lang) {
    return lang === "ja" ? `${letter}、${text}` : `${letter}. ${text}`;
  }

  function rateControl(lang) {
    const wrap = document.createElement("div");
    wrap.className = "tts-rate";
    wrap.setAttribute("role", "group");
    wrap.setAttribute("aria-label", UI.speed[lang]);
    wrap.innerHTML = `<span class="tts-rate-icon" title="${UI.speed[lang]}">${ICON_SPEAK}</span>`;
    const active = currentRate();
    for (const r of RATES) {
      const b = document.createElement("button");
      b.type = "button";
      b.textContent = `${r}×`;
      b.classList.toggle("active", r === active);
      b.setAttribute("aria-pressed", String(r === active));
      b.addEventListener("click", () => {
        saveRate(r);
        for (const other of wrap.querySelectorAll("button")) {
          const on = other === b;
          other.classList.toggle("active", on);
          other.setAttribute("aria-pressed", String(on));
        }
      });
      wrap.appendChild(b);
    }
    return wrap;
  }

  function syncSpeechAvailability() {
    root.classList.toggle("tts-off", !speechAvailable(currentLang()));
  }

  if (synth) {
    synth.addEventListener?.("voiceschanged", syncSpeechAvailability);
    window.addEventListener("pagehide", stopSpeaking);
  }

  function currentLang() {
    if (html.classList.contains("lang-en")) return "en";
    if (html.classList.contains("lang-es")) return "es";
    return "ja";
  }

  function pick(q, field, lang) {
    if (lang !== "ja" && q[`${field}_${lang}`] !== undefined) return q[`${field}_${lang}`];
    return q[field];
  }

  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function render() {
    const lang = currentLang();
    let score = 0;
    let answered = 0;

    stopSpeaking();
    root.innerHTML = "";

    const summary = document.createElement("div");
    summary.className = "quiz-summary";
    summary.innerHTML = `<span>${UI.score[lang]} <strong id="quiz-score">0</strong> / <strong id="quiz-total">${questions.length}</strong></span>`;
    if (synth) summary.appendChild(rateControl(lang));
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
      stem.innerHTML = `<span class="quiz-num">Q${qi + 1}</span>${escapeHtml(pick(q, "stem", lang))}`;
      card.appendChild(stem);
      if (synth) {
        card.classList.add("has-tts");
        card.appendChild(
          speakButton("speak", () => [
            ...splitSentences(pick(q, "stem", lang)),
            ...pick(q, "choices", lang).map((text, ci) => choiceLine(letters[ci], text, lang)),
          ])
        );
      }

      const choices = document.createElement("div");
      choices.className = "quiz-choices";

      pick(q, "choices", lang).forEach((text, ci) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "quiz-choice";
        btn.innerHTML = `<span class="quiz-letter">${letters[ci]}</span><span>${escapeHtml(text)}</span>`;
        btn.addEventListener("click", () => {
          if (card.classList.contains("answered")) return;
          card.classList.add("answered");
          if (speakingBtn && card.contains(speakingBtn)) stopSpeaking();
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
          const expText = pick(q, "explain", lang);
          const expBody = document.createElement("span");
          expBody.textContent = expText;
          exp.appendChild(expBody);
          if (synth) {
            exp.classList.add("has-tts");
            exp.appendChild(speakButton("speakExplain", () => splitSentences(expText)));
          }
          card.appendChild(exp);
          document.getElementById("quiz-score").textContent = String(score);
          if (answered === questions.length) {
            summary.classList.add("done");
            summary.insertAdjacentHTML(
              "beforeend",
              `<span class="quiz-done-msg">${score === questions.length ? UI.allCorrect[lang] : UI.retry[lang]}</span>`
            );
          }
        });
        choices.appendChild(btn);
      });

      card.appendChild(choices);
      list.appendChild(card);
    });
    syncSpeechAvailability();
  }

  render();
  document.addEventListener("lang-change", render);
})();
