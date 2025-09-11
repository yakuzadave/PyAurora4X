"""
Victory Conditions and Game End System for PyAurora 4X

Defines victory conditions, progress tracking, game end detection,
and comprehensive game statistics for determining winners.
"""

from typing import Dict, List, Optional, Any, Union, Tuple
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
from enum import Enum

from pyaurora4x.core.enums import VictoryCondition, TechnologyType, DiplomaticRelation
from pyaurora4x.core.models import Vector3D


class VictoryProgress(BaseModel):
    """Tracks progress toward a specific victory condition."""
    
    victory_type: VictoryCondition
    empire_id: str
    
    # Progress tracking
    current_progress: float = 0.0  # 0.0 to 1.0
    target_value: float = 1.0
    current_value: float = 0.0
    
    # Victory requirements
    requirements: Dict[str, Any] = Field(default_factory=dict)
    completed_requirements: Dict[str, bool] = Field(default_factory=dict)
    
    # Progress milestones
    milestones: List[float] = Field(default_factory=lambda: [0.25, 0.5, 0.75, 0.9])
    reached_milestones: List[float] = Field(default_factory=list)
    
    # Status
    is_achievable: bool = True
    last_progress_update: float = 0.0
    estimated_completion_time: Optional[float] = None
    
    # Additional data
    details: Dict[str, Any] = Field(default_factory=dict)
    progress_history: List[Tuple[float, float]] = Field(default_factory=list)  # (time, progress)


class GameEndCondition(BaseModel):
    """Defines conditions that can end the game."""
    
    condition_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    
    # Condition type
    condition_type: str  # "victory", "defeat", "draw", "time_limit", "special"
    
    # Trigger conditions
    trigger_requirements: Dict[str, Any] = Field(default_factory=dict)
    
    # Results
    winning_empires: List[str] = Field(default_factory=list)
    losing_empires: List[str] = Field(default_factory=list)
    
    # Status
    is_active: bool = True
    is_met: bool = False
    met_at_time: Optional[float] = None
    
    # Priority (higher number = higher priority)
    priority: int = 100


class VictoryStatistics(BaseModel):
    """Comprehensive statistics for victory analysis."""
    
    empire_id: str
    empire_name: str
    
    # General statistics
    game_start_time: float = 0.0
    game_end_time: Optional[float] = None
    total_game_time: float = 0.0
    
    # Territory and exploration
    systems_controlled: int = 0
    systems_explored: int = 0
    total_systems: int = 0
    planets_colonized: int = 0
    total_territory_score: float = 0.0
    
    # Military statistics
    total_ships_built: int = 0
    total_ships_lost: int = 0
    battles_won: int = 0
    battles_lost: int = 0
    enemy_ships_destroyed: int = 0
    military_score: float = 0.0
    
    # Economic statistics
    total_minerals_mined: float = 0.0
    total_energy_generated: float = 0.0
    total_research_points: float = 0.0
    peak_population: int = 0
    economic_score: float = 0.0
    
    # Technological progress
    technologies_researched: int = 0
    total_tech_trees: int = 0
    advanced_technologies: List[str] = Field(default_factory=list)
    tech_score: float = 0.0
    
    # Diplomatic achievements
    treaties_signed: int = 0
    alliances_formed: int = 0
    wars_declared: int = 0
    diplomatic_score: float = 0.0
    
    # Special achievements
    achievements: List[str] = Field(default_factory=list)
    special_events: List[str] = Field(default_factory=list)
    
    # Final scores
    total_score: float = 0.0
    victory_points: float = 0.0
    final_rank: Optional[int] = None


class GameResult(BaseModel):
    """Represents the final result of a completed game."""
    
    game_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Game information
    game_start_time: float
    game_end_time: float
    total_duration: float
    
    # Victory information
    victory_condition: VictoryCondition
    game_end_reason: str
    
    # Results
    winner_empire_ids: List[str] = Field(default_factory=list)
    loser_empire_ids: List[str] = Field(default_factory=list)
    
    # Empire rankings
    empire_rankings: List[Tuple[str, int, float]] = Field(default_factory=list)  # (empire_id, rank, score)
    
    # Statistics for all empires
    empire_statistics: Dict[str, VictoryStatistics] = Field(default_factory=dict)
    
    # Game metadata
    difficulty_level: str = "normal"
    galaxy_size: str = "medium"
    total_empires: int = 0
    human_empires: List[str] = Field(default_factory=list)
    ai_empires: List[str] = Field(default_factory=list)
    
    # Victory details
    victory_details: Dict[str, Any] = Field(default_factory=dict)
    decisive_moments: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Performance metrics
    game_performance: Dict[str, float] = Field(default_factory=dict)


