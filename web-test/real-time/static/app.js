import { createSpaceRack } from "./api/realtime-space.js";

const $ = (selector) => document.querySelector(selector);

const PARAMETRIC_BANDS = [1, 2, 3];
const GRAPHIC_EQ_BANDS = [100, 250, 1000, 4000, 12000];
const FORMANT_VOWELS = ["A", "E", "I", "O", "U"];

const elements = {
  startEngine: $("#start-engine"),
  useMic: $("#use-mic"),
  stopMic: $("#stop-mic"),
  fileInput: $("#file-input"),
  sourcePlayer: $("#source-player"),
  crossfadeFileInput: $("#crossfade-file-input"),
  crossfadePlayer: $("#crossfade-player"),
  convolutionIrInput: $("#convolution-ir-input"),
  engineState: $("#engine-state"),
  sourceKind: $("#source-kind"),
  crossfadePartnerName: $("#crossfade-partner-name"),
  convolutionIrName: $("#convolution-ir-name"),
  sampleRate: $("#metric-sample-rate"),
  latency: $("#metric-latency"),
  quantum: $("#metric-quantum"),
  mode: $("#metric-mode"),
  meterFill: $("#meter-fill"),
  meterDb: $("#meter-db"),
  presetButtons: [...document.querySelectorAll("[data-preset]")],
  controls: {
    inputGain: $("#input-gain"),
    outputGain: $("#output-gain"),
    normalizeEnabled: $("#normalize-enabled"),
    normalizeHeadroom: $("#normalize-headroom"),
    normalizeMaxGain: $("#normalize-max-gain"),
    fadeInEnabled: $("#fade-in-enabled"),
    fadeInDuration: $("#fade-in-duration"),
    fadeOutEnabled: $("#fade-out-enabled"),
    fadeOutDuration: $("#fade-out-duration"),
    crossfadeEnabled: $("#crossfade-enabled"),
    crossfadeDuration: $("#crossfade-duration"),
    trimEnabled: $("#trim-enabled"),
    trimStart: $("#trim-start"),
    trimEnd: $("#trim-end"),
    trimFeather: $("#trim-feather"),
    cutEnabled: $("#cut-enabled"),
    cutStart: $("#cut-start"),
    cutEnd: $("#cut-end"),
    cutFeather: $("#cut-feather"),
    silenceRemovalEnabled: $("#silence-removal-enabled"),
    silenceRemovalThreshold: $("#silence-removal-threshold"),
    silenceRemovalMin: $("#silence-removal-min"),
    silenceRemovalPadding: $("#silence-removal-padding"),
    reverseEnabled: $("#reverse-enabled"),
    reverseWindow: $("#reverse-window"),
    reverseMix: $("#reverse-mix"),
    pan: $("#pan"),
    monoMix: $("#mono-mix"),
    dcBlock: $("#dc-block"),
    highpassEnabled: $("#highpass-enabled"),
    highpassFreq: $("#highpass-freq"),
    lowpassEnabled: $("#lowpass-enabled"),
    lowpassFreq: $("#lowpass-freq"),
    bandpassEnabled: $("#bandpass-enabled"),
    bandpassFreq: $("#bandpass-freq"),
    bandpassQ: $("#bandpass-q"),
    notchEnabled: $("#notch-enabled"),
    notchFreq: $("#notch-freq"),
    notchQ: $("#notch-q"),
    resonantEnabled: $("#resonant-enabled"),
    resonantMode: $("#resonant-mode"),
    resonantFreq: $("#resonant-freq"),
    resonantResonance: $("#resonant-resonance"),
    peakEqEnabled: $("#peak-eq-enabled"),
    peakEqFreq: $("#peak-eq-freq"),
    peakEqGain: $("#peak-eq-gain"),
    peakEqQ: $("#peak-eq-q"),
    lowShelfEnabled: $("#low-shelf-enabled"),
    lowShelfFreq: $("#low-shelf-freq"),
    lowShelfGain: $("#low-shelf-gain"),
    lowShelfSlope: $("#low-shelf-slope"),
    highShelfEnabled: $("#high-shelf-enabled"),
    highShelfFreq: $("#high-shelf-freq"),
    highShelfGain: $("#high-shelf-gain"),
    highShelfSlope: $("#high-shelf-slope"),
    graphicEqEnabled: $("#graphic-eq-enabled"),
    graphicEqQ: $("#graphic-eq-q"),
    graphicEq100: $("#graphic-eq-100"),
    graphicEq250: $("#graphic-eq-250"),
    graphicEq1000: $("#graphic-eq-1000"),
    graphicEq4000: $("#graphic-eq-4000"),
    graphicEq12000: $("#graphic-eq-12000"),
    dynamicEqEnabled: $("#dynamic-eq-enabled"),
    dynamicEqFrequency: $("#dynamic-eq-frequency"),
    dynamicEqThreshold: $("#dynamic-eq-threshold"),
    dynamicEqCut: $("#dynamic-eq-cut"),
    dynamicEqQ: $("#dynamic-eq-q"),
    formantEnabled: $("#formant-enabled"),
    formantMorph: $("#formant-morph"),
    formantIntensity: $("#formant-intensity"),
    formantQ: $("#formant-q"),
    delayEnabled: $("#delay-enabled"),
    delayTime: $("#delay-time"),
    delayFeedback: $("#delay-feedback"),
    delayMix: $("#delay-mix"),
    compressorEnabled: $("#compressor-enabled"),
    compressorThreshold: $("#compressor-threshold"),
    compressorRatio: $("#compressor-ratio"),
    compressorMakeup: $("#compressor-makeup"),
    downwardEnabled: $("#downward-enabled"),
    downwardThreshold: $("#downward-threshold"),
    downwardRatio: $("#downward-ratio"),
    upwardEnabled: $("#upward-enabled"),
    upwardThreshold: $("#upward-threshold"),
    upwardRatio: $("#upward-ratio"),
    upwardMaxGain: $("#upward-max-gain"),
    limiterEnabled: $("#limiter-enabled"),
    limiterCeiling: $("#limiter-ceiling"),
    expanderEnabled: $("#expander-enabled"),
    expanderThreshold: $("#expander-threshold"),
    expanderRatio: $("#expander-ratio"),
    noiseGateEnabled: $("#noise-gate-enabled"),
    noiseGateThreshold: $("#noise-gate-threshold"),
    noiseGateFloor: $("#noise-gate-floor"),
    deesserEnabled: $("#deesser-enabled"),
    deesserFrequency: $("#deesser-frequency"),
    deesserThreshold: $("#deesser-threshold"),
    deesserAmount: $("#deesser-amount"),
    transientEnabled: $("#transient-enabled"),
    transientAttack: $("#transient-attack"),
    transientSustain: $("#transient-sustain"),
    multibandEnabled: $("#multiband-enabled"),
    multibandLowCut: $("#multiband-low-cut"),
    multibandHighCut: $("#multiband-high-cut"),
    multibandLowThreshold: $("#multiband-low-threshold"),
    multibandMidThreshold: $("#multiband-mid-threshold"),
    multibandHighThreshold: $("#multiband-high-threshold"),
    multibandLowRatio: $("#multiband-low-ratio"),
    multibandMidRatio: $("#multiband-mid-ratio"),
    multibandHighRatio: $("#multiband-high-ratio"),
    multibandAttack: $("#multiband-attack"),
    multibandRelease: $("#multiband-release"),
    multibandLowMakeup: $("#multiband-low-makeup"),
    multibandMidMakeup: $("#multiband-mid-makeup"),
    multibandHighMakeup: $("#multiband-high-makeup"),
    chorusEnabled: $("#chorus-enabled"),
    chorusRate: $("#chorus-rate"),
    chorusDepth: $("#chorus-depth"),
    chorusDelay: $("#chorus-delay"),
    chorusMix: $("#chorus-mix"),
    chorusFeedback: $("#chorus-feedback"),
    flangerEnabled: $("#flanger-enabled"),
    flangerRate: $("#flanger-rate"),
    flangerDepth: $("#flanger-depth"),
    flangerDelay: $("#flanger-delay"),
    flangerMix: $("#flanger-mix"),
    flangerFeedback: $("#flanger-feedback"),
    phaserEnabled: $("#phaser-enabled"),
    phaserRate: $("#phaser-rate"),
    phaserDepth: $("#phaser-depth"),
    phaserCenter: $("#phaser-center"),
    phaserFeedback: $("#phaser-feedback"),
    phaserMix: $("#phaser-mix"),
    phaserStages: $("#phaser-stages"),
    tremoloEnabled: $("#tremolo-enabled"),
    tremoloRate: $("#tremolo-rate"),
    tremoloDepth: $("#tremolo-depth"),
    vibratoEnabled: $("#vibrato-enabled"),
    vibratoRate: $("#vibrato-rate"),
    vibratoDepth: $("#vibrato-depth"),
    vibratoDelay: $("#vibrato-delay"),
    autoPanEnabled: $("#auto-pan-enabled"),
    autoPanRate: $("#auto-pan-rate"),
    autoPanDepth: $("#auto-pan-depth"),
    rotaryEnabled: $("#rotary-enabled"),
    rotaryRate: $("#rotary-rate"),
    rotaryDepth: $("#rotary-depth"),
    rotaryMix: $("#rotary-mix"),
    rotaryCrossover: $("#rotary-crossover"),
    ringModEnabled: $("#ring-mod-enabled"),
    ringModFrequency: $("#ring-mod-frequency"),
    ringModMix: $("#ring-mod-mix"),
    frequencyShifterEnabled: $("#frequency-shifter-enabled"),
    frequencyShifterShift: $("#frequency-shifter-shift"),
    frequencyShifterMix: $("#frequency-shifter-mix"),
    echoEnabled: $("#echo-enabled"),
    echoTime: $("#echo-time"),
    echoFeedback: $("#echo-feedback"),
    echoMix: $("#echo-mix"),
    pingPongEnabled: $("#ping-pong-enabled"),
    pingPongTime: $("#ping-pong-time"),
    pingPongFeedback: $("#ping-pong-feedback"),
    pingPongMix: $("#ping-pong-mix"),
    multiTapEnabled: $("#multi-tap-enabled"),
    multiTapDelay: $("#multi-tap-delay"),
    multiTapTaps: $("#multi-tap-taps"),
    multiTapSpacing: $("#multi-tap-spacing"),
    multiTapDecay: $("#multi-tap-decay"),
    multiTapMix: $("#multi-tap-mix"),
    slapbackEnabled: $("#slapback-enabled"),
    slapbackTime: $("#slapback-time"),
    slapbackMix: $("#slapback-mix"),
    earlyReflectionsEnabled: $("#early-reflections-enabled"),
    earlyReflectionsPreDelay: $("#early-reflections-pre-delay"),
    earlyReflectionsSpread: $("#early-reflections-spread"),
    earlyReflectionsTaps: $("#early-reflections-taps"),
    earlyReflectionsDecay: $("#early-reflections-decay"),
    earlyReflectionsMix: $("#early-reflections-mix"),
    roomReverbEnabled: $("#room-reverb-enabled"),
    roomReverbDecay: $("#room-reverb-decay"),
    roomReverbMix: $("#room-reverb-mix"),
    roomReverbTone: $("#room-reverb-tone"),
    hallReverbEnabled: $("#hall-reverb-enabled"),
    hallReverbDecay: $("#hall-reverb-decay"),
    hallReverbMix: $("#hall-reverb-mix"),
    hallReverbTone: $("#hall-reverb-tone"),
    plateReverbEnabled: $("#plate-reverb-enabled"),
    plateReverbDecay: $("#plate-reverb-decay"),
    plateReverbMix: $("#plate-reverb-mix"),
    plateReverbTone: $("#plate-reverb-tone"),
    convolutionReverbEnabled: $("#convolution-reverb-enabled"),
    convolutionReverbMix: $("#convolution-reverb-mix"),
    convolutionReverbNormalize: $("#convolution-reverb-normalize"),
    distortionEnabled: $("#distortion-enabled"),
    distortionDrive: $("#distortion-drive"),
    overdriveEnabled: $("#overdrive-enabled"),
    overdriveDrive: $("#overdrive-drive"),
    overdriveTone: $("#overdrive-tone"),
    overdriveMix: $("#overdrive-mix"),
    fuzzEnabled: $("#fuzz-enabled"),
    fuzzDrive: $("#fuzz-drive"),
    fuzzBias: $("#fuzz-bias"),
    fuzzMix: $("#fuzz-mix"),
    bitcrusherEnabled: $("#bitcrusher-enabled"),
    bitcrusherBitDepth: $("#bitcrusher-bit-depth"),
    bitcrusherSampleRateReduction: $("#bitcrusher-sample-rate-reduction"),
    bitcrusherMix: $("#bitcrusher-mix"),
    waveshaperEnabled: $("#waveshaper-enabled"),
    waveshaperAmount: $("#waveshaper-amount"),
    waveshaperSymmetry: $("#waveshaper-symmetry"),
    waveshaperMix: $("#waveshaper-mix"),
    tubeSaturationEnabled: $("#tube-saturation-enabled"),
    tubeSaturationDrive: $("#tube-saturation-drive"),
    tubeSaturationBias: $("#tube-saturation-bias"),
    tubeSaturationMix: $("#tube-saturation-mix"),
    tapeSaturationEnabled: $("#tape-saturation-enabled"),
    tapeSaturationDrive: $("#tape-saturation-drive"),
    tapeSaturationSoftness: $("#tape-saturation-softness"),
    tapeSaturationMix: $("#tape-saturation-mix"),
    softClippingEnabled: $("#soft-clipping-enabled"),
    softClippingThreshold: $("#soft-clipping-threshold"),
    hardClippingEnabled: $("#hard-clipping-enabled"),
    hardClippingThreshold: $("#hard-clipping-threshold"),
    pitchShiftEnabled: $("#pitch-shift-enabled"),
    pitchShiftSemitones: $("#pitch-shift-semitones"),
    pitchShiftMix: $("#pitch-shift-mix"),
    timeStretchEnabled: $("#time-stretch-enabled"),
    timeStretchRate: $("#time-stretch-rate"),
    timeCompressionEnabled: $("#time-compression-enabled"),
    timeCompressionRate: $("#time-compression-rate"),
    autoTuneEnabled: $("#auto-tune-enabled"),
    autoTuneStrength: $("#auto-tune-strength"),
    autoTuneKey: $("#auto-tune-key"),
    autoTuneScale: $("#auto-tune-scale"),
    autoTuneMinHz: $("#auto-tune-min-hz"),
    autoTuneMaxHz: $("#auto-tune-max-hz"),
    harmonizerEnabled: $("#harmonizer-enabled"),
    harmonizerIntervalA: $("#harmonizer-interval-a"),
    harmonizerIntervalB: $("#harmonizer-interval-b"),
    harmonizerIntervalC: $("#harmonizer-interval-c"),
    harmonizerMix: $("#harmonizer-mix"),
    octaverEnabled: $("#octaver-enabled"),
    octaverDown: $("#octaver-down"),
    octaverUp: $("#octaver-up"),
    octaverDownMix: $("#octaver-down-mix"),
    octaverUpMix: $("#octaver-up-mix"),
    formantShiftingEnabled: $("#formant-shifting-enabled"),
    formantShiftingShift: $("#formant-shifting-shift"),
    formantShiftingMix: $("#formant-shifting-mix"),
    noiseReductionEnabled: $("#noise-reduction-enabled"),
    noiseReductionStrength: $("#noise-reduction-strength"),
    voiceIsolationEnabled: $("#voice-isolation-enabled"),
    voiceIsolationStrength: $("#voice-isolation-strength"),
    voiceIsolationLowHz: $("#voice-isolation-low-hz"),
    voiceIsolationHighHz: $("#voice-isolation-high-hz"),
    sourceSeparationEnabled: $("#source-separation-enabled"),
    sourceSeparationTarget: $("#source-separation-target"),
    sourceSeparationStrength: $("#source-separation-strength"),
    sourceSeparationLowHz: $("#source-separation-low-hz"),
    sourceSeparationHighHz: $("#source-separation-high-hz"),
    deReverbEnabled: $("#de-reverb-enabled"),
    deReverbAmount: $("#de-reverb-amount"),
    deReverbTailMs: $("#de-reverb-tail-ms"),
    deEchoEnabled: $("#de-echo-enabled"),
    deEchoAmount: $("#de-echo-amount"),
    deEchoMinDelayMs: $("#de-echo-min-delay-ms"),
    deEchoMaxDelayMs: $("#de-echo-max-delay-ms"),
    spectralRepairEnabled: $("#spectral-repair-enabled"),
    spectralRepairStrength: $("#spectral-repair-strength"),
    aiEnhancerEnabled: $("#ai-enhancer-enabled"),
    aiEnhancerAmount: $("#ai-enhancer-amount"),
    speechEnhancementEnabled: $("#speech-enhancement-enabled"),
    speechEnhancementAmount: $("#speech-enhancement-amount"),
    glitchEffectEnabled: $("#glitch-effect-enabled"),
    glitchEffectSliceMs: $("#glitch-effect-slice-ms"),
    glitchEffectRepeatProbability: $("#glitch-effect-repeat-probability"),
    glitchEffectDropoutProbability: $("#glitch-effect-dropout-probability"),
    glitchEffectReverseProbability: $("#glitch-effect-reverse-probability"),
    glitchEffectMix: $("#glitch-effect-mix"),
    stutterEnabled: $("#stutter-enabled"),
    stutterSliceMs: $("#stutter-slice-ms"),
    stutterRepeats: $("#stutter-repeats"),
    stutterIntervalMs: $("#stutter-interval-ms"),
    stutterMix: $("#stutter-mix"),
    tapeStopEnabled: $("#tape-stop-enabled"),
    tapeStopStopTimeMs: $("#tape-stop-stop-time-ms"),
    tapeStopCurve: $("#tape-stop-curve"),
    tapeStopMix: $("#tape-stop-mix"),
    reverseReverbEnabled: $("#reverse-reverb-enabled"),
    reverseReverbDecaySeconds: $("#reverse-reverb-decay-seconds"),
    reverseReverbMix: $("#reverse-reverb-mix"),
    granularSynthesisEnabled: $("#granular-synthesis-enabled"),
    granularSynthesisGrainMs: $("#granular-synthesis-grain-ms"),
    granularSynthesisOverlap: $("#granular-synthesis-overlap"),
    granularSynthesisJitterMs: $("#granular-synthesis-jitter-ms"),
    granularSynthesisMix: $("#granular-synthesis-mix"),
    timeSlicingEnabled: $("#time-slicing-enabled"),
    timeSlicingSliceMs: $("#time-slicing-slice-ms"),
    timeSlicingMix: $("#time-slicing-mix"),
    randomPitchModEnabled: $("#random-pitch-mod-enabled"),
    randomPitchModDepthSemitones: $("#random-pitch-mod-depth-semitones"),
    randomPitchModSegmentMs: $("#random-pitch-mod-segment-ms"),
    randomPitchModMix: $("#random-pitch-mod-mix"),
    vinylEffectEnabled: $("#vinyl-effect-enabled"),
    vinylEffectNoise: $("#vinyl-effect-noise"),
    vinylEffectWow: $("#vinyl-effect-wow"),
    vinylEffectCrackle: $("#vinyl-effect-crackle"),
    vinylEffectMix: $("#vinyl-effect-mix"),
    radioEffectEnabled: $("#radio-effect-enabled"),
    radioEffectNoiseLevel: $("#radio-effect-noise-level"),
    radioEffectMix: $("#radio-effect-mix"),
    telephoneEffectEnabled: $("#telephone-effect-enabled"),
    telephoneEffectMix: $("#telephone-effect-mix"),
    retro8bitEnabled: $("#retro-8bit-enabled"),
    retro8bitBitDepth: $("#retro-8bit-bit-depth"),
    retro8bitSampleRateReduction: $("#retro-8bit-sample-rate-reduction"),
    retro8bitMix: $("#retro-8bit-mix"),
    slowMotionExtremeEnabled: $("#slow-motion-extreme-enabled"),
    slowMotionExtremeRate: $("#slow-motion-extreme-rate"),
    slowMotionExtremeToneHz: $("#slow-motion-extreme-tone-hz"),
    slowMotionExtremeMix: $("#slow-motion-extreme-mix"),
    robotVoiceEnabled: $("#robot-voice-enabled"),
    robotVoiceCarrierHz: $("#robot-voice-carrier-hz"),
    robotVoiceMix: $("#robot-voice-mix"),
    alienVoiceEnabled: $("#alien-voice-enabled"),
    alienVoiceShiftSemitones: $("#alien-voice-shift-semitones"),
    alienVoiceFormantShift: $("#alien-voice-formant-shift"),
    alienVoiceMix: $("#alien-voice-mix"),
    fftFilterEnabled: $("#fft-filter-enabled"),
    fftFilterLowHz: $("#fft-filter-low-hz"),
    fftFilterHighHz: $("#fft-filter-high-hz"),
    fftFilterMix: $("#fft-filter-mix"),
    spectralGatingEnabled: $("#spectral-gating-enabled"),
    spectralGatingThresholdDb: $("#spectral-gating-threshold-db"),
    spectralGatingFloor: $("#spectral-gating-floor"),
    spectralBlurEnabled: $("#spectral-blur-enabled"),
    spectralBlurAmount: $("#spectral-blur-amount"),
    spectralFreezeEnabled: $("#spectral-freeze-enabled"),
    spectralFreezeStartMs: $("#spectral-freeze-start-ms"),
    spectralFreezeMix: $("#spectral-freeze-mix"),
    spectralMorphingEnabled: $("#spectral-morphing-enabled"),
    spectralMorphingAmount: $("#spectral-morphing-amount"),
    phaseVocoderEnabled: $("#phase-vocoder-enabled"),
    phaseVocoderRate: $("#phase-vocoder-rate"),
    harmonicPercussiveSeparationEnabled: $("#harmonic-percussive-separation-enabled"),
    harmonicPercussiveSeparationTarget: $("#harmonic-percussive-separation-target"),
    harmonicPercussiveSeparationMix: $("#harmonic-percussive-separation-mix"),
    spectralDelayEnabled: $("#spectral-delay-enabled"),
    spectralDelayMaxDelayMs: $("#spectral-delay-max-delay-ms"),
    spectralDelayFeedback: $("#spectral-delay-feedback"),
    spectralDelayMix: $("#spectral-delay-mix"),
    stereoWideningEnabled: $("#stereo-widening-enabled"),
    stereoWideningAmount: $("#stereo-widening-amount"),
    midSideProcessingEnabled: $("#mid-side-processing-enabled"),
    midSideProcessingMidGainDb: $("#mid-side-processing-mid-gain-db"),
    midSideProcessingSideGainDb: $("#mid-side-processing-side-gain-db"),
    stereoImagerEnabled: $("#stereo-imager-enabled"),
    stereoImagerLowWidth: $("#stereo-imager-low-width"),
    stereoImagerHighWidth: $("#stereo-imager-high-width"),
    stereoImagerCrossoverHz: $("#stereo-imager-crossover-hz"),
    binauralEffectEnabled: $("#binaural-effect-enabled"),
    binauralEffectAzimuthDeg: $("#binaural-effect-azimuth-deg"),
    binauralEffectDistance: $("#binaural-effect-distance"),
    binauralEffectRoomMix: $("#binaural-effect-room-mix"),
    spatialPositioningEnabled: $("#spatial-positioning-enabled"),
    spatialPositioningAzimuthDeg: $("#spatial-positioning-azimuth-deg"),
    spatialPositioningElevationDeg: $("#spatial-positioning-elevation-deg"),
    spatialPositioningDistance: $("#spatial-positioning-distance"),
    hrtfSimulationEnabled: $("#hrtf-simulation-enabled"),
    hrtfSimulationAzimuthDeg: $("#hrtf-simulation-azimuth-deg"),
    hrtfSimulationElevationDeg: $("#hrtf-simulation-elevation-deg"),
    hrtfSimulationDistance: $("#hrtf-simulation-distance"),
    parametric1Enabled: $("#parametric-1-enabled"),
    parametric1Kind: $("#parametric-1-kind"),
    parametric1Freq: $("#parametric-1-freq"),
    parametric1Gain: $("#parametric-1-gain"),
    parametric1Q: $("#parametric-1-q"),
    parametric2Enabled: $("#parametric-2-enabled"),
    parametric2Kind: $("#parametric-2-kind"),
    parametric2Freq: $("#parametric-2-freq"),
    parametric2Gain: $("#parametric-2-gain"),
    parametric2Q: $("#parametric-2-q"),
    parametric3Enabled: $("#parametric-3-enabled"),
    parametric3Kind: $("#parametric-3-kind"),
    parametric3Freq: $("#parametric-3-freq"),
    parametric3Gain: $("#parametric-3-gain"),
    parametric3Q: $("#parametric-3-q"),
    drive: $("#drive"),
  },
};

