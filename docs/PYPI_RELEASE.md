# Voxis PyPI Release

Recommended values for your public release setup:

- PyPI project name: `voxis`
- GitHub owner: `spiralRbx`
- Repository name: `voxis`
- Workflow name: `Publish Voxis to PyPI`
- Workflow file: `.github/workflows/publish-pypi.yml`
- Optional GitHub environment: `pypi`

## Release structure

- Python package: `src/voxis`
- Native core: `cpp/src/bindings.cpp`
- Native headers: `cpp/include/voxis/dsp.hpp`
- Project metadata: `pyproject.toml`
- CMake build: `CMakeLists.txt`
- Local automation: `Makefile`
- Publish workflow: `.github/workflows/publish-pypi.yml`

## Local release flow

```bash
make install-dev
make test
make build
make check
```

Manual publish to PyPI:

```bash
make publish-pypi
```

Manual publish to TestPyPI:

```bash
make publish-testpypi
```

## GitHub Actions flow

The workflow publishes when you push a tag such as:

```bash
git tag v0.0.1
git push origin v0.0.1
```

## What must exist on GitHub

1. Repository: `spiralRbx/voxis`
2. Optional environment: `pypi`
3. Trusted Publishing configured in PyPI pointing to:
   - owner: `spiralRbx`
   - repository: `voxis`
   - workflow: `publish-pypi.yml`
   - environment: `pypi`

## What must exist on PyPI

1. A reserved project named `voxis`
2. A Trusted Publisher linked to the repository
3. A new version in `pyproject.toml` before creating the release tag

## Notes

- `voxis` is both the project name and the package name
- `pip install voxis` uses this exact name
- Main import:

```python
from voxis import AudioClip
```
