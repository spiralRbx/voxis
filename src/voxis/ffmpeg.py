from __future__ import annotations

import inspect
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ._util import ensure_float32_frames
from .exceptions import FFmpegError

_AUDIO_LINE_RE = re.compile(r"Audio:\s*(?P<codec>[^,]+),\s*(?P<rate>\d+)\s*Hz,\s*(?P<layout>[^,]+)")

_LAYOUT_TO_CHANNELS = {
    "mono": 1,
    "stereo": 2,
    "2.1": 3,
    "3.0": 3,
    "3.1": 4,
    "quad": 4,
    "4.0": 4,
    "4.1": 5,
    "5.0": 5,
    "5.1": 6,
    "6.1": 7,
    "7.1": 8,
}

FORMAT_CAPABILITIES: dict[str, dict[str, object]] = {
    "wav": {"bitrate": False, "default_codec": "pcm_s16le", "mime": "audio/wav", "ffmpeg_format": "wav"},
    "mp3": {"bitrate": True, "default_codec": "libmp3lame", "mime": "audio/mpeg", "ffmpeg_format": "mp3"},
    "ogg": {"bitrate": True, "default_codec": "libopus", "mime": "audio/ogg", "ffmpeg_format": "ogg", "supported_sample_rates": (48_000, 24_000, 16_000, 12_000, 8_000)},
    "flac": {"bitrate": False, "default_codec": "flac", "mime": "audio/flac", "ffmpeg_format": "flac"},
    "aac": {"bitrate": True, "default_codec": "aac", "mime": "audio/aac", "ffmpeg_format": "adts"},
    "m4a": {"bitrate": True, "default_codec": "aac", "mime": "audio/mp4", "ffmpeg_format": "ipod"},
}


@dataclass(frozen=True, slots=True)
class AudioMetadata:
    sample_rate: int
    channels: int
    codec: str


@dataclass(frozen=True, slots=True)
class ExportSettings:
    output_path: Path
    format: str
    ffmpeg_format: str
    codec: str | None
    bitrate: str | None
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class InputPathResolution:
    original_path: str | Path
    resolved_path: str | Path
    is_local_file: bool
    used_caller_dir: bool
    caller_dir: Path | None


def resolve_ffmpeg() -> str:
    env_path = os.environ.get("VOXIS_FFMPEG") or os.environ.get("VOXERA_FFMPEG")
    if env_path:
        return env_path

    try:
        import imageio_ffmpeg
    except ImportError:
        imageio_ffmpeg = None

    if imageio_ffmpeg is not None:
        return imageio_ffmpeg.get_ffmpeg_exe()

    binary = shutil.which("ffmpeg")
    if binary:
        return binary

    raise FFmpegError(
        "FFmpeg was not found. Install imageio-ffmpeg or set VOXIS_FFMPEG."
    )


def _guess_channels(layout: str) -> int:
    lowered = layout.strip().lower()
    if lowered in _LAYOUT_TO_CHANNELS:
        return _LAYOUT_TO_CHANNELS[lowered]

    match = re.search(r"(\d+)\s*channels?", lowered)
    if match:
        return int(match.group(1))

    raise FFmpegError(f"Unable to parse channel layout from FFmpeg output: {layout!r}")


def infer_format(path: str | Path, format: str | None = None) -> str:
    if format:
        return format.lower().lstrip(".")
    suffix = Path(path).suffix.lower().lstrip(".")
    return suffix or "wav"


def _is_local_path(value: str | Path) -> bool:
    if isinstance(value, Path):
        return True
    text = str(value)
    if text == "-" or text.startswith("pipe:"):
        return False
    return "://" not in text


def _package_root() -> Path:
    return Path(__file__).resolve().parent


def _find_caller_dir() -> Path | None:
    frame = inspect.currentframe()
    if frame is None:
        return None

    package_root = _package_root()
    current = frame.f_back
    try:
        while current is not None:
            filename = current.f_code.co_filename
            if filename and not filename.startswith("<"):
                candidate = Path(filename).resolve()
                if not candidate.is_relative_to(package_root):
                    return candidate.parent
            current = current.f_back
    finally:
        del frame

    return None


