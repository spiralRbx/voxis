import { createVoxisRealtimePlayer, effects } from "./api/voxis-realtime.js";

const $ = (selector) => document.querySelector(selector);

const elements = {
  status: $("#editor-status"),
  mode: $("#editor-mode"),
  irName: $("#editor-ir-name"),
  crossfadeName: $("#editor-crossfade-name"),
  activeEffects: $("#editor-active-effects"),
  playerHost: $("#api-player-host"),
  start: $("#editor-start"),
  useMic: $("#editor-use-mic"),
  stopMic: $("#editor-stop-mic"),
  reset: $("#editor-reset"),
  fileInput: $("#editor-file-input"),
  crossfadeInput: $("#editor-crossfade-input"),
  irInput: $("#editor-ir-input"),
  gain: $("#gain-range"),
  gainValue: $("#gain-value"),
  outputLevel: $("#output-level-range"),
  outputLevelValue: $("#output-level-value"),
  pan: $("#pan-range"),
  panValue: $("#pan-value"),
  compressorEnabled: $("#compressor-enabled"),
  compressorThreshold: $("#compressor-threshold-range"),
  compressorThresholdValue: $("#compressor-threshold-value"),
  compressorRatio: $("#compressor-ratio-range"),
  compressorRatioValue: $("#compressor-ratio-value"),
  highpassEnabled: $("#highpass-enabled"),
  highpassFrequency: $("#highpass-frequency-range"),
  highpassFrequencyValue: $("#highpass-frequency-value"),
  highpassQ: $("#highpass-q-range"),
  highpassQValue: $("#highpass-q-value"),
  chorusEnabled: $("#chorus-enabled"),
  chorusMix: $("#chorus-mix-range"),
  chorusMixValue: $("#chorus-mix-value"),
  chorusRate: $("#chorus-rate-range"),
  chorusRateValue: $("#chorus-rate-value"),
  hallEnabled: $("#hall-enabled"),
  hallMix: $("#hall-mix-range"),
  hallMixValue: $("#hall-mix-value"),
  hallDecay: $("#hall-decay-range"),
  hallDecayValue: $("#hall-decay-value"),
  overdriveEnabled: $("#overdrive-enabled"),
  overdriveDrive: $("#overdrive-drive-range"),
  overdriveDriveValue: $("#overdrive-drive-value"),
  overdriveMix: $("#overdrive-mix-range"),
  overdriveMixValue: $("#overdrive-mix-value"),
  pitchEnabled: $("#pitch-enabled"),
  pitchSemitones: $("#pitch-semitones-range"),
  pitchSemitonesValue: $("#pitch-semitones-value"),
  pitchMix: $("#pitch-mix-range"),
  pitchMixValue: $("#pitch-mix-value"),
  noiseReductionEnabled: $("#noise-reduction-enabled"),
  noiseReductionStrength: $("#noise-reduction-strength-range"),
  noiseReductionStrengthValue: $("#noise-reduction-strength-value"),
  glitchEnabled: $("#glitch-enabled"),
  glitchSlice: $("#glitch-slice-range"),
  glitchSliceValue: $("#glitch-slice-value"),
  glitchMix: $("#glitch-mix-range"),
  glitchMixValue: $("#glitch-mix-value"),
  fftEnabled: $("#fft-enabled"),
  fftLow: $("#fft-low-range"),
  fftLowValue: $("#fft-low-value"),
  fftHigh: $("#fft-high-range"),
  fftHighValue: $("#fft-high-value"),
  spatialEnabled: $("#spatial-enabled"),
  spatialWidth: $("#spatial-width-range"),
  spatialWidthValue: $("#spatial-width-value"),
  spatialAzimuth: $("#spatial-azimuth-range"),
  spatialAzimuthValue: $("#spatial-azimuth-value"),
};

