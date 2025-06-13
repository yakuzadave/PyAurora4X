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


## Documentation
Additional markdown resources are stored in the `docs` directory.
See [docs/README.md](docs/README.md) for an overview of available files,
a table of contents, and instructions on contributing new documentation.
Remember to add new markdown files to that index and mention them here when appropriate.

## License

PyAurora 4X is released under the [MIT License](LICENSE).

