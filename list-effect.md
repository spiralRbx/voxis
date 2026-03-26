# Audio Effects Checklist - 108 audio features in the checklist

Current summary:
- `95` chainable effects/processors via `effect_names()`
- `108` resources in the full checklist, including clip ops, effects, utilities, and analysis helpers
- `[x]` means the effect already exists in the offline Voxis workflow
- `[y]` means the effect already has a realtime path configured in Voxis

## 1. Basic effects (required)
- [x] [y] Gain (volume)
- [x] [y] Normalize
- [x] [y] Fade in
- [x] [y] Fade out
- [x] [y] Crossfade
- [x] [y] Trim
- [x] [y] Cut
- [x] [y] Silence removal
- [x] [y] Reverse
- [x] [y] Stereo balance (pan)
- [x] [y] Mono ↔ Stereo
- [x] [y] DC offset removal

Current status in Voxis:
- `AudioClip.gain()`
- `AudioClip.normalize()`
- `AudioClip.fade_in()`
- `AudioClip.fade_out()`
- `AudioClip.crossfade()`
- `AudioClip.trim()`
- `AudioClip.cut()`
- `AudioClip.remove_silence()`
- `AudioClip.reverse()`
- `AudioClip.pan()`
- `AudioClip.to_mono()`
- `AudioClip.to_stereo()`
- `AudioClip.remove_dc_offset()`

Realtime starter status:
- `web-test/real-time/` now includes the full checklist-aligned basic layer with realtime paths for `gain`, `normalize`, `fade in`, `fade out`, `crossfade`, `trim`, `cut`, `silence removal`, `reverse`, `pan`, `mono ↔ stereo`, and `DC offset removal`.
- The browser demo keeps these as streaming-safe realtime previews, while the offline `AudioClip` API keeps the destructive full-buffer versions.

---

## 2. Dynamics
- [x] [y] Compressor
- [x] [y] Limiter
- [x] [y] Expander
- [x] [y] Noise Gate
- [x] [y] Multiband Compressor
- [x] [y] De-esser
- [x] [y] Transient shaper
- [x] [y] Upward compression
- [x] [y] Downward compression

Current status in Voxis:
- `compressor()`
- `limiter()`
- `expander()`
- `noise_gate()`
- `deesser()`
- `downward_compression()`
- `upward_compression()`
- `transient_shaper()`
- `multiband_compressor()` or `AudioClip.multiband_compressor()`

Realtime status in Voxis:
- `web-test/real-time/` now routes `compressor`, `downward compression`, `upward compression`, `limiter`, `expander`, `noise gate`, `de-esser`, `transient shaper`, and `multiband compressor` through a WASM module built from the native C++ DSP.

---

## 3. EQ / Filters
- [x] [y] Parametric equalizer
- [x] [y] Graphic EQ
- [x] [y] Low-pass filter
- [x] [y] High-pass filter
- [x] [y] Band-pass filter
- [x] [y] Notch filter
- [x] [y] Low shelf
- [x] [y] High shelf
- [x] [y] Resonant filter
- [x] [y] Dynamic EQ
- [x] [y] Formant filter

Current status in Voxis:
- `parametric_eq()`
- `graphic_eq()`
- `lowpass()`
- `highpass()`
- `bandpass()`
- `notch()`
- `low_shelf()`
- `high_shelf()`
- `resonant_filter()`
- `dynamic_eq()`
- `formant_filter()`

Realtime status in Voxis:
- `web-test/real-time/` now routes `lowpass`, `highpass`, `bandpass`, `notch`, `peak_eq`, `low_shelf`, `high_shelf`, `resonant_filter`, `parametric_eq`, `graphic_eq`, `dynamic_eq`, and `formant_filter` through the native Voxis WASM chain.

---

## 4. Modulation
- [x] [y] Chorus
- [x] [y] Flanger
- [x] [y] Phaser
- [x] [y] Tremolo
- [x] [y] Vibrato
- [x] [y] Auto-pan
- [x] [y] Rotary speaker (Leslie)
- [x] [y] Ring modulation
- [x] [y] Frequency shifter

