# Design Overview

This document provides a brief summary of the purpose of PyAurora 4X, the phases of gameplay, and how the source code is organized.

## Project Goals
- Deliver a terminal-based 4X strategy game inspired by Aurora 4X
- Simulate realistic orbital mechanics using the REBOUND library
- Offer an extensible architecture that separates game logic, data storage, and the user interface

## Gameplay Phases
PyAurora 4X follows the classic "4X" structure:
1. **Explore** – Survey star systems and discover new worlds
2. **Expand** – Establish colonies and grow your empire
3. **Exploit** – Gather resources and research new technologies
4. **Exterminate** – Build fleets and confront rival powers

## Folder Structure
The main Python package is located in `pyaurora4x/` and is divided into several submodules:
- `engine/` – Core game simulation such as star systems, schedulers, and orbital physics
- `ui/` – Textual-based user interface and widgets
- `data/` – Persistence, tech trees, and ship component definitions
- `core/` – Shared models, events, and utility helpers

These directories work together to support a modular and extensible code base.