const state = {
  audioContext: null,
  graph: null,
  activeSourceNode: null,
  secondarySourceNode: null,
  micStream: null,
  mediaElementSource: null,
  secondaryMediaSource: null,
  objectUrl: null,
  secondaryObjectUrl: null,
  meterFrame: null,
  dynamicsWasmBytes: null,
  basicConfigTimer: null,
  pendingBasicConfig: null,
  colorTimeConfigTimer: null,
  pendingColorTimeConfig: null,
  modernCreativeConfigTimer: null,
  pendingModernCreativeConfig: null,
  spectralSpatialConfigTimer: null,
  pendingSpectralSpatialConfig: null,
  modulationConfigTimer: null,
  pendingModulationConfig: null,
  dynamicsConfigTimer: null,
  pendingDynamicsConfig: null,
  spaceConfigTimer: null,
  pendingSpaceConfig: null,
  sourceMode: "none",
  primaryLabel: "No source connected",
  secondaryStarted: false,
};

const defaultControlValues = {
  inputGain: 1.0,
  outputGain: 1.0,
  normalizeEnabled: false,
  normalizeHeadroom: 1.0,
  normalizeMaxGain: 4.0,
  fadeInEnabled: false,
  fadeInDuration: 400,
  fadeOutEnabled: false,
  fadeOutDuration: 500,
  crossfadeEnabled: false,
  crossfadeDuration: 1200,
  trimEnabled: false,
  trimStart: 0,
  trimEnd: 30000,
  trimFeather: 12,
  cutEnabled: false,
  cutStart: 1200,
  cutEnd: 2200,
  cutFeather: 12,
  silenceRemovalEnabled: false,
  silenceRemovalThreshold: -48,
  silenceRemovalMin: 80,
  silenceRemovalPadding: 10,
  reverseEnabled: false,
  reverseWindow: 350,
  reverseMix: 1.0,
  pan: 0.0,
  monoMix: 0.0,
  dcBlock: true,
  highpassEnabled: true,
  highpassFreq: 80,
  lowpassEnabled: false,
  lowpassFreq: 18000,
  bandpassEnabled: false,
  bandpassFreq: 1200,
  bandpassQ: 0.9,
  notchEnabled: false,
  notchFreq: 3500,
  notchQ: 2.0,
  resonantEnabled: false,
  resonantMode: "lowpass",
  resonantFreq: 1200,
  resonantResonance: 1.6,
  peakEqEnabled: false,
  peakEqFreq: 2800,
  peakEqGain: 0.0,
  peakEqQ: 1.0,
  lowShelfEnabled: false,
  lowShelfFreq: 120,
  lowShelfGain: 0.0,
  lowShelfSlope: 1.0,
  highShelfEnabled: false,
  highShelfFreq: 9500,
  highShelfGain: 0.0,
  highShelfSlope: 1.0,
  graphicEqEnabled: false,
  graphicEqQ: 1.1,
  graphicEq100: 0.0,
  graphicEq250: 0.0,
  graphicEq1000: 0.0,
  graphicEq4000: 0.0,
  graphicEq12000: 0.0,
  dynamicEqEnabled: false,
  dynamicEqFrequency: 2800,
  dynamicEqThreshold: -24,
  dynamicEqCut: -6,
  dynamicEqQ: 1.2,
  formantEnabled: false,
  formantMorph: 0.0,
  formantIntensity: 1.0,
  formantQ: 4.0,
  delayEnabled: false,
  delayTime: 180,
  delayFeedback: 0.25,
  delayMix: 0.18,
  compressorEnabled: true,
  compressorThreshold: -18,
  compressorRatio: 3.0,
  compressorMakeup: 0.0,
  downwardEnabled: false,
  downwardThreshold: -18,
  downwardRatio: 4.0,
  upwardEnabled: false,
  upwardThreshold: -42,
  upwardRatio: 2.0,
  upwardMaxGain: 18.0,
  limiterEnabled: false,
  limiterCeiling: -1.0,
  expanderEnabled: false,
  expanderThreshold: -35,
  expanderRatio: 2.0,
  noiseGateEnabled: false,
  noiseGateThreshold: -45,
  noiseGateFloor: -80,
  deesserEnabled: false,
  deesserFrequency: 6500,
  deesserThreshold: -28,
  deesserAmount: 0.8,
  transientEnabled: false,
  transientAttack: 0.7,
  transientSustain: 0.2,
  multibandEnabled: false,
  multibandLowCut: 180,
  multibandHighCut: 3200,
  multibandLowThreshold: -24,
  multibandMidThreshold: -18,
  multibandHighThreshold: -20,
  multibandLowRatio: 2.2,
  multibandMidRatio: 3.0,
  multibandHighRatio: 2.4,
  multibandAttack: 10,
  multibandRelease: 90,
  multibandLowMakeup: 0.0,
  multibandMidMakeup: 0.0,
  multibandHighMakeup: 0.0,
  chorusEnabled: false,
  chorusRate: 0.9,
  chorusDepth: 7.5,
  chorusDelay: 18.0,
  chorusMix: 0.35,
  chorusFeedback: 0.12,
  flangerEnabled: false,
  flangerRate: 0.25,
  flangerDepth: 1.8,
  flangerDelay: 2.5,
  flangerMix: 0.45,
  flangerFeedback: 0.35,
  phaserEnabled: false,
  phaserRate: 0.35,
  phaserDepth: 0.75,
  phaserCenter: 900.0,
  phaserFeedback: 0.2,
  phaserMix: 0.5,
  phaserStages: 4,
  tremoloEnabled: false,
  tremoloRate: 4.0,
  tremoloDepth: 0.5,
  vibratoEnabled: false,
  vibratoRate: 5.0,
  vibratoDepth: 3.5,
  vibratoDelay: 5.5,
  autoPanEnabled: false,
  autoPanRate: 0.35,
  autoPanDepth: 1.0,
  rotaryEnabled: false,
  rotaryRate: 0.8,
  rotaryDepth: 0.7,
  rotaryMix: 0.65,
  rotaryCrossover: 900.0,
  ringModEnabled: false,
  ringModFrequency: 30.0,
  ringModMix: 0.5,
  frequencyShifterEnabled: false,
  frequencyShifterShift: 120.0,
  frequencyShifterMix: 1.0,
  echoEnabled: false,
  echoTime: 320.0,
  echoFeedback: 0.38,
  echoMix: 0.28,
  pingPongEnabled: false,
  pingPongTime: 280.0,
  pingPongFeedback: 0.55,
  pingPongMix: 0.3,
  multiTapEnabled: false,
  multiTapDelay: 120.0,
  multiTapTaps: 4,
  multiTapSpacing: 65.0,
  multiTapDecay: 0.6,
  multiTapMix: 0.32,
  slapbackEnabled: false,
  slapbackTime: 95.0,
  slapbackMix: 0.24,
  earlyReflectionsEnabled: false,
  earlyReflectionsPreDelay: 12.0,
  earlyReflectionsSpread: 8.0,
  earlyReflectionsTaps: 6,
  earlyReflectionsDecay: 0.7,
  earlyReflectionsMix: 0.22,
  roomReverbEnabled: false,
  roomReverbDecay: 0.8,
  roomReverbMix: 0.22,
  roomReverbTone: 8000.0,
  hallReverbEnabled: false,
  hallReverbDecay: 1.8,
  hallReverbMix: 0.28,
  hallReverbTone: 7200.0,
  plateReverbEnabled: false,
  plateReverbDecay: 1.2,
  plateReverbMix: 0.24,
  plateReverbTone: 9500.0,
  convolutionReverbEnabled: false,
  convolutionReverbMix: 0.28,
  convolutionReverbNormalize: true,
  distortionEnabled: false,
  distortionDrive: 2.0,
  overdriveEnabled: false,
  overdriveDrive: 1.8,
  overdriveTone: 0.55,
  overdriveMix: 1.0,
  fuzzEnabled: false,
  fuzzDrive: 3.6,
  fuzzBias: 0.12,
  fuzzMix: 1.0,
  bitcrusherEnabled: false,
  bitcrusherBitDepth: 8,
  bitcrusherSampleRateReduction: 4,
  bitcrusherMix: 1.0,
  waveshaperEnabled: false,
  waveshaperAmount: 1.4,
  waveshaperSymmetry: 0.0,
  waveshaperMix: 1.0,
  tubeSaturationEnabled: false,
  tubeSaturationDrive: 1.6,
  tubeSaturationBias: 0.08,
  tubeSaturationMix: 1.0,
  tapeSaturationEnabled: false,
  tapeSaturationDrive: 1.4,
  tapeSaturationSoftness: 0.35,
  tapeSaturationMix: 1.0,
  softClippingEnabled: false,
  softClippingThreshold: 0.85,
  hardClippingEnabled: false,
  hardClippingThreshold: 0.92,
  pitchShiftEnabled: false,
  pitchShiftSemitones: 0.0,
  pitchShiftMix: 1.0,
  timeStretchEnabled: false,
  timeStretchRate: 0.9,
  timeCompressionEnabled: false,
  timeCompressionRate: 1.15,
  autoTuneEnabled: false,
  autoTuneStrength: 0.7,
  autoTuneKey: "C",
  autoTuneScale: "chromatic",
  autoTuneMinHz: 80.0,
  autoTuneMaxHz: 1000.0,
  harmonizerEnabled: false,
  harmonizerIntervalA: 7.0,
  harmonizerIntervalB: 12.0,
  harmonizerIntervalC: 0.0,
  harmonizerMix: 0.35,
  octaverEnabled: false,
  octaverDown: 1,
  octaverUp: 0,
  octaverDownMix: 0.45,
  octaverUpMix: 0.0,
  formantShiftingEnabled: false,
  formantShiftingShift: 1.12,
  formantShiftingMix: 1.0,
  noiseReductionEnabled: false,
  noiseReductionStrength: 0.5,
  voiceIsolationEnabled: false,
  voiceIsolationStrength: 0.75,
  voiceIsolationLowHz: 120.0,
  voiceIsolationHighHz: 5200.0,
  sourceSeparationEnabled: false,
  sourceSeparationTarget: "vocals",
  sourceSeparationStrength: 0.8,
  sourceSeparationLowHz: 120.0,
  sourceSeparationHighHz: 5200.0,
  deReverbEnabled: false,
  deReverbAmount: 0.45,
  deReverbTailMs: 240.0,
  deEchoEnabled: false,
  deEchoAmount: 0.45,
  deEchoMinDelayMs: 60.0,
  deEchoMaxDelayMs: 800.0,
  spectralRepairEnabled: false,
  spectralRepairStrength: 0.35,
  aiEnhancerEnabled: false,
  aiEnhancerAmount: 0.6,
  speechEnhancementEnabled: false,
  speechEnhancementAmount: 0.7,
  glitchEffectEnabled: false,
  glitchEffectSliceMs: 70.0,
  glitchEffectRepeatProbability: 0.22,
  glitchEffectDropoutProbability: 0.12,
  glitchEffectReverseProbability: 0.10,
  glitchEffectMix: 1.0,
  stutterEnabled: false,
  stutterSliceMs: 90.0,
  stutterRepeats: 3,
  stutterIntervalMs: 480.0,
  stutterMix: 1.0,
  tapeStopEnabled: false,
  tapeStopStopTimeMs: 900.0,
  tapeStopCurve: 2.0,
  tapeStopMix: 1.0,
  reverseReverbEnabled: false,
  reverseReverbDecaySeconds: 1.2,
  reverseReverbMix: 0.45,
  granularSynthesisEnabled: false,
  granularSynthesisGrainMs: 80.0,
  granularSynthesisOverlap: 0.5,
  granularSynthesisJitterMs: 25.0,
  granularSynthesisMix: 1.0,
  timeSlicingEnabled: false,
  timeSlicingSliceMs: 120.0,
  timeSlicingMix: 1.0,
  randomPitchModEnabled: false,
  randomPitchModDepthSemitones: 2.0,
  randomPitchModSegmentMs: 180.0,
  randomPitchModMix: 1.0,
  vinylEffectEnabled: false,
  vinylEffectNoise: 0.08,
  vinylEffectWow: 0.15,
  vinylEffectCrackle: 0.12,
  vinylEffectMix: 1.0,
  radioEffectEnabled: false,
  radioEffectNoiseLevel: 0.04,
  radioEffectMix: 1.0,
  telephoneEffectEnabled: false,
  telephoneEffectMix: 1.0,
  retro8bitEnabled: false,
  retro8bitBitDepth: 6,
  retro8bitSampleRateReduction: 8,
  retro8bitMix: 1.0,
  slowMotionExtremeEnabled: false,
  slowMotionExtremeRate: 0.45,
  slowMotionExtremeToneHz: 4800.0,
  slowMotionExtremeMix: 1.0,
  robotVoiceEnabled: false,
  robotVoiceCarrierHz: 70.0,
  robotVoiceMix: 0.85,
  alienVoiceEnabled: false,
  alienVoiceShiftSemitones: 5.0,
  alienVoiceFormantShift: 1.18,
  alienVoiceMix: 0.8,
  fftFilterEnabled: false,
  fftFilterLowHz: 80.0,
  fftFilterHighHz: 12000.0,
  fftFilterMix: 1.0,
  spectralGatingEnabled: false,
  spectralGatingThresholdDb: -42.0,
  spectralGatingFloor: 0.08,
  spectralBlurEnabled: false,
  spectralBlurAmount: 0.45,
  spectralFreezeEnabled: false,
  spectralFreezeStartMs: 120.0,
  spectralFreezeMix: 0.7,
  spectralMorphingEnabled: false,
  spectralMorphingAmount: 0.5,
  phaseVocoderEnabled: false,
  phaseVocoderRate: 0.85,
  harmonicPercussiveSeparationEnabled: false,
  harmonicPercussiveSeparationTarget: "harmonic",
  harmonicPercussiveSeparationMix: 1.0,
  spectralDelayEnabled: false,
  spectralDelayMaxDelayMs: 240.0,
  spectralDelayFeedback: 0.15,
  spectralDelayMix: 0.35,
  stereoWideningEnabled: false,
  stereoWideningAmount: 1.25,
  midSideProcessingEnabled: false,
  midSideProcessingMidGainDb: 0.0,
  midSideProcessingSideGainDb: 0.0,
  stereoImagerEnabled: false,
  stereoImagerLowWidth: 0.9,
  stereoImagerHighWidth: 1.35,
  stereoImagerCrossoverHz: 280.0,
  binauralEffectEnabled: false,
  binauralEffectAzimuthDeg: 25.0,
  binauralEffectDistance: 1.0,
  binauralEffectRoomMix: 0.08,
  spatialPositioningEnabled: false,
  spatialPositioningAzimuthDeg: 25.0,
  spatialPositioningElevationDeg: 0.0,
  spatialPositioningDistance: 1.0,
  hrtfSimulationEnabled: false,
  hrtfSimulationAzimuthDeg: 30.0,
  hrtfSimulationElevationDeg: 0.0,
  hrtfSimulationDistance: 1.0,
  parametric1Enabled: false,
  parametric1Kind: "peak",
  parametric1Freq: 180,
  parametric1Gain: 0.0,
  parametric1Q: 0.9,
  parametric2Enabled: false,
  parametric2Kind: "peak",
  parametric2Freq: 3000,
  parametric2Gain: 0.0,
  parametric2Q: 1.0,
  parametric3Enabled: false,
  parametric3Kind: "peak",
  parametric3Freq: 9500,
  parametric3Gain: 0.0,
  parametric3Q: 0.8,
  drive: 1.0,
};

const presetOverrides = {
  clean: {
    inputGain: 1.08,
    normalizeEnabled: true,
    normalizeHeadroom: 1.0,
    highpassEnabled: true,
    highpassFreq: 80,
    peakEqEnabled: true,
    peakEqFreq: 3000,
    peakEqGain: 2.4,
    peakEqQ: 0.9,
    highShelfEnabled: true,
    highShelfFreq: 10500,
    highShelfGain: 1.4,
    compressorEnabled: true,
    compressorThreshold: -18,
    compressorRatio: 3.0,
    deesserEnabled: true,
    deesserFrequency: 6500,
    deesserThreshold: -28,
    deesserAmount: 0.75,
  },
  warm: {
    inputGain: 1.12,
    outputGain: 0.9,
    normalizeEnabled: true,
    normalizeHeadroom: 1.5,
    highpassEnabled: true,
    highpassFreq: 70,
    lowpassEnabled: true,
    lowpassFreq: 9500,
    lowShelfEnabled: true,
    lowShelfFreq: 140,
    lowShelfGain: 2.2,
    peakEqEnabled: true,
    peakEqFreq: 2500,
    peakEqGain: 1.6,
    peakEqQ: 0.85,
    drive: 2.3,
    compressorEnabled: true,
    compressorThreshold: -22,
    compressorRatio: 4.2,
    compressorMakeup: 2.5,
    limiterEnabled: true,
  },
  space: {
    outputGain: 0.95,
    highpassEnabled: true,
    highpassFreq: 65,
    highShelfEnabled: true,
    highShelfFreq: 9500,
    highShelfGain: 1.2,
    echoEnabled: true,
    echoTime: 280,
    echoFeedback: 0.36,
    echoMix: 0.24,
    hallReverbEnabled: true,
    hallReverbDecay: 2.4,
    hallReverbMix: 0.18,
    compressorEnabled: true,
    compressorThreshold: -20,
    compressorRatio: 2.6,
    compressorMakeup: 1.5,
  },
  mono: {
    monoMix: 1.0,
    normalizeEnabled: true,
    highpassEnabled: true,
    highpassFreq: 100,
    peakEqEnabled: true,
    peakEqFreq: 1800,
    peakEqGain: 1.5,
    peakEqQ: 1.4,
    compressorEnabled: true,
    compressorThreshold: -16,
    compressorRatio: 2.0,
  },
};

function setEngineState(text) {
  elements.engineState.textContent = text;
}

function setOutput(id, text) {
  const node = document.querySelector(`#${id}`);
  if (node) {
    node.textContent = text;
  }
}

function setCrossfadePartnerName(text) {
  if (elements.crossfadePartnerName) {
    elements.crossfadePartnerName.textContent = text;
  }
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function setPreservesPitch(node, enabled) {
  if (!node) {
    return;
  }
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

function syncPitchTimeTransport() {
  const c = elements.controls;
  let playbackRate = 1.0;
  let preservePitch = false;

  if (c.timeCompressionEnabled.checked) {
    playbackRate = Math.max(1.01, Number(c.timeCompressionRate.value));
    preservePitch = true;
  } else if (c.timeStretchEnabled.checked) {
    playbackRate = clamp(Number(c.timeStretchRate.value), 0.5, 0.99);
    preservePitch = true;
  }

  [elements.sourcePlayer, elements.crossfadePlayer].forEach((player) => {
    if (!player) {
      return;
    }
    player.playbackRate = playbackRate;
    setPreservesPitch(player, preservePitch);
  });

  if (state.sourceMode === "file") {
    updateTransportFromPrimary();
  }
}

function formatMilliseconds(value) {
  return `${Math.round(Number(value))} ms`;
}

function formatFormantMorph(value) {
  const amount = Number(value);
  const lowIndex = Math.max(0, Math.min(FORMANT_VOWELS.length - 1, Math.floor(amount)));
  const highIndex = Math.min(FORMANT_VOWELS.length - 1, lowIndex + 1);
  if (lowIndex === highIndex) {
    return `${amount.toFixed(2)} (${FORMANT_VOWELS[lowIndex]})`;
  }
  return `${amount.toFixed(2)} (${FORMANT_VOWELS[lowIndex]} -> ${FORMANT_VOWELS[highIndex]})`;
}

function updateReadouts() {
  const c = elements.controls;
  setOutput("input-gain-value", `${Number(c.inputGain.value).toFixed(2)}x`);
  setOutput("output-gain-value", `${Number(c.outputGain.value).toFixed(2)}x`);
  setOutput("normalize-headroom-value", `${Number(c.normalizeHeadroom.value).toFixed(1)} dB`);
  setOutput("normalize-max-gain-value", `${Number(c.normalizeMaxGain.value).toFixed(1)}x`);
  setOutput("fade-in-duration-value", formatMilliseconds(c.fadeInDuration.value));
  setOutput("fade-out-duration-value", formatMilliseconds(c.fadeOutDuration.value));
  setOutput("crossfade-duration-value", formatMilliseconds(c.crossfadeDuration.value));
  setOutput("trim-start-value", formatMilliseconds(c.trimStart.value));
  setOutput("trim-end-value", formatMilliseconds(c.trimEnd.value));
  setOutput("trim-feather-value", formatMilliseconds(c.trimFeather.value));
  setOutput("cut-start-value", formatMilliseconds(c.cutStart.value));
  setOutput("cut-end-value", formatMilliseconds(c.cutEnd.value));
  setOutput("cut-feather-value", formatMilliseconds(c.cutFeather.value));
  setOutput("silence-removal-threshold-value", `${Math.round(Number(c.silenceRemovalThreshold.value))} dB`);
  setOutput("silence-removal-min-value", formatMilliseconds(c.silenceRemovalMin.value));
  setOutput("silence-removal-padding-value", formatMilliseconds(c.silenceRemovalPadding.value));
  setOutput("reverse-window-value", formatMilliseconds(c.reverseWindow.value));
  setOutput("reverse-mix-value", `${Math.round(Number(c.reverseMix.value) * 100)}%`);
  setOutput("pan-value", Number(c.pan.value).toFixed(2));
  setOutput("mono-mix-value", `${Math.round(Number(c.monoMix.value) * 100)}%`);
  setOutput("highpass-freq-value", `${Math.round(Number(c.highpassFreq.value))} Hz`);
  setOutput("lowpass-freq-value", `${Math.round(Number(c.lowpassFreq.value))} Hz`);
  setOutput("bandpass-freq-value", `${Math.round(Number(c.bandpassFreq.value))} Hz`);
  setOutput("bandpass-q-value", Number(c.bandpassQ.value).toFixed(2));
  setOutput("notch-freq-value", `${Math.round(Number(c.notchFreq.value))} Hz`);
  setOutput("notch-q-value", Number(c.notchQ.value).toFixed(2));
  setOutput("resonant-freq-value", `${Math.round(Number(c.resonantFreq.value))} Hz`);
  setOutput("resonant-resonance-value", Number(c.resonantResonance.value).toFixed(2));
  setOutput("peak-eq-freq-value", `${Math.round(Number(c.peakEqFreq.value))} Hz`);
  setOutput("peak-eq-gain-value", `${Number(c.peakEqGain.value).toFixed(1)} dB`);
  setOutput("peak-eq-q-value", Number(c.peakEqQ.value).toFixed(2));
  setOutput("low-shelf-freq-value", `${Math.round(Number(c.lowShelfFreq.value))} Hz`);
  setOutput("low-shelf-gain-value", `${Number(c.lowShelfGain.value).toFixed(1)} dB`);
  setOutput("low-shelf-slope-value", Number(c.lowShelfSlope.value).toFixed(2));
  setOutput("high-shelf-freq-value", `${Math.round(Number(c.highShelfFreq.value))} Hz`);
  setOutput("high-shelf-gain-value", `${Number(c.highShelfGain.value).toFixed(1)} dB`);
  setOutput("high-shelf-slope-value", Number(c.highShelfSlope.value).toFixed(2));
  setOutput("graphic-eq-q-value", Number(c.graphicEqQ.value).toFixed(2));
  GRAPHIC_EQ_BANDS.forEach((band) => {
    setOutput(`graphic-eq-${band}-value`, `${Number(c[`graphicEq${band}`].value).toFixed(1)} dB`);
  });
  setOutput("dynamic-eq-frequency-value", `${Math.round(Number(c.dynamicEqFrequency.value))} Hz`);
  setOutput("dynamic-eq-threshold-value", `${Math.round(Number(c.dynamicEqThreshold.value))} dB`);
  setOutput("dynamic-eq-cut-value", `${Number(c.dynamicEqCut.value).toFixed(1)} dB`);
  setOutput("dynamic-eq-q-value", Number(c.dynamicEqQ.value).toFixed(2));
  setOutput("formant-morph-value", formatFormantMorph(c.formantMorph.value));
  setOutput("formant-intensity-value", `${Math.round(Number(c.formantIntensity.value) * 100)}%`);
  setOutput("formant-q-value", Number(c.formantQ.value).toFixed(2));
  PARAMETRIC_BANDS.forEach((index) => {
    setOutput(`parametric-${index}-freq-value`, `${Math.round(Number(c[`parametric${index}Freq`].value))} Hz`);
    setOutput(`parametric-${index}-gain-value`, `${Number(c[`parametric${index}Gain`].value).toFixed(1)} dB`);
    setOutput(`parametric-${index}-q-value`, Number(c[`parametric${index}Q`].value).toFixed(2));
  });
  setOutput("drive-value", `${Number(c.drive.value).toFixed(2)}x`);
  setOutput("delay-time-value", `${Math.round(Number(c.delayTime.value))} ms`);
  setOutput("delay-feedback-value", Number(c.delayFeedback.value).toFixed(2));
  setOutput("delay-mix-value", `${Math.round(Number(c.delayMix.value) * 100)}%`);
  setOutput("compressor-threshold-value", `${Math.round(Number(c.compressorThreshold.value))} dB`);
  setOutput("compressor-ratio-value", `${Number(c.compressorRatio.value).toFixed(2)}:1`);
  setOutput("compressor-makeup-value", `${Number(c.compressorMakeup.value).toFixed(1)} dB`);
  setOutput("downward-threshold-value", `${Math.round(Number(c.downwardThreshold.value))} dB`);
  setOutput("downward-ratio-value", `${Number(c.downwardRatio.value).toFixed(2)}:1`);
  setOutput("upward-threshold-value", `${Math.round(Number(c.upwardThreshold.value))} dB`);
  setOutput("upward-ratio-value", `${Number(c.upwardRatio.value).toFixed(2)}:1`);
  setOutput("upward-max-gain-value", `${Number(c.upwardMaxGain.value).toFixed(1)} dB`);
  setOutput("limiter-ceiling-value", `${Number(c.limiterCeiling.value).toFixed(1)} dB`);
  setOutput("expander-threshold-value", `${Math.round(Number(c.expanderThreshold.value))} dB`);
  setOutput("expander-ratio-value", `${Number(c.expanderRatio.value).toFixed(2)}:1`);
  setOutput("noise-gate-threshold-value", `${Math.round(Number(c.noiseGateThreshold.value))} dB`);
  setOutput("noise-gate-floor-value", `${Math.round(Number(c.noiseGateFloor.value))} dB`);
  setOutput("deesser-frequency-value", `${Math.round(Number(c.deesserFrequency.value))} Hz`);
  setOutput("deesser-threshold-value", `${Math.round(Number(c.deesserThreshold.value))} dB`);
  setOutput("deesser-amount-value", `${Math.round(Number(c.deesserAmount.value) * 100)}%`);
  setOutput("transient-attack-value", Number(c.transientAttack.value).toFixed(2));
  setOutput("transient-sustain-value", Number(c.transientSustain.value).toFixed(2));
  setOutput("multiband-low-cut-value", `${Math.round(Number(c.multibandLowCut.value))} Hz`);
  setOutput("multiband-high-cut-value", `${Math.round(Number(c.multibandHighCut.value))} Hz`);
  setOutput("multiband-low-threshold-value", `${Math.round(Number(c.multibandLowThreshold.value))} dB`);
  setOutput("multiband-mid-threshold-value", `${Math.round(Number(c.multibandMidThreshold.value))} dB`);
  setOutput("multiband-high-threshold-value", `${Math.round(Number(c.multibandHighThreshold.value))} dB`);
  setOutput("multiband-low-ratio-value", `${Number(c.multibandLowRatio.value).toFixed(2)}:1`);
  setOutput("multiband-mid-ratio-value", `${Number(c.multibandMidRatio.value).toFixed(2)}:1`);
  setOutput("multiband-high-ratio-value", `${Number(c.multibandHighRatio.value).toFixed(2)}:1`);
  setOutput("multiband-attack-value", formatMilliseconds(c.multibandAttack.value));
  setOutput("multiband-release-value", formatMilliseconds(c.multibandRelease.value));
  setOutput("multiband-low-makeup-value", `${Number(c.multibandLowMakeup.value).toFixed(1)} dB`);
  setOutput("multiband-mid-makeup-value", `${Number(c.multibandMidMakeup.value).toFixed(1)} dB`);
  setOutput("multiband-high-makeup-value", `${Number(c.multibandHighMakeup.value).toFixed(1)} dB`);
  setOutput("chorus-rate-value", `${Number(c.chorusRate.value).toFixed(2)} Hz`);
  setOutput("chorus-depth-value", formatMilliseconds(c.chorusDepth.value));
  setOutput("chorus-delay-value", formatMilliseconds(c.chorusDelay.value));
  setOutput("chorus-mix-value", `${Math.round(Number(c.chorusMix.value) * 100)}%`);
  setOutput("chorus-feedback-value", Number(c.chorusFeedback.value).toFixed(2));
  setOutput("flanger-rate-value", `${Number(c.flangerRate.value).toFixed(2)} Hz`);
  setOutput("flanger-depth-value", formatMilliseconds(c.flangerDepth.value));
  setOutput("flanger-delay-value", formatMilliseconds(c.flangerDelay.value));
  setOutput("flanger-mix-value", `${Math.round(Number(c.flangerMix.value) * 100)}%`);
  setOutput("flanger-feedback-value", Number(c.flangerFeedback.value).toFixed(2));
  setOutput("phaser-rate-value", `${Number(c.phaserRate.value).toFixed(2)} Hz`);
  setOutput("phaser-depth-value", Number(c.phaserDepth.value).toFixed(2));
  setOutput("phaser-center-value", `${Math.round(Number(c.phaserCenter.value))} Hz`);
  setOutput("phaser-feedback-value", Number(c.phaserFeedback.value).toFixed(2));
  setOutput("phaser-mix-value", `${Math.round(Number(c.phaserMix.value) * 100)}%`);
  setOutput("phaser-stages-value", `${Math.round(Number(c.phaserStages.value))}`);
  setOutput("tremolo-rate-value", `${Number(c.tremoloRate.value).toFixed(2)} Hz`);
  setOutput("tremolo-depth-value", `${Math.round(Number(c.tremoloDepth.value) * 100)}%`);
  setOutput("vibrato-rate-value", `${Number(c.vibratoRate.value).toFixed(2)} Hz`);
  setOutput("vibrato-depth-value", formatMilliseconds(c.vibratoDepth.value));
  setOutput("vibrato-delay-value", formatMilliseconds(c.vibratoDelay.value));
  setOutput("auto-pan-rate-value", `${Number(c.autoPanRate.value).toFixed(2)} Hz`);
  setOutput("auto-pan-depth-value", `${Math.round(Number(c.autoPanDepth.value) * 100)}%`);
  setOutput("rotary-rate-value", `${Number(c.rotaryRate.value).toFixed(2)} Hz`);
  setOutput("rotary-depth-value", `${Math.round(Number(c.rotaryDepth.value) * 100)}%`);
  setOutput("rotary-mix-value", `${Math.round(Number(c.rotaryMix.value) * 100)}%`);
  setOutput("rotary-crossover-value", `${Math.round(Number(c.rotaryCrossover.value))} Hz`);
  setOutput("ring-mod-frequency-value", `${Math.round(Number(c.ringModFrequency.value))} Hz`);
  setOutput("ring-mod-mix-value", `${Math.round(Number(c.ringModMix.value) * 100)}%`);
  setOutput("frequency-shifter-shift-value", `${Math.round(Number(c.frequencyShifterShift.value))} Hz`);
  setOutput("frequency-shifter-mix-value", `${Math.round(Number(c.frequencyShifterMix.value) * 100)}%`);
  setOutput("echo-time-value", formatMilliseconds(c.echoTime.value));
  setOutput("echo-feedback-value", Number(c.echoFeedback.value).toFixed(2));
  setOutput("echo-mix-value", `${Math.round(Number(c.echoMix.value) * 100)}%`);
  setOutput("ping-pong-time-value", formatMilliseconds(c.pingPongTime.value));
  setOutput("ping-pong-feedback-value", Number(c.pingPongFeedback.value).toFixed(2));
  setOutput("ping-pong-mix-value", `${Math.round(Number(c.pingPongMix.value) * 100)}%`);
  setOutput("multi-tap-delay-value", formatMilliseconds(c.multiTapDelay.value));
  setOutput("multi-tap-taps-value", `${Math.round(Number(c.multiTapTaps.value))}`);
  setOutput("multi-tap-spacing-value", formatMilliseconds(c.multiTapSpacing.value));
  setOutput("multi-tap-decay-value", Number(c.multiTapDecay.value).toFixed(2));
  setOutput("multi-tap-mix-value", `${Math.round(Number(c.multiTapMix.value) * 100)}%`);
  setOutput("slapback-time-value", formatMilliseconds(c.slapbackTime.value));
  setOutput("slapback-mix-value", `${Math.round(Number(c.slapbackMix.value) * 100)}%`);
  setOutput("early-reflections-pre-delay-value", formatMilliseconds(c.earlyReflectionsPreDelay.value));
  setOutput("early-reflections-spread-value", formatMilliseconds(c.earlyReflectionsSpread.value));
  setOutput("early-reflections-taps-value", `${Math.round(Number(c.earlyReflectionsTaps.value))}`);
  setOutput("early-reflections-decay-value", Number(c.earlyReflectionsDecay.value).toFixed(2));
  setOutput("early-reflections-mix-value", `${Math.round(Number(c.earlyReflectionsMix.value) * 100)}%`);
  setOutput("room-reverb-decay-value", `${Number(c.roomReverbDecay.value).toFixed(2)} s`);
  setOutput("room-reverb-mix-value", `${Math.round(Number(c.roomReverbMix.value) * 100)}%`);
  setOutput("room-reverb-tone-value", `${Math.round(Number(c.roomReverbTone.value))} Hz`);
  setOutput("hall-reverb-decay-value", `${Number(c.hallReverbDecay.value).toFixed(2)} s`);
  setOutput("hall-reverb-mix-value", `${Math.round(Number(c.hallReverbMix.value) * 100)}%`);
  setOutput("hall-reverb-tone-value", `${Math.round(Number(c.hallReverbTone.value))} Hz`);
  setOutput("plate-reverb-decay-value", `${Number(c.plateReverbDecay.value).toFixed(2)} s`);
  setOutput("plate-reverb-mix-value", `${Math.round(Number(c.plateReverbMix.value) * 100)}%`);
  setOutput("plate-reverb-tone-value", `${Math.round(Number(c.plateReverbTone.value))} Hz`);
  setOutput("convolution-reverb-mix-value", `${Math.round(Number(c.convolutionReverbMix.value) * 100)}%`);
  setOutput("distortion-drive-value", `${Number(c.distortionDrive.value).toFixed(2)}x`);
  setOutput("overdrive-drive-value", `${Number(c.overdriveDrive.value).toFixed(2)}x`);
  setOutput("overdrive-tone-value", `${Math.round(Number(c.overdriveTone.value) * 100)}%`);
  setOutput("overdrive-mix-value", `${Math.round(Number(c.overdriveMix.value) * 100)}%`);
  setOutput("fuzz-drive-value", `${Number(c.fuzzDrive.value).toFixed(2)}x`);
  setOutput("fuzz-bias-value", Number(c.fuzzBias.value).toFixed(2));
  setOutput("fuzz-mix-value", `${Math.round(Number(c.fuzzMix.value) * 100)}%`);
  setOutput("bitcrusher-bit-depth-value", `${Math.round(Number(c.bitcrusherBitDepth.value))}-bit`);
  setOutput("bitcrusher-sample-rate-reduction-value", `${Math.round(Number(c.bitcrusherSampleRateReduction.value))}x`);
  setOutput("bitcrusher-mix-value", `${Math.round(Number(c.bitcrusherMix.value) * 100)}%`);
  setOutput("waveshaper-amount-value", `${Number(c.waveshaperAmount.value).toFixed(2)}x`);
  setOutput("waveshaper-symmetry-value", Number(c.waveshaperSymmetry.value).toFixed(2));
  setOutput("waveshaper-mix-value", `${Math.round(Number(c.waveshaperMix.value) * 100)}%`);
  setOutput("tube-saturation-drive-value", `${Number(c.tubeSaturationDrive.value).toFixed(2)}x`);
  setOutput("tube-saturation-bias-value", Number(c.tubeSaturationBias.value).toFixed(2));
  setOutput("tube-saturation-mix-value", `${Math.round(Number(c.tubeSaturationMix.value) * 100)}%`);
  setOutput("tape-saturation-drive-value", `${Number(c.tapeSaturationDrive.value).toFixed(2)}x`);
  setOutput("tape-saturation-softness-value", `${Math.round(Number(c.tapeSaturationSoftness.value) * 100)}%`);
  setOutput("tape-saturation-mix-value", `${Math.round(Number(c.tapeSaturationMix.value) * 100)}%`);
  setOutput("soft-clipping-threshold-value", Number(c.softClippingThreshold.value).toFixed(2));
  setOutput("hard-clipping-threshold-value", Number(c.hardClippingThreshold.value).toFixed(2));
  setOutput("pitch-shift-semitones-value", `${Number(c.pitchShiftSemitones.value).toFixed(1)} st`);
  setOutput("pitch-shift-mix-value", `${Math.round(Number(c.pitchShiftMix.value) * 100)}%`);
  setOutput("time-stretch-rate-value", `${Number(c.timeStretchRate.value).toFixed(2)}x`);
  setOutput("time-compression-rate-value", `${Number(c.timeCompressionRate.value).toFixed(2)}x`);
  setOutput("auto-tune-strength-value", `${Math.round(Number(c.autoTuneStrength.value) * 100)}%`);
  setOutput("auto-tune-min-hz-value", `${Math.round(Number(c.autoTuneMinHz.value))} Hz`);
  setOutput("auto-tune-max-hz-value", `${Math.round(Number(c.autoTuneMaxHz.value))} Hz`);
  setOutput("harmonizer-interval-a-value", `${Number(c.harmonizerIntervalA.value).toFixed(1)} st`);
  setOutput("harmonizer-interval-b-value", `${Number(c.harmonizerIntervalB.value).toFixed(1)} st`);
  setOutput("harmonizer-interval-c-value", `${Number(c.harmonizerIntervalC.value).toFixed(1)} st`);
  setOutput("harmonizer-mix-value", `${Math.round(Number(c.harmonizerMix.value) * 100)}%`);
  setOutput("octaver-down-value", `${Math.round(Number(c.octaverDown.value))}`);
  setOutput("octaver-up-value", `${Math.round(Number(c.octaverUp.value))}`);
  setOutput("octaver-down-mix-value", `${Math.round(Number(c.octaverDownMix.value) * 100)}%`);
  setOutput("octaver-up-mix-value", `${Math.round(Number(c.octaverUpMix.value) * 100)}%`);
  setOutput("formant-shifting-shift-value", `${Number(c.formantShiftingShift.value).toFixed(2)}x`);
  setOutput("formant-shifting-mix-value", `${Math.round(Number(c.formantShiftingMix.value) * 100)}%`);
  setOutput("noise-reduction-strength-value", `${Math.round(Number(c.noiseReductionStrength.value) * 100)}%`);
  setOutput("voice-isolation-strength-value", `${Math.round(Number(c.voiceIsolationStrength.value) * 100)}%`);
  setOutput("voice-isolation-low-hz-value", `${Math.round(Number(c.voiceIsolationLowHz.value))} Hz`);
  setOutput("voice-isolation-high-hz-value", `${Math.round(Number(c.voiceIsolationHighHz.value))} Hz`);
  setOutput("source-separation-strength-value", `${Math.round(Number(c.sourceSeparationStrength.value) * 100)}%`);
  setOutput("source-separation-low-hz-value", `${Math.round(Number(c.sourceSeparationLowHz.value))} Hz`);
  setOutput("source-separation-high-hz-value", `${Math.round(Number(c.sourceSeparationHighHz.value))} Hz`);
  setOutput("de-reverb-amount-value", `${Math.round(Number(c.deReverbAmount.value) * 100)}%`);
  setOutput("de-reverb-tail-ms-value", formatMilliseconds(c.deReverbTailMs.value));
  setOutput("de-echo-amount-value", `${Math.round(Number(c.deEchoAmount.value) * 100)}%`);
  setOutput("de-echo-min-delay-ms-value", formatMilliseconds(c.deEchoMinDelayMs.value));
  setOutput("de-echo-max-delay-ms-value", formatMilliseconds(c.deEchoMaxDelayMs.value));
  setOutput("spectral-repair-strength-value", `${Math.round(Number(c.spectralRepairStrength.value) * 100)}%`);
  setOutput("ai-enhancer-amount-value", `${Math.round(Number(c.aiEnhancerAmount.value) * 100)}%`);
  setOutput("speech-enhancement-amount-value", `${Math.round(Number(c.speechEnhancementAmount.value) * 100)}%`);
  setOutput("glitch-effect-slice-ms-value", formatMilliseconds(c.glitchEffectSliceMs.value));
  setOutput("glitch-effect-repeat-probability-value", `${Math.round(Number(c.glitchEffectRepeatProbability.value) * 100)}%`);
  setOutput("glitch-effect-dropout-probability-value", `${Math.round(Number(c.glitchEffectDropoutProbability.value) * 100)}%`);
  setOutput("glitch-effect-reverse-probability-value", `${Math.round(Number(c.glitchEffectReverseProbability.value) * 100)}%`);
  setOutput("glitch-effect-mix-value", `${Math.round(Number(c.glitchEffectMix.value) * 100)}%`);
  setOutput("stutter-slice-ms-value", formatMilliseconds(c.stutterSliceMs.value));
  setOutput("stutter-repeats-value", `${Math.round(Number(c.stutterRepeats.value))}`);
  setOutput("stutter-interval-ms-value", formatMilliseconds(c.stutterIntervalMs.value));
  setOutput("stutter-mix-value", `${Math.round(Number(c.stutterMix.value) * 100)}%`);
  setOutput("tape-stop-stop-time-ms-value", formatMilliseconds(c.tapeStopStopTimeMs.value));
  setOutput("tape-stop-curve-value", Number(c.tapeStopCurve.value).toFixed(2));
  setOutput("tape-stop-mix-value", `${Math.round(Number(c.tapeStopMix.value) * 100)}%`);
  setOutput("reverse-reverb-decay-seconds-value", `${Number(c.reverseReverbDecaySeconds.value).toFixed(2)} s`);
  setOutput("reverse-reverb-mix-value", `${Math.round(Number(c.reverseReverbMix.value) * 100)}%`);
  setOutput("granular-synthesis-grain-ms-value", formatMilliseconds(c.granularSynthesisGrainMs.value));
  setOutput("granular-synthesis-overlap-value", `${Math.round(Number(c.granularSynthesisOverlap.value) * 100)}%`);
  setOutput("granular-synthesis-jitter-ms-value", formatMilliseconds(c.granularSynthesisJitterMs.value));
  setOutput("granular-synthesis-mix-value", `${Math.round(Number(c.granularSynthesisMix.value) * 100)}%`);
  setOutput("time-slicing-slice-ms-value", formatMilliseconds(c.timeSlicingSliceMs.value));
  setOutput("time-slicing-mix-value", `${Math.round(Number(c.timeSlicingMix.value) * 100)}%`);
  setOutput("random-pitch-mod-depth-semitones-value", `${Number(c.randomPitchModDepthSemitones.value).toFixed(1)} st`);
  setOutput("random-pitch-mod-segment-ms-value", formatMilliseconds(c.randomPitchModSegmentMs.value));
  setOutput("random-pitch-mod-mix-value", `${Math.round(Number(c.randomPitchModMix.value) * 100)}%`);
  setOutput("vinyl-effect-noise-value", `${Math.round(Number(c.vinylEffectNoise.value) * 100)}%`);
  setOutput("vinyl-effect-wow-value", `${Math.round(Number(c.vinylEffectWow.value) * 100)}%`);
  setOutput("vinyl-effect-crackle-value", `${Math.round(Number(c.vinylEffectCrackle.value) * 100)}%`);
  setOutput("vinyl-effect-mix-value", `${Math.round(Number(c.vinylEffectMix.value) * 100)}%`);
  setOutput("radio-effect-noise-level-value", `${Math.round(Number(c.radioEffectNoiseLevel.value) * 100)}%`);
  setOutput("radio-effect-mix-value", `${Math.round(Number(c.radioEffectMix.value) * 100)}%`);
  setOutput("telephone-effect-mix-value", `${Math.round(Number(c.telephoneEffectMix.value) * 100)}%`);
  setOutput("retro-8bit-bit-depth-value", `${Math.round(Number(c.retro8bitBitDepth.value))}-bit`);
  setOutput("retro-8bit-sample-rate-reduction-value", `${Math.round(Number(c.retro8bitSampleRateReduction.value))}x`);
  setOutput("retro-8bit-mix-value", `${Math.round(Number(c.retro8bitMix.value) * 100)}%`);
  setOutput("slow-motion-extreme-rate-value", `${Number(c.slowMotionExtremeRate.value).toFixed(2)}x`);
  setOutput("slow-motion-extreme-tone-hz-value", `${Math.round(Number(c.slowMotionExtremeToneHz.value))} Hz`);
  setOutput("slow-motion-extreme-mix-value", `${Math.round(Number(c.slowMotionExtremeMix.value) * 100)}%`);
  setOutput("robot-voice-carrier-hz-value", `${Math.round(Number(c.robotVoiceCarrierHz.value))} Hz`);
  setOutput("robot-voice-mix-value", `${Math.round(Number(c.robotVoiceMix.value) * 100)}%`);
  setOutput("alien-voice-shift-semitones-value", `${Number(c.alienVoiceShiftSemitones.value).toFixed(1)} st`);
  setOutput("alien-voice-formant-shift-value", `${Number(c.alienVoiceFormantShift.value).toFixed(2)}x`);
  setOutput("alien-voice-mix-value", `${Math.round(Number(c.alienVoiceMix.value) * 100)}%`);
  setOutput("fft-filter-low-hz-value", `${Math.round(Number(c.fftFilterLowHz.value))} Hz`);
  setOutput("fft-filter-high-hz-value", `${Math.round(Number(c.fftFilterHighHz.value))} Hz`);
  setOutput("fft-filter-mix-value", `${Math.round(Number(c.fftFilterMix.value) * 100)}%`);
  setOutput("spectral-gating-threshold-db-value", `${Math.round(Number(c.spectralGatingThresholdDb.value))} dB`);
  setOutput("spectral-gating-floor-value", `${Math.round(Number(c.spectralGatingFloor.value) * 100)}%`);
  setOutput("spectral-blur-amount-value", `${Math.round(Number(c.spectralBlurAmount.value) * 100)}%`);
  setOutput("spectral-freeze-start-ms-value", formatMilliseconds(c.spectralFreezeStartMs.value));
  setOutput("spectral-freeze-mix-value", `${Math.round(Number(c.spectralFreezeMix.value) * 100)}%`);
  setOutput("spectral-morphing-amount-value", `${Math.round(Number(c.spectralMorphingAmount.value) * 100)}%`);
  setOutput("phase-vocoder-rate-value", `${Number(c.phaseVocoderRate.value).toFixed(2)}x`);
  setOutput("harmonic-percussive-separation-mix-value", `${Math.round(Number(c.harmonicPercussiveSeparationMix.value) * 100)}%`);
  setOutput("spectral-delay-max-delay-ms-value", formatMilliseconds(c.spectralDelayMaxDelayMs.value));
  setOutput("spectral-delay-feedback-value", Number(c.spectralDelayFeedback.value).toFixed(2));
  setOutput("spectral-delay-mix-value", `${Math.round(Number(c.spectralDelayMix.value) * 100)}%`);
  setOutput("stereo-widening-amount-value", `${Number(c.stereoWideningAmount.value).toFixed(2)}x`);
  setOutput("mid-side-processing-mid-gain-db-value", `${Number(c.midSideProcessingMidGainDb.value).toFixed(1)} dB`);
  setOutput("mid-side-processing-side-gain-db-value", `${Number(c.midSideProcessingSideGainDb.value).toFixed(1)} dB`);
  setOutput("stereo-imager-low-width-value", `${Number(c.stereoImagerLowWidth.value).toFixed(2)}x`);
  setOutput("stereo-imager-high-width-value", `${Number(c.stereoImagerHighWidth.value).toFixed(2)}x`);
  setOutput("stereo-imager-crossover-hz-value", `${Math.round(Number(c.stereoImagerCrossoverHz.value))} Hz`);
  setOutput("binaural-effect-azimuth-deg-value", `${Math.round(Number(c.binauralEffectAzimuthDeg.value))} deg`);
  setOutput("binaural-effect-distance-value", `${Number(c.binauralEffectDistance.value).toFixed(2)}x`);
  setOutput("binaural-effect-room-mix-value", `${Math.round(Number(c.binauralEffectRoomMix.value) * 100)}%`);
  setOutput("spatial-positioning-azimuth-deg-value", `${Math.round(Number(c.spatialPositioningAzimuthDeg.value))} deg`);
  setOutput("spatial-positioning-elevation-deg-value", `${Math.round(Number(c.spatialPositioningElevationDeg.value))} deg`);
  setOutput("spatial-positioning-distance-value", `${Number(c.spatialPositioningDistance.value).toFixed(2)}x`);
  setOutput("hrtf-simulation-azimuth-deg-value", `${Math.round(Number(c.hrtfSimulationAzimuthDeg.value))} deg`);
  setOutput("hrtf-simulation-elevation-deg-value", `${Math.round(Number(c.hrtfSimulationElevationDeg.value))} deg`);
  setOutput("hrtf-simulation-distance-value", `${Number(c.hrtfSimulationDistance.value).toFixed(2)}x`);
}

function buildParametricBandConfig(index) {
  const c = elements.controls;
  return {
    enabled: c[`parametric${index}Enabled`].checked,
    kind: c[`parametric${index}Kind`].value,
    frequencyHz: Number(c[`parametric${index}Freq`].value),
    gainDb: Number(c[`parametric${index}Gain`].value),
    q: Number(c[`parametric${index}Q`].value),
    slope: 1.0,
    stages: 1,
  };
}

function buildBasicConfig() {
  const c = elements.controls;
  return {
    normalize: {
      enabled: c.normalizeEnabled.checked,
      headroomDb: Number(c.normalizeHeadroom.value),
      maxGain: Number(c.normalizeMaxGain.value),
    },
    fadeIn: {
      enabled: c.fadeInEnabled.checked,
      durationMs: Number(c.fadeInDuration.value),
    },
    fadeOut: {
      enabled: c.fadeOutEnabled.checked,
      durationMs: Number(c.fadeOutDuration.value),
    },
    trim: {
      enabled: c.trimEnabled.checked,
      startMs: Number(c.trimStart.value),
      endMs: Number(c.trimEnd.value),
      featherMs: Number(c.trimFeather.value),
    },
    cut: {
      enabled: c.cutEnabled.checked,
      startMs: Number(c.cutStart.value),
      endMs: Number(c.cutEnd.value),
      featherMs: Number(c.cutFeather.value),
    },
    silenceRemoval: {
      enabled: c.silenceRemovalEnabled.checked,
      thresholdDb: Number(c.silenceRemovalThreshold.value),
      minSilenceMs: Number(c.silenceRemovalMin.value),
      paddingMs: Number(c.silenceRemovalPadding.value),
    },
    reverse: {
      enabled: c.reverseEnabled.checked,
      windowMs: Number(c.reverseWindow.value),
      mix: Number(c.reverseMix.value),
    },
  };
}

function buildColorTimeConfig() {
  const c = elements.controls;
  return {
    distortion: {
      enabled: c.distortionEnabled.checked,
      drive: Number(c.distortionDrive.value),
    },
    overdrive: {
      enabled: c.overdriveEnabled.checked,
      drive: Number(c.overdriveDrive.value),
      tone: Number(c.overdriveTone.value),
      mix: Number(c.overdriveMix.value),
    },
    fuzz: {
      enabled: c.fuzzEnabled.checked,
      drive: Number(c.fuzzDrive.value),
      bias: Number(c.fuzzBias.value),
      mix: Number(c.fuzzMix.value),
    },
    bitcrusher: {
      enabled: c.bitcrusherEnabled.checked,
      bitDepth: Number(c.bitcrusherBitDepth.value),
      sampleRateReduction: Number(c.bitcrusherSampleRateReduction.value),
      mix: Number(c.bitcrusherMix.value),
    },
    waveshaper: {
      enabled: c.waveshaperEnabled.checked,
      amount: Number(c.waveshaperAmount.value),
      symmetry: Number(c.waveshaperSymmetry.value),
      mix: Number(c.waveshaperMix.value),
    },
    tubeSaturation: {
      enabled: c.tubeSaturationEnabled.checked,
      drive: Number(c.tubeSaturationDrive.value),
      bias: Number(c.tubeSaturationBias.value),
      mix: Number(c.tubeSaturationMix.value),
    },
    tapeSaturation: {
      enabled: c.tapeSaturationEnabled.checked,
      drive: Number(c.tapeSaturationDrive.value),
      softness: Number(c.tapeSaturationSoftness.value),
      mix: Number(c.tapeSaturationMix.value),
    },
    softClipping: {
      enabled: c.softClippingEnabled.checked,
      threshold: Number(c.softClippingThreshold.value),
    },
    hardClipping: {
      enabled: c.hardClippingEnabled.checked,
      threshold: Number(c.hardClippingThreshold.value),
    },
    pitchShift: {
      enabled: c.pitchShiftEnabled.checked,
      semitones: Number(c.pitchShiftSemitones.value),
      mix: Number(c.pitchShiftMix.value),
    },
    autoTune: {
      enabled: c.autoTuneEnabled.checked,
      strength: Number(c.autoTuneStrength.value),
      key: c.autoTuneKey.value,
      scale: c.autoTuneScale.value,
      minHz: Number(c.autoTuneMinHz.value),
      maxHz: Number(c.autoTuneMaxHz.value),
    },
    harmonizer: {
      enabled: c.harmonizerEnabled.checked,
      intervalA: Number(c.harmonizerIntervalA.value),
      intervalB: Number(c.harmonizerIntervalB.value),
      intervalC: Number(c.harmonizerIntervalC.value),
      mix: Number(c.harmonizerMix.value),
    },
    octaver: {
      enabled: c.octaverEnabled.checked,
      octavesDown: Number(c.octaverDown.value),
      octavesUp: Number(c.octaverUp.value),
      downMix: Number(c.octaverDownMix.value),
      upMix: Number(c.octaverUpMix.value),
    },
    formantShifting: {
      enabled: c.formantShiftingEnabled.checked,
      shift: Number(c.formantShiftingShift.value),
      mix: Number(c.formantShiftingMix.value),
      q: 3.6,
    },
  };
}

function buildModernCreativeConfig() {
  const c = elements.controls;
  return {
    noiseReduction: {
      enabled: c.noiseReductionEnabled.checked,
      strength: Number(c.noiseReductionStrength.value),
    },
    voiceIsolation: {
      enabled: c.voiceIsolationEnabled.checked,
      strength: Number(c.voiceIsolationStrength.value),
      lowHz: Number(c.voiceIsolationLowHz.value),
      highHz: Number(c.voiceIsolationHighHz.value),
    },
    sourceSeparation: {
      enabled: c.sourceSeparationEnabled.checked,
      target: c.sourceSeparationTarget.value,
      strength: Number(c.sourceSeparationStrength.value),
      lowHz: Number(c.sourceSeparationLowHz.value),
      highHz: Number(c.sourceSeparationHighHz.value),
    },
    deReverb: {
      enabled: c.deReverbEnabled.checked,
      amount: Number(c.deReverbAmount.value),
      tailMs: Number(c.deReverbTailMs.value),
    },
    deEcho: {
      enabled: c.deEchoEnabled.checked,
      amount: Number(c.deEchoAmount.value),
      minDelayMs: Number(c.deEchoMinDelayMs.value),
      maxDelayMs: Number(c.deEchoMaxDelayMs.value),
    },
    spectralRepair: {
      enabled: c.spectralRepairEnabled.checked,
      strength: Number(c.spectralRepairStrength.value),
    },
    aiEnhancer: {
      enabled: c.aiEnhancerEnabled.checked,
      amount: Number(c.aiEnhancerAmount.value),
    },
    speechEnhancement: {
      enabled: c.speechEnhancementEnabled.checked,
      amount: Number(c.speechEnhancementAmount.value),
    },
    glitchEffect: {
      enabled: c.glitchEffectEnabled.checked,
      sliceMs: Number(c.glitchEffectSliceMs.value),
      repeatProbability: Number(c.glitchEffectRepeatProbability.value),
      dropoutProbability: Number(c.glitchEffectDropoutProbability.value),
      reverseProbability: Number(c.glitchEffectReverseProbability.value),
      mix: Number(c.glitchEffectMix.value),
    },
    stutter: {
      enabled: c.stutterEnabled.checked,
      sliceMs: Number(c.stutterSliceMs.value),
      repeats: Number(c.stutterRepeats.value),
      intervalMs: Number(c.stutterIntervalMs.value),
      mix: Number(c.stutterMix.value),
    },
    tapeStop: {
      enabled: c.tapeStopEnabled.checked,
      stopTimeMs: Number(c.tapeStopStopTimeMs.value),
      curve: Number(c.tapeStopCurve.value),
      mix: Number(c.tapeStopMix.value),
    },
    reverseReverb: {
      enabled: c.reverseReverbEnabled.checked,
      decaySeconds: Number(c.reverseReverbDecaySeconds.value),
      mix: Number(c.reverseReverbMix.value),
    },
    granularSynthesis: {
      enabled: c.granularSynthesisEnabled.checked,
      grainMs: Number(c.granularSynthesisGrainMs.value),
      overlap: Number(c.granularSynthesisOverlap.value),
      jitterMs: Number(c.granularSynthesisJitterMs.value),
      mix: Number(c.granularSynthesisMix.value),
    },
    timeSlicing: {
      enabled: c.timeSlicingEnabled.checked,
      sliceMs: Number(c.timeSlicingSliceMs.value),
      mix: Number(c.timeSlicingMix.value),
    },
    randomPitchMod: {
      enabled: c.randomPitchModEnabled.checked,
      depthSemitones: Number(c.randomPitchModDepthSemitones.value),
      segmentMs: Number(c.randomPitchModSegmentMs.value),
      mix: Number(c.randomPitchModMix.value),
    },
    vinylEffect: {
      enabled: c.vinylEffectEnabled.checked,
      noise: Number(c.vinylEffectNoise.value),
      wow: Number(c.vinylEffectWow.value),
      crackle: Number(c.vinylEffectCrackle.value),
      mix: Number(c.vinylEffectMix.value),
    },
    radioEffect: {
      enabled: c.radioEffectEnabled.checked,
      noiseLevel: Number(c.radioEffectNoiseLevel.value),
      mix: Number(c.radioEffectMix.value),
    },
    telephoneEffect: {
      enabled: c.telephoneEffectEnabled.checked,
      mix: Number(c.telephoneEffectMix.value),
    },
    retro8bit: {
      enabled: c.retro8bitEnabled.checked,
      bitDepth: Number(c.retro8bitBitDepth.value),
      sampleRateReduction: Number(c.retro8bitSampleRateReduction.value),
      mix: Number(c.retro8bitMix.value),
    },
    slowMotionExtreme: {
      enabled: c.slowMotionExtremeEnabled.checked,
      rate: Number(c.slowMotionExtremeRate.value),
      toneHz: Number(c.slowMotionExtremeToneHz.value),
      mix: Number(c.slowMotionExtremeMix.value),
    },
    robotVoice: {
      enabled: c.robotVoiceEnabled.checked,
      carrierHz: Number(c.robotVoiceCarrierHz.value),
      mix: Number(c.robotVoiceMix.value),
    },
    alienVoice: {
      enabled: c.alienVoiceEnabled.checked,
      shiftSemitones: Number(c.alienVoiceShiftSemitones.value),
      formantShift: Number(c.alienVoiceFormantShift.value),
      mix: Number(c.alienVoiceMix.value),
    },
  };
}

function buildSpectralSpatialConfig() {
  const c = elements.controls;
  return {
    fftFilter: {
      enabled: c.fftFilterEnabled.checked,
      lowHz: Number(c.fftFilterLowHz.value),
      highHz: Number(c.fftFilterHighHz.value),
      mix: Number(c.fftFilterMix.value),
    },
    spectralGating: {
      enabled: c.spectralGatingEnabled.checked,
      thresholdDb: Number(c.spectralGatingThresholdDb.value),
      floor: Number(c.spectralGatingFloor.value),
    },
    spectralBlur: {
      enabled: c.spectralBlurEnabled.checked,
      amount: Number(c.spectralBlurAmount.value),
    },
    spectralFreeze: {
      enabled: c.spectralFreezeEnabled.checked,
      startMs: Number(c.spectralFreezeStartMs.value),
      mix: Number(c.spectralFreezeMix.value),
    },
    spectralMorphing: {
      enabled: c.spectralMorphingEnabled.checked,
      amount: Number(c.spectralMorphingAmount.value),
    },
    phaseVocoder: {
      enabled: c.phaseVocoderEnabled.checked,
      rate: Number(c.phaseVocoderRate.value),
    },
    harmonicPercussiveSeparation: {
      enabled: c.harmonicPercussiveSeparationEnabled.checked,
      target: c.harmonicPercussiveSeparationTarget.value,
      mix: Number(c.harmonicPercussiveSeparationMix.value),
    },
    spectralDelay: {
      enabled: c.spectralDelayEnabled.checked,
      maxDelayMs: Number(c.spectralDelayMaxDelayMs.value),
      feedback: Number(c.spectralDelayFeedback.value),
      mix: Number(c.spectralDelayMix.value),
    },
    stereoWidening: {
      enabled: c.stereoWideningEnabled.checked,
      amount: Number(c.stereoWideningAmount.value),
    },
    midSideProcessing: {
      enabled: c.midSideProcessingEnabled.checked,
      midGainDb: Number(c.midSideProcessingMidGainDb.value),
      sideGainDb: Number(c.midSideProcessingSideGainDb.value),
    },
    stereoImager: {
      enabled: c.stereoImagerEnabled.checked,
      lowWidth: Number(c.stereoImagerLowWidth.value),
      highWidth: Number(c.stereoImagerHighWidth.value),
      crossoverHz: Number(c.stereoImagerCrossoverHz.value),
    },
    binauralEffect: {
      enabled: c.binauralEffectEnabled.checked,
      azimuthDeg: Number(c.binauralEffectAzimuthDeg.value),
      distance: Number(c.binauralEffectDistance.value),
      roomMix: Number(c.binauralEffectRoomMix.value),
    },
    spatialPositioning: {
      enabled: c.spatialPositioningEnabled.checked,
      azimuthDeg: Number(c.spatialPositioningAzimuthDeg.value),
      elevationDeg: Number(c.spatialPositioningElevationDeg.value),
      distance: Number(c.spatialPositioningDistance.value),
    },
    hrtfSimulation: {
      enabled: c.hrtfSimulationEnabled.checked,
      azimuthDeg: Number(c.hrtfSimulationAzimuthDeg.value),
      elevationDeg: Number(c.hrtfSimulationElevationDeg.value),
      distance: Number(c.hrtfSimulationDistance.value),
    },
  };
}

function buildModulationConfig() {
  const c = elements.controls;
  return {
    chorus: {
      enabled: c.chorusEnabled.checked,
      rateHz: Number(c.chorusRate.value),
      depthMs: Number(c.chorusDepth.value),
      delayMs: Number(c.chorusDelay.value),
      mix: Number(c.chorusMix.value),
      feedback: Number(c.chorusFeedback.value),
    },
    flanger: {
      enabled: c.flangerEnabled.checked,
      rateHz: Number(c.flangerRate.value),
      depthMs: Number(c.flangerDepth.value),
      delayMs: Number(c.flangerDelay.value),
      mix: Number(c.flangerMix.value),
      feedback: Number(c.flangerFeedback.value),
    },
    phaser: {
      enabled: c.phaserEnabled.checked,
      rateHz: Number(c.phaserRate.value),
      depth: Number(c.phaserDepth.value),
      centerHz: Number(c.phaserCenter.value),
      feedback: Number(c.phaserFeedback.value),
      mix: Number(c.phaserMix.value),
      stages: Number(c.phaserStages.value),
    },
    tremolo: {
      enabled: c.tremoloEnabled.checked,
      rateHz: Number(c.tremoloRate.value),
      depth: Number(c.tremoloDepth.value),
    },
    vibrato: {
      enabled: c.vibratoEnabled.checked,
      rateHz: Number(c.vibratoRate.value),
      depthMs: Number(c.vibratoDepth.value),
      delayMs: Number(c.vibratoDelay.value),
    },
    autoPan: {
      enabled: c.autoPanEnabled.checked,
      rateHz: Number(c.autoPanRate.value),
      depth: Number(c.autoPanDepth.value),
    },
    rotarySpeaker: {
      enabled: c.rotaryEnabled.checked,
      rateHz: Number(c.rotaryRate.value),
      depth: Number(c.rotaryDepth.value),
      mix: Number(c.rotaryMix.value),
      crossoverHz: Number(c.rotaryCrossover.value),
    },
    ringModulation: {
      enabled: c.ringModEnabled.checked,
      frequencyHz: Number(c.ringModFrequency.value),
      mix: Number(c.ringModMix.value),
    },
    frequencyShifter: {
      enabled: c.frequencyShifterEnabled.checked,
      shiftHz: Number(c.frequencyShifterShift.value),
      mix: Number(c.frequencyShifterMix.value),
    },
  };
}

function buildSpaceConfig() {
  const c = elements.controls;
  return {
    delay: {
      enabled: c.delayEnabled.checked,
      delayMs: Number(c.delayTime.value),
      feedback: Number(c.delayFeedback.value),
      mix: Number(c.delayMix.value),
    },
    echo: {
      enabled: c.echoEnabled.checked,
      delayMs: Number(c.echoTime.value),
      feedback: Number(c.echoFeedback.value),
      mix: Number(c.echoMix.value),
    },
    pingPongDelay: {
      enabled: c.pingPongEnabled.checked,
      delayMs: Number(c.pingPongTime.value),
      feedback: Number(c.pingPongFeedback.value),
      mix: Number(c.pingPongMix.value),
    },
    multiTapDelay: {
      enabled: c.multiTapEnabled.checked,
      delayMs: Number(c.multiTapDelay.value),
      taps: Number(c.multiTapTaps.value),
      spacingMs: Number(c.multiTapSpacing.value),
      decay: Number(c.multiTapDecay.value),
      mix: Number(c.multiTapMix.value),
    },
    slapbackDelay: {
      enabled: c.slapbackEnabled.checked,
      delayMs: Number(c.slapbackTime.value),
      feedback: 0.0,
      mix: Number(c.slapbackMix.value),
    },
    earlyReflections: {
      enabled: c.earlyReflectionsEnabled.checked,
      preDelayMs: Number(c.earlyReflectionsPreDelay.value),
      spreadMs: Number(c.earlyReflectionsSpread.value),
      taps: Number(c.earlyReflectionsTaps.value),
      decay: Number(c.earlyReflectionsDecay.value),
      mix: Number(c.earlyReflectionsMix.value),
    },
    roomReverb: {
      enabled: c.roomReverbEnabled.checked,
      decaySeconds: Number(c.roomReverbDecay.value),
      mix: Number(c.roomReverbMix.value),
      toneHz: Number(c.roomReverbTone.value),
    },
    hallReverb: {
      enabled: c.hallReverbEnabled.checked,
      decaySeconds: Number(c.hallReverbDecay.value),
      mix: Number(c.hallReverbMix.value),
      toneHz: Number(c.hallReverbTone.value),
    },
    plateReverb: {
      enabled: c.plateReverbEnabled.checked,
      decaySeconds: Number(c.plateReverbDecay.value),
      mix: Number(c.plateReverbMix.value),
      toneHz: Number(c.plateReverbTone.value),
    },
    convolutionReverb: {
      enabled: c.convolutionReverbEnabled.checked,
      mix: Number(c.convolutionReverbMix.value),
      normalizeIr: c.convolutionReverbNormalize.checked,
    },
  };
}

function buildDynamicsConfig() {
  const c = elements.controls;
  const multibandLowCut = Number(c.multibandLowCut.value);
  const multibandHighCut = Math.max(multibandLowCut + 20, Number(c.multibandHighCut.value));
  return {
    highpass: {
      enabled: c.highpassEnabled.checked,
      frequencyHz: Number(c.highpassFreq.value),
      q: 0.70710678,
      gainDb: 0,
      slope: 1,
      stages: 2,
    },
    lowpass: {
      enabled: c.lowpassEnabled.checked,
      frequencyHz: Number(c.lowpassFreq.value),
      q: 0.70710678,
      gainDb: 0,
      slope: 1,
      stages: 2,
    },
    bandpass: {
      enabled: c.bandpassEnabled.checked,
      frequencyHz: Number(c.bandpassFreq.value),
      q: Number(c.bandpassQ.value),
      gainDb: 0,
      slope: 1,
      stages: 1,
    },
    notch: {
      enabled: c.notchEnabled.checked,
      frequencyHz: Number(c.notchFreq.value),
      q: Number(c.notchQ.value),
      gainDb: 0,
      slope: 1,
      stages: 1,
    },
    peakEq: {
      enabled: c.peakEqEnabled.checked,
      frequencyHz: Number(c.peakEqFreq.value),
      q: Number(c.peakEqQ.value),
      gainDb: Number(c.peakEqGain.value),
      slope: 1,
      stages: 1,
    },
    lowShelf: {
      enabled: c.lowShelfEnabled.checked,
      frequencyHz: Number(c.lowShelfFreq.value),
      q: 0.70710678,
      gainDb: Number(c.lowShelfGain.value),
      slope: Number(c.lowShelfSlope.value),
      stages: 1,
    },
    highShelf: {
      enabled: c.highShelfEnabled.checked,
      frequencyHz: Number(c.highShelfFreq.value),
      q: 0.70710678,
      gainDb: Number(c.highShelfGain.value),
      slope: Number(c.highShelfSlope.value),
      stages: 1,
    },
    resonantFilter: {
      enabled: c.resonantEnabled.checked,
      mode: c.resonantMode.value,
      frequencyHz: Number(c.resonantFreq.value),
      resonance: Number(c.resonantResonance.value),
      stages: 1,
    },
    parametricEq: PARAMETRIC_BANDS.map((index) => buildParametricBandConfig(index)),
    graphicEq: {
      enabled: c.graphicEqEnabled.checked,
      q: Number(c.graphicEqQ.value),
      bandsDb: GRAPHIC_EQ_BANDS.map((band) => Number(c[`graphicEq${band}`].value)),
    },
    dynamicEq: {
      enabled: c.dynamicEqEnabled.checked,
      frequencyHz: Number(c.dynamicEqFrequency.value),
      thresholdDb: Number(c.dynamicEqThreshold.value),
      cutDb: Number(c.dynamicEqCut.value),
      q: Number(c.dynamicEqQ.value),
      attackMs: 10,
      releaseMs: 120,
    },
    formantFilter: {
      enabled: c.formantEnabled.checked,
      morph: Number(c.formantMorph.value),
      intensity: Number(c.formantIntensity.value),
      q: Number(c.formantQ.value),
    },
    compressor: {
      enabled: c.compressorEnabled.checked,
      thresholdDb: Number(c.compressorThreshold.value),
      ratio: Number(c.compressorRatio.value),
      attackMs: 10,
      releaseMs: 80,
      makeupDb: Number(c.compressorMakeup.value),
    },
    downwardCompression: {
      enabled: c.downwardEnabled.checked,
      thresholdDb: Number(c.downwardThreshold.value),
      ratio: Number(c.downwardRatio.value),
      attackMs: 10,
      releaseMs: 80,
      makeupDb: 0,
    },
    upwardCompression: {
      enabled: c.upwardEnabled.checked,
      thresholdDb: Number(c.upwardThreshold.value),
      ratio: Number(c.upwardRatio.value),
      attackMs: 12,
      releaseMs: 120,
      maxGainDb: Number(c.upwardMaxGain.value),
    },
    limiter: {
      enabled: c.limiterEnabled.checked,
      ceilingDb: Number(c.limiterCeiling.value),
      attackMs: 1,
      releaseMs: 60,
    },
    expander: {
      enabled: c.expanderEnabled.checked,
      thresholdDb: Number(c.expanderThreshold.value),
      ratio: Number(c.expanderRatio.value),
      attackMs: 8,
      releaseMs: 80,
      makeupDb: 0,
    },
    noiseGate: {
      enabled: c.noiseGateEnabled.checked,
      thresholdDb: Number(c.noiseGateThreshold.value),
      attackMs: 3,
      releaseMs: 60,
      floorDb: Number(c.noiseGateFloor.value),
    },
    deesser: {
      enabled: c.deesserEnabled.checked,
      frequencyHz: Number(c.deesserFrequency.value),
      thresholdDb: Number(c.deesserThreshold.value),
      ratio: 4.0,
      attackMs: 2,
      releaseMs: 60,
      amount: Number(c.deesserAmount.value),
    },
    transientShaper: {
      enabled: c.transientEnabled.checked,
      attack: Number(c.transientAttack.value),
      sustain: Number(c.transientSustain.value),
      attackMs: 18,
      releaseMs: 120,
    },
    multibandCompressor: {
      enabled: c.multibandEnabled.checked,
      lowCutHz: multibandLowCut,
      highCutHz: multibandHighCut,
      lowThresholdDb: Number(c.multibandLowThreshold.value),
      midThresholdDb: Number(c.multibandMidThreshold.value),
      highThresholdDb: Number(c.multibandHighThreshold.value),
      lowRatio: Number(c.multibandLowRatio.value),
      midRatio: Number(c.multibandMidRatio.value),
      highRatio: Number(c.multibandHighRatio.value),
      attackMs: Number(c.multibandAttack.value),
      releaseMs: Number(c.multibandRelease.value),
      lowMakeupDb: Number(c.multibandLowMakeup.value),
      midMakeupDb: Number(c.multibandMidMakeup.value),
      highMakeupDb: Number(c.multibandHighMakeup.value),
    },
  };
}

async function loadDynamicsWasmBytes() {
  if (state.dynamicsWasmBytes instanceof ArrayBuffer) {
    return state.dynamicsWasmBytes;
  }

  const response = await fetch("/static/api/voxis-realtime-dynamics.wasm");
  if (!response.ok) {
    throw new Error(`Failed to load Voxis dynamics WASM: ${response.status}`);
  }

  state.dynamicsWasmBytes = await response.arrayBuffer();
  return state.dynamicsWasmBytes;
}

function createGraph(audioContext, dynamicsWasmBytes) {
  const input = audioContext.createGain();
  const sourceBus = audioContext.createGain();
  const primarySourceGain = audioContext.createGain();
  const secondarySourceGain = audioContext.createGain();
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
    processorOptions: {
      wasmBytes: dynamicsWasmBytes,
    },
  });
  const modulationWorklet = new AudioWorkletNode(audioContext, "voxis-modulation-processor", {
    numberOfInputs: 1,
    numberOfOutputs: 1,
    outputChannelCount: [2],
  });
  const spaceRack = createSpaceRack(audioContext);
  const panner = audioContext.createStereoPanner();
  const master = audioContext.createGain();
  const analyser = audioContext.createAnalyser();

  analyser.fftSize = 2048;
  analyser.smoothingTimeConstant = 0.8;
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
  master.connect(analyser);
  analyser.connect(audioContext.destination);

  dynamicsWorklet.port.onmessage = (event) => {
    if (event.data?.type === "ready") {
      setEngineState("Engine ready");
    }
    if (event.data?.type === "error") {
      console.error(event.data.message);
      setEngineState("WASM chain failed");
    }
  };

  return {
    input,
    sourceBus,
    primarySourceGain,
    secondarySourceGain,
    basicWorklet,
    colorTimeWorklet,
    modernCreativeWorklet,
    spectralSpatialWorklet,
    dynamicsWorklet,
    modulationWorklet,
    spaceRack,
    panner,
    master,
    analyser,
  };
}

function setTransportState(transport) {
  if (!state.graph) {
    return;
  }
  state.graph.basicWorklet.port.postMessage({
    type: "transport",
    transport,
  });
}

function updateTransportFromPrimary() {
  if (state.sourceMode !== "file") {
    return;
  }
  setTransportState({
    sourceKind: "file",
    playing: !elements.sourcePlayer.paused && !elements.sourcePlayer.ended,
    startContextTimeSec: state.audioContext ? state.audioContext.currentTime : 0,
    positionSec: elements.sourcePlayer.currentTime || 0,
    durationSec: Number.isFinite(elements.sourcePlayer.duration) ? elements.sourcePlayer.duration : 0,
    playbackRate: elements.sourcePlayer.playbackRate || 1,
  });
}

function setMicTransportState(active) {
  if (!state.audioContext) {
    return;
  }
  setTransportState({
    sourceKind: active ? "mic" : "none",
    playing: active,
    startContextTimeSec: state.audioContext.currentTime,
    positionSec: 0,
    durationSec: 0,
    playbackRate: 1,
  });
}

function resetCrossfadePartner(resetPosition = true) {
  state.secondaryStarted = false;
  if (state.graph) {
    state.graph.primarySourceGain.gain.value = 1.0;
    state.graph.secondarySourceGain.gain.value = 0.0;
  }
  if (elements.crossfadePlayer) {
    elements.crossfadePlayer.pause();
    if (resetPosition) {
      try {
        elements.crossfadePlayer.currentTime = 0;
      } catch (error) {
        console.debug(error);
      }
    }
  }
}

function syncCrossfadeState() {
  if (!state.graph) {
    return;
  }

  const enabled =
    elements.controls.crossfadeEnabled.checked &&
    Boolean(elements.crossfadePlayer?.src) &&
    state.sourceMode === "file" &&
    Number.isFinite(elements.sourcePlayer.duration) &&
    elements.sourcePlayer.duration > 0;

  if (!enabled) {
    resetCrossfadePartner(false);
    return;
  }

  const crossfadeDurationSec = Math.max(Number(elements.controls.crossfadeDuration.value) / 1000, 0.01);
  const crossfadeStartSec = Math.max(elements.sourcePlayer.duration - crossfadeDurationSec, 0);
  const currentSec = elements.sourcePlayer.currentTime || 0;

  if (elements.sourcePlayer.paused || currentSec < crossfadeStartSec) {
    if (currentSec + 0.05 < crossfadeStartSec) {
      resetCrossfadePartner(true);
    }
    return;
  }

  const progress = Math.min(1, Math.max(0, (currentSec - crossfadeStartSec) / crossfadeDurationSec));
  const partnerTargetTime = Math.max(0, currentSec - crossfadeStartSec);

  if (!state.secondaryStarted) {
    try {
      elements.crossfadePlayer.currentTime = 0;
    } catch (error) {
      console.debug(error);
    }
    elements.crossfadePlayer.playbackRate = elements.sourcePlayer.playbackRate || 1;
    setPreservesPitch(elements.crossfadePlayer, Boolean(elements.sourcePlayer.preservesPitch));
    elements.crossfadePlayer.play().catch((error) => {
      console.error(error);
      setEngineState("Crossfade partner blocked");
    });
    state.secondaryStarted = true;
  } else if (Math.abs((elements.crossfadePlayer.currentTime || 0) - partnerTargetTime) > 0.08) {
    try {
      elements.crossfadePlayer.currentTime = partnerTargetTime;
    } catch (error) {
      console.debug(error);
    }
  }

  state.graph.primarySourceGain.gain.value = 1.0 - progress;
  state.graph.secondarySourceGain.gain.value = progress;
}

async function ensureSecondaryMediaSource() {
  if (!state.audioContext || !state.graph || !elements.crossfadePlayer?.src) {
    return;
  }
  if (!state.secondaryMediaSource) {
    state.secondaryMediaSource = state.audioContext.createMediaElementSource(elements.crossfadePlayer);
  }
  if (state.secondarySourceNode) {
    state.secondarySourceNode.disconnect();
  }
  state.secondarySourceNode = state.secondaryMediaSource;
  state.secondarySourceNode.connect(state.graph.secondarySourceGain);
}

async function ensureAudioContext() {
  if (state.audioContext) {
    if (state.audioContext.state === "suspended") {
      await state.audioContext.resume();
    }
    return state.audioContext;
  }

  const audioContext = new AudioContext({ latencyHint: "interactive" });
  const dynamicsWasmBytes = await loadDynamicsWasmBytes();
  await audioContext.audioWorklet.addModule("/static/api/voxis-basic-processor.js");
  await audioContext.audioWorklet.addModule("/static/api/voxis-color-time-processor.js");
  await audioContext.audioWorklet.addModule("/static/api/voxis-modern-creative-processor.js");
  await audioContext.audioWorklet.addModule("/static/api/voxis-spectral-spatial-processor.js");
  await audioContext.audioWorklet.addModule("/static/api/voxis-dynamics-processor.js");
  await audioContext.audioWorklet.addModule("/static/api/voxis-modulation-processor.js");
  state.audioContext = audioContext;
  state.graph = createGraph(audioContext, dynamicsWasmBytes);
  updateMetrics();
  applyControlsToGraph();
  if (elements.crossfadePlayer?.src) {
    await ensureSecondaryMediaSource();
  }
  startMeterLoop();
  setEngineState("Engine booting");
  return audioContext;
}

function updateMetrics() {
  if (!state.audioContext) {
    return;
  }
  elements.sampleRate.textContent = `${state.audioContext.sampleRate} Hz`;
  const latencyMs = state.audioContext.baseLatency
    ? `${(state.audioContext.baseLatency * 1000).toFixed(1)} ms`
    : "browser default";
  elements.latency.textContent = latencyMs;
  elements.mode.textContent = "JS basic + JS color/time + JS modern/creative + JS spectral/spatial + WASM EQ/filter/dynamics + JS modulation/space";
}

function scheduleBasicConfigUpdate() {
  if (!state.graph) {
    return;
  }

  state.pendingBasicConfig = buildBasicConfig();
  if (state.basicConfigTimer !== null) {
    return;
  }

  state.basicConfigTimer = window.setTimeout(() => {
    state.basicConfigTimer = null;
    if (!state.graph || !state.pendingBasicConfig) {
      return;
    }
    state.graph.basicWorklet.port.postMessage({
      type: "config",
      config: state.pendingBasicConfig,
    });
    state.pendingBasicConfig = null;
  }, 16);
}

function scheduleColorTimeConfigUpdate() {
  if (!state.graph) {
    return;
  }

  state.pendingColorTimeConfig = buildColorTimeConfig();
  if (state.colorTimeConfigTimer !== null) {
    return;
  }

  state.colorTimeConfigTimer = window.setTimeout(() => {
    state.colorTimeConfigTimer = null;
    if (!state.graph || !state.pendingColorTimeConfig) {
      return;
    }
    state.graph.colorTimeWorklet.port.postMessage({
      type: "config",
      config: state.pendingColorTimeConfig,
    });
    state.pendingColorTimeConfig = null;
  }, 16);
}

function scheduleModernCreativeConfigUpdate() {
  if (!state.graph) {
    return;
  }

  state.pendingModernCreativeConfig = buildModernCreativeConfig();
  if (state.modernCreativeConfigTimer !== null) {
    return;
  }

  state.modernCreativeConfigTimer = window.setTimeout(() => {
    state.modernCreativeConfigTimer = null;
    if (!state.graph || !state.pendingModernCreativeConfig) {
      return;
    }
    state.graph.modernCreativeWorklet.port.postMessage({
      type: "config",
      config: state.pendingModernCreativeConfig,
    });
    state.pendingModernCreativeConfig = null;
  }, 16);
}

function scheduleSpectralSpatialConfigUpdate() {
  if (!state.graph) {
    return;
  }

  state.pendingSpectralSpatialConfig = buildSpectralSpatialConfig();
  if (state.spectralSpatialConfigTimer !== null) {
    return;
  }

  state.spectralSpatialConfigTimer = window.setTimeout(() => {
    state.spectralSpatialConfigTimer = null;
    if (!state.graph || !state.pendingSpectralSpatialConfig) {
      return;
    }
    state.graph.spectralSpatialWorklet.port.postMessage({
      type: "config",
      config: state.pendingSpectralSpatialConfig,
    });
    state.pendingSpectralSpatialConfig = null;
  }, 16);
}

function scheduleModulationConfigUpdate() {
  if (!state.graph) {
    return;
  }

  state.pendingModulationConfig = buildModulationConfig();
  if (state.modulationConfigTimer !== null) {
    return;
  }

  state.modulationConfigTimer = window.setTimeout(() => {
    state.modulationConfigTimer = null;
    if (!state.graph || !state.pendingModulationConfig) {
      return;
    }
    state.graph.modulationWorklet.port.postMessage({
      type: "config",
      config: state.pendingModulationConfig,
    });
    state.pendingModulationConfig = null;
  }, 16);
}

function scheduleDynamicsConfigUpdate() {
  if (!state.graph) {
    return;
  }

  state.pendingDynamicsConfig = buildDynamicsConfig();
  if (state.dynamicsConfigTimer !== null) {
    return;
  }

  state.dynamicsConfigTimer = window.setTimeout(() => {
    state.dynamicsConfigTimer = null;
    if (!state.graph || !state.pendingDynamicsConfig) {
      return;
    }
    state.graph.dynamicsWorklet.port.postMessage({
      type: "config",
      config: state.pendingDynamicsConfig,
    });
    state.pendingDynamicsConfig = null;
  }, 16);
}

function scheduleSpaceConfigUpdate() {
  if (!state.graph) {
    return;
  }

  state.pendingSpaceConfig = buildSpaceConfig();
  if (state.spaceConfigTimer !== null) {
    return;
  }

  state.spaceConfigTimer = window.setTimeout(() => {
    state.spaceConfigTimer = null;
    if (!state.graph || !state.pendingSpaceConfig) {
      return;
    }
    state.graph.spaceRack.configure(state.pendingSpaceConfig);
    state.pendingSpaceConfig = null;
  }, 40);
}

function applyControlsToGraph() {
  updateReadouts();
  syncPitchTimeTransport();
  if (!state.graph) {
    return;
  }

  const c = elements.controls;
  const graph = state.graph;
  const params = graph.basicWorklet.parameters;

  params.get("inputGain").value = Number(c.inputGain.value);
  params.get("outputGain").value = Number(c.outputGain.value);
  params.get("monoMix").value = Number(c.monoMix.value);
  params.get("drive").value = Number(c.drive.value);
  params.get("dcBlock").value = c.dcBlock.checked ? 1.0 : 0.0;

  graph.panner.pan.value = Number(c.pan.value);
  graph.master.gain.value = 1.0;
  scheduleBasicConfigUpdate();
  scheduleColorTimeConfigUpdate();
  scheduleModernCreativeConfigUpdate();
  scheduleSpectralSpatialConfigUpdate();
  scheduleModulationConfigUpdate();
  scheduleDynamicsConfigUpdate();
  scheduleSpaceConfigUpdate();
  syncCrossfadeState();
}

function connectSource(sourceNode, label) {
  if (!state.graph) {
    return;
  }
  if (state.activeSourceNode) {
    state.activeSourceNode.disconnect();
  }
  state.activeSourceNode = sourceNode;
  state.activeSourceNode.connect(state.graph.primarySourceGain);
  state.primaryLabel = label;
  elements.sourceKind.textContent = label;
}

async function useFileSource(file) {
  await ensureAudioContext();

  if (state.objectUrl) {
    URL.revokeObjectURL(state.objectUrl);
  }
  state.objectUrl = URL.createObjectURL(file);
  elements.sourcePlayer.src = state.objectUrl;
  elements.sourcePlayer.load();
  syncPitchTimeTransport();

  if (!state.mediaElementSource) {
    state.mediaElementSource = state.audioContext.createMediaElementSource(elements.sourcePlayer);
  }

  if (state.micStream) {
    stopMicrophone();
  }

  state.sourceMode = "file";
  connectSource(state.mediaElementSource, `File: ${file.name}`);
  resetCrossfadePartner(true);
  updateTransportFromPrimary();
  setEngineState("File source armed");
}

async function loadCrossfadePartner(file) {
  await ensureAudioContext();

  if (state.secondaryObjectUrl) {
    URL.revokeObjectURL(state.secondaryObjectUrl);
  }
  state.secondaryObjectUrl = URL.createObjectURL(file);
  elements.crossfadePlayer.src = state.secondaryObjectUrl;
  elements.crossfadePlayer.load();
  syncPitchTimeTransport();
  await ensureSecondaryMediaSource();
  resetCrossfadePartner(true);
  setCrossfadePartnerName(`Loaded: ${file.name}`);
  setEngineState("Crossfade partner ready");
}

async function useMicrophone() {
  await ensureAudioContext();

  if (state.micStream) {
    connectSource(state.audioContext.createMediaStreamSource(state.micStream), "Microphone");
    state.sourceMode = "mic";
    setMicTransportState(true);
    setEngineState("Microphone active");
    return;
  }

  const stream = await navigator.mediaDevices.getUserMedia({
    audio: {
      echoCancellation: false,
      noiseSuppression: false,
      autoGainControl: false,
    },
  });

  state.micStream = stream;
  if (!elements.sourcePlayer.paused) {
    elements.sourcePlayer.pause();
  }
  connectSource(state.audioContext.createMediaStreamSource(stream), "Microphone");
  state.sourceMode = "mic";
  resetCrossfadePartner(true);
  setMicTransportState(true);
  setEngineState("Microphone active");
}

function stopMicrophone() {
  if (!state.micStream) {
    return;
  }
  for (const track of state.micStream.getTracks()) {
    track.stop();
  }
  state.micStream = null;
  if (state.activeSourceNode) {
    state.activeSourceNode.disconnect();
    state.activeSourceNode = null;
  }
  if (elements.sourcePlayer.src && state.mediaElementSource) {
    connectSource(state.mediaElementSource, state.primaryLabel.startsWith("File:") ? state.primaryLabel : "Loaded file");
    state.sourceMode = "file";
    updateTransportFromPrimary();
    setEngineState("File source armed");
    return;
  }
  state.sourceMode = "none";
  elements.sourceKind.textContent = "Microphone stopped";
  setMicTransportState(false);
  setEngineState("Engine ready");
}

function startMeterLoop() {
  if (!state.graph || state.meterFrame) {
    return;
  }

  const analyser = state.graph.analyser;
  const buffer = new Float32Array(analyser.fftSize);

  const draw = () => {
    analyser.getFloatTimeDomainData(buffer);
    let sum = 0;
    for (let index = 0; index < buffer.length; index += 1) {
      sum += buffer[index] * buffer[index];
    }
    const rms = Math.sqrt(sum / buffer.length);
    const db = rms > 0 ? 20 * Math.log10(rms) : -Infinity;
    const normalized = Number.isFinite(db) ? Math.max(0, Math.min(1, (db + 60) / 60)) : 0;
    elements.meterFill.style.width = `${(normalized * 100).toFixed(1)}%`;
    elements.meterDb.textContent = Number.isFinite(db) ? `${db.toFixed(1)} dBFS` : "-inf dBFS";
    syncCrossfadeState();
    state.meterFrame = window.requestAnimationFrame(draw);
  };

  state.meterFrame = window.requestAnimationFrame(draw);
}

function setControlValue(control, value) {
  if (control instanceof HTMLInputElement) {
    if (control.type === "checkbox") {
      control.checked = Boolean(value);
    } else {
      control.value = String(value);
    }
    return;
  }
  if (control instanceof HTMLSelectElement) {
    control.value = String(value);
  }
}

function applyControlValues(values) {
  for (const [key, value] of Object.entries(values)) {
    const control = elements.controls[key];
    if (!control) {
      continue;
    }
    setControlValue(control, value);
  }
}

function applyPreset(name) {
  const values = { ...defaultControlValues, ...(presetOverrides[name] || {}) };
  applyControlValues(values);
  applyControlsToGraph();
}

async function startEngine() {
  await ensureAudioContext();
  if (state.sourceMode === "file") {
    updateTransportFromPrimary();
  }
  setEngineState("Engine running");
}

elements.startEngine.addEventListener("click", async () => {
  try {
    await startEngine();
  } catch (error) {
    console.error(error);
    setEngineState("Engine failed");
  }
});

elements.fileInput.addEventListener("change", async (event) => {
  const [file] = event.target.files || [];
  if (!file) {
    return;
  }
  try {
    await useFileSource(file);
  } catch (error) {
    console.error(error);
    setEngineState("File load failed");
  }
});

elements.crossfadeFileInput.addEventListener("change", async (event) => {
  const [file] = event.target.files || [];
  if (!file) {
    return;
  }
  try {
    await loadCrossfadePartner(file);
  } catch (error) {
    console.error(error);
    setEngineState("Crossfade load failed");
  }
});

elements.convolutionIrInput?.addEventListener("change", async (event) => {
  const [file] = event.target.files || [];
  if (!file) {
    if (state.graph) {
      state.graph.spaceRack.clearConvolutionFile();
      scheduleSpaceConfigUpdate();
    }
    if (elements.convolutionIrName) {
      elements.convolutionIrName.textContent = "No IR loaded";
    }
    return;
  }

  try {
    await ensureAudioContext();
    await state.graph.spaceRack.loadConvolutionFile(file, elements.controls.convolutionReverbNormalize.checked);
    if (elements.convolutionIrName) {
      elements.convolutionIrName.textContent = `Loaded: ${file.name}`;
    }
    scheduleSpaceConfigUpdate();
    setEngineState("Convolution IR ready");
  } catch (error) {
    console.error(error);
    setEngineState("IR load failed");
  }
});

elements.useMic.addEventListener("click", async () => {
  try {
    await useMicrophone();
  } catch (error) {
    console.error(error);
    elements.sourceKind.textContent = "Microphone permission denied";
    setEngineState("Mic unavailable");
  }
});

elements.stopMic.addEventListener("click", () => {
  stopMicrophone();
});

elements.presetButtons.forEach((button) => {
  button.addEventListener("click", () => applyPreset(button.dataset.preset));
});

[
  "loadedmetadata",
  "play",
  "pause",
  "seeking",
  "seeked",
  "timeupdate",
  "ratechange",
  "ended",
].forEach((eventName) => {
  elements.sourcePlayer.addEventListener(eventName, async () => {
    if ((eventName === "play" || eventName === "seeked") && state.audioContext) {
      await state.audioContext.resume();
    }
    if (state.sourceMode === "file") {
      updateTransportFromPrimary();
      if (eventName === "play") {
        resetCrossfadePartner(true);
      }
      if (eventName === "pause" || eventName === "ended") {
        elements.crossfadePlayer.pause();
      }
      if (eventName === "seeked" || eventName === "seeking") {
        resetCrossfadePartner(true);
      }
    }
  });
});

Object.values(elements.controls).forEach((control) => {
  if (!(control instanceof HTMLInputElement) && !(control instanceof HTMLSelectElement)) {
    return;
  }
  const eventName = control instanceof HTMLSelectElement || control.type === "checkbox" ? "change" : "input";
  control.addEventListener(eventName, () => applyControlsToGraph());
});

elements.controls.timeStretchEnabled?.addEventListener("change", () => {
  if (elements.controls.timeStretchEnabled.checked) {
    elements.controls.timeCompressionEnabled.checked = false;
  }
  applyControlsToGraph();
});

elements.controls.timeCompressionEnabled?.addEventListener("change", () => {
  if (elements.controls.timeCompressionEnabled.checked) {
    elements.controls.timeStretchEnabled.checked = false;
  }
  applyControlsToGraph();
});

window.addEventListener("beforeunload", () => {
  if (state.objectUrl) {
    URL.revokeObjectURL(state.objectUrl);
  }
  if (state.secondaryObjectUrl) {
    URL.revokeObjectURL(state.secondaryObjectUrl);
  }
  if (state.basicConfigTimer !== null) {
    window.clearTimeout(state.basicConfigTimer);
  }
  if (state.colorTimeConfigTimer !== null) {
    window.clearTimeout(state.colorTimeConfigTimer);
  }
  if (state.modernCreativeConfigTimer !== null) {
    window.clearTimeout(state.modernCreativeConfigTimer);
  }
  if (state.spectralSpatialConfigTimer !== null) {
    window.clearTimeout(state.spectralSpatialConfigTimer);
  }
  if (state.modulationConfigTimer !== null) {
    window.clearTimeout(state.modulationConfigTimer);
  }
  if (state.dynamicsConfigTimer !== null) {
    window.clearTimeout(state.dynamicsConfigTimer);
  }
  if (state.spaceConfigTimer !== null) {
    window.clearTimeout(state.spaceConfigTimer);
  }
  if (state.meterFrame) {
    window.cancelAnimationFrame(state.meterFrame);
  }
  elements.crossfadePlayer.pause();
  stopMicrophone();
});

applyControlValues(defaultControlValues);
updateReadouts();
syncPitchTimeTransport();
setCrossfadePartnerName("No crossfade partner loaded");
if (elements.convolutionIrName) {
  elements.convolutionIrName.textContent = "No IR loaded";
}
