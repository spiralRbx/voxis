import { createLockedControl, createVoxisRealtimePlayer, effects } from "./api/voxis-realtime.js";

const $ = (selector) => document.querySelector(selector);

const elements = {
  start: $("#start-engine"),
  viewCode: $("#view-code-button"),
  codePanel: $("#code-panel"),
  fileInput: $("#editor-file-input"),
  compressorEnabled: $("#compressor-enabled"),
  gainRange: $("#gain-range"),
  gainOutput: $("#gain-output"),
  thresholdRange: $("#compressor-threshold-range"),
  thresholdOutput: $("#compressor-threshold-output"),
  host: $("#player-host"),
  status: $("#example-status"),
  jsSource: $("#example-js-source"),
};

let player = null;
const gainControl = createLockedControl({
  input: "#gain-range",
  output: "#gain-output",
  min: 0.0,
  max: 2.0,
  step: 0.01,
  format: (value) => `${value.toFixed(2)}x`,
});
const thresholdControl = createLockedControl({
  input: "#compressor-threshold-range",
  output: "#compressor-threshold-output",
  min: -48.0,
  max: -1.0,
  step: 0.5,
  format: (value) => `${value.toFixed(1)} dB`,
});

function setStatus(message) {
  elements.status.textContent = message;
}

function updateReadouts() {
  gainControl.lock();
  thresholdControl.lock();
}

async function ensurePlayer() {
  if (player) {
    return player;
  }
  player = await createVoxisRealtimePlayer({ container: elements.host });
  setStatus("Engine ready. Load a file to hear the realtime effect chain.");
  return player;
}

function buildEffects() {
  const list = [
    effects.gain({
      value: gainControl.read(),
      limits: { min: 0.0, max: 2.0 },
    }),
  ];

  if (elements.compressorEnabled.checked) {
    list.push(
      effects.compressor({
        thresholdDb: thresholdControl.read(),
        ratio: 3.0,
        makeupDb: 0.0,
        limits: {
          thresholdDb: { min: -48.0, max: -1.0 },
          ratio: { min: 1.0, max: 12.0 },
          makeupDb: { min: -12.0, max: 12.0 },
        },
      }),
    );
  }

  return list;
}

function applyEffects() {
  updateReadouts();
  if (!player) {
    return;
  }
  player.setEffects(buildEffects());
}

async function handleFileChange(event) {
  const [file] = event.target.files || [];
  if (!file) {
    setStatus("No file selected.");
    return;
  }
  const activePlayer = await ensurePlayer();
  await activePlayer.loadFile(file);
  applyEffects();
  setStatus(`Loaded ${file.name}. Press play on the audio element below.`);
}

async function toggleCodePanel() {
  const hidden = elements.codePanel.hidden;
  elements.codePanel.hidden = !hidden;
  elements.viewCode.setAttribute("aria-expanded", String(hidden));
  elements.viewCode.textContent = hidden ? "Hide code" : "View code";
  if (hidden) {
    elements.codePanel.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

async function loadOwnSource() {
  try {
    const response = await fetch(new URL("./realtime-example.js", import.meta.url));
    if (!response.ok) {
      throw new Error(`Unable to load source: ${response.status}`);
    }
    elements.jsSource.textContent = await response.text();
  } catch (error) {
    elements.jsSource.textContent = String(error.message || error);
  }
}

elements.start.addEventListener("click", async () => {
  await ensurePlayer();
  applyEffects();
});
elements.viewCode.addEventListener("click", toggleCodePanel);
elements.fileInput.addEventListener("change", handleFileChange);
elements.gainRange.addEventListener("input", applyEffects);
elements.thresholdRange.addEventListener("input", applyEffects);
elements.compressorEnabled.addEventListener("change", applyEffects);

updateReadouts();
loadOwnSource();
