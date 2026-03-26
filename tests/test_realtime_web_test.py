from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path


def load_realtime_app():
    module_path = Path(__file__).resolve().parents[1] / "web-test" / "real-time" / "app.py"
    spec = importlib.util.spec_from_file_location("voxis_web_test_realtime", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load web-test/real-time/app.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.app


def test_realtime_web_test_index_renders_controls() -> None:
    app = load_realtime_app()
    client = app.test_client()

    response = client.get("/")

    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Voxis Realtime Starter" in text
    assert "AudioWorklet" in text
    assert "EQ + Dynamics in WASM" in text
    assert "Use microphone" in text
    assert "Realtime effect chain" in text
    assert "Parametric equalizer" in text
    assert "Graphic EQ" in text
    assert "Dynamic EQ" in text
    assert "Gain (volume)" in text
    assert "Silence removal" in text
    assert "Multiband Compressor" in text
    assert "Noise Gate" in text
    assert "Formant filter" in text
    assert "Modulation" in text
    assert "Space / Ambience" in text
    assert "Chorus" in text
    assert "Flanger" in text
    assert "Frequency shifter" in text
    assert "Rotary speaker (Leslie)" in text
    assert "Reverb (plate, hall, room)" in text
    assert "Convolution reverb (IR)" in text
    assert "Early reflections" in text
    assert "Ping-pong delay" in text
    assert "Multi-tap delay" in text
    assert "Slapback delay" in text
    assert "Distortion / Saturation" in text
    assert "Pitch / Time" in text
    assert "Distortion" in text
    assert "Overdrive" in text
    assert "Fuzz" in text
    assert "Bitcrusher" in text
    assert "Waveshaper" in text
    assert "Tube saturation" in text
    assert "Tape saturation" in text
    assert "Soft clipping" in text
    assert "Hard clipping" in text
    assert "Pitch shift" in text
    assert "Time stretch" in text
    assert "Time compression" in text
    assert "Auto-tune (pitch correction)" in text
    assert "Harmonizer" in text
    assert "Octaver" in text
    assert "Formant shifting" in text
    assert "Modern / AI-like effects" in text
    assert "Creative / special effects" in text
    assert "Noise reduction" in text
    assert "Voice isolation" in text
    assert "Source separation" in text
    assert "De-reverb" in text
    assert "De-echo" in text
    assert "Spectral repair" in text
    assert "AI enhancer" in text
    assert "Speech enhancement" in text
    assert "Glitch effect" in text
    assert "Stutter" in text
    assert "Tape stop" in text
    assert "Reverse reverb" in text
    assert "Granular synthesis" in text
    assert "Time slicing" in text
    assert "Random pitch mod" in text
    assert "Vinyl effect" in text
    assert "Radio effect" in text
    assert "Telephone effect" in text
    assert "8-bit / retro sound" in text
    assert "Slow motion extreme" in text
    assert "Robot voice" in text
    assert "Alien voice" in text
    assert "Spectral processing" in text
    assert "Advanced stereo / spatial" in text
    assert "FFT filter" in text
    assert "Spectral gating" in text
    assert "Spectral blur" in text
    assert "Spectral freeze" in text
    assert "Spectral morphing" in text
    assert "Phase vocoder" in text
    assert "Harmonic/percussive separation" in text
    assert "Spectral delay" in text
    assert "Stereo widening" in text
    assert "Mid/Side processing" in text
    assert "Stereo imager" in text
    assert "Binaural effect" in text
    assert "3D audio positioning" in text
    assert "HRTF simulation" in text


def test_realtime_web_test_serves_worklet_script() -> None:
    app = load_realtime_app()
    client = app.test_client()

    response = client.get("/static/api/voxis-basic-processor.js")

    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'registerProcessor("voxis-basic-processor"' in text


def test_realtime_web_test_serves_realtime_assets() -> None:
    app = load_realtime_app()
    client = app.test_client()

    color_time_response = client.get("/static/api/voxis-color-time-processor.js")
    modern_creative_response = client.get("/static/api/voxis-modern-creative-processor.js")
    spectral_spatial_response = client.get("/static/api/voxis-spectral-spatial-processor.js")
    modulation_response = client.get("/static/api/voxis-modulation-processor.js")
    processor_response = client.get("/static/api/voxis-dynamics-processor.js")
    space_response = client.get("/static/api/realtime-space.js")
    realtime_api_response = client.get("/static/api/voxis-realtime.js")
    realtime_controls_response = client.get("/static/api/voxis-realtime-controls.js")
    realtime_effects_response = client.get("/static/api/voxis-realtime-effects.js")
    realtime_player_response = client.get("/static/api/voxis-realtime-player.js")
    wasm_response = client.get("/static/api/voxis-realtime-dynamics.wasm")
    app_js_response = client.get("/static/app.js")

    color_time_text = color_time_response.get_data(as_text=True)
    modern_creative_text = modern_creative_response.get_data(as_text=True)
    spectral_spatial_text = spectral_spatial_response.get_data(as_text=True)
    modulation_text = modulation_response.get_data(as_text=True)
    processor_text = processor_response.get_data(as_text=True)
    space_text = space_response.get_data(as_text=True)
    realtime_api_text = realtime_api_response.get_data(as_text=True)
    realtime_controls_text = realtime_controls_response.get_data(as_text=True)
    realtime_effects_text = realtime_effects_response.get_data(as_text=True)
    realtime_player_text = realtime_player_response.get_data(as_text=True)
    app_js_text = app_js_response.get_data(as_text=True)
    assert color_time_response.status_code == 200
    assert 'registerProcessor("voxis-color-time-processor"' in color_time_text
    assert "autoTune" in color_time_text
    assert "bitcrusher" in color_time_text
    assert "formantShifting" in color_time_text
    assert modern_creative_response.status_code == 200
    assert 'registerProcessor("voxis-modern-creative-processor"' in modern_creative_text
    assert "noiseReduction" in modern_creative_text
    assert "sourceSeparation" in modern_creative_text
    assert "glitchEffect" in modern_creative_text
    assert "alienVoice" in modern_creative_text
    assert spectral_spatial_response.status_code == 200
    assert 'registerProcessor("voxis-spectral-spatial-processor"' in spectral_spatial_text
    assert "fftFilter" in spectral_spatial_text
    assert "spectralDelay" in spectral_spatial_text
    assert "stereoWidening" in spectral_spatial_text
    assert "hrtfSimulation" in spectral_spatial_text
    assert modulation_response.status_code == 200
    assert 'registerProcessor("voxis-modulation-processor"' in modulation_text
    assert "frequencyShifter" in modulation_text
    assert "rotarySpeaker" in modulation_text
    assert processor_response.status_code == 200
    assert 'registerProcessor("voxis-dynamics-processor"' in processor_text
    assert "instantiateStreaming(fetch" not in processor_text
    assert "emscripten_notify_memory_growth" in processor_text
    assert "createDynamicsImports()" in processor_text
    assert "__wasm_call_ctors" in processor_text
    assert "voxis_rt_get_limits_json_ptr" in processor_text
    assert "voxis_rt_get_warning_ptr" in processor_text
    assert 'typeof TextDecoder === "function"' in processor_text
    assert "String.fromCharCode" in processor_text
    assert "scheduleDynamicsConfigUpdate" in app_js_text
    assert "scheduleBasicConfigUpdate" in app_js_text
    assert "scheduleColorTimeConfigUpdate" in app_js_text
    assert "scheduleModernCreativeConfigUpdate" in app_js_text
    assert "scheduleSpectralSpatialConfigUpdate" in app_js_text
    assert "scheduleModulationConfigUpdate" in app_js_text
    assert "scheduleSpaceConfigUpdate" in app_js_text
    assert "window.setTimeout" in app_js_text
    assert "graphicEq" in app_js_text
    assert "multibandCompressor" in app_js_text
    assert "createSpaceRack" in app_js_text
    assert "syncPitchTimeTransport" in app_js_text
    assert 'voxis-color-time-processor.js' in app_js_text
    assert 'voxis-modulation-processor.js' in app_js_text
    assert "buildBasicConfig" in app_js_text
    assert "buildColorTimeConfig" in app_js_text
    assert "buildModernCreativeConfig" in app_js_text
    assert "buildSpectralSpatialConfig" in app_js_text
    assert "buildModulationConfig" in app_js_text
    assert "buildSpaceConfig" in app_js_text
    assert "parametricEq" in processor_text
    assert "voxis_rt_set_graphic_eq" in processor_text
    assert "voxis_rt_set_dynamic_eq" in processor_text
    assert "voxis_rt_set_multiband_compressor" in processor_text
    assert "processorOptions" in app_js_text
    assert "/static/api/voxis-realtime-dynamics.wasm" in app_js_text
    assert 'voxis-modern-creative-processor.js' in app_js_text
    assert 'voxis-spectral-spatial-processor.js' in app_js_text
    assert space_response.status_code == 200
    assert "export function createSpaceRack" in space_text
    assert "buildSyntheticReverbImpulse" in space_text
    assert "loadConvolutionFile" in space_text
    assert realtime_api_response.status_code == 200
    assert "buildEffectState" in realtime_api_text
    assert "buildEffectStateWithWarnings" in realtime_api_text
    assert "createVoxisRealtimePlayer" in realtime_api_text
    assert "createLockedControl" in realtime_api_text
    assert "effects" in realtime_api_text
    assert "./voxis-realtime-effects.js" in realtime_api_text
    assert "./voxis-realtime-player.js" in realtime_api_text
    assert "./voxis-realtime-controls.js" in realtime_api_text
    assert realtime_controls_response.status_code == 200
    assert "export function createLockedControl" in realtime_controls_text
    assert realtime_effects_response.status_code == 200
    assert "export const effects = Object.fromEntries" in realtime_effects_text
    assert "export function buildEffectState" in realtime_effects_text
    assert "export function buildEffectStateWithWarnings" in realtime_effects_text
    assert "output_level" in realtime_effects_text
    assert "gain" in realtime_effects_text
    assert "compressor" in realtime_effects_text
    assert "highpass" in realtime_effects_text
    assert "chorus" in realtime_effects_text
    assert "delay" in realtime_effects_text
    assert "distortion" in realtime_effects_text
    assert "pitch_shift" in realtime_effects_text
    assert "noise_reduction" in realtime_effects_text
    assert "glitch_effect" in realtime_effects_text
    assert "fft_filter" in realtime_effects_text
    assert "hrtf_simulation" in realtime_effects_text
    assert realtime_player_response.status_code == 200
    assert "export class VoxisRealtimePlayer" in realtime_player_text
    assert "createVoxisRealtimePlayer" in realtime_player_text
    assert "onWarning(handler)" in realtime_player_text
    assert "getNativeDynamicsLimits()" in realtime_player_text
    assert "loadCrossfadePartnerFile" in realtime_player_text
    assert "loadConvolutionIrFile" in realtime_player_text
    assert "useMicrophone" in realtime_player_text
    assert "setEffects(effectList)" in realtime_player_text
    assert "voxis-basic-processor.js" in realtime_player_text
    assert "voxis-spectral-spatial-processor.js" in realtime_player_text
    assert "voxis-realtime-dynamics.wasm" in realtime_player_text
    assert wasm_response.status_code == 200
    assert len(wasm_response.get_data()) > 0

def test_realtime_templates_do_not_duplicate_modal_control_ids() -> None:
    template_root = Path(__file__).resolve().parents[1] / "web-test" / "real-time" / "templates"
    combined = "".join(
        (template_root / name).read_text(encoding="utf-8")
        for name in (
            "index.html",
            "_basic_modals.html",
            "_eq_modals.html",
            "_dynamics_modals.html",
            "_modulation_modals.html",
            "_space_modals.html",
            "_distortion_modals.html",
            "_pitch_time_modals.html",
            "_modern_modals.html",
            "_creative_modals.html",
            "_spectral_modals.html",
            "_stereo_spatial_modals.html",
            "_extras_modals.html",
        )
    )

    ids = re.findall(r'id="([^"]+)"', combined)
    duplicates = sorted({value for value in ids if ids.count(value) > 1})
    assert duplicates == []
