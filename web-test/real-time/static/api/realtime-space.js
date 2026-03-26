function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function createSeededRandom(seed = 12345) {
  let state = seed >>> 0;
  return () => {
    state = (1664525 * state + 1013904223) >>> 0;
    return state / 0xffffffff;
  };
}

function copyAudioBuffer(audioContext, sourceBuffer, normalize = false) {
  const channels = Math.max(1, Math.min(2, sourceBuffer.numberOfChannels));
  const length = sourceBuffer.length;
  const buffer = audioContext.createBuffer(2, length, audioContext.sampleRate);
  let peak = 0.0;

  for (let channel = 0; channel < channels; channel += 1) {
    const source = sourceBuffer.getChannelData(channel);
    const destination = buffer.getChannelData(channel);
    destination.set(source);
    for (let index = 0; index < source.length; index += 1) {
      peak = Math.max(peak, Math.abs(source[index]));
    }
  }

  if (channels === 1) {
    buffer.copyToChannel(buffer.getChannelData(0), 1);
  }

  if (normalize && peak > 1e-6) {
    const scale = 1.0 / peak;
    for (let channel = 0; channel < 2; channel += 1) {
      const data = buffer.getChannelData(channel);
      for (let index = 0; index < data.length; index += 1) {
        data[index] *= scale;
      }
    }
  }

  return buffer;
}

function createBufferFromChannels(audioContext, channelsData, normalize = false) {
  const length = channelsData[0]?.length ?? 1;
  const buffer = audioContext.createBuffer(2, length, audioContext.sampleRate);
  let peak = 0.0;

  for (let channel = 0; channel < 2; channel += 1) {
    const source = channelsData[Math.min(channel, channelsData.length - 1)] ?? new Float32Array(length);
    const destination = buffer.getChannelData(channel);
    destination.set(source);
    for (let index = 0; index < source.length; index += 1) {
      peak = Math.max(peak, Math.abs(source[index]));
    }
  }

  if (normalize && peak > 1e-6) {
    const scale = 1.0 / peak;
    for (let channel = 0; channel < 2; channel += 1) {
      const data = buffer.getChannelData(channel);
      for (let index = 0; index < data.length; index += 1) {
        data[index] *= scale;
      }
    }
  }

  return buffer;
}

function buildMultiTapImpulse(audioContext, { delayMs, taps, spacingMs, decay }) {
  const tapCount = Math.max(1, Math.round(taps));
  const maxDelayMs = delayMs + Math.max(0, tapCount - 1) * spacingMs + 5.0;
  const length = Math.max(2, Math.ceil(maxDelayMs * audioContext.sampleRate / 1000.0) + 1);
  const left = new Float32Array(length);
  const right = new Float32Array(length);

  for (let tapIndex = 0; tapIndex < tapCount; tapIndex += 1) {
    const tapDelayMs = Math.max(0.001, delayMs + tapIndex * spacingMs);
    const frame = Math.min(length - 1, Math.round(tapDelayMs * audioContext.sampleRate / 1000.0));
    const amplitude = Math.pow(decay, tapIndex);
    left[frame] += amplitude;
    right[frame] += amplitude;
  }

  return createBufferFromChannels(audioContext, [left, right], false);
}

function buildEarlyReflectionsImpulse(audioContext, { preDelayMs, spreadMs, taps, decay }) {
  const tapCount = Math.max(1, Math.round(taps));
  const maxDelayMs = preDelayMs + tapCount * spreadMs + 4.0;
  const length = Math.max(4, Math.ceil(maxDelayMs * audioContext.sampleRate / 1000.0) + 1);
  const left = new Float32Array(length);
  const right = new Float32Array(length);

  for (let tapIndex = 0; tapIndex < tapCount; tapIndex += 1) {
    const tapDelayMs = preDelayMs + tapIndex * spreadMs;
    const frame = Math.min(length - 1, Math.round(tapDelayMs * audioContext.sampleRate / 1000.0));
    const amplitude = Math.pow(decay, tapIndex) * (1.0 - 0.08 * tapIndex);
    left[frame] += amplitude;
    const shiftedFrame = Math.min(length - 1, frame + 2);
    right[shiftedFrame] += amplitude;
  }

  return createBufferFromChannels(audioContext, [left, right], false);
}

