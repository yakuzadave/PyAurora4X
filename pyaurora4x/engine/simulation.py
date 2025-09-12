"""
Core game simulation engine for PyAurora 4X

Manages the overall game state, time advancement, and coordination
between different game systems.
"""

from typing import Dict, Optional, Any, List, Tuple
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
from pyaurora4x.core.events import EventCategory, EventPriority

from pyaurora4x.core.events import EventManager
from pyaurora4x.engine.scheduler import GameScheduler
from pyaurora4x.engine.star_system import StarSystemGenerator
from pyaurora4x.engine.orbital_mechanics import OrbitalMechanics
from pyaurora4x.engine.turn_manager import GameTurnManager
from pyaurora4x.engine.infrastructure_manager import ColonyInfrastructureManager
from pyaurora4x.engine.jump_point_manager import JumpPointManager
from pyaurora4x.engine.victory_manager import VictoryManager
from pyaurora4x.engine.shipyard_manager import ShipyardManager

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
        self.infrastructure_manager = ColonyInfrastructureManager()
        self.jump_point_manager = JumpPointManager()
        self.victory_manager = VictoryManager(event_manager=self.event_manager)
        self.shipyard_manager = ShipyardManager()
        
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
        # Generate enhanced jump point network
        self.jump_point_manager.generate_enhanced_jump_network(
            list(self.star_systems.values()), connectivity_level=0.25
        )

        # Create player empire
        self._create_player_empire()

        # Create AI empires
        self._create_ai_empires(num_empires - 1)
        
        # Initialize orbital mechanics for all systems
        self._initialize_orbital_mechanics()
        
        # Initialize shipyards for all empires
        self._initialize_empire_shipyards()
        
        # Initialize victory tracking
        self._initialize_victory_tracking()
        
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
        
        # Jump point operations
        self._process_jump_point_operations(delta_seconds)
        
        # Industry: update shipyard throughput and advance queues daily
        if int(self.current_time // 86400) != int(old_time // 86400):
            self._update_shipyard_throughput()
            days = (self.current_time - old_time) / 86400.0
            self.shipyard_manager.tick(days=days, now=self.current_time, event_manager=self.event_manager)

        # Check victory conditions (every 10 seconds of game time to avoid excessive checking)
        if int(self.current_time) % 10 == 0 and int(old_time) % 10 != 0:
            self.check_victory_conditions()
        
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
        
        # Initialize AI jump point knowledge
        self.jump_point_manager.initialize_empire_knowledge(empire.id)
        
        # Process idle fleets with enhanced AI behavior
        for fleet_id in empire.fleets:
            fleet = self.fleets.get(fleet_id)
            if not fleet:
                continue
            
            self._process_ai_fleet_behavior(fleet, empire)
        
        # Strategic AI decisions for exploration and expansion
        self._process_ai_strategic_decisions(empire)

    
    def _process_ai_fleet_behavior(self, fleet: Fleet, empire: Empire) -> None:
        """Process AI behavior for a single fleet."""
        if fleet.status not in [FleetStatus.IDLE, FleetStatus.ORBITING]:
            return  # Fleet is busy
        
        system = self.star_systems.get(fleet.system_id)
        if not system:
            return
        
        # AI decision priorities (in order):
        # 1. Explore unknown systems through jump points (30% chance)
        # 2. Conduct exploration missions in current system (20% chance) 
        # 3. Survey discovered but unmapped jump points (15% chance)
        # 4. Move to planets within system (35% chance - fallback)
        
        decision_roll = random.random()
        
        if decision_roll < 0.30:
            # Try to jump to unexplored systems
            if self._ai_attempt_jump_exploration(fleet, empire):
                return
        
        if decision_roll < 0.50:
            # Start exploration mission in current system
            if self._ai_attempt_system_exploration(fleet, empire):
                return
        
        if decision_roll < 0.65:
            # Survey jump points
            if self._ai_attempt_jump_point_survey(fleet, empire):
                return
        
        # Fallback: Move within system
        self._ai_move_within_system(fleet, system)
    
    def _ai_attempt_jump_exploration(self, fleet: Fleet, empire: Empire) -> bool:
        """AI attempts to jump to unexplored systems."""
        available_jumps = self.get_available_jumps(fleet.id)
        
        if not available_jumps:
            return False
        
        # Filter for accessible and unexplored targets
        viable_jumps = []
        for jump_info in available_jumps:
            if not jump_info.get("can_jump"):
                continue
            
            target_system_id = jump_info.get("target_system_id")
            target_system = self.star_systems.get(target_system_id)
            
            if target_system and not target_system.is_explored:
                # Prefer systems with lower exploration status
                exploration_status = jump_info.get("target_exploration_status", {})
                exploration_progress = exploration_status.get("exploration_progress", 0.0)
                
                # Weight by unexplored potential (lower progress = higher weight)
                weight = max(0.1, 1.0 - exploration_progress)
                viable_jumps.append((jump_info, weight))
        
        if not viable_jumps:
            return False
        
        # Choose jump point with weighted random selection
        total_weight = sum(weight for _, weight in viable_jumps)
        if total_weight == 0:
            return False
        
        roll = random.uniform(0, total_weight)
        cumulative_weight = 0
        
        for jump_info, weight in viable_jumps:
            cumulative_weight += weight
            if roll <= cumulative_weight:
                # Attempt the jump
                jump_point_id = jump_info.get("jump_point_id")
                success, message = self.initiate_fleet_jump(fleet.id, jump_point_id)
                if success:
                    logger.info(
                        f"AI fleet {fleet.name} jumping to {jump_info.get('target_system_name', 'unknown system')}"
                    )
                    return True
                break
        
        return False
    
    def _ai_attempt_system_exploration(self, fleet: Fleet, empire: Empire) -> bool:
        """AI attempts to start exploration mission in current system."""
        system = self.star_systems.get(fleet.system_id)
        if not system:
            return False
        
        # Check if system needs exploration
        exploration_status = self.get_system_exploration_status(system.id, empire.id)
        exploration_progress = exploration_status.get("exploration_progress", 0.0)
        survey_completeness = exploration_status.get("survey_completeness", 0.0)
        
        # Don't explore if system is already well explored
        if exploration_progress > 0.8 and survey_completeness > 0.8:
            return False
        
        # Choose mission type based on current status
        if survey_completeness < 0.5:
            mission_type = "survey"
        else:
            mission_type = "explore"
        
        success, message = self.start_fleet_exploration(fleet.id, mission_type)
        if success:
            logger.info(f"AI fleet {fleet.name} starting {mission_type} mission in {system.name}")
            return True
        
        return False
    
    def _ai_attempt_jump_point_survey(self, fleet: Fleet, empire: Empire) -> bool:
        """AI attempts to survey discovered but unmapped jump points."""
        system = self.star_systems.get(fleet.system_id)
        if not system:
            return False
        
        # Find jump points that need surveying
        surveyable_points = []
        for jump_point in system.jump_points:
            if (jump_point.is_accessible_by(empire.id) and
                jump_point.survey_level < 3 and
                jump_point.survey_level > 0):  # Detected but not fully surveyed
                surveyable_points.append(jump_point)
        
        if not surveyable_points:
            return False
        
        # Choose a random jump point to survey
        jump_point = random.choice(surveyable_points)
        success, message = self.survey_jump_point(fleet.id, jump_point.id)
        
        if success:
            logger.info(f"AI fleet {fleet.name} surveying jump point {jump_point.name}")
            return True
        
        return False
    
    def _ai_move_within_system(self, fleet: Fleet, system: StarSystem) -> None:
        """AI fallback: move fleet to a planet within the system."""
        if not system.planets:
            return
        
        target = random.choice(system.planets)
        transfer = self.orbital_mechanics.calculate_transfer_orbit(
            fleet.position, target.position, system.star_mass
        )
        fleet.destination = target.position.copy()
        fleet.estimated_arrival = self.current_time + transfer["transfer_time"]
        order = f"Transfer to {target.name} via {transfer['transfer_type']}"
        fleet.current_orders.append(order)
        fleet.status = FleetStatus.IN_TRANSIT
        
        logger.debug(
            f"AI fleet {fleet.name} transferring to {target.name} (ETA {transfer['transfer_time']}s)"
        )
    
    def _process_ai_strategic_decisions(self, empire: Empire) -> None:
        """Process high-level strategic AI decisions for the empire."""
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
        
        # Strategic expansion decisions could be added here:
        # - Decide whether to colonize discovered systems
        # - Plan long-term exploration routes
        # - Coordinate multiple fleets for exploration
        # - Build additional exploration fleets

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
    
    def _process_jump_point_operations(self, delta_seconds: float) -> None:
        """Process jump point exploration, travel, and discovery operations."""
        # Update jump point network
        self.jump_point_manager.update_network(self.star_systems)
        
        # Process all jump point operations
        results = self.jump_point_manager.process_turn_update(
            self.fleets, self.star_systems, {}, self.current_time, delta_seconds
        )
        
        # Log significant discoveries
        for discovery in results.get("discoveries", []):
            if discovery["type"] == "jump_point_detection":
                fleet_name = self.fleets.get(discovery["fleet_id"], {}).get("name", "Unknown Fleet")
                system_name = self.star_systems.get(discovery["system_id"], {}).get("name", "Unknown System")
                logger.info(
                    "Fleet %s discovered %d jump points in system %s", 
                    fleet_name, len(discovery["jump_points"]), system_name
                )

    def _update_colonies(self, delta_seconds: float) -> None:
        """Update population, resource production, and construction for all colonies."""
        seconds_per_year = 365.25 * 24 * 3600
        
        for colony in self.colonies.values():
            # Initialize infrastructure if needed
            if colony.id not in self.infrastructure_manager.colony_states:
                self.infrastructure_manager.initialize_colony_infrastructure(colony)
            
            # Population growth (capped by max population)
            growth = colony.population * (colony.growth_rate / seconds_per_year) * delta_seconds
            colony.population = min(colony.max_population, colony.population + int(growth))
            
            # Process construction projects
            empire = self.empires.get(colony.empire_id)
            if empire:
                self.infrastructure_manager.process_construction(colony, empire, delta_seconds)
            
            # Apply daily resource production from buildings
            state = self.infrastructure_manager.get_colony_state(colony.id)
            if state:
                # Convert daily rates to per-second and apply
                seconds_per_day = 86400.0
                
                for resource, daily_amount in state.net_production.items():
                    per_second_amount = daily_amount / seconds_per_day
                    resource_change = per_second_amount * delta_seconds
                    colony.stockpiles[resource] = max(0, colony.stockpiles.get(resource, 0.0) + resource_change)

    
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
    
    def get_infrastructure_manager(self) -> ColonyInfrastructureManager:
        """Get the colony infrastructure manager."""
        return self.infrastructure_manager
    
    def get_colony(self, colony_id: str) -> Optional[Colony]:
        """Get a colony by ID."""
        return self.colonies.get(colony_id)

    def jump_fleet(self, fleet_id: str, target_system_id: str) -> bool:
        """Instantly move a fleet through a jump point to another system (legacy method)."""
        # Find the jump point to use
        fleet = self.fleets.get(fleet_id)
        if not fleet:
            return False

        current_system = self.star_systems.get(fleet.system_id)
        if not current_system:
            return False

        jump_point = next(
            (jp for jp in current_system.jump_points if jp.connects_to == target_system_id),
            None,
        )
        if not jump_point:
            return False

        # Use the enhanced jump system for proper preparation and execution
        success, message = self.jump_point_manager.initiate_fleet_jump(
            fleet, jump_point.id, self.star_systems, {}, {}, self.current_time
        )
        
        return success
    
    def initiate_fleet_jump(self, fleet_id: str, jump_point_id: str) -> Tuple[bool, str]:
        """Initiate a jump for a fleet through a specific jump point."""
        fleet = self.fleets.get(fleet_id)
        if not fleet:
            return False, "Fleet not found"
        
        return self.jump_point_manager.initiate_fleet_jump(
            fleet, jump_point_id, self.star_systems, {}, {}, self.current_time
        )
    
    def start_fleet_exploration(self, fleet_id: str, mission_type: str = "explore") -> Tuple[bool, str]:
        """Start an exploration mission for a fleet."""
        fleet = self.fleets.get(fleet_id)
        if not fleet:
            return False, "Fleet not found"
        
        system = self.star_systems.get(fleet.system_id)
        if not system:
            return False, "Fleet system not found"
        
        return self.jump_point_manager.start_exploration_mission(
            fleet, system, mission_type, self.current_time
        )
    
    def survey_jump_point(self, fleet_id: str, jump_point_id: str) -> Tuple[bool, str]:
        """Start a survey mission for a specific jump point."""
        fleet = self.fleets.get(fleet_id)
        if not fleet:
            return False, "Fleet not found"
        
        return self.jump_point_manager.survey_jump_point(
            fleet, jump_point_id, self.star_systems, self.current_time
        )
    
    def get_available_jumps(self, fleet_id: str) -> List[Dict[str, Any]]:
        """Get available jump options for a fleet."""
        fleet = self.fleets.get(fleet_id)
        if not fleet:
            return []
        
        return self.jump_point_manager.get_available_jumps_for_fleet(
            fleet, self.star_systems, {}, {}
        )
    
    def get_fleet_jump_status(self, fleet_id: str) -> Dict[str, Any]:
        """Get current jump status for a fleet."""
        return self.jump_point_manager.get_fleet_jump_status(fleet_id)
    
    def cancel_fleet_jump(self, fleet_id: str) -> Tuple[bool, str]:
        """Cancel an active jump operation for a fleet."""
        return self.jump_point_manager.cancel_fleet_jump(fleet_id)
    
    def get_system_exploration_status(self, system_id: str, empire_id: str) -> Dict[str, Any]:
        """Get exploration status for a system."""
        return self.jump_point_manager.get_system_exploration_status(system_id, empire_id)
    
    def get_empire_jump_network(self, empire_id: str) -> Dict[str, Any]:
        """Get the jump network as known by a specific empire."""
        return self.jump_point_manager.get_empire_jump_network(empire_id, self.star_systems)
    
    def get_jump_point_manager(self) -> "JumpPointManager":
        """Get the jump point manager for direct access."""
        return self.jump_point_manager

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
            "shipyards": {id: yard.model_dump() for id, yard in self.shipyard_manager.yards.items()},
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

        # Load shipyards
        self.shipyard_manager = ShipyardManager()
        for yard_id, yard_data in state.get("shipyards", {}).items():
            from pyaurora4x.core.shipyards import Shipyard
            self.shipyard_manager.yards[yard_id] = Shipyard(**yard_data)

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
        self._initialize_victory_tracking()
        self._schedule_initial_events()

        self.is_running = True
        logger.info("Game state loaded successfully")

    def advance_turn(self) -> None:
        """Advance the game by one turn."""
        if not self.is_running or self.is_paused:
            return
        delta = self.turn_manager.advance_turn()
        self.advance_time(delta)
    
    def _initialize_victory_tracking(self) -> None:
        """Initialize victory tracking for all empires."""
        empires = list(self.empires.values())
        total_systems = len(self.star_systems)
        
        self.victory_manager.initialize_game(
            empires=empires,
            total_systems=total_systems,
            game_start_time=self.current_time
        )
        
        logger.info("Victory tracking initialized for %d empires", len(empires))
    
    def _initialize_empire_shipyards(self) -> None:
        """Create initial shipyards for all empires."""
        from pyaurora4x.core.shipyards import Shipyard, Slipway, YardType
        
        for empire in self.empires.values():
            # Create a basic commercial shipyard for each empire
            yard = Shipyard(
                id=f"{empire.id}_starter_yard",
                empire_id=empire.id,
                name=f"{empire.name} Starter Shipyard",
                yard_type=YardType.COMMERCIAL,
                bp_per_day=50.0,  # Basic throughput
                tooling_bonus=1.0,
                slipways=[
                    Slipway(id=f"{empire.id}_slip_1", max_hull_tonnage=5000),
                    Slipway(id=f"{empire.id}_slip_2", max_hull_tonnage=5000) if empire.is_player else Slipway(id=f"{empire.id}_slip_1_ai", max_hull_tonnage=3000),
                ]
            )
            
            self.shipyard_manager.add_yard(yard)
            logger.info("Created starter shipyard for %s with %d slipways", empire.name, len(yard.slipways))
    
    def _update_shipyard_throughput(self) -> None:
        """Update build points per day for all shipyards based on available industry."""
        for yard in self.shipyard_manager.yards.values():
            empire = self.empires.get(yard.empire_id)
            if not empire:
                continue
            
            # Calculate base throughput from factories and infrastructure
            base_bp = self._calculate_empire_industrial_capacity(empire)
            
            # Apply technology bonuses
            tech_multiplier = self._calculate_construction_tech_bonus(empire)
            
            # Distribute capacity among empire's yards (simple equal split for now)
            empire_yards = [y for y in self.shipyard_manager.yards.values() if y.empire_id == empire.id]
            yard_share = base_bp / max(1, len(empire_yards))
            
            # Update the yard's base throughput
            yard.bp_per_day = yard_share * tech_multiplier
    
    def _calculate_empire_industrial_capacity(self, empire: Empire) -> float:
        """Calculate an empire's total industrial capacity for shipbuilding."""
        total_capacity = 0.0
        
        # Base capacity from colonies
        for colony_id in empire.colonies:
            colony = self.colonies.get(colony_id)
            if not colony:
                continue
            
            # Get infrastructure state if available
            if hasattr(self, 'infrastructure_manager'):
                state = self.infrastructure_manager.get_colony_state(colony_id)
                if state:
                    # Count construction-related buildings
                    factory_count = 0
                    for building_id, building in state.buildings.items():
                        template = self.infrastructure_manager.building_templates.get(building.template_id)
                        if template and 'factory' in template.id.lower():
                            factory_count += 1
                    
                    # Each factory contributes to shipyard capacity
                    total_capacity += factory_count * 10.0
            
            # Fallback: use legacy infrastructure
            if colony.infrastructure:
                factory_count = colony.infrastructure.get('factory', 0)
                total_capacity += factory_count * 10.0
            
            # Base colony contribution (minimum capacity)
            total_capacity += 20.0  # Each colony provides some basic capacity
        
        return max(50.0, total_capacity)  # Minimum capacity for any empire
    
    def _calculate_construction_tech_bonus(self, empire: Empire) -> float:
        """Calculate technology bonus multiplier for construction."""
        multiplier = 1.0
        
        # Check for construction-related technologies
        construction_techs = [
            'automated_construction',
            'nano_construction', 
            'orbital_shipyards',
            'advanced_materials'
        ]
        
        for tech_id in construction_techs:
            tech = empire.technologies.get(tech_id)
            if tech and tech.is_researched:
                multiplier += 0.15  # 15% bonus per relevant tech
        
        return multiplier
    
    def check_victory_conditions(self) -> bool:
        """Check victory conditions and handle game end if needed."""
        if not self.is_running:
            return True
        
        # Prepare data for victory checking
        empires = list(self.empires.values())
        systems = list(self.star_systems.values())
        technologies = {}
        
        # Collect technology data for each empire
        for empire in empires:
            empire_techs = [tech for tech in empire.technologies.values() if tech.is_researched]
            technologies[empire.id] = empire_techs
        
        # Update victory progress and check for game end
        game_result = self.victory_manager.update_victory_progress(
            empires=empires,
            systems=systems,
            fleets=self.fleets,
            technologies=technologies,
            current_time=self.current_time
        )
        
        if game_result:
            self._handle_game_end(game_result)
            return True
        
        return False
    
    def _handle_game_end(self, game_result) -> None:
        """Handle game end with victory result."""
        self.is_running = False
        
        logger.info("Game ended: %s", game_result.game_end_reason)
        
        # Emit game end event
        self.event_manager.create_and_post_event(
            EventCategory.SYSTEM,
            EventPriority.HIGH,
            f"Game Ended: {game_result.game_end_reason}",
            f"Game ended: {game_result.game_end_reason}",
            self.current_time,
            data={
                "game_result": game_result.model_dump(),
                "winner_empires": game_result.winner_empire_ids,
                "total_duration": game_result.total_duration
            }
        )
    
    def get_victory_status(self, empire_id: str = None) -> Dict[str, Any]:
        """Get victory status for an empire or all empires."""
        if empire_id:
            return self.victory_manager.get_victory_status(empire_id)
        else:
            return {
                "leaderboard": self.victory_manager.get_leaderboard(),
                "game_active": self.victory_manager.game_active,
                "game_result": self.victory_manager.game_result.dict() if self.victory_manager.game_result else None
            }
    
    def force_game_end(self, reason: str, winner_empire_ids: List[str] = None) -> None:
        """Force the game to end with a specific reason."""
        game_result = self.victory_manager.force_game_end(
            reason=reason,
            winner_empire_ids=winner_empire_ids or [],
            current_time=self.current_time
        )
        self._handle_game_end(game_result)
