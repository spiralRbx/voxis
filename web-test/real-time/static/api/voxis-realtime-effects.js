const PARAMETRIC_BANDS = [1, 2, 3];

export const DEFAULT_BASIC_CONFIG = {
  normalize: { enabled: false, headroomDb: 1.0, maxGain: 4.0 },
  fadeIn: { enabled: false, durationMs: 400.0 },
  fadeOut: { enabled: false, durationMs: 500.0 },
  trim: { enabled: false, startMs: 0.0, endMs: 30000.0, featherMs: 12.0 },
  cut: { enabled: false, startMs: 1200.0, endMs: 2200.0, featherMs: 12.0 },
  silenceRemoval: { enabled: false, thresholdDb: -48.0, minSilenceMs: 80.0, paddingMs: 10.0 },
  reverse: { enabled: false, windowMs: 350.0, mix: 1.0 },
};

export const DEFAULT_COLOR_TIME_CONFIG = {
  distortion: { enabled: false, drive: 2.0 },
  overdrive: { enabled: false, drive: 1.8, tone: 0.55, mix: 1.0 },
  fuzz: { enabled: false, drive: 3.6, bias: 0.12, mix: 1.0 },
  bitcrusher: { enabled: false, bitDepth: 8, sampleRateReduction: 4, mix: 1.0 },
  waveshaper: { enabled: false, amount: 1.4, symmetry: 0.0, mix: 1.0 },
  tubeSaturation: { enabled: false, drive: 1.6, bias: 0.08, mix: 1.0 },
  tapeSaturation: { enabled: false, drive: 1.4, softness: 0.35, mix: 1.0 },
  softClipping: { enabled: false, threshold: 0.85 },
  hardClipping: { enabled: false, threshold: 0.92 },
  pitchShift: { enabled: false, semitones: 0.0, mix: 1.0 },
  autoTune: { enabled: false, strength: 0.7, key: "C", scale: "chromatic", minHz: 80.0, maxHz: 1000.0 },
  harmonizer: { enabled: false, intervalA: 7.0, intervalB: 12.0, intervalC: 0.0, mix: 0.35 },
  octaver: { enabled: false, octavesDown: 1, octavesUp: 0, downMix: 0.45, upMix: 0.0 },
  formantShifting: { enabled: false, shift: 1.12, mix: 1.0, q: 3.6 },
};

export const DEFAULT_MODERN_CREATIVE_CONFIG = {
  noiseReduction: { enabled: false, strength: 0.5 },
  voiceIsolation: { enabled: false, strength: 0.75, lowHz: 120.0, highHz: 5200.0 },
  sourceSeparation: { enabled: false, target: "vocals", strength: 0.8, lowHz: 120.0, highHz: 5200.0 },
  deReverb: { enabled: false, amount: 0.45, tailMs: 240.0 },
  deEcho: { enabled: false, amount: 0.45, minDelayMs: 60.0, maxDelayMs: 800.0 },
  spectralRepair: { enabled: false, strength: 0.35 },
  aiEnhancer: { enabled: false, amount: 0.6 },
  speechEnhancement: { enabled: false, amount: 0.7 },
  glitchEffect: { enabled: false, sliceMs: 70.0, repeatProbability: 0.22, dropoutProbability: 0.12, reverseProbability: 0.1, mix: 1.0 },
  stutter: { enabled: false, sliceMs: 90.0, repeats: 3, intervalMs: 480.0, mix: 1.0 },
  tapeStop: { enabled: false, stopTimeMs: 900.0, curve: 2.0, mix: 1.0 },
  reverseReverb: { enabled: false, decaySeconds: 1.2, mix: 0.45 },
  granularSynthesis: { enabled: false, grainMs: 80.0, overlap: 0.5, jitterMs: 25.0, mix: 1.0 },
  timeSlicing: { enabled: false, sliceMs: 120.0, mix: 1.0 },
  randomPitchMod: { enabled: false, depthSemitones: 2.0, segmentMs: 180.0, mix: 1.0 },
  vinylEffect: { enabled: false, noise: 0.08, wow: 0.15, crackle: 0.12, mix: 1.0 },
  radioEffect: { enabled: false, noiseLevel: 0.04, mix: 1.0 },
  telephoneEffect: { enabled: false, mix: 1.0 },
  retro8bit: { enabled: false, bitDepth: 6, sampleRateReduction: 8, mix: 1.0 },
  slowMotionExtreme: { enabled: false, rate: 0.45, toneHz: 4800.0, mix: 1.0 },
  robotVoice: { enabled: false, carrierHz: 70.0, mix: 0.85 },
  alienVoice: { enabled: false, shiftSemitones: 5.0, formantShift: 1.18, mix: 0.8 },
};

export const DEFAULT_SPECTRAL_SPATIAL_CONFIG = {
  fftFilter: { enabled: false, lowHz: 80.0, highHz: 12000.0, mix: 1.0 },
  spectralGating: { enabled: false, thresholdDb: -42.0, floor: 0.08 },
  spectralBlur: { enabled: false, amount: 0.45 },
  spectralFreeze: { enabled: false, startMs: 120.0, mix: 0.7 },
  spectralMorphing: { enabled: false, amount: 0.5 },
  phaseVocoder: { enabled: false, rate: 0.85 },
  harmonicPercussiveSeparation: { enabled: false, target: "harmonic", mix: 1.0 },
  spectralDelay: { enabled: false, maxDelayMs: 240.0, feedback: 0.15, mix: 0.35 },
  stereoWidening: { enabled: false, amount: 1.25 },
  midSideProcessing: { enabled: false, midGainDb: 0.0, sideGainDb: 0.0 },
  stereoImager: { enabled: false, lowWidth: 0.9, highWidth: 1.35, crossoverHz: 280.0 },
  binauralEffect: { enabled: false, azimuthDeg: 25.0, distance: 1.0, roomMix: 0.08 },
  spatialPositioning: { enabled: false, azimuthDeg: 25.0, elevationDeg: 0.0, distance: 1.0 },
  hrtfSimulation: { enabled: false, azimuthDeg: 30.0, elevationDeg: 0.0, distance: 1.0 },
};

