from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from pyaurora4x.core.shipyards import Shipyard, BuildOrder, RefitOrder, Slipway, YardType
from pyaurora4x.core.events import EventCategory, EventPriority

class ShipyardManager(BaseModel):
    yards: Dict[str, Shipyard] = Field(default_factory=dict)

    def add_yard(self, yard: Shipyard) -> None:
        self.yards[yard.id] = yard

    def assign_orders(self) -> None:
        for yard in self.yards.values():
            # Try to assign build orders to free slipways
            for order in yard.build_queue:
                if order.assigned_slipway_id or order.paused:
                    continue
                slip = yard.available_slipway(order.hull_tonnage)
                if slip:
                    slip.active_order_id = order.id
                    order.assigned_slipway_id = slip.id
            # Try to assign refit orders to free slipways
            for order in yard.refit_queue:
                if order.assigned_slipway_id or order.paused:
                    continue
                slip = yard.available_slipway(order.hull_tonnage)
                if slip:
                    slip.active_order_id = order.id
                    order.assigned_slipway_id = slip.id

    def tick(self, days: float, now: float, event_manager: Optional[object] = None) -> List[dict]:
        """Advance all yards by a number of days; return completion events."""
        self.assign_orders()
        completed: List[dict] = []
        for yard in self.yards.values():
            capacity = max(0.0, yard.effective_bp_per_day() * days)
            if capacity <= 0:
                continue
            # Process active orders in slipways first (round-robin simple split)
            active_orders: List[BuildOrder | RefitOrder] = []
            id_to_order: Dict[str, BuildOrder | RefitOrder] = {}
            for o in yard.build_queue:
                if o.assigned_slipway_id and not o.paused:
                    active_orders.append(o)
                    id_to_order[o.id] = o
            for o in yard.refit_queue:
                if o.assigned_slipway_id and not o.paused:
                    active_orders.append(o)
                    id_to_order[o.id] = o
            if not active_orders:
                continue
            share = capacity / len(active_orders)
            for o in active_orders:
                need = max(0.0, o.total_bp - o.progress_bp)
                delta = min(share, need)
                if delta <= 0:
                    continue
                o.progress_bp += delta
                if o.progress_bp + 1e-6 >= o.total_bp:
                    # mark complete and free slipway
                    slip: Optional[Slipway] = None
                    if o.assigned_slipway_id:
                        for s in yard.slipways:
                            if s.id == o.assigned_slipway_id:
                                slip = s
                                break
                    if slip:
                        slip.active_order_id = None
                        slip.occupied_until = now
                    completed.append({
                        "yard_id": yard.id,
                        "order_id": o.id,
                        "type": o.__class__.__name__,
                        "time": now,
                    })
                    # Remove from queue after freeing
                    if isinstance(o, BuildOrder):
                        yard.build_queue = [x for x in yard.build_queue if x.id != o.id]
                    else:
                        yard.refit_queue = [x for x in yard.refit_queue if x.id != o.id]
                    if event_manager:
                        # Lazy-format logging rule compliant; event payload
                        event_manager.create_and_post_event(
                            EventCategory.INDUSTRY,
                            EventPriority.NORMAL,
                            "Order Completed: %s",
                            "Shipyard %s completed %s",
                            now,
                            data={
                                "yard_id": yard.id,
                                "order_id": o.id,
                                "order_type": o.__class__.__name__,
                            },
                        )
        # Try to assign newly freed slipways
        self.assign_orders()
        return completed
    
    def create_refit_order(self, ship_id: str, from_design_id: str, to_design_id: str, 
                          hull_tonnage: int, priority: int = 5) -> RefitOrder:
        """Create a refit order for a ship."""
        # Calculate refit cost based on design differences
        refit_cost = self._calculate_refit_cost(from_design_id, to_design_id, hull_tonnage)
        
        order = RefitOrder(
            ship_id=ship_id,
            from_design_id=from_design_id,
            to_design_id=to_design_id,
            hull_tonnage=hull_tonnage,
            total_bp=refit_cost,
            refit_cost_multiplier=1.5,  # Default refit penalty
            components_to_add={},  # Would be populated by design comparison
            components_to_remove={}  # Would be populated by design comparison
        )
        
        return order
    
    def _calculate_refit_cost(self, from_design_id: str, to_design_id: str, hull_tonnage: int) -> float:
        """Calculate the build points required for a refit."""
        # Simplified calculation - in reality would compare ship designs
        # For now, estimate based on tonnage and a refit multiplier
        base_cost = hull_tonnage * 0.1  # Base BP per ton
        refit_penalty = 1.5  # Refits cost 50% more than new builds
        
        return base_cost * refit_penalty
    
    def add_refit_order(self, yard_id: str, refit_order: RefitOrder) -> bool:
        """Add a refit order to a shipyard's queue."""
        yard = self.yards.get(yard_id)
        if not yard:
            return False
        
        yard.refit_queue.append(refit_order)
        
        # Sort by priority (higher priority first)
        yard.refit_queue.sort(key=lambda x: getattr(x, 'priority', 5), reverse=True)
        
        return True
    
    def compare_ship_designs(self, design_a_id: str, design_b_id: str) -> Dict[str, Any]:
        """Compare two ship designs and return differences."""
        # This would integrate with the ship design system
        # For now, return a placeholder comparison
        return {
            "components_different": True,
            "size_change": 0,
            "cost_difference": 100.0,
            "time_estimate_days": 10.0,
            "feasible": True,
            "notes": ["Placeholder comparison - integrate with ship design system"]
        }
    
    def get_yards_by_empire(self, empire_id: str) -> List[Shipyard]:
        """Get all shipyards belonging to a specific empire."""
        return [yard for yard in self.yards.values() if yard.empire_id == empire_id]
    
    def get_yards_by_type(self, yard_type: YardType) -> List[Shipyard]:
        """Get all shipyards of a specific type."""
        return [yard for yard in self.yards.values() if yard.yard_type == yard_type]
    
    def get_empire_total_throughput(self, empire_id: str) -> float:
        """Calculate total build throughput for an empire."""
        empire_yards = self.get_yards_by_empire(empire_id)
        return sum(yard.effective_bp_per_day() for yard in empire_yards)

