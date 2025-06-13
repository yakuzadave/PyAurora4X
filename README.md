# PyAurora 4X

A Python-based 4X space strategy game with realistic orbital mechanics, terminal UI, and modular architecture inspired by Aurora 4X.

## Features

- **Realistic Orbital Mechanics**: Uses REBOUND for N-body physics simulation of planetary orbits
- **Terminal-Based UI**: Clean, responsive interface built with Textual
- **Modular Architecture**: Extensible design with separate engine, UI, data, and core modules
- **4X Gameplay**: Explore, Expand, Exploit, and Exterminate across star systems
- **Research System**: Technology tree with prerequisites and unlocks
- **Fleet Management**: Design ships, manage fleets, and conduct space operations
- **Save/Load System**: Persistent game states with TinyDB and JSON support
- **Comprehensive Testing**: Full test coverage with pytest

## Installation

### Prerequisites

- Python 3.11 or higher
- pip package manager

### Required Dependencies

Install the core dependencies with pip:

```bash
pip install numpy pydantic textual rich tinydb rebound duckdb pytest
```

`rebound` provides the N-body orbital mechanics engine and `duckdb` enables the
optional high-performance save backend. If `duckdb` is not installed the game
will fall back to TinyDB or plain JSON files.

### Optional Features

PyAurora 4X can store saves using TinyDB or DuckDB. By default the
`SaveManager` automatically uses DuckDB when available. You can explicitly
select the backend when creating the `SaveManager`:

```python
from pyaurora4x.data import SaveManager

# Force DuckDB
manager = SaveManager(use_duckdb=True)

# Use TinyDB even if DuckDB is installed
manager = SaveManager(use_duckdb=False)
```

### Running the Game

Launch the main interface with:

```bash
python main.py
```

You can also start a brand new game immediately with:

```bash
python main.py --new-game
```

This is useful when you want to skip loading existing saves and jump straight into a fresh session.

### Simulation Test

You can run a headless simulation for quick verification:

```bash
python main.py --test
```

### Running the Test Suite

Execute the unit tests with pytest:

```bash
pytest -q
```

### Pre-commit Hooks

Install the `pre-commit` tool and set up the git hooks:

```bash
pip install pre-commit
pre-commit install
```

The hooks will automatically format code with **black**, lint with **ruff**,
and type-check with **mypy** every time you commit.

## Documentation

All written guides and reference material live in the `docs/` directory.  It
acts as the central hub for design notes, usage instructions, and other
supplementary information.  Begin with
[docs/README.md](docs/README.md) which serves as the index and explains how to
contribute new documents.

### Available Guides

- [docs/README.md](docs/README.md) – Documentation index and contribution
  guidelines.
- [docs/design_overview.md](docs/design_overview.md) – Summary of project goals
  and folder structure.
- [docs/gameplay_guide.md](docs/gameplay_guide.md) – Gameplay instructions
  *(planned)*.
- [docs/contributing.md](docs/contributing.md) – Developer contribution guide
  *(planned)*.


## License

This project is licensed under the [MIT License](LICENSE).

