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

- Python 3.8 or higher
- pip package manager

### Required Dependencies

The game requires several Python packages. Install them using:

```bash
pip install textual rich pydantic numpy tinydb
```

## Development

This project uses `pre-commit` to run formatting, linting and type checks. Set it up with:

```bash
pip install pre-commit
pre-commit install
```

Run all checks manually using:

```bash
pre-commit run --all-files
```
