import pytest

from pyaurora4x.engine.star_system import StarSystemGenerator
from pyaurora4x.engine.simulation import GameSimulation
from pyaurora4x.core.models import Fleet, Vector3D


def test_jump_network_generation():
    gen = StarSystemGenerator(seed=1)
    systems = [gen.generate_system(f"sys{i}") for i in range(3)]
    gen.generate_jump_network(systems)

    for i, system in enumerate(systems):
        assert system.jump_points  # each system has at least one
        targets = {jp.connects_to for jp in system.jump_points}
        # Each system connects to the next in the ring
        expected = systems[(i + 1) % len(systems)].id
        assert expected in targets


def test_simulation_jump_fleet():
    sim = GameSimulation()
    sim.initialize_new_game(num_systems=2, num_empires=1)
    sys_ids = list(sim.star_systems.keys())
    fleet = Fleet(
        name="Jumpers",
        empire_id="player",
        system_id=sys_ids[0],
        position=Vector3D(),
    )
    sim.fleets[fleet.id] = fleet

    result = sim.jump_fleet(fleet.id, sys_ids[1])
    assert result
    assert fleet.system_id == sys_ids[1]