const defaults = {
  gain: "1",
  outputLevel: "1",
  pan: "0",
  compressorEnabled: false,
  compressorThreshold: "-18",
  compressorRatio: "3",
  highpassEnabled: false,
  highpassFrequency: "90",
  highpassQ: "0.71",
  chorusEnabled: false,
  chorusMix: "0.35",
  chorusRate: "0.9",
  hallEnabled: false,
  hallMix: "0.2",
  hallDecay: "1.8",
  overdriveEnabled: false,
  overdriveDrive: "1.8",
  overdriveMix: "0.8",
  pitchEnabled: false,
  pitchSemitones: "0",
  pitchMix: "0.45",
  noiseReductionEnabled: false,
  noiseReductionStrength: "0.5",
  glitchEnabled: false,
  glitchSlice: "60",
  glitchMix: "0.45",
  fftEnabled: false,
  fftLow: "90",
  fftHigh: "9000",
  spatialEnabled: false,
  spatialWidth: "1.25",
  spatialAzimuth: "30",
};

let player = null;
let applyFrame = 0;
let hasCrossfadePartner = false;
let hasConvolutionIr = false;

function setStatus(text) {
  elements.status.textContent = text;
}

function formatPercent(value) {
  return `${Math.round(Number(value) * 100)}%`;
}

function updateOutputs() {
  elements.gainValue.textContent = `${Number(elements.gain.value).toFixed(2)}x`;
  elements.outputLevelValue.textContent = `${Number(elements.outputLevel.value).toFixed(2)}x`;
  elements.panValue.textContent = Number(elements.pan.value).toFixed(2);
  elements.compressorThresholdValue.textContent = `${Number(elements.compressorThreshold.value).toFixed(1)} dB`;
  elements.compressorRatioValue.textContent = `${Number(elements.compressorRatio.value).toFixed(1)}:1`;
  elements.highpassFrequencyValue.textContent = `${Math.round(Number(elements.highpassFrequency.value))} Hz`;
  elements.highpassQValue.textContent = Number(elements.highpassQ.value).toFixed(2);
  elements.chorusMixValue.textContent = formatPercent(elements.chorusMix.value);
  elements.chorusRateValue.textContent = `${Number(elements.chorusRate.value).toFixed(2)} Hz`;
  elements.hallMixValue.textContent = formatPercent(elements.hallMix.value);
  elements.hallDecayValue.textContent = `${Number(elements.hallDecay.value).toFixed(2)} s`;
  elements.overdriveDriveValue.textContent = Number(elements.overdriveDrive.value).toFixed(2);
  elements.overdriveMixValue.textContent = formatPercent(elements.overdriveMix.value);
  elements.pitchSemitonesValue.textContent = `${Number(elements.pitchSemitones.value).toFixed(1)} st`;
  elements.pitchMixValue.textContent = formatPercent(elements.pitchMix.value);
  elements.noiseReductionStrengthValue.textContent = formatPercent(elements.noiseReductionStrength.value);
  elements.glitchSliceValue.textContent = `${Math.round(Number(elements.glitchSlice.value))} ms`;
  elements.glitchMixValue.textContent = formatPercent(elements.glitchMix.value);
  elements.fftLowValue.textContent = `${Math.round(Number(elements.fftLow.value))} Hz`;
  elements.fftHighValue.textContent = `${Math.round(Number(elements.fftHigh.value))} Hz`;
  elements.spatialWidthValue.textContent = `${Number(elements.spatialWidth.value).toFixed(2)}x`;
  elements.spatialAzimuthValue.textContent = `${Math.round(Number(elements.spatialAzimuth.value))}°`;
}

async function ensurePlayer() {
  if (player) {
    return player;
  }
  player = await createVoxisRealtimePlayer({ container: elements.playerHost });
  setStatus("Engine ready");
  return player;
}

