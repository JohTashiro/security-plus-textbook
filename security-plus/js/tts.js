// Read-aloud via the browser's Web Speech API. Exposes window.SPT_TTS for quiz.js / app.js.
(() => {
  const html = document.documentElement;
  const SETTINGS_KEY = "spt-settings";
  const RATES = [0.8, 1, 1.2];
  const SPEECH_LANG = { ja: ["ja-JP"], en: ["en-GB", "en-US"], es: ["es-ES", "es-MX", "es-US"] };
  // macOS novelty voices that sound odd for study material
  const NOVELTY =
    /^(Albert|Bad News|Bahh|Bells|Boing|Bubbles|Cellos|Good News|Jester|Organ|Superstar|Trinoids|Whisper|Wobble|Zarvox|Junior|Ralph|Fred|Kathy|Grandma|Grandpa|Rocko|Eddy|Flo|Reed|Sandy|Shelley)\b/;
  const STOP_LABEL = { ja: "読み上げを停止", en: "Stop reading", es: "Detener la lectura" };

  const ICON_SPEAK =
    '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9v6h4l5 4V5L8 9H4z" fill="currentColor"/>' +
    '<path d="M16 8.5a4.5 4.5 0 0 1 0 7M18.5 6a8 8 0 0 1 0 12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>';
  const ICON_STOP =
    '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor"/></svg>';

  const synth =
    "speechSynthesis" in window && "SpeechSynthesisUtterance" in window ? window.speechSynthesis : null;
  let speakingBtn = null;
  let speakToken = 0;
  // Keep references so Chrome doesn't garbage-collect utterances and drop their end events
  let liveUtterances = [];

  function currentLang() {
    if (html.classList.contains("lang-en")) return "en";
    if (html.classList.contains("lang-es")) return "es";
    return "ja";
  }

  function loadSettings() {
    try {
      return JSON.parse(localStorage.getItem(SETTINGS_KEY) || "{}");
    } catch {
      return {};
    }
  }

  function currentRate() {
    const r = Number(loadSettings().ttsRate);
    return RATES.includes(r) ? r : 1;
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

  function pickVoice(lang) {
    const voices = synth ? synth.getVoices() : [];
    const wanted = SPEECH_LANG[lang];
    let best = null;
    let bestScore = -Infinity;
    for (const v of voices) {
      const vl = (v.lang || "").replace("_", "-").toLowerCase();
      if (!vl.startsWith(lang)) continue;
      const idx = wanted.findIndex((w) => w.toLowerCase() === vl);
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

  // Voices load asynchronously in Chrome; an empty list means "unknown", not "unsupported".
  function available(lang) {
    if (!synth) return false;
    return synth.getVoices().length === 0 || pickVoice(lang) !== null;
  }

  function syncAvailability() {
    html.classList.toggle("tts-off", !available(currentLang()));
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
    const labels = btn._ttsLabels || {};
    const label = speaking ? STOP_LABEL[lang] : labels[lang] || labels.ja || "";
    btn.setAttribute("aria-label", label);
    btn.title = label;
  }

  function stop() {
    speakToken += 1;
    if (synth) synth.cancel();
    liveUtterances = [];
    setBtnState(speakingBtn, false);
    speakingBtn = null;
  }

  // chunks: short strings, each spoken as its own utterance (avoids Chrome's long-utterance cutoff)
  function speak(btn, chunks) {
    if (!synth) return;
    if (speakingBtn === btn) {
      stop();
      return;
    }
    stop();
    const lang = currentLang();
    const voice = pickVoice(lang);
    const rate = currentRate();
    const token = speakToken;
    const parts = chunks.map((c) => String(c).trim()).filter(Boolean);
    if (parts.length === 0) return;
    speakingBtn = btn;
    setBtnState(btn, true);
    parts.forEach((text, i) => {
      const u = new SpeechSynthesisUtterance(text);
      u.lang = voice ? voice.lang : SPEECH_LANG[lang][0];
      if (voice) u.voice = voice;
      u.rate = rate;
      if (i === parts.length - 1) {
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

  // labels: {ja, en, es}; getChunks: () => string[]
  function button(labels, getChunks, className = "") {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = ("tts-btn " + className).trim();
    btn._ttsLabels = labels;
    setBtnState(btn, false);
    btn.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      speak(btn, getChunks());
    });
    return btn;
  }

  function isSpeaking(within) {
    return !!speakingBtn && (!within || within.contains(speakingBtn));
  }

  // Speed buttons live in the settings panel on every page
  function initRateButtons() {
    const buttons = [...document.querySelectorAll("[data-tts-rate]")];
    const sync = () => {
      const active = currentRate();
      for (const b of buttons) {
        const on = Number(b.dataset.ttsRate) === active;
        b.classList.toggle("active", on);
        b.setAttribute("aria-pressed", String(on));
      }
    };
    for (const b of buttons) {
      b.addEventListener("click", () => {
        saveRate(Number(b.dataset.ttsRate));
        sync();
      });
    }
    sync();
  }

  if (!synth) html.classList.add("tts-off", "no-tts");
  else {
    synth.addEventListener?.("voiceschanged", syncAvailability);
    window.addEventListener("pagehide", stop);
    syncAvailability();
  }
  document.addEventListener("lang-change", () => {
    stop();
    syncAvailability();
    // Relabel idle buttons for the new language
    for (const b of document.querySelectorAll(".tts-btn")) setBtnState(b, false);
  });
  initRateButtons();

  window.SPT_TTS = { supported: !!synth, button, stop, isSpeaking, splitSentences, currentLang };
})();
