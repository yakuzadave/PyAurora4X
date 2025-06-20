# Jump Point Mechanics

PyAurora 4X uses jump points to connect star systems and enable faster-than-light travel. Each
star system contains a set of `JumpPoint` objects describing a location in space and the system
it connects to. During world generation the `StarSystemGenerator` links systems into a simple
network so fleets can traverse between them.

Fleets equipped with a jump drive can instantaneously move to another system via an available
jump point. The `GameSimulation.jump_fleet` helper checks for a valid connection and updates the
fleet's location when a jump is performed.

