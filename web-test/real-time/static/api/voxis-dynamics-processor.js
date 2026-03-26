const FILTER_KIND = {
  lowpass: 0,
  highpass: 1,
  bandpass: 2,
  notch: 3,
  peak: 4,
  lowShelf: 5,
  highShelf: 6,
};

const FILTER_SLOT = {
  highpass: 0,
  lowpass: 1,
  bandpass: 2,
  notch: 3,
  peakEq: 4,
  lowShelf: 5,
  highShelf: 6,
};

const RESONANT_MODE = {
  lowpass: 0,
  highpass: 1,
  bandpass: 2,
};

const defaultConfig = {
  highpass: { enabled: false, frequencyHz: 80, q: 0.70710678, gainDb: 0, slope: 1, stages: 2 },
  lowpass: { enabled: false, frequencyHz: 18000, q: 0.70710678, gainDb: 0, slope: 1, stages: 2 },
  bandpass: { enabled: false, frequencyHz: 1200, q: 0.9, gainDb: 0, slope: 1, stages: 1 },
  notch: { enabled: false, frequencyHz: 3500, q: 2.0, gainDb: 0, slope: 1, stages: 1 },
  peakEq: { enabled: false, frequencyHz: 2800, q: 1.0, gainDb: 0, slope: 1, stages: 1 },
  lowShelf: { enabled: false, frequencyHz: 120, q: 0.70710678, gainDb: 0, slope: 1, stages: 1 },
  highShelf: { enabled: false, frequencyHz: 9500, q: 0.70710678, gainDb: 0, slope: 1, stages: 1 },
  resonantFilter: { enabled: false, mode: "lowpass", frequencyHz: 1200, resonance: 1.6, stages: 1 },
  parametricEq: [
    { enabled: false, kind: "peak", frequencyHz: 180, gainDb: 0, q: 0.9, slope: 1, stages: 1 },
    { enabled: false, kind: "peak", frequencyHz: 3000, gainDb: 0, q: 1.0, slope: 1, stages: 1 },
    { enabled: false, kind: "peak", frequencyHz: 9500, gainDb: 0, q: 0.8, slope: 1, stages: 1 },
  ],
  graphicEq: { enabled: false, q: 1.1, bandsDb: [0, 0, 0, 0, 0] },
  dynamicEq: { enabled: false, frequencyHz: 2800, thresholdDb: -24, cutDb: -6, q: 1.2, attackMs: 10, releaseMs: 120 },
  formantFilter: { enabled: false, morph: 0, intensity: 1, q: 4.0 },
  compressor: { enabled: true, thresholdDb: -18, ratio: 3.0, attackMs: 10, releaseMs: 80, makeupDb: 0 },
  downwardCompression: { enabled: false, thresholdDb: -18, ratio: 4.0, attackMs: 10, releaseMs: 80, makeupDb: 0 },
  upwardCompression: { enabled: false, thresholdDb: -42, ratio: 2.0, attackMs: 12, releaseMs: 120, maxGainDb: 18 },
  limiter: { enabled: false, ceilingDb: -1, attackMs: 1, releaseMs: 60 },
  expander: { enabled: false, thresholdDb: -35, ratio: 2.0, attackMs: 8, releaseMs: 80, makeupDb: 0 },
  noiseGate: { enabled: false, thresholdDb: -45, attackMs: 3, releaseMs: 60, floorDb: -80 },
  deesser: { enabled: false, frequencyHz: 6500, thresholdDb: -28, ratio: 4.0, attackMs: 2, releaseMs: 60, amount: 0.8 },
  transientShaper: { enabled: false, attack: 0.7, sustain: 0.2, attackMs: 18, releaseMs: 120 },
  multibandCompressor: {
    enabled: false,
    lowCutHz: 180,
    highCutHz: 3200,
    lowThresholdDb: -24,
    midThresholdDb: -18,
    highThresholdDb: -20,
    lowRatio: 2.2,
    midRatio: 3.0,
    highRatio: 2.4,
    attackMs: 10,
    releaseMs: 90,
    lowMakeupDb: 0,
    midMakeupDb: 0,
    highMakeupDb: 0,
  },
};

