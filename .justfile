# Cross-platform shell configuration
# Use PowerShell on Windows (higher precedence than shell setting)

set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

# Use sh on Unix-like systems

set shell := ["sh", "-c"]

lint:
    just ruff
    just codespell
    just slots
    just bandit

ruff:
    ruff check --fix .

codespell:
    codespell src examples

[unix]
slots:
    PYTHONPATH=src slotscheck -m maxo

[windows]
slots:
    $env:PYTHONPATH="src"; slotscheck -m maxo

bandit:
    bandit src -r

mypy:
    mypy

test:
    pytest --cov src

tests:
    just test

test-all:
    nox

tests-all:
    just test-all

all:
    just lint
    just mypy
    just test-all
