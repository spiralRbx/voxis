import { createSpaceRack } from "./realtime-space.js";
import { DEFAULT_TRANSPORT, buildEffectState, buildEffectStateWithWarnings } from "./voxis-realtime-effects.js";

const DEFAULT_PROCESSOR_BASE_URL = new URL(".", import.meta.url).href.replace(/\/$/, "");
const DEFAULT_WASM_URL = new URL("./voxis-realtime-dynamics.wasm", import.meta.url).href;
const textDecoder = new TextDecoder("utf-8");
const STAGE_CONFIG_KEY = {
  runtime: "runtime",
  basicConfig: "basicConfig",
  colorTime: "colorTimeConfig",
  modernCreative: "modernCreativeConfig",
  spectralSpatial: "spectralSpatialConfig",
  dynamics: "dynamicsConfig",
  modulation: "modulationConfig",
  space: "spaceConfig",
};

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function resolveElement(elementOrSelector) {
  if (!elementOrSelector) {
    return null;
  }
  if (typeof elementOrSelector === "string") {
    return document.querySelector(elementOrSelector);
  }
  return elementOrSelector;
}

function createAudioElement(className = "voxis-realtime-audio") {
  const audio = document.createElement("audio");
  audio.controls = true;
  audio.preload = "metadata";
  audio.className = className;
  return audio;
}

function dispatchWarningEvent(target, detail) {
  if (!target || typeof target.dispatchEvent !== "function" || typeof CustomEvent !== "function") {
    return;
  }
  target.dispatchEvent(new CustomEvent("voxis-warning", { detail }));
}