export const DEFAULT_DYNAMICS_CONFIG = {
  highpass: { enabled: false, frequencyHz: 80.0, q: 0.70710678, gainDb: 0.0, slope: 1.0, stages: 2 },
  lowpass: { enabled: false, frequencyHz: 18000.0, q: 0.70710678, gainDb: 0.0, slope: 1.0, stages: 2 },
  bandpass: { enabled: false, frequencyHz: 1200.0, q: 0.9, gainDb: 0.0, slope: 1.0, stages: 1 },
  notch: { enabled: false, frequencyHz: 3500.0, q: 2.0, gainDb: 0.0, slope: 1.0, stages: 1 },
  peakEq: { enabled: false, frequencyHz: 2800.0, q: 1.0, gainDb: 0.0, slope: 1.0, stages: 1 },
  lowShelf: { enabled: false, frequencyHz: 120.0, q: 0.70710678, gainDb: 0.0, slope: 1.0, stages: 1 },
  highShelf: { enabled: false, frequencyHz: 9500.0, q: 0.70710678, gainDb: 0.0, slope: 1.0, stages: 1 },
  resonantFilter: { enabled: false, mode: "lowpass", frequencyHz: 1200.0, resonance: 1.6, stages: 1 },
  parametricEq: [
    { enabled: false, kind: "peak", frequencyHz: 180.0, gainDb: 0.0, q: 0.9, slope: 1.0, stages: 1 },
    { enabled: false, kind: "peak", frequencyHz: 3000.0, gainDb: 0.0, q: 1.0, slope: 1.0, stages: 1 },
    { enabled: false, kind: "peak", frequencyHz: 9500.0, gainDb: 0.0, q: 0.8, slope: 1.0, stages: 1 },
  ],
  graphicEq: { enabled: false, q: 1.1, bandsDb: [0.0, 0.0, 0.0, 0.0, 0.0] },
  dynamicEq: { enabled: false, frequencyHz: 2800.0, thresholdDb: -24.0, cutDb: -6.0, q: 1.2, attackMs: 10.0, releaseMs: 120.0 },
  formantFilter: { enabled: false, morph: 0.0, intensity: 1.0, q: 4.0 },
  compressor: { enabled: false, thresholdDb: -18.0, ratio: 3.0, attackMs: 10.0, releaseMs: 80.0, makeupDb: 0.0 },
  downwardCompression: { enabled: false, thresholdDb: -18.0, ratio: 4.0, attackMs: 10.0, releaseMs: 80.0, makeupDb: 0.0 },
  upwardCompression: { enabled: false, thresholdDb: -42.0, ratio: 2.0, attackMs: 12.0, releaseMs: 120.0, maxGainDb: 18.0 },
  limiter: { enabled: false, ceilingDb: -1.0, attackMs: 1.0, releaseMs: 60.0 },
  expander: { enabled: false, thresholdDb: -35.0, ratio: 2.0, attackMs: 8.0, releaseMs: 80.0, makeupDb: 0.0 },
  noiseGate: { enabled: false, thresholdDb: -45.0, attackMs: 3.0, releaseMs: 60.0, floorDb: -80.0 },
  deesser: { enabled: false, frequencyHz: 6500.0, thresholdDb: -28.0, ratio: 4.0, attackMs: 2.0, releaseMs: 60.0, amount: 0.8 },
  transientShaper: { enabled: false, attack: 0.7, sustain: 0.2, attackMs: 18.0, releaseMs: 120.0 },
  multibandCompressor: { enabled: false, lowCutHz: 180.0, highCutHz: 3200.0, lowThresholdDb: -24.0, midThresholdDb: -18.0, highThresholdDb: -20.0, lowRatio: 2.2, midRatio: 3.0, highRatio: 2.4, attackMs: 10.0, releaseMs: 90.0, lowMakeupDb: 0.0, midMakeupDb: 0.0, highMakeupDb: 0.0 },
};

export const DEFAULT_MODULATION_CONFIG = {
  chorus: { enabled: false, rateHz: 0.9, depthMs: 7.5, delayMs: 18.0, mix: 0.35, feedback: 0.12 },
  flanger: { enabled: false, rateHz: 0.25, depthMs: 1.8, delayMs: 2.5, mix: 0.45, feedback: 0.35 },
  phaser: { enabled: false, rateHz: 0.35, depth: 0.75, centerHz: 900.0, feedback: 0.2, mix: 0.5, stages: 4 },
  tremolo: { enabled: false, rateHz: 4.0, depth: 0.5 },
  vibrato: { enabled: false, rateHz: 5.0, depthMs: 3.5, delayMs: 5.5 },
  autoPan: { enabled: false, rateHz: 0.35, depth: 1.0 },
  rotarySpeaker: { enabled: false, rateHz: 0.8, depth: 0.7, mix: 0.65, crossoverHz: 900.0 },
  ringModulation: { enabled: false, frequencyHz: 30.0, mix: 0.5 },
  frequencyShifter: { enabled: false, shiftHz: 120.0, mix: 1.0 },
};

export const DEFAULT_SPACE_CONFIG = {
  delay: { enabled: false, delayMs: 180.0, feedback: 0.25, mix: 0.18 },
  echo: { enabled: false, delayMs: 320.0, feedback: 0.38, mix: 0.28 },
  pingPongDelay: { enabled: false, delayMs: 280.0, feedback: 0.55, mix: 0.3 },
  multiTapDelay: { enabled: false, delayMs: 120.0, taps: 4, spacingMs: 65.0, decay: 0.6, mix: 0.32 },
  slapbackDelay: { enabled: false, delayMs: 95.0, feedback: 0.0, mix: 0.24 },
  earlyReflections: { enabled: false, preDelayMs: 12.0, spreadMs: 8.0, taps: 6, decay: 0.7, mix: 0.22 },
  roomReverb: { enabled: false, decaySeconds: 0.8, mix: 0.22, toneHz: 8000.0 },
  hallReverb: { enabled: false, decaySeconds: 1.8, mix: 0.28, toneHz: 7200.0 },
  plateReverb: { enabled: false, decaySeconds: 1.2, mix: 0.24, toneHz: 9500.0 },
  convolutionReverb: { enabled: false, mix: 0.28, normalizeIr: true },
};