function lowpassNoise(signal, sampleRate, cutoffHz) {
  if (cutoffHz <= 0.0) {
    return signal;
  }
  const alphaBase = Math.min(0.999, 2.0 * Math.PI * cutoffHz / Math.max(sampleRate, 1));
  const alpha = alphaBase / (alphaBase + 1.0);
  const output = new Float32Array(signal.length);
  output[0] = signal[0];
  for (let index = 1; index < signal.length; index += 1) {
    output[index] = output[index - 1] + alpha * (signal[index] - output[index - 1]);
  }
  return output;
}

function buildSyntheticReverbImpulse(audioContext, kind, { decaySeconds, toneHz }) {
  const random = createSeededRandom(12345);
  const length = Math.max(64, Math.round(audioContext.sampleRate * Math.max(decaySeconds, 0.05)));
  const leftNoise = new Float32Array(length);
  const rightNoise = new Float32Array(length);
  for (let index = 0; index < length; index += 1) {
    leftNoise[index] = random() * 2.0 - 1.0;
    rightNoise[index] = random() * 2.0 - 1.0;
  }

  const left = lowpassNoise(leftNoise, audioContext.sampleRate, toneHz);
  const right = lowpassNoise(rightNoise, audioContext.sampleRate, toneHz);
  const decayCurve = new Float32Array(length);
  for (let index = 0; index < length; index += 1) {
    const timeSeconds = index / audioContext.sampleRate;
    decayCurve[index] = Math.exp(-timeSeconds / Math.max(decaySeconds, 0.05));
  }

  let earlySettings;
  let modulation = 1.0;
  if (kind === "room") {
    earlySettings = { preDelayMs: 8.0, spreadMs: 7.0, taps: 5, decay: 0.72 };
    modulation = 1.1;
  } else if (kind === "hall") {
    earlySettings = { preDelayMs: 18.0, spreadMs: 11.0, taps: 8, decay: 0.82 };
    modulation = 1.35;
  } else {
    earlySettings = { preDelayMs: 10.0, spreadMs: 5.5, taps: 7, decay: 0.76 };
    modulation = 0.95;
  }

  const early = buildEarlyReflectionsImpulse(audioContext, earlySettings);
  const earlyLeft = early.getChannelData(0);
  const earlyRight = early.getChannelData(1);

  for (let index = 0; index < length; index += 1) {
    left[index] *= decayCurve[index] * modulation;
    right[index] *= decayCurve[index] * modulation;
  }

  left[0] += 1.0;
  right[0] += 1.0;
  for (let index = 0; index < early.length && index < length; index += 1) {
    left[index] += earlyLeft[index];
    right[index] += earlyRight[index];
  }

  return createBufferFromChannels(audioContext, [left, right], true);
}

function createSimpleDelayUnit(audioContext, maxDelaySeconds = 2.5) {
  const input = audioContext.createGain();
  const output = audioContext.createGain();
  const dryGain = audioContext.createGain();
  const delay = audioContext.createDelay(maxDelaySeconds);
  const feedbackGain = audioContext.createGain();
  const wetGain = audioContext.createGain();

  input.connect(dryGain);
  dryGain.connect(output);
  input.connect(delay);
  delay.connect(wetGain);
  wetGain.connect(output);
  delay.connect(feedbackGain);
  feedbackGain.connect(delay);

  return {
    input,
    output,
    configure(config) {
      if (!config.enabled) {
        dryGain.gain.value = 1.0;
        wetGain.gain.value = 0.0;
        feedbackGain.gain.value = 0.0;
        return;
      }
      delay.delayTime.value = Math.max(0.001, config.delayMs / 1000.0);
      dryGain.gain.value = 1.0 - clamp(config.mix, 0.0, 1.0);
      wetGain.gain.value = clamp(config.mix, 0.0, 1.0);
      feedbackGain.gain.value = clamp(config.feedback ?? 0.0, -0.99, 0.99);
    },
  };
}

