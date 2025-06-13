from pyaurora4x.engine.simulation import GameSimulation
from pyaurora4x.data.save_manager import SaveManager


def test_research_completion():
    sim = GameSimulation()
    sim.initialize_new_game(num_systems=1, num_empires=1)
    empire = sim.get_player_empire()

    tech_id = "basic_propulsion"
    empire.current_research = tech_id
    empire.research_points = 0
    tech = empire.technologies[tech_id]

    sim.advance_time(tech.research_cost)

    assert tech.is_researched
    assert empire.current_research is None


def test_research_persistence(tmp_path):
    sim = GameSimulation()
    sim.initialize_new_game(num_systems=1, num_empires=1)
    empire = sim.get_player_empire()

    tech_id = "basic_sensors"
    empire.current_research = tech_id
    empire.research_points = 0
    tech = empire.technologies[tech_id]

    sim.advance_time(tech.research_cost)

    manager = SaveManager(save_directory=str(tmp_path))
    manager.use_tinydb = False
    save_file = manager.save_game(sim.get_game_state(), "save1")
    loaded = manager.load_game(save_file)

    sim2 = GameSimulation()
    sim2.load_game_state(loaded)
    empire2 = sim2.get_player_empire()
    assert empire2.technologies[tech_id].is_researched