let wasmReadyPromise = null;
const textDecoder = typeof TextDecoder === "function" ? new TextDecoder("utf-8") : null;

function cloneConfig(config) {
  return JSON.parse(JSON.stringify(config));
}

function createDynamicsImports() {
  return {
    env: {
      emscripten_notify_memory_growth() {},
    },
  };
}

function loadDynamicsWasm(wasmBytes) {
  if (!wasmBytes) {
    return Promise.reject(new Error("Missing WASM bytes for Voxis dynamics processor."));
  }
  if (!wasmReadyPromise) {
    wasmReadyPromise = WebAssembly.instantiate(wasmBytes, createDynamicsImports())
      .then(({ instance }) => {
        if (typeof instance.exports.__wasm_call_ctors === "function") {
          instance.exports.__wasm_call_ctors();
        }
        return instance.exports;
      })
      .catch((error) => {
        wasmReadyPromise = null;
        throw error;
      });
  }
  return wasmReadyPromise;
}

function readWasmString(exports, pointer, length) {
  if (!exports || !exports.memory || !pointer || length <= 0) {
    return "";
  }
  const bytes = new Uint8Array(exports.memory.buffer, pointer, length);
  if (textDecoder) {
    return textDecoder.decode(bytes);
  }
  let text = "";
  for (let index = 0; index < bytes.length; index += 1) {
    text += String.fromCharCode(bytes[index]);
  }
  return text;
}

function filterKindToCode(kind) {
  return FILTER_KIND[kind] ?? FILTER_KIND.peak;
}

function resonantModeToCode(mode) {
  return RESONANT_MODE[mode] ?? RESONANT_MODE.lowpass;
}

class VoxisDynamicsProcessor extends AudioWorkletProcessor {
  constructor(options) {
    super();
    this.exports = null;
    this.handle = 0;
    this.bufferPtr = 0;
    this.bufferCapacity = 0;
    this.ready = false;
    this.configDirty = true;
    this.config = cloneConfig(defaultConfig);
    const wasmBytes = options?.processorOptions?.wasmBytes ?? null;

    this.port.onmessage = (event) => {
      if (event.data?.type === "config") {
        this.config = { ...this.config, ...event.data.config };
        this.configDirty = true;
      }
    };

    loadDynamicsWasm(wasmBytes)
      .then((exports) => {
        this.exports = exports;
        this.handle = this.exports.voxis_rt_create(sampleRate, 2, 256);
        this.bufferPtr = this.exports.voxis_rt_get_buffer_ptr(this.handle);
        this.bufferCapacity = this.exports.voxis_rt_get_buffer_capacity(this.handle);
        this.ready = true;
        this.configDirty = true;
        this._postNativeLimits();
        this.port.postMessage({ type: "ready" });
      })
      .catch((error) => {
        this.port.postMessage({ type: "error", message: String(error) });
      });
  }

  _postNativeLimits() {
    if (typeof this.exports?.voxis_rt_get_limits_json_ptr !== "function") {
      return;
    }
    const pointer = this.exports.voxis_rt_get_limits_json_ptr();
    const length = this.exports.voxis_rt_get_limits_json_length?.() ?? 0;
    const jsonText = readWasmString(this.exports, pointer, length).trim();
    if (!jsonText) {
      return;
    }
    try {
      this.port.postMessage({
        type: "native-limits",
        limits: JSON.parse(jsonText),
      });
    } catch (error) {
      this.port.postMessage({
        type: "warning",
        warnings: [{
          source: "native",
          type: "limits",
          message: `Warning: Voxis native dynamics limits metadata could not be parsed. ${String(error)}`,
        }],
      });
    }
  }

  _postNativeWarnings() {
    if (typeof this.exports?.voxis_rt_get_warning_ptr !== "function") {
      return;
    }
    const pointer = this.exports.voxis_rt_get_warning_ptr(this.handle);
    const length = this.exports.voxis_rt_get_warning_length?.(this.handle) ?? 0;
    const warningText = readWasmString(this.exports, pointer, length).trim();
    if (!warningText) {
      return;
    }
    const warnings = warningText
      .split(/\r?\n/g)
      .map((message) => message.trim())
      .filter(Boolean)
      .map((message) => ({
        source: "native",
        type: "limit",
        message,
      }));
    if (warnings.length > 0) {
      this.port.postMessage({ type: "warning", warnings });
    }
  }

