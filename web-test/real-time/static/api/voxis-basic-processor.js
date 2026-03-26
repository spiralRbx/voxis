const DEFAULT_BASIC_CONFIG = {
  normalize: {
    enabled: false,
    headroomDb: 1.0,
    maxGain: 4.0,
  },
  fadeIn: {
    enabled: false,
    durationMs: 400,
  },
  fadeOut: {
    enabled: false,
    durationMs: 400,
  },
  trim: {
    enabled: false,
    startMs: 0,
    endMs: 30000,
    featherMs: 12,
  },
  cut: {
    enabled: false,
    startMs: 1200,
    endMs: 2200,
    featherMs: 12,
  },
  silenceRemoval: {
    enabled: false,
    thresholdDb: -48,
    minSilenceMs: 80,
    paddingMs: 10,
  },
  reverse: {
    enabled: false,
    windowMs: 350,
    mix: 1.0,
  },
};

const DEFAULT_TRANSPORT = {
  sourceKind: "none",
  playing: false,
  startContextTimeSec: 0,
  positionSec: 0,
  durationSec: 0,
  playbackRate: 1,
};

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function dbToLinear(db) {
  return Math.pow(10, db / 20);
}

function smoothingCoeff(timeMs) {
  return Math.exp(-1 / (0.001 * Math.max(timeMs, 0.5) * sampleRate));
}

function linearRamp(value, start, end) {
  if (end <= start) {
    return value >= end ? 1.0 : 0.0;
  }
  return clamp((value - start) / (end - start), 0.0, 1.0);
}

class VoxisBasicProcessor extends AudioWorkletProcessor {
  static get parameterDescriptors() {
    return [
      { name: "inputGain", defaultValue: 1.0, minValue: 0.0, maxValue: 4.0, automationRate: "k-rate" },
      { name: "drive", defaultValue: 1.0, minValue: 1.0, maxValue: 8.0, automationRate: "k-rate" },
      { name: "monoMix", defaultValue: 0.0, minValue: 0.0, maxValue: 1.0, automationRate: "k-rate" },
      { name: "dcBlock", defaultValue: 1.0, minValue: 0.0, maxValue: 1.0, automationRate: "k-rate" },
      { name: "outputGain", defaultValue: 1.0, minValue: 0.0, maxValue: 2.0, automationRate: "k-rate" },
    ];
  }

  constructor() {
    super();
    this._config = clone(DEFAULT_BASIC_CONFIG);
    this._transport = clone(DEFAULT_TRANSPORT);
    this._dcPrevInput = [0.0, 0.0];
    this._dcPrevOutput = [0.0, 0.0];
    this._dcCoefficient = 0.995;
    this._normalizeEnvelope = 0.0;
    this._normalizeGain = 1.0;
    this._silenceEnvelope = 1.0;
    this._silenceFrames = 0;
    this._reverseWindowFrames = 0;
    this._reverseWriteIndex = 0;
    this._reverseOutputIndex = 0;
    this._reverseOutputReady = false;
    this._reverseInputBuffers = [];
    this._reverseOutputBuffers = [];

    this.port.onmessage = (event) => {
      if (event.data?.type === "config") {
        const nextConfig = event.data.config ? clone(event.data.config) : clone(DEFAULT_BASIC_CONFIG);
        if (!nextConfig.reverse?.enabled && this._config.reverse?.enabled) {
          this._resetReverseState();
        }
        if (!nextConfig.normalize?.enabled) {
          this._normalizeEnvelope = 0.0;
          this._normalizeGain = 1.0;
        }
        if (!nextConfig.silenceRemoval?.enabled) {
          this._silenceEnvelope = 1.0;
          this._silenceFrames = 0;
        }
        this._config = nextConfig;
      }
      if (event.data?.type === "transport") {
        this._transport = {
          ...clone(DEFAULT_TRANSPORT),
          ...(event.data.transport || {}),
        };
      }
    };
  }

  _resetReverseState() {
    this._reverseWriteIndex = 0;
    this._reverseOutputIndex = 0;
    this._reverseOutputReady = false;
    this._reverseInputBuffers = [];
    this._reverseOutputBuffers = [];
    this._reverseWindowFrames = 0;
  }

  _ensureChannelState(channelCount) {
    while (this._dcPrevInput.length < channelCount) {
      this._dcPrevInput.push(0.0);
      this._dcPrevOutput.push(0.0);
    }
  }

  _ensureReverseBuffers(channelCount) {
    const reverseConfig = this._config.reverse;
    const windowFrames = Math.max(8, Math.round(sampleRate * Math.max(reverseConfig.windowMs, 10) / 1000));
    if (this._reverseWindowFrames === windowFrames && this._reverseInputBuffers.length === channelCount) {
      return;
    }

    this._reverseWindowFrames = windowFrames;
    this._reverseWriteIndex = 0;
    this._reverseOutputIndex = 0;
    this._reverseOutputReady = false;
    this._reverseInputBuffers = Array.from({ length: channelCount }, () => new Float32Array(windowFrames));
    this._reverseOutputBuffers = Array.from({ length: channelCount }, () => new Float32Array(windowFrames));
  }

