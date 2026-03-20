from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import numpy as np


def ensure_float32_frames(samples: Any) -> np.ndarray:
    array = np.asarray(samples)

    if array.ndim == 1:
        array = array[:, None]

    if array.ndim != 2:
        raise ValueError("Audio buffers must have shape (frames, channels) or (frames,).")

    if np.issubdtype(array.dtype, np.integer):
        info = np.iinfo(array.dtype)
        scale = float(max(abs(info.min), info.max))
        array = array.astype(np.float32) / scale
    else:
        array = array.astype(np.float32, copy=False)

    return np.ascontiguousarray(array)


def flatten_effects(effects: Iterable[Any]) -> list[Any]:
    flattened: list[Any] = []
    for effect in effects:
        if effect is None:
            continue
        if isinstance(effect, (list, tuple)):
            flattened.extend(flatten_effects(effect))
        else:
            flattened.append(effect)
    return flattened
