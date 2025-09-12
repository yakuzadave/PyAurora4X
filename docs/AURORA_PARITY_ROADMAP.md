# Aurora Parity Roadmap

## Purpose
A living roadmap to evolve PyAurora4X toward Aurora 4X fidelity while maintaining a modern, modular Python architecture with strong tests and data-driven systems.

## Priorities (P0 → P2)
- P0
  - Shipyards & Slipways (build/refit queues, capacity, tooling)  
  - Maintenance & Overhaul (MSP, failures, overhaul clocks)
- P1
  - Sensors & Signatures & ECM/ECCM  
  - Ordnance & Magazines (production, loadouts, reloads)
  - Fuel Economy (sorium harvest, refining, transfer)
- P2
  - Civilian Shipping & Contracts  
  - Officers/Commanders  
  - Standing/Conditional Orders  
  - Industry Specialization (factory types)  
  - Survey Layers (geo/gravity/ruins/anomalies)

## Guiding Principles
- Pydantic v2 models for domain entities; strict types  
- Discrete-event scheduler integration for scalable simulation  
- Domain services per subsystem; UI decoupled from engine  
- Logging with lazy % formatting per project rules  
- Property-based testing for key math and schedulers  
- Data-driven configs for economy and tech  

## Milestones & Tasks

### M1: Shipyards & Slipways (P0)
- Core models: YardType, Slipway, BuildOrder, RefitOrder, Shipyard
- Manager: queue assignment, per-tick progress, completion events
- Save/Load: versioned, backward-compatible defaults
- Minimal UI (later): yard panel & queue view
- Tests: throughput math, slipway occupancy, completion

### M2: Maintenance & Overhaul (P0)
- Add component MTBF/MTTR and failure events  
- MSP consumption and spares stockpiles (colony/tenders)  
- Overhaul at shipyards; resets failure clocks  
- Tests: stochastic failures (seeded), overhaul flow, MSP depletion

### M3: Sensors & Signatures (P1)
- Thermal/EM signatures, active/passive detection thresholds
- ECM/ECCM impact; fire control resolution and lock
- Tests: deterministic contact tables with tech variations

### M4: Ordnance & Magazines (P1)
- Magazine capacities, ordnance factory throughput, missile entities
- Reload logistics (planetary depots, tenders), salvo coordinator
- Tests: stockpile accounting, reload timings, hit probability effects

### M5: Fuel Economy (P1)
- Sorium harvesting (gas giants), refining throughput, engine fuel burn
- Fleet refuel orders and tanker behavior
- Tests: harvest→refine→consume loop

### M6: Extended Systems (P2)
- Civilian shipping lines & contracts; officer assignments; standing orders; specialized factories; survey layers

## Acceptance for M1
- New shipyard subsystem compiles, saves/loads, and passes tests
- No regressions in existing test suite
- Minimal docs included and discoverable via docs/README