class VictoryConditionConfig(BaseModel):
    """Configuration for victory condition requirements."""
    
    # Conquest victory
    conquest_percentage: float = 0.75  # Control 75% of galaxy
    conquest_systems_required: Optional[int] = None  # Alternative: specific number
    
    # Research victory
    research_trees_required: int = 5  # Complete 5 tech trees
    research_breakthrough_technologies: List[TechnologyType] = Field(default_factory=list)
    research_total_points: Optional[float] = None  # Alternative: total research points
    
    # Economic victory
    economic_gdp_multiplier: float = 3.0  # 3x the GDP of next rival
    economic_total_score: Optional[float] = None  # Alternative: absolute score
    economic_duration_required: float = 50.0  # Maintain lead for 50 years
    
    # Diplomatic victory
    diplomatic_alliance_percentage: float = 0.8  # 80% of empires in alliance
    diplomatic_peace_duration: float = 100.0  # 100 years of galactic peace
    diplomatic_federation_control: bool = True  # Control galactic federation
    
    # Exploration victory
    exploration_percentage: float = 0.95  # Explore 95% of galaxy
    exploration_anomalies_discovered: int = 50  # Discover 50 special anomalies
    exploration_first_contact: int = 10  # First contact with 10 alien species
    
    # Time limits
    max_game_duration: Optional[float] = None  # Maximum game time in years
    early_victory_bonus: float = 1.2  # Bonus for early victories
    
    # Custom conditions
    custom_conditions: List[Dict[str, Any]] = Field(default_factory=list)


def get_default_victory_config() -> VictoryConditionConfig:
    """Get default victory condition configuration."""
    return VictoryConditionConfig(
        conquest_percentage=0.75,
        research_trees_required=5,
        research_breakthrough_technologies=[
            TechnologyType.PHYSICS, TechnologyType.ENGINEERING, 
            TechnologyType.BIOLOGY, TechnologyType.COMPUTING
        ],
        economic_gdp_multiplier=2.5,
        economic_duration_required=50.0,
        diplomatic_alliance_percentage=0.8,
        diplomatic_peace_duration=100.0,
        exploration_percentage=0.95,
        exploration_anomalies_discovered=25,
        max_game_duration=500.0  # 500 year limit
    )


class VictoryAchievement(BaseModel):
    """Represents a special achievement or milestone."""
    
    achievement_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    category: str  # "military", "economic", "scientific", "diplomatic", "exploration"
    
    # Requirements
    requirements: Dict[str, Any] = Field(default_factory=dict)
    
    # Achievement data
    points_value: float = 10.0
    rarity: str = "common"  # "common", "uncommon", "rare", "legendary"
    
    # Status
    is_unlocked: bool = False
    unlocked_by_empire: Optional[str] = None
    unlocked_at_time: Optional[float] = None
    
    # Display
    icon: str = "🏆"
    hidden_until_unlocked: bool = False


def get_default_achievements() -> List[VictoryAchievement]:
    """Get list of default achievements."""
    return [
        # Military achievements
        VictoryAchievement(
            name="First Blood",
            description="Destroy your first enemy ship",
            category="military",
            requirements={"enemy_ships_destroyed": 1},
            points_value=5.0,
            rarity="common",
            icon="⚔️"
        ),
        VictoryAchievement(
            name="Admiral",
            description="Win 10 battles",
            category="military",
            requirements={"battles_won": 10},
            points_value=25.0,
            rarity="uncommon",
            icon="🎖️"
        ),
        VictoryAchievement(
            name="Fleet Destroyer",
            description="Destroy 100 enemy ships",
            category="military",
            requirements={"enemy_ships_destroyed": 100},
            points_value=50.0,
            rarity="rare",
            icon="💥"
        ),
        
        # Economic achievements
        VictoryAchievement(
            name="Entrepreneur",
            description="Build your first colony",
            category="economic",
            requirements={"planets_colonized": 1},
            points_value=10.0,
            rarity="common",
            icon="🏗️"
        ),
        VictoryAchievement(
            name="Empire Builder",
            description="Control 25 systems",
            category="economic",
            requirements={"systems_controlled": 25},
            points_value=30.0,
            rarity="uncommon",
            icon="🌟"
        ),
        
        # Scientific achievements
        VictoryAchievement(
            name="Researcher",
            description="Complete your first technology",
            category="scientific",
            requirements={"technologies_researched": 1},
            points_value=5.0,
            rarity="common",
            icon="🔬"
        ),
        VictoryAchievement(
            name="Breakthrough",
            description="Complete an entire technology tree",
            category="scientific",
            requirements={"tech_trees_completed": 1},
            points_value=40.0,
            rarity="rare",
            icon="🧬"
        ),
        
        # Exploration achievements
        VictoryAchievement(
            name="Explorer",
            description="Explore 10 systems",
            category="exploration",
            requirements={"systems_explored": 10},
            points_value=15.0,
            rarity="common",
            icon="🚀"
        ),
        VictoryAchievement(
            name="Pathfinder",
            description="Discover 5 jump points",
            category="exploration",
            requirements={"jump_points_discovered": 5},
            points_value=20.0,
            rarity="uncommon",
            icon="🌌"
        ),
        
        # Diplomatic achievements
        VictoryAchievement(
            name="Diplomat",
            description="Sign your first treaty",
            category="diplomatic",
            requirements={"treaties_signed": 1},
            points_value=10.0,
            rarity="common",
            icon="🤝"
        ),
        VictoryAchievement(
            name="Peacemaker",
            description="Maintain peace for 50 years",
            category="diplomatic",
            requirements={"peaceful_years": 50},
            points_value=35.0,
            rarity="rare",
            icon="🕊️"
        ),
        
        # Special achievements
        VictoryAchievement(
            name="Speed Runner",
            description="Win a game in under 100 years",
            category="special",
            requirements={"victory_time": 100},
            points_value=100.0,
            rarity="legendary",
            icon="⚡"
        ),
        VictoryAchievement(
            name="Survivor",
            description="Win after losing your home system",
            category="special",
            requirements={"home_system_lost": True, "victory": True},
            points_value=75.0,
            rarity="legendary",
            icon="💪"
        ),
    ]
