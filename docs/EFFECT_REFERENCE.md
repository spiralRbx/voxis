# Voxis Effect Reference

This document is the full callable reference for the current Voxis effect catalog.

## Scope

- `95` chainable effects/processors are exported by `effect_names()`
- the 12 implemented effect groups are present in this workspace
- clip editing, utility, and analysis helpers are listed at the end because they are method-based instead of `Effect` factories

## Starter recipe

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
```

## Notes

- signatures below match the current Python API
- starter calls are practical examples, not strict recommendations
- `graphic_eq()` and `formant_filter()` return lists of effects/builders that can still be inserted into a pipeline
- `parametric_eq()` is a builder helper rather than a single effect name from `effect_names()`

## Core and Stereo Helpers

- `gain(db)`
  Starter: `gain(db=6.0)`
- `clip(threshold=0.98)`
  Starter: `clip(threshold=0.98)`
- `pan(position)`
  Starter: `pan(position=0.25)`
- `stereo_width(width=1.0)`
  Starter: `stereo_width(width=1.15)`

## Dynamics

- `compressor(threshold_db=-18.0, ratio=4.0, attack_ms=10.0, release_ms=80.0, makeup_db=0.0)`
  Starter: `compressor(threshold_db=-18.0, ratio=3.0, makeup_db=1.5)`
- `downward_compression(threshold_db=-18.0, ratio=4.0, attack_ms=10.0, release_ms=80.0, makeup_db=0.0)`
  Starter: `downward_compression(threshold_db=-20.0, ratio=4.0)`
- `upward_compression(threshold_db=-42.0, ratio=2.0, attack_ms=12.0, release_ms=120.0, max_gain_db=18.0)`
  Starter: `upward_compression(threshold_db=-42.0, ratio=2.0, max_gain_db=18.0)`
- `limiter(ceiling_db=-1.0, attack_ms=1.0, release_ms=60.0)`
  Starter: `limiter(ceiling_db=-1.0)`
- `expander(threshold_db=-35.0, ratio=2.0, attack_ms=8.0, release_ms=80.0, makeup_db=0.0)`
  Starter: `expander(threshold_db=-34.0, ratio=1.8)`
- `noise_gate(threshold_db=-45.0, attack_ms=3.0, release_ms=60.0, floor_db=-80.0)`
  Starter: `noise_gate(threshold_db=-48.0, floor_db=-80.0)`
- `deesser(frequency_hz=6500.0, threshold_db=-28.0, ratio=4.0, attack_ms=2.0, release_ms=60.0, amount=1.0)`
  Starter: `deesser(frequency_hz=6500.0, threshold_db=-28.0, amount=0.8)`
- `transient_shaper(attack=0.7, sustain=0.2, attack_ms=18.0, release_ms=120.0)`
  Starter: `transient_shaper(attack=0.75, sustain=0.25)`

## Filters and EQ

- `lowpass(frequency_hz, q=0.70710678, stages=1)`
  Starter: `lowpass(frequency_hz=12_000.0, stages=2)`
- `highpass(frequency_hz, q=0.70710678, stages=1)`
  Starter: `highpass(frequency_hz=120.0, stages=2)`
- `bandpass(frequency_hz, q=0.70710678, stages=1)`
  Starter: `bandpass(frequency_hz=1_200.0, q=0.9)`
- `notch(frequency_hz, q=0.70710678, stages=1)`
  Starter: `notch(frequency_hz=3_500.0, q=2.0)`
- `peak_eq(frequency_hz, gain_db, q=1.0, stages=1)`
  Starter: `peak_eq(frequency_hz=2_800.0, gain_db=2.5, q=1.0)`
- `low_shelf(frequency_hz, gain_db, slope=1.0, stages=1)`
  Starter: `low_shelf(frequency_hz=120.0, gain_db=2.0)`
- `high_shelf(frequency_hz, gain_db, slope=1.0, stages=1)`
  Starter: `high_shelf(frequency_hz=9_000.0, gain_db=1.8)`
- `graphic_eq(bands, q=1.1)`
  Starter: `graphic_eq({100.0: 0.0, 250.0: 0.0, 1000.0: 0.0, 4000.0: 0.0, 12000.0: 0.0}, q=1.1)`
- `resonant_filter(frequency_hz, resonance=1.6, mode="lowpass", stages=1)`
  Starter: `resonant_filter(frequency_hz=1_200.0, resonance=2.4, mode="lowpass")`
- `dynamic_eq(frequency_hz, threshold_db=-24.0, cut_db=-6.0, q=1.2, attack_ms=10.0, release_ms=120.0)`
  Starter: `dynamic_eq(frequency_hz=2_800.0, threshold_db=-24.0, cut_db=-6.0)`
- `formant_filter(morph=0.0, intensity=1.0, q=4.0)`
  Starter: `formant_filter(morph=0.75, intensity=0.65)`
- `eq_band(kind, frequency_hz, gain_db=0.0, q=0.70710678, slope=1.0, stages=1)`
  Starter: `eq_band("peak", frequency_hz=3_000.0, gain_db=2.0, q=1.0)`
- `parametric_eq(*bands)`
  Starter: `parametric_eq(eq_band("highpass", 90.0, stages=2), eq_band("peak", 3_000.0, gain_db=2.0, q=1.0), eq_band("high_shelf", 10_000.0, gain_db=1.5))`

## Delay and Reverb

- `delay(delay_ms, feedback=0.35, mix=0.2)`
  Starter: `delay(delay_ms=50.0, feedback=0.50, mix=1.00)`
- `feedback_delay(delay_ms, feedback=0.6, mix=0.35)`
  Starter: `feedback_delay(delay_ms=240.0, feedback=0.62, mix=0.35)`
- `echo(delay_ms=320.0, feedback=0.38, mix=0.28)`
  Starter: `echo(delay_ms=320.0, feedback=0.38, mix=0.28)`
- `ping_pong_delay(delay_ms, feedback=0.55, mix=0.3)`
  Starter: `ping_pong_delay(delay_ms=220.0, feedback=0.58, mix=0.30)`
- `multi_tap_delay(delay_ms=120.0, taps=4, spacing_ms=65.0, decay=0.6, mix=0.32)`
  Starter: `multi_tap_delay(delay_ms=110.0, taps=4, spacing_ms=65.0, decay=0.6, mix=0.32)`
- `slapback(delay_ms=95.0, mix=0.24)`
  Starter: `slapback(delay_ms=92.0, mix=0.22)`
- `early_reflections(pre_delay_ms=12.0, spread_ms=8.0, taps=6, decay=0.7, mix=0.22)`
  Starter: `early_reflections(pre_delay_ms=12.0, spread_ms=8.0, taps=6, decay=0.7, mix=0.18)`
- `room_reverb(decay_seconds=0.8, mix=0.22, tone_hz=8000.0)`
  Starter: `room_reverb(decay_seconds=0.8, mix=0.22, tone_hz=8_000.0)`
- `hall_reverb(decay_seconds=1.8, mix=0.28, tone_hz=7200.0)`
  Starter: `hall_reverb(decay_seconds=1.9, mix=0.26, tone_hz=7_200.0)`
- `plate_reverb(decay_seconds=1.2, mix=0.24, tone_hz=9500.0)`
  Starter: `plate_reverb(decay_seconds=1.2, mix=0.22, tone_hz=9_500.0)`
- `convolution_reverb(impulse_response, mix=0.28, normalize_ir=True)`
  Starter: `convolution_reverb("impulse-response.wav", mix=0.24, normalize_ir=True)`

## Modulation

- `chorus(rate_hz=0.9, depth_ms=7.5, delay_ms=18.0, mix=0.35, feedback=0.12)`
  Starter: `chorus(rate_hz=0.9, depth_ms=7.5, mix=0.35)`
- `flanger(rate_hz=0.25, depth_ms=1.8, delay_ms=2.5, mix=0.45, feedback=0.35)`
  Starter: `flanger(rate_hz=0.25, depth_ms=1.8, mix=0.45)`
- `phaser(rate_hz=0.35, depth=0.75, center_hz=900.0, feedback=0.2, mix=0.5, stages=4)`
  Starter: `phaser(rate_hz=0.35, depth=0.75, mix=0.50, stages=4)`
- `tremolo(rate_hz, depth=0.5)`
  Starter: `tremolo(rate_hz=5.0, depth=0.50)`
- `vibrato(rate_hz=5.0, depth_ms=3.5, delay_ms=5.5)`
  Starter: `vibrato(rate_hz=5.0, depth_ms=3.5)`
- `auto_pan(rate_hz=0.35, depth=1.0)`
  Starter: `auto_pan(rate_hz=0.35, depth=1.0)`
- `rotary_speaker(rate_hz=0.8, depth=0.7, mix=0.65, crossover_hz=900.0)`
  Starter: `rotary_speaker(rate_hz=0.8, depth=0.7, mix=0.65)`
- `ring_modulation(frequency_hz=30.0, mix=0.5)`
  Starter: `ring_modulation(frequency_hz=30.0, mix=0.5)`
- `frequency_shifter(shift_hz=120.0, mix=1.0)`
  Starter: `frequency_shifter(shift_hz=120.0, mix=1.0)`

## Distortion and Saturation

- `distortion(drive=2.0)`
  Starter: `distortion(drive=2.5)`
- `overdrive(drive=1.8, tone=0.55, mix=1.0)`
  Starter: `overdrive(drive=1.8, tone=0.55, mix=1.0)`
- `fuzz(drive=3.6, bias=0.12, mix=1.0)`
  Starter: `fuzz(drive=3.6, bias=0.12, mix=1.0)`
- `bitcrusher(bit_depth=8, sample_rate_reduction=4, mix=1.0)`
  Starter: `bitcrusher(bit_depth=8, sample_rate_reduction=4, mix=1.0)`
- `waveshaper(amount=1.4, symmetry=0.0, mix=1.0)`
  Starter: `waveshaper(amount=1.4, symmetry=0.0, mix=1.0)`
- `tube_saturation(drive=1.6, bias=0.08, mix=1.0)`
  Starter: `tube_saturation(drive=1.6, bias=0.08, mix=1.0)`
- `tape_saturation(drive=1.4, softness=0.35, mix=1.0)`
  Starter: `tape_saturation(drive=1.4, softness=0.35, mix=1.0)`
- `soft_clipping(threshold=0.85)`
  Starter: `soft_clipping(threshold=0.85)`
- `hard_clipping(threshold=0.92)`
  Starter: `hard_clipping(threshold=0.92)`

## Pitch and Time

- `pitch_shift(semitones, fft_size=1536, hop_size=512)`
  Starter: `pitch_shift(semitones=3.0, fft_size=1536, hop_size=512)`
- `time_stretch(rate=0.9, fft_size=1536, hop_size=512)`
  Starter: `time_stretch(rate=0.85, fft_size=1536, hop_size=512)`
- `time_compression(rate=1.15, fft_size=1536, hop_size=512)`
  Starter: `time_compression(rate=1.18, fft_size=1536, hop_size=512)`
- `auto_tune(strength=0.7, key="C", scale="chromatic", min_hz=80.0, max_hz=1000.0, fft_size=1024, hop_size=512)`
  Starter: `auto_tune(strength=0.70, key="C", scale="chromatic")`
- `harmonizer(intervals_semitones=(7.0,), mix=0.35, fft_size=1536, hop_size=512)`
  Starter: `harmonizer(intervals_semitones=(7.0,), mix=0.35)`
- `octaver(octaves_down=1, octaves_up=0, down_mix=0.45, up_mix=0.0, fft_size=1536, hop_size=512)`
  Starter: `octaver(octaves_down=1, down_mix=0.45, up_mix=0.0)`
- `formant_shifting(shift=1.12, mix=1.0, fft_size=1536, hop_size=512)`
  Starter: `formant_shifting(shift=1.12, mix=1.0)`

## Restoration and AI-like

- `noise_reduction(strength=0.5, fft_size=1024, hop_size=512)`
  Starter: `noise_reduction(strength=0.50)`
- `voice_isolation(strength=0.75, low_hz=120.0, high_hz=5200.0, fft_size=1024, hop_size=512)`
  Starter: `voice_isolation(strength=0.75, low_hz=120.0, high_hz=5_200.0)`
- `source_separation(target="vocals", strength=0.8, low_hz=120.0, high_hz=5200.0, fft_size=1024, hop_size=512)`
  Starter: `source_separation(target="vocals", strength=0.80)`
- `de_reverb(amount=0.45, tail_ms=240.0, fft_size=1024, hop_size=512)`
  Starter: `de_reverb(amount=0.45, tail_ms=240.0)`
- `de_echo(amount=0.45, min_delay_ms=60.0, max_delay_ms=800.0)`
  Starter: `de_echo(amount=0.45, min_delay_ms=60.0, max_delay_ms=800.0)`
- `spectral_repair(strength=0.35, fft_size=1024, hop_size=512)`
  Starter: `spectral_repair(strength=0.35)`
- `ai_enhancer(amount=0.6, fft_size=1024, hop_size=512)`
  Starter: `ai_enhancer(amount=0.60)`
- `speech_enhancement(amount=0.7, fft_size=1024, hop_size=512)`
  Starter: `speech_enhancement(amount=0.70)`

## Creative Processors

- `glitch_effect(slice_ms=70.0, repeat_probability=0.22, dropout_probability=0.12, reverse_probability=0.1, mix=1.0)`
  Starter: `glitch_effect(slice_ms=70.0, repeat_probability=0.22, mix=1.0)`
- `stutter(slice_ms=90.0, repeats=3, interval_ms=480.0, mix=1.0)`
  Starter: `stutter(slice_ms=90.0, repeats=3, interval_ms=480.0, mix=1.0)`
- `tape_stop(stop_time_ms=900.0, curve=2.0, mix=1.0)`
  Starter: `tape_stop(stop_time_ms=900.0, curve=2.0, mix=1.0)`
- `reverse_reverb(decay_seconds=1.2, mix=0.45)`
  Starter: `reverse_reverb(decay_seconds=1.2, mix=0.45)`
- `granular_synthesis(grain_ms=80.0, overlap=0.5, jitter_ms=25.0, mix=1.0)`
  Starter: `granular_synthesis(grain_ms=80.0, overlap=0.5, jitter_ms=25.0, mix=1.0)`
- `time_slicing(slice_ms=120.0, mix=1.0)`
  Starter: `time_slicing(slice_ms=120.0, mix=1.0)`
- `random_pitch_mod(depth_semitones=2.0, segment_ms=180.0, mix=1.0)`
  Starter: `random_pitch_mod(depth_semitones=2.0, segment_ms=180.0, mix=1.0)`
- `vinyl_effect(noise=0.08, wow=0.15, crackle=0.12, mix=1.0)`
  Starter: `vinyl_effect(noise=0.08, wow=0.15, crackle=0.12, mix=1.0)`
- `radio_effect(noise_level=0.04, mix=1.0)`
  Starter: `radio_effect(noise_level=0.04, mix=1.0)`
- `telephone_effect(mix=1.0)`
  Starter: `telephone_effect(mix=1.0)`
- `retro_8bit(bit_depth=6, sample_rate_reduction=8, mix=1.0)`
  Starter: `retro_8bit(bit_depth=6, sample_rate_reduction=8, mix=1.0)`
- `slow_motion_extreme(rate=0.45, tone_hz=4800.0)`
  Starter: `slow_motion_extreme(rate=0.45, tone_hz=4_800.0)`
- `robot_voice(carrier_hz=70.0, mix=0.85)`
  Starter: `robot_voice(carrier_hz=70.0, mix=0.85)`
- `alien_voice(shift_semitones=5.0, formant_shift=1.18, mix=0.8)`
  Starter: `alien_voice(shift_semitones=5.0, formant_shift=1.18, mix=0.80)`

## Spectral Processors

- `fft_filter(low_hz=80.0, high_hz=12000.0, mix=1.0, fft_size=1024, hop_size=512)`
  Starter: `fft_filter(low_hz=80.0, high_hz=12_000.0, mix=1.0)`
- `spectral_gating(threshold_db=-42.0, floor=0.08, fft_size=1024, hop_size=512)`
  Starter: `spectral_gating(threshold_db=-42.0, floor=0.08)`
- `spectral_blur(amount=0.45, fft_size=1024, hop_size=512)`
  Starter: `spectral_blur(amount=0.45)`
- `spectral_freeze(start_ms=120.0, mix=0.7, fft_size=1024, hop_size=512)`
  Starter: `spectral_freeze(start_ms=120.0, mix=0.70)`
- `spectral_morphing(amount=0.5, fft_size=1024, hop_size=512)`
  Starter: `spectral_morphing(amount=0.50)`
- `phase_vocoder(rate=0.85, fft_size=1536, hop_size=512)`
  Starter: `phase_vocoder(rate=0.85)`
- `harmonic_percussive_separation(target="harmonic", mix=1.0, fft_size=1024, hop_size=512)`
  Starter: `harmonic_percussive_separation(target="harmonic", mix=1.0)`
- `spectral_delay(max_delay_ms=240.0, feedback=0.15, mix=0.35, fft_size=1024, hop_size=512)`
  Starter: `spectral_delay(max_delay_ms=240.0, feedback=0.15, mix=0.35)`

## Spatial Processors

- `stereo_widening(amount=1.25)`
  Starter: `stereo_widening(amount=1.25)`
- `mid_side_processing(mid_gain_db=0.0, side_gain_db=0.0)`
  Starter: `mid_side_processing(mid_gain_db=0.0, side_gain_db=1.5)`
- `stereo_imager(low_width=0.9, high_width=1.35, crossover_hz=280.0)`
  Starter: `stereo_imager(low_width=0.9, high_width=1.35, crossover_hz=280.0)`
- `binaural_effect(azimuth_deg=25.0, distance=1.0, room_mix=0.08)`
  Starter: `binaural_effect(azimuth_deg=25.0, distance=1.0, room_mix=0.08)`
- `spatial_positioning(azimuth_deg=25.0, elevation_deg=0.0, distance=1.0)`
  Starter: `spatial_positioning(azimuth_deg=30.0, elevation_deg=10.0, distance=1.2)`
- `hrtf_simulation(azimuth_deg=30.0, elevation_deg=0.0, distance=1.0)`
  Starter: `hrtf_simulation(azimuth_deg=30.0, elevation_deg=0.0, distance=1.0)`

## Clip Operation Methods

- `AudioClip.gain(db)`
- `AudioClip.normalize(headroom_db=1.0)`
- `AudioClip.fade_in(duration_ms)`
- `AudioClip.fade_out(duration_ms)`
- `AudioClip.crossfade(other_clip, duration_ms)`
- `AudioClip.trim(start_ms=None, end_ms=None)`
- `AudioClip.cut(start_ms, end_ms)`
- `AudioClip.remove_silence(threshold_db=-48.0, min_silence_ms=80.0, padding_ms=10.0)`
- `AudioClip.reverse()`
- `AudioClip.to_mono()`
- `AudioClip.to_stereo()`
- `AudioClip.remove_dc_offset()`
- `AudioClip.pan(position)`

Starter examples:

```python
edited = (
    clip.fade_in(180.0)
    .trim(start_ms=50.0, end_ms=12_000.0)
    .remove_silence(threshold_db=-50.0, min_silence_ms=90.0, padding_ms=15.0)
    .remove_dc_offset()
    .normalize(headroom_db=1.0)
)
```

## Utility and Analysis Methods

- `AudioClip.resample(target_sample_rate)`
- `AudioClip.dither(bit_depth=16)`
- `AudioClip.bit_depth_conversion(bit_depth=16, dither=True)`
- `AudioClip.loudness_normalization(target_lufs=-16.0)`
- `AudioClip.peak_detection()`
- `AudioClip.rms_analysis()`
- `AudioClip.loudness_lufs()`
- `AudioClip.envelope_follower(attack_ms=10.0, release_ms=80.0)`
- `AudioClip.multiband_compressor(low_cut_hz=180.0, high_cut_hz=3200.0, low_threshold_db=-24.0, mid_threshold_db=-18.0, high_threshold_db=-20.0, ratio=2.6)`

Starter examples:

```python
prepared = (
    clip.resample(48_000)
    .loudness_normalization(target_lufs=-16.0)
    .bit_depth_conversion(bit_depth=16)
)

print(prepared.peak_detection())
print(prepared.rms_analysis())
print(prepared.loudness_lufs())
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

Starter examples:

```python
processed = clip.apply("vocal_enhance")
lazy_render = clip.apply("cinematic", lazy=True).normalize(headroom_db=1.0).render()
```

## Catalog check helpers

```python
from voxis import effect_names, preset_names

print(len(effect_names()))
print(effect_names())
print(preset_names())
```
