# Cross-platform shell configuration
# Use PowerShell on Windows (higher precedence than shell setting)

set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

# Use sh on Unix-like systems

set shell := ["sh", "-c"]


alias tests := test
alias tests-all := test-all

# Все линтеры, кроме mypy
lint: ruff codespell slots bandit

ruff:
    uv run ruff check --fix .

codespell:
    uv run codespell src examples

[unix]
slots:
    PYTHONPATH=src uv run slotscheck -m maxo

[windows]
slots:
    $env:PYTHONPATH="src"; uv run slotscheck -m maxo

bandit:
    uv run bandit -c pyproject.toml src -r

mypy:
    uv run mypy --config-file pyproject.toml

test *args:
    uv run pytest tests/ --cov=src --cov-report=term {{ args }}

docs *args:
    uv run sphinx-build -b html docs docs/_build/html {{ args }}

test-all:
    uv run nox

butcher *args:
    uv run --group butcher python -m butcher {{ args }}

butcher-test *args:
    uv run --group butcher pytest butcher/tests {{ args }}

all: lint mypy test-all