def _resolve_input_path(path: str | Path) -> InputPathResolution:
    if not _is_local_path(path):
        return InputPathResolution(
            original_path=path,
            resolved_path=path,
            is_local_file=False,
            used_caller_dir=False,
            caller_dir=None,
        )

    local_path = Path(path).expanduser()
    caller_dir = _find_caller_dir() if not local_path.is_absolute() else None

    if local_path.is_absolute():
        return InputPathResolution(
            original_path=path,
            resolved_path=local_path,
            is_local_file=True,
            used_caller_dir=False,
            caller_dir=None,
        )

    base_dir = caller_dir if caller_dir is not None else Path.cwd()
    resolved_path = (base_dir / local_path).resolve()

    return InputPathResolution(
        original_path=path,
        resolved_path=resolved_path,
        is_local_file=True,
        used_caller_dir=caller_dir is not None,
        caller_dir=caller_dir,
    )


def _resolve_output_path(path: str | Path) -> str | Path:
    if not _is_local_path(path):
        return path

    local_path = Path(path).expanduser()
    if local_path.is_absolute():
        return local_path

    caller_dir = _find_caller_dir()
    base_dir = caller_dir if caller_dir is not None else Path.cwd()
    return (base_dir / local_path).resolve()


def _missing_input_error(resolution: InputPathResolution) -> FFmpegError:
    original = Path(resolution.original_path).expanduser()
    if original.is_absolute():
        return FFmpegError(f"Audio file not found: {original!s}.")

    if resolution.caller_dir is not None:
        checked = str((resolution.caller_dir / original).resolve())
        return FFmpegError(
            f"Audio file not found: {original!s}. Voxis resolved this relative path from the calling script directory: {checked}."
        )

    checked = str((Path.cwd() / original).resolve())
    return FFmpegError(
        f"Audio file not found: {original!s}. Voxis resolved this relative path from the current working directory: {checked}."
    )


def prepare_export_settings(
    path: str | Path,
    *,
    format: str | None = None,
    codec: str | None = None,
    bitrate: str | None = None,
) -> ExportSettings:
    resolved_output = _resolve_output_path(path)
    output_path = Path(resolved_output)
    resolved_format = infer_format(output_path, format)
    warnings: list[str] = []

    capabilities = FORMAT_CAPABILITIES.get(resolved_format)
    resolved_codec = codec
    resolved_bitrate = bitrate
    resolved_ffmpeg_format = resolved_format

    if capabilities is not None:
        if resolved_codec is None:
            resolved_codec = capabilities.get("default_codec")  # type: ignore[assignment]
        resolved_ffmpeg_format = str(capabilities.get("ffmpeg_format", resolved_format))
        if not bool(capabilities.get("bitrate", False)) and resolved_bitrate is not None:
            warnings.append(
                f"The {resolved_format.upper()} format does not use bitrate in this workflow. The value {resolved_bitrate!r} was ignored."
            )
            resolved_bitrate = None

    return ExportSettings(
        output_path=output_path,
        format=resolved_format,
        ffmpeg_format=resolved_ffmpeg_format,
        codec=resolved_codec,
        bitrate=resolved_bitrate,
        warnings=tuple(warnings),
    )


def probe_audio(path: str | Path) -> AudioMetadata:
    resolution = _resolve_input_path(path)
    resolved_path = resolution.resolved_path
    if resolution.is_local_file and isinstance(resolved_path, Path) and not resolved_path.exists():
        raise _missing_input_error(resolution)

    ffmpeg = resolve_ffmpeg()
    result = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", str(resolved_path)],
        capture_output=True,
        text=True,
        check=False,
    )

    combined = "\n".join(part for part in (result.stdout, result.stderr) if part)
    match = _AUDIO_LINE_RE.search(combined)
    if match is None:
        raise FFmpegError(f"Unable to probe audio stream metadata for {resolved_path!s}.")

    return AudioMetadata(
        sample_rate=int(match.group("rate")),
        channels=_guess_channels(match.group("layout")),
        codec=match.group("codec").strip(),
    )


