# Voxis Effects Overview

Voxis uses the following audio flow:

```text
decoder -> PCM float32 -> DSP pipeline -> encoder
```

## Current catalog summary

- `95` chainable effects/processors are available through `effect_names()`
- `108` total checklist resources are present when clip operations, utilities, and analysis helpers are included
- all 12 planned effect groups currently exposed in the project are implemented in this workspace

## Data model

- input audio is decoded to `float32` PCM before DSP
- the internal layout is `(frames, channels)`
- the fast path runs in the native C++ core
- advanced spectral, restoration, and automation-heavy processors use the Python path when needed

## Full reference

Use [EFFECT_REFERENCE.md](EFFECT_REFERENCE.md) for the complete per-effect catalog, including:

- every exported effect name
- the callable signature
- a starter call for each effect
- clip operation methods
- utility and analysis helpers
- preset names

## Effect groups

The current effect catalog is organized into these groups:

1. Core and stereo helpers
2. Dynamics
3. Filters and EQ
4. Delay and reverb
5. Modulation
6. Distortion and saturation
7. Pitch and time
8. Restoration and AI-like processing
9. Creative processors
10. Spectral processors
11. Spatial processors
12. Clip operations, utilities, and analysis helpers

## Example pipeline

```python
from voxis import AudioClip, Pipeline, delay, distortion, gain, lowpass

clip = AudioClip.from_file("input.wav")

pipeline = (
    Pipeline(sample_rate=clip.sample_rate, channels=clip.channels, block_size=2048)
    >> [
        distortion(drive=2.5),
        lowpass(frequency_hz=12_000.0, stages=2),
        delay(delay_ms=50.0, feedback=0.50, mix=1.00),
        gain(db=10.0),
    ]
)

processed = clip.apply_pipeline(pipeline)
processed.export("output.wav")
```

## Presets

Current preset names:

- `cinematic`
- `clarity_eq`
- `lofi`
- `podcast_clean`
- `radio`
- `vocal_enhance`
- `wide_chorus`

## Useful API entry points

- `effect_names()`
- `preset_names()`
- `Pipeline(...) >> [...]`
- `AudioClip.apply("preset")`
- `AudioClip.apply_pipeline(pipeline)`
- `AudioClip.pipeline_info()`

## Web test app

The `web-test/app.py` demo exposes all implemented groups with ready-to-test defaults, export controls, and timing logs.
