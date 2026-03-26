const DEFAULT_SPECTRAL_SPATIAL_CONFIG = {
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

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function dbToLinear(db) {
  return Math.pow(10.0, db / 20.0);
}

function mixFrames(dry, wet, mix) {
  const wetMix = clamp(mix, 0.0, 1.0);
  return dry.map((sample, index) => sample * (1.0 - wetMix) + wet[index] * wetMix);
}

function normalizeBiquad(b0, b1, b2, a0, a1, a2) {
  return {
    b0: b0 / a0,
    b1: b1 / a0,
    b2: b2 / a0,
    a1: a1 / a0,
    a2: a2 / a0,
  };
}

function makeLowpassCoefficients(sampleRateValue, frequencyHz, q = 0.70710678) {
  const clampedFrequency = clamp(frequencyHz, 20.0, Math.max(20.0, sampleRateValue * 0.45));
  const omega = (2.0 * Math.PI * clampedFrequency) / sampleRateValue;
  const sinOmega = Math.sin(omega);
  const cosOmega = Math.cos(omega);
  const alpha = sinOmega / (2.0 * q);
  return normalizeBiquad(
    (1.0 - cosOmega) * 0.5,
    1.0 - cosOmega,
    (1.0 - cosOmega) * 0.5,
    1.0 + alpha,
    -2.0 * cosOmega,
    1.0 - alpha,
  );
}

function makeHighpassCoefficients(sampleRateValue, frequencyHz, q = 0.70710678) {
  const clampedFrequency = clamp(frequencyHz, 20.0, Math.max(20.0, sampleRateValue * 0.45));
  const omega = (2.0 * Math.PI * clampedFrequency) / sampleRateValue;
  const sinOmega = Math.sin(omega);
  const cosOmega = Math.cos(omega);
  const alpha = sinOmega / (2.0 * q);
  return normalizeBiquad(
    (1.0 + cosOmega) * 0.5,
    -(1.0 + cosOmega),
    (1.0 + cosOmega) * 0.5,
    1.0 + alpha,
    -2.0 * cosOmega,
    1.0 - alpha,
  );
}

function makePeakCoefficients(sampleRateValue, frequencyHz, q, gainDb) {
  const clampedFrequency = clamp(frequencyHz, 30.0, Math.max(30.0, sampleRateValue * 0.45));
  const safeQ = clamp(q, 0.1, 24.0);
  const omega = (2.0 * Math.PI * clampedFrequency) / sampleRateValue;
  const sinOmega = Math.sin(omega);
  const cosOmega = Math.cos(omega);
  const alpha = sinOmega / (2.0 * safeQ);
  const amplitude = Math.pow(10.0, gainDb / 40.0);
  return normalizeBiquad(
    1.0 + alpha * amplitude,
    -2.0 * cosOmega,
    1.0 - alpha * amplitude,
    1.0 + alpha / amplitude,
    -2.0 * cosOmega,
    1.0 - alpha / amplitude,
  );
}

function readAtAbsolute(line, position) {
  const length = line.length;
  let wrapped = position % length;
  if (wrapped < 0) {
    wrapped += length;
  }
  const base = Math.floor(wrapped);
  const fraction = wrapped - base;
  const newer = line[base % length];
  const older = line[(base - 1 + length) % length];
  return newer * (1.0 - fraction) + older * fraction;
}

class BiquadState {
  constructor() {
    this.z1 = 0.0;
    this.z2 = 0.0;
  }

  process(sample, coeffs) {
    const out = coeffs.b0 * sample + this.z1;
    this.z1 = coeffs.b1 * sample - coeffs.a1 * out + this.z2;
    this.z2 = coeffs.b2 * sample - coeffs.a2 * out;
    return out;
  }
}

class VoxisSpectralSpatialProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.config = clone(DEFAULT_SPECTRAL_SPATIAL_CONFIG);
    this.bufferLength = Math.max(16384, Math.ceil(sampleRate * 4.0));
    this.recentBuffers = [];
    this.absoluteWritePosition = 0.0;
    this.effectFlags = Object.create(null);
    this.effectStates = Object.create(null);
    this.coeffCache = new Map();
    this.gatingEnvelope = [];
    this.gatingGain = [];

    this.port.onmessage = (event) => {
      if (event.data?.type === "config") {
        this.config = { ...this.config, ...clone(event.data.config || {}) };
      }
    };
  }

  _ensureChannelState(channelCount) {
    while (this.recentBuffers.length < channelCount) {
      this.recentBuffers.push(new Float32Array(this.bufferLength));
    }
    while (this.gatingEnvelope.length < channelCount) {
      this.gatingEnvelope.push(0.0);
      this.gatingGain.push(1.0);
    }
  }

  _writeRecentFrame(frameSamples) {
    const writeIndex = Math.floor(this.absoluteWritePosition) % this.bufferLength;
    for (let channel = 0; channel < frameSamples.length; channel += 1) {
      this.recentBuffers[channel][writeIndex] = frameSamples[channel];
    }
    this.absoluteWritePosition += 1.0;
  }

  _captureRecentSlice(channelCount, lengthSamples, offsetSamples = 0) {
    const safeLength = Math.max(8, Math.min(this.bufferLength - 8, Math.round(lengthSamples)));
    const start = this.absoluteWritePosition - offsetSamples - safeLength;
    return Array.from({ length: channelCount }, (_, channel) => {
      const slice = new Float32Array(safeLength);
      for (let index = 0; index < safeLength; index += 1) {
        slice[index] = readAtAbsolute(this.recentBuffers[channel], start + index);
      }
      return slice;
    });
  }

  _getCoeff(type, frequencyHz, q = 0.70710678, gainDb = 0.0) {
    const key = `${type}|${frequencyHz.toFixed(3)}|${q.toFixed(3)}|${gainDb.toFixed(3)}`;
    if (this.coeffCache.has(key)) {
      return this.coeffCache.get(key);
    }
    let coeffs;
    if (type === "highpass") {
      coeffs = makeHighpassCoefficients(sampleRate, frequencyHz, q);
    } else if (type === "peak") {
      coeffs = makePeakCoefficients(sampleRate, frequencyHz, q, gainDb);
    } else {
      coeffs = makeLowpassCoefficients(sampleRate, frequencyHz, q);
    }
    this.coeffCache.set(key, coeffs);
    return coeffs;
  }

  _ensureNamedState(name, channelCount, factory) {
    const current = this.effectStates[name];
    if (!current || current.length !== channelCount) {
      this.effectStates[name] = Array.from({ length: channelCount }, () => factory());
    }
    return this.effectStates[name];
  }

  _resetIfDisabled(name, enabled) {
    const wasEnabled = this.effectFlags[name] === true;
    if (!enabled) {
      delete this.effectStates[name];
      this.effectFlags[name] = false;
      return wasEnabled;
    }
    this.effectFlags[name] = true;
    return wasEnabled;
  }

  _toStereo(frameSamples) {
    if (frameSamples.length >= 2) {
      return [frameSamples[0], frameSamples[1]];
    }
    return [frameSamples[0], frameSamples[0]];
  }

  _fromStereo(left, right, channelCount) {
    if (channelCount >= 2) {
      return [left, right];
    }
    return [(left + right) * 0.5];
  }

  _bandLimit(frameSamples, stateKey, lowHz, highHz) {
    const states = this._ensureNamedState(stateKey, frameSamples.length, () => ({
      hp: new BiquadState(),
      lp: new BiquadState(),
    }));
    const hpCoeffs = this._getCoeff("highpass", lowHz);
    const lpCoeffs = this._getCoeff("lowpass", highHz);
    return frameSamples.map((sample, channel) => {
      const highPassed = states[channel].hp.process(sample, hpCoeffs);
      return states[channel].lp.process(highPassed, lpCoeffs);
    });
  }

  _applyWidth(frameSamples, width) {
    const [left, right] = this._toStereo(frameSamples);
    const mid = 0.5 * (left + right);
    const side = 0.5 * (left - right) * width;
    return this._fromStereo(mid + side, mid - side, frameSamples.length);
  }

  _renderVarispeed(stateName, channelCount, rate, safetyDelaySamples, maxGapSamples) {
    const state = this.effectStates[stateName] ?? {
      initialized: false,
      readPosition: 0.0,
      currentRate: rate,
    };
    this.effectStates[stateName] = state;

    if (!state.initialized) {
      state.readPosition = this.absoluteWritePosition - safetyDelaySamples;
      state.initialized = true;
    }

    const maxDistance = Math.max(safetyDelaySamples * 2.0, maxGapSamples);
    if (this.absoluteWritePosition - state.readPosition > maxDistance) {
      state.readPosition = this.absoluteWritePosition - safetyDelaySamples;
    }

    const output = new Array(channelCount);
    for (let channel = 0; channel < channelCount; channel += 1) {
      output[channel] = readAtAbsolute(this.recentBuffers[channel], state.readPosition);
    }
    state.readPosition += rate;
    return output;
  }

  _applyFftFilter(frameSamples) {
    const config = this.config.fftFilter;
    if (!config.enabled) {
      return frameSamples;
    }
    const wet = this._bandLimit(frameSamples, "fftFilter", config.lowHz, config.highHz);
    return mixFrames(frameSamples, wet, config.mix);
  }

  _applySpectralGating(frameSamples) {
    const config = this.config.spectralGating;
    if (!config.enabled) {
      return frameSamples;
    }

    const threshold = Math.pow(10.0, Number(config.thresholdDb) / 20.0);
    const floor = clamp(config.floor, 0.0, 1.0);
    return frameSamples.map((sample, channel) => {
      const absSample = Math.abs(sample);
      this.gatingEnvelope[channel] = this.gatingEnvelope[channel] * 0.995 + absSample * 0.005;
      const normalized = clamp(
        (this.gatingEnvelope[channel] - threshold) / Math.max(threshold * 0.75, 1e-5),
        0.0,
        1.0,
      );
      const targetGain = floor + (1.0 - floor) * normalized;
      this.gatingGain[channel] = this.gatingGain[channel] * 0.97 + targetGain * 0.03;
      return sample * this.gatingGain[channel];
    });
  }

  _applySpectralBlur(frameSamples) {
    const config = this.config.spectralBlur;
    if (!config.enabled) {
      return frameSamples;
    }

    const amount = clamp(config.amount, 0.0, 1.0);
    const states = this._ensureNamedState("spectralBlur", frameSamples.length, () => ({ value: 0.0 }));
    const alpha = clamp(1.0 - amount * 0.92, 0.04, 1.0);
    const wet = frameSamples.map((sample, channel) => {
      states[channel].value += alpha * (sample - states[channel].value);
      return states[channel].value;
    });
    return mixFrames(frameSamples, wet, amount);
  }

  _applySpectralFreeze(frameSamples) {
    const config = this.config.spectralFreeze;
    const wasEnabled = this._resetIfDisabled("spectralFreeze", config.enabled);
    if (!config.enabled) {
      return frameSamples;
    }

    const captureLength = Math.max(64, Math.round(sampleRate * 0.24));
    let state = this.effectStates.spectralFreeze;
    if (!wasEnabled || !state) {
      state = {
        elapsed: 0,
        captured: false,
        buffers: [],
        phase: 0,
      };
      this.effectStates.spectralFreeze = state;
    }

    state.elapsed += 1;
    if (!state.captured && state.elapsed >= Math.max(0, Math.round(sampleRate * config.startMs / 1000.0))) {
      state.buffers = this._captureRecentSlice(frameSamples.length, captureLength, 0);
      state.phase = 0;
      state.captured = true;
    }

    if (!state.captured || !state.buffers.length) {
      return frameSamples;
    }

    const wet = frameSamples.map((_, channel) => state.buffers[channel][state.phase] || 0.0);
    state.phase = (state.phase + 1) % state.buffers[0].length;
    return mixFrames(frameSamples, wet, config.mix);
  }

  _applySpectralMorphing(frameSamples) {
    const config = this.config.spectralMorphing;
    if (!config.enabled) {
      return frameSamples;
    }

    const amount = clamp(config.amount, 0.0, 1.0);
    const blurred = this._applySpectralBlur(frameSamples);
    const filtered = this._bandLimit(frameSamples, "spectralMorphingBand", 90.0, 9000.0);
    const wet = frameSamples.map((_, channel) => 0.5 * (blurred[channel] + filtered[channel]));
    return mixFrames(frameSamples, wet, amount);
  }

  _applyPhaseVocoder(frameSamples) {
    const config = this.config.phaseVocoder;
    const wasEnabled = this._resetIfDisabled("phaseVocoder", config.enabled);
    if (!config.enabled) {
      return frameSamples;
    }
    if (!wasEnabled) {
      delete this.effectStates.phaseVocoderRead;
    }
    return this._renderVarispeed(
      "phaseVocoderRead",
      frameSamples.length,
      clamp(config.rate, 0.35, 2.0),
      1100,
      sampleRate * 2.5,
    );
  }

  _applyHarmonicPercussive(frameSamples) {
    const config = this.config.harmonicPercussiveSeparation;
    const wasEnabled = this._resetIfDisabled("harmonicPercussiveSeparation", config.enabled);
    if (!config.enabled) {
      return frameSamples;
    }

    const states = this._ensureNamedState("harmonicPercussiveSeparation", frameSamples.length, () => ({ harmonic: 0.0 }));
    const harmonic = frameSamples.map((sample, channel) => {
      states[channel].harmonic += 0.035 * (sample - states[channel].harmonic);
      return states[channel].harmonic;
    });
    const percussive = frameSamples.map((sample, channel) => (sample - harmonic[channel]) * 1.9);
    let wet = harmonic;
    if (config.target === "percussive") {
      wet = percussive;
    } else if (config.target === "both") {
      wet = frameSamples;
    }
    if (!wasEnabled) {
      return mixFrames(frameSamples, wet, config.mix);
    }
    return mixFrames(frameSamples, wet, config.mix);
  }

  _applySpectralDelay(frameSamples) {
    const config = this.config.spectralDelay;
    const wasEnabled = this._resetIfDisabled("spectralDelay", config.enabled);
    if (!config.enabled) {
      return frameSamples;
    }

    const maxDelaySamples = Math.max(2, Math.round(sampleRate * config.maxDelayMs / 1000.0));
    let state = this.effectStates.spectralDelay;
    if (!wasEnabled || !state || state.length !== maxDelaySamples + 2 || state.channelCount !== frameSamples.length) {
      state = {
        length: maxDelaySamples + 2,
        writeIndex: 0,
        channelCount: frameSamples.length,
        lines: Array.from({ length: 3 }, () =>
          Array.from({ length: frameSamples.length }, () => new Float32Array(maxDelaySamples + 2)),
        ),
      };
      this.effectStates.spectralDelay = state;
    }

    const low = this._bandLimit(frameSamples, "spectralDelayLow", 20.0, 260.0);
    const high = this._bandLimit(frameSamples, "spectralDelayHigh", 2200.0, 14000.0);
    const mid = frameSamples.map((sample, channel) => sample - low[channel] - high[channel]);
    const bands = [low, mid, high];
    const bandDelay = [
      maxDelaySamples,
      Math.max(1, Math.round(maxDelaySamples * 0.62)),
      Math.max(1, Math.round(maxDelaySamples * 0.32)),
    ];
    const bandGain = [0.7, 0.85, 1.0];
    const wet = new Array(frameSamples.length).fill(0.0);

    for (let bandIndex = 0; bandIndex < 3; bandIndex += 1) {
      for (let channel = 0; channel < frameSamples.length; channel += 1) {
        const line = state.lines[bandIndex][channel];
        const readIndex = (state.writeIndex - bandDelay[bandIndex] + state.length) % state.length;
        const delayed = line[readIndex];
        wet[channel] += delayed * bandGain[bandIndex];
        line[state.writeIndex] = bands[bandIndex][channel] + delayed * clamp(config.feedback, 0.0, 0.95);
      }
    }
    state.writeIndex = (state.writeIndex + 1) % state.length;
    return mixFrames(frameSamples, wet, config.mix);
  }

  _applySection10(frameSamples) {
    let processed = frameSamples;
    processed = this._applyFftFilter(processed);
    processed = this._applySpectralGating(processed);
    processed = this._applySpectralBlur(processed);
    processed = this._applySpectralFreeze(processed);
    processed = this._applySpectralMorphing(processed);
    processed = this._applyPhaseVocoder(processed);
    processed = this._applyHarmonicPercussive(processed);
    processed = this._applySpectralDelay(processed);
    return processed;
  }

  _applyStereoWidening(frameSamples) {
    const config = this.config.stereoWidening;
    if (!config.enabled) {
      return frameSamples;
    }
    return this._applyWidth(frameSamples, clamp(config.amount, 0.0, 3.0));
  }

  _applyMidSideProcessing(frameSamples) {
    const config = this.config.midSideProcessing;
    if (!config.enabled) {
      return frameSamples;
    }
    const [left, right] = this._toStereo(frameSamples);
    const mid = 0.5 * (left + right) * dbToLinear(config.midGainDb);
    const side = 0.5 * (left - right) * dbToLinear(config.sideGainDb);
    return this._fromStereo(mid + side, mid - side, frameSamples.length);
  }

  _applyStereoImager(frameSamples) {
    const config = this.config.stereoImager;
    if (!config.enabled) {
      return frameSamples;
    }
    const states = this._ensureNamedState("stereoImagerSplit", 2, () => ({ lowpass: new BiquadState() }));
    const coeffs = this._getCoeff("lowpass", config.crossoverHz);
    const [left, right] = this._toStereo(frameSamples);
    const lowLeft = states[0].lowpass.process(left, coeffs);
    const lowRight = states[1].lowpass.process(right, coeffs);
    const highLeft = left - lowLeft;
    const highRight = right - lowRight;
    const lowOut = this._applyWidth([lowLeft, lowRight], clamp(config.lowWidth, 0.0, 3.0));
    const highOut = this._applyWidth([highLeft, highRight], clamp(config.highWidth, 0.0, 3.0));
    return this._fromStereo(lowOut[0] + highOut[0], lowOut[1] + highOut[1], frameSamples.length);
  }

  _applyBinauralBase(frameSamples, stateKey, azimuthDeg, distance, roomMix, elevationDeg = 0.0, hrtf = false) {
    const length = 96;
    let state = this.effectStates[stateKey];
    if (!state) {
      state = {
        index: 0,
        monoLine: new Float32Array(length),
        leftLowpass: new BiquadState(),
        rightLowpass: new BiquadState(),
        leftPeak: new BiquadState(),
        rightPeak: new BiquadState(),
      };
      this.effectStates[stateKey] = state;
    }

    const [leftIn, rightIn] = this._toStereo(frameSamples);
    const mono = 0.5 * (leftIn + rightIn);
    const pan = clamp(azimuthDeg / 90.0, -1.0, 1.0);
    const distanceClamped = clamp(distance, 0.35, 4.0);
    const distanceGain = 1.0 / (1.0 + 0.45 * (distanceClamped - 1.0));
    const itdSamples = Math.round(Math.abs(pan) * (8.0 + 12.0 * Math.min(distanceClamped, 2.0)));
    const farAttenuation = 1.0 - 0.4 * Math.abs(pan);
    const leftDelay = pan > 0 ? itdSamples : 0;
    const rightDelay = pan < 0 ? itdSamples : 0;

    state.monoLine[state.index] = mono;
    const leftRead = (state.index - leftDelay + length) % length;
    const rightRead = (state.index - rightDelay + length) % length;
    let left = state.monoLine[leftRead];
    let right = state.monoLine[rightRead];

    if (pan > 0) {
      left *= farAttenuation;
    } else if (pan < 0) {
      right *= farAttenuation;
    }

    const room = clamp(roomMix, 0.0, 1.0) * 0.18;
    left += right * room;
    right += left * room;

    const cutoffBase = 14000.0 / (1.0 + 0.35 * (distanceClamped - 1.0));
    const elevationBrightness = clamp(1.0 + elevationDeg / 120.0, 0.55, 1.45);
    const leftCutoff = clamp(cutoffBase * elevationBrightness, 300.0, 16000.0);
    const rightCutoff = clamp(cutoffBase * elevationBrightness, 300.0, 16000.0);
    left = state.leftLowpass.process(left * distanceGain, this._getCoeff("lowpass", leftCutoff));
    right = state.rightLowpass.process(right * distanceGain, this._getCoeff("lowpass", rightCutoff));

    if (hrtf) {
      const peakFrequency = clamp(2600.0 + pan * 900.0 + elevationDeg * 8.0, 900.0, 7000.0);
      const leftPeakGain = clamp(-2.5 - pan * 4.0, -7.0, 2.0);
      const rightPeakGain = clamp(-2.5 + pan * 4.0, -7.0, 2.0);
      left = state.leftPeak.process(left, this._getCoeff("peak", peakFrequency, 2.2, leftPeakGain));
      right = state.rightPeak.process(right, this._getCoeff("peak", peakFrequency, 2.2, rightPeakGain));
    }

    state.index = (state.index + 1) % length;
    return this._fromStereo(left, right, frameSamples.length);
  }

  _applyBinauralEffect(frameSamples) {
    const config = this.config.binauralEffect;
    const wasEnabled = this._resetIfDisabled("binauralEffect", config.enabled);
    if (!config.enabled) {
      return frameSamples;
    }
    if (!wasEnabled) {
      delete this.effectStates.binauralBase;
    }
    return this._applyBinauralBase(
      frameSamples,
      "binauralBase",
      config.azimuthDeg,
      config.distance,
      config.roomMix,
      0.0,
      false,
    );
  }

  _applySpatialPositioning(frameSamples) {
    const config = this.config.spatialPositioning;
    const wasEnabled = this._resetIfDisabled("spatialPositioning", config.enabled);
    if (!config.enabled) {
      return frameSamples;
    }
    if (!wasEnabled) {
      delete this.effectStates.spatialPositionBase;
    }
    return this._applyBinauralBase(
      frameSamples,
      "spatialPositionBase",
      config.azimuthDeg,
      config.distance,
      0.1,
      config.elevationDeg,
      false,
    );
  }

  _applyHrtfSimulation(frameSamples) {
    const config = this.config.hrtfSimulation;
    const wasEnabled = this._resetIfDisabled("hrtfSimulation", config.enabled);
    if (!config.enabled) {
      return frameSamples;
    }
    if (!wasEnabled) {
      delete this.effectStates.hrtfBase;
    }
    return this._applyBinauralBase(
      frameSamples,
      "hrtfBase",
      config.azimuthDeg,
      config.distance,
      0.14,
      config.elevationDeg,
      true,
    );
  }

  _applySection11(frameSamples) {
    let processed = frameSamples;
    processed = this._applyStereoWidening(processed);
    processed = this._applyMidSideProcessing(processed);
    processed = this._applyStereoImager(processed);
    processed = this._applyBinauralEffect(processed);
    processed = this._applySpatialPositioning(processed);
    processed = this._applyHrtfSimulation(processed);
    return processed;
  }

  process(inputs, outputs) {
    const input = inputs[0];
    const output = outputs[0];
    if (!output || output.length === 0) {
      return true;
    }

    const channelCount = output.length;
    const frameCount = output[0].length;
    this._ensureChannelState(channelCount);

    for (let frame = 0; frame < frameCount; frame += 1) {
      const frameSamples = new Array(channelCount);
      for (let channel = 0; channel < channelCount; channel += 1) {
        const source = input[channel] || input[0];
        frameSamples[channel] = source ? source[frame] : 0.0;
      }

      this._writeRecentFrame(frameSamples);

      let processed = frameSamples;
      processed = this._applySection10(processed);
      processed = this._applySection11(processed);

      for (let channel = 0; channel < channelCount; channel += 1) {
        output[channel][frame] = processed[channel];
      }
    }

    return true;
  }
}

registerProcessor("voxis-spectral-spatial-processor", VoxisSpectralSpatialProcessor);
