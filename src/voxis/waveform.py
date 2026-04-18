from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal, TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from .audio import AudioClip


WaveformStyle = Literal["peaks", "line", "filled", "mirror", "bars"]

_VALID_STYLES = ("peaks", "line", "filled", "mirror", "bars")


def _coerce_samples(source: "np.ndarray | AudioClip", channel: int | None) -> tuple[np.ndarray, int]:
    samples = getattr(source, "samples", None)
    sample_rate = getattr(source, "sample_rate", None)

    if samples is None:
        samples = np.asarray(source, dtype=np.float32)
        sample_rate = sample_rate or 44100

    samples = np.asarray(samples, dtype=np.float32)
    if samples.ndim == 1:
        mono = samples
    elif samples.ndim == 2:
        if channel is None:
            mono = np.mean(samples, axis=1, dtype=np.float32)
        else:
            c = max(0, min(samples.shape[1] - 1, int(channel)))
            mono = np.ascontiguousarray(samples[:, c], dtype=np.float32)
    else:
        raise ValueError(f"Unsupported sample shape: {samples.shape}")

    if sample_rate is None:
        raise ValueError("sample_rate could not be determined; pass an AudioClip or raw samples with a rate.")
    return mono, int(sample_rate)


def _compute_peaks(mono: np.ndarray, pixels: int) -> tuple[np.ndarray, np.ndarray]:
    pixels = max(1, int(pixels))
    n = mono.shape[0]
    if n == 0:
        return np.zeros(pixels, np.float32), np.zeros(pixels, np.float32)

    edges = np.linspace(0, n, num=pixels + 1, dtype=np.int64)
    mins = np.empty(pixels, dtype=np.float32)
    maxs = np.empty(pixels, dtype=np.float32)

    starts = edges[:-1]
    ends = edges[1:]

    for i in range(pixels):
        s, e = int(starts[i]), int(ends[i])
        if e <= s:
            mins[i] = mins[i - 1] if i else 0.0
            maxs[i] = maxs[i - 1] if i else 0.0
            continue
        chunk = mono[s:e]
        mins[i] = chunk.min()
        maxs[i] = chunk.max()

    return mins, maxs


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    c = color.lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    if len(c) != 6:
        raise ValueError(f"Invalid hex color: {color!r}")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def _hex_to_rgba(color: str, alpha: float) -> str:
    r, g, b = _hex_to_rgb(color)
    return f"rgba({r},{g},{b},{alpha:.3f})"


@dataclass
class Waveform:
    source: object
    style: WaveformStyle = "peaks"
    channel: int | None = None
    color: str = "#3b82f6"
    background: str | None = None

    def __post_init__(self) -> None:
        if self.style not in _VALID_STYLES:
            raise ValueError(f"style must be one of {_VALID_STYLES}, got {self.style!r}")
        self._mono, self._sample_rate = _coerce_samples(self.source, self.channel)
        self._cache_pixels = -1
        self._cache_mins = None
        self._cache_maxs = None

    def _peaks(self, pixels: int) -> tuple[np.ndarray, np.ndarray]:
        if pixels == self._cache_pixels and self._cache_mins is not None:
            return self._cache_mins, self._cache_maxs  # type: ignore[return-value]
        mins, maxs = _compute_peaks(self._mono, pixels)
        self._cache_pixels = pixels
        self._cache_mins = mins
        self._cache_maxs = maxs
        return mins, maxs

    @property
    def duration_seconds(self) -> float:
        return self._mono.shape[0] / float(self._sample_rate)

    def to_peaks(self, pixels: int = 800) -> tuple[np.ndarray, np.ndarray]:
        return tuple(arr.copy() for arr in self._peaks(pixels))  # type: ignore[return-value]

    def to_json(self, pixels: int = 800) -> dict:
        mins, maxs = self._peaks(pixels)
        return {
            "mins": mins.tolist(),
            "maxs": maxs.tolist(),
            "pixels": int(pixels),
            "sampleRate": self._sample_rate,
            "durationSeconds": self.duration_seconds,
            "style": self.style,
            "color": self.color,
        }

    def to_json_string(self, pixels: int = 800, **dumps_kwargs) -> str:
        return json.dumps(self.to_json(pixels), **dumps_kwargs)

    def to_svg(
        self,
        *,
        width: int = 800,
        height: int = 120,
        color: str | None = None,
        background: str | None = None,
        pixels: int | None = None,
    ) -> str:
        color = color or self.color
        bg = background if background is not None else self.background
        px = int(pixels or width)
        mins, maxs = self._peaks(px)

        parts: list[str] = []
        parts.append(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'width="{width}" height="{height}" preserveAspectRatio="none">'
        )
        if bg:
            parts.append(f'<rect width="{width}" height="{height}" fill="{bg}"/>')

        mid = height / 2.0
        xs = np.linspace(0, width, num=px, dtype=np.float32)

        if self.style == "peaks":
            d_parts = []
            for i in range(px):
                x = float(xs[i])
                y1 = mid + float(mins[i]) * mid
                y2 = mid + float(maxs[i]) * mid
                d_parts.append(f"M{x:.2f},{y1:.2f}L{x:.2f},{y2:.2f}")
            parts.append(
                f'<path d="{"".join(d_parts)}" stroke="{color}" stroke-width="1" fill="none"/>'
            )

        elif self.style == "line":
            points = " ".join(f"{float(xs[i]):.2f},{mid + float(maxs[i]) * mid:.2f}" for i in range(px))
            parts.append(
                f'<polyline points="{points}" stroke="{color}" stroke-width="1.5" fill="none"/>'
            )

        elif self.style == "filled":
            top = " ".join(f"{float(xs[i]):.2f},{mid + float(mins[i]) * mid:.2f}" for i in range(px))
            bot = " ".join(
                f"{float(xs[i]):.2f},{mid + float(maxs[i]) * mid:.2f}"
                for i in range(px - 1, -1, -1)
            )
            parts.append(
                f'<polygon points="{top} {bot}" fill="{_hex_to_rgba(color, 0.55)}" stroke="{color}" stroke-width="1"/>'
            )

        elif self.style == "mirror":
            d_parts = []
            for i in range(px):
                x = float(xs[i])
                amp = max(abs(float(mins[i])), abs(float(maxs[i])))
                d_parts.append(f"M{x:.2f},{mid - amp * mid:.2f}L{x:.2f},{mid + amp * mid:.2f}")
            parts.append(
                f'<path d="{"".join(d_parts)}" stroke="{color}" stroke-width="1.5" fill="none"/>'
            )

        elif self.style == "bars":
            bar_count = max(1, min(px, width // 3))
            mins_bar, maxs_bar = self._peaks(bar_count)
            step = width / bar_count
            bar_w = max(1, step * 0.7)
            for i in range(bar_count):
                x = i * step + (step - bar_w) / 2
                amp = max(abs(float(mins_bar[i])), abs(float(maxs_bar[i])))
                h = max(1.0, amp * height)
                y = mid - h / 2
                parts.append(
                    f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_w:.2f}" height="{h:.2f}" fill="{color}"/>'
                )

        parts.append("</svg>")
        return "".join(parts)

    def save_svg(self, path: str | Path, **kwargs) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(self.to_svg(**kwargs), encoding="utf-8")
        return out

    def to_png(
        self,
        *,
        width: int = 800,
        height: int = 120,
        color: str | None = None,
        background: str | None = None,
        pixels: int | None = None,
    ) -> bytes:
        try:
            from PIL import Image, ImageDraw
        except ImportError as exc:
            raise RuntimeError(
                "PNG export requires the 'pillow' package. Install with `pip install pillow`."
            ) from exc

        color_rgb = _hex_to_rgb(color or self.color)
        bg = background if background is not None else self.background
        bg_rgba = _hex_to_rgb(bg) + (255,) if bg else (0, 0, 0, 0)

        img = Image.new("RGBA", (width, height), bg_rgba)
        draw = ImageDraw.Draw(img)

        px = int(pixels or width)
        mins, maxs = self._peaks(px)
        mid = height / 2.0
        xs = np.linspace(0, width - 1, num=px, dtype=np.float32)

        if self.style == "peaks":
            for i in range(px):
                x = int(xs[i])
                y1 = int(mid + float(mins[i]) * mid)
                y2 = int(mid + float(maxs[i]) * mid)
                draw.line([(x, y1), (x, y2)], fill=color_rgb + (255,), width=1)

        elif self.style == "line":
            pts = [(int(xs[i]), int(mid + float(maxs[i]) * mid)) for i in range(px)]
            draw.line(pts, fill=color_rgb + (255,), width=2)

        elif self.style == "filled":
            top = [(int(xs[i]), int(mid + float(mins[i]) * mid)) for i in range(px)]
            bot = [(int(xs[i]), int(mid + float(maxs[i]) * mid)) for i in range(px - 1, -1, -1)]
            draw.polygon(top + bot, fill=color_rgb + (140,), outline=color_rgb + (255,))

        elif self.style == "mirror":
            for i in range(px):
                x = int(xs[i])
                amp = max(abs(float(mins[i])), abs(float(maxs[i])))
                y1 = int(mid - amp * mid)
                y2 = int(mid + amp * mid)
                draw.line([(x, y1), (x, y2)], fill=color_rgb + (255,), width=2)

        elif self.style == "bars":
            bar_count = max(1, min(px, width // 3))
            mins_bar, maxs_bar = self._peaks(bar_count)
            step = width / bar_count
            bar_w = max(1, int(step * 0.7))
            for i in range(bar_count):
                x = int(i * step + (step - bar_w) / 2)
                amp = max(abs(float(mins_bar[i])), abs(float(maxs_bar[i])))
                h = max(1, int(amp * height))
                y = int(mid - h / 2)
                draw.rectangle([(x, y), (x + bar_w, y + h)], fill=color_rgb + (255,))

        from io import BytesIO
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def save_png(self, path: str | Path, **kwargs) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(self.to_png(**kwargs))
        return out

    def to_ascii(
        self,
        *,
        width: int = 80,
        height: int = 12,
        charset: str | Iterable[str] = " .-=o#@",
    ) -> str:
        chars = "".join(charset)
        if not chars:
            raise ValueError("charset must be non-empty")

        mins, maxs = self._peaks(width)
        amp = np.maximum(np.abs(mins), np.abs(maxs))
        peak = float(max(amp.max(), 1e-9))
        amp_norm = amp / peak

        rows: list[str] = []
        mid = height // 2
        for row in range(height):
            dist_from_mid = abs(row - mid) / max(1, mid)
            line_chars: list[str] = []
            for col in range(width):
                strength = max(0.0, float(amp_norm[col]) - dist_from_mid)
                idx = int(strength * (len(chars) - 1) + 0.5)
                line_chars.append(chars[idx])
            rows.append("".join(line_chars))
        return "\n".join(rows)

    def __repr__(self) -> str:
        return (
            f"Waveform(style={self.style!r}, samples={self._mono.shape[0]}, "
            f"sample_rate={self._sample_rate}, duration={self.duration_seconds:.2f}s)"
        )
