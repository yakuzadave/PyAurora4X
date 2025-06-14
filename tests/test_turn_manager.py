from pyaurora4x.engine.turn_manager import GameTurnManager
from pyaurora4x.engine.simulation import GameSimulation


class TestGameTurnManager:
    def test_advance_and_reset(self):
        tm = GameTurnManager(turn_length=10.0)
        assert tm.current_turn == 0
        delta = tm.advance_turn()
        assert delta == 10.0
        assert tm.current_turn == 1
        tm.reset()
        assert tm.current_turn == 0


class TestGameSimulationTurns:
    def test_simulation_advance_turn(self):
        sim = GameSimulation()
        sim.initialize_new_game(num_systems=1, num_empires=1)
        initial_time = sim.current_time
        sim.advance_turn()
        assert sim.current_time == initial_time + sim.turn_manager.turn_length
        assert sim.turn_manager.current_turn == 1
