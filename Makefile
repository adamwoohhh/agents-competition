.PHONY: venv install dev-install test check build publish-test publish run compete agent llm clean

SYSTEM_PYTHON ?= python3
VENV ?= .venv
PYTHON := $(VENV)/bin/python
PIP := $(PYTHON) -m pip
DINO := $(VENV)/bin/dino

venv:
	$(SYSTEM_PYTHON) -m venv $(VENV)

install: venv
	$(PIP) install .

dev-install: venv
	$(PIP) install -e .

test: venv
	env PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m unittest tests/test_packaging.py

check: test
	env PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m py_compile dino_game.py

build:
	$(SYSTEM_PYTHON) -m build

publish-test:
	$(SYSTEM_PYTHON) -m twine upload --repository testpypi dist/*

publish:
	$(SYSTEM_PYTHON) -m twine upload dist/*

run:
	$(DINO)

compete:
	$(DINO) compete

agent:
	$(DINO) --agent

llm:
	$(DINO) --llm

clean:
	rm -rf __pycache__ tests/__pycache__ *.egg-info build dist
