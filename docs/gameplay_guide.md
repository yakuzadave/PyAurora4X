# Gameplay Guide

This guide covers the essentials of playing **PyAurora 4X**. It explains the terminal interface, common commands, and how a typical session progresses.

## UI Overview

PyAurora 4X runs entirely in the terminal using the Textual library. After launching the game you will see the main star system map surrounded by informational panels.

- **Top Bar** – displays the current date and active game speed
- **Left Panel** – context-sensitive commands for colonies, fleets, and research
- **Right Panel** – event log with messages and notifications
- **Main Area** – orbital view of planets, moons, and fleets

Navigate between elements with the arrow keys or `j`/`k`. Press `Enter` to activate a highlighted option.

## Basic Commands

- `n` – start a new game
- `l` – load an existing save
- `s` – save the current game
- `q` – quit to the terminal
- `?` – open the help screen
- `F1`–`F5` – focus the first five fleets for quick selection
- `f` – toggle between basic and advanced fleet management modes
- `6` – switch to advanced fleet command view

Other shortcuts appear at the bottom of the UI when available.

## Gameplay Phases

1. **Setup** – create your empire and choose starting conditions
2. **Exploration & Expansion** – survey systems and found new colonies
3. **Research & Development** – unlock technologies to improve ships and industry
4. **Fleet Operations** – organize forces and assign missions
5. **Conflict** – engage rival powers or defend your territory

## Fleet Management

### Basic Fleet Operations

Fleets use Hohmann or bi-elliptic transfer orbits to travel between planetary bodies. When REBOUND is installed the game calculates realistic transfer times based on current positions. The most efficient method is selected automatically and the arrival time is displayed in each order.

### Advanced Fleet Command System

Press `f` to toggle between basic and advanced fleet management modes, or press `6` to directly access the advanced Fleet Command Panel. The advanced system provides:

#### Tactical Views
- **Overview** – mission performance, status summary, operational readiness
- **Formation** – formation control, integrity status, available formations  
- **Combat** – combat ratings, experience, morale, engagement status
- **Logistics** – fuel status, maintenance needs, supply lines, operational time

#### Order Management
- Issue complex orders with priority levels (Emergency, High, Normal, Low, Background)
- Track order progress and estimated completion times
- Queue multiple orders for sequential execution
- Cancel or modify pending orders

#### Formation Control
- Choose from predefined formations: Line Ahead, Battle Line, Screening Formation, Box Formation, Escort Formation
- Monitor formation integrity and cohesion
- Formation effects on movement speed, combat effectiveness, and detection
- Real-time formation status updates

#### Quick Actions
- **Move** – Issue movement orders with tactical positioning
- **Attack** – Engage hostile forces with coordinated assault
- **Patrol** – Establish patrol routes with repeating orders
- **Defend** – Adopt defensive postures and protect assets

#### Keyboard Shortcuts (Advanced Fleet Command)
- `f` – Switch to formations view
- `o` – Switch to orders view  
- `c` – Switch to combat view
- `l` – Switch to logistics view
- `a` – Issue attack order
- `m` – Issue move order
- `p` – Issue patrol order
- `Escape` – Cancel selected order
