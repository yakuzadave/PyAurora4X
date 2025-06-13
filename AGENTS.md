# PyAurora4X Agent Instructions

This repository contains a terminal-based 4X space strategy game implemented in Python. The project features realistic orbital mechanics using the REBOUND library, a Textual-based UI, and a modular architecture spanning engine, data, and core modules.

## Project History
The commit history shows a gradual build-out of game functionality, including:
- Initial project setup with core modules, data files, and tests.
- Addition of ship components, REBOUND integration, and early UI improvements.
- Implementation of AI actions and unit tests for the scheduler and simulation.
- Packaging metadata updates and pre-commit configuration.
- Research management and persistence, including DuckDB backend support.
- AI and research improvements, save/load dialog, and extensive tech tree tests.

## Running Tests
Install dependencies as specified in `pyproject.toml` and run the test suite:

```bash
pip install -r requirements.txt  # or install packages manually
pytest -q
```