Current status in Voxis:
- `chorus()`
- `flanger()`
- `phaser()`
- `tremolo()`
- `vibrato()`
- `auto_pan()`
- `rotary_speaker()`
- `ring_modulation()`
- `frequency_shifter()`

Realtime status in Voxis:
- `web-test/real-time/` now routes `chorus`, `flanger`, `phaser`, `tremolo`, `vibrato`, `auto_pan`, `rotary_speaker`, `ring_modulation`, and `frequency_shifter` through the modulation `AudioWorklet` path.

---

## 5. Space / Ambience
- [x] [y] Reverb (plate, hall, room)
- [x] [y] Convolution reverb (IR)
- [x] [y] Early reflections
- [x] [y] Delay
- [x] [y] Echo
- [x] [y] Ping-pong delay
- [x] [y] Multi-tap delay
- [x] [y] Slapback delay

Current status in Voxis:
- `delay()`
- `feedback_delay()`
- `echo()`
- `ping_pong_delay()`
- `multi_tap_delay()`
- `slapback()`
- `early_reflections()`
- `room_reverb()`
- `hall_reverb()`
- `plate_reverb()`
- `convolution_reverb()`

Realtime status in Voxis:
- `web-test/real-time/` now routes `delay`, `echo`, `ping_pong_delay`, `multi_tap_delay`, `slapback`, `early_reflections`, `room_reverb`, `hall_reverb`, `plate_reverb`, and `convolution_reverb` through the realtime space / ambience rack.

---

## 6. Distortion / Saturation
- [x] [y] Distortion
- [x] [y] Overdrive
- [x] [y] Fuzz
- [x] [y] Bitcrusher
- [x] [y] Waveshaper
- [x] [y] Tube saturation
- [x] [y] Tape saturation
- [x] [y] Soft clipping
- [x] [y] Hard clipping

Current status in Voxis:
- `distortion()`
- `overdrive()`
- `fuzz()`
- `bitcrusher()`
- `waveshaper()`
- `tube_saturation()`
- `tape_saturation()`
- `soft_clipping()`
- `hard_clipping()`

Realtime status in Voxis:
- `web-test/real-time/` now routes `distortion`, `overdrive`, `fuzz`, `bitcrusher`, `waveshaper`, `tube_saturation`, `tape_saturation`, `soft_clipping`, and `hard_clipping` through the realtime color/time `AudioWorklet` path.

---

## 7. Pitch / Time
- [x] [y] Pitch shift  
  - Note: changes pitch without changing duration (time)
- [x] [y] Time stretch  
  - Note: changes duration (time) without changing pitch
- [x] [y] Time compression
- [x] [y] Auto-tune (pitch correction)
- [x] [y] Harmonizer
- [x] [y] Octaver
- [x] [y] Formant shifting

Current status in Voxis:
- `pitch_shift()`
- `time_stretch()`
- `time_compression()`
- `auto_tune()`
- `harmonizer()`
- `octaver()`
- `formant_shifting()`

Realtime status in Voxis:
- `web-test/real-time/` now routes `pitch_shift`, `auto_tune`, `harmonizer`, `octaver`, and `formant_shifting` through the realtime color/time `AudioWorklet` path.
- `time_stretch` and `time_compression` now use the browser file transport with pitch preservation enabled for realtime preview.

---

## 8. Modern / AI-like effects
- [x] [y] Noise reduction
- [x] [y] Voice isolation
- [x] [y] Source separation
- [x] [y] De-reverb
- [x] [y] De-echo
- [x] [y] Spectral repair
- [x] [y] AI enhancer
- [x] [y] Speech enhancement

Current status in Voxis:
- `noise_reduction()`
- `voice_isolation()`
- `source_separation()`
- `de_reverb()`
- `de_echo()`
- `spectral_repair()`
- `ai_enhancer()`
- `speech_enhancement()`

