# PyAurora 4X

A Python-based 4X space strategy game with realistic orbital mechanics, terminal UI, and modular architecture inspired by Aurora 4X.

## Features

- **Realistic Orbital Mechanics**: Uses REBOUND for N-body physics simulation of planetary orbits
- **Terminal-Based UI**: Clean, responsive interface built with Textual
- **Command Dashboard Mode**: Dense Aurora-inspired command-line cockpit for resource, fleet, colony, and star-system monitoring
- **Modular Architecture**: Extensible design with separate engine, UI, data, and core modules
- **4X Gameplay**: Explore, Expand, Exploit, and Exterminate across star systems
- **Research System**: Technology tree with prerequisites and unlocks
- **Advanced Fleet Command**: Comprehensive tactical fleet management with formations, orders, and AI-controlled behavior
- **Fleet Management**: Design ships, manage fleets, and conduct space operations
- **Save/Load System**: Persistent game states with TinyDB and JSON support
- **Colony Management**: Colonies grow and produce resources over time
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

`rebound` provides the N-body orbital mechanics engine and `duckdb` enables the optional high-performance save backend. If `duckdb` is not installed the game will fall back to TinyDB or plain JSON files.

### Optional Features

PyAurora 4X can store saves using TinyDB or DuckDB. By default the `SaveManager` automatically uses DuckDB when available. You can explicitly select the backend when creating the `SaveManager`:

```python
from pyaurora4x.data import SaveManager

# Force DuckDB
manager = SaveManager(use_duckdb=True)

# Use TinyDB even if DuckDB is installed
manager = SaveManager(use_duckdb=False)
```

You can change the default save directory by setting the `PYAURORA_SAVE_DIR` environment variable. If `save_directory` is not provided, `SaveManager` will use this path:

```bash
export PYAURORA_SAVE_DIR=/path/to/saves
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

You can customize the initial galaxy:

```bash
python main.py --new-game --systems 5 --empires 3
```

`--systems` controls how many star systems are generated, while `--empires` sets the total number of empires (including the player). This is useful when you want to skip loading existing saves and jump straight into a fresh session.

### Command Dashboard Mode

Launch the dense command dashboard instead of the default multi-panel Textual UI:

```bash
python main.py --command-ui
```

The command dashboard can also start from a customized new game:

```bash
python main.py --command-ui --new-game --systems 8 --empires 4
```

The command dashboard uses a single-screen cockpit layout. The left panel summarizes resources, colonies, fleets, and empire data. The center panel renders the selected star system, planets, belts, fleets, and selected-object details. The right panel lists the available keyboard commands.

Useful command dashboard keys:

| Key | Action |
| --- | --- |
| `N` / `B` | Move to the next or previous star system |
| `Up` / `Down` | Select the previous or next object in the current system |
| `A` | Advance time by 30 seconds |
| `Y` | Advance time by one year |
| `Space` | Pause or resume the simulation |
| `S` | Save the current game |
| `H` | Show an in-app help notification |
| `Q` / `Esc` | Quit |

To resume a previous session, provide the save name or path:

```bash
python main.py --load <save_name_or_path>
```

`<save_name_or_path>` refers to either a file path or the name of a save stored in the default directory.

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

The hooks will automatically format code with **black**, lint with **ruff**, and type-check with **mypy** every time you commit.
