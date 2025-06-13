#!/usr/bin/env python3
"""
PyAurora 4X - Main Entry Point

A Python-based 4X space strategy game with realistic orbital mechanics,
terminal UI, and modular architecture inspired by Aurora 4X.
"""

import sys
import argparse
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from pyaurora4x.ui.main_app import PyAurora4XApp
from pyaurora4x.engine.simulation import GameSimulation
from pyaurora4x.data.save_manager import SaveManager


def run_simulation_test():
    """Run a headless simulation test for debugging."""
    print("Running headless simulation test...")
    
    # Create a new game simulation
    sim = GameSimulation()
    sim.initialize_new_game()
    
    # Print initial state
    print(f"Game Time: {sim.current_time}")
    print(f"Star Systems: {len(sim.star_systems)}")
    
    for system_id, system in sim.star_systems.items():
        print(f"  System {system.name}: {len(system.planets)} planets")
        for planet in system.planets:
            print(f"    {planet.name}: {planet.planet_type}")
    
    print(f"Empires: {len(sim.empires)}")
    for empire_id, empire in sim.empires.items():
        print(f"  {empire.name}: {len(empire.fleets)} fleets")
    
    # Advance time a few steps
    print("\nAdvancing time...")
    for i in range(5):
        sim.advance_time(30)  # 30 seconds per step
        print(f"Step {i+1}: Game Time = {sim.current_time}")
    
    print("Simulation test completed successfully!")


def main():
    """Main entry point for PyAurora 4X."""
    parser = argparse.ArgumentParser(
        description="PyAurora 4X - Terminal-based 4X space strategy game"
    )
    parser.add_argument(
        "--test", 
        action="store_true", 
        help="Run headless simulation test"
    )
    parser.add_argument(
        "--load", 
        type=str, 
        help="Load a saved game file"
    )
    parser.add_argument(
        "--new-game", 
        action="store_true", 
        help="Start a new game (default)"
    )
    
    args = parser.parse_args()
    
    if args.test:
        run_simulation_test()
        return
    
    # Run the main Textual application
    app = PyAurora4XApp()
    
    if args.load:
        # Load existing game
        save_manager = SaveManager()
        try:
            game_data = save_manager.load_game(args.load)
            app.load_game_data(game_data)
            print(f"Loaded game: {args.load}")
        except Exception as e:
            print(f"Error loading game: {e}")
            return
    else:
        # Start new game (default)
        app.start_new_game()
    
    # Run the application
    app.run()


if __name__ == "__main__":
    main()
