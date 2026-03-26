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

See [docs/EFFECTS.md](docs/EFFECTS.md) for the overview, [docs/EFFECT_REFERENCE.md](docs/EFFECT_REFERENCE.md) for the complete per-effect usage catalog, and [docs/REALTIME.md](docs/REALTIME.md) for the first realtime browser starter. The offline `web-test` app exposes items 1 through 12 with ready-to-demo defaults, independent control columns, metrics, and per-step timing.

## Documentation site

The repository ships a static documentation site for GitHub Pages and local browsing:

- `index.html`: documentation home page
- `python.html`: step-by-step offline Python guide
- `realtime.html`: step-by-step browser realtime guide
- `realtime-example.html`: live minimal browser example with a `View code` toggle
- `api/`: public browser runtime modules and the shipped WASM asset

The public tutorials are written as learning material, not just reference pages. The Python guide starts from `AudioClip`, `Pipeline`, imports, and presets. The realtime guide explains the HTML + JavaScript wiring pattern, how file inputs connect to `createVoxisRealtimePlayer()`, how `player.setEffects([...])` works, and how to build a slider-based editor.

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

## Realtime Starter

The first realtime browser demo lives in `web-test/real-time/`.

- It now covers checklist sections `1. Basic effects`, `2. Dynamics`, `3. EQ / Filters`, `4. Modulation`, `5. Space / Ambience`, `6. Distortion / Saturation`, `7. Pitch / Time`, `8. Modern / AI-like effects`, `9. Creative / special effects`, `10. Spectral processing`, and `11. Advanced stereo / spatial` in realtime.
- The popup menu now uses the same effect names from `list-effect.md`.
- The basic `AudioWorklet` layer now carries realtime paths for gain, normalize, fade in, fade out, crossfade, trim, cut, silence removal, reverse, pan, mono ↔ stereo, and DC offset removal.
- The WASM EQ/filter/dynamics chain now includes high-pass, low-pass, band-pass, notch, low shelf, high shelf, resonant filter, parametric equalizer, graphic EQ, dynamic EQ, formant filter, compressor, downward compression, upward compression, limiter, expander, noise gate, multiband compressor, de-esser, and transient shaper.
- The modulation `AudioWorklet` layer now includes chorus, flanger, phaser, tremolo, vibrato, auto-pan, rotary speaker, ring modulation, and frequency shifter.
- The realtime space / ambience rack now includes delay, echo, ping-pong delay, multi-tap delay, slapback delay, early reflections, room / hall / plate reverb, and convolution reverb (IR).
- The realtime color/time `AudioWorklet` layer now includes distortion, overdrive, fuzz, bitcrusher, waveshaper, tube saturation, tape saturation, soft clipping, hard clipping, pitch shift, auto-tune, harmonizer, octaver, and formant shifting.
- The realtime modern/creative `AudioWorklet` layer now includes noise reduction, voice isolation, source separation, de-reverb, de-echo, spectral repair, AI enhancer, speech enhancement, glitch effect, stutter, tape stop, reverse reverb, granular synthesis, time slicing, random pitch mod, vinyl effect, radio effect, telephone effect, 8-bit / retro sound, slow motion extreme, robot voice, and alien voice.
- The realtime spectral/spatial `AudioWorklet` layer now includes FFT filter, spectral gating, spectral blur, spectral freeze, spectral morphing, phase vocoder, harmonic/percussive separation, spectral delay, stereo widening, mid/side processing, stereo imager, binaural effect, 3D audio positioning, and HRTF simulation.
- `Time stretch` and `Time compression` now run in realtime preview through the browser file transport with preserved pitch. On microphone input, those two controls are bypassed.
- It uses Web Audio API plus `AudioWorklet` for low-latency preview with either a file source or microphone input.
- The browser UI/controller lives in `app.js`; the realtime DSP entry points live in the processor files; the native EQ/filter/dynamics core is compiled to `voxis-realtime-dynamics.wasm`.
- The processor files are part of the current browser-side Voxis realtime layer. The `.wasm` file alone is not enough by itself; it needs the JavaScript worklet bridge and Web Audio graph wiring around it.
- The reusable browser module now lives in the root `api/` folder, with `voxis-realtime.js` as the public entry point, `voxis-realtime-player.js` handling the graph/player side, and `voxis-realtime-effects.js` exposing builder helpers for the checklist sections.
- It still does not replace the offline `AudioClip` workflow. The browser demo uses streaming-safe counterparts for section 1 clip edits, while the offline API keeps the destructive full-buffer versions.
- For section 8, the browser path is a low-latency realtime approximation layer for monitoring and UI preview; the heavier offline restoration flow still lives in the Python/C++ path.

