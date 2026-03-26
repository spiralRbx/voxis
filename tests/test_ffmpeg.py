from __future__ import annotations

import os
import subprocess
import sys
import textwrap
import wave
from pathlib import Path

import numpy as np

from voxis import AudioClip, FORMAT_CAPABILITIES, prepare_export_settings

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _write_test_wav(path: Path, sample_rate: int, *, duration_seconds: float = 0.1) -> int:
    frame_count = int(round(sample_rate * duration_seconds))
    timeline = np.arange(frame_count, dtype=np.float32) / sample_rate
    mono = 0.2 * np.sin(2.0 * np.pi * 220.0 * timeline)
    samples = np.column_stack([mono, mono])
    pcm = np.clip(samples * 32767.0, -32768.0, 32767.0).astype(np.int16)

    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(pcm.tobytes())

    return frame_count


def _run_python_script(script_path: Path, *, cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    pythonpath = [str(PROJECT_ROOT / "src")]
    if env.get("PYTHONPATH"):
        pythonpath.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(pythonpath)

    return subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def test_ffmpeg_roundtrip_wav(tmp_path) -> None:
    sample_rate = 44_100
    timeline = np.arange(sample_rate, dtype=np.float32) / sample_rate
    mono = 0.2 * np.sin(2.0 * np.pi * 220.0 * timeline)
    samples = np.column_stack([mono, mono]).astype(np.float32)

    original = AudioClip.from_array(samples, sample_rate)
    output_path = tmp_path / "roundtrip.wav"
    original.export(output_path)

    recovered = AudioClip.from_file(output_path)

    assert recovered.sample_rate == sample_rate
    assert recovered.channels == 2
    assert recovered.frames == original.frames
    assert np.max(np.abs(recovered.samples - original.samples)) < 5e-4


def test_lazy_export_supports_format_and_resample(tmp_path) -> None:
    sample_rate = 48_000
    timeline = np.arange(sample_rate, dtype=np.float32) / sample_rate
    mono = 0.15 * np.sin(2.0 * np.pi * 330.0 * timeline)
    samples = np.column_stack([mono, mono]).astype(np.float32)

    clip = AudioClip.from_array(samples, sample_rate)
    output_path = tmp_path / "resampled.wav"

    clip.apply("cinematic", lazy=True).export(
        output_path,
        format="wav",
        sample_rate=22_050,
        channels=1,
    )

    recovered = AudioClip.from_file(output_path)

    assert recovered.sample_rate == 22_050
    assert recovered.channels == 1


def test_export_validation_ignores_bitrate_for_wav() -> None:
    settings = prepare_export_settings("demo.wav", format="wav", bitrate="320k")
    assert settings.format == "wav"
    assert settings.bitrate is None
    assert settings.warnings
    assert FORMAT_CAPABILITIES["wav"]["bitrate"] is False


def test_ogg_export_coerces_unsupported_sample_rate(tmp_path) -> None:
    sample_rate = 44_100
    timeline = np.arange(sample_rate, dtype=np.float32) / sample_rate
    mono = 0.2 * np.sin(2.0 * np.pi * 180.0 * timeline)
    samples = np.column_stack([mono, mono]).astype(np.float32)

    clip = AudioClip.from_array(samples, sample_rate).resample(44_100)
    output_path = tmp_path / "resampled.ogg"

    clip.export(output_path, format="ogg", bitrate="192k")
    recovered = AudioClip.from_file(output_path)

    assert output_path.exists()
    assert recovered.sample_rate in set(FORMAT_CAPABILITIES["ogg"]["supported_sample_rates"])  # type: ignore[index]


def test_from_file_resolves_relative_to_caller_script_directory(tmp_path) -> None:
    script_dir = tmp_path / "example"
    script_dir.mkdir()
    frame_count = _write_test_wav(script_dir / "tone.wav", 22_050)
    script_path = script_dir / "load_tone.py"
    script_path.write_text(
        textwrap.dedent(
            """
            from voxis import AudioClip

            clip = AudioClip.from_file("tone.wav")
            print(f"{clip.sample_rate}:{clip.channels}:{clip.frames}")
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    result = _run_python_script(script_path, cwd=tmp_path)

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f"22050:2:{frame_count}"


def test_from_file_uses_caller_script_directory_even_when_cwd_has_same_name(tmp_path) -> None:
    _write_test_wav(tmp_path / "tone.wav", 16_000)

    script_dir = tmp_path / "example"
    script_dir.mkdir()
    _write_test_wav(script_dir / "tone.wav", 22_050)
    script_path = script_dir / "load_tone.py"
    script_path.write_text(
        textwrap.dedent(
            """
            from voxis import AudioClip

            clip = AudioClip.from_file("tone.wav")
            print(clip.sample_rate)
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    result = _run_python_script(script_path, cwd=tmp_path)

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "22050"


def test_from_file_supports_parent_navigation_from_caller_script_directory(tmp_path) -> None:
    frame_count = _write_test_wav(tmp_path / "tone.wav", 24_000)

    script_dir = tmp_path / "example"
    script_dir.mkdir()
    script_path = script_dir / "load_parent_tone.py"
    script_path.write_text(
        textwrap.dedent(
            """
            from voxis import AudioClip

            clip = AudioClip.from_file("../tone.wav")
            print(f"{clip.sample_rate}:{clip.channels}:{clip.frames}")
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    result = _run_python_script(script_path, cwd=tmp_path)

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f"24000:2:{frame_count}"


def test_export_resolves_relative_to_caller_script_directory(tmp_path) -> None:
    script_dir = tmp_path / "example"
    script_dir.mkdir()
    script_path = script_dir / "save_tone.py"
    script_path.write_text(
        textwrap.dedent(
            """
            import numpy as np
            from voxis import AudioClip

            clip = AudioClip.from_array(np.zeros((256, 2), dtype=np.float32), 16_000)
            output = clip.export("saved.wav")
            print(output)
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    result = _run_python_script(script_path, cwd=tmp_path)
    expected_output = (script_dir / "saved.wav").resolve()

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(expected_output)
    assert expected_output.exists()
    assert not (tmp_path / "saved.wav").exists()


def test_export_creates_relative_parent_directories_next_to_caller_script(tmp_path) -> None:
    script_dir = tmp_path / "example"
    script_dir.mkdir()
    script_path = script_dir / "save_nested_tone.py"
    script_path.write_text(
        textwrap.dedent(
            """
            import numpy as np
            from voxis import AudioClip

            clip = AudioClip.from_array(np.zeros((256, 2), dtype=np.float32), 16_000)
            output = clip.export("outputs/final.wav")
            print(output)
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    result = _run_python_script(script_path, cwd=tmp_path)
    expected_output = (script_dir / "outputs" / "final.wav").resolve()

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(expected_output)
    assert expected_output.exists()
