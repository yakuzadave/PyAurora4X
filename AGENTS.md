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
Install the dependencies listed in `pyproject.toml` using pip, then run the test
suite:

```bash
pip install numpy "pydantic>=2.11.5" textual tinydb rebound duckdb pytest
pytest -q
```

## Documentation
Place new markdown documents in the `docs` folder when adding project documentation.
Update README.md with references to any new documents.