export const DEFAULT_RUNTIME_STATE = {
  inputGain: 1.0,
  outputGain: 1.0,
  monoMix: 0.0,
  dcBlock: true,
  drive: 1.0,
  pan: 0.0,
  crossfade: { enabled: false, durationMs: 1200.0 },
  timeStretch: { enabled: false, rate: 0.9 },
  timeCompression: { enabled: false, rate: 1.15 },
};

export const DEFAULT_TRANSPORT = {
  sourceKind: "none",
  playing: false,
  startContextTimeSec: 0.0,
  positionSec: 0.0,
  durationSec: 0.0,
  playbackRate: 1.0,
};

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function toFiniteNumber(value, fallback) {
  const number = Number(value);
  return Number.isFinite(number) ? number : Number(fallback);
}

function sanitizeStringByKey(key, value, fallback) {
  const text = value == null ? String(fallback) : String(value);
  const normalizedKey = String(key || "").toLowerCase();
  if (normalizedKey === "mode") {
    return ["lowpass", "highpass", "bandpass", "notch"].includes(text) ? text : String(fallback);
  }
  if (normalizedKey === "kind") {
    return ["peak", "lowShelf", "highShelf", "lowpass", "highpass", "bandpass", "notch"].includes(text) ? text : String(fallback);
  }
  if (normalizedKey === "target") {
    return ["vocals", "drums", "bass", "other", "harmonic", "percussive"].includes(text) ? text : String(fallback);
  }
  if (normalizedKey === "key") {
    return ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"].includes(text) ? text : String(fallback);
  }
  if (normalizedKey === "scale") {
    return ["chromatic", "major", "minor", "pentatonic"].includes(text) ? text : String(fallback);
  }
  return text;
}

function sanitizeNumberByKey(key, value, fallback) {
  const normalizedKey = String(key || "").toLowerCase();

  if (normalizedKey === "inputgain" || normalizedKey === "outputgain") {
    return clamp(toFiniteNumber(value, fallback), 0.0, 4.0);
  }
  if (normalizedKey === "monomix") {
    return clamp(toFiniteNumber(value, fallback), 0.0, 1.0);
  }
  if (normalizedKey === "pan") {
    return clamp(toFiniteNumber(value, fallback), -1.0, 1.0);
  }
  if (normalizedKey === "threshold") {
    return clamp(toFiniteNumber(value, fallback), 0.01, 1.0);
  }
  if (normalizedKey === "tone") {
    return clamp(toFiniteNumber(value, fallback), 0.0, 1.0);
  }
  if (normalizedKey === "bias" || normalizedKey === "symmetry") {
    return clamp(toFiniteNumber(value, fallback), -1.0, 1.0);
  }
  if (normalizedKey === "maxgain") {
    return clamp(toFiniteNumber(value, fallback), 0.0, 16.0);
  }
  if (normalizedKey === "drive") {
    return clamp(toFiniteNumber(value, fallback), 0.0, 16.0);
  }
  if (normalizedKey === "distance") {
    return clamp(toFiniteNumber(value, fallback), 0.1, 10.0);
  }
  if (normalizedKey === "azimuthdeg") {
    return clamp(toFiniteNumber(value, fallback), -180.0, 180.0);
  }
  if (normalizedKey === "elevationdeg") {
    return clamp(toFiniteNumber(value, fallback), -90.0, 90.0);
  }
  if (normalizedKey === "q" || normalizedKey === "resonance") {
    return clamp(toFiniteNumber(value, fallback), 0.1, 24.0);
  }
  if (normalizedKey === "stages") {
    return clamp(Math.round(toFiniteNumber(value, fallback)), 1, 12);
  }
  if (normalizedKey === "taps") {
    return clamp(Math.round(toFiniteNumber(value, fallback)), 1, 16);
  }
  if (normalizedKey === "repeats") {
    return clamp(Math.round(toFiniteNumber(value, fallback)), 1, 16);
  }
  if (normalizedKey === "octavesdown" || normalizedKey === "octavesup") {
    return clamp(Math.round(toFiniteNumber(value, fallback)), 0, 4);
  }
  if (normalizedKey === "bitdepth") {
    return clamp(Math.round(toFiniteNumber(value, fallback)), 1, 24);
  }
  if (normalizedKey === "sampleratereduction") {
    return clamp(Math.round(toFiniteNumber(value, fallback)), 1, 64);
  }
  if (normalizedKey === "bandsdb") {
    return clamp(toFiniteNumber(value, fallback), -24.0, 24.0);
  }
  if (normalizedKey === "rate") {
    return clamp(toFiniteNumber(value, fallback), 0.05, 4.0);
  }
  if (normalizedKey.endsWith("ratehz")) {
    return clamp(toFiniteNumber(value, fallback), 0.01, 40.0);
  }
  if (normalizedKey.endsWith("mix") || ["strength", "amount", "floor", "noise", "crackle", "wow", "softness", "overlap", "normalizeir"].includes(normalizedKey)) {
    return clamp(toFiniteNumber(value, fallback), 0.0, 1.0);
  }
  if (normalizedKey.endsWith("hz") || normalizedKey.includes("cuthz")) {
    return clamp(toFiniteNumber(value, fallback), 0.0, 24000.0);
  }
  if (normalizedKey.endsWith("ms")) {
    return clamp(toFiniteNumber(value, fallback), 0.0, 120000.0);
  }
  if (normalizedKey.endsWith("seconds")) {
    return clamp(toFiniteNumber(value, fallback), 0.0, 120.0);
  }
  if (normalizedKey.endsWith("db")) {
    return clamp(toFiniteNumber(value, fallback), -120.0, 48.0);
  }
  if (normalizedKey === "ratio" || normalizedKey.endsWith("ratio")) {
    return clamp(toFiniteNumber(value, fallback), 1.0, 20.0);
  }
  if (normalizedKey.includes("semitones")) {
    return clamp(toFiniteNumber(value, fallback), -48.0, 48.0);
  }

  return toFiniteNumber(value, fallback);
}

