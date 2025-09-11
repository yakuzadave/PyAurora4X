"""
Victory Manager Engine for PyAurora 4X

Centralized management of victory conditions, progress tracking,
game end detection, and comprehensive game result generation.
"""

import logging
import math
from typing import Dict, List, Optional, Tuple, Any, Set
from collections import defaultdict

from pyaurora4x.core.models import Empire, StarSystem, Fleet, Technology
from pyaurora4x.core.enums import VictoryCondition, TechnologyType, DiplomaticRelation
from pyaurora4x.core.victory import (
    VictoryProgress, GameEndCondition, VictoryStatistics, GameResult,
    VictoryConditionConfig, VictoryAchievement, get_default_victory_config,
    get_default_achievements
)
from pyaurora4x.core.events import EventManager, EventCategory, EventPriority

logger = logging.getLogger(__name__)


class VictoryManager:
    """Central manager for victory conditions and game end detection."""
    
    def __init__(self, config: Optional[VictoryConditionConfig] = None,
                 event_manager: Optional[EventManager] = None):
        self.config = config or get_default_victory_config()
        self.event_manager = event_manager
        
        # Victory tracking
        self.victory_progress: Dict[str, Dict[VictoryCondition, VictoryProgress]] = {}  # empire_id -> victory_type -> progress
        self.game_end_conditions: List[GameEndCondition] = []
        self.empire_statistics: Dict[str, VictoryStatistics] = {}
        self.achievements: List[VictoryAchievement] = get_default_achievements()
        
        # Game state
        self.game_start_time: float = 0.0
        self.game_end_time: Optional[float] = None
        self.game_active: bool = True
        self.game_result: Optional[GameResult] = None
        
        # Tracking data
        self.empire_scores: Dict[str, float] = defaultdict(float)
        self.empire_rankings: List[Tuple[str, float]] = []  # (empire_id, score)
        
        # Initialize default game end conditions
        self._initialize_default_conditions()
    
    def initialize_game(self, empires: List[Empire], total_systems: int, 
                       game_start_time: float) -> None:
        """Initialize victory tracking for a new game."""
        self.game_start_time = game_start_time
        self.game_active = True
        self.game_result = None
        
        # Initialize victory progress for each empire
        for empire in empires:
            self._initialize_empire_progress(empire, total_systems)
            self._initialize_empire_statistics(empire)
        
        logger.info("Initialized victory tracking for %d empires", len(empires))
    
    def update_victory_progress(self, empires: List[Empire], systems: List[StarSystem],
                              fleets: Dict[str, Fleet], technologies: Dict[str, List[Technology]],
                              current_time: float) -> Optional[GameResult]:
        """Update victory progress and check for game end conditions."""
        if not self.game_active:
            return self.game_result
        
        # Update statistics for all empires
        for empire in empires:
            self._update_empire_statistics(empire, systems, fleets, technologies, current_time)
        
        # Calculate progress for each victory condition
        for empire in empires:
            self._calculate_conquest_progress(empire, systems)
            self._calculate_research_progress(empire, technologies.get(empire.id, []))
            self._calculate_economic_progress(empire, empires)
            self._calculate_diplomatic_progress(empire, empires)
            self._calculate_exploration_progress(empire, systems)
        
        # Check achievements
        self._check_achievements(empires, current_time)
        
        # Check for game end conditions
        game_result = self._check_game_end_conditions(empires, current_time)
        if game_result:
            self.game_active = False
            self.game_end_time = current_time
            self.game_result = game_result
            
            if self.event_manager:
                self.event_manager.create_and_post_event(
                    EventCategory.VICTORY,
                    EventPriority.CRITICAL,
                    f"Game Ended: {game_result.victory_condition.value} Victory",
                    f"Game ended with {game_result.victory_condition.value} victory",
                    current_time,
                    data={"game_result": game_result.model_dump()}
                )
        
        return game_result
    
    def get_victory_status(self, empire_id: str) -> Dict[str, Any]:
        """Get comprehensive victory status for an empire."""
        if empire_id not in self.victory_progress:
            return {"error": "Empire not found"}
        
        progress_data = {}
        for victory_type, progress in self.victory_progress[empire_id].items():
            progress_data[victory_type.value] = {
                "progress": progress.current_progress,
                "current_value": progress.current_value,
                "target_value": progress.target_value,
                "is_achievable": progress.is_achievable,
                "milestones_reached": len(progress.reached_milestones),
                "total_milestones": len(progress.milestones),
                "estimated_completion": progress.estimated_completion_time,
                "details": progress.details
            }
        
        statistics = self.empire_statistics.get(empire_id)
        achievements = [a for a in self.achievements if a.unlocked_by_empire == empire_id]
        
        return {
            "empire_id": empire_id,
            "progress": progress_data,
            "statistics": statistics.model_dump() if statistics else {},
            "achievements": [a.dict() for a in achievements],
            "current_rank": self._get_empire_rank(empire_id),
            "total_score": self.empire_scores.get(empire_id, 0.0)
        }
    
    def get_leaderboard(self) -> List[Dict[str, Any]]:
        """Get current game leaderboard."""
        leaderboard = []
        
        # Sort empires by total score
        sorted_empires = sorted(self.empire_scores.items(), key=lambda x: x[1], reverse=True)
        
        for rank, (empire_id, score) in enumerate(sorted_empires, 1):
            statistics = self.empire_statistics.get(empire_id)
            empire_name = statistics.empire_name if statistics else empire_id
            
            # Get best victory progress
            best_progress = 0.0
            best_victory_type = None
            
            if empire_id in self.victory_progress:
                for victory_type, progress in self.victory_progress[empire_id].items():
                    if progress.current_progress > best_progress:
                        best_progress = progress.current_progress
                        best_victory_type = victory_type
            
            leaderboard.append({
                "rank": rank,
                "empire_id": empire_id,
                "empire_name": empire_name,
                "total_score": score,
                "best_victory_progress": best_progress,
                "best_victory_type": best_victory_type.value if best_victory_type else None,
                "achievements_count": len([a for a in self.achievements if a.unlocked_by_empire == empire_id])
            })
        
        return leaderboard
    
    def force_game_end(self, reason: str, winner_empire_ids: List[str] = None,
                      current_time: float = 0.0) -> GameResult:
        """Force the game to end with a specific reason."""
        self.game_active = False
        self.game_end_time = current_time
        
        game_result = GameResult(
            game_start_time=self.game_start_time,
            game_end_time=current_time,
            total_duration=current_time - self.game_start_time,
            victory_condition=VictoryCondition.CUSTOM,
            game_end_reason=reason,
            winner_empire_ids=winner_empire_ids or [],
            empire_statistics=self.empire_statistics,
            victory_details={"forced_end": True, "reason": reason}
        )
        
        self.game_result = game_result
        return game_result
    
    # Private helper methods
    
    def _initialize_empire_progress(self, empire: Empire, total_systems: int) -> None:
        """Initialize victory progress tracking for an empire."""
        self.victory_progress[empire.id] = {}
        
        for victory_type in VictoryCondition:
            progress = VictoryProgress(
                victory_type=victory_type,
                empire_id=empire.id,
                target_value=self._get_victory_target(victory_type, total_systems)
            )
            
            # Set specific requirements
            progress.requirements = self._get_victory_requirements(victory_type, total_systems)
            progress.completed_requirements = {req: False for req in progress.requirements.keys()}
            
            self.victory_progress[empire.id][victory_type] = progress
    
    def _initialize_empire_statistics(self, empire: Empire) -> None:
        """Initialize statistics tracking for an empire."""
        self.empire_statistics[empire.id] = VictoryStatistics(
            empire_id=empire.id,
            empire_name=empire.name,
            game_start_time=self.game_start_time
        )
    
    def _get_victory_target(self, victory_type: VictoryCondition, total_systems: int) -> float:
        """Get the target value for a victory condition."""
        if victory_type == VictoryCondition.CONQUEST:
            return total_systems * self.config.conquest_percentage
        elif victory_type == VictoryCondition.RESEARCH:
            return self.config.research_trees_required
        elif victory_type == VictoryCondition.ECONOMIC:
            return self.config.economic_gdp_multiplier
        elif victory_type == VictoryCondition.DIPLOMATIC:
            return self.config.diplomatic_alliance_percentage
        elif victory_type == VictoryCondition.EXPLORATION:
            return total_systems * self.config.exploration_percentage
        else:
            return 1.0
    
    def _get_victory_requirements(self, victory_type: VictoryCondition, 
                                total_systems: int) -> Dict[str, Any]:
        """Get specific requirements for a victory condition."""
        if victory_type == VictoryCondition.CONQUEST:
            return {
                "systems_controlled": int(total_systems * self.config.conquest_percentage),
                "maintain_control": True
            }
        elif victory_type == VictoryCondition.RESEARCH:
            return {
                "tech_trees_completed": self.config.research_trees_required,
                "breakthrough_technologies": self.config.research_breakthrough_technologies
            }
        elif victory_type == VictoryCondition.ECONOMIC:
            return {
                "gdp_multiplier": self.config.economic_gdp_multiplier,
                "maintain_duration": self.config.economic_duration_required
            }
        elif victory_type == VictoryCondition.DIPLOMATIC:
            return {
                "alliance_percentage": self.config.diplomatic_alliance_percentage,
                "peace_duration": self.config.diplomatic_peace_duration
            }
        elif victory_type == VictoryCondition.EXPLORATION:
            return {
                "systems_explored": int(total_systems * self.config.exploration_percentage),
                "anomalies_discovered": self.config.exploration_anomalies_discovered
            }
        else:
            return {}
    
    def _calculate_conquest_progress(self, empire: Empire, systems: List[StarSystem]) -> None:
        """Calculate conquest victory progress."""
        if empire.id not in self.victory_progress:
            return
        
        progress = self.victory_progress[empire.id][VictoryCondition.CONQUEST]
        
        # Count systems controlled by this empire
        controlled_systems = len(empire.controlled_systems)
        
        progress.current_value = controlled_systems
        progress.current_progress = min(1.0, controlled_systems / progress.target_value)
        
        # Update details
        progress.details.update({
            "systems_controlled": controlled_systems,
            "target_systems": int(progress.target_value),
            "control_percentage": (controlled_systems / len(systems)) * 100 if systems else 0
        })
        
        # Check milestones
        self._check_progress_milestones(progress)
    
    def _calculate_research_progress(self, empire: Empire, technologies: List[Technology]) -> None:
        """Calculate research victory progress."""
        if empire.id not in self.victory_progress:
            return
        
        progress = self.victory_progress[empire.id][VictoryCondition.RESEARCH]
        
        # Count completed technology trees (simplified - count technologies by type)
        tech_by_type = defaultdict(int)
        for tech in technologies:
            tech_by_type[tech.tech_type] += 1
        
        # Consider a tech tree "completed" if it has 10+ technologies
        completed_trees = len([t for t in tech_by_type.values() if t >= 10])
        
        progress.current_value = completed_trees
        progress.current_progress = min(1.0, completed_trees / progress.target_value)
        
        # Update details
        progress.details.update({
            "tech_trees_completed": completed_trees,
            "target_trees": int(progress.target_value),
            "total_technologies": len(technologies),
            "tech_by_type": dict(tech_by_type)
        })
        
        # Check milestones
        self._check_progress_milestones(progress)
    
    def _calculate_economic_progress(self, empire: Empire, all_empires: List[Empire]) -> None:
        """Calculate economic victory progress."""
        if empire.id not in self.victory_progress:
            return
        
        progress = self.victory_progress[empire.id][VictoryCondition.ECONOMIC]
        
        # Calculate empire's economic strength (simplified)
        empire_gdp = len(empire.colonies) * 1000 + len(empire.fleets) * 500
        
        # Find the next highest GDP
        other_gdps = []
        for other_empire in all_empires:
            if other_empire.id != empire.id:
                other_gdp = len(other_empire.colonies) * 1000 + len(other_empire.fleets) * 500
                other_gdps.append(other_gdp)
        
        if other_gdps:
            max_other_gdp = max(other_gdps)
            if max_other_gdp > 0:
                gdp_ratio = empire_gdp / max_other_gdp
                progress.current_value = gdp_ratio
                progress.current_progress = min(1.0, gdp_ratio / progress.target_value)
            else:
                # All empires have zero GDP - no economic victory possible yet
                progress.current_value = 0.0
                progress.current_progress = 0.0
        else:
            # Only one empire - economic victory requires competition
            progress.current_value = 0.0
            progress.current_progress = 0.0
        
        # Update details
        progress.details.update({
            "empire_gdp": empire_gdp,
            "gdp_ratio": progress.current_value,
            "target_ratio": progress.target_value,
            "colonies": len(empire.colonies),
            "fleets": len(empire.fleets)
        })
        
        # Check milestones
        self._check_progress_milestones(progress)
    
    def _calculate_diplomatic_progress(self, empire: Empire, all_empires: List[Empire]) -> None:
        """Calculate diplomatic victory progress."""
        if empire.id not in self.victory_progress:
            return
        
        progress = self.victory_progress[empire.id][VictoryCondition.DIPLOMATIC]
        
        # Count allied empires (simplified - assume all empires are potential allies)
        allied_empires = 0
        total_other_empires = len(all_empires) - 1  # Exclude self
        
        # This would need to check actual diplomatic relations
        # For now, use a simplified calculation
        if total_other_empires > 0:
            alliance_percentage = allied_empires / total_other_empires
            progress.current_value = alliance_percentage
            progress.current_progress = min(1.0, alliance_percentage / progress.target_value)
        else:
            progress.current_progress = 1.0
        
        # Update details
        progress.details.update({
            "allied_empires": allied_empires,
            "total_empires": total_other_empires,
            "alliance_percentage": progress.current_value * 100,
            "target_percentage": progress.target_value * 100
        })
        
        # Check milestones
        self._check_progress_milestones(progress)
    
    def _calculate_exploration_progress(self, empire: Empire, systems: List[StarSystem]) -> None:
        """Calculate exploration victory progress."""
        if empire.id not in self.victory_progress:
            return
        
        progress = self.victory_progress[empire.id][VictoryCondition.EXPLORATION]
        
        # Count explored systems (systems where empire has knowledge)
        explored_systems = len([s for s in systems if empire.id in getattr(s, 'explored_by', [])])
        
        progress.current_value = explored_systems
        progress.current_progress = min(1.0, explored_systems / progress.target_value)
        
        # Update details
        progress.details.update({
            "systems_explored": explored_systems,
            "target_systems": int(progress.target_value),
            "exploration_percentage": (explored_systems / len(systems)) * 100 if systems else 0,
            "total_systems": len(systems)
        })
        
        # Check milestones
        self._check_progress_milestones(progress)
    
    def _check_progress_milestones(self, progress: VictoryProgress) -> None:
        """Check if progress has reached new milestones."""
        for milestone in progress.milestones:
            if (milestone not in progress.reached_milestones and 
                progress.current_progress >= milestone):
                
                progress.reached_milestones.append(milestone)
                
                if self.event_manager:
                    self.event_manager.create_and_post_event(
                        EventCategory.VICTORY,
                        EventPriority.HIGH,
                        f"Victory Milestone: {progress.victory_type.value} {milestone*100:.0f}%",
                        f"Empire {progress.empire_id} reached {milestone*100:.0f}% progress toward {progress.victory_type.value} victory",
                        0.0,  # timestamp
                        empire_id=progress.empire_id,
                        data={
                            "victory_type": progress.victory_type.value,
                            "milestone": milestone,
                            "progress": progress.current_progress
                        }
                    )
    
    def _update_empire_statistics(self, empire: Empire, systems: List[StarSystem],
                                 fleets: Dict[str, Fleet], technologies: Dict[str, List[Technology]],
                                 current_time: float) -> None:
        """Update comprehensive statistics for an empire."""
        stats = self.empire_statistics[empire.id]
        
        # Update basic stats
        stats.systems_controlled = len(empire.controlled_systems)
        stats.systems_explored = len([s for s in systems if s.discovered_by == empire.id or (isinstance(s.discovered_by, list) and empire.id in s.discovered_by)])
        stats.total_systems = len(systems)
        stats.planets_colonized = len(empire.colonies)
        
        # Update technology stats
        empire_techs = technologies.get(empire.id, [])
        stats.technologies_researched = len(empire_techs)
        
        # Update fleet stats (simplified)
        empire_fleets = [f for f in fleets.values() if f.empire_id == empire.id]
        total_ships = sum(len(f.ships) for f in empire_fleets)
        stats.total_ships_built = max(stats.total_ships_built, total_ships)
        
        # Calculate scores
        stats.total_territory_score = stats.systems_controlled * 100
        stats.military_score = total_ships * 50
        stats.economic_score = stats.planets_colonized * 200
        stats.tech_score = stats.technologies_researched * 25
        
        # Update total score
        stats.total_score = (stats.total_territory_score + stats.military_score + 
                           stats.economic_score + stats.tech_score)
        
        # Update empire score in tracking
        self.empire_scores[empire.id] = stats.total_score
    
    def _check_achievements(self, empires: List[Empire], current_time: float) -> None:
        """Check and unlock achievements for empires."""
        for achievement in self.achievements:
            if achievement.is_unlocked:
                continue
            
            for empire in empires:
                stats = self.empire_statistics.get(empire.id)
                if not stats:
                    continue
                
                if self._check_achievement_requirements(achievement, stats):
                    achievement.is_unlocked = True
                    achievement.unlocked_by_empire = empire.id
                    achievement.unlocked_at_time = current_time
                    
                    # Add to empire's achievement list
                    stats.achievements.append(achievement.achievement_id)
                    
                    if self.event_manager:
                        self.event_manager.create_and_post_event(
                            EventCategory.ACHIEVEMENT,
                            EventPriority.NORMAL,
                            f"Achievement Unlocked: {achievement.name}",
                            f"Empire {empire.id} unlocked achievement: {achievement.name}",
                            current_time,
                            empire_id=empire.id,
                            data={"achievement": achievement.model_dump()}
                        )
    
    def _check_achievement_requirements(self, achievement: VictoryAchievement,
                                      stats: VictoryStatistics) -> bool:
        """Check if an empire meets achievement requirements."""
        for req_key, req_value in achievement.requirements.items():
            stat_value = getattr(stats, req_key, 0)
            
            if isinstance(req_value, bool):
                if not stat_value:
                    return False
            elif stat_value < req_value:
                return False
        
        return True
    
    def _check_game_end_conditions(self, empires: List[Empire], 
                                  current_time: float) -> Optional[GameResult]:
        """Check if any game end conditions are met."""
        # Check victory conditions
        for empire in empires:
            for victory_type, progress in self.victory_progress[empire.id].items():
                if progress.current_progress >= 1.0:
                    return self._create_victory_result(empire, victory_type, current_time)
        
        # Check time limit
        if (self.config.max_game_duration and 
            current_time - self.game_start_time >= self.config.max_game_duration):
            return self._create_time_limit_result(empires, current_time)
        
        # Check custom conditions
        for condition in self.game_end_conditions:
            if condition.is_active and self._evaluate_game_end_condition(condition, empires):
                return self._create_custom_result(condition, current_time)
        
        return None
    
    def _create_victory_result(self, winning_empire: Empire, victory_type: VictoryCondition,
                             current_time: float) -> GameResult:
        """Create a game result for a victory condition."""
        # Calculate final rankings
        sorted_empires = sorted(self.empire_scores.items(), key=lambda x: x[1], reverse=True)
        empire_rankings = [(emp_id, rank+1, score) for rank, (emp_id, score) in enumerate(sorted_empires)]
        
        # Update final statistics
        for stats in self.empire_statistics.values():
            stats.game_end_time = current_time
            stats.total_game_time = current_time - stats.game_start_time
            stats.final_rank = next(rank for emp_id, rank, _ in empire_rankings if emp_id == stats.empire_id)
        
        return GameResult(
            game_start_time=self.game_start_time,
            game_end_time=current_time,
            total_duration=current_time - self.game_start_time,
            victory_condition=victory_type,
            game_end_reason=f"{victory_type.value.title()} Victory",
            winner_empire_ids=[winning_empire.id],
            loser_empire_ids=[emp_id for emp_id in self.empire_statistics.keys() if emp_id != winning_empire.id],
            empire_rankings=empire_rankings,
            empire_statistics=self.empire_statistics,
            victory_details={
                "winning_empire": winning_empire.name,
                "victory_type": victory_type.value,
                "progress": self.victory_progress[winning_empire.id][victory_type].model_dump()
            }
        )
    
    def _create_time_limit_result(self, empires: List[Empire], current_time: float) -> GameResult:
        """Create a game result for time limit reached."""
        # Winner is empire with highest score
        sorted_empires = sorted(self.empire_scores.items(), key=lambda x: x[1], reverse=True)
        winner_id = sorted_empires[0][0] if sorted_empires else None
        
        empire_rankings = [(emp_id, rank+1, score) for rank, (emp_id, score) in enumerate(sorted_empires)]
        
        return GameResult(
            game_start_time=self.game_start_time,
            game_end_time=current_time,
            total_duration=current_time - self.game_start_time,
            victory_condition=VictoryCondition.CUSTOM,
            game_end_reason="Time Limit Reached",
            winner_empire_ids=[winner_id] if winner_id else [],
            empire_rankings=empire_rankings,
            empire_statistics=self.empire_statistics,
            victory_details={"time_limit": True, "max_duration": self.config.max_game_duration}
        )
    
    def _create_custom_result(self, condition: GameEndCondition, current_time: float) -> GameResult:
        """Create a game result for a custom condition."""
        sorted_empires = sorted(self.empire_scores.items(), key=lambda x: x[1], reverse=True)
        empire_rankings = [(emp_id, rank+1, score) for rank, (emp_id, score) in enumerate(sorted_empires)]
        
        return GameResult(
            game_start_time=self.game_start_time,
            game_end_time=current_time,
            total_duration=current_time - self.game_start_time,
            victory_condition=VictoryCondition.CUSTOM,
            game_end_reason=condition.name,
            winner_empire_ids=condition.winning_empires,
            loser_empire_ids=condition.losing_empires,
            empire_rankings=empire_rankings,
            empire_statistics=self.empire_statistics,
            victory_details={"custom_condition": condition.dict()}
        )
    
    def _evaluate_game_end_condition(self, condition: GameEndCondition, 
                                   empires: List[Empire]) -> bool:
        """Evaluate if a custom game end condition is met."""
        # This would contain logic to evaluate custom conditions
        # For now, return False (no custom conditions met)
        return False
    
    def _get_empire_rank(self, empire_id: str) -> int:
        """Get current rank of an empire."""
        sorted_empires = sorted(self.empire_scores.items(), key=lambda x: x[1], reverse=True)
        for rank, (emp_id, _) in enumerate(sorted_empires, 1):
            if emp_id == empire_id:
                return rank
        return len(sorted_empires)
    
    def _initialize_default_conditions(self) -> None:
        """Initialize default game end conditions."""
        # This would set up standard game end conditions
        pass
