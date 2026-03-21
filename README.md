# Voxis

Voxis is a hybrid Python + C++ audio library built for modular DSP pipelines, band-based processing, and a developer experience that feels closer to `pydub` than to low-level DSP toolkits.

## Goals

- Modular DSP pipeline with block-based float32 processing
- Simple Python API for loading, chaining effects, and exporting audio
- C++ core for high-performance effect execution
- FFmpeg-powered decode/encode flow that works cross-platform
- Band-splitting foundation for multiband effects and processing graphs

## Architecture

```text
decoder (FFmpeg) -> PCM float32 buffer -> DSP pipeline -> encoder (FFmpeg)
```

### Design principles

- All transformations run on `float32` buffers
- Internal layout is frame-major: `(frames, channels)`
- Effects are stateful and process in blocks
- Multithreading is optional and exposed through the pipeline API
- Python owns orchestration; C++ owns the hot DSP loop

## Included in this baseline

- `95` chainable effects/processors available via `effect_names()`
- `108` total checklist resources when you count clip ops, utilities, and analysis helpers
- C++ pipeline runner with Python bindings
- Basic clip operations: normalize, fade in/out, trim, cut, crossfade, silence removal, reverse, mono/stereo conversion, DC offset removal
- Effects: gain, clip, lowpass, highpass, bandpass, notch, peak EQ, low shelf, high shelf, delay, tremolo, distortion, compressor, limiter, expander, noise gate, de-esser, pan, stereo width
- Dynamics extensions: downward compression, upward compression, transient shaper, multiband compressor
- Advanced EQ/modulation: graphic EQ, resonant filter, dynamic EQ, formant filter, chorus, flanger, phaser, vibrato, auto-pan, rotary speaker, ring modulation, frequency shifter
- Advanced time/space effects: delay, feedback delay, echo, ping-pong delay, multi-tap delay, slapback, room/hall/plate reverb, early reflections, convolution reverb
- Saturation and lo-fi effects: overdrive, fuzz, bitcrusher, waveshaper, tube saturation, tape saturation, soft clipping, hard clipping
- Pitch/tempo effects: pitch shift, time stretch, time compression, auto-tune, harmonizer, octaver, formant shifting
- Restoration effects: noise reduction, voice isolation, source separation, de-reverb, de-echo, spectral repair, AI enhancer, speech enhancement
- Creative effects: glitch, stutter, tape stop, reverse reverb, granular synthesis, time slicing, random pitch modulation, vinyl, radio, telephone, retro 8-bit, slow motion, robot voice, alien voice
- Spectral effects: FFT filter, spectral gating, spectral blur, spectral freeze, spectral morphing, phase vocoder, harmonic/percussive separation, spectral delay
- Spatial effects: stereo widening, mid/side processing, stereo imager, binaural effect, spatial positioning, HRTF-style simulation
- Utility/analysis tools: resample, dither, bit-depth conversion, loudness normalization, peak detection, RMS analysis, envelope follower
- `AudioClip` class inspired by the ergonomics of `pydub`
- Multiband processor scaffold using Linkwitz-Riley-style band splits
- Lazy render support for deferred processing chains
- Presets such as `radio`, `vocal_enhance`, `cinematic`, `podcast_clean`, and `lofi`
- Pipeline debug via `pipeline_info()` and lazy render cache reuse
- FFmpeg backend using `imageio-ffmpeg` to resolve the binary portably
- Tests and a simple benchmark

See [docs/EFFECTS.md](docs/EFFECTS.md) for the overview and [docs/EFFECT_REFERENCE.md](docs/EFFECT_REFERENCE.md) for the complete per-effect usage catalog. The `web-test` app now exposes items 1 through 12 with ready-to-demo defaults, independent control columns, metrics, and per-step timing.

## Quick start

```python
from voxis import AudioClip, Pipeline, compressor, delay, distortion, lowpass

clip = AudioClip.from_file("input.wav")

pipeline = (
    Pipeline(sample_rate=clip.sample_rate, channels=clip.channels, block_size=2048)
    >> [
        distortion(drive=2.5),
        lowpass(frequency_hz=8_000, stages=2),
        delay(delay_ms=135, feedback=0.32, mix=0.22),
        compressor(threshold_db=-18.0, ratio=3.5),
    ]
)

processed = clip.apply_pipeline(pipeline)
processed.export("output.wav")
```

## Presets

```python
from voxis import AudioClip

clip = AudioClip.from_file("voice.wav")
processed = clip.apply("vocal_enhance")
processed.export("voice_master.mp3", bitrate="192k", format="mp3", sample_rate=44_100)
```

## Clip Editing

```python
edited = (
    clip.fade_in(180.0)
    .trim(start_ms=50.0, end_ms=12_000.0)
    .remove_silence(threshold_db=-50.0, min_silence_ms=90.0, padding_ms=15.0)
    .remove_dc_offset()
)
```

## Lazy render

```python
lazy_clip = clip.apply("cinematic", lazy=True).normalize(headroom_db=1.0)
lazy_clip.export("final.wav")
```

## Pipeline Debug

```python
rendered = clip.apply("radio", lazy=True).render()
print(rendered.pipeline_info())
```

## Installation

```bash
python -m pip install voxis
```

For local development:

```bash
python -m pip install -e .[dev]
```

The build pulls `cmake`, `ninja`, and `pybind11` automatically through the package build backend when they are not already available on the machine.

When the native DSP core changes, rerun `python -m pip install -e .[dev]` and restart `web-test/app.py` so the rebuilt extension is the one actually loaded.

## Packaging

```bash
make install-dev
make test
make build
make check
```

## Roadmap

- Streaming decoder -> pipeline -> encoder path without loading entire files into memory
- More filters and modulation effects
- Convolution and FIR kernels
- SIMD-specialized kernels
- Native codec integration through libav* for tighter FFmpeg coupling
