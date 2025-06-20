# Fleet Combat and Command Structure

This document outlines the early combat mechanics for **PyAurora 4X**.

## Tactical Engagements

Fleets can engage each other directly. The `GameSimulation.start_combat`
method resolves a basic battle by comparing the number of ships in each
fleet. The side with the larger force wins and both fleets return to the
`IDLE` status afterward.

These rules provide a placeholder system that will be expanded with
weapon damage, ship roles and commander bonuses in future updates.

## Officers and Ship Roles

Ships now include a `role` attribute describing their duty within the
fleet such as `command`, `assault`, or `support`. Fleets may have a
`commander_id` and a list of assigned officers. Officers track rank and
experience but currently provide no modifiers.
