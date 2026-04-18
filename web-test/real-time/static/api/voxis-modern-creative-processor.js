const DEFAULT_MODERN_CREATIVE_CONFIG = {
  noiseReduction: { enabled: false, strength: 0.5 },
  voiceIsolation: { enabled: false, strength: 0.75, lowHz: 120.0, highHz: 5200.0 },
  sourceSeparation: { enabled: false, target: "vocals", strength: 0.8, lowHz: 120.0, highHz: 5200.0 },
  deReverb: { enabled: false, amount: 0.45, tailMs: 240.0 },
  deEcho: { enabled: false, amount: 0.45, minDelayMs: 60.0, maxDelayMs: 800.0 },
  spectralRepair: { enabled: false, strength: 0.35 },
  aiEnhancer: { enabled: false, amount: 0.6 },
  speechEnhancement: { enabled: false, amount: 0.7 },
  glitchEffect: { enabled: false, sliceMs: 70.0, repeatProbability: 0.22, dropoutProbability: 0.12, reverseProbability: 0.10, mix: 1.0 },
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

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function mixArrays(dry, wet, mix) {
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

function frequencyFromSemitones(semitones) {
  return Math.pow(2.0, semitones / 12.0);
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

class VoxisModernCreativeProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.config = clone(DEFAULT_MODERN_CREATIVE_CONFIG);
    this.bufferLength = Math.max(16384, Math.ceil(sampleRate * 4.0));
    this.recentBuffers = [];
    this.absoluteWritePosition = 0.0;
    this.prngState = 123456789;
    this.effectFlags = Object.create(null);
    this.effectStates = Object.create(null);
    this.coeffCache = new Map();
    this.noiseEnvelope = [];
    this.noiseGain = [];
    this.signalEnvelope = [];
    this.reverbTail = [];
    this.repairHistory = [];
    this.bitcrusherHeld = [];
    this.bitcrusherCounter = 0;
    this.robotPhase = 0.0;
    this.vinylPhase = 0.0;
    this.formantStates = [];
    this.inputEnvelope = 0.0;
    this.inputGate = 0.0;

    this.port.onmessage = (event) => {
      if (event.data?.type === "config") {
        this.config = { ...this.config, ...clone(event.data.config || {}) };
      }
    };
  }

  _random() {
    this.prngState = (1664525 * this.prngState + 1013904223) >>> 0;
    return this.prngState / 0xffffffff;
  }

  _ensureChannelState(channelCount) {
    while (this.recentBuffers.length < channelCount) {
      this.recentBuffers.push(new Float32Array(this.bufferLength));
    }
    while (this.noiseEnvelope.length < channelCount) {
      this.noiseEnvelope.push(1e-3);
      this.noiseGain.push(1.0);
      this.signalEnvelope.push(0.0);
      this.reverbTail.push(0.0);
      this.repairHistory.push([0.0, 0.0]);
      this.bitcrusherHeld.push(0.0);
    }
    if (this.formantStates.length !== channelCount) {
      this.formantStates = Array.from({ length: channelCount }, () =>
        Array.from({ length: 3 }, () => new BiquadState()),
      );
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

  _stereoFromMono(value, channelCount) {
    return Array.from({ length: channelCount }, () => value);
  }

  _renderVarispeed(stateName, channelCount, rate, safetyDelaySamples, maxGapSamples) {
    const state = this.effectStates[stateName] ?? {
      initialized: false,
      readPosition: 0.0,
      currentRate: 1.0,
      targetRate: 1.0,
      remaining: 0,
      progress: 0.0,
    };
    this.effectStates[stateName] = state;

    if (!state.initialized) {
      state.readPosition = this.absoluteWritePosition - safetyDelaySamples;
      state.initialized = true;
      state.currentRate = rate;
      state.targetRate = rate;
    }

    const gap = this.absoluteWritePosition - state.readPosition;
    if (gap < 16 || gap > maxGapSamples) {
      state.readPosition = this.absoluteWritePosition - safetyDelaySamples;
    }

    const output = new Array(channelCount);
    for (let channel = 0; channel < channelCount; channel += 1) {
      output[channel] = readAtAbsolute(this.recentBuffers[channel], state.readPosition);
    }
    state.readPosition += rate;
    return output;
  }

  _resetIfDisabled(name, enabled) {
    const wasEnabled = Boolean(this.effectFlags[name]);
    this.effectFlags[name] = enabled;
    if (!enabled && wasEnabled) {
      delete this.effectStates[name];
    }
    return wasEnabled;
  }

  _applyNoiseReduction(frameSamples) {
    const config = this.config.noiseReduction;
    if (!config.enabled) {
      return frameSamples;
    }

    const strength = clamp(config.strength, 0.0, 1.0);
    const output = new Array(frameSamples.length);
    for (let channel = 0; channel < frameSamples.length; channel += 1) {
      const absSample = Math.abs(frameSamples[channel]);
      this.noiseEnvelope[channel] = this.noiseEnvelope[channel] * 0.995 + absSample * 0.005;
      this.signalEnvelope[channel] = this.signalEnvelope[channel] * 0.92 + absSample * 0.08;
      const threshold = this.noiseEnvelope[channel] * (1.1 + strength * 2.0);
      const targetGain = this.signalEnvelope[channel] > threshold ? 1.0 : 1.0 - strength * 0.82;
      this.noiseGain[channel] = this.noiseGain[channel] * 0.88 + targetGain * 0.12;
      output[channel] = frameSamples[channel] * this.noiseGain[channel];
    }
    return output;
  }

  _applyVoiceIsolation(frameSamples) {
    const config = this.config.voiceIsolation;
    if (!config.enabled) {
      return frameSamples;
    }

    const strength = clamp(config.strength, 0.0, 1.0);
    const mono = frameSamples.length > 1 ? 0.5 * (frameSamples[0] + frameSamples[1]) : frameSamples[0];
    const isolated = this._bandLimit(this._stereoFromMono(mono, frameSamples.length), "voiceIsolation", config.lowHz, config.highHz);
    const vocal = isolated[0] * (0.45 + strength * 0.9);
    return this._stereoFromMono(vocal, frameSamples.length);
  }

  _applySourceSeparation(frameSamples) {
    const config = this.config.sourceSeparation;
    if (!config.enabled) {
      return frameSamples;
    }

    const target = String(config.target || "vocals").trim().toLowerCase();
    const strength = clamp(config.strength, 0.0, 1.0);
    const vocals = this._applyVoiceIsolation(frameSamples.map((sample) => sample));
    if (target === "instrumental" || target === "accompaniment" || target === "music") {
      return frameSamples.map((sample, channel) => sample - vocals[channel] * strength);
    }
    if (target === "bass") {
      return this._bandLimit(frameSamples, "sourceSeparationBass", 20.0, Math.max(120.0, config.lowHz + 80.0));
    }
    if (target === "drums") {
      const low = this._bandLimit(frameSamples, "sourceSeparationDrumsLow", 20.0, 220.0);
      const vocalReduced = frameSamples.map((sample, channel) => sample - vocals[channel] * 0.8 - low[channel] * 0.3);
      return vocalReduced.map((sample) => sample * (0.55 + strength * 0.45));
    }
    return vocals.map((sample) => sample * strength);
  }

  _applyDeReverb(frameSamples) {
    const config = this.config.deReverb;
    if (!config.enabled) {
      return frameSamples;
    }

    const amount = clamp(config.amount, 0.0, 1.0);
    const decay = Math.exp(-1.0 / Math.max(sampleRate * Math.max(config.tailMs, 10.0) / 1000.0, 1.0));
    return frameSamples.map((sample, channel) => {
      this.reverbTail[channel] = this.reverbTail[channel] * decay + sample * (1.0 - decay);
      return sample - this.reverbTail[channel] * amount * 0.42;
    });
  }

  _applyDeEcho(frameSamples) {
    const config = this.config.deEcho;
    if (!config.enabled) {
      return frameSamples;
    }

    const amount = clamp(config.amount, 0.0, 1.0);
    const delayA = sampleRate * clamp((config.minDelayMs + config.maxDelayMs) * 0.5 / 1000.0, 0.01, 1.2);
    const delayB = sampleRate * clamp(config.maxDelayMs / 1000.0, 0.02, 1.6);
    return frameSamples.map((sample, channel) => {
      const delayedA = readAtAbsolute(this.recentBuffers[channel], this.absoluteWritePosition - delayA);
      const delayedB = readAtAbsolute(this.recentBuffers[channel], this.absoluteWritePosition - delayB);
      return sample - (delayedA * 0.6 + delayedB * 0.24) * amount * 0.5;
    });
  }

  _applySpectralRepair(frameSamples) {
    const config = this.config.spectralRepair;
    if (!config.enabled) {
      return frameSamples;
    }

    const strength = clamp(config.strength, 0.0, 1.0);
    return frameSamples.map((sample, channel) => {
      const history = this.repairHistory[channel];
      const average = 0.5 * (history[0] + history[1]);
      const deviation = Math.abs(sample - average);
      const repaired = deviation > 0.35 ? average * strength + sample * (1.0 - strength) : sample;
      history[1] = history[0];
      history[0] = sample;
      return repaired;
    });
  }

  _applySpeechEnhancement(frameSamples) {
    const config = this.config.speechEnhancement;
    if (!config.enabled) {
      return frameSamples;
    }

    const amount = clamp(config.amount, 0.0, 1.0);
    const voice = this._bandLimit(this._applyNoiseReduction(frameSamples), "speechEnhancement", 110.0, 5600.0);
    return frameSamples.map((sample, channel) => sample * (0.72 - amount * 0.12) + voice[channel] * (0.28 + amount * 0.48));
  }

  _applyAiEnhancer(frameSamples) {
    const config = this.config.aiEnhancer;
    if (!config.enabled) {
      return frameSamples;
    }

    const amount = clamp(config.amount, 0.0, 1.0);
    const speech = this._applySpeechEnhancement(frameSamples);
    const isolated = this._applyVoiceIsolation(frameSamples);
    return frameSamples.map((sample, channel) => (
      sample * (0.78 - amount * 0.12)
      + speech[channel] * (0.14 + amount * 0.18)
      + isolated[channel] * (0.08 + amount * 0.14)
    ));
  }

  _applySection8(frameSamples) {
    let processed = frameSamples;
    processed = this._applyNoiseReduction(processed);
    processed = this._applyVoiceIsolation(processed);
    processed = this._applySourceSeparation(processed);
    processed = this._applyDeReverb(processed);
    processed = this._applyDeEcho(processed);
    processed = this._applySpectralRepair(processed);
    processed = this._applyAiEnhancer(processed);
    processed = this._applySpeechEnhancement(processed);
    return processed;
  }

  _applyGlitch(frameSamples) {
    const config = this.config.glitchEffect;
    const wasEnabled = this._resetIfDisabled("glitchEffect", config.enabled);
    if (!config.enabled) {
      return frameSamples;
    }

    const sliceLength = Math.max(8, Math.round(sampleRate * config.sliceMs / 1000.0));
    let state = this.effectStates.glitchEffect;
    if (!wasEnabled || !state || state.sliceLength !== sliceLength) {
      state = {
        sliceLength,
        phase: sliceLength,
        mode: "dry",
        buffers: [],
      };
      this.effectStates.glitchEffect = state;
    }

    if (state.phase >= state.sliceLength) {
      state.buffers = this._captureRecentSlice(frameSamples.length, state.sliceLength, 0);
      state.phase = 0;
      const chance = this._random();
      if (chance < config.dropoutProbability) {
        state.mode = "dropout";
      } else if (chance < config.dropoutProbability + config.reverseProbability) {
        state.mode = "reverse";
      } else if (chance < config.dropoutProbability + config.reverseProbability + config.repeatProbability) {
        state.mode = "repeat";
      } else {
        state.mode = "dry";
      }
    }

    let wet = frameSamples;
    if (state.mode === "dropout") {
      wet = frameSamples.map(() => 0.0);
    } else if (state.mode === "reverse") {
      wet = frameSamples.map((_, channel) => state.buffers[channel][state.sliceLength - 1 - state.phase] || 0.0);
    } else if (state.mode === "repeat") {
      wet = frameSamples.map((_, channel) => state.buffers[channel][state.phase] || 0.0);
    }
    state.phase += 1;
    return mixArrays(frameSamples, wet, config.mix);
  }

  _applyStutter(frameSamples) {
    const config = this.config.stutter;
    const wasEnabled = this._resetIfDisabled("stutter", config.enabled);
    if (!config.enabled) {
      return frameSamples;
    }

    const sliceLength = Math.max(8, Math.round(sampleRate * config.sliceMs / 1000.0));
    const intervalLength = Math.max(sliceLength, Math.round(sampleRate * config.intervalMs / 1000.0));
    let state = this.effectStates.stutter;
    if (!wasEnabled || !state || state.sliceLength !== sliceLength || state.intervalLength !== intervalLength) {
      state = {
        sliceLength,
        intervalLength,
        samplesUntilTrigger: intervalLength,
        active: false,
        phase: 0,
        totalSamples: 0,
        buffers: [],
      };
      this.effectStates.stutter = state;
    }

    state.samplesUntilTrigger -= 1;
    if (state.samplesUntilTrigger <= 0 && !state.active) {
      state.buffers = this._captureRecentSlice(frameSamples.length, state.sliceLength, 0);
      state.samplesUntilTrigger = state.intervalLength;
      state.active = true;
      state.phase = 0;
      state.totalSamples = state.sliceLength * Math.max(1, Math.round(config.repeats));
    }

    if (!state.active) {
      return frameSamples;
    }

    const wet = frameSamples.map((_, channel) => state.buffers[channel][state.phase % state.sliceLength] || 0.0);
    state.phase += 1;
    if (state.phase >= state.totalSamples) {
      state.active = false;
      state.phase = 0;
    }
    return mixArrays(frameSamples, wet, config.mix);
  }

  _applyTapeStop(frameSamples) {
    const config = this.config.tapeStop;
    const wasEnabled = this._resetIfDisabled("tapeStop", config.enabled);
    if (!config.enabled) {
      return frameSamples;
    }

    const stopSamples = Math.max(32, Math.round(sampleRate * config.stopTimeMs / 1000.0));
    let state = this.effectStates.tapeStop;
    if (!wasEnabled || !state) {
      state = {
        progress: 0,
        readPosition: this.absoluteWritePosition - 512,
      };
      this.effectStates.tapeStop = state;
    }

    const progress = Math.min(1.0, state.progress / stopSamples);
    const rate = Math.max(0.02, Math.pow(1.0 - progress, Math.max(config.curve, 0.1)));
    const wet = this._renderVarispeed("tapeStopRead", frameSamples.length, rate, 768, sampleRate * 2.0);
    state.progress += 1;
    return mixArrays(frameSamples, wet, config.mix);
  }

  _applyReverseReverb(frameSamples) {
    const config = this.config.reverseReverb;
    const wasEnabled = this._resetIfDisabled("reverseReverb", config.enabled);
    if (!config.enabled) {
      return frameSamples;
    }

    const sliceLength = Math.max(64, Math.min(this.bufferLength / 2, Math.round(sampleRate * Math.min(config.decaySeconds * 0.25, 0.5))));
    let state = this.effectStates.reverseReverb;
    if (!wasEnabled || !state || state.sliceLength !== sliceLength) {
      state = {
        sliceLength,
        phase: sliceLength,
        buffers: [],
      };
      this.effectStates.reverseReverb = state;
    }

    if (state.phase >= state.sliceLength) {
      state.buffers = this._captureRecentSlice(frameSamples.length, state.sliceLength, 0);
      state.phase = 0;
    }

    const wet = frameSamples.map((_, channel) => {
      const index = state.sliceLength - 1 - state.phase;
      const envelope = Math.pow((state.phase + 1) / state.sliceLength, 1.6);
      return (state.buffers[channel][index] || 0.0) * envelope;
    });
    state.phase += 1;
    return mixArrays(frameSamples, wet, config.mix);
  }

  _applyGranularSynthesis(frameSamples) {
    const config = this.config.granularSynthesis;
    const wasEnabled = this._resetIfDisabled("granularSynthesis", config.enabled);
    if (!config.enabled) {
      return frameSamples;
    }

    const grainLength = Math.max(16, Math.round(sampleRate * config.grainMs / 1000.0));
    const hopLength = Math.max(1, Math.round(grainLength * (1.0 - clamp(config.overlap, 0.0, 0.95))));
    const jitterLength = Math.max(0, Math.round(sampleRate * config.jitterMs / 1000.0));
    let state = this.effectStates.granularSynthesis;
    if (!wasEnabled || !state || state.grainLength !== grainLength || state.hopLength !== hopLength) {
      state = {
        grainLength,
        hopLength,
        phase: grainLength,
        buffers: [],
      };
      this.effectStates.granularSynthesis = state;
    }

    if (state.phase >= state.grainLength) {
      const offset = Math.round((this._random() * 2.0 - 1.0) * jitterLength);
      state.buffers = this._captureRecentSlice(frameSamples.length, state.grainLength, offset);
      state.phase = 0;
    }

    const wet = frameSamples.map((_, channel) => {
      const phase = state.phase;
      const window = 0.5 - 0.5 * Math.cos((2.0 * Math.PI * phase) / Math.max(state.grainLength - 1, 1));
      return (state.buffers[channel][phase] || 0.0) * window;
    });
    state.phase += 1;
    if (state.phase >= state.hopLength) {
      state.phase = state.grainLength;
    }
    return mixArrays(frameSamples, wet, config.mix);
  }

  _applyTimeSlicing(frameSamples) {
    const config = this.config.timeSlicing;
    const wasEnabled = this._resetIfDisabled("timeSlicing", config.enabled);
    if (!config.enabled) {
      return frameSamples;
    }

    const sliceLength = Math.max(8, Math.round(sampleRate * config.sliceMs / 1000.0));
    let state = this.effectStates.timeSlicing;
    if (!wasEnabled || !state || state.sliceLength !== sliceLength) {
      state = {
        sliceLength,
        phase: sliceLength,
        reverse: false,
        buffers: [],
      };
      this.effectStates.timeSlicing = state;
    }

    if (state.phase >= state.sliceLength) {
      state.buffers = this._captureRecentSlice(frameSamples.length, state.sliceLength, 0);
      state.phase = 0;
      state.reverse = !state.reverse;
    }

    const wet = frameSamples.map((_, channel) => {
      const index = state.reverse ? state.sliceLength - 1 - state.phase : state.phase;
      return state.buffers[channel][index] || 0.0;
    });
    state.phase += 1;
    return mixArrays(frameSamples, wet, config.mix);
  }

  _applyRandomPitchMod(frameSamples) {
    const config = this.config.randomPitchMod;
    const wasEnabled = this._resetIfDisabled("randomPitchMod", config.enabled);
    if (!config.enabled) {
      return frameSamples;
    }

    const segmentSamples = Math.max(16, Math.round(sampleRate * config.segmentMs / 1000.0));
    let state = this.effectStates.randomPitchMod;
    if (!wasEnabled || !state) {
      state = {
        currentRate: 1.0,
        targetRate: 1.0,
        remaining: 0,
        readPosition: this.absoluteWritePosition - 1024,
      };
      this.effectStates.randomPitchMod = state;
    }

    if (state.remaining <= 0) {
      const depth = clamp(config.depthSemitones, 0.0, 12.0);
      const randomSemitones = (this._random() * 2.0 - 1.0) * depth;
      state.targetRate = frequencyFromSemitones(randomSemitones);
      state.remaining = segmentSamples;
    }
    state.remaining -= 1;
    state.currentRate = state.currentRate * 0.995 + state.targetRate * 0.005;

    const wet = this._renderVarispeed("randomPitchRead", frameSamples.length, state.currentRate, 1200, sampleRate * 2.5);
    return mixArrays(frameSamples, wet, config.mix);
  }

  _applyVinyl(frameSamples) {
    const config = this.config.vinylEffect;
    if (!config.enabled) {
      return frameSamples;
    }

    const wowAmount = clamp(config.wow, 0.0, 1.0);
    const wowRate = 1.0
      + 0.0025 * wowAmount * Math.sin(this.vinylPhase)
      + 0.0012 * wowAmount * Math.sin(this.vinylPhase * 4.7);
    const read = this._renderVarispeed("vinylRead", frameSamples.length, wowRate, 1024, sampleRate * 2.5);
    this.vinylPhase += (2.0 * Math.PI * 0.35) / sampleRate;

    // Gate the vinyl-generated noise by the input envelope so paused/silent
    // audio does not leak crackle and hiss into the output bus.
    const gate = this.inputGate;
    const hissAmount = clamp(config.noise, 0.0, 1.0) * 0.02 * gate;
    const crackleAmount = clamp(config.crackle, 0.0, 1.0) * gate;
    const lowpassed = this._bandLimit(read, "vinylTone", 60.0, 8500.0);
    const wet = lowpassed.map((sample) => {
      const hiss = (this._random() * 2.0 - 1.0) * hissAmount;
      const crackle = this._random() < crackleAmount * 0.002 ? (this._random() * 2.0 - 1.0) * 0.6 : 0.0;
      return sample + hiss + crackle;
    });
    return mixArrays(frameSamples, wet, config.mix);
  }

  _applyRadio(frameSamples) {
    const config = this.config.radioEffect;
    if (!config.enabled) {
      return frameSamples;
    }

    // Gate the radio hiss by input envelope so silent input stays silent.
    const gate = this.inputGate;
    const noiseAmount = clamp(config.noiseLevel, 0.0, 1.0) * 0.01 * gate;
    const wet = this._bandLimit(frameSamples, "radioBand", 180.0, 3800.0).map((sample) => {
      const noisy = sample + (this._random() * 2.0 - 1.0) * noiseAmount;
      return Math.tanh(noisy * 1.7);
    });
    return mixArrays(frameSamples, wet, config.mix);
  }

  _applyTelephone(frameSamples) {
    const config = this.config.telephoneEffect;
    if (!config.enabled) {
      return frameSamples;
    }

    const mono = frameSamples.length > 1 ? 0.5 * (frameSamples[0] + frameSamples[1]) : frameSamples[0];
    const wet = this._bandLimit(this._stereoFromMono(mono, frameSamples.length), "telephoneBand", 300.0, 3200.0);
    return mixArrays(frameSamples, wet, config.mix);
  }

  _applyRetro8Bit(frameSamples) {
    const config = this.config.retro8bit;
    if (!config.enabled) {
      return frameSamples;
    }

    const safeBits = Math.max(2, Math.round(config.bitDepth));
    const safeReduction = Math.max(1, Math.round(config.sampleRateReduction));
    if (this.bitcrusherCounter <= 0) {
      const levels = (1 << safeBits) - 1;
      for (let channel = 0; channel < frameSamples.length; channel += 1) {
        const quantized = Math.round(((frameSamples[channel] + 1.0) * 0.5) * levels) / levels;
        this.bitcrusherHeld[channel] = quantized * 2.0 - 1.0;
      }
      this.bitcrusherCounter = safeReduction - 1;
    } else {
      this.bitcrusherCounter -= 1;
    }
    const wet = frameSamples.map((_, channel) => this.bitcrusherHeld[channel]);
    return mixArrays(frameSamples, wet, config.mix);
  }

  _applySlowMotionExtreme(frameSamples) {
    const config = this.config.slowMotionExtreme;
    if (!config.enabled) {
      return frameSamples;
    }

    const read = this._renderVarispeed("slowMotionRead", frameSamples.length, clamp(config.rate, 0.1, 0.9), 1600, sampleRate * 3.0);
    const toned = this._bandLimit(read, "slowMotionTone", 40.0, config.toneHz);
    return mixArrays(frameSamples, toned, config.mix);
  }

  _applyRobotVoice(frameSamples) {
    const config = this.config.robotVoice;
    if (!config.enabled) {
      return frameSamples;
    }

    const mono = frameSamples.length > 1 ? 0.5 * (frameSamples[0] + frameSamples[1]) : frameSamples[0];
    const carrier = Math.sign(Math.sin(this.robotPhase));
    this.robotPhase += (2.0 * Math.PI * Math.max(config.carrierHz, 5.0)) / sampleRate;
    const wet = this._bandLimit(this._stereoFromMono(mono * carrier, frameSamples.length), "robotBand", 120.0, 4500.0);
    return mixArrays(frameSamples, wet, config.mix);
  }

  _applyAlienVoice(frameSamples) {
    const config = this.config.alienVoice;
    if (!config.enabled) {
      return frameSamples;
    }

    const rate = frequencyFromSemitones(clamp(config.shiftSemitones, -12.0, 12.0));
    const shifted = this._renderVarispeed("alienRead", frameSamples.length, rate, 1400, sampleRate * 2.8);
    const formantLow = 200.0 * clamp(config.formantShift, 0.6, 1.8);
    const formantHigh = 3400.0 * clamp(config.formantShift, 0.6, 1.8);
    let wet = this._bandLimit(shifted, "alienFormant", formantLow, formantHigh);
    // Gate alien-voice dithering by input so it does not hiss in silence.
    const alienNoise = 0.004 * this.inputGate;
    wet = wet.map((sample) => sample + (this._random() * 2.0 - 1.0) * alienNoise);
    return mixArrays(frameSamples, wet, config.mix);
  }

  _applySection9(frameSamples) {
    let processed = frameSamples;
    processed = this._applyGlitch(processed);
    processed = this._applyStutter(processed);
    processed = this._applyTapeStop(processed);
    processed = this._applyReverseReverb(processed);
    processed = this._applyGranularSynthesis(processed);
    processed = this._applyTimeSlicing(processed);
    processed = this._applyRandomPitchMod(processed);
    processed = this._applyVinyl(processed);
    processed = this._applyRadio(processed);
    processed = this._applyTelephone(processed);
    processed = this._applyRetro8Bit(processed);
    processed = this._applySlowMotionExtreme(processed);
    processed = this._applyRobotVoice(processed);
    processed = this._applyAlienVoice(processed);
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
      let peak = 0.0;
      for (let channel = 0; channel < channelCount; channel += 1) {
        const source = input[channel] || input[0];
        const value = source ? source[frame] : 0.0;
        frameSamples[channel] = value;
        const absValue = Math.abs(value);
        if (absValue > peak) peak = absValue;
      }

      // Input envelope follower (peak + slow release ~130ms at 44.1kHz).
      // Used to gate self-generated noise so Vinyl/Radio/Alien hiss does not
      // leak through when the input is paused or silent.
      const envelopeRelease = 0.9995;
      this.inputEnvelope = peak > this.inputEnvelope
        ? peak
        : this.inputEnvelope * envelopeRelease;
      // Soft gate: 0 below -80dB, fully open above -50dB
      const gateFloor = 0.0001;
      const gateRange = 0.003;
      this.inputGate = Math.min(
        1.0,
        Math.max(0.0, (this.inputEnvelope - gateFloor) / gateRange),
      );

      this._writeRecentFrame(frameSamples);

      let processed = frameSamples;
      processed = this._applySection8(processed);
      processed = this._applySection9(processed);

      for (let channel = 0; channel < channelCount; channel += 1) {
        output[channel][frame] = processed[channel];
      }
    }

    return true;
  }
}

registerProcessor("voxis-modern-creative-processor", VoxisModernCreativeProcessor);