def decode_audio(
    path: str | Path,
    *,
    sample_rate: int | None = None,
    channels: int | None = None,
) -> tuple[np.ndarray, AudioMetadata]:
    resolution = _resolve_input_path(path)
    input_path = resolution.resolved_path
    if resolution.is_local_file and isinstance(input_path, Path) and not input_path.exists():
        raise _missing_input_error(resolution)

    metadata = probe_audio(input_path)
    target_sample_rate = metadata.sample_rate if sample_rate is None else int(sample_rate)
    target_channels = metadata.channels if channels is None else int(channels)

    ffmpeg = resolve_ffmpeg()
    command = [
        ffmpeg,
        "-v",
        "error",
        "-i",
        str(input_path),
        "-f",
        "f32le",
        "-acodec",
        "pcm_f32le",
        "-ac",
        str(target_channels),
        "-ar",
        str(target_sample_rate),
        "pipe:1",
    ]

    result = subprocess.run(command, capture_output=True, check=False)
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace")
        raise FFmpegError(f"FFmpeg decode failed for {input_path!s}: {stderr}")

    buffer = np.frombuffer(result.stdout, dtype=np.float32)
    if buffer.size % target_channels != 0:
        raise FFmpegError("Decoded PCM buffer size is not aligned with the channel count.")

    frames = np.ascontiguousarray(buffer.reshape(-1, target_channels))
    return frames, AudioMetadata(
        sample_rate=target_sample_rate,
        channels=target_channels,
        codec=metadata.codec,
    )


def encode_audio(
    samples: np.ndarray,
    sample_rate: int,
    path: str | Path,
    *,
    codec: str | None = None,
    bitrate: str | None = None,
    format: str | None = None,
    output_sample_rate: int | None = None,
    output_channels: int | None = None,
    overwrite: bool = True,
) -> Path:
    frames = ensure_float32_frames(samples)
    ffmpeg = resolve_ffmpeg()
    source_sample_rate = int(sample_rate)
    target_sample_rate = source_sample_rate if output_sample_rate is None else int(output_sample_rate)
    target_channels = int(frames.shape[1]) if output_channels is None else int(output_channels)
    settings = prepare_export_settings(path, format=format, codec=codec, bitrate=bitrate)
    capabilities = FORMAT_CAPABILITIES.get(settings.format, {})
    supported_rates = capabilities.get("supported_sample_rates")
    if supported_rates:
        supported_values = tuple(int(value) for value in supported_rates)  # type: ignore[arg-type]
        if target_sample_rate not in supported_values:
            target_sample_rate = min(supported_values, key=lambda value: abs(value - target_sample_rate))

    settings.output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        ffmpeg,
        "-v",
        "error",
    ]
    if overwrite:
        command.append("-y")

    command.extend(
        [
            "-f",
            "f32le",
            "-ar",
            str(source_sample_rate),
            "-ac",
            str(frames.shape[1]),
            "-i",
            "pipe:0",
        ]
    )

    if settings.codec:
        command.extend(["-c:a", settings.codec])
    if settings.bitrate:
        command.extend(["-b:a", settings.bitrate])
    if settings.ffmpeg_format:
        command.extend(["-f", settings.ffmpeg_format])
    if target_channels != frames.shape[1]:
        command.extend(["-ac", str(target_channels)])
    if target_sample_rate != source_sample_rate:
        command.extend(["-ar", str(target_sample_rate)])

    command.append(str(settings.output_path))

    result = subprocess.run(
        command,
        input=frames.tobytes(),
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace")
        raise FFmpegError(f"FFmpeg encode failed for {settings.output_path!s}: {stderr}")

    return settings.output_path