function createPingPongUnit(audioContext, maxDelaySeconds = 2.5) {
  const input = audioContext.createGain();
  const output = audioContext.createGain();
  const dryGain = audioContext.createGain();
  const splitter = audioContext.createChannelSplitter(2);
  const merger = audioContext.createChannelMerger(2);
  const delayLeft = audioContext.createDelay(maxDelaySeconds);
  const delayRight = audioContext.createDelay(maxDelaySeconds);
  const feedbackLeft = audioContext.createGain();
  const feedbackRight = audioContext.createGain();
  const wetGain = audioContext.createGain();

  input.connect(dryGain);
  dryGain.connect(output);
  input.connect(splitter);
  splitter.connect(delayLeft, 0);
  splitter.connect(delayRight, 1);
  delayLeft.connect(feedbackLeft);
  feedbackLeft.connect(delayRight);
  delayRight.connect(feedbackRight);
  feedbackRight.connect(delayLeft);
  delayLeft.connect(merger, 0, 0);
  delayRight.connect(merger, 0, 1);
  merger.connect(wetGain);
  wetGain.connect(output);

  return {
    input,
    output,
    configure(config) {
      if (!config.enabled) {
        dryGain.gain.value = 1.0;
        wetGain.gain.value = 0.0;
        feedbackLeft.gain.value = 0.0;
        feedbackRight.gain.value = 0.0;
        return;
      }
      const delaySeconds = Math.max(0.001, config.delayMs / 1000.0);
      delayLeft.delayTime.value = delaySeconds;
      delayRight.delayTime.value = delaySeconds;
      dryGain.gain.value = 1.0 - clamp(config.mix, 0.0, 1.0);
      wetGain.gain.value = clamp(config.mix, 0.0, 1.0);
      feedbackLeft.gain.value = clamp(config.feedback ?? 0.0, -0.99, 0.99);
      feedbackRight.gain.value = clamp(config.feedback ?? 0.0, -0.99, 0.99);
    },
  };
}

function createConvolverUnit(audioContext) {
  const input = audioContext.createGain();
  const output = audioContext.createGain();
  const dryGain = audioContext.createGain();
  const convolver = audioContext.createConvolver();
  const wetGain = audioContext.createGain();

  convolver.normalize = false;
  input.connect(dryGain);
  dryGain.connect(output);
  input.connect(convolver);
  convolver.connect(wetGain);
  wetGain.connect(output);

  return {
    input,
    output,
    setBuffer(buffer) {
      convolver.buffer = buffer;
    },
    configure(config) {
      const enabled = config.enabled && Boolean(config.buffer);
      if (!enabled) {
        dryGain.gain.value = 1.0;
        wetGain.gain.value = 0.0;
        return;
      }
      dryGain.gain.value = 1.0 - clamp(config.mix, 0.0, 1.0);
      wetGain.gain.value = clamp(config.mix, 0.0, 1.0);
      convolver.buffer = config.buffer;
    },
  };
}

function makeCacheSignature(parts) {
  return JSON.stringify(parts);
}

