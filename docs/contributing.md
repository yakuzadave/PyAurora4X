# Contributing Guide

This document explains how to prepare your environment, follow the project's coding style, and verify your changes with tests.

## Coding Style

- Format code with **black** using a line length of 88 characters.
- Lint the project with **ruff** for standard Python style and import ordering.
- Type-check new code with **mypy**.

All these tools run automatically via the pre-commit hooks described below.

## Pre-commit Workflow

1. Install the [`pre-commit`](https://pre-commit.com) tool:
   ```bash
   pip install pre-commit
   ```
2. Install the hooks for this repository:
   ```bash
   pre-commit install
   ```
3. The hooks will run **black**, **ruff**, and **mypy** each time you commit. You can manually run them on all files with:
   ```bash
   pre-commit run --all-files
   ```

Keeping the hooks active ensures that every commit adheres to the project's coding standards.

## Running Tests

Before submitting changes, install the project's dependencies and execute the test suite:

```bash
pip install numpy "pydantic>=2.11.5" textual tinydb rebound duckdb pytest
pytest -q
```

All tests should pass before opening a pull request.
