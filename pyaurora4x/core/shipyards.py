from __future__ import annotations

from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field
import uuid

class YardType(str, Enum):
    NAVAL = "naval"
    COMMERCIAL = "commercial"

class Slipway(BaseModel):
    id: str
    max_hull_tonnage: int
    active_order_id: Optional[str] = None
    occupied_until: Optional[float] = None  # simulation time (seconds)
    
    def is_occupied(self) -> bool:
        """Check if this slipway is currently occupied."""
        return self.active_order_id is not None
    
    def can_build(self, order: 'BuildOrder') -> bool:
        """Check if this slipway can build the given order."""
        return order.hull_tonnage <= self.max_hull_tonnage

class BuildOrder(BaseModel):
    id: str
    design_id: str
    hull_tonnage: int
    total_bp: float  # total build points required
    progress_bp: float = 0.0
    assigned_slipway_id: Optional[str] = None
    paused: bool = False
    priority: int = 5  # Build priority (higher = more urgent)
    
    def is_complete(self) -> bool:
        """Check if this build order is complete."""
        return self.progress_bp >= self.total_bp
    
    def completion_percentage(self) -> float:
        """Get completion percentage."""
        if self.total_bp <= 0:
            return 100.0
        return min(100.0, (self.progress_bp / self.total_bp) * 100.0)