export function createSpaceRack(audioContext) {
  const input = audioContext.createGain();
  const output = audioContext.createGain();

  const units = {
    delay: createSimpleDelayUnit(audioContext, 2.5),
    echo: createSimpleDelayUnit(audioContext, 2.5),
    pingPongDelay: createPingPongUnit(audioContext, 2.5),
    multiTapDelay: createConvolverUnit(audioContext),
    slapbackDelay: createSimpleDelayUnit(audioContext, 1.0),
    earlyReflections: createConvolverUnit(audioContext),
    roomReverb: createConvolverUnit(audioContext),
    hallReverb: createConvolverUnit(audioContext),
    plateReverb: createConvolverUnit(audioContext),
    convolutionReverb: createConvolverUnit(audioContext),
  };

  const orderedUnits = [
    units.delay,
    units.echo,
    units.pingPongDelay,
    units.multiTapDelay,
    units.slapbackDelay,
    units.earlyReflections,
    units.roomReverb,
    units.hallReverb,
    units.plateReverb,
    units.convolutionReverb,
  ];

  let cursor = input;
  orderedUnits.forEach((unit) => {
    cursor.connect(unit.input);
    cursor = unit.output;
  });
  cursor.connect(output);

  const generatedBuffers = {
    multiTapDelay: { signature: null, buffer: null },
    earlyReflections: { signature: null, buffer: null },
    roomReverb: { signature: null, buffer: null },
    hallReverb: { signature: null, buffer: null },
    plateReverb: { signature: null, buffer: null },
  };

  function getCachedBuffer(cacheKey, enabled, signature, buildBuffer) {
    if (!enabled) {
      return null;
    }

    const cache = generatedBuffers[cacheKey];
    if (!cache.buffer || cache.signature !== signature) {
      cache.signature = signature;
      cache.buffer = buildBuffer();
    }
    return cache.buffer;
  }

  let convolutionBuffer = null;
  let convolutionSourceBuffer = null;
  let convolutionNormalized = true;

  function refreshConvolutionBuffer(normalizeIr) {
    if (!convolutionSourceBuffer) {
      convolutionBuffer = null;
      units.convolutionReverb.setBuffer(null);
      return null;
    }

    if (convolutionBuffer && convolutionNormalized === normalizeIr) {
      return convolutionBuffer;
    }

    convolutionNormalized = normalizeIr;
    convolutionBuffer = copyAudioBuffer(audioContext, convolutionSourceBuffer, normalizeIr);
    units.convolutionReverb.setBuffer(convolutionBuffer);
    return convolutionBuffer;
  }

  return {
    input,
    output,
    async loadConvolutionFile(file, normalizeIr = true) {
      const bytes = await file.arrayBuffer();
      convolutionSourceBuffer = await audioContext.decodeAudioData(bytes.slice(0));
      convolutionBuffer = null;
      refreshConvolutionBuffer(normalizeIr);
      return convolutionBuffer;
    },
    clearConvolutionFile() {
      convolutionBuffer = null;
      convolutionSourceBuffer = null;
      units.convolutionReverb.setBuffer(null);
    },
    configure(config) {
      units.delay.configure(config.delay);
      units.echo.configure(config.echo);
      units.pingPongDelay.configure(config.pingPongDelay);
      units.slapbackDelay.configure(config.slapbackDelay);

      const multiTapBuffer = getCachedBuffer(
        "multiTapDelay",
        config.multiTapDelay.enabled,
        makeCacheSignature([
          config.multiTapDelay.delayMs,
          config.multiTapDelay.taps,
          config.multiTapDelay.spacingMs,
          config.multiTapDelay.decay,
        ]),
        () => buildMultiTapImpulse(audioContext, config.multiTapDelay),
      );
      units.multiTapDelay.configure({
        enabled: config.multiTapDelay.enabled,
        mix: config.multiTapDelay.mix,
        buffer: multiTapBuffer,
      });

      const earlyBuffer = getCachedBuffer(
        "earlyReflections",
        config.earlyReflections.enabled,
        makeCacheSignature([
          config.earlyReflections.preDelayMs,
          config.earlyReflections.spreadMs,
          config.earlyReflections.taps,
          config.earlyReflections.decay,
        ]),
        () => buildEarlyReflectionsImpulse(audioContext, config.earlyReflections),
      );
      units.earlyReflections.configure({
        enabled: config.earlyReflections.enabled,
        mix: config.earlyReflections.mix,
        buffer: earlyBuffer,
      });

      const roomBuffer = getCachedBuffer(
        "roomReverb",
        config.roomReverb.enabled,
        makeCacheSignature([
          config.roomReverb.decaySeconds,
          config.roomReverb.toneHz,
        ]),
        () => buildSyntheticReverbImpulse(audioContext, "room", config.roomReverb),
      );
      units.roomReverb.configure({
        enabled: config.roomReverb.enabled,
        mix: config.roomReverb.mix,
        buffer: roomBuffer,
      });

      const hallBuffer = getCachedBuffer(
        "hallReverb",
        config.hallReverb.enabled,
        makeCacheSignature([
          config.hallReverb.decaySeconds,
          config.hallReverb.toneHz,
        ]),
        () => buildSyntheticReverbImpulse(audioContext, "hall", config.hallReverb),
      );
      units.hallReverb.configure({
        enabled: config.hallReverb.enabled,
        mix: config.hallReverb.mix,
        buffer: hallBuffer,
      });

      const plateBuffer = getCachedBuffer(
        "plateReverb",
        config.plateReverb.enabled,
        makeCacheSignature([
          config.plateReverb.decaySeconds,
          config.plateReverb.toneHz,
        ]),
        () => buildSyntheticReverbImpulse(audioContext, "plate", config.plateReverb),
      );
      units.plateReverb.configure({
        enabled: config.plateReverb.enabled,
        mix: config.plateReverb.mix,
        buffer: plateBuffer,
      });

      refreshConvolutionBuffer(config.convolutionReverb.normalizeIr);

      units.convolutionReverb.configure({
        enabled: config.convolutionReverb.enabled,
        mix: config.convolutionReverb.mix,
        buffer: convolutionBuffer,
      });
    },
  };
}
