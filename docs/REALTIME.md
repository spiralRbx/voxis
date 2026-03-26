# Realtime Audio Starter

The browser realtime slice for Voxis lives in `web-test/real-time/`.

This version now covers checklist sections `1. Basic effects`, `2. Dynamics`, `3. EQ / Filters`, `4. Modulation`, `5. Space / Ambience`, `6. Distortion / Saturation`, `7. Pitch / Time`, `8. Modern / AI-like effects`, `9. Creative / special effects`, `10. Spectral processing`, and `11. Advanced stereo / spatial` in the browser demo. For the clip-editing items from section 1, the realtime layer uses streaming-safe counterparts so they can stay inside a low-latency graph.

## What ships now

- Browser-side realtime graph using Web Audio API
- `AudioWorklet` node for custom sample-by-sample DSP
- Native Voxis EQ, filters, and dynamics compiled to WASM with Emscripten
- Dedicated realtime color/time `AudioWorklet`
- Dedicated realtime modern/creative `AudioWorklet`
- Dedicated realtime spectral/spatial `AudioWorklet`
- Dedicated realtime modulation `AudioWorklet`
- Dedicated realtime space / ambience rack using browser audio nodes and generated impulse buffers
- Standard HTML `<audio>` element as the file transport
- Microphone input through `getUserMedia()`
- Realtime-safe starter effects:
  - Gain (volume)
  - Normalize
  - Fade in
  - Fade out
  - Crossfade
  - Trim
  - Cut
  - Silence removal
  - Reverse
  - Stereo balance (pan)
  - Mono ↔ Stereo
  - DC offset removal
  - High-pass filter
  - Low-pass filter
  - Band-pass filter
  - Notch filter
  - Low shelf
  - High shelf
  - Resonant filter
  - Parametric equalizer
  - Graphic EQ
  - Dynamic EQ
  - Formant filter
  - Compressor
  - Downward compression
  - Upward compression
  - Limiter
  - Expander
  - Noise Gate
  - Multiband Compressor
  - De-esser
  - Transient shaper
  - Drive / soft saturation
  - Chorus
  - Flanger
  - Phaser
  - Tremolo
  - Vibrato
  - Auto-pan
  - Rotary speaker (Leslie)
  - Ring modulation
  - Frequency shifter
  - Reverb (plate, hall, room)
  - Convolution reverb (IR)
  - Early reflections
  - Delay
  - Echo
  - Ping-pong delay
  - Multi-tap delay
  - Slapback delay
  - Distortion
  - Overdrive
  - Fuzz
  - Bitcrusher
  - Waveshaper
  - Tube saturation
  - Tape saturation
  - Soft clipping
  - Hard clipping
  - Pitch shift
  - Time stretch
  - Time compression
  - Auto-tune (pitch correction)
  - Harmonizer
  - Octaver
  - Formant shifting
  - Noise reduction
  - Voice isolation
  - Source separation
  - De-reverb
  - De-echo
  - Spectral repair
  - AI enhancer
  - Speech enhancement
  - Glitch effect
  - Stutter
  - Tape stop
  - Reverse reverb
  - Granular synthesis
  - Time slicing
  - Random pitch mod
  - Vinyl effect
  - Radio effect
  - Telephone effect
  - 8-bit / retro sound
  - Slow motion extreme
  - Robot voice
  - Alien voice
  - FFT filter
  - Spectral gating
  - Spectral blur
  - Spectral freeze
  - Spectral morphing
  - Phase vocoder
  - Harmonic/percussive separation
  - Spectral delay
  - Stereo widening
  - Mid/Side processing
  - Stereo imager
  - Binaural effect
  - 3D audio positioning
  - HRTF simulation
- Ready-made presets for fast preview
- CSS variables for quick styling changes
- Reusable browser module starter in the root `api/voxis-realtime.js`, split into a player module plus effect builders for embedding in other projects

## Realtime notes

The realtime graph and the offline `AudioClip` workflow both exist, but they are not identical:

