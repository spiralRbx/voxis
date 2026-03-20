# Voxis Effects

Voxis uses `decoder -> PCM float32 -> DSP pipeline -> encoder`.

Current summary:

- `95` chainable effects/processors available via `effect_names()`
- `108` resources in the full checklist when you count clip ops, utilities, and analysis helpers

- Input `mp3`, `ogg`, `wav`, `flac`, `aac`, or `m4a` is always converted to `float32` PCM before DSP.
- The internal buffer uses `(frames, channels)` layout.
- The hot path lives in the native C++ core; the Python path is used for advanced effects and automation.

## Basic Clip Ops (Item 1)

Clip operations:

- `AudioClip.gain(db)`
- `AudioClip.normalize(headroom_db=1.0)`
- `AudioClip.fade_in(duration_ms)`
- `AudioClip.fade_out(duration_ms)`
- `AudioClip.crossfade(other_clip, duration_ms)`
- `AudioClip.trim(start_ms=None, end_ms=None)`
- `AudioClip.cut(start_ms, end_ms)`
- `AudioClip.remove_silence(threshold_db=-48.0, min_silence_ms=80.0, padding_ms=10.0)`
- `AudioClip.reverse()`
- `AudioClip.pan(position)`
- `AudioClip.to_mono()`
- `AudioClip.to_stereo()`
- `AudioClip.remove_dc_offset()`

Example:

```python
from voxis import AudioClip

clip = AudioClip.from_file("voice.wav")
edited = (
    clip.fade_in(180.0)
    .trim(start_ms=50.0, end_ms=12_000.0)
    .remove_silence(threshold_db=-50.0, min_silence_ms=90.0, padding_ms=15.0)
    .remove_dc_offset()
    .normalize(headroom_db=1.0)
)
edited.export("voice_clean.wav")
```

## Dynamics (Item 2)

Individual effects:

- `compressor(threshold_db, ratio, attack_ms, release_ms, makeup_db)`
- `downward_compression(threshold_db, ratio, attack_ms, release_ms, makeup_db)`
- `upward_compression(threshold_db, ratio, attack_ms, release_ms, max_gain_db)`
- `limiter(ceiling_db, attack_ms, release_ms)`
- `expander(threshold_db, ratio, attack_ms, release_ms, makeup_db)`
- `noise_gate(threshold_db, attack_ms, release_ms, floor_db)`
- `deesser(frequency_hz, threshold_db, ratio, attack_ms, release_ms, amount)`
- `transient_shaper(attack, sustain, attack_ms, release_ms)`

Multiband processing:

- `multiband_compressor(sample_rate, ...)`
- `AudioClip.multiband_compressor(...)`

Example:

```python
from voxis import AudioClip

clip = AudioClip.from_file("mix.wav")
mastered = (
    clip.compressor(threshold_db=-18.0, ratio=3.0)
    .upward_compression(threshold_db=-40.0, ratio=2.0, max_gain_db=10.0)
    .transient_shaper(attack=0.6, sustain=0.2)
    .multiband_compressor(low_cut_hz=180.0, high_cut_hz=3200.0)
)
mastered.export("mix_master.wav")
```

## Filters and EQ

- `lowpass(frequency_hz, q, stages)`
- `highpass(frequency_hz, q, stages)`
- `bandpass(frequency_hz, q, stages)`
- `notch(frequency_hz, q, stages)`
- `peak_eq(frequency_hz, gain_db, q, stages)`
- `low_shelf(frequency_hz, gain_db, slope, stages)`
- `high_shelf(frequency_hz, gain_db, slope, stages)`
- `parametric_eq(...)`
- `graphic_eq({100.0: 1.5, 250.0: -1.0, 1_000.0: 2.0, 4_000.0: -0.5, 12_000.0: 1.0}, q=1.1)`
- `resonant_filter(frequency_hz, resonance, mode="lowpass", stages=1)`
- `dynamic_eq(frequency_hz, threshold_db, cut_db, q, attack_ms, release_ms)`
- `formant_filter(morph=0.0, intensity=1.0, q=4.0)`

Example:

```python
from voxis import AudioClip

clip = AudioClip.from_file("voice.wav")
shaped = (
    clip.highpass(90.0, stages=2)
    .graphic_eq({250.0: -1.5, 1_000.0: 1.0, 4_000.0: 2.2, 12_000.0: 1.4})
    .dynamic_eq(3_000.0, threshold_db=-22.0, cut_db=-5.0)
    .formant_filter(0.75, intensity=0.65)
)
shaped.export("voice_eq.wav")
```

## Delay and Reverb