function sanitizeLike(value, fallback, key = "") {
  if (Array.isArray(fallback)) {
    const source = Array.isArray(value) ? value : [];
    return fallback.map((entry, index) => sanitizeLike(source[index] ?? entry, entry, key));
  }
  if (fallback && typeof fallback === "object") {
    const source = value && typeof value === "object" && !Array.isArray(value) ? value : {};
    const output = {};
    for (const [childKey, childFallback] of Object.entries(fallback)) {
      output[childKey] = sanitizeLike(source[childKey] ?? childFallback, childFallback, childKey);
    }
    return output;
  }
  if (typeof fallback === "number") {
    return sanitizeNumberByKey(key, value, fallback);
  }
  if (typeof fallback === "boolean") {
    return value === undefined ? fallback : Boolean(value);
  }
  if (typeof fallback === "string") {
    return sanitizeStringByKey(key, value, fallback);
  }
  return value ?? fallback;
}

function applyLimits(value, limits) {
  if (!limits) {
    return value;
  }
  if (Array.isArray(value)) {
    if (!Array.isArray(limits)) {
      return value;
    }
    return value.map((entry, index) => applyLimits(entry, limits[index] ?? limits[limits.length - 1]));
  }
  if (value && typeof value === "object") {
    if (!limits || typeof limits !== "object" || Array.isArray(limits)) {
      return value;
    }
    const output = { ...value };
    for (const [key, entry] of Object.entries(value)) {
      output[key] = applyLimits(entry, limits[key]);
    }
    return output;
  }
  if (typeof value === "number" && limits && typeof limits === "object" && !Array.isArray(limits)) {
    const hasMin = Object.prototype.hasOwnProperty.call(limits, "min");
    const hasMax = Object.prototype.hasOwnProperty.call(limits, "max");
    let result = value;
    if (hasMin || hasMax) {
      const min = hasMin ? toFiniteNumber(limits.min, value) : -Infinity;
      const max = hasMax ? toFiniteNumber(limits.max, value) : Infinity;
      result = clamp(value, Math.min(min, max), Math.max(min, max));
    }
    if (limits.integer) {
      result = Math.round(result);
    }
    return result;
  }
  if (typeof value === "string" && limits && Array.isArray(limits.choices)) {
    const choices = limits.choices.map((entry) => String(entry));
    return choices.includes(value) ? value : String(choices[0] ?? value);
  }
  return value;
}

function formatWarningNumber(value) {
  if (!Number.isFinite(value)) {
    return String(value);
  }
  if (Math.abs(value) >= 1000 || Number.isInteger(value)) {
    return String(Number(value));
  }
  return Number(value).toFixed(3).replace(/\.?0+$/, "");
}

