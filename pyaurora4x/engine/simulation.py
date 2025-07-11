"""
Core game simulation engine for PyAurora 4X

Manages the overall game state, time advancement, and coordination
between different game systems.
"""

from typing import Dict, Optional, Any, List
from datetime import datetime
import logging
import random


from pyaurora4x.core.models import (
    Empire,
    StarSystem,
    Fleet,
    Technology,
    Planet,
    Vector3D,
    Colony,
)


from pyaurora4x.core.enums import FleetStatus, PlanetType

from pyaurora4x.core.events import EventManager
from pyaurora4x.engine.scheduler import GameScheduler
from pyaurora4x.engine.star_system import StarSystemGenerator
from pyaurora4x.engine.orbital_mechanics import OrbitalMechanics
from pyaurora4x.engine.turn_manager import GameTurnManager

from pyaurora4x.data.tech_tree import TechTreeManager

logger = logging.getLogger(__name__)


class GameSimulation:
    """
    Main game simulation engine that coordinates all game systems.
    
    This class manages the overall game state including empires, star systems,
    time advancement, and event processing. It can run with or without a UI
    for testing purposes.
    """
    
    def __init__(self):
        """Initialize the game simulation."""
        self.current_time: float = 0.0  # Game time in seconds since epoch
        self.game_start_time: datetime = datetime.now()
        self.time_acceleration: float = 1.0  # Real seconds per game second
        
        # Core game objects
        self.empires: Dict[str, Empire] = {}
        self.star_systems: Dict[str, StarSystem] = {}
        self.fleets: Dict[str, Fleet] = {}
        self.colonies: Dict[str, Colony] = {}

        # Game systems
        self.scheduler = GameScheduler()
        self.event_manager = EventManager()
        self.orbital_mechanics = OrbitalMechanics()
        self.system_generator = StarSystemGenerator()
        self.tech_manager = TechTreeManager()
        self.turn_manager = GameTurnManager()
        
        # Game state
        self.is_running = False
        self.is_paused = False

        logger.info("Game simulation initialized")

    def _get_initial_empire_technologies(self) -> Dict[str, Technology]:
        """Create a fresh copy of all technologies for a new empire."""
        techs = {}
        for tech_id, tech in self.tech_manager.get_all_technologies().items():
            techs[tech_id] = Technology(**tech.model_dump())
        return techs
    
    def initialize_new_game(self, num_systems: int = 3, num_empires: int = 2) -> None:
        """
        Initialize a new game with default settings.
        
        Args:
            num_systems: Number of star systems to generate
            num_empires: Number of AI empires to create
        """
        logger.info(f"Initializing new game with {num_systems} systems and {num_empires} empires")
        
        # Reset game state
        self.current_time = 0.0
        self.empires.clear()
        self.star_systems.clear()
        self.fleets.clear()
        self.turn_manager.reset()
        
        # Generate star systems
        self._generate_star_systems(num_systems)
        # Link systems via jump points
        self.system_generator.generate_jump_network(list(self.star_systems.values()))

        # Create player empire
        self._create_player_empire()

        # Create AI empires
        self._create_ai_empires(num_empires - 1)
        
        # Initialize orbital mechanics for all systems
        self._initialize_orbital_mechanics()
        
        # Schedule initial events
        self._schedule_initial_events()
        
        self.is_running = True
        logger.info("New game initialized successfully")
    
    def _generate_star_systems(self, num_systems: int) -> None:
        """Generate the specified number of star systems."""
        for i in range(num_systems):
            system = self.system_generator.generate_system(f"system_{i}")
            self.star_systems[system.id] = system
            logger.debug(f"Generated star system: {system.name}")
    
    def _create_player_empire(self) -> None:
        """Create the player's empire."""
        # Find a suitable home system
        home_system = list(self.star_systems.values())[0]

        if not home_system.planets:
            home_system.planets.append(
                Planet(
                    name="Home",
                    planet_type=PlanetType.TERRESTRIAL,
                    mass=1.0,
                    radius=1.0,
                    surface_temperature=288.0,
                    orbital_distance=1.0,
                    orbital_period=1.0,
                    position=Vector3D(),
                )
            )

        home_planet = None

        for planet in home_system.planets:
            if planet.planet_type == PlanetType.TERRESTRIAL:
                home_planet = planet
                break

        if not home_planet:
            home_planet = home_system.planets[0]
        
        # Create player empire
        player_empire = Empire(
            id="player",
            name="Human Empire",
            is_player=True,
            home_system_id=home_system.id,
            home_planet_id=home_planet.id
        )
        player_empire.technologies = self._get_initial_empire_technologies()
        
        # Create initial fleet
        initial_fleet = Fleet(
            id="player_fleet_0",
            name="First Fleet",
            empire_id="player",
            system_id=home_system.id,
            position=home_planet.position.copy()
        )
        
        player_empire.fleets.append(initial_fleet.id)
        # Create initial colony on the home planet
        colony = Colony(
            name=f"{home_planet.name} Colony",
            empire_id=player_empire.id,
            planet_id=home_planet.id,
            established_date=self.current_time,
        )
        player_empire.colonies.append(colony.id)
        self.colonies[colony.id] = colony
        home_planet.colony_id = colony.id

        self.empires[player_empire.id] = player_empire
        self.fleets[initial_fleet.id] = initial_fleet
        
        logger.info(f"Created player empire: {player_empire.name}")
    
    def _create_ai_empires(self, num_ai: int) -> None:
        """Create AI empires."""
        available_systems = list(self.star_systems.values())[1:]  # Exclude player's system
        
        for i in range(min(num_ai, len(available_systems))):
            system = available_systems[i]
            home_planet = system.planets[0] if system.planets else None
            
            if not home_planet:
                continue
            
            ai_empire = Empire(
                id=f"ai_{i}",
                name=f"AI Empire {i+1}",
                is_player=False,
                home_system_id=system.id,
                home_planet_id=home_planet.id
            )
            ai_empire.technologies = self._get_initial_empire_technologies()
            
            # Create initial fleet for AI
            ai_fleet = Fleet(
                id=f"ai_{i}_fleet_0",
                name=f"AI Fleet {i+1}",
                empire_id=ai_empire.id,
                system_id=system.id,
                position=home_planet.position.copy()
            )
            
            ai_empire.fleets.append(ai_fleet.id)
            # Create initial colony for AI
            colony = Colony(
                name=f"{home_planet.name} Colony",
                empire_id=ai_empire.id,
                planet_id=home_planet.id,
                established_date=self.current_time,
            )
            ai_empire.colonies.append(colony.id)
            self.colonies[colony.id] = colony
            home_planet.colony_id = colony.id

            self.empires[ai_empire.id] = ai_empire
            self.fleets[ai_fleet.id] = ai_fleet
            
            logger.info(f"Created AI empire: {ai_empire.name}")
    
    def _initialize_orbital_mechanics(self) -> None:
        """Initialize REBOUND simulations for all star systems."""
        for system in self.star_systems.values():
            self.orbital_mechanics.initialize_system(system)
    
    def _schedule_initial_events(self) -> None:
        """Schedule initial recurring events."""
        # Schedule orbital updates every 30 seconds
        self.scheduler.schedule_recurring_event(
            "orbital_update",
            30.0,
            self._update_orbital_positions
        )
        
        # Schedule empire AI updates every 60 seconds
        self.scheduler.schedule_recurring_event(
            "ai_update", 
            60.0,
            self._update_ai_empires
        )
    
    def advance_time(self, delta_seconds: float) -> None:
        """
        Advance the game simulation by the specified time.
        
        Args:
            delta_seconds: Number of game seconds to advance
        """
        if not self.is_running or self.is_paused:
            return
        
        old_time = self.current_time
        self.current_time += delta_seconds
        
        # Process scheduled events
        self.scheduler.process_events(old_time, self.current_time)
        
        # Process any queued events
        self.event_manager.process_events()

        # Research progression
        self._process_research(delta_seconds)

        # Colony management
        self._update_colonies(delta_seconds)
        
        logger.debug(f"Advanced time by {delta_seconds}s to {self.current_time}")
    
    def _update_orbital_positions(self) -> None:
        """Update orbital positions for all systems."""
        for system in self.star_systems.values():
            self.orbital_mechanics.update_positions(system, self.current_time)
    
    def _update_ai_empires(self) -> None:
        """Update AI empire decision making."""
        for empire in self.empires.values():
            if not empire.is_player:
                self._process_ai_empire(empire)

    def _process_ai_empire(self, empire: Empire) -> None:
        """Process AI decisions for a single empire."""
        logger.debug(f"Processing AI for empire: {empire.name}")

        # Move idle fleets using orbital transfer calculations
        for fleet_id in empire.fleets:
            fleet = self.fleets.get(fleet_id)
            if not fleet or fleet.status != FleetStatus.IDLE:
                continue

            system = self.star_systems.get(fleet.system_id)
            if not system or not system.planets:
                continue

            target = random.choice(system.planets)
            transfer = self.orbital_mechanics.calculate_transfer_orbit(
                fleet.position, target.position, system.star_mass
            )
            fleet.destination = target.position.copy()
            fleet.estimated_arrival = self.current_time + transfer["transfer_time"]
            order = (
                f"Transfer to {target.name} via {transfer['transfer_type']}"
            )
            fleet.current_orders.append(order)
            fleet.status = FleetStatus.IN_TRANSIT
            logger.debug(
                f"{fleet.name} transferring to {target.name} (ETA {transfer['transfer_time']}s)"
            )

        # Start new research if labs are available
        active_count = (
            (1 if empire.current_research else 0)
            + len(empire.research_projects)
        )
        if active_count < empire.research_labs:
            available = [
                t
                for t in self.tech_manager.technologies.values()
                if t.id not in empire.technologies
                or not empire.technologies[t.id].is_researched
            ]
            if available:
                chosen = random.choice(available)
                empire.technologies[chosen.id] = chosen
                if not empire.current_research:
                    empire.current_research = chosen.id
                    empire.research_points = 0.0
                else:
                    empire.research_projects[chosen.id] = 0.0
                empire.research_allocation = {chosen.tech_type: 100.0}
                logger.debug(f"{empire.name} started researching {chosen.name}")

    def _process_research(self, delta_seconds: float) -> None:
        """Advance research progress for all empires."""
        for empire in self.empires.values():
            # Legacy single-project research
            tech_id = empire.current_research
            if tech_id:
                tech = empire.technologies.get(tech_id)
                if tech:
                    empire.research_points += delta_seconds
                    if empire.research_points >= tech.research_cost:
                        tech.is_researched = True
                        empire.current_research = None
                        empire.research_points = 0

            # Additional concurrent projects
            completed: List[str] = []
            for proj_id, progress in list(empire.research_projects.items()):
                tech = empire.technologies.get(proj_id)
                if not tech:
                    completed.append(proj_id)
                    continue

                progress += delta_seconds
                if progress >= tech.research_cost:
                    tech.is_researched = True
                    completed.append(proj_id)
                else:
                    empire.research_projects[proj_id] = progress

            for proj_id in completed:
                empire.research_projects.pop(proj_id, None)

            # AI-specific behaviors like fleet movement and new research
            # assignment are handled by `_update_ai_empires` via
            # `_process_ai_empire` and should not be duplicated here.

    def _update_colonies(self, delta_seconds: float) -> None:
        """Update population and resource production for all colonies."""
        seconds_per_year = 365.25 * 24 * 3600
        for colony in self.colonies.values():
            # Population growth
            growth = colony.population * (colony.growth_rate / seconds_per_year) * delta_seconds
            colony.population += int(growth)

            # Mining infrastructure produces minerals
            mines = colony.infrastructure.get("mine", 0)
            if mines > 0:
                produced = mines * 10.0 * (delta_seconds / 86400)
                colony.stockpiles["minerals"] = colony.stockpiles.get("minerals", 0.0) + produced

    
    def pause(self) -> None:
        """Pause the game simulation."""
        self.is_paused = True
        logger.info("Game simulation paused")
    
    def resume(self) -> None:
        """Resume the game simulation."""
        self.is_paused = False
        logger.info("Game simulation resumed")
    
    def stop(self) -> None:
        """Stop the game simulation."""
        self.is_running = False
        self.is_paused = False
        logger.info("Game simulation stopped")
    
    def get_empire(self, empire_id: str) -> Optional[Empire]:
        """Get an empire by ID."""
        return self.empires.get(empire_id)
    
    def get_player_empire(self) -> Optional[Empire]:
        """Get the player's empire."""
        for empire in self.empires.values():
            if empire.is_player:
                return empire
        return None
    
    def get_system(self, system_id: str) -> Optional[StarSystem]:
        """Get a star system by ID."""
        return self.star_systems.get(system_id)
    
    def get_fleet(self, fleet_id: str) -> Optional[Fleet]:
        """Get a fleet by ID."""
        return self.fleets.get(fleet_id)

    def jump_fleet(self, fleet_id: str, target_system_id: str) -> bool:
        """Instantly move a fleet through a jump point to another system."""
        fleet = self.fleets.get(fleet_id)
        if not fleet:
            return False

        current_system = self.star_systems.get(fleet.system_id)
        target_system = self.star_systems.get(target_system_id)
        if not current_system or not target_system:
            return False

        connection = next(
            (jp for jp in current_system.jump_points if jp.connects_to == target_system_id),
            None,
        )
        if not connection:
            return False

        fleet.system_id = target_system_id
        fleet.position = Vector3D(**target_system.planets[0].position.model_dump()) if target_system.planets else Vector3D()
        fleet.destination = None
        fleet.estimated_arrival = None
        fleet.status = FleetStatus.IDLE
        return True

    def start_combat(self, attacker_id: str, defender_id: str) -> Optional[str]:
        """Resolve a simple combat between two fleets.

        The fleet with the greater number of ships is declared the winner.

        Args:
            attacker_id: Attacking fleet ID.
            defender_id: Defending fleet ID.

        Returns:
            The winning fleet ID, or ``None`` if combat could not start.
        """
        attacker = self.get_fleet(attacker_id)
        defender = self.get_fleet(defender_id)
        if not attacker or not defender:
            return None

        attacker.status = FleetStatus.IN_COMBAT
        defender.status = FleetStatus.IN_COMBAT

        attacker_strength = len(attacker.ships)
        defender_strength = len(defender.ships)

        winner = attacker if attacker_strength >= defender_strength else defender
        loser = defender if winner is attacker else attacker

        winner.status = FleetStatus.IDLE
        loser.status = FleetStatus.IDLE

        return winner.id
    
    def get_game_state(self) -> Dict[str, Any]:
        """Get the current game state for saving."""
        return {
            "current_time": self.current_time,
            "game_start_time": self.game_start_time.isoformat(),
            "turn_number": self.turn_manager.current_turn,
            "empires": {id: empire.model_dump() for id, empire in self.empires.items()},
            "star_systems": {id: system.model_dump() for id, system in self.star_systems.items()},
            "fleets": {id: fleet.model_dump() for id, fleet in self.fleets.items()},
            "colonies": {id: colony.model_dump() for id, colony in self.colonies.items()},
        }
    
    def load_game_state(self, state: Dict[str, Any]) -> None:
        """Load a game state from saved data."""
        self.current_time = state["current_time"]
        self.game_start_time = datetime.fromisoformat(state["game_start_time"])
        self.turn_manager.current_turn = state.get("turn_number", 0)
        
        # Load empires
        self.empires.clear()
        for empire_id, empire_data in state["empires"].items():
            self.empires[empire_id] = Empire(**empire_data)
        
        # Load star systems
        self.star_systems.clear()
        for system_id, system_data in state["star_systems"].items():
            self.star_systems[system_id] = StarSystem(**system_data)
        
        # Load fleets
        self.fleets.clear()
        for fleet_id, fleet_data in state["fleets"].items():
            self.fleets[fleet_id] = Fleet(**fleet_data)

        # Load colonies
        self.colonies.clear()
        for colony_id, colony_data in state.get("colonies", {}).items():
            self.colonies[colony_id] = Colony(**colony_data)

        # Restore colony links
        for colony in self.colonies.values():
            # Add colony to owning empire
            empire = self.empires.get(colony.empire_id)
            if empire and colony.id not in empire.colonies:
                empire.colonies.append(colony.id)
            for system in self.star_systems.values():
                for planet in system.planets:
                    if planet.id == colony.planet_id:
                        planet.colony_id = colony.id
                        break
        
        # Reinitialize systems
        self._initialize_orbital_mechanics()
        self._schedule_initial_events()

        self.is_running = True
        logger.info("Game state loaded successfully")

    def advance_turn(self) -> None:
        """Advance the game by one turn."""
        if not self.is_running or self.is_paused:
            return
        delta = self.turn_manager.advance_turn()
        self.advance_time(delta)