- `delay(delay_ms, feedback, mix)`
- `feedback_delay(delay_ms, feedback, mix)`
- `echo(delay_ms, feedback, mix)`
- `ping_pong_delay(delay_ms, feedback, mix)`
- `multi_tap_delay(delay_ms, taps, spacing_ms, decay, mix)`
- `slapback(delay_ms, mix)`
- `early_reflections(pre_delay_ms, spread_ms, taps, decay, mix)`
- `room_reverb(decay_seconds, mix, tone_hz)`
- `hall_reverb(decay_seconds, mix, tone_hz)`
- `plate_reverb(decay_seconds, mix, tone_hz)`
- `convolution_reverb(impulse_response, mix, normalize_ir)`

Example:

```python
from voxis import AudioClip

clip = AudioClip.from_file("guitar.wav")
spaced = (
    clip.echo(delay_ms=320.0, feedback=0.35, mix=0.24)
    .slapback(delay_ms=92.0, mix=0.18)
    .plate_reverb(decay_seconds=1.2, mix=0.22)
)
spaced.export("guitar_space.wav")
```

## Modulation

- `chorus(rate_hz, depth_ms, delay_ms, mix, feedback)`
- `flanger(rate_hz, depth_ms, delay_ms, mix, feedback)`
- `phaser(rate_hz, depth, center_hz, feedback, mix, stages)`
- `tremolo(rate_hz, depth)`
- `vibrato(rate_hz, depth_ms, delay_ms)`
- `auto_pan(rate_hz, depth)`
- `rotary_speaker(rate_hz, depth, mix, crossover_hz)`
- `ring_modulation(frequency_hz, mix)`
- `frequency_shifter(shift_hz, mix)`

Example:

```python
from voxis import AudioClip

clip = AudioClip.from_file("synth.wav")
modded = (
    clip.chorus(rate_hz=0.35, depth_ms=8.0, mix=0.4)
    .phaser(rate_hz=0.25, depth=0.8, feedback=0.2, mix=0.45)
    .rotary_speaker(rate_hz=0.9, depth=0.7, mix=0.55)
)
modded.export("synth_motion.wav")
```

## Saturation and Drive

- `distortion(drive)`
- `overdrive(drive, tone, mix)`
- `fuzz(drive, bias, mix)`
- `bitcrusher(bit_depth, sample_rate_reduction, mix)`
- `waveshaper(amount, symmetry, mix)`
- `tube_saturation(drive, bias, mix)`
- `tape_saturation(drive, softness, mix)`
- `soft_clipping(threshold)`
- `hard_clipping(threshold)`

Example:

```python
from voxis import AudioClip

clip = AudioClip.from_file("bass.wav")
driven = (
    clip.overdrive(drive=1.7, tone=0.6)
    .tube_saturation(drive=1.4, bias=0.06, mix=0.75)
    .soft_clipping(threshold=0.86)
)
driven.export("bass_drive.wav")
```

## Pitch and Time

- `pitch_shift(semitones, fft_size, hop_size)`
- `time_stretch(rate, fft_size, hop_size)`
- `time_compression(rate, fft_size, hop_size)`
- `auto_tune(strength, key, scale, min_hz, max_hz, fft_size, hop_size)`
- `harmonizer(intervals_semitones, mix, fft_size, hop_size)`
- `octaver(octaves_down, octaves_up, down_mix, up_mix, fft_size, hop_size)`
- `formant_shifting(shift, mix, fft_size, hop_size)`

Example:

```python
from voxis import AudioClip

clip = AudioClip.from_file("lead.wav")
pitched = (
    clip.pitch_shift(3.0)
    .harmonizer((7.0,), mix=0.28)
    .formant_shifting(1.08, mix=0.75)
)
pitched.export("lead_shifted.wav")
```

## Restoration and AI-like

- `noise_reduction(strength, fft_size, hop_size)`
- `voice_isolation(strength, low_hz, high_hz, fft_size, hop_size)`
- `source_separation(target, strength, low_hz, high_hz, fft_size, hop_size)`
- `de_reverb(amount, tail_ms, fft_size, hop_size)`
- `de_echo(amount, min_delay_ms, max_delay_ms)`
- `spectral_repair(strength, fft_size, hop_size)`
- `ai_enhancer(amount, fft_size, hop_size)`
- `speech_enhancement(amount, fft_size, hop_size)`

Example:

```python
from voxis import AudioClip

clip = AudioClip.from_file("podcast.wav")
restored = (
    clip.noise_reduction(strength=0.45)
    .de_reverb(amount=0.30)
    .speech_enhancement(amount=0.65)
)
restored.export("podcast_restored.wav")
```

## Creative and Special

- `glitch_effect(slice_ms, repeat_probability, dropout_probability, reverse_probability, mix)`
- `stutter(slice_ms, repeats, interval_ms, mix)`
- `tape_stop(stop_time_ms, curve, mix)`
- `reverse_reverb(decay_seconds, mix)`
- `granular_synthesis(grain_ms, overlap, jitter_ms, mix)`
- `time_slicing(slice_ms, mix)`
- `random_pitch_mod(depth_semitones, segment_ms, mix)`
- `vinyl_effect(noise, wow, crackle, mix)`
- `radio_effect(noise_level, mix)`
- `telephone_effect(mix)`
- `retro_8bit(bit_depth, sample_rate_reduction, mix)`
- `slow_motion_extreme(rate, tone_hz)`
- `robot_voice(carrier_hz, mix)`
- `alien_voice(shift_semitones, formant_shift, mix)`

Example:

```python
from voxis import AudioClip

clip = AudioClip.from_file("hook.wav")
creative = (
    clip.glitch_effect(slice_ms=60.0, repeat_probability=0.18, mix=0.85)
    .stutter(slice_ms=75.0, repeats=2, interval_ms=420.0, mix=0.65)
    .vinyl_effect(noise=0.06, wow=0.12, crackle=0.09)
)
creative.export("hook_fx.wav")
```

## Spectral

- `fft_filter(low_hz, high_hz, mix, fft_size, hop_size)`
- `spectral_gating(threshold_db, floor, fft_size, hop_size)`
- `spectral_blur(amount, fft_size, hop_size)`
- `spectral_freeze(start_ms, mix, fft_size, hop_size)`
- `spectral_morphing(amount, fft_size, hop_size)`
- `phase_vocoder(rate, fft_size, hop_size)`
- `harmonic_percussive_separation(target, mix, fft_size, hop_size)`
- `spectral_delay(max_delay_ms, feedback, mix, fft_size, hop_size)`

Example:

```python
from voxis import AudioClip

clip = AudioClip.from_file("texture.wav")
spectral = (
    clip.fft_filter(low_hz=120.0, high_hz=8_500.0)
    .spectral_blur(amount=0.35)
    .spectral_delay(max_delay_ms=180.0, feedback=0.2, mix=0.3)
)
spectral.export("texture_spectral.wav")
```

## Spatial

- `pan(position)`
- `stereo_width(width)`
- `stereo_widening(amount)`
- `mid_side_processing(mid_gain_db, side_gain_db)`
- `stereo_imager(low_width, high_width, crossover_hz)`
- `binaural_effect(azimuth_deg, distance, room_mix)`
- `spatial_positioning(azimuth_deg, elevation_deg, distance)`
- `hrtf_simulation(azimuth_deg, elevation_deg, distance)`

Example:

```python
from voxis import AudioClip

clip = AudioClip.from_file("ambience.wav")
space = (
    clip.stereo_widening(1.25)
    .stereo_imager(low_width=0.9, high_width=1.4)
    .spatial_positioning(azimuth_deg=30.0, elevation_deg=10.0, distance=1.2)
)
space.export("ambience_spatial.wav")
```

## Utilities and Analysis

Processing:

- `AudioClip.resample(target_sample_rate)`
- `AudioClip.dither(bit_depth=16)`
- `AudioClip.bit_depth_conversion(bit_depth=16, dither=True)`
- `AudioClip.loudness_normalization(target_lufs=-16.0)`

Analysis:

- `AudioClip.peak_detection()`
- `AudioClip.rms_analysis()`
- `AudioClip.loudness_lufs()`
- `AudioClip.envelope_follower(attack_ms=10.0, release_ms=80.0)`

Example:

```python
from voxis import AudioClip

clip = AudioClip.from_file("mix.wav")
prepared = (
    clip.resample(48_000)
    .loudness_normalization(target_lufs=-16.0)
    .bit_depth_conversion(16)
)

print("Peak:", prepared.peak_detection())
print("RMS:", prepared.rms_analysis())
print("LUFS:", prepared.loudness_lufs())
envelope = prepared.envelope_follower()
```

## Presets

- `radio`
- `vocal_enhance`
- `cinematic`
- `podcast_clean`
- `lofi`
- `clarity_eq`
- `wide_chorus`

## Pipeline Debug

```python
rendered = clip.apply("radio", lazy=True).render()
print(rendered.pipeline_info())
```

Example:

```text
[0] highpass(frequency_hz=180.00Hz, q=0.707, stages=2)
[1] lowpass(frequency_hz=3200.00Hz, q=0.707, stages=2)
[2] distortion(drive=1.2)
```

## Lazy Render and Cache

```python
first = clip.apply("cinematic", lazy=True).normalize().render()
second = clip.apply("cinematic", lazy=True).normalize().render()
```

If the lazy chain is identical for the same `AudioClip`, Voxis reuses the cached render.

## Web Test

`web-test/app.py` now exposes items 1 through 12 directly, splits the groups into independent columns for faster testing, and shows timing per stage in the `<pre>` block, which helps validate:

- cost per effect/operation
- final pipeline
- export warnings
- resample/export behavior by format

