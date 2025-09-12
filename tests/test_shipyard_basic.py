"""
Basic shipyard functionality tests to validate core operations.
"""

import pytest
import uuid

from pyaurora4x.core.shipyards import Shipyard, Slipway, BuildOrder, YardType
from pyaurora4x.engine.shipyard_manager import ShipyardManager


class TestBasicShipyardOperations:
    """Test core shipyard functionality without complex dependencies."""
    
    def test_shipyard_creation(self):
        """Test basic shipyard object creation."""
        yard = Shipyard(
            id="test_yard_1",
            empire_id="test_empire",
            name="Test Shipyard",
            yard_type=YardType.COMMERCIAL,
            bp_per_day=50.0,
            slipways=[
                Slipway(id="slip_1", max_hull_tonnage=5000),
                Slipway(id="slip_2", max_hull_tonnage=8000)
            ]
        )
        
        assert yard.id == "test_yard_1"
        assert yard.empire_id == "test_empire"
        assert yard.name == "Test Shipyard"
        assert yard.yard_type == YardType.COMMERCIAL
        assert yard.bp_per_day == 50.0
        assert len(yard.slipways) == 2
        assert yard.build_queue == []
    
    def test_build_order_creation(self):
        """Test creating build orders."""
        order = BuildOrder(
            id=str(uuid.uuid4()),
            design_id="frigate_mk1",
            hull_tonnage=3000,
            total_bp=150.0,
            progress_bp=0.0,
            priority=5
        )
        
        assert order.design_id == "frigate_mk1"
        assert order.hull_tonnage == 3000
        assert order.total_bp == 150.0
        assert order.progress_bp == 0.0
        assert order.priority == 5
        assert order.is_complete() is False
    
    def test_build_order_completion(self):
        """Test build order completion logic."""
        order = BuildOrder(
            id=str(uuid.uuid4()),
            design_id="frigate_mk1",
            hull_tonnage=3000,
            total_bp=150.0,
            progress_bp=150.0  # Complete
        )
        
        assert order.is_complete() is True
        assert order.completion_percentage() == 100.0
    
    def test_shipyard_manager_creation(self):
        """Test shipyard manager initialization."""
        manager = ShipyardManager()
        
        assert len(manager.yards) == 0
    
    def test_shipyard_manager_add_yard(self):
        """Test adding yards to the manager."""
        manager = ShipyardManager()
        
        yard = Shipyard(
            id="managed_yard",
            empire_id="empire_1",
            name="Managed Yard",
            yard_type=YardType.NAVAL,
            bp_per_day=100.0
        )
        
        manager.add_yard(yard)
        
        assert len(manager.yards) == 1
        assert "managed_yard" in manager.yards
        assert manager.yards["managed_yard"] == yard
    
    def test_shipyard_build_queue_management(self):
        """Test adding orders to shipyard build queue."""
        yard = Shipyard(
            id="queue_test_yard",
            empire_id="empire_1",
            name="Queue Test Yard",
            yard_type=YardType.COMMERCIAL,
            bp_per_day=75.0,
            slipways=[Slipway(id="slip_1", max_hull_tonnage=10000)]
        )
        
        # Add build orders
        order1 = BuildOrder(
            id=str(uuid.uuid4()),
            design_id="destroyer_mk1",
            hull_tonnage=5000,
            total_bp=250.0,
            priority=10
        )
        
        order2 = BuildOrder(
            id=str(uuid.uuid4()),
            design_id="cruiser_mk1", 
            hull_tonnage=8000,
            total_bp=400.0,
            priority=8
        )
        
        yard.build_queue.append(order1)
        yard.build_queue.append(order2)
        
        assert len(yard.build_queue) == 2
        assert yard.build_queue[0] == order1
        assert yard.build_queue[1] == order2
    
    def test_slipway_assignment(self):
        """Test assigning build orders to slipways."""
        slipway = Slipway(id="test_slip", max_hull_tonnage=6000)
        order = BuildOrder(
            id=str(uuid.uuid4()),
            design_id="frigate_mk2",
            hull_tonnage=3500,
            total_bp=175.0
        )
        
        # Assign order to slipway
        order.assigned_slipway_id = slipway.id
        slipway.active_order_id = order.id
        
        assert slipway.active_order_id == order.id
        assert order.assigned_slipway_id == slipway.id
        assert slipway.is_occupied()
    
    def test_slipway_capacity_check(self):
        """Test slipway tonnage capacity constraints."""
        slipway = Slipway(id="capacity_test", max_hull_tonnage=5000)
        
        # Order within capacity
        small_order = BuildOrder(
            id=str(uuid.uuid4()),
            design_id="corvette",
            hull_tonnage=2000,
            total_bp=100.0
        )
        
        # Order exceeding capacity  
        large_order = BuildOrder(
            id=str(uuid.uuid4()),
            design_id="battleship",
            hull_tonnage=15000,
            total_bp=750.0
        )
        
        assert slipway.can_build(small_order)
        assert not slipway.can_build(large_order)


class TestShipyardManagerOperations:
    """Test shipyard manager operations with multiple yards."""
    
    @pytest.fixture
    def populated_manager(self):
        """Create a shipyard manager with test yards."""
        manager = ShipyardManager()
        
        # Add test yards for different empires
        yard1 = Shipyard(
            id="empire1_yard1",
            empire_id="empire_1",
            name="Empire 1 Commercial",
            yard_type=YardType.COMMERCIAL,
            bp_per_day=60.0
        )
        
        yard2 = Shipyard(
            id="empire1_yard2", 
            empire_id="empire_1",
            name="Empire 1 Naval",
            yard_type=YardType.NAVAL,
            bp_per_day=120.0
        )
        
        yard3 = Shipyard(
            id="empire2_yard1",
            empire_id="empire_2", 
            name="Empire 2 Commercial",
            yard_type=YardType.COMMERCIAL,
            bp_per_day=80.0
        )
        
        manager.add_yard(yard1)
        manager.add_yard(yard2)
        manager.add_yard(yard3)
        
        return manager
    
    def test_get_yards_by_empire(self, populated_manager):
        """Test filtering yards by empire."""
        empire1_yards = populated_manager.get_yards_by_empire("empire_1")
        empire2_yards = populated_manager.get_yards_by_empire("empire_2")
        
        assert len(empire1_yards) == 2
        assert len(empire2_yards) == 1
        
        # Check correct yards returned
        empire1_ids = {yard.id for yard in empire1_yards}
        assert "empire1_yard1" in empire1_ids
        assert "empire1_yard2" in empire1_ids
        
        assert empire2_yards[0].id == "empire2_yard1"
    
    def test_get_yards_by_type(self, populated_manager):
        """Test filtering yards by type."""
        commercial_yards = populated_manager.get_yards_by_type(YardType.COMMERCIAL)
        naval_yards = populated_manager.get_yards_by_type(YardType.NAVAL)
        
        assert len(commercial_yards) == 2
        assert len(naval_yards) == 1
        
        for yard in commercial_yards:
            assert yard.yard_type == YardType.COMMERCIAL
            
        assert naval_yards[0].yard_type == YardType.NAVAL
    
    def test_total_empire_throughput(self, populated_manager):
        """Test calculating total BP throughput for an empire."""
        empire1_throughput = populated_manager.get_empire_total_throughput("empire_1")
        empire2_throughput = populated_manager.get_empire_total_throughput("empire_2")
        
        # Empire 1 has yards with 60 + 120 = 180 bp_per_day
        assert empire1_throughput == 180.0
        
        # Empire 2 has yard with 80 bp_per_day
        assert empire2_throughput == 80.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