  _currentTimelineMs(frameOffset) {
    const nowSec = currentTime + frameOffset / sampleRate;
    const transport = this._transport;

    if (transport.sourceKind === "file") {
      if (!transport.playing) {
        return Math.max(0, Number(transport.positionSec || 0) * 1000);
      }
      const elapsedSec = (nowSec - Number(transport.startContextTimeSec || 0)) * Math.max(Number(transport.playbackRate || 1), 0);
      return Math.max(0, (Number(transport.positionSec || 0) + elapsedSec) * 1000);
    }

    if (transport.sourceKind === "mic") {
      if (!transport.playing) {
        return Math.max(0, Number(transport.positionSec || 0) * 1000);
      }
      return Math.max(0, (Number(transport.positionSec || 0) + (nowSec - Number(transport.startContextTimeSec || 0))) * 1000);
    }

    return Math.max(0, nowSec * 1000);
  }

  _effectiveDurationMs() {
    const transportDuration = Number(this._transport.durationSec || 0);
    if (Number.isFinite(transportDuration) && transportDuration > 0) {
      return transportDuration * 1000;
    }

    const trimConfig = this._config.trim;
    if (trimConfig.enabled && Number(trimConfig.endMs) > Number(trimConfig.startMs)) {
      return Number(trimConfig.endMs);
    }

    return null;
  }

  _trimGain(timelineMs) {
    const trimConfig = this._config.trim;
    if (!trimConfig.enabled) {
      return 1.0;
    }

    const startMs = Math.max(0, Number(trimConfig.startMs || 0));
    const endMs = Math.max(startMs, Number(trimConfig.endMs || startMs));
    const featherMs = Math.max(1, Number(trimConfig.featherMs || 1));
    const fadeIn = linearRamp(timelineMs, startMs, startMs + featherMs);
    const fadeOut = linearRamp(timelineMs, endMs - featherMs, endMs);
    return fadeIn * (1.0 - fadeOut);
  }

  _cutGain(timelineMs) {
    const cutConfig = this._config.cut;
    if (!cutConfig.enabled) {
      return 1.0;
    }

    const startMs = Math.max(0, Number(cutConfig.startMs || 0));
    const endMs = Math.max(startMs, Number(cutConfig.endMs || startMs));
    const featherMs = Math.max(1, Number(cutConfig.featherMs || 1));
    const fadeDown = linearRamp(timelineMs, startMs - featherMs, startMs);
    const fadeUp = linearRamp(timelineMs, endMs, endMs + featherMs);

    if (timelineMs < startMs - featherMs || timelineMs >= endMs + featherMs) {
      return 1.0;
    }
    if (timelineMs >= startMs && timelineMs < endMs) {
      return 0.0;
    }
    if (timelineMs < startMs) {
      return 1.0 - fadeDown;
    }
    return fadeUp;
  }

  _fadeGain(timelineMs) {
    let gain = 1.0;
    const fadeInConfig = this._config.fadeIn;
    if (fadeInConfig.enabled && Number(fadeInConfig.durationMs) > 0) {
      gain *= linearRamp(timelineMs, 0, Number(fadeInConfig.durationMs));
    }

    const fadeOutConfig = this._config.fadeOut;
    const effectiveDurationMs = this._effectiveDurationMs();
    if (fadeOutConfig.enabled && Number(fadeOutConfig.durationMs) > 0 && effectiveDurationMs !== null) {
      const durationMs = Number(fadeOutConfig.durationMs);
      const startMs = Math.max(0, effectiveDurationMs - durationMs);
      gain *= 1.0 - linearRamp(timelineMs, startMs, effectiveDurationMs);
    }

    return gain;
  }

  _timelineGain(timelineMs) {
    return this._trimGain(timelineMs) * this._cutGain(timelineMs) * this._fadeGain(timelineMs);
  }

  _updateNormalizeGain(detector) {
    const normalizeConfig = this._config.normalize;
    if (!normalizeConfig.enabled) {
      return 1.0;
    }

    const attackCoeff = smoothingCoeff(5);
    const releaseCoeff = smoothingCoeff(140);
    const detectorValue = Math.max(0.0, detector);
    const envelopeCoeff = detectorValue > this._normalizeEnvelope ? attackCoeff : releaseCoeff;
    this._normalizeEnvelope = envelopeCoeff * this._normalizeEnvelope + (1.0 - envelopeCoeff) * detectorValue;

    const targetPeak = dbToLinear(-Math.abs(Number(normalizeConfig.headroomDb || 0)));
    const maxGain = Math.max(1.0, Number(normalizeConfig.maxGain || 1));
    const desiredGain =
      this._normalizeEnvelope > 1e-5 ? clamp(targetPeak / this._normalizeEnvelope, 0.0, maxGain) : 1.0;
    const gainCoeff = desiredGain < this._normalizeGain ? attackCoeff : releaseCoeff;
    this._normalizeGain = gainCoeff * this._normalizeGain + (1.0 - gainCoeff) * desiredGain;
    return this._normalizeGain;
  }