  _applyFilterSlot(slot, kind, config) {
    this.exports.voxis_rt_set_filter_slot(
      this.handle,
      slot,
      config.enabled ? 1 : 0,
      filterKindToCode(kind),
      config.frequencyHz,
      config.q,
      config.gainDb ?? 0,
      config.slope ?? 1,
      config.stages ?? 1,
    );
  }

  _applyConfig() {
    if (!this.ready || !this.configDirty) {
      return;
    }

    const fx = this.config;
    if (typeof this.exports.voxis_rt_clear_warnings === "function") {
      this.exports.voxis_rt_clear_warnings(this.handle);
    }

    this._applyFilterSlot(FILTER_SLOT.highpass, "highpass", fx.highpass);
    this._applyFilterSlot(FILTER_SLOT.lowpass, "lowpass", fx.lowpass);
    this._applyFilterSlot(FILTER_SLOT.bandpass, "bandpass", fx.bandpass);
    this._applyFilterSlot(FILTER_SLOT.notch, "notch", fx.notch);
    this._applyFilterSlot(FILTER_SLOT.peakEq, "peak", fx.peakEq);
    this._applyFilterSlot(FILTER_SLOT.lowShelf, "lowShelf", fx.lowShelf);
    this._applyFilterSlot(FILTER_SLOT.highShelf, "highShelf", fx.highShelf);

    this.exports.voxis_rt_set_resonant_filter(
      this.handle,
      fx.resonantFilter.enabled ? 1 : 0,
      resonantModeToCode(fx.resonantFilter.mode),
      fx.resonantFilter.frequencyHz,
      fx.resonantFilter.resonance,
      fx.resonantFilter.stages ?? 1,
    );

    const parametricBands = Array.isArray(fx.parametricEq) ? fx.parametricEq : [];
    for (let index = 0; index < 3; index += 1) {
      const band = parametricBands[index] ?? defaultConfig.parametricEq[index];
      this.exports.voxis_rt_set_parametric_band(
        this.handle,
        index,
        band.enabled ? 1 : 0,
        filterKindToCode(band.kind),
        band.frequencyHz,
        band.gainDb ?? 0,
        band.q ?? 1,
        band.slope ?? 1,
        band.stages ?? 1,
      );
    }

    const graphicBands = Array.isArray(fx.graphicEq.bandsDb) ? fx.graphicEq.bandsDb : defaultConfig.graphicEq.bandsDb;
    this.exports.voxis_rt_set_graphic_eq(
      this.handle,
      fx.graphicEq.enabled ? 1 : 0,
      fx.graphicEq.q,
      graphicBands[0] ?? 0,
      graphicBands[1] ?? 0,
      graphicBands[2] ?? 0,
      graphicBands[3] ?? 0,
      graphicBands[4] ?? 0,
    );

    this.exports.voxis_rt_set_dynamic_eq(
      this.handle,
      fx.dynamicEq.enabled ? 1 : 0,
      fx.dynamicEq.frequencyHz,
      fx.dynamicEq.thresholdDb,
      fx.dynamicEq.cutDb,
      fx.dynamicEq.q,
      fx.dynamicEq.attackMs,
      fx.dynamicEq.releaseMs,
    );

    this.exports.voxis_rt_set_formant_filter(
      this.handle,
      fx.formantFilter.enabled ? 1 : 0,
      fx.formantFilter.morph,
      fx.formantFilter.intensity,
      fx.formantFilter.q,
    );

    this.exports.voxis_rt_set_compressor(
      this.handle,
      fx.compressor.enabled ? 1 : 0,
      fx.compressor.thresholdDb,
      fx.compressor.ratio,
      fx.compressor.attackMs,
      fx.compressor.releaseMs,
      fx.compressor.makeupDb,
    );
    this.exports.voxis_rt_set_downward_compression(
      this.handle,
      fx.downwardCompression.enabled ? 1 : 0,
      fx.downwardCompression.thresholdDb,
      fx.downwardCompression.ratio,
      fx.downwardCompression.attackMs,
      fx.downwardCompression.releaseMs,
      fx.downwardCompression.makeupDb,
    );
    this.exports.voxis_rt_set_upward_compression(
      this.handle,
      fx.upwardCompression.enabled ? 1 : 0,
      fx.upwardCompression.thresholdDb,
      fx.upwardCompression.ratio,
      fx.upwardCompression.attackMs,
      fx.upwardCompression.releaseMs,
      fx.upwardCompression.maxGainDb,
    );
    this.exports.voxis_rt_set_limiter(
      this.handle,
      fx.limiter.enabled ? 1 : 0,
      fx.limiter.ceilingDb,
      fx.limiter.attackMs,
      fx.limiter.releaseMs,
    );
    this.exports.voxis_rt_set_expander(
      this.handle,
      fx.expander.enabled ? 1 : 0,
      fx.expander.thresholdDb,
      fx.expander.ratio,
      fx.expander.attackMs,
      fx.expander.releaseMs,
      fx.expander.makeupDb,
    );
    this.exports.voxis_rt_set_noise_gate(
      this.handle,
      fx.noiseGate.enabled ? 1 : 0,
      fx.noiseGate.thresholdDb,
      fx.noiseGate.attackMs,
      fx.noiseGate.releaseMs,
      fx.noiseGate.floorDb,
    );
    this.exports.voxis_rt_set_deesser(
      this.handle,
      fx.deesser.enabled ? 1 : 0,
      fx.deesser.frequencyHz,
      fx.deesser.thresholdDb,
      fx.deesser.ratio,
      fx.deesser.attackMs,
      fx.deesser.releaseMs,
      fx.deesser.amount,
    );
    this.exports.voxis_rt_set_transient_shaper(
      this.handle,
      fx.transientShaper.enabled ? 1 : 0,
      fx.transientShaper.attack,
      fx.transientShaper.sustain,
      fx.transientShaper.attackMs,
      fx.transientShaper.releaseMs,
    );
    this.exports.voxis_rt_set_multiband_compressor(
      this.handle,
      fx.multibandCompressor.enabled ? 1 : 0,
      fx.multibandCompressor.lowCutHz,
      fx.multibandCompressor.highCutHz,
      fx.multibandCompressor.lowThresholdDb,
      fx.multibandCompressor.midThresholdDb,
      fx.multibandCompressor.highThresholdDb,
      fx.multibandCompressor.lowRatio,
      fx.multibandCompressor.midRatio,
      fx.multibandCompressor.highRatio,
      fx.multibandCompressor.attackMs,
      fx.multibandCompressor.releaseMs,
      fx.multibandCompressor.lowMakeupDb,
      fx.multibandCompressor.midMakeupDb,
      fx.multibandCompressor.highMakeupDb,
    );

    this._postNativeWarnings();
    this.configDirty = false;
  }