- In the browser graph, section 1 clip-editing operations are implemented as timeline-aware or streaming-safe previews.
- In the offline API, the same names keep the destructive full-buffer behavior.
- `Crossfade` in the browser demo crossfades the main file into an optional partner file loaded inside the popup control.
- `Silence removal` in realtime behaves as a continuous streaming remover instead of rewriting the file on disk.
- `Time stretch` and `Time compression` use the browser file transport with pitch preservation enabled, so those two controls apply to file preview and are bypassed for live microphone monitoring.
- The section 8 browser effects are realtime-friendly approximations for interactive monitoring; the heavier offline restoration flow still lives in the Python/C++ path.
- The section 10 browser effects are also realtime-friendly approximations for interactive spectral preview instead of full offline FFT batch processing.

## Architecture

Current realtime path:

```text
Audio file or microphone
        ->
Web Audio API source node
        ->
AudioWorklet custom DSP
  (gain, normalize, fades, trim, cut,
   silence removal, reverse, mono mix,
   drive, DC blocker)
        ->
AudioWorklet color/time stage
  (distortion, overdrive, fuzz, bitcrusher,
   waveshaper, tube saturation, tape saturation,
   soft clipping, hard clipping, pitch shift,
   auto-tune, harmonizer, octaver,
   formant shifting)
        ->
AudioWorklet modern/creative stage
  (noise reduction, voice isolation,
   source separation, de-reverb, de-echo,
   spectral repair, AI enhancer,
   speech enhancement, glitch effect,
   stutter, tape stop, reverse reverb,
   granular synthesis, time slicing,
   random pitch mod, vinyl effect,
   radio effect, telephone effect,
   retro 8-bit, slow motion extreme,
   robot voice, alien voice)
        ->
AudioWorklet spectral/spatial stage
  (FFT filter, spectral gating,
   spectral blur, spectral freeze,
   spectral morphing, phase vocoder,
   harmonic/percussive separation,
   spectral delay, stereo widening,
   mid/side processing, stereo imager,
   binaural effect, 3D positioning,
   HRTF simulation)
        ->
Voxis WASM EQ/filter/dynamics bridge
  (high-pass, low-pass, band-pass, notch,
   peak EQ, shelves, resonant filter,
   parametric EQ, graphic EQ, dynamic EQ,
   formant filter, compressor, downward,
   upward, limiter, expander, gate,
   multiband compressor, de-esser,
   transient shaper)
        ->
AudioWorklet modulation stage
  (chorus, flanger, phaser, tremolo,
   vibrato, auto-pan, rotary speaker,
   ring modulation, frequency shifter)
        ->
space / ambience rack
  (delay, echo, ping-pong delay,
   multi-tap delay, slapback,
   early reflections, room/hall/plate reverb,
   convolution reverb)
        ->
stereo panner
        ->
destination
```

This is already buffer-based realtime processing. The basic, color/time, modern/creative, spectral/spatial, and modulation stages run as JavaScript DSP in the audio thread, the EQ/filter/dynamics stage runs through a native Voxis WASM module, and the space / ambience stage uses browser-native realtime nodes plus cached generated buffers.

## Running the demo

```bash
python web-test/real-time/app.py
```

Then open:

```text
http://127.0.0.1:5101
```

For the separate API editor site with live range controls, run:

```bash
python web-test/api-test/app.py
```

Then open:

```text
http://127.0.0.1:5102
```

For a reusable browser-side entry point:

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

That starter wrapper now exposes effect builders for sections `1` through `11`, creates a standard `<audio>` element automatically when you pass a container, resolves its processor and WASM files relative to the module location, and can drive file input, microphone input, a crossfade partner, and convolution IR loading without going through the demo controller.

## Building a minified browser API

```bash
npm install
npm run build:api
```

The build reads the source modules from `api/`, minifies the JavaScript layer file-by-file, copies `voxis-realtime-dynamics.wasm` unchanged, and writes the result to `dist-api/` with a `build-manifest.json` summary.

