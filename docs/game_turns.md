# Game Turns

This document describes the turn system used by the simulation. Each turn advances the game by a fixed amount of in-game time. The default length of a turn is five seconds, but this can be adjusted.

The `GameTurnManager` class stores the current turn number and length. Calling `advance_turn()` increments the turn counter and returns the time delta to apply to the simulation. `GameSimulation` exposes an `advance_turn()` method that integrates with `GameTurnManager` and processes scheduled events.
