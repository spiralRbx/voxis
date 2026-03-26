from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


def load_api_test_app():
    module_path = Path(__file__).resolve().parents[1] / "web-test" / "api-test" / "app.py"
    spec = importlib.util.spec_from_file_location("voxis_api_test_web", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load web-test/api-test/app.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.app


def test_api_test_site_renders_range_editor() -> None:
    app = load_api_test_app()
    client = app.test_client()

    response = client.get("/")

    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Voxis Realtime API Editor" in text
    assert "./api/voxis-realtime.js" in text
    assert "Start engine" in text
    assert "Use microphone" in text
    assert "Gain" in text
    assert "Output level" in text
    assert "Enable compressor" in text
    assert "Enable hall reverb" in text
    assert "Enable FFT filter" in text
    assert "Enable spatial section" in text


def test_api_test_site_serves_api_assets() -> None:
    app = load_api_test_app()
    client = app.test_client()

    api_response = client.get("/api/voxis-realtime.js")
    controls_response = client.get("/api/voxis-realtime-controls.js")
    effects_response = client.get("/api/voxis-realtime-effects.js")
    player_response = client.get("/api/voxis-realtime-player.js")
    editor_response = client.get("/static/editor.js")
    wasm_response = client.get("/api/voxis-realtime-dynamics.wasm")

    api_text = api_response.get_data(as_text=True)
    controls_text = controls_response.get_data(as_text=True)
    effects_text = effects_response.get_data(as_text=True)
    player_text = player_response.get_data(as_text=True)
    editor_text = editor_response.get_data(as_text=True)
    assert api_response.status_code == 200
    assert "buildEffectState" in api_text
    assert "buildEffectStateWithWarnings" in api_text
    assert "createVoxisRealtimePlayer" in api_text
    assert "createLockedControl" in api_text
    assert "effects" in api_text
    assert "./voxis-realtime-effects.js" in api_text
    assert "./voxis-realtime-player.js" in api_text
    assert "./voxis-realtime-controls.js" in api_text
    assert controls_response.status_code == 200
    assert "createLockedControl" in controls_text
    assert effects_response.status_code == 200
    assert "output_level" in effects_text
    assert "noise_reduction" in effects_text
    assert "hrtf_simulation" in effects_text
    assert player_response.status_code == 200
    assert "VoxisRealtimePlayer" in player_text
    assert "import.meta.url" in player_text
    assert "voxis-realtime-dynamics.wasm" in player_text
    assert "onWarning(" in player_text
    assert "getNativeRealtimeLimits()" in player_text
    assert "getNativeDynamicsLimits()" in player_text
    assert "loadCrossfadePartnerFile" in player_text
    assert editor_response.status_code == 200
    assert 'import { createVoxisRealtimePlayer, effects } from "./api/voxis-realtime.js"' in editor_text
    assert "effects.output_level" in editor_text
    assert "effects.glitch_effect" in editor_text
    assert "effects.hrtf_simulation" in editor_text
    assert wasm_response.status_code == 200
    assert len(wasm_response.get_data()) > 0


def test_dist_api_public_exports_match_source_api() -> None:
    root = Path(__file__).resolve().parents[1]
    command = [
        "node",
        "-e",
        (
            "Promise.all(["
            "import('./api/voxis-realtime.js'),"
            "import('./dist-api/voxis-realtime.js'),"
            "import('./api/voxis-realtime-effects.js'),"
            "import('./dist-api/voxis-realtime-effects.js'),"
            "import('./api/voxis-realtime-player.js'),"
            "import('./dist-api/voxis-realtime-player.js'),"
            "import('./api/voxis-realtime-controls.js'),"
            "import('./dist-api/voxis-realtime-controls.js')"
            "]).then(([sourceEntry, distEntry, sourceEffects, distEffects, sourcePlayer, distPlayer, sourceControls, distControls]) => {"
            "const payload = {"
            "entry: [Object.keys(sourceEntry).sort(), Object.keys(distEntry).sort()],"
            "effects: [Object.keys(sourceEffects).sort(), Object.keys(distEffects).sort()],"
            "player: [Object.keys(sourcePlayer).sort(), Object.keys(distPlayer).sort()],"
            "controls: [Object.keys(sourceControls).sort(), Object.keys(distControls).sort()]"
            "};"
            "console.log(JSON.stringify(payload));"
            "}).catch((error) => { console.error(error); process.exit(1); });"
        ),
    ]

    result = subprocess.run(
        command,
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout.strip().splitlines()[0])

    assert payload["entry"][0] == payload["entry"][1]
    assert payload["effects"][0] == payload["effects"][1]
    assert payload["player"][0] == payload["player"][1]
    assert payload["controls"][0] == payload["controls"][1]
