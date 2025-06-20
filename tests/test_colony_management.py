from pyaurora4x.engine.simulation import GameSimulation


def test_colony_initialization():
    sim = GameSimulation()
    sim.initialize_new_game(num_systems=2, num_empires=2)

    total_colonies = sum(len(emp.colonies) for emp in sim.empires.values())
    assert total_colonies == len(sim.colonies)
    assert total_colonies == len(sim.empires)


def test_colony_growth_and_mining():
    sim = GameSimulation()
    sim.initialize_new_game(num_systems=1, num_empires=1)
    empire = sim.get_player_empire()
    colony_id = empire.colonies[0]
    colony = sim.colonies[colony_id]
    colony.population = 1000
    colony.infrastructure["mine"] = 1

    sim.advance_time(86400)  # one day

    assert colony.population > 1000
    assert colony.stockpiles.get("minerals", 0) > 0
