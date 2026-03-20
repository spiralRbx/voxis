# Audio Effects Checklist - 108 audio features in the checklist

Current summary:
- `95` chainable effects/processors via `effect_names()`
- `108` resources in the full checklist, including clip ops, effects, utilities, and analysis helpers

## 1. Basic effects (required)
- [x] Gain (volume)
- [x] Normalize
- [x] Fade in
- [x] Fade out
- [x] Crossfade
- [x] Trim
- [x] Cut
- [x] Silence removal
- [x] Reverse
- [x] Stereo balance (pan)
- [x] Mono ↔ Stereo
- [x] DC offset removal

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

---

## 2. Dynamics
- [x] Compressor
- [x] Limiter
- [x] Expander
- [x] Noise Gate
- [x] Multiband Compressor
- [x] De-esser
- [x] Transient shaper
- [x] Upward compression
- [x] Downward compression

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

---

## 3. EQ / Filters
- [x] Parametric equalizer
- [x] Graphic EQ
- [x] Low-pass filter
- [x] High-pass filter
- [x] Band-pass filter
- [x] Notch filter
- [x] Low shelf
- [x] High shelf
- [x] Resonant filter
- [x] Dynamic EQ
- [x] Formant filter

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

---

## 4. Modulation
- [x] Chorus
- [x] Flanger
- [x] Phaser
- [x] Tremolo
- [x] Vibrato
- [x] Auto-pan
- [x] Rotary speaker (Leslie)
- [x] Ring modulation
- [x] Frequency shifter

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

---

## 5. Space / Ambience
- [x] Reverb (plate, hall, room)
- [x] Convolution reverb (IR)
- [x] Early reflections
- [x] Delay
- [x] Echo
- [x] Ping-pong delay
- [x] Multi-tap delay
- [x] Slapback delay

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

---

## 6. Distortion / Saturation
- [x] Distortion
- [x] Overdrive
- [x] Fuzz
- [x] Bitcrusher
- [x] Waveshaper
- [x] Tube saturation
- [x] Tape saturation
- [x] Soft clipping
- [x] Hard clipping

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

---

## 7. Pitch / Time
- [x] Pitch shift  
  - Note: changes pitch without changing duration (time)
- [x] Time stretch  
  - Note: changes duration (time) without changing pitch
- [x] Time compression
- [x] Auto-tune (pitch correction)
- [x] Harmonizer
- [x] Octaver
- [x] Formant shifting

Current status in Voxis:
- `pitch_shift()`
- `time_stretch()`
- `time_compression()`
- `auto_tune()`
- `harmonizer()`
- `octaver()`
- `formant_shifting()`

---

## 8. Modern / AI-like effects
- [x] Noise reduction
- [x] Voice isolation
- [x] Source separation
- [x] De-reverb
- [x] De-echo
- [x] Spectral repair
- [x] AI enhancer
- [x] Speech enhancement

Current status in Voxis:
- `noise_reduction()`
- `voice_isolation()`
- `source_separation()`
- `de_reverb()`
- `de_echo()`
- `spectral_repair()`
- `ai_enhancer()`
- `speech_enhancement()`

---

## 9. Creative / special effects
- [x] Glitch effect
- [x] Stutter
- [x] Tape stop
- [x] Reverse reverb
- [x] Granular synthesis
- [x] Time slicing
- [x] Random pitch mod
- [x] Vinyl effect
- [x] Radio effect
- [x] Telephone effect
- [x] 8-bit / retro sound
- [x] Slow motion extreme
- [x] Robot voice
- [x] Alien voice

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

---

## 10. Spectral processing
- [x] FFT filter
- [x] Spectral gating
- [x] Spectral blur
- [x] Spectral freeze
- [x] Spectral morphing
- [x] Phase vocoder
- [x] Harmonic/percussive separation
- [x] Spectral delay

Current status in Voxis:
- `fft_filter()`
- `spectral_gating()`
- `spectral_blur()`
- `spectral_freeze()`
- `spectral_morphing()`
- `phase_vocoder()`
- `harmonic_percussive_separation()`
- `spectral_delay()`

---

## 11. Advanced stereo / spatial
- [x] Stereo widening
- [x] Mid/Side processing
- [x] Stereo imager
- [x] Binaural effect
- [x] 3D audio positioning
- [x] HRTF simulation

Current status in Voxis:
- `stereo_widening()`
- `mid_side_processing()`
- `stereo_imager()`
- `binaural_effect()`
- `spatial_positioning()`
- `hrtf_simulation()`

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