Run it with:

```bash
python web-test/real-time/app.py
```

Then open `http://127.0.0.1:5101`.

For the separate API test site with live range controls, run `python web-test/api-test/app.py` and open `http://127.0.0.1:5102`.

For a browser-side reusable starter, you can also import:

```js
import { createVoxisRealtimePlayer, effects } from "./api/voxis-realtime.js";

const player = await createVoxisRealtimePlayer({ container: "#player" });
await player.loadUrl("/audio/example.mp3");
player.setEffects([
  effects.gain({ value: 1.1 }),
  effects.compressor({ thresholdDb: -18, ratio: 3.0, makeupDb: 2.0 }),
  effects.chorus({ mix: 0.35, rateHz: 0.9 }),
  effects.hall_reverb({ decaySeconds: 1.8, mix: 0.2 }),
  effects.noise_reduction({ strength: 0.8 }),
  effects.fft_filter({ lowHz: 90, highHz: 9000, mix: 1.0 }),
  effects.hrtf_simulation({ azimuthDeg: 30, elevationDeg: 0, distance: 1.1 }),
]);
```

That wrapper now ships effect builders for sections `1` through `11`, creates a standard `<audio>` element automatically when you pass a container, resolves its processor and WASM files relative to the module location, and can load a file source, microphone source, crossfade partner, and convolution IR without depending on the main demo controller.

## Path resolution

For audio input and output, Voxis resolves every relative path from the directory of the Python file that called the API.

That means this works even when you launch Python from the project root:

```text
project/
  tests/
    test_readme.md.py
    example.mp3
```
---
```python
from voxis import AudioClip

audio = AudioClip.from_file("example.mp3")
```

`example.mp3` is resolved as `tests/example.mp3` because the script is inside `tests/`.

If the file is outside the script folder, use normal relative navigation:

```python
AudioClip.from_file("../example.mp3")
AudioClip.from_file("../folder/example.mp3")
AudioClip.from_file("folder/example.mp3")
```

Those examples mean:

```text
../example.mp3
  go one folder up from the script directory

../folder/example.mp3
  go one folder up, then enter folder/

folder/example.mp3
  enter folder/ inside the script directory
```

Exports follow the same rule, so relative outputs are also created next to the script by default:

```text
project/
  tests/
    test_readme.md.py
```
---
```python
processed.export("output-1.mp3")
processed.export("outputs/clean.wav")
```

The examples above will create:

```text
project/
  tests/
    output-1.mp3
    outputs/
      clean.wav
```

If you want to save or load using another base, pass an explicit relative path like `../example.wav` or an absolute path.

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

PyPI releases are meant to ship prebuilt wheels for Windows, Linux, and macOS. If `pip` ever falls back to the source distribution, Voxis can still install without a local C++ toolchain and will use the Python DSP backend automatically, with the native extension remaining an optional speed-up.

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

Tagged releases are published through GitHub Actions with `cibuildwheel`, so the normal `pip install voxis` path downloads a ready-made wheel instead of compiling C++ on the user's machine.

## Roadmap

- Streaming decoder -> pipeline -> encoder path without loading entire files into memory
- More filters and modulation effects
- Convolution and FIR kernels
- SIMD-specialized kernels
- Native codec integration through libav* for tighter FFmpeg coupling
