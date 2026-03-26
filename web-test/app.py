from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_offline_app():
    module_path = Path(__file__).resolve().parent / "offline" / "app.py"
    spec = importlib.util.spec_from_file_location("voxis_web_test_offline", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load web-test/offline/app.py")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


offline = _load_offline_app()
app = offline.app


if __name__ == "__main__":
    app.run(debug=True)
