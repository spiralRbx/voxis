const DEFAULT_MODULATION_CONFIG = {
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

function cloneConfig(value) {
  return JSON.parse(JSON.stringify(value));
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function advancePhase(phase, step) {
  let next = phase + step;
  const tau = Math.PI * 2.0;
  if (next >= tau || next < 0.0) {
    next %= tau;
    if (next < 0.0) {
      next += tau;
    }
  }
  return next;
}

function linearRead(line, writeIndex, delaySamples) {
  const length = line.length;
  const readPosition = writeIndex - delaySamples;
  const basePosition = Math.floor(readPosition);
  const fraction = readPosition - basePosition;
  const newer = line[((basePosition % length) + length) % length];
  const older = line[(((basePosition - 1) % length) + length) % length];
  return newer * (1.0 - fraction) + older * fraction;
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

function makeLowpassCoefficients(sampleRateValue, frequencyHz) {
  const clampedFrequency = clamp(frequencyHz, 5.0, Math.max(5.0, sampleRateValue * 0.499));
  const omega = 2.0 * Math.PI * clampedFrequency / sampleRateValue;
  const sinOmega = Math.sin(omega);
  const cosOmega = Math.cos(omega);
  const q = 0.70710678;
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

function makeHilbertCoefficients(length = 31) {
  const size = length % 2 === 0 ? length + 1 : length;
  const center = (size - 1) / 2;
  const coefficients = new Float32Array(size);
  for (let index = 0; index < size; index += 1) {
    const m = index - center;
    let value = 0.0;
    if (m !== 0 && Math.abs(m % 2) === 1) {
      value = 2.0 / (Math.PI * m);
    }
    const window = 0.54 - 0.46 * Math.cos((2.0 * Math.PI * index) / (size - 1));
    coefficients[index] = value * window;
  }
  return coefficients;
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

class VoxisModulationProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.config = cloneConfig(DEFAULT_MODULATION_CONFIG);
    this.tremoloPhase = 0.0;
    this.autoPanSampleIndex = 0;
    this.ringModPhase = 0.0;
    this.frequencyShifterPhase = 0.0;
    this.frequencyHilbertCoeffs = makeHilbertCoefficients(31);
    this.frequencyBuffers = [];
    this.frequencyWriteIndex = 0;
    this.modulatedDelayStates = {
      chorus: { buffers: [], position: 0, sampleIndex: 0, phaseOffsets: [] },
      flanger: { buffers: [], position: 0, sampleIndex: 0, phaseOffsets: [] },
      vibrato: { buffers: [], position: 0, sampleIndex: 0, phaseOffsets: [] },
    };
    this.phaserState = {
      prevX: [],
      prevY: [],
      feedback: [],
      sampleIndex: 0,
      stageCount: 4,
    };
    this.rotaryState = {
      hornPhase: 0.0,
      bassPhase: 0.0,
      crossoverStates: [],
      crossoverHz: 900.0,
      coeffs: makeLowpassCoefficients(sampleRate, 900.0),
    };

    this.port.onmessage = (event) => {
      if (event.data?.type === "config") {
        this.config = { ...this.config, ...cloneConfig(event.data.config || {}) };
      }
    };
  }

  _ensureFrequencyBuffers(channelCount) {
    const length = this.frequencyHilbertCoeffs.length;
    while (this.frequencyBuffers.length < channelCount) {
      this.frequencyBuffers.push(new Float32Array(length));
    }
  }

  _applyFrequencyShifter(frameSamples) {
    const config = this.config.frequencyShifter;
    if (!config.enabled) {
      return frameSamples;
    }

    const channelCount = frameSamples.length;
    this._ensureFrequencyBuffers(channelCount);
    const length = this.frequencyHilbertCoeffs.length;
    const center = (length - 1) >> 1;
    const wetMix = clamp(config.mix, 0.0, 1.0);
    const cosine = Math.cos(this.frequencyShifterPhase);
    const sine = Math.sin(this.frequencyShifterPhase);
    const output = new Array(channelCount);

    for (let channel = 0; channel < channelCount; channel += 1) {
      const buffer = this.frequencyBuffers[channel];
      buffer[this.frequencyWriteIndex] = frameSamples[channel];

      let imag = 0.0;
      for (let tap = 0; tap < length; tap += 1) {
        const index = (this.frequencyWriteIndex - tap + length) % length;
        imag += this.frequencyHilbertCoeffs[tap] * buffer[index];
      }

      const delayedIndex = (this.frequencyWriteIndex - center + length) % length;
      const dryAligned = buffer[delayedIndex];
      const wet = dryAligned * cosine - imag * sine;
      output[channel] = frameSamples[channel] * (1.0 - wetMix) + wet * wetMix;
    }

    this.frequencyWriteIndex = (this.frequencyWriteIndex + 1) % length;
    const shiftHz = clamp(config.shiftHz, -sampleRate * 0.45, sampleRate * 0.45);
    this.frequencyShifterPhase = advancePhase(
      this.frequencyShifterPhase,
      (2.0 * Math.PI * shiftHz) / sampleRate,
    );

    return output;
  }

  _ensureModulatedDelayState(state, channelCount, maxDelayMs) {
    const lineLength = Math.max(8, Math.ceil(sampleRate * Math.max(maxDelayMs, 1.0) / 1000.0) + 4);
    if (state.buffers.length !== channelCount || (state.buffers[0] && state.buffers[0].length !== lineLength)) {
      state.buffers = Array.from({ length: channelCount }, () => new Float32Array(lineLength));
      state.position = 0;
      state.sampleIndex = 0;
      state.phaseOffsets = Array.from({ length: channelCount }, (_, channel) => channel * (Math.PI * 0.5));
    }
  }

  _applyModulatedDelay(frameSamples, config, state, wetOnly = false) {
    if (!config.enabled) {
      return frameSamples;
    }

    const channelCount = frameSamples.length;
    this._ensureModulatedDelayState(state, channelCount, config.delayMs + Math.abs(config.depthMs) + 10.0);
    const output = new Array(channelCount);
    const lfoBase = 2.0 * Math.PI * Math.max(config.rateHz, 0.01) * (state.sampleIndex / sampleRate);

    for (let channel = 0; channel < channelCount; channel += 1) {
      const lfo = 0.5 * (Math.sin(lfoBase + state.phaseOffsets[channel]) + 1.0);
      const delaySamples = Math.max(1.0, (config.delayMs + config.depthMs * lfo) * sampleRate / 1000.0);
      const wet = linearRead(state.buffers[channel], state.position, delaySamples);
      output[channel] = wetOnly ? wet : frameSamples[channel] * (1.0 - config.mix) + wet * config.mix;
      state.buffers[channel][state.position] = frameSamples[channel] + wet * (config.feedback ?? 0.0);
    }

    state.position = (state.position + 1) % state.buffers[0].length;
    state.sampleIndex += 1;
    return output;
  }

  _applyTremolo(frameSamples) {
    const config = this.config.tremolo;
    if (!config.enabled) {
      return frameSamples;
    }
    const lfo = 0.5 * (Math.sin(this.tremoloPhase) + 1.0);
    const gain = (1.0 - clamp(config.depth, 0.0, 1.0)) + clamp(config.depth, 0.0, 1.0) * lfo;
    this.tremoloPhase = advancePhase(this.tremoloPhase, (2.0 * Math.PI * Math.max(config.rateHz, 0.01)) / sampleRate);
    return frameSamples.map((sample) => sample * gain);
  }

  _ensurePhaserState(channelCount, stageCount) {
    if (this.phaserState.prevX.length !== channelCount || this.phaserState.stageCount !== stageCount) {
      this.phaserState.prevX = Array.from({ length: channelCount }, () => new Float32Array(stageCount));
      this.phaserState.prevY = Array.from({ length: channelCount }, () => new Float32Array(stageCount));
      this.phaserState.feedback = new Float32Array(channelCount);
      this.phaserState.stageCount = stageCount;
      this.phaserState.sampleIndex = 0;
    }
  }

  _applyPhaser(frameSamples) {
    const config = this.config.phaser;
    if (!config.enabled) {
      return frameSamples;
    }

    const channelCount = frameSamples.length;
    const stageCount = Math.max(1, Math.round(config.stages));
    this._ensurePhaserState(channelCount, stageCount);

    const lfo = 0.5 * (Math.sin(2.0 * Math.PI * Math.max(config.rateHz, 0.01) * (this.phaserState.sampleIndex / sampleRate)) + 1.0);
    const sweepHz = clamp(
      Math.max(80.0, config.centerHz * (0.35 + clamp(config.depth, 0.0, 1.0) * 1.65 * lfo)),
      80.0,
      sampleRate * 0.45,
    );
    const omega = Math.PI * sweepHz / sampleRate;
    const tangent = Math.tan(omega);
    const coefficient = (1.0 - tangent) / Math.max(1.0 + tangent, 1e-6);
    const output = new Array(channelCount);

    for (let channel = 0; channel < channelCount; channel += 1) {
      const dry = frameSamples[channel];
      let stageSample = dry + this.phaserState.feedback[channel] * clamp(config.feedback, -1.0, 1.0);
      for (let stage = 0; stage < stageCount; stage += 1) {
        const stageOut = -coefficient * stageSample + this.phaserState.prevX[channel][stage] + coefficient * this.phaserState.prevY[channel][stage];
        this.phaserState.prevX[channel][stage] = stageSample;
        this.phaserState.prevY[channel][stage] = stageOut;
        stageSample = stageOut;
      }
      this.phaserState.feedback[channel] = stageSample;
      output[channel] = dry * (1.0 - clamp(config.mix, 0.0, 1.0)) + stageSample * clamp(config.mix, 0.0, 1.0);
    }

    this.phaserState.sampleIndex += 1;
    return output;
  }

  _applyAutoPan(frameSamples) {
    const config = this.config.autoPan;
    if (!config.enabled || frameSamples.length < 2) {
      return frameSamples;
    }
    const lfo = Math.sin(2.0 * Math.PI * Math.max(config.rateHz, 0.01) * (this.autoPanSampleIndex / sampleRate)) * clamp(config.depth, 0.0, 1.0);
    const angle = (lfo + 1.0) * (Math.PI * 0.25);
    const output = [...frameSamples];
    output[0] *= Math.cos(angle);
    output[1] *= Math.sin(angle);
    this.autoPanSampleIndex += 1;
    return output;
  }

  _ensureRotaryState(channelCount, crossoverHz) {
    if (this.rotaryState.crossoverStates.length !== channelCount) {
      this.rotaryState.crossoverStates = Array.from({ length: channelCount }, () => new BiquadState());
    }
    if (Math.abs(this.rotaryState.crossoverHz - crossoverHz) > 1e-3) {
      this.rotaryState.crossoverHz = crossoverHz;
      this.rotaryState.coeffs = makeLowpassCoefficients(sampleRate, crossoverHz);
    }
  }

  _applyRotary(frameSamples) {
    const config = this.config.rotarySpeaker;
    if (!config.enabled) {
      return frameSamples;
    }

    const channelCount = frameSamples.length;
    this._ensureRotaryState(channelCount, config.crossoverHz);
    const hornPan = Math.sin(this.rotaryState.hornPhase) * clamp(config.depth, 0.0, 1.0);
    const hornAngle = (hornPan + 1.0) * (Math.PI * 0.25);
    const hornLeft = Math.cos(hornAngle);
    const hornRight = Math.sin(hornAngle);
    const hornGain = 0.78 + 0.22 * Math.sin(this.rotaryState.hornPhase + Math.PI * 0.5);
    const bassGain = 0.9 + 0.1 * Math.sin(this.rotaryState.bassPhase);
    const dryMix = 1.0 - clamp(config.mix, 0.0, 1.0);
    const wetMix = clamp(config.mix, 0.0, 1.0);
    const output = [...frameSamples];

    if (channelCount >= 2) {
      const lowLeft = this.rotaryState.crossoverStates[0].process(frameSamples[0], this.rotaryState.coeffs);
      const lowRight = this.rotaryState.crossoverStates[1].process(frameSamples[1], this.rotaryState.coeffs);
      const highLeft = frameSamples[0] - lowLeft;
      const highRight = frameSamples[1] - lowRight;
      output[0] = frameSamples[0] * dryMix + (lowLeft * bassGain + highLeft * hornLeft * hornGain) * wetMix;
      output[1] = frameSamples[1] * dryMix + (lowRight * bassGain + highRight * hornRight * hornGain) * wetMix;
      const monoHorn = 0.5 * (hornLeft + hornRight) * hornGain;
      for (let channel = 2; channel < channelCount; channel += 1) {
        const low = this.rotaryState.crossoverStates[channel].process(frameSamples[channel], this.rotaryState.coeffs);
        const high = frameSamples[channel] - low;
        output[channel] = frameSamples[channel] * dryMix + (low * bassGain + high * monoHorn) * wetMix;
      }
    } else {
      const low = this.rotaryState.crossoverStates[0].process(frameSamples[0], this.rotaryState.coeffs);
      const high = frameSamples[0] - low;
      const monoHorn = 0.5 * (hornLeft + hornRight) * hornGain;
      output[0] = frameSamples[0] * dryMix + (low * bassGain + high * monoHorn) * wetMix;
    }

    this.rotaryState.hornPhase = advancePhase(this.rotaryState.hornPhase, (2.0 * Math.PI * Math.max(config.rateHz, 0.01)) / sampleRate);
    this.rotaryState.bassPhase = advancePhase(this.rotaryState.bassPhase, (2.0 * Math.PI * Math.max(config.rateHz * 0.62, 0.01)) / sampleRate);
    return output;
  }

  _applyRingModulation(frameSamples) {
    const config = this.config.ringModulation;
    if (!config.enabled) {
      return frameSamples;
    }
    const wetMix = clamp(config.mix, 0.0, 1.0);
    const carrier = Math.sin(this.ringModPhase);
    const output = frameSamples.map((sample) => sample * (1.0 - wetMix) + sample * carrier * wetMix);
    this.ringModPhase = advancePhase(this.ringModPhase, (2.0 * Math.PI * Math.max(config.frequencyHz, 0.01)) / sampleRate);
    return output;
  }

  process(inputs, outputs) {
    const input = inputs[0];
    const output = outputs[0];
    if (!output || output.length === 0) {
      return true;
    }

    const channelCount = output.length;
    const frameCount = output[0].length;

    for (let frame = 0; frame < frameCount; frame += 1) {
      const frameSamples = new Array(channelCount);
      for (let channel = 0; channel < channelCount; channel += 1) {
        const source = input[channel] || input[0];
        frameSamples[channel] = source ? source[frame] : 0.0;
      }

      let processed = frameSamples;
      processed = this._applyModulatedDelay(processed, this.config.chorus, this.modulatedDelayStates.chorus, false);
      processed = this._applyModulatedDelay(processed, this.config.flanger, this.modulatedDelayStates.flanger, false);
      processed = this._applyPhaser(processed);
      processed = this._applyTremolo(processed);
      processed = this._applyModulatedDelay(processed, this.config.vibrato, this.modulatedDelayStates.vibrato, true);
      processed = this._applyAutoPan(processed);
      processed = this._applyRotary(processed);
      processed = this._applyRingModulation(processed);
      processed = this._applyFrequencyShifter(processed);

      for (let channel = 0; channel < channelCount; channel += 1) {
        output[channel][frame] = processed[channel];
      }
    }

    return true;
  }
}

registerProcessor("voxis-modulation-processor", VoxisModulationProcessor);