function formatWarningPath(path) {
  if (!Array.isArray(path) || path.length === 0) {
    return "value";
  }
  return path
    .map((entry) => (typeof entry === "number" ? `[${entry}]` : String(entry)))
    .join(".")
    .replace(/\.\[/g, "[");
}

function createLimitWarning(effectName, parameterPath, received, applied, min, max) {
  return {
    source: "javascript",
    type: "limit",
    effect: effectName,
    parameter: parameterPath,
    received,
    applied,
    min,
    max,
    message: `Warning: ${effectName} parameter "${parameterPath}" exceeded app limits. Allowed range: [${formatWarningNumber(min)}, ${formatWarningNumber(max)}]. Received: ${formatWarningNumber(received)}. Applied: ${formatWarningNumber(applied)}.`,
  };
}

function createChoiceWarning(effectName, parameterPath, received, applied, choices) {
  return {
    source: "javascript",
    type: "choice",
    effect: effectName,
    parameter: parameterPath,
    received,
    applied,
    choices,
    message: `Warning: ${effectName} parameter "${parameterPath}" used an unsupported choice. Allowed choices: ${choices.join(", ")}. Received: ${String(received)}. Applied: ${String(applied)}.`,
  };
}

function collectLimitWarnings(effectName, attemptedValue, appliedValue, limits, path = []) {
  if (!limits) {
    return [];
  }

  if (Array.isArray(appliedValue)) {
    if (!Array.isArray(limits)) {
      return [];
    }
    const attemptedList = Array.isArray(attemptedValue) ? attemptedValue : [];
    return appliedValue.flatMap((entry, index) =>
      collectLimitWarnings(
        effectName,
        attemptedList[index],
        entry,
        limits[index] ?? limits[limits.length - 1],
        path.concat(index),
      ),
    );
  }

  if (appliedValue && typeof appliedValue === "object") {
    if (!limits || typeof limits !== "object" || Array.isArray(limits)) {
      return [];
    }
    const attemptedObject =
      attemptedValue && typeof attemptedValue === "object" && !Array.isArray(attemptedValue)
        ? attemptedValue
        : {};
    const keys = Object.keys(limits).filter((key) => !["min", "max", "integer", "choices"].includes(key));
    return keys.flatMap((key) =>
      collectLimitWarnings(
        effectName,
        attemptedObject[key],
        appliedValue[key],
        limits[key],
        path.concat(key),
      ),
    );
  }

  if (typeof appliedValue === "number" && limits && typeof limits === "object" && !Array.isArray(limits)) {
    const hasMin = Object.prototype.hasOwnProperty.call(limits, "min");
    const hasMax = Object.prototype.hasOwnProperty.call(limits, "max");
    const received = Number(attemptedValue);
    if (!Number.isFinite(received)) {
      return [];
    }
    const min = hasMin ? toFiniteNumber(limits.min, received) : Number.NEGATIVE_INFINITY;
    const max = hasMax ? toFiniteNumber(limits.max, received) : Number.POSITIVE_INFINITY;
    const clamped = clamp(received, Math.min(min, max), Math.max(min, max));
    const normalized = limits.integer ? Math.round(clamped) : clamped;
    if (Math.abs(normalized - received) <= 1e-9) {
      return [];
    }
    return [
      createLimitWarning(
        effectName,
        formatWarningPath(path),
        received,
        appliedValue,
        Math.min(min, max),
        Math.max(min, max),
      ),
    ];
  }

  if (typeof appliedValue === "string" && limits && Array.isArray(limits.choices) && attemptedValue != null) {
    const received = String(attemptedValue);
    if (received === appliedValue) {
      return [];
    }
    const choices = limits.choices.map((entry) => String(entry));
    return [createChoiceWarning(effectName, formatWarningPath(path), received, appliedValue, choices)];
  }

  return [];
}

function humanizeEffectName(value) {
  return String(value)
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/_/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function normalizeParametricBands(options = {}) {
  const bands = Array.isArray(options.bands) ? options.bands : DEFAULT_DYNAMICS_CONFIG.parametricEq;
  return PARAMETRIC_BANDS.map((index) => {
    const band = bands[index - 1] || {};
    const fallback = DEFAULT_DYNAMICS_CONFIG.parametricEq[index - 1];
    return {
      enabled: Boolean(band.enabled ?? fallback.enabled),
      kind: String(band.kind ?? fallback.kind),
      frequencyHz: Number(band.frequencyHz ?? band.frequency_hz ?? fallback.frequencyHz),
      gainDb: Number(band.gainDb ?? band.gain_db ?? fallback.gainDb),
      q: Number(band.q ?? fallback.q),
      slope: Number(band.slope ?? fallback.slope),
      stages: Math.max(1, Math.round(Number(band.stages ?? fallback.stages))),
    };
  });
}

function normalizeGraphicEq(options = {}) {
  const bandsDb = Array.isArray(options.bandsDb)
    ? options.bandsDb
    : Array.isArray(options.bands)
      ? options.bands
      : [0.0, 0.0, 0.0, 0.0, 0.0];
  return {
    enabled: true,
    q: Number(options.q ?? DEFAULT_DYNAMICS_CONFIG.graphicEq.q),
    bandsDb: bandsDb.map((value) => Number(value)).slice(0, 5).concat(Array(Math.max(0, 5 - bandsDb.length)).fill(0.0)).slice(0, 5),
  };
}

function mergeStage(defaults, list, stageName) {
  const config = clone(defaults);
  for (const effect of list) {
    if (!effect || effect.stage !== stageName) {
      continue;
    }
    config[effect.key] = clone(effect.config);
  }
  return config;
}

export function buildEffectStateWithWarnings(effectList) {
  const list = Array.isArray(effectList) ? effectList.filter(Boolean) : [];
  const warnings = list.flatMap((effect) => (Array.isArray(effect.warnings) ? effect.warnings : []));
  const runtime = sanitizeLike(mergeStage(DEFAULT_RUNTIME_STATE, list, "runtime"), DEFAULT_RUNTIME_STATE, "runtime");
  if (runtime.timeCompression.enabled) {
    runtime.timeStretch.enabled = false;
  } else if (runtime.timeStretch.enabled) {
    runtime.timeCompression.enabled = false;
  }
  return {
    state: {
      runtime,
      basicConfig: sanitizeLike(mergeStage(DEFAULT_BASIC_CONFIG, list, "basicConfig"), DEFAULT_BASIC_CONFIG, "basicConfig"),
      colorTimeConfig: sanitizeLike(mergeStage(DEFAULT_COLOR_TIME_CONFIG, list, "colorTime"), DEFAULT_COLOR_TIME_CONFIG, "colorTime"),
      modernCreativeConfig: sanitizeLike(mergeStage(DEFAULT_MODERN_CREATIVE_CONFIG, list, "modernCreative"), DEFAULT_MODERN_CREATIVE_CONFIG, "modernCreative"),
      spectralSpatialConfig: sanitizeLike(mergeStage(DEFAULT_SPECTRAL_SPATIAL_CONFIG, list, "spectralSpatial"), DEFAULT_SPECTRAL_SPATIAL_CONFIG, "spectralSpatial"),
      dynamicsConfig: sanitizeLike(mergeStage(DEFAULT_DYNAMICS_CONFIG, list, "dynamics"), DEFAULT_DYNAMICS_CONFIG, "dynamics"),
      modulationConfig: sanitizeLike(mergeStage(DEFAULT_MODULATION_CONFIG, list, "modulation"), DEFAULT_MODULATION_CONFIG, "modulation"),
      spaceConfig: sanitizeLike(mergeStage(DEFAULT_SPACE_CONFIG, list, "space"), DEFAULT_SPACE_CONFIG, "space"),
    },
    warnings,
  };
}

export function buildEffectState(effectList) {
  return buildEffectStateWithWarnings(effectList).state;
}

function stageEffect(stage, key, defaults, normalize = (options) => ({ ...clone(defaults), ...clone(options), enabled: true })) {
  return (options = {}) => {
    const requestedConfig = normalize(options);
    const normalizedConfig = sanitizeLike(requestedConfig, defaults, key);
    return {
      stage,
      key,
      config: applyLimits(normalizedConfig, options.limits),
      _warningAttemptedConfig: requestedConfig,
      _nativeRequestedConfig: requestedConfig,
      _warningLimits: options.limits,
    };
  };
}

const EFFECT_BUILDERS = {
  gain: stageEffect("runtime", "inputGain", 1.0, (options) => Number(options.value ?? options.gain ?? 1.0)),
  output_level: stageEffect("runtime", "outputGain", 1.0, (options) => Number(options.value ?? options.gain ?? 1.0)),
  output_gain: stageEffect("runtime", "outputGain", 1.0, (options) => Number(options.value ?? options.gain ?? 1.0)),
  normalize: stageEffect("basicConfig", "normalize", DEFAULT_BASIC_CONFIG.normalize),
  fade_in: stageEffect("basicConfig", "fadeIn", DEFAULT_BASIC_CONFIG.fadeIn),
  fade_out: stageEffect("basicConfig", "fadeOut", DEFAULT_BASIC_CONFIG.fadeOut),
  crossfade: stageEffect("runtime", "crossfade", DEFAULT_RUNTIME_STATE.crossfade, (options) => ({ enabled: true, durationMs: Number(options.durationMs ?? options.duration_ms ?? 1200.0) })),
  trim: stageEffect("basicConfig", "trim", DEFAULT_BASIC_CONFIG.trim),
  cut: stageEffect("basicConfig", "cut", DEFAULT_BASIC_CONFIG.cut),
  silence_removal: stageEffect("basicConfig", "silenceRemoval", DEFAULT_BASIC_CONFIG.silenceRemoval),
  remove_silence: stageEffect("basicConfig", "silenceRemoval", DEFAULT_BASIC_CONFIG.silenceRemoval),
  reverse: stageEffect("basicConfig", "reverse", DEFAULT_BASIC_CONFIG.reverse),
  pan: stageEffect("runtime", "pan", 0.0, (options) => Number(options.value ?? options.pan ?? 0.0)),
  stereo_balance: stageEffect("runtime", "pan", 0.0, (options) => Number(options.value ?? options.pan ?? 0.0)),
  to_mono: stageEffect("runtime", "monoMix", 1.0, (options) => Number(options.mix ?? 1.0)),
  to_stereo: stageEffect("runtime", "monoMix", 0.0, (options) => Number(options.mix ?? 0.0)),
  remove_dc_offset: stageEffect("runtime", "dcBlock", true, (options) => Boolean(options.enabled ?? true)),
  dc_offset_removal: stageEffect("runtime", "dcBlock", true, (options) => Boolean(options.enabled ?? true)),
  compressor: stageEffect("dynamics", "compressor", DEFAULT_DYNAMICS_CONFIG.compressor),
  limiter: stageEffect("dynamics", "limiter", DEFAULT_DYNAMICS_CONFIG.limiter),
  expander: stageEffect("dynamics", "expander", DEFAULT_DYNAMICS_CONFIG.expander),
  noise_gate: stageEffect("dynamics", "noiseGate", DEFAULT_DYNAMICS_CONFIG.noiseGate),
  multiband_compressor: stageEffect("dynamics", "multibandCompressor", DEFAULT_DYNAMICS_CONFIG.multibandCompressor),
  deesser: stageEffect("dynamics", "deesser", DEFAULT_DYNAMICS_CONFIG.deesser),
  transient_shaper: stageEffect("dynamics", "transientShaper", DEFAULT_DYNAMICS_CONFIG.transientShaper),
  upward_compression: stageEffect("dynamics", "upwardCompression", DEFAULT_DYNAMICS_CONFIG.upwardCompression),
  downward_compression: stageEffect("dynamics", "downwardCompression", DEFAULT_DYNAMICS_CONFIG.downwardCompression),
  highpass: stageEffect("dynamics", "highpass", DEFAULT_DYNAMICS_CONFIG.highpass),
  lowpass: stageEffect("dynamics", "lowpass", DEFAULT_DYNAMICS_CONFIG.lowpass),
  bandpass: stageEffect("dynamics", "bandpass", DEFAULT_DYNAMICS_CONFIG.bandpass),
  notch: stageEffect("dynamics", "notch", DEFAULT_DYNAMICS_CONFIG.notch),
  low_shelf: stageEffect("dynamics", "lowShelf", DEFAULT_DYNAMICS_CONFIG.lowShelf),
  high_shelf: stageEffect("dynamics", "highShelf", DEFAULT_DYNAMICS_CONFIG.highShelf),
  resonant_filter: stageEffect("dynamics", "resonantFilter", DEFAULT_DYNAMICS_CONFIG.resonantFilter),
  dynamic_eq: stageEffect("dynamics", "dynamicEq", DEFAULT_DYNAMICS_CONFIG.dynamicEq),
  formant_filter: stageEffect("dynamics", "formantFilter", DEFAULT_DYNAMICS_CONFIG.formantFilter),
  parametric_eq: stageEffect("dynamics", "parametricEq", DEFAULT_DYNAMICS_CONFIG.parametricEq, normalizeParametricBands),
  graphic_eq: stageEffect("dynamics", "graphicEq", DEFAULT_DYNAMICS_CONFIG.graphicEq, normalizeGraphicEq),
  chorus: stageEffect("modulation", "chorus", DEFAULT_MODULATION_CONFIG.chorus),
  flanger: stageEffect("modulation", "flanger", DEFAULT_MODULATION_CONFIG.flanger),
  phaser: stageEffect("modulation", "phaser", DEFAULT_MODULATION_CONFIG.phaser),
  tremolo: stageEffect("modulation", "tremolo", DEFAULT_MODULATION_CONFIG.tremolo),
  vibrato: stageEffect("modulation", "vibrato", DEFAULT_MODULATION_CONFIG.vibrato),
  auto_pan: stageEffect("modulation", "autoPan", DEFAULT_MODULATION_CONFIG.autoPan),
  rotary_speaker: stageEffect("modulation", "rotarySpeaker", DEFAULT_MODULATION_CONFIG.rotarySpeaker),
  ring_modulation: stageEffect("modulation", "ringModulation", DEFAULT_MODULATION_CONFIG.ringModulation),
  frequency_shifter: stageEffect("modulation", "frequencyShifter", DEFAULT_MODULATION_CONFIG.frequencyShifter),
  delay: stageEffect("space", "delay", DEFAULT_SPACE_CONFIG.delay),
  echo: stageEffect("space", "echo", DEFAULT_SPACE_CONFIG.echo),
  ping_pong_delay: stageEffect("space", "pingPongDelay", DEFAULT_SPACE_CONFIG.pingPongDelay),
  multi_tap_delay: stageEffect("space", "multiTapDelay", DEFAULT_SPACE_CONFIG.multiTapDelay),
  slapback: stageEffect("space", "slapbackDelay", DEFAULT_SPACE_CONFIG.slapbackDelay),
  early_reflections: stageEffect("space", "earlyReflections", DEFAULT_SPACE_CONFIG.earlyReflections),
  room_reverb: stageEffect("space", "roomReverb", DEFAULT_SPACE_CONFIG.roomReverb),
  hall_reverb: stageEffect("space", "hallReverb", DEFAULT_SPACE_CONFIG.hallReverb),
  plate_reverb: stageEffect("space", "plateReverb", DEFAULT_SPACE_CONFIG.plateReverb),
  convolution_reverb: stageEffect("space", "convolutionReverb", DEFAULT_SPACE_CONFIG.convolutionReverb),
  distortion: stageEffect("colorTime", "distortion", DEFAULT_COLOR_TIME_CONFIG.distortion),
  overdrive: stageEffect("colorTime", "overdrive", DEFAULT_COLOR_TIME_CONFIG.overdrive),
  fuzz: stageEffect("colorTime", "fuzz", DEFAULT_COLOR_TIME_CONFIG.fuzz),
  bitcrusher: stageEffect("colorTime", "bitcrusher", DEFAULT_COLOR_TIME_CONFIG.bitcrusher),
  waveshaper: stageEffect("colorTime", "waveshaper", DEFAULT_COLOR_TIME_CONFIG.waveshaper),
  tube_saturation: stageEffect("colorTime", "tubeSaturation", DEFAULT_COLOR_TIME_CONFIG.tubeSaturation),
  tape_saturation: stageEffect("colorTime", "tapeSaturation", DEFAULT_COLOR_TIME_CONFIG.tapeSaturation),
  soft_clipping: stageEffect("colorTime", "softClipping", DEFAULT_COLOR_TIME_CONFIG.softClipping),
  hard_clipping: stageEffect("colorTime", "hardClipping", DEFAULT_COLOR_TIME_CONFIG.hardClipping),
  pitch_shift: stageEffect("colorTime", "pitchShift", DEFAULT_COLOR_TIME_CONFIG.pitchShift),
  time_stretch: stageEffect("runtime", "timeStretch", DEFAULT_RUNTIME_STATE.timeStretch, (options) => ({ enabled: true, rate: Number(options.rate ?? 0.9) })),
  time_compression: stageEffect("runtime", "timeCompression", DEFAULT_RUNTIME_STATE.timeCompression, (options) => ({ enabled: true, rate: Number(options.rate ?? 1.15) })),
  auto_tune: stageEffect("colorTime", "autoTune", DEFAULT_COLOR_TIME_CONFIG.autoTune),
  harmonizer: stageEffect("colorTime", "harmonizer", DEFAULT_COLOR_TIME_CONFIG.harmonizer),
  octaver: stageEffect("colorTime", "octaver", DEFAULT_COLOR_TIME_CONFIG.octaver),
  formant_shifting: stageEffect("colorTime", "formantShifting", DEFAULT_COLOR_TIME_CONFIG.formantShifting),
  noise_reduction: stageEffect("modernCreative", "noiseReduction", DEFAULT_MODERN_CREATIVE_CONFIG.noiseReduction),
  voice_isolation: stageEffect("modernCreative", "voiceIsolation", DEFAULT_MODERN_CREATIVE_CONFIG.voiceIsolation),
  source_separation: stageEffect("modernCreative", "sourceSeparation", DEFAULT_MODERN_CREATIVE_CONFIG.sourceSeparation),
  de_reverb: stageEffect("modernCreative", "deReverb", DEFAULT_MODERN_CREATIVE_CONFIG.deReverb),
  de_echo: stageEffect("modernCreative", "deEcho", DEFAULT_MODERN_CREATIVE_CONFIG.deEcho),
  spectral_repair: stageEffect("modernCreative", "spectralRepair", DEFAULT_MODERN_CREATIVE_CONFIG.spectralRepair),
  ai_enhancer: stageEffect("modernCreative", "aiEnhancer", DEFAULT_MODERN_CREATIVE_CONFIG.aiEnhancer),
  speech_enhancement: stageEffect("modernCreative", "speechEnhancement", DEFAULT_MODERN_CREATIVE_CONFIG.speechEnhancement),
  glitch_effect: stageEffect("modernCreative", "glitchEffect", DEFAULT_MODERN_CREATIVE_CONFIG.glitchEffect),
  stutter: stageEffect("modernCreative", "stutter", DEFAULT_MODERN_CREATIVE_CONFIG.stutter),
  tape_stop: stageEffect("modernCreative", "tapeStop", DEFAULT_MODERN_CREATIVE_CONFIG.tapeStop),
  reverse_reverb: stageEffect("modernCreative", "reverseReverb", DEFAULT_MODERN_CREATIVE_CONFIG.reverseReverb),
  granular_synthesis: stageEffect("modernCreative", "granularSynthesis", DEFAULT_MODERN_CREATIVE_CONFIG.granularSynthesis),
  time_slicing: stageEffect("modernCreative", "timeSlicing", DEFAULT_MODERN_CREATIVE_CONFIG.timeSlicing),
  random_pitch_mod: stageEffect("modernCreative", "randomPitchMod", DEFAULT_MODERN_CREATIVE_CONFIG.randomPitchMod),
  vinyl_effect: stageEffect("modernCreative", "vinylEffect", DEFAULT_MODERN_CREATIVE_CONFIG.vinylEffect),
  radio_effect: stageEffect("modernCreative", "radioEffect", DEFAULT_MODERN_CREATIVE_CONFIG.radioEffect),
  telephone_effect: stageEffect("modernCreative", "telephoneEffect", DEFAULT_MODERN_CREATIVE_CONFIG.telephoneEffect),
  retro_8bit: stageEffect("modernCreative", "retro8bit", DEFAULT_MODERN_CREATIVE_CONFIG.retro8bit),
  slow_motion_extreme: stageEffect("modernCreative", "slowMotionExtreme", DEFAULT_MODERN_CREATIVE_CONFIG.slowMotionExtreme),
  robot_voice: stageEffect("modernCreative", "robotVoice", DEFAULT_MODERN_CREATIVE_CONFIG.robotVoice),
  alien_voice: stageEffect("modernCreative", "alienVoice", DEFAULT_MODERN_CREATIVE_CONFIG.alienVoice),
  fft_filter: stageEffect("spectralSpatial", "fftFilter", DEFAULT_SPECTRAL_SPATIAL_CONFIG.fftFilter),
  spectral_gating: stageEffect("spectralSpatial", "spectralGating", DEFAULT_SPECTRAL_SPATIAL_CONFIG.spectralGating),
  spectral_blur: stageEffect("spectralSpatial", "spectralBlur", DEFAULT_SPECTRAL_SPATIAL_CONFIG.spectralBlur),
  spectral_freeze: stageEffect("spectralSpatial", "spectralFreeze", DEFAULT_SPECTRAL_SPATIAL_CONFIG.spectralFreeze),
  spectral_morphing: stageEffect("spectralSpatial", "spectralMorphing", DEFAULT_SPECTRAL_SPATIAL_CONFIG.spectralMorphing),
  phase_vocoder: stageEffect("spectralSpatial", "phaseVocoder", DEFAULT_SPECTRAL_SPATIAL_CONFIG.phaseVocoder),
  harmonic_percussive_separation: stageEffect("spectralSpatial", "harmonicPercussiveSeparation", DEFAULT_SPECTRAL_SPATIAL_CONFIG.harmonicPercussiveSeparation),
  spectral_delay: stageEffect("spectralSpatial", "spectralDelay", DEFAULT_SPECTRAL_SPATIAL_CONFIG.spectralDelay),
  stereo_widening: stageEffect("spectralSpatial", "stereoWidening", DEFAULT_SPECTRAL_SPATIAL_CONFIG.stereoWidening),
  mid_side_processing: stageEffect("spectralSpatial", "midSideProcessing", DEFAULT_SPECTRAL_SPATIAL_CONFIG.midSideProcessing),
  stereo_imager: stageEffect("spectralSpatial", "stereoImager", DEFAULT_SPECTRAL_SPATIAL_CONFIG.stereoImager),
  binaural_effect: stageEffect("spectralSpatial", "binauralEffect", DEFAULT_SPECTRAL_SPATIAL_CONFIG.binauralEffect),
  spatial_positioning: stageEffect("spectralSpatial", "spatialPositioning", DEFAULT_SPECTRAL_SPATIAL_CONFIG.spatialPositioning),
  hrtf_simulation: stageEffect("spectralSpatial", "hrtfSimulation", DEFAULT_SPECTRAL_SPATIAL_CONFIG.hrtfSimulation),
};

const EFFECT_LABELS = {
  gain: "Gain (volume)",
  output_level: "Output level",
  output_gain: "Output gain",
  fade_in: "Fade in",
  fade_out: "Fade out",
  silence_removal: "Silence removal",
  remove_silence: "Silence removal",
  pan: "Stereo balance (pan)",
  stereo_balance: "Stereo balance (pan)",
  to_mono: "To mono",
  to_stereo: "To stereo",
  remove_dc_offset: "DC offset removal",
  dc_offset_removal: "DC offset removal",
  noise_gate: "Noise Gate",
  multiband_compressor: "Multiband Compressor",
  transient_shaper: "Transient shaper",
  upward_compression: "Upward compression",
  downward_compression: "Downward compression",
  low_shelf: "Low shelf",
  high_shelf: "High shelf",
  dynamic_eq: "Dynamic EQ",
  formant_filter: "Formant filter",
  parametric_eq: "Parametric equalizer",
  graphic_eq: "Graphic EQ",
  auto_pan: "Auto-pan",
  rotary_speaker: "Rotary speaker (Leslie)",
  ring_modulation: "Ring modulation",
  frequency_shifter: "Frequency shifter",
  ping_pong_delay: "Ping-pong delay",
  multi_tap_delay: "Multi-tap delay",
  room_reverb: "Room reverb",
  hall_reverb: "Hall reverb",
  plate_reverb: "Plate reverb",
  convolution_reverb: "Convolution reverb (IR)",
  tube_saturation: "Tube saturation",
  tape_saturation: "Tape saturation",
  soft_clipping: "Soft clipping",
  hard_clipping: "Hard clipping",
  pitch_shift: "Pitch shift",
  time_stretch: "Time stretch",
  time_compression: "Time compression",
  auto_tune: "Auto-tune (pitch correction)",
  formant_shifting: "Formant shifting",
  noise_reduction: "Noise reduction",
  voice_isolation: "Voice isolation",
  source_separation: "Source separation",
  de_reverb: "De-reverb",
  de_echo: "De-echo",
  spectral_repair: "Spectral repair",
  ai_enhancer: "AI enhancer",
  speech_enhancement: "Speech enhancement",
  glitch_effect: "Glitch effect",
  tape_stop: "Tape stop",
  reverse_reverb: "Reverse reverb",
  granular_synthesis: "Granular synthesis",
  time_slicing: "Time slicing",
  random_pitch_mod: "Random pitch mod",
  vinyl_effect: "Vinyl effect",
  radio_effect: "Radio effect",
  telephone_effect: "Telephone effect",
  retro_8bit: "8-bit / retro sound",
  slow_motion_extreme: "Slow motion extreme",
  robot_voice: "Robot voice",
  alien_voice: "Alien voice",
  fft_filter: "FFT filter",
  spectral_gating: "Spectral gating",
  spectral_blur: "Spectral blur",
  spectral_freeze: "Spectral freeze",
  spectral_morphing: "Spectral morphing",
  phase_vocoder: "Phase vocoder",
  harmonic_percussive_separation: "Harmonic/percussive separation",
  spectral_delay: "Spectral delay",
  stereo_widening: "Stereo widening",
  mid_side_processing: "Mid/Side processing",
  stereo_imager: "Stereo imager",
  binaural_effect: "Binaural effect",
  spatial_positioning: "3D audio positioning",
  hrtf_simulation: "HRTF simulation",
};

export const effects = Object.fromEntries(
  Object.entries(EFFECT_BUILDERS).map(([id, builder]) => [
    id,
    (options = {}) => {
      const built = builder(options);
      const effectName = EFFECT_LABELS[id] || humanizeEffectName(id);
      return {
        stage: built.stage,
        key: built.key,
        config: built.config,
        id,
        name: effectName,
        requestedConfig: built._nativeRequestedConfig,
        warnings: collectLimitWarnings(effectName, built._warningAttemptedConfig, built.config, built._warningLimits),
      };
    },
  ]),
);