function buildEffects() {
  const list = [
    effects.gain({ value: Number(elements.gain.value) }),
    effects.output_level({ value: Number(elements.outputLevel.value) }),
    effects.pan({ value: Number(elements.pan.value) }),
  ];

  if (hasCrossfadePartner) {
    list.push(effects.crossfade({ durationMs: 1200 }));
  }
  if (elements.compressorEnabled.checked) {
    list.push(
      effects.compressor({
        thresholdDb: Number(elements.compressorThreshold.value),
        ratio: Number(elements.compressorRatio.value),
        makeupDb: 0.0,
      }),
    );
  }
  if (elements.highpassEnabled.checked) {
    list.push(
      effects.highpass({
        frequencyHz: Number(elements.highpassFrequency.value),
        q: Number(elements.highpassQ.value),
      }),
    );
  }
  if (elements.chorusEnabled.checked) {
    list.push(
      effects.chorus({
        mix: Number(elements.chorusMix.value),
        rateHz: Number(elements.chorusRate.value),
      }),
    );
  }
  if (elements.hallEnabled.checked) {
    if (hasConvolutionIr) {
      list.push(effects.convolution_reverb({ mix: Number(elements.hallMix.value), normalizeIr: true }));
    } else {
      list.push(
        effects.hall_reverb({
          mix: Number(elements.hallMix.value),
          decaySeconds: Number(elements.hallDecay.value),
        }),
      );
    }
  }
  if (elements.overdriveEnabled.checked) {
    list.push(
      effects.overdrive({
        drive: Number(elements.overdriveDrive.value),
        mix: Number(elements.overdriveMix.value),
      }),
    );
  }
  if (elements.pitchEnabled.checked) {
    list.push(
      effects.pitch_shift({
        semitones: Number(elements.pitchSemitones.value),
        mix: Number(elements.pitchMix.value),
      }),
    );
  }
  if (elements.noiseReductionEnabled.checked) {
    list.push(
      effects.noise_reduction({
        strength: Number(elements.noiseReductionStrength.value),
      }),
    );
  }
  if (elements.glitchEnabled.checked) {
    list.push(
      effects.glitch_effect({
        sliceMs: Number(elements.glitchSlice.value),
        mix: Number(elements.glitchMix.value),
      }),
    );
  }
  if (elements.fftEnabled.checked) {
    list.push(
      effects.fft_filter({
        lowHz: Number(elements.fftLow.value),
        highHz: Number(elements.fftHigh.value),
        mix: 1.0,
      }),
    );
  }
  if (elements.spatialEnabled.checked) {
    list.push(
      effects.stereo_widening({
        amount: Number(elements.spatialWidth.value),
      }),
    );
    list.push(
      effects.hrtf_simulation({
        azimuthDeg: Number(elements.spatialAzimuth.value),
        elevationDeg: 0.0,
        distance: 1.0,
      }),
    );
  }

  return list;
}

function updateActiveEffects(list) {
  elements.activeEffects.textContent = list.map((effect) => effect.name).join(", ");
}

async function applyEffectsNow() {
  updateOutputs();
  const list = buildEffects();
  updateActiveEffects(list);
  if (!player) {
    return;
  }
  player.setEffects(list);
}

function scheduleApply() {
  if (applyFrame) {
    cancelAnimationFrame(applyFrame);
  }
  applyFrame = requestAnimationFrame(() => {
    applyFrame = 0;
    applyEffectsNow().catch((error) => {
      console.error(error);
      setStatus("Effect update failed");
    });
  });
}

function resetEditor() {
  elements.gain.value = defaults.gain;
  elements.outputLevel.value = defaults.outputLevel;
  elements.pan.value = defaults.pan;
  elements.compressorEnabled.checked = defaults.compressorEnabled;
  elements.compressorThreshold.value = defaults.compressorThreshold;
  elements.compressorRatio.value = defaults.compressorRatio;
  elements.highpassEnabled.checked = defaults.highpassEnabled;
  elements.highpassFrequency.value = defaults.highpassFrequency;
  elements.highpassQ.value = defaults.highpassQ;
  elements.chorusEnabled.checked = defaults.chorusEnabled;
  elements.chorusMix.value = defaults.chorusMix;
  elements.chorusRate.value = defaults.chorusRate;
  elements.hallEnabled.checked = defaults.hallEnabled;
  elements.hallMix.value = defaults.hallMix;
  elements.hallDecay.value = defaults.hallDecay;
  elements.overdriveEnabled.checked = defaults.overdriveEnabled;
  elements.overdriveDrive.value = defaults.overdriveDrive;
  elements.overdriveMix.value = defaults.overdriveMix;
  elements.pitchEnabled.checked = defaults.pitchEnabled;
  elements.pitchSemitones.value = defaults.pitchSemitones;
  elements.pitchMix.value = defaults.pitchMix;
  elements.noiseReductionEnabled.checked = defaults.noiseReductionEnabled;
  elements.noiseReductionStrength.value = defaults.noiseReductionStrength;
  elements.glitchEnabled.checked = defaults.glitchEnabled;
  elements.glitchSlice.value = defaults.glitchSlice;
  elements.glitchMix.value = defaults.glitchMix;
  elements.fftEnabled.checked = defaults.fftEnabled;
  elements.fftLow.value = defaults.fftLow;
  elements.fftHigh.value = defaults.fftHigh;
  elements.spatialEnabled.checked = defaults.spatialEnabled;
  elements.spatialWidth.value = defaults.spatialWidth;
  elements.spatialAzimuth.value = defaults.spatialAzimuth;
  updateOutputs();
}