Use that output when you want a smaller production distribution without changing the shape of the public API. The output is intentionally minified, not obfuscated, so it stays easier to audit and does not add extra realtime overhead in the audio thread.

## Safety and warnings

- `createLockedControl(...)` and per-effect `limits` are app-side guardrails. They help keep the UI inside the range you intended, even if the HTML input is edited in DevTools.
- Those guardrails are still not a replacement for product-level security. In the browser, the embedding project remains responsible for the final policy because the user still controls their own JavaScript runtime.
- The shipped WASM module is now the native source of truth for realtime guardrail metadata.
- EQ/filter/dynamics values are validated directly in the native DSP bridge and emit English warnings when the WASM layer clamps a parameter.
- The remaining realtime stages still process audio in JavaScript, but their public min/max/choice limits are now read from the WASM metadata before config reaches those processors.
- The browser API exposes those warnings through `player.onWarning((warning) => { ... })`.
- The browser API exposes the full native metadata through `player.getNativeRealtimeLimits()`.
- `player.getNativeDynamicsLimits()` is kept as a compatibility alias for the same metadata object.

Example:

```js
import { createLockedControl, createVoxisRealtimePlayer, effects }
  from "./api/voxis-realtime.js";

const player = await createVoxisRealtimePlayer({ container: "#player-host" });

player.onWarning((warning) => {
  console.warn("[Voxis warning]", warning.message);
});

console.log(player.getNativeRealtimeLimits());

const delayTimeControl = createLockedControl({
  input: "#delay-ms-range",
  min: 0.0,
  max: 1200.0,
  step: 1.0,
});

player.setEffects([
  effects.delay({
    delayMs: delayTimeControl.read(),
    limits: { delayMs: { min: 0.0, max: 1200.0 } },
  }),
]);
```

The important split is:

- EQ/filter/dynamics use native DSP validation and native DSP processing
- the other sections still process audio in JavaScript, but now read their public guardrail metadata from the shipped WASM module

## Usage flow

1. Click `Start audio engine`.
2. Choose one source:
   - upload a local file
   - enable the microphone
3. Use the standard audio element to play/pause file preview.
4. Move the effect controls while audio is playing.
5. Watch the output meter and latency info.

## Latency notes

- The demo creates `AudioContext({ latencyHint: "interactive" })`.
- The browser audio thread runs in small render quanta, typically `128` frames.
- Delay, modulation, ambience, and the dynamics chain are safe in this graph because they keep internal state and process incrementally.
- The browser transport-backed time-stretch path keeps pitch stable for file preview without moving that specific feature into the audio-thread DSP worklets.
- The browser demo now uses timeline-aware or streaming-safe versions of the section 1 clip operations.

## File roles

- `web-test/real-time/static/app.js`
  - UI controller and graph wiring
  - reads sliders, toggles, file input, and microphone input
  - posts config updates into the realtime processors
- `web-test/real-time/static/voxis-basic-processor.js`
  - JavaScript audio-thread DSP for the basic layer
  - handles gain, normalize, fades, trim, cut, silence removal, reverse, mono mix, drive, and DC blocker
- `web-test/real-time/static/voxis-color-time-processor.js`
  - JavaScript audio-thread DSP for sections 6 and most of 7
  - handles distortion, overdrive, fuzz, bitcrusher, waveshaper, tube saturation, tape saturation, soft clipping, hard clipping, pitch shift, auto-tune, harmonizer, octaver, and formant shifting
- `web-test/real-time/static/voxis-modern-creative-processor.js`
  - JavaScript audio-thread DSP for sections 8 and 9
  - handles the realtime-friendly browser versions of noise reduction, voice isolation, source separation, de-reverb, de-echo, spectral repair, AI enhancer, speech enhancement, glitch effect, stutter, tape stop, reverse reverb, granular synthesis, time slicing, random pitch mod, vinyl effect, radio effect, telephone effect, retro 8-bit, slow motion extreme, robot voice, and alien voice
