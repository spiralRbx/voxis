from __future__ import annotations

from pathlib import Path


def test_root_docs_site_files_exist_and_focus_on_public_docs() -> None:
    root = Path(__file__).resolve().parents[1]
    index_html = (root / "index.html").read_text(encoding="utf-8")
    site_css = (root / "site.css").read_text(encoding="utf-8")
    site_js = (root / "site.js").read_text(encoding="utf-8")

    assert "Voxis Documentation" in index_html
    assert "Python Guide" in index_html
    assert "Realtime Guide" in index_html
    assert "Documentation Browser" in index_html
    assert "./api/voxis-realtime.js" in index_html
    assert "docs/EFFECT_REFERENCE.md" in site_js
    assert "docs/REALTIME.md" in site_js
    assert "publish.md" not in site_js
    assert "renderMarkdown" in site_js
    assert "--accent:" in site_css


def test_public_python_and_realtime_guides_cover_tutorial_flow() -> None:
    root = Path(__file__).resolve().parents[1]
    python_html = (root / "python.html").read_text(encoding="utf-8")
    realtime_html = (root / "realtime.html").read_text(encoding="utf-8")
    realtime_example_html = (root / "realtime-example.html").read_text(encoding="utf-8")
    realtime_example_js = (root / "realtime-example.js").read_text(encoding="utf-8")

    assert "Learn the Voxis Python API from the beginning." in python_html
    assert "from voxis import effects" in python_html
    assert 'AudioClip.from_file("voice.wav")' in python_html
    assert "print(clip.duration_seconds)" in python_html
    assert "clip.duration_ms" in python_html
    assert "pip install -e .[dev]" not in python_html
    assert "print(len(effect_names()))" in python_html
    assert "What an effect call does" in python_html
    assert 'edited.export("voice_edited.wav")' in python_html

    assert "Build realtime audio tools with Voxis in the browser." in realtime_html
    assert "Voxis does <strong>not</strong> auto-detect HTML IDs by magic." in realtime_html
    assert "const elements = {" in realtime_html
    assert 'fileInput: $("#editor-file-input")' in realtime_html
    assert "createVoxisRealtimePlayer" in realtime_html
    assert "player.setEffects([" in realtime_html
    assert "player.loadFile(file)" in realtime_html
    assert "player.loadConvolutionIrFile(file, true)" in realtime_html
    assert "https://spiralRbx.github.io/voxis/api/voxis-realtime.js" in realtime_html
    assert "createLockedControl" in realtime_html
    assert "getNativeRealtimeLimits()" in realtime_html
    assert "limits: { min: 0.0, max: 2.0 }" in realtime_html
    assert "realtime-example.html" in realtime_html

    assert "Try a minimal Voxis browser page and inspect its code." in realtime_example_html
    assert "View code" in realtime_example_html
    assert "Loading JavaScript source..." in realtime_example_html
    assert 'from "./api/voxis-realtime.js"' in realtime_example_js
    assert "createLockedControl" in realtime_example_js
    assert "createVoxisRealtimePlayer" in realtime_example_js
    assert "limits: { min: 0.0, max: 2.0 }" in realtime_example_js
    assert "elements.codePanel.hidden" in realtime_example_js
    assert "loadOwnSource" in realtime_example_js


def test_root_api_folder_contains_realtime_public_assets() -> None:
    root = Path(__file__).resolve().parents[1]
    api_root = root / "api"

    assert (api_root / "voxis-realtime.js").exists()
    assert (api_root / "voxis-realtime-effects.js").exists()
    assert (api_root / "voxis-realtime-player.js").exists()
    assert (api_root / "voxis-realtime-controls.js").exists()
    assert (api_root / "voxis-basic-processor.js").exists()
    assert (api_root / "voxis-dynamics-processor.js").exists()
    assert (api_root / "voxis-realtime-dynamics.wasm").exists()

    api_entry = (api_root / "voxis-realtime.js").read_text(encoding="utf-8")
    api_effects = (api_root / "voxis-realtime-effects.js").read_text(encoding="utf-8")
    api_player = (api_root / "voxis-realtime-player.js").read_text(encoding="utf-8")
    api_controls = (api_root / "voxis-realtime-controls.js").read_text(encoding="utf-8")
    assert 'export { effects, buildEffectState, buildEffectStateWithWarnings }' in api_entry
    assert 'export { createLockedControl }' in api_entry
    assert "output_level" in api_effects
    assert "noise_reduction" in api_effects
    assert "createVoxisRealtimePlayer" in api_player
    assert "loadCrossfadePartnerFile" in api_player
    assert "loadConvolutionIrFile" in api_player
    assert "useMicrophone" in api_player
    assert "export function createLockedControl" in api_controls


def test_private_release_notes_are_not_in_public_docs_tree() -> None:
    root = Path(__file__).resolve().parents[1]
    assert not (root / "publish.md").exists()
    assert not (root / "web-test" / "real-time" / "build-wasm.ps1").exists()
    assert not (root / "PKG-INFO").exists()


def test_pyproject_points_to_public_docs_page_and_runtime_dependencies() -> None:
    root = Path(__file__).resolve().parents[1]
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")

    assert 'Documentation = "https://spiralRbx.github.io/voxis/page/voxis/"' in pyproject
    assert '"numpy>=2.0"' in pyproject
    assert '"imageio-ffmpeg>=0.6.0"' in pyproject