  _updateSilenceGain(detector) {
    const silenceConfig = this._config.silenceRemoval;
    if (!silenceConfig.enabled) {
      return 1.0;
    }

    const threshold = dbToLinear(Number(silenceConfig.thresholdDb || -48));
    const minSilenceFrames = Math.max(1, Math.round(sampleRate * Math.max(Number(silenceConfig.minSilenceMs || 1), 1) / 1000));
    const paddingMs = Math.max(Number(silenceConfig.paddingMs || 1), 1);
    const smoothing = smoothingCoeff(paddingMs);

    if (detector < threshold) {
      this._silenceFrames += 1;
    } else {
      this._silenceFrames = 0;
    }

    const target = this._silenceFrames >= minSilenceFrames ? 0.0 : 1.0;
    this._silenceEnvelope = smoothing * this._silenceEnvelope + (1.0 - smoothing) * target;
    return this._silenceEnvelope;
  }

  _processReverseFrame(frameSamples) {
    const reverseConfig = this._config.reverse;
    if (!reverseConfig.enabled) {
      return frameSamples;
    }

    this._ensureReverseBuffers(frameSamples.length);
    const mix = clamp(Number(reverseConfig.mix || 0), 0.0, 1.0);
    const outputFrame = new Array(frameSamples.length);
    const useReverseOutput = this._reverseOutputReady;

    for (let channel = 0; channel < frameSamples.length; channel += 1) {
      const dry = frameSamples[channel];
      const wet = useReverseOutput ? this._reverseOutputBuffers[channel][this._reverseOutputIndex] : dry;
      outputFrame[channel] = dry * (1.0 - mix) + wet * mix;
      this._reverseInputBuffers[channel][this._reverseWriteIndex] = dry;
    }

    if (useReverseOutput) {
      this._reverseOutputIndex += 1;
      if (this._reverseOutputIndex >= this._reverseWindowFrames) {
        this._reverseOutputIndex = 0;
        this._reverseOutputReady = false;
      }
    }

    this._reverseWriteIndex += 1;
    if (this._reverseWriteIndex >= this._reverseWindowFrames) {
      for (let channel = 0; channel < frameSamples.length; channel += 1) {
        const source = this._reverseInputBuffers[channel];
        const destination = this._reverseOutputBuffers[channel];
        for (let index = 0; index < this._reverseWindowFrames; index += 1) {
          destination[index] = source[this._reverseWindowFrames - index - 1];
        }
      }
      this._reverseWriteIndex = 0;
      this._reverseOutputIndex = 0;
      this._reverseOutputReady = true;
    }

    return outputFrame;
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0];
    const output = outputs[0];

    if (!input || input.length === 0 || !output || output.length === 0) {
      return true;
    }

    const channelCount = output.length;
    const frameCount = output[0].length;
    this._ensureChannelState(channelCount);

    const inputGain = parameters.inputGain[0];
    const drive = parameters.drive[0];
    const monoMix = parameters.monoMix[0];
    const dcBlock = parameters.dcBlock[0];
    const outputGain = parameters.outputGain[0];
    const driveNorm = drive > 1.0 ? Math.tanh(drive) : 1.0;

    for (let frame = 0; frame < frameCount; frame += 1) {
      let mono = 0.0;
      const sourceChannels = Math.max(1, input.length);
      for (let channel = 0; channel < sourceChannels; channel += 1) {
        const samples = input[Math.min(channel, input.length - 1)];
        mono += samples ? samples[frame] : 0.0;
      }
      mono /= sourceChannels;

      let frameSamples = new Array(channelCount);
      for (let channel = 0; channel < channelCount; channel += 1) {
        const source = input[Math.min(channel, input.length - 1)] || input[0];
        const drySample = source ? source[frame] : mono;
        frameSamples[channel] = drySample * (1.0 - monoMix) + mono * monoMix;
      }

      frameSamples = this._processReverseFrame(frameSamples);

      let detector = 0.0;
      for (let channel = 0; channel < channelCount; channel += 1) {
        detector += Math.abs(frameSamples[channel]);
      }
      detector /= Math.max(channelCount, 1);

      const timelineMs = this._currentTimelineMs(frame);
      const timelineGain = this._timelineGain(timelineMs);
      const silenceGain = this._updateSilenceGain(detector);
      const normalizeGain = this._updateNormalizeGain(detector);

      for (let channel = 0; channel < channelCount; channel += 1) {
        let sample = frameSamples[channel];

        sample *= timelineGain;
        sample *= silenceGain;
        sample *= normalizeGain;
        sample *= inputGain;

        if (drive > 1.0) {
          sample = Math.tanh(sample * drive) / driveNorm;
        }

        if (dcBlock >= 0.5) {
          const previousInput = this._dcPrevInput[channel] || 0.0;
          const previousOutput = this._dcPrevOutput[channel] || 0.0;
          const filtered = sample - previousInput + this._dcCoefficient * previousOutput;
          this._dcPrevInput[channel] = sample;
          this._dcPrevOutput[channel] = filtered;
          sample = filtered;
        }

        output[channel][frame] = sample * outputGain;
      }
    }

    return true;
  }
}

registerProcessor("voxis-basic-processor", VoxisBasicProcessor);