- `web-test/real-time/static/voxis-spectral-spatial-processor.js`
  - JavaScript audio-thread DSP for sections 10 and 11
  - handles the realtime-friendly browser versions of FFT filter, spectral gating, spectral blur, spectral freeze, spectral morphing, phase vocoder, harmonic/percussive separation, spectral delay, stereo widening, mid/side processing, stereo imager, binaural effect, spatial positioning, and HRTF simulation
- `web-test/real-time/static/voxis-dynamics-processor.js`
  - AudioWorklet bridge for the WASM EQ/filter/dynamics engine
  - copies render quanta into the WASM buffer and runs the native chain
- `web-test/real-time/static/voxis-modulation-processor.js`
  - AudioWorklet DSP for the modulation block
  - handles chorus, flanger, phaser, tremolo, vibrato, auto-pan, rotary speaker, ring modulation, and frequency shifter
- `web-test/real-time/static/realtime-space.js`
  - browser-side realtime rack for section 5 space / ambience effects
  - handles delay, echo, ping-pong, multi-tap, slapback, early reflections, synthetic room / hall / plate reverb, and convolution IR loading
- `api/voxis-realtime.js`
  - reusable browser-side starter API
  - public entry point that re-exports the reusable player and effect-builder helpers
- `api/voxis-realtime-player.js`
  - reusable browser-side player/graph wrapper
  - creates a standard `<audio>` element, boots the realtime graph, and handles file loading, microphone input, crossfade partner loading, and convolution IR loading
- `api/voxis-realtime-effects.js`
  - reusable effect-builder catalog for checklist sections 1 through 11
  - translates `effects.*` calls into the stage configs consumed by the realtime player
- `api/voxis-realtime-dynamics.wasm`
  - compiled native Voxis realtime EQ/filter/dynamics module
  - built from `cpp/src/realtime_dynamics_wasm.cpp`, including multiband compression
- `web-test/api-test/static/editor.js`
  - standalone editor/controller for testing the reusable browser API with live ranges
- `web-test/api-test/templates/index.html`
  - separate browser page for testing the importable Voxis realtime API without the main demo UI

## Why this split

The split keeps the browser UI layer separate from the DSP layer:

1. `app.js` is not the Voxis DSP library. It is the demo controller.
2. The processor files are the realtime DSP entry points inside the browser audio thread and are part of the current browser-side Voxis realtime layer.
3. The WASM file is the native Voxis part that gives you shared realtime DSP logic closer to the offline engine, but it is not enough by itself without the JavaScript worklet bridge.
4. `api/voxis-realtime.js` is the public browser entry point for the library-style API, while `app.js` stays focused on the demo UI.

That keeps the next step clear:

1. Keep the same Web Audio routing and UI.
2. Move more effects from JavaScript or browser-native nodes into additional WASM modules when the native engine grows.
3. Reuse the same parameter model when the wider C++ engine is ported further.

## Files

- `web-test/real-time/app.py`
- `web-test/real-time/templates/index.html`
- `web-test/real-time/static/styles.css`
- `web-test/real-time/static/app.js`
- `web-test/real-time/static/voxis-basic-processor.js`
- `web-test/real-time/static/voxis-color-time-processor.js`
- `web-test/real-time/static/voxis-modern-creative-processor.js`
- `web-test/real-time/static/voxis-spectral-spatial-processor.js`
- `web-test/real-time/static/voxis-dynamics-processor.js`
- `web-test/real-time/static/voxis-modulation-processor.js`
- `web-test/real-time/static/realtime-space.js`
- `api/voxis-realtime.js`
- `api/voxis-realtime-player.js`
- `api/voxis-realtime-effects.js`
- `web-test/api-test/app.py`
- `web-test/api-test/templates/index.html`
- `web-test/api-test/static/styles.css`
- `web-test/api-test/static/editor.js`
- `api/voxis-realtime-dynamics.wasm`
- `cpp/src/realtime_dynamics_wasm.cpp`