class RefitOrder(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ship_id: str  # Ship being refitted
    from_design_id: str
    to_design_id: str
    hull_tonnage: int
    total_bp: float
    progress_bp: float = 0.0
    assigned_slipway_id: Optional[str] = None
    paused: bool = False
    
    # Refit-specific data
    refit_cost_multiplier: float = 1.5  # Extra cost for refit vs new build
    components_to_add: Dict[str, int] = Field(default_factory=dict)
    components_to_remove: Dict[str, int] = Field(default_factory=dict)
    estimated_time_days: Optional[float] = None

class Shipyard(BaseModel):
    id: str
    empire_id: str
    name: str
    yard_type: YardType

    bp_per_day: float = 0.0  # base build throughput
    tooling_bonus: float = 1.0  # multiplier from tooling/retooling

    slipways: List[Slipway] = Field(default_factory=list)
    build_queue: List[BuildOrder] = Field(default_factory=list)
    refit_queue: List[RefitOrder] = Field(default_factory=list)

    def effective_bp_per_day(self) -> float:
        """Calculate effective Build Points per day including tooling bonus.
        
        Returns:
            float: Effective BP/day (base_bp_per_day × tooling_bonus)
            
        Example:
            ```python
            shipyard.bp_per_day = 1000.0
            shipyard.tooling_bonus = 1.5
            effective_bp = shipyard.effective_bp_per_day()  # 1500.0
            ```
        """
        return max(0.0, self.bp_per_day * self.tooling_bonus)

    def available_slipway(self, tonnage: int) -> Optional[Slipway]:
        """Find first available slipway that can accommodate the specified tonnage.
        
        Args:
            tonnage: Required hull tonnage capacity
            
        Returns:
            Optional[Slipway]: Available slipway or None if none suitable
            
        Example:
            ```python
            slipway = shipyard.available_slipway(tonnage=5000)
            if slipway:
                print(f"Using slipway {slipway.id} (capacity: {slipway.max_hull_tonnage})")
            else:
                print("No available slipways for this ship size")
            ```
        """
        for s in self.slipways:
            if s.active_order_id is None and s.max_hull_tonnage >= tonnage:
                return s
        return None
    
    def upgrade_tooling(self, cost_multiplier: float = 2.0) -> Dict[str, Any]:
        """Calculate cost and time to upgrade shipyard tooling efficiency.
        
        Tooling upgrades improve BP generation by 10% per upgrade, up to 200% maximum.
        Cost scales quadratically with current tooling level.
        
        Args:
            cost_multiplier: Multiplier for upgrade cost (default: 2.0)
            
        Returns:
            Dict[str, Any]: Upgrade information containing:
                - feasible: bool - Whether upgrade is possible
                - current_bonus: float - Current tooling bonus
                - new_bonus: float - Bonus after upgrade
                - cost_bp: float - Total BP cost for upgrade
                - time_days: float - Time to complete upgrade
                - efficiency_gain: float - Percentage improvement
                
        Example:
            ```python
            info = shipyard.upgrade_tooling()
            
            if info["feasible"]:
                print(f"Cost: {info['cost_bp']:,.0f} BP")
                print(f"Time: {info['time_days']:.1f} days")
                print(f"Efficiency gain: {info['efficiency_gain']:.1f}%")
                print(f"New BP/day: {shipyard.bp_per_day * info['new_bonus']:.0f}")
            else:
                print(info["reason"])
            ```
        """
        current_bonus = self.tooling_bonus
        new_bonus = min(current_bonus + 0.1, 2.0)  # Cap at 200% efficiency
        
        if new_bonus <= current_bonus:
            return {"feasible": False, "reason": "Already at maximum tooling"}
        
        # Cost based on yard size and current tooling level
        base_cost = len(self.slipways) * 1000 * cost_multiplier
        tooling_cost = base_cost * (current_bonus ** 2)  # More expensive at higher levels
        
        return {
            "feasible": True,
            "current_bonus": current_bonus,
            "new_bonus": new_bonus,
            "cost_bp": tooling_cost,
            "time_days": tooling_cost / max(1, self.bp_per_day),
            "efficiency_gain": round((new_bonus - current_bonus) / current_bonus * 100, 4)
        }
    
    def add_slipway(self, max_tonnage: int = 10000) -> Dict[str, Any]:
        """Calculate cost and time to add a new slipway."""
        new_slip_id = f"{self.id}_slip_{len(self.slipways) + 1}"
        
        # Cost increases with yard size and slipway capacity
        base_cost = 2000 + (len(self.slipways) * 500)  # More expensive with more slipways
        tonnage_cost = max_tonnage * 0.2  # Cost per ton capacity
        total_cost = base_cost + tonnage_cost
        
        return {
            "feasible": True,
            "new_slipway_id": new_slip_id,
            "max_tonnage": max_tonnage,
            "cost_bp": total_cost,
            "construction_time_days": total_cost / max(1, self.bp_per_day * 0.5),  # Slower for expansion
            "total_slipways_after": len(self.slipways) + 1
        }
    
    def retool_for_design(self, design_id: str, retool_cost_multiplier: float = 0.25) -> Dict[str, Any]:
        """Calculate cost and time to retool shipyard for a specific ship design.
        
        Retooling optimizes the yard for building a particular design, providing
        efficiency bonuses but requiring downtime and resources.
        
        Args:
            design_id: ID of the ship design to retool for
            retool_cost_multiplier: Cost as fraction of 30 days production (default: 0.25)
            
        Returns:
            Dict[str, Any]: Retooling information containing:
                - feasible: bool - Whether retooling is possible
                - design_id: str - Target design
                - retool_cost: float - Total BP cost
                - retool_time_days: float - Downtime required
                - new_tooling_bonus: float - Bonus for target design
                
        Example:
            ```python
            info = shipyard.retool_for_design("battleship_mk2")
            
            if info["feasible"]:
                print(f"Retool cost: {info['retool_cost']:,.0f} BP")
                print(f"Downtime: {info['retool_time_days']:.1f} days")
                print(f"Bonus for {design_id}: {info['new_tooling_bonus']:.1%}")
            ```
            
        Note:
            Retooling is cost-effective when building 3+ ships of the same design.
        """
        # Retooling provides bonus for specific design but reduces general efficiency
        retool_cost = self.bp_per_day * 30 * retool_cost_multiplier  # 30 days of production
        
        return {
            "feasible": True,
            "design_id": design_id,
            "cost_bp": retool_cost,
            "retool_time_days": 15,  # Fixed retooling time
            "design_bonus": 1.25,  # 25% bonus for this specific design
            "general_penalty": 0.95,  # 5% penalty for other designs
            "note": "Retooling optimizes yard for specific design"
        }