Realtime status in Voxis:
- `web-test/real-time/` now routes `noise_reduction`, `voice_isolation`, `source_separation`, `de_reverb`, `de_echo`, `spectral_repair`, `ai_enhancer`, and `speech_enhancement` through the realtime modern/creative `AudioWorklet` path.
- This browser stage is a low-latency realtime approximation layer for interactive preview; the offline API keeps the heavier full-buffer restoration workflows.

---

## 9. Creative / special effects
- [x] [y] Glitch effect
- [x] [y] Stutter
- [x] [y] Tape stop
- [x] [y] Reverse reverb
- [x] [y] Granular synthesis
- [x] [y] Time slicing
- [x] [y] Random pitch mod
- [x] [y] Vinyl effect
- [x] [y] Radio effect
- [x] [y] Telephone effect
- [x] [y] 8-bit / retro sound
- [x] [y] Slow motion extreme
- [x] [y] Robot voice
- [x] [y] Alien voice

Current status in Voxis:
- `glitch_effect()`
- `stutter()`
- `tape_stop()`
- `reverse_reverb()`
- `granular_synthesis()`
- `time_slicing()`
- `random_pitch_mod()`
- `vinyl_effect()`
- `radio_effect()`
- `telephone_effect()`
- `retro_8bit()`
- `slow_motion_extreme()`
- `robot_voice()`
- `alien_voice()`

Realtime status in Voxis:
- `web-test/real-time/` now routes `glitch_effect`, `stutter`, `tape_stop`, `reverse_reverb`, `granular_synthesis`, `time_slicing`, `random_pitch_mod`, `vinyl_effect`, `radio_effect`, `telephone_effect`, `retro_8bit`, `slow_motion_extreme`, `robot_voice`, and `alien_voice` through the realtime modern/creative `AudioWorklet` path.

---

## 10. Spectral processing
- [x] [y] FFT filter
- [x] [y] Spectral gating
- [x] [y] Spectral blur
- [x] [y] Spectral freeze
- [x] [y] Spectral morphing
- [x] [y] Phase vocoder
- [x] [y] Harmonic/percussive separation
- [x] [y] Spectral delay

Current status in Voxis:
- `fft_filter()`
- `spectral_gating()`
- `spectral_blur()`
- `spectral_freeze()`
- `spectral_morphing()`
- `phase_vocoder()`
- `harmonic_percussive_separation()`
- `spectral_delay()`

Realtime status in Voxis:
- `web-test/real-time/` now routes `fft_filter`, `spectral_gating`, `spectral_blur`, `spectral_freeze`, `spectral_morphing`, `phase_vocoder`, `harmonic_percussive_separation`, and `spectral_delay` through the realtime spectral/spatial `AudioWorklet` path.
- This browser stage keeps a low-latency approximation of the spectral workflows for interactive preview.

---

## 11. Advanced stereo / spatial
- [x] [y] Stereo widening
- [x] [y] Mid/Side processing
- [x] [y] Stereo imager
- [x] [y] Binaural effect
- [x] [y] 3D audio positioning
- [x] [y] HRTF simulation

Current status in Voxis:
- `stereo_widening()`
- `mid_side_processing()`
- `stereo_imager()`
- `binaural_effect()`
- `spatial_positioning()`
- `hrtf_simulation()`

Realtime status in Voxis:
- `web-test/real-time/` now routes `stereo_widening`, `mid_side_processing`, `stereo_imager`, `binaural_effect`, `spatial_positioning`, and `hrtf_simulation` through the realtime spectral/spatial `AudioWorklet` path.

---

## 12. Advanced utilities
- [x] Resample
- [x] Dither
- [x] Bit depth conversion
- [x] Loudness normalization (LUFS)
- [x] Peak detection
- [x] RMS analysis
- [x] Envelope follower

Current status in Voxis:
- `AudioClip.resample()`
- `AudioClip.dither()`
- `AudioClip.bit_depth_conversion()`
- `AudioClip.loudness_normalization()`
- `AudioClip.peak_detection()`
- `AudioClip.rms_analysis()`
- `AudioClip.loudness_lufs()`
- `AudioClip.envelope_follower()`
