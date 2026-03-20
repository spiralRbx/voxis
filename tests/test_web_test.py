from __future__ import annotations

import importlib.util
import io
import sys
import wave
from pathlib import Path

import numpy as np


def load_web_app():
    module_path = Path(__file__).resolve().parents[1] / "web-test" / "app.py"
    spec = importlib.util.spec_from_file_location("voxis_web_test", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Nao foi possivel carregar web-test/app.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.app


def make_wav_bytes(*, sample_rate: int = 22_050, duration_seconds: float = 0.15) -> io.BytesIO:
    timeline = np.arange(int(sample_rate * duration_seconds), dtype=np.float32) / sample_rate
    mono = 0.15 * np.sin(2.0 * np.pi * 330.0 * timeline)
    stereo = np.column_stack([mono, mono]).astype(np.float32)
    pcm = np.clip(stereo * 32767.0, -32768, 32767).astype(np.int16)

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm.tobytes())
    buffer.seek(0)
    return buffer


def test_web_test_process_endpoint_returns_timing_debug() -> None:
    app = load_web_app()
    client = app.test_client()
    audio = make_wav_bytes()

    response = client.post(
        "/process",
        data={
            "audio": (audio, "demo.wav"),
            "format": "wav",
            "normalize_enabled": "yes",
            "normalize_headroom_db": "1.0",
            "gain": "on",
            "gain_db": "3.0",
            "upward_compression": "on",
            "upward_threshold_db": "-36.0",
            "upward_ratio": "2.0",
            "upward_max_gain_db": "10.0",
        },
        content_type="multipart/form-data",
    )

    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Tempos por etapa" in text
    assert "Render concluido" in text


def test_web_test_index_renders_effect_columns() -> None:
    app = load_web_app()
    client = app.test_client()

    response = client.get("/")

    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "effect-columns" in text
    assert "Voxis Audio Lab" in text


def test_web_test_handles_time_stretch_effect() -> None:
    app = load_web_app()
    client = app.test_client()
    audio = make_wav_bytes()

    response = client.post(
        "/process",
        data={
            "audio": (audio, "stretch.wav"),
            "format": "wav",
            "normalize_enabled": "yes",
            "time_stretch": "on",
            "time_stretch_rate": "0.85",
        },
        content_type="multipart/form-data",
    )

    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "time_stretch" in text
    assert "Render concluido" in text


def test_web_test_handles_creative_and_spectral_effects() -> None:
    app = load_web_app()
    client = app.test_client()
    audio = make_wav_bytes()

    response = client.post(
        "/process",
        data={
            "audio": (audio, "fx.wav"),
            "format": "wav",
            "normalize_enabled": "no",
            "glitch_effect": "on",
            "glitch_slice_ms": "60",
            "glitch_repeat": "0.18",
            "glitch_mix": "0.85",
            "spectral_delay": "on",
            "spectral_delay_ms": "120",
            "spectral_delay_feedback": "0.18",
            "spectral_delay_mix": "0.25",
        },
        content_type="multipart/form-data",
    )

    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "glitch_effect" in text
    assert "spectral_delay" in text
    assert "Render concluido" in text


def test_web_test_handles_spatial_and_analysis_blocks() -> None:
    app = load_web_app()
    client = app.test_client()
    audio = make_wav_bytes()

    response = client.post(
        "/process",
        data={
            "audio": (audio, "spatial.wav"),
            "format": "wav",
            "normalize_enabled": "no",
            "stereo_imager": "on",
            "stereo_imager_low": "0.9",
            "stereo_imager_high": "1.4",
            "loudness_normalization": "on",
            "utility_target_lufs": "-18.0",
            "analysis_envelope": "on",
            "analysis_attack_ms": "8.0",
            "analysis_release_ms": "60.0",
        },
        content_type="multipart/form-data",
    )

    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Metricas de entrada" in text
    assert "Metricas de saida" in text
    assert "stereo_imager" in text