  process(inputs, outputs) {
    const input = inputs[0];
    const output = outputs[0];
    if (!output || output.length === 0) {
      return true;
    }

    const channelCount = output.length;
    const frameCount = output[0].length;

    for (let channel = 0; channel < channelCount; channel += 1) {
      const source = input[channel] || input[0];
      const destination = output[channel];
      if (!source) {
        destination.fill(0);
        continue;
      }
      destination.set(source);
    }

    if (!this.ready || !input || input.length === 0) {
      return true;
    }

    this._applyConfig();

    if (frameCount * channelCount > this.bufferCapacity) {
      return true;
    }

    const wasmView = new Float32Array(this.exports.memory.buffer, this.bufferPtr, this.bufferCapacity);
    for (let frame = 0; frame < frameCount; frame += 1) {
      for (let channel = 0; channel < channelCount; channel += 1) {
        const source = input[channel] || input[0];
        wasmView[frame * channelCount + channel] = source ? source[frame] : 0;
      }
    }

    this.exports.voxis_rt_process(this.handle, frameCount);

    for (let frame = 0; frame < frameCount; frame += 1) {
      for (let channel = 0; channel < channelCount; channel += 1) {
        output[channel][frame] = wasmView[frame * channelCount + channel];
      }
    }

    return true;
  }
}

registerProcessor("voxis-dynamics-processor", VoxisDynamicsProcessor);
