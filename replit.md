# PyAurora 4X - Replit Development Guide

## Overview

PyAurora 4X is a Python-based 4X space strategy game featuring realistic orbital mechanics, a terminal-based UI, and modular architecture. The game simulates space exploration, empire building, fleet management, and research progression in a scientifically accurate solar system environment.

## System Architecture

### Core Technologies
- **Python 3.11+** - Primary language with modern features
- **Textual** - Terminal-based UI framework for rich console interfaces
- **REBOUND** - N-body physics simulation for realistic orbital mechanics
- **Pydantic** - Data validation and serialization for game models
- **DuckDB/TinyDB** - Flexible persistence layer with fallback options
- **NumPy** - Mathematical operations and vector calculations
- **Pytest** - Comprehensive testing framework

### Architecture Pattern
The project follows a modular MVC-style architecture:
- **Engine** - Core simulation logic and game state management
- **UI** - Textual-based presentation layer with reactive widgets
- **Data** - Persistence, serialization, and data management
- **Core** - Shared models, events, and utilities

## Key Components

### Game Engine (`pyaurora4x/engine/`)
- **GameSimulation** - Main orchestrator managing all game systems
- **OrbitalMechanics** - REBOUND integration for realistic physics
- **GameScheduler** - Event-driven time management system
- **StarSystemGenerator** - Procedural generation of star systems
- **GameTurnManager** - Turn-based progression controls

### User Interface (`pyaurora4x/ui/`)
- **PyAurora4XApp** - Main Textual application entry point
- **StarSystemView** - ASCII visualization of orbital mechanics
- **FleetPanel** - Fleet management and command interface
- **ResearchPanel** - Technology tree progression
- **EmpireStatsWidget** - Empire status and resource tracking

### Data Layer (`pyaurora4x/data/`)
- **SaveManager** - Multi-backend persistence (DuckDB/TinyDB/JSON)
- **TechTreeManager** - Technology system and prerequisites
- **ShipComponentManager** - Ship design and component systems

### Core Systems (`pyaurora4x/core/`)
- **Models** - Pydantic data models for all game entities
- **Events** - Event-driven architecture for game mechanics
- **Enums** - Type-safe constants and classifications
- **Utils** - Mathematical and utility functions

## Data Flow

### Game State Management
1. **Initialization** - GameSimulation creates initial universe state
2. **Time Advancement** - Scheduler processes events and updates positions
3. **User Input** - UI widgets trigger commands through event system
4. **State Updates** - Models are updated and changes propagated
5. **Persistence** - SaveManager serializes state to chosen backend

### Orbital Mechanics Pipeline
1. **System Generation** - StarSystemGenerator creates realistic star systems
2. **Physics Integration** - OrbitalMechanics initializes REBOUND simulations
3. **Position Updates** - Real-time calculation of planetary positions
4. **Fleet Movement** - Hohmann transfers and orbital mechanics for ships
5. **Visualization** - StarSystemView renders current positions

### Research and Technology
1. **Tech Tree Loading** - TechTreeManager loads from JSON configuration
2. **Prerequisite Validation** - Ensures valid research dependencies
3. **Research Progress** - Empire accumulates research points over time
4. **Technology Unlocks** - New capabilities become available
5. **Component Access** - ShipComponentManager provides buildable components

## External Dependencies

### Required Dependencies
- **numpy** - Mathematical operations and array handling
- **pydantic** - Data validation and model serialization
- **textual** - Terminal UI framework and widget system
- **tinydb** - Lightweight JSON database (fallback)
- **rebound** - N-body orbital mechanics simulation
- **duckdb** - High-performance analytical database
- **pytest** - Testing framework and test utilities

### Optional Features
- **DuckDB backend** - Automatically used when available for better performance
- **REBOUND physics** - Falls back to simplified mechanics if unavailable
- **Rich formatting** - Enhanced terminal output (via Textual dependency)

## Deployment Strategy

### Development Environment
- Uses Python 3.11 with modern language features
- Pre-commit hooks enforce code quality (black, ruff, mypy)
- Comprehensive test suite with pytest
- Replit-compatible with automated dependency installation

### Production Considerations
- Single-file entry point (`main.py`) for easy deployment
- Graceful fallbacks for optional dependencies
- Configurable save directory via environment variables
- Cross-platform compatibility (Windows, macOS, Linux)

### Build and Distribution
- Poetry/pyproject.toml for modern Python packaging
- MIT license for open-source distribution
- Modular design allows selective feature deployment
- Docker-friendly with minimal system dependencies

## Changelog

- December 19, 2024. Successfully migrated from Replit Agent to Replit environment
  - Fixed FleetPanel.refresh() method compatibility with Textual framework
  - Fixed ResearchPanel.refresh() method compatibility with Textual framework
  - Verified all UI components are functional and responsive
- June 20, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.