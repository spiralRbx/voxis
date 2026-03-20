PYTHON ?= python
PIP ?= $(PYTHON) -m pip
PACKAGE ?= voxis

.PHONY: install install-dev install-web test build check clean rebuild web benchmark publish-testpypi publish-pypi

install:
	$(PIP) install -e .

install-dev:
	$(PIP) install -e .[dev,web]

install-web:
	$(PIP) install -e .[web]

test:
	$(PYTHON) -m pytest -q

build:
	$(PYTHON) -m build

check: build
	$(PYTHON) -m twine check dist/*

clean:
	$(PYTHON) -c "import shutil, pathlib; [shutil.rmtree(path, ignore_errors=True) for path in ('build','dist','.pytest_cache')]; [shutil.rmtree(path, ignore_errors=True) for path in pathlib.Path('src').glob('*.egg-info')]; [shutil.rmtree(path, ignore_errors=True) for path in pathlib.Path('src').glob('*/__pycache__')]; [shutil.rmtree(path, ignore_errors=True) for path in pathlib.Path('tests').glob('__pycache__')]"

rebuild: clean install-dev

web:
	$(PYTHON) web-test/app.py

benchmark:
	$(PYTHON) benchmarks/benchmark_pipeline.py

publish-testpypi: build check
	$(PYTHON) -m twine upload --repository testpypi dist/*

publish-pypi: build check
	$(PYTHON) -m twine upload dist/*