async function loadWasm(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to load Voxis realtime WASM: ${response.status}`);
  }
  return response.arrayBuffer();
}

function readWasmString(exports, pointer, length) {
  if (!exports?.memory || !pointer || length <= 0) {
    return "";
  }
  return textDecoder.decode(new Uint8Array(exports.memory.buffer, pointer, length));
}

async function loadNativeRealtimeMetadata(wasmBytes) {
  const { instance } = await WebAssembly.instantiate(wasmBytes, {
    env: {
      emscripten_notify_memory_growth() {},
    },
  });
  if (typeof instance.exports.__wasm_call_ctors === "function") {
    instance.exports.__wasm_call_ctors();
  }
  const pointer = instance.exports.voxis_rt_get_limits_json_ptr?.() ?? 0;
  const length = instance.exports.voxis_rt_get_limits_json_length?.() ?? 0;
  const jsonText = readWasmString(instance.exports, pointer, length).trim();
  return jsonText ? JSON.parse(jsonText) : null;
}

function normalizeNativeRuleKey(value) {
  return String(value ?? "")
    .replace(/[^a-z0-9]/gi, "")
    .toLowerCase();
}

function formatNativeRulePath(path) {
  if (!Array.isArray(path) || path.length === 0) {
    return "value";
  }
  return path
    .map((entry) => (typeof entry === "number" ? `[${entry}]` : String(entry)))
    .join(".")
    .replace(/\.\[/g, "[");
}

function formatNativeRuleNumber(value) {
  if (!Number.isFinite(value)) {
    return String(value);
  }
  if (Math.abs(value) >= 1000 || Number.isInteger(value)) {
    return String(Number(value));
  }
  return Number(value).toFixed(3).replace(/\.?0+$/, "");
}

function getNativeNumericRule(nativeLimits, key) {
  const normalizedKey = normalizeNativeRuleKey(key);
  const exactRules = nativeLimits?.parameterRules ?? {};
  if (exactRules[normalizedKey]) {
    return exactRules[normalizedKey];
  }
  const suffixRules = nativeLimits?.suffixRules ?? {};
  const suffixEntries = Object.entries(suffixRules).sort((left, right) => right[0].length - left[0].length);
  for (const [suffix, rule] of suffixEntries) {
    if (normalizedKey.endsWith(suffix)) {
      return rule;
    }
  }
  return null;
}

function getNativeChoiceRule(nativeLimits, key) {
  const normalizedKey = normalizeNativeRuleKey(key);
  return nativeLimits?.choiceRules?.[normalizedKey] ?? null;
}

function createNativeLimitWarning(effectName, parameterPath, received, applied, min, max) {
  return {
    source: "native",
    type: "limit",
    effect: effectName,
    parameter: parameterPath,
    received,
    applied,
    min,
    max,
    message: `Warning: ${effectName} parameter "${parameterPath}" exceeded native realtime limits. Allowed range: [${formatNativeRuleNumber(min)}, ${formatNativeRuleNumber(max)}]. Received: ${formatNativeRuleNumber(received)}. Applied: ${formatNativeRuleNumber(applied)}.`,
  };
}

function createNativeChoiceWarning(effectName, parameterPath, received, applied, choices) {
  return {
    source: "native",
    type: "choice",
    effect: effectName,
    parameter: parameterPath,
    received,
    applied,
    choices,
    message: `Warning: ${effectName} parameter "${parameterPath}" used an unsupported native choice. Allowed choices: ${choices.join(", ")}. Received: ${String(received)}. Applied: ${String(applied)}.`,
  };
}

function createNativeInvalidWarning(effectName, parameterPath, applied, min, max) {
  return {
    source: "native",
    type: "limit",
    effect: effectName,
    parameter: parameterPath,
    received: null,
    applied,
    min,
    max,
    message: `Warning: ${effectName} parameter "${parameterPath}" received a non-finite value. Allowed range: [${formatNativeRuleNumber(min)}, ${formatNativeRuleNumber(max)}]. Applied: ${formatNativeRuleNumber(applied)}.`,
  };
}

function applyNativeMetadataValue({
  effectName,
  key,
  requestedValue,
  currentValue,
  nativeLimits,
  warnings,
  path = [],
}) {
  if (Array.isArray(currentValue)) {
    const requestedList = Array.isArray(requestedValue) ? requestedValue : [];
    return currentValue.map((entry, index) =>
      applyNativeMetadataValue({
        effectName,
        key,
        requestedValue: requestedList[index],
        currentValue: entry,
        nativeLimits,
        warnings,
        path: path.concat(index),
      }),
    );
  }

  if (currentValue && typeof currentValue === "object") {
    const requestedObject =
      requestedValue && typeof requestedValue === "object" && !Array.isArray(requestedValue)
        ? requestedValue
        : {};
    const output = Array.isArray(currentValue) ? [] : {};
    for (const [childKey, childValue] of Object.entries(currentValue)) {
      output[childKey] = applyNativeMetadataValue({
        effectName,
        key: childKey,
        requestedValue: requestedObject[childKey],
        currentValue: childValue,
        nativeLimits,
        warnings,
        path: path.concat(childKey),
      });
    }
    return output;
  }

  if (typeof currentValue === "number") {
    const rule = getNativeNumericRule(nativeLimits, key);
    if (!rule) {
      return currentValue;
    }
    const min = Number(rule.min ?? currentValue);
    const max = Number(rule.max ?? currentValue);
    const sourceValue = Number(requestedValue);
    const currentNumber = Number(currentValue);
    let applied = Number.isFinite(currentNumber) ? currentNumber : Number.isFinite(sourceValue) ? sourceValue : min;
    applied = Math.min(Math.max(applied, Math.min(min, max)), Math.max(min, max));
    if (rule.type === "integer") {
      applied = Math.round(applied);
    }
    const parameterPath = formatNativeRulePath(path);
    if (!Number.isFinite(sourceValue)) {
      warnings.push(createNativeInvalidWarning(effectName, parameterPath, applied, Math.min(min, max), Math.max(min, max)));
      return applied;
    }
    if (Math.abs(applied - sourceValue) > 1e-9) {
      warnings.push(
        createNativeLimitWarning(
          effectName,
          parameterPath,
          sourceValue,
          applied,
          Math.min(min, max),
          Math.max(min, max),
        ),
      );
    }
    return applied;
  }

  if (typeof currentValue === "string") {
    const rule = getNativeChoiceRule(nativeLimits, key);
    if (!rule?.choices) {
      return currentValue;
    }
    const received = requestedValue == null ? currentValue : String(requestedValue);
    const choices = rule.choices.map((entry) => String(entry));
    const applied = choices.includes(currentValue) ? currentValue : choices[0] ?? currentValue;
    if (!choices.includes(received)) {
      warnings.push(createNativeChoiceWarning(effectName, formatNativeRulePath(path), received, applied, choices));
    }
    return applied;
  }

  return currentValue;
}

function applyNativeMetadataToState(effectState, effectList, nativeLimits) {
  if (!nativeLimits) {
    return { state: effectState, warnings: [] };
  }
  const nextState = clone(effectState);
  const warnings = [];
  for (const effect of effectList) {
    if (!effect || effect.stage === "dynamics") {
      continue;
    }
    const stageKey = STAGE_CONFIG_KEY[effect.stage];
    if (!stageKey) {
      continue;
    }
    const stageState = nextState[stageKey];
    if (!stageState || !Object.prototype.hasOwnProperty.call(stageState, effect.key)) {
      continue;
    }
    stageState[effect.key] = applyNativeMetadataValue({
      effectName: effect.name ?? effect.id ?? effect.key,
      key: effect.key,
      requestedValue: effect.requestedConfig,
      currentValue: stageState[effect.key],
      nativeLimits,
      warnings,
      path: [effect.key],
    });
  }
  return { state: nextState, warnings };
}

function createGraph(audioContext, wasmBytes) {
  const sourceBus = audioContext.createGain();
  const primarySourceGain = audioContext.createGain();
  const secondarySourceGain = audioContext.createGain();
  const input = audioContext.createGain();
  const basicWorklet = new AudioWorkletNode(audioContext, "voxis-basic-processor", {
    numberOfInputs: 1,
    numberOfOutputs: 1,
    outputChannelCount: [2],
  });
  const colorTimeWorklet = new AudioWorkletNode(audioContext, "voxis-color-time-processor", {
    numberOfInputs: 1,
    numberOfOutputs: 1,
    outputChannelCount: [2],
  });
  const modernCreativeWorklet = new AudioWorkletNode(audioContext, "voxis-modern-creative-processor", {
    numberOfInputs: 1,
    numberOfOutputs: 1,
    outputChannelCount: [2],
  });
  const spectralSpatialWorklet = new AudioWorkletNode(audioContext, "voxis-spectral-spatial-processor", {
    numberOfInputs: 1,
    numberOfOutputs: 1,
    outputChannelCount: [2],
  });
  const dynamicsWorklet = new AudioWorkletNode(audioContext, "voxis-dynamics-processor", {
    numberOfInputs: 1,
    numberOfOutputs: 1,
    outputChannelCount: [2],
    processorOptions: { wasmBytes },
  });
  const modulationWorklet = new AudioWorkletNode(audioContext, "voxis-modulation-processor", {
    numberOfInputs: 1,
    numberOfOutputs: 1,
    outputChannelCount: [2],
  });
  const spaceRack = createSpaceRack(audioContext);
  const panner = audioContext.createStereoPanner();
  const master = audioContext.createGain();

  secondarySourceGain.gain.value = 0.0;
  primarySourceGain.connect(sourceBus);
  secondarySourceGain.connect(sourceBus);
  sourceBus.connect(input);
  input.connect(basicWorklet);
  basicWorklet.connect(colorTimeWorklet);
  colorTimeWorklet.connect(modernCreativeWorklet);
  modernCreativeWorklet.connect(spectralSpatialWorklet);
  spectralSpatialWorklet.connect(dynamicsWorklet);
  dynamicsWorklet.connect(modulationWorklet);
  modulationWorklet.connect(spaceRack.input);
  spaceRack.output.connect(panner);
  panner.connect(master);
  master.connect(audioContext.destination);

  return {
    sourceBus,
    primarySourceGain,
    secondarySourceGain,
    input,
    basicWorklet,
    colorTimeWorklet,
    modernCreativeWorklet,
    spectralSpatialWorklet,
    dynamicsWorklet,
    modulationWorklet,
    spaceRack,
    panner,
    master,
  };
}

export class VoxisRealtimePlayer {
  constructor({
    container = null,
    audio = null,
    processorBaseUrl = DEFAULT_PROCESSOR_BASE_URL,
    wasmUrl = DEFAULT_WASM_URL,
    appendAudio = true,
  } = {}) {
    this.processorBaseUrl = processorBaseUrl.replace(/\/$/, "");
    this.wasmUrl = wasmUrl;
    this.container = resolveElement(container);
    this.audio = audio instanceof HTMLAudioElement ? audio : createAudioElement();
    this.crossfadeAudio = createAudioElement("voxis-realtime-audio voxis-realtime-hidden");
    this.crossfadeAudio.style.display = "none";

    if (!audio && appendAudio && this.container) {
      this.container.appendChild(this.audio);
    }
    if (appendAudio && this.container) {
      this.container.appendChild(this.crossfadeAudio);
    }

    this.audio.crossOrigin = "anonymous";
    this.crossfadeAudio.crossOrigin = "anonymous";
    this.audioContext = null;
    this.graph = null;
    this.mediaElementSource = null;
    this.secondaryMediaElementSource = null;
    this.activeSourceNode = null;
    this.micStream = null;
    this.objectUrl = null;
    this.secondaryObjectUrl = null;
    this.effects = [];
    this.effectState = buildEffectState([]);
    this.warningHistory = [];
    this.warningHandlers = new Set();
    this.nativeRealtimeLimits = null;
    this.nativeDynamicsLimits = null;
    this.sourceMode = "none";
    this.secondaryStarted = false;
    this._raf = null;

    this._bindAudioEvents();
  }

  _bindAudioEvents() {
    const events = ["loadedmetadata", "play", "pause", "seeking", "seeked", "timeupdate", "ratechange", "ended"];
    events.forEach((eventName) => {
      this.audio.addEventListener(eventName, async () => {
        if ((eventName === "play" || eventName === "seeked") && this.audioContext) {
          await this.audioContext.resume();
        }
        if (this.sourceMode !== "file") {
          return;
        }
        this._updateTransportFromPrimary();
        if (eventName === "play") {
          this._resetCrossfadePartner(true);
          this._startLoop();
        }
        if (eventName === "pause" || eventName === "ended") {
          this.crossfadeAudio.pause();
          this._stopLoop();
        }
        if (eventName === "seeked" || eventName === "seeking") {
          this._resetCrossfadePartner(true);
        }
      });
    });
  }

  _startLoop() {
    if (this._raf !== null) {
      return;
    }
    const tick = () => {
      if (!this.audioContext) {
        this._raf = null;
        return;
      }
      if (this.sourceMode === "file") {
        this._updateTransportFromPrimary();
        this._syncCrossfadeState();
      }
      this._raf = window.requestAnimationFrame(tick);
    };
    this._raf = window.requestAnimationFrame(tick);
  }

  _stopLoop() {
    if (this._raf !== null) {
      window.cancelAnimationFrame(this._raf);
      this._raf = null;
    }
  }

  _setPreservesPitch(node, enabled) {
    if ("preservesPitch" in node) {
      node.preservesPitch = enabled;
    }
    if ("mozPreservesPitch" in node) {
      node.mozPreservesPitch = enabled;
    }
    if ("webkitPreservesPitch" in node) {
      node.webkitPreservesPitch = enabled;
    }
  }

  _setTransportState(transport) {
    if (!this.graph) {
      return;
    }
    this.graph.basicWorklet.port.postMessage({ type: "transport", transport });
  }

  _updateTransportFromPrimary() {
    if (this.sourceMode !== "file") {
      return;
    }
    this._setTransportState({
      ...clone(DEFAULT_TRANSPORT),
      sourceKind: "file",
      playing: !this.audio.paused && !this.audio.ended,
      startContextTimeSec: this.audioContext ? this.audioContext.currentTime : 0.0,
      positionSec: this.audio.currentTime || 0.0,
      durationSec: Number.isFinite(this.audio.duration) ? this.audio.duration : 0.0,
      playbackRate: this.audio.playbackRate || 1.0,
    });
  }

  _setMicTransportState(active) {
    if (!this.audioContext) {
      return;
    }
    this._setTransportState({
      ...clone(DEFAULT_TRANSPORT),
      sourceKind: active ? "mic" : "none",
      playing: active,
      startContextTimeSec: this.audioContext.currentTime,
      positionSec: 0.0,
      durationSec: 0.0,
      playbackRate: 1.0,
    });
  }

  _resetCrossfadePartner(resetPosition = true) {
    this.secondaryStarted = false;
    if (this.graph) {
      this.graph.primarySourceGain.gain.value = 1.0;
      this.graph.secondarySourceGain.gain.value = 0.0;
    }
    this.crossfadeAudio.pause();
    if (resetPosition) {
      try {
        this.crossfadeAudio.currentTime = 0.0;
      } catch (error) {
        console.debug(error);
      }
    }
  }

  _syncCrossfadeState() {
    if (!this.graph) {
      return;
    }
    const crossfade = this.effectState.runtime.crossfade;
    const enabled =
      crossfade.enabled &&
      Boolean(this.crossfadeAudio.src) &&
      this.sourceMode === "file" &&
      Number.isFinite(this.audio.duration) &&
      this.audio.duration > 0.0;

    if (!enabled) {
      this._resetCrossfadePartner(false);
      return;
    }

    const crossfadeDurationSec = Math.max(crossfade.durationMs / 1000.0, 0.01);
    const crossfadeStartSec = Math.max(this.audio.duration - crossfadeDurationSec, 0.0);
    const currentSec = this.audio.currentTime || 0.0;
    if (this.audio.paused || currentSec < crossfadeStartSec) {
      if (currentSec + 0.05 < crossfadeStartSec) {
        this._resetCrossfadePartner(true);
      }
      return;
    }

    const progress = Math.min(1.0, Math.max(0.0, (currentSec - crossfadeStartSec) / crossfadeDurationSec));
    const partnerTargetTime = Math.max(0.0, currentSec - crossfadeStartSec);
    if (!this.secondaryStarted) {
      this.crossfadeAudio.playbackRate = this.audio.playbackRate || 1.0;
      this._setPreservesPitch(this.crossfadeAudio, Boolean(this.audio.preservesPitch));
      this.crossfadeAudio.play().catch((error) => console.error(error));
      this.secondaryStarted = true;
    } else if (Math.abs((this.crossfadeAudio.currentTime || 0.0) - partnerTargetTime) > 0.08) {
      try {
        this.crossfadeAudio.currentTime = partnerTargetTime;
      } catch (error) {
        console.debug(error);
      }
    }
    this.graph.primarySourceGain.gain.value = 1.0 - progress;
    this.graph.secondarySourceGain.gain.value = progress;
  }

  _syncPitchTimeTransport() {
    let playbackRate = 1.0;
    let preservePitch = false;
    if (this.effectState.runtime.timeCompression.enabled) {
      playbackRate = Math.max(1.01, this.effectState.runtime.timeCompression.rate);
      preservePitch = true;
    } else if (this.effectState.runtime.timeStretch.enabled) {
      playbackRate = clamp(this.effectState.runtime.timeStretch.rate, 0.5, 0.99);
      preservePitch = true;
    }

    [this.audio, this.crossfadeAudio].forEach((node) => {
      node.playbackRate = playbackRate;
      this._setPreservesPitch(node, preservePitch);
    });
    if (this.sourceMode === "file") {
      this._updateTransportFromPrimary();
    }
  }

  _connectSource(sourceNode) {
    if (!this.graph) {
      return;
    }
    if (this.activeSourceNode) {
      this.activeSourceNode.disconnect();
    }
    this.activeSourceNode = sourceNode;
    this.activeSourceNode.connect(this.graph.primarySourceGain);
  }

  async _ensureSecondaryMediaSource() {
    if (!this.audioContext || !this.graph || !this.crossfadeAudio.src) {
      return;
    }
    if (!this.secondaryMediaElementSource) {
      this.secondaryMediaElementSource = this.audioContext.createMediaElementSource(this.crossfadeAudio);
    }
    this.secondaryMediaElementSource.disconnect();
    this.secondaryMediaElementSource.connect(this.graph.secondarySourceGain);
  }

  async start() {
    if (this.audioContext) {
      if (this.audioContext.state === "suspended") {
        await this.audioContext.resume();
      }
      return this;
    }

    const audioContext = new AudioContext({ latencyHint: "interactive" });
    const wasmBytes = await loadWasm(this.wasmUrl);
    this.nativeRealtimeLimits = await loadNativeRealtimeMetadata(wasmBytes);
    this.nativeDynamicsLimits = this.nativeRealtimeLimits;
    await audioContext.audioWorklet.addModule(`${this.processorBaseUrl}/voxis-basic-processor.js`);
    await audioContext.audioWorklet.addModule(`${this.processorBaseUrl}/voxis-color-time-processor.js`);
    await audioContext.audioWorklet.addModule(`${this.processorBaseUrl}/voxis-modern-creative-processor.js`);
    await audioContext.audioWorklet.addModule(`${this.processorBaseUrl}/voxis-spectral-spatial-processor.js`);
    await audioContext.audioWorklet.addModule(`${this.processorBaseUrl}/voxis-dynamics-processor.js`);
    await audioContext.audioWorklet.addModule(`${this.processorBaseUrl}/voxis-modulation-processor.js`);

    this.audioContext = audioContext;
    this.graph = createGraph(audioContext, wasmBytes);
    this._bindProcessorPorts();
    this.mediaElementSource = audioContext.createMediaElementSource(this.audio);
    this._connectSource(this.mediaElementSource);
    if (this.crossfadeAudio.src) {
      await this._ensureSecondaryMediaSource();
    }
    this._applyEffects();
    return this;
  }

  getAudioElement() {
    return this.audio;
  }

  async loadFile(file) {
    await this.start();
    if (this.objectUrl) {
      URL.revokeObjectURL(this.objectUrl);
    }
    this.objectUrl = URL.createObjectURL(file);
    this.audio.src = this.objectUrl;
    this.audio.load();
    if (this.micStream) {
      this.stopMicrophone();
    }
    this.sourceMode = "file";
    this._connectSource(this.mediaElementSource);
    this._syncPitchTimeTransport();
    this._resetCrossfadePartner(true);
    this._updateTransportFromPrimary();
    return this;
  }

  async loadUrl(url) {
    await this.start();
    if (this.objectUrl) {
      URL.revokeObjectURL(this.objectUrl);
      this.objectUrl = null;
    }
    this.audio.src = url;
    this.audio.load();
    if (this.micStream) {
      this.stopMicrophone();
    }
    this.sourceMode = "file";
    this._connectSource(this.mediaElementSource);
    this._syncPitchTimeTransport();
    this._resetCrossfadePartner(true);
    this._updateTransportFromPrimary();
    return this;
  }

  async loadCrossfadePartnerFile(file) {
    await this.start();
    if (this.secondaryObjectUrl) {
      URL.revokeObjectURL(this.secondaryObjectUrl);
    }
    this.secondaryObjectUrl = URL.createObjectURL(file);
    this.crossfadeAudio.src = this.secondaryObjectUrl;
    this.crossfadeAudio.load();
    await this._ensureSecondaryMediaSource();
    this._syncPitchTimeTransport();
    this._resetCrossfadePartner(true);
    return this;
  }

  async loadCrossfadePartnerUrl(url) {
    await this.start();
    if (this.secondaryObjectUrl) {
      URL.revokeObjectURL(this.secondaryObjectUrl);
      this.secondaryObjectUrl = null;
    }
    this.crossfadeAudio.src = url;
    this.crossfadeAudio.load();
    await this._ensureSecondaryMediaSource();
    this._syncPitchTimeTransport();
    this._resetCrossfadePartner(true);
    return this;
  }

  async loadConvolutionIrFile(file, normalizeIr = true) {
    await this.start();
    await this.graph.spaceRack.loadConvolutionFile(file, normalizeIr);
    this.effectState.spaceConfig.convolutionReverb.normalizeIr = normalizeIr;
    this.graph.spaceRack.configure(this.effectState.spaceConfig);
    return this;
  }

  async loadConvolutionIrUrl(url, normalizeIr = true) {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to load convolution IR: ${response.status}`);
    }
    const blob = await response.blob();
    const file = new File([blob], "voxis-ir.wav", { type: blob.type || "audio/wav" });
    return this.loadConvolutionIrFile(file, normalizeIr);
  }

  clearConvolutionIr() {
    if (this.graph) {
      this.graph.spaceRack.clearConvolutionFile();
      this.graph.spaceRack.configure(this.effectState.spaceConfig);
    }
    return this;
  }

  async useMicrophone() {
    await this.start();
    if (!this.micStream) {
      this.micStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: false,
          noiseSuppression: false,
          autoGainControl: false,
        },
      });
    }
    if (!this.audio.paused) {
      this.audio.pause();
    }
    const micSource = this.audioContext.createMediaStreamSource(this.micStream);
    this._connectSource(micSource);
    this.sourceMode = "mic";
    this._resetCrossfadePartner(true);
    this._setMicTransportState(true);
    return this;
  }

  stopMicrophone() {
    if (!this.micStream) {
      return this;
    }
    for (const track of this.micStream.getTracks()) {
      track.stop();
    }
    this.micStream = null;
    if (this.audio.src) {
      this._connectSource(this.mediaElementSource);
      this.sourceMode = "file";
      this._updateTransportFromPrimary();
    } else {
      this.sourceMode = "none";
      this._setMicTransportState(false);
    }
    return this;
  }

  setEffects(effectList) {
    this.effects = Array.isArray(effectList) ? effectList.filter(Boolean) : [];
    const { state, warnings } = buildEffectStateWithWarnings(this.effects);
    const nativeResult = applyNativeMetadataToState(state, this.effects, this.nativeRealtimeLimits);
    this.effectState = nativeResult.state;
    warnings.forEach((warning) => this._emitWarning(warning));
    nativeResult.warnings.forEach((warning) => this._emitWarning(warning));
    this._applyEffects();
    return this;
  }

  clearEffects() {
    return this.setEffects([]);
  }

  _applyEffects() {
    if (!this.graph) {
      return;
    }
    const params = this.graph.basicWorklet.parameters;
    params.get("inputGain").value = this.effectState.runtime.inputGain;
    params.get("outputGain").value = this.effectState.runtime.outputGain;
    params.get("monoMix").value = this.effectState.runtime.monoMix;
    params.get("drive").value = this.effectState.runtime.drive;
    params.get("dcBlock").value = this.effectState.runtime.dcBlock ? 1.0 : 0.0;

    this.graph.panner.pan.value = this.effectState.runtime.pan;
    this.graph.basicWorklet.port.postMessage({ type: "config", config: this.effectState.basicConfig });
    this.graph.colorTimeWorklet.port.postMessage({ type: "config", config: this.effectState.colorTimeConfig });
    this.graph.modernCreativeWorklet.port.postMessage({ type: "config", config: this.effectState.modernCreativeConfig });
    this.graph.spectralSpatialWorklet.port.postMessage({ type: "config", config: this.effectState.spectralSpatialConfig });
    this.graph.dynamicsWorklet.port.postMessage({ type: "config", config: this.effectState.dynamicsConfig });
    this.graph.modulationWorklet.port.postMessage({ type: "config", config: this.effectState.modulationConfig });
    this.graph.spaceRack.configure(this.effectState.spaceConfig);
    this._syncPitchTimeTransport();
    this._syncCrossfadeState();
  }

  _bindProcessorPorts() {
    if (!this.graph?.dynamicsWorklet) {
      return;
    }
    this.graph.dynamicsWorklet.port.onmessage = (event) => {
      const payload = event.data ?? {};
      if (payload.type === "native-limits" && payload.limits) {
        this.nativeDynamicsLimits = payload.limits;
        return;
      }
      if (payload.type === "warning") {
        const warnings = Array.isArray(payload.warnings)
          ? payload.warnings
          : payload.message
            ? [{ source: "native", message: payload.message }]
            : [];
        warnings.forEach((warning) => this._emitWarning(warning));
        return;
      }
      if (payload.type === "error" && payload.message) {
        this._emitWarning({
          source: "native",
          type: "error",
          message: `Warning: Voxis realtime dynamics bridge reported an error. ${payload.message}`,
        });
      }
    };
  }

  _emitWarning(warning) {
    if (!warning || !warning.message) {
      return;
    }
    const entry = {
      source: warning.source ?? "javascript",
      type: warning.type ?? "warning",
      effect: warning.effect ?? null,
      parameter: warning.parameter ?? null,
      min: warning.min ?? null,
      max: warning.max ?? null,
      received: warning.received ?? null,
      applied: warning.applied ?? null,
      message: String(warning.message),
      timestamp: Date.now(),
    };
    this.warningHistory.push(entry);
    for (const handler of this.warningHandlers) {
      try {
        handler(entry);
      } catch (error) {
        console.error(error);
      }
    }
    dispatchWarningEvent(this.container, entry);
    dispatchWarningEvent(this.audio, entry);
  }

  onWarning(handler) {
    if (typeof handler === "function") {
      this.warningHandlers.add(handler);
    }
    return this;
  }

  offWarning(handler) {
    this.warningHandlers.delete(handler);
    return this;
  }

  getWarnings() {
    return this.warningHistory.map((entry) => ({ ...entry }));
  }

  clearWarnings() {
    this.warningHistory = [];
    return this;
  }

  getNativeDynamicsLimits() {
    return this.nativeDynamicsLimits ? clone(this.nativeDynamicsLimits) : null;
  }

  getNativeRealtimeLimits() {
    return this.nativeRealtimeLimits ? clone(this.nativeRealtimeLimits) : null;
  }

  async destroy() {
    this._stopLoop();
    this.audio.pause();
    this.crossfadeAudio.pause();
    if (this.objectUrl) {
      URL.revokeObjectURL(this.objectUrl);
      this.objectUrl = null;
    }
    if (this.secondaryObjectUrl) {
      URL.revokeObjectURL(this.secondaryObjectUrl);
      this.secondaryObjectUrl = null;
    }
    this.stopMicrophone();
    if (this.mediaElementSource) {
      this.mediaElementSource.disconnect();
      this.mediaElementSource = null;
    }
    if (this.secondaryMediaElementSource) {
      this.secondaryMediaElementSource.disconnect();
      this.secondaryMediaElementSource = null;
    }
    if (this.audioContext) {
      await this.audioContext.close();
      this.audioContext = null;
    }
    this.graph = null;
  }
}

export async function createVoxisRealtimePlayer(options = {}) {
  const player = new VoxisRealtimePlayer(options);
  await player.start();
  return player;
}
