const DEFAULT_COLOR_TIME_CONFIG = {
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

const NOTE_TO_PC = Object.freeze({
  C: 0,
  "C#": 1,
  Db: 1,
  D: 2,
  "D#": 3,
  Eb: 3,
  E: 4,
  F: 5,
  "F#": 6,
  Gb: 6,
  G: 7,
  "G#": 8,
  Ab: 8,
  A: 9,
  "A#": 10,
  Bb: 10,
  B: 11,
});

const SCALE_INTERVALS = Object.freeze({
  chromatic: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
  major: [0, 2, 4, 5, 7, 9, 11],
  minor: [0, 2, 3, 5, 7, 8, 10],
  pentatonic_major: [0, 2, 4, 7, 9],
  pentatonic_minor: [0, 3, 5, 7, 10],
});

const FORMANT_BASE_FREQUENCIES = [650.0, 1100.0, 2900.0];
const FORMANT_BAND_GAINS = [1.0, 0.82, 0.65];

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function wrapPhase(value) {
  let next = value % 1.0;
  if (next < 0.0) {
    next += 1.0;
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

function makeBandpassCoefficients(sampleRateValue, frequencyHz, q) {
  const clampedFrequency = clamp(frequencyHz, 40.0, Math.max(40.0, sampleRateValue * 0.45));
  const safeQ = clamp(q, 0.1, 24.0);
  const omega = (2.0 * Math.PI * clampedFrequency) / sampleRateValue;
  const sinOmega = Math.sin(omega);
  const cosOmega = Math.cos(omega);
  const alpha = sinOmega / (2.0 * safeQ);
  return normalizeBiquad(
    alpha,
    0.0,
    -alpha,
    1.0 + alpha,
    -2.0 * cosOmega,
    1.0 - alpha,
  );
}

function midiFromFrequency(frequencyHz) {
  return 69.0 + 12.0 * Math.log2(frequencyHz / 440.0);
}

function frequencyFromMidi(midi) {
  return 440.0 * Math.pow(2.0, (midi - 69.0) / 12.0);
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

class VoxisColorTimeProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.config = clone(DEFAULT_COLOR_TIME_CONFIG);
    this.pitchMinDelaySamples = 32;
    this.pitchWindowSamples = Math.max(256, Math.round(sampleRate * 0.045));
    this.pitchBufferLength = this.pitchMinDelaySamples + this.pitchWindowSamples + 8;
    this.pitchBuffers = [];
    this.pitchWriteIndex = 0;
    this.voiceStates = Object.create(null);
    this.bitcrusherHeld = [];
    this.bitcrusherCounter = 0;
    this.tapeLowpass = [];
    this.analysisBuffer = new Float32Array(1024);
    this.analysisScratch = new Float32Array(1024);
    this.analysisFilled = 0;
    this.analysisWriteIndex = 0;
    this.analysisSamplesSinceDetect = 0;
    this.autoTuneRatio = 1.0;
    this.formantStates = [];
    this.formantCoefficients = FORMANT_BASE_FREQUENCIES.map((frequencyHz) =>
      makeBandpassCoefficients(sampleRate, frequencyHz, this.config.formantShifting.q),
    );
    this.formantKey = "";

    this.port.onmessage = (event) => {
      if (event.data?.type === "config") {
        this.config = { ...this.config, ...clone(event.data.config || {}) };
      }
    };
  }

  _ensureChannelState(channelCount) {
    while (this.pitchBuffers.length < channelCount) {
      this.pitchBuffers.push(new Float32Array(this.pitchBufferLength));
    }
    while (this.bitcrusherHeld.length < channelCount) {
      this.bitcrusherHeld.push(0.0);
    }
    while (this.tapeLowpass.length < channelCount) {
      this.tapeLowpass.push(0.0);
    }
    if (this.formantStates.length !== channelCount) {
      this.formantStates = Array.from({ length: channelCount }, () =>
        FORMANT_BASE_FREQUENCIES.map(() => new BiquadState()),
      );
    }
  }

  _voiceState(name) {
    if (!this.voiceStates[name]) {
      this.voiceStates[name] = {
        phase: wrapPhase((Object.keys(this.voiceStates).length * 0.173) % 1.0),
      };
    }
    return this.voiceStates[name];
  }

  _writePitchFrame(frameSamples) {
    for (let channel = 0; channel < frameSamples.length; channel += 1) {
      this.pitchBuffers[channel][this.pitchWriteIndex] = frameSamples[channel];
    }

    const mono = frameSamples.length > 1
      ? 0.5 * (frameSamples[0] + frameSamples[1])
      : frameSamples[0];
    this.analysisBuffer[this.analysisWriteIndex] = mono;
    this.analysisWriteIndex = (this.analysisWriteIndex + 1) % this.analysisBuffer.length;
    this.analysisFilled = Math.min(this.analysisFilled + 1, this.analysisBuffer.length);
    this.analysisSamplesSinceDetect += 1;
    this.pitchWriteIndex = (this.pitchWriteIndex + 1) % this.pitchBufferLength;
  }

  _detectPitch(minHz, maxHz) {
    if (this.analysisFilled < this.analysisBuffer.length) {
      return null;
    }

    for (let index = 0; index < this.analysisBuffer.length; index += 1) {
      this.analysisScratch[index] =
        this.analysisBuffer[(this.analysisWriteIndex + index) % this.analysisBuffer.length];
    }

    let energy = 0.0;
    for (let index = 0; index < this.analysisScratch.length; index += 1) {
      const sample = this.analysisScratch[index];
      energy += sample * sample;
    }
    if (energy < 1e-3) {
      return null;
    }

    const minLag = Math.max(2, Math.floor(sampleRate / Math.max(maxHz, 1.0)));
    const maxLag = Math.min(this.analysisScratch.length - 8, Math.ceil(sampleRate / Math.max(minHz, 1.0)));
    let bestLag = -1;
    let bestScore = 0.0;

    for (let lag = minLag; lag <= maxLag; lag += 1) {
      let correlation = 0.0;
      let normA = 0.0;
      let normB = 0.0;
      const limit = this.analysisScratch.length - lag;
      for (let index = 0; index < limit; index += 1) {
        const a = this.analysisScratch[index];
        const b = this.analysisScratch[index + lag];
        correlation += a * b;
        normA += a * a;
        normB += b * b;
      }
      const score = correlation / Math.sqrt(normA * normB + 1e-9);
      if (score > bestScore) {
        bestScore = score;
        bestLag = lag;
      }
    }

    if (bestLag < 0 || bestScore < 0.6) {
      return null;
    }
    return sampleRate / bestLag;
  }

  _nearestScaleMidi(midiValue, key, scale) {
    const keyPc = NOTE_TO_PC[key] ?? 0;
    const scaleIntervals = SCALE_INTERVALS[scale] ?? SCALE_INTERVALS.chromatic;
    let bestMidi = Math.round(midiValue);
    let bestDistance = Number.POSITIVE_INFINITY;
    const center = Math.round(midiValue);

    for (let candidate = center - 24; candidate <= center + 24; candidate += 1) {
      const pitchClass = ((candidate - keyPc) % 12 + 12) % 12;
      if (!scaleIntervals.includes(pitchClass)) {
        continue;
      }
      const distance = Math.abs(candidate - midiValue);
      if (distance < bestDistance) {
        bestDistance = distance;
        bestMidi = candidate;
      }
    }

    return bestMidi;
  }

  _refreshAutoTuneRatio() {
    const config = this.config.autoTune;
    if (!config.enabled) {
      this.autoTuneRatio += 0.05 * (1.0 - this.autoTuneRatio);
      return;
    }

    const detectedHz = this._detectPitch(config.minHz, config.maxHz);
    if (!detectedHz) {
      this.autoTuneRatio += 0.03 * (1.0 - this.autoTuneRatio);
      return;
    }

    const midiValue = midiFromFrequency(detectedHz);
    const targetMidi = this._nearestScaleMidi(midiValue, config.key, config.scale);
    const semitoneCorrection = (targetMidi - midiValue) * clamp(config.strength, 0.0, 1.0);
    const targetRatio = Math.pow(2.0, semitoneCorrection / 12.0);
    this.autoTuneRatio = this.autoTuneRatio * 0.88 + targetRatio * 0.12;
  }

  _renderPitchVoice(frameSamples, voiceName, ratio) {
    if (Math.abs(ratio - 1.0) < 1e-4) {
      return [...frameSamples];
    }

    const state = this._voiceState(voiceName);
    const delaySlope = (1.0 - ratio) / this.pitchWindowSamples;
    const phaseA = state.phase;
    const phaseB = wrapPhase(state.phase + 0.5);
    const delayA = this.pitchMinDelaySamples + phaseA * this.pitchWindowSamples;
    const delayB = this.pitchMinDelaySamples + phaseB * this.pitchWindowSamples;
    const weightA = 0.5 - 0.5 * Math.cos(phaseA * Math.PI * 2.0);
    const weightB = 0.5 - 0.5 * Math.cos(phaseB * Math.PI * 2.0);
    const weightSum = weightA + weightB + 1e-6;
    const output = new Array(frameSamples.length);

    for (let channel = 0; channel < frameSamples.length; channel += 1) {
      const readA = linearRead(this.pitchBuffers[channel], this.pitchWriteIndex, delayA);
      const readB = linearRead(this.pitchBuffers[channel], this.pitchWriteIndex, delayB);
      output[channel] = (readA * weightA + readB * weightB) / weightSum;
    }

    state.phase = wrapPhase(state.phase + delaySlope);
    return output;
  }

  _applyAutoTune(frameSamples) {
    const config = this.config.autoTune;
    if (!config.enabled || config.strength <= 0.0) {
      return frameSamples;
    }
    return this._renderPitchVoice(frameSamples, "autoTune", clamp(this.autoTuneRatio, 0.5, 2.0));
  }

  _applyPitchShift(frameSamples) {
    const config = this.config.pitchShift;
    if (!config.enabled) {
      return frameSamples;
    }
    const ratio = Math.pow(2.0, clamp(config.semitones, -24.0, 24.0) / 12.0);
    const wet = this._renderPitchVoice(frameSamples, "pitchShift", ratio);
    return mixArrays(frameSamples, wet, config.mix);
  }

  _applyHarmonizer(frameSamples) {
    const config = this.config.harmonizer;
    if (!config.enabled) {
      return frameSamples;
    }

    const intervals = [
      Number(config.intervalA),
      Number(config.intervalB),
      Number(config.intervalC),
    ].filter((value) => Math.abs(value) > 1e-4);

    if (intervals.length === 0) {
      return frameSamples;
    }

    const wet = [...frameSamples];
    intervals.forEach((interval, index) => {
      const voice = this._renderPitchVoice(
        frameSamples,
        `harmonizer-${index}`,
        Math.pow(2.0, clamp(interval, -24.0, 24.0) / 12.0),
      );
      for (let channel = 0; channel < wet.length; channel += 1) {
        wet[channel] += voice[channel];
      }
    });

    for (let channel = 0; channel < wet.length; channel += 1) {
      wet[channel] /= intervals.length + 1.0;
    }
    return mixArrays(frameSamples, wet, config.mix);
  }

  _applyOctaver(frameSamples) {
    const config = this.config.octaver;
    if (!config.enabled) {
      return frameSamples;
    }

    const wet = [...frameSamples];
    let normalization = 1.0;
    const downCount = Math.max(0, Math.round(config.octavesDown));
    const upCount = Math.max(0, Math.round(config.octavesUp));

    if (downCount > 0) {
      const perVoiceGain = clamp(config.downMix, 0.0, 1.0) / downCount;
      for (let octave = 1; octave <= downCount; octave += 1) {
        const voice = this._renderPitchVoice(frameSamples, `octave-down-${octave}`, Math.pow(0.5, octave));
        for (let channel = 0; channel < wet.length; channel += 1) {
          wet[channel] += voice[channel] * perVoiceGain;
        }
        normalization += perVoiceGain;
      }
    }

    if (upCount > 0) {
      const perVoiceGain = clamp(config.upMix, 0.0, 1.0) / upCount;
      for (let octave = 1; octave <= upCount; octave += 1) {
        const voice = this._renderPitchVoice(frameSamples, `octave-up-${octave}`, Math.pow(2.0, octave));
        for (let channel = 0; channel < wet.length; channel += 1) {
          wet[channel] += voice[channel] * perVoiceGain;
        }
        normalization += perVoiceGain;
      }
    }

    return wet.map((sample) => sample / normalization);
  }

  _updateFormantCoefficients() {
    const config = this.config.formantShifting;
    const shift = clamp(config.shift, 0.5, 1.8);
    const q = clamp(config.q ?? 3.6, 0.4, 12.0);
    const nextKey = `${shift.toFixed(4)}|${q.toFixed(4)}`;
    if (nextKey === this.formantKey) {
      return;
    }
    this.formantKey = nextKey;
    this.formantCoefficients = FORMANT_BASE_FREQUENCIES.map((frequencyHz) =>
      makeBandpassCoefficients(sampleRate, frequencyHz * shift, q),
    );
  }

  _applyFormantShift(frameSamples) {
    const config = this.config.formantShifting;
    if (!config.enabled) {
      return frameSamples;
    }

    this._updateFormantCoefficients();
    const wetMix = clamp(config.mix, 0.0, 1.0);
    const totalGain = FORMANT_BAND_GAINS.reduce((sum, value) => sum + value, 0.0);
    const output = new Array(frameSamples.length);

    for (let channel = 0; channel < frameSamples.length; channel += 1) {
      let filtered = 0.0;
      for (let band = 0; band < this.formantCoefficients.length; band += 1) {
        filtered += this.formantStates[channel][band].process(
          frameSamples[channel],
          this.formantCoefficients[band],
        ) * FORMANT_BAND_GAINS[band];
      }
      const wet = filtered / totalGain;
      output[channel] = frameSamples[channel] * (1.0 - wetMix) + wet * wetMix;
    }

    return output;
  }

  _applyDistortion(frameSamples) {
    const config = this.config.distortion;
    if (!config.enabled) {
      return frameSamples;
    }
    const drive = Math.max(config.drive, 0.01);
    return frameSamples.map((sample) => Math.tanh(sample * (1.0 + drive * 2.5)));
  }

  _applyOverdrive(frameSamples) {
    const config = this.config.overdrive;
    if (!config.enabled) {
      return frameSamples;
    }
    const drive = Math.max(config.drive, 0.01);
    const tone = clamp(config.tone, 0.0, 1.0);
    const preGain = 1.0 + drive * (1.3 + tone * 1.7);
    const wet = frameSamples.map((sample) => {
      const shaped = (2.0 / Math.PI) * Math.atan(sample * preGain);
      return shaped * (0.82 + tone * 0.18) + sample * (0.18 - tone * 0.08);
    });
    return mixArrays(frameSamples, wet, config.mix);
  }

  _applyFuzz(frameSamples) {
    const config = this.config.fuzz;
    if (!config.enabled) {
      return frameSamples;
    }
    const drive = Math.max(config.drive, 0.01);
    const bias = clamp(config.bias, -0.45, 0.45);
    const wet = frameSamples.map((sample) => {
      const pre = sample * (2.5 + drive * 3.0) + bias * Math.sign(sample);
      const saturated = Math.tanh(pre);
      return Math.sign(saturated) * Math.sqrt(Math.abs(saturated) + 1e-8);
    });
    return mixArrays(frameSamples, wet, config.mix);
  }

  _applyBitcrusher(frameSamples) {
    const config = this.config.bitcrusher;
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

  _applyWaveshaper(frameSamples) {
    const config = this.config.waveshaper;
    if (!config.enabled) {
      return frameSamples;
    }
    const amount = Math.max(config.amount, 0.01);
    const symmetry = clamp(config.symmetry, -0.95, 0.95);
    const strength = 1.0 + amount * 4.0;
    const denominator = Math.max(1e-6, 1.0 - Math.exp(-strength));
    const wet = frameSamples.map((sample) => {
      const shifted = clamp(sample + symmetry * 0.25, -1.0, 1.0);
      return Math.sign(shifted) * (1.0 - Math.exp(-Math.abs(shifted) * strength)) / denominator;
    });
    return mixArrays(frameSamples, wet, config.mix);
  }

  _applyTubeSaturation(frameSamples) {
    const config = this.config.tubeSaturation;
    if (!config.enabled) {
      return frameSamples;
    }
    const drive = Math.max(config.drive, 0.01);
    const bias = clamp(config.bias, -0.4, 0.4);
    const dcShift = bias * 0.35;
    const wet = frameSamples.map((sample) => {
      const shaped = Math.tanh(sample * (1.0 + drive * 2.4) + dcShift) - Math.tanh(dcShift);
      return clamp(shaped, -1.0, 1.0);
    });
    return mixArrays(frameSamples, wet, config.mix);
  }

  _applyTapeSaturation(frameSamples) {
    const config = this.config.tapeSaturation;
    if (!config.enabled) {
      return frameSamples;
    }
    const drive = Math.max(config.drive, 0.01);
    const softness = clamp(config.softness, 0.0, 1.0);
    const alpha = clamp(0.72 - softness * 0.56, 0.08, 0.92);
    const wet = new Array(frameSamples.length);

    for (let channel = 0; channel < frameSamples.length; channel += 1) {
      const pre = Math.tanh(frameSamples[channel] * (1.0 + drive * 1.8));
      this.tapeLowpass[channel] += alpha * (pre - this.tapeLowpass[channel]);
      wet[channel] = this.tapeLowpass[channel] * 0.82 + pre * 0.18;
    }

    return mixArrays(frameSamples, wet, config.mix);
  }

  _applySoftClipping(frameSamples) {
    const config = this.config.softClipping;
    if (!config.enabled) {
      return frameSamples;
    }
    const threshold = Math.max(config.threshold, 0.05);
    return frameSamples.map((sample) => {
      const normalized = sample / threshold;
      const absNormalized = Math.abs(normalized);
      const wet = absNormalized < 1.0
        ? normalized - (normalized ** 3) / 3.0
        : Math.sign(normalized) * (2.0 / 3.0);
      return clamp(wet * threshold * 1.5, -1.0, 1.0);
    });
  }

  _applyHardClipping(frameSamples) {
    const config = this.config.hardClipping;
    if (!config.enabled) {
      return frameSamples;
    }
    const threshold = Math.max(config.threshold, 0.05);
    return frameSamples.map((sample) => clamp(sample, -threshold, threshold));
  }

  _applyColorChain(frameSamples) {
    let processed = frameSamples;
    processed = this._applyDistortion(processed);
    processed = this._applyOverdrive(processed);
    processed = this._applyFuzz(processed);
    processed = this._applyBitcrusher(processed);
    processed = this._applyWaveshaper(processed);
    processed = this._applyTubeSaturation(processed);
    processed = this._applyTapeSaturation(processed);
    processed = this._applySoftClipping(processed);
    processed = this._applyHardClipping(processed);
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

      this._writePitchFrame(frameSamples);
      if (this.config.autoTune.enabled && this.analysisSamplesSinceDetect >= this.analysisBuffer.length) {
        this.analysisSamplesSinceDetect = 0;
        this._refreshAutoTuneRatio();
      } else if (!this.config.autoTune.enabled) {
        this.autoTuneRatio += 0.04 * (1.0 - this.autoTuneRatio);
      }

      let processed = frameSamples;
      processed = this._applyAutoTune(processed);
      processed = this._applyPitchShift(processed);
      processed = this._applyHarmonizer(processed);
      processed = this._applyOctaver(processed);
      processed = this._applyFormantShift(processed);
      processed = this._applyColorChain(processed);

      for (let channel = 0; channel < channelCount; channel += 1) {
        output[channel][frame] = processed[channel];
      }
    }

    return true;
  }
}

registerProcessor("voxis-color-time-processor", VoxisColorTimeProcessor);
