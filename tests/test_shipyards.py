import uuid

from pyaurora4x.core.shipyards import Shipyard, Slipway, BuildOrder, YardType
from pyaurora4x.engine.shipyard_manager import ShipyardManager


def test_build_queue_progression_and_completion():
    # Create a shipyard with 2 slipways and throughput of 100 BP/day
    yard = Shipyard(
        id="yard_1",
        empire_id="empire_0",
        name="Naval Yard Alpha",
        yard_type=YardType.NAVAL,
        bp_per_day=100.0,
        tooling_bonus=1.0,
        slipways=[
            Slipway(id="s1", max_hull_tonnage=20000),
            Slipway(id="s2", max_hull_tonnage=20000),
        ],
    )

    # Two build orders, each requires 200 BP
    o1 = BuildOrder(id=str(uuid.uuid4()), design_id="d1", hull_tonnage=10000, total_bp=200.0)
    o2 = BuildOrder(id=str(uuid.uuid4()), design_id="d2", hull_tonnage=12000, total_bp=200.0)
    yard.build_queue.extend([o1, o2])

    mgr = ShipyardManager()
    mgr.add_yard(yard)

    # Tick for 1 day: 100 BP split between 2 active orders => +50 BP each
    completed = mgr.tick(days=1.0, now=1.0)
    assert len(completed) == 0
    assert o1.progress_bp == 50.0
    assert o2.progress_bp == 50.0
    assert yard.slipways[0].active_order_id is not None
    assert yard.slipways[1].active_order_id is not None

    # Tick for 3 more days: total BP 300 -> each gets +150 => reaches 200 (complete)
    completed = mgr.tick(days=3.0, now=4.0)
    assert len(completed) == 2
    assert o1.progress_bp >= 200.0
    assert o2.progress_bp >= 200.0
    # Slipways freed
    assert yard.slipways[0].active_order_id is None
    assert yard.slipways[1].active_order_id is None

