import pytest
from pyaurora4x.engine.simulation import GameSimulation
from pyaurora4x.core.enums import FleetStatus
from pyaurora4x.core.models import Fleet, Vector3D


def test_start_combat():
    sim = GameSimulation()
    sim.initialize_new_game(num_systems=2, num_empires=2)

    system_id = list(sim.star_systems.keys())[0]
    attacker = Fleet(name="Attacker", empire_id="player", system_id=system_id, position=Vector3D())
    ai_id = next(eid for eid in sim.empires if eid != "player")
    defender = Fleet(name="Defender", empire_id=ai_id, system_id=system_id, position=Vector3D())

    attacker.ships = ["s1", "s2"]
    defender.ships = ["s3"]

    sim.fleets[attacker.id] = attacker
    sim.fleets[defender.id] = defender

    winner = sim.start_combat(attacker.id, defender.id)
    assert winner in (attacker.id, defender.id)
    assert sim.fleets[attacker.id].status == FleetStatus.IDLE
    assert sim.fleets[defender.id].status == FleetStatus.IDLE
