# 🎧 Lista de Efeitos de Áudio - 108 recursos de áudio no checklist

Resumo atual:
- `95` efeitos/processadores encadeáveis via `effect_names()`
- `108` recursos no checklist total, contando clip ops, efeitos, utilitários e análises

## 🔊 1. Efeitos básicos (obrigatórios)
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

Status atual na Voxis:
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

## 🎛️ 2. Dinâmica
- [x] Compressor
- [x] Limiter
- [x] Expander
- [x] Noise Gate
- [x] Multiband Compressor
- [x] De-esser
- [x] Transient shaper
- [x] Upward compression
- [x] Downward compression

Status atual na Voxis:
- `compressor()`
- `limiter()`
- `expander()`
- `noise_gate()`
- `deesser()`
- `downward_compression()`
- `upward_compression()`
- `transient_shaper()`
- `multiband_compressor()` ou `AudioClip.multiband_compressor()`

---

## 🎚️ 3. Equalização / Filtros
- [x] Equalizer (paramétrico)
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

Status atual na Voxis:
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

## 🌊 4. Modulação
- [x] Chorus
- [x] Flanger
- [x] Phaser
- [x] Tremolo
- [x] Vibrato
- [x] Auto-pan
- [x] Rotary speaker (Leslie)
- [x] Ring modulation
- [x] Frequency shifter

Status atual na Voxis:
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

## 🏔️ 5. Espaço / Ambiência
- [x] Reverb (plate, hall, room)
- [x] Convolution reverb (IR)
- [x] Early reflections
- [x] Delay
- [x] Echo
- [x] Ping-pong delay
- [x] Multi-tap delay
- [x] Slapback delay

Status atual na Voxis:
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

## 🔥 6. Distortion / Saturação
- [x] Distortion
- [x] Overdrive
- [x] Fuzz
- [x] Bitcrusher
- [x] Waveshaper
- [x] Tube saturation
- [x] Tape saturation
- [x] Soft clipping
- [x] Hard clipping

Status atual na Voxis:
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

## 🎼 7. Pitch / Tempo
- [x] Pitch shift  
  - Obs: muda o tom do áudio sem alterar a duração (tempo)
- [x] Time stretch  
  - Obs: altera a duração (tempo) do áudio sem mudar o tom
- [x] Time compression
- [x] Auto-tune (pitch correction)
- [x] Harmonizer
- [x] Octaver
- [x] Formant shifting

Status atual na Voxis:
- `pitch_shift()`
- `time_stretch()`
- `time_compression()`
- `auto_tune()`
- `harmonizer()`
- `octaver()`
- `formant_shifting()`

---

## 🤖 8. Efeitos modernos / IA-like
- [x] Noise reduction
- [x] Voice isolation
- [x] Source separation
- [x] De-reverb
- [x] De-echo
- [x] Spectral repair
- [x] AI enhancer
- [x] Speech enhancement

Status atual na Voxis:
- `noise_reduction()`
- `voice_isolation()`
- `source_separation()`
- `de_reverb()`
- `de_echo()`
- `spectral_repair()`
- `ai_enhancer()`
- `speech_enhancement()`

---

## 📡 9. Efeitos criativos / especiais
- [x] Glitch effect
- [x] Stutter
- [x] Tape stop
- [x] Reverse reverb
- [x] Granular synthesis
- [x] Time slicing
- [x] Random pitch mod
- [x] Vinyl effect
- [x] Radio effect
- [x] Telefone effect
- [x] 8-bit / retro sound
- [x] Slow motion extreme
- [x] Robot voice
- [x] Alien voice

Status atual na Voxis:
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

## 🧪 10. Processamento espectral
- [x] FFT filter
- [x] Spectral gating
- [x] Spectral blur
- [x] Spectral freeze
- [x] Spectral morphing
- [x] Phase vocoder
- [x] Harmonic/percussive separation
- [x] Spectral delay

Status atual na Voxis:
- `fft_filter()`
- `spectral_gating()`
- `spectral_blur()`
- `spectral_freeze()`
- `spectral_morphing()`
- `phase_vocoder()`
- `harmonic_percussive_separation()`
- `spectral_delay()`

---

## 🔊 11. Stereo / espacial avançado
- [x] Stereo widening
- [x] Mid/Side processing
- [x] Stereo imager
- [x] Binaural effect
- [x] 3D audio positioning
- [x] HRTF simulation

Status atual na Voxis:
- `stereo_widening()`
- `mid_side_processing()`
- `stereo_imager()`
- `binaural_effect()`
- `spatial_positioning()`
- `hrtf_simulation()`

---

## 🧱 12. Utilitários avançados
- [x] Resample
- [x] Dither
- [x] Bit depth conversion
- [x] Loudness normalization (LUFS)
- [x] Peak detection
- [x] RMS analysis
- [x] Envelope follower

Status atual na Voxis:
- `AudioClip.resample()`
- `AudioClip.dither()`
- `AudioClip.bit_depth_conversion()`
- `AudioClip.loudness_normalization()`
- `AudioClip.peak_detection()`
- `AudioClip.rms_analysis()`
- `AudioClip.loudness_lufs()`
- `AudioClip.envelope_follower()`