elements.start.addEventListener("click", async () => {
  try {
    await ensurePlayer();
    await applyEffectsNow();
  } catch (error) {
    console.error(error);
    setStatus("Engine failed");
  }
});

elements.fileInput.addEventListener("change", async (event) => {
  const [file] = event.target.files || [];
  if (!file) {
    return;
  }
  try {
    const instance = await ensurePlayer();
    await instance.loadFile(file);
    elements.mode.textContent = `File: ${file.name}`;
    setStatus("Main source loaded");
    await applyEffectsNow();
  } catch (error) {
    console.error(error);
    setStatus("Main source failed");
  }
});

elements.crossfadeInput.addEventListener("change", async (event) => {
  const [file] = event.target.files || [];
  if (!file) {
    hasCrossfadePartner = false;
    elements.crossfadeName.textContent = "No partner loaded";
    scheduleApply();
    return;
  }
  try {
    const instance = await ensurePlayer();
    await instance.loadCrossfadePartnerFile(file);
    hasCrossfadePartner = true;
    elements.crossfadeName.textContent = file.name;
    setStatus("Crossfade partner loaded");
    await applyEffectsNow();
  } catch (error) {
    console.error(error);
    setStatus("Crossfade load failed");
  }
});

elements.irInput.addEventListener("change", async (event) => {
  const [file] = event.target.files || [];
  if (!file) {
    hasConvolutionIr = false;
    elements.irName.textContent = "No IR loaded";
    if (player) {
      player.clearConvolutionIr();
    }
    scheduleApply();
    return;
  }
  try {
    const instance = await ensurePlayer();
    await instance.loadConvolutionIrFile(file, true);
    hasConvolutionIr = true;
    elements.irName.textContent = file.name;
    setStatus("Convolution IR loaded");
    await applyEffectsNow();
  } catch (error) {
    console.error(error);
    setStatus("IR load failed");
  }
});

elements.useMic.addEventListener("click", async () => {
  try {
    const instance = await ensurePlayer();
    await instance.useMicrophone();
    elements.mode.textContent = "Microphone";
    setStatus("Microphone active");
    await applyEffectsNow();
  } catch (error) {
    console.error(error);
    setStatus("Microphone unavailable");
  }
});

elements.stopMic.addEventListener("click", () => {
  if (!player) {
    return;
  }
  player.stopMicrophone();
  elements.mode.textContent = "Microphone stopped";
  setStatus("Microphone stopped");
});

elements.reset.addEventListener("click", async () => {
  resetEditor();
  if (player) {
    player.clearEffects();
  }
  setStatus("Editor reset");
  await applyEffectsNow();
});

[
  elements.gain,
  elements.outputLevel,
  elements.pan,
  elements.compressorEnabled,
  elements.compressorThreshold,
  elements.compressorRatio,
  elements.highpassEnabled,
  elements.highpassFrequency,
  elements.highpassQ,
  elements.chorusEnabled,
  elements.chorusMix,
  elements.chorusRate,
  elements.hallEnabled,
  elements.hallMix,
  elements.hallDecay,
  elements.overdriveEnabled,
  elements.overdriveDrive,
  elements.overdriveMix,
  elements.pitchEnabled,
  elements.pitchSemitones,
  elements.pitchMix,
  elements.noiseReductionEnabled,
  elements.noiseReductionStrength,
  elements.glitchEnabled,
  elements.glitchSlice,
  elements.glitchMix,
  elements.fftEnabled,
  elements.fftLow,
  elements.fftHigh,
  elements.spatialEnabled,
  elements.spatialWidth,
  elements.spatialAzimuth,
].forEach((element) => {
  element.addEventListener("input", scheduleApply);
  element.addEventListener("change", scheduleApply);
});

resetEditor();
updateOutputs();
updateActiveEffects(buildEffects());
