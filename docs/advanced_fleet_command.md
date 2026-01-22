# Advanced Fleet Command Guide

**Version:** 1.0  
**Last Updated:** 2026-01-22

---

## Table of Contents

1. [Overview](#overview)
2. [Fleet Command Basics](#fleet-command-basics)
3. [Order System](#order-system)
4. [Formation Mechanics](#formation-mechanics)
5. [Combat Operations](#combat-operations)
6. [Logistics Management](#logistics-management)
7. [Practical Examples](#practical-examples)
8. [Advanced Tactics](#advanced-tactics)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The Advanced Fleet Command System provides comprehensive tactical control over your fleets beyond basic movement and positioning. It includes:

- **Order Management:** Priority-based command queue for complex operations
- **Formations:** Tactical ship arrangements with bonuses
- **Combat Resolution:** Detailed battle mechanics with experience and morale
- **Logistics:** Fuel, supplies, and maintenance tracking

This system is accessed through the `FleetCommandManager` class in the game engine.

---

## Fleet Command Basics

### Initializing Fleet Command

Before issuing orders, a fleet must be initialized with the command system:

```python
from pyaurora4x.engine.fleet_command_manager import FleetCommandManager

manager = FleetCommandManager()
fleet = empire.get_fleet("fleet_1")
command_state = manager.initialize_fleet_command(fleet, empire)
```

**What Happens During Initialization:**
1. Fleet command state is created
2. Combat capabilities are calculated from ship loadouts
3. Logistics requirements are determined
4. Formation templates are made available
5. Order queue is prepared

### Checking Fleet Status

Get comprehensive status information at any time:

```python
status = manager.get_fleet_tactical_status("fleet_1")

print(f"Command Effectiveness: {status['command_effectiveness']:.1%}")
print(f"Active Orders: {status['current_orders']}")
print(f"In Combat: {status['combat']['in_combat']}")
print(f"Fuel: {status['logistics']['fuel_status']:.1%}")
```

---

## Order System

### Order Types

PyAurora4X supports the following order types:

| Order Type | Description | Key Parameters |
|------------|-------------|----------------|
| `MOVE_TO` | Move fleet to coordinates | `target_position`, `speed` |
| `ATTACK` | Engage enemy fleet | `target_fleet_id` |
| `DEFEND` | Defend location/asset | `target_position`, `defend_radius` |
| `PATROL` | Patrol between waypoints | `waypoints`, `patrol_speed` |
| `ESCORT` | Escort friendly fleet | `target_fleet_id` |
| `FORM_UP` | Form tactical formation | `formation_template_id` |
| `CHANGE_FORMATION` | Switch formations | `new_formation_id` |
| `SURVEY` | Survey system/planet | `target_system_id` |
| `REFUEL` | Refuel at station | `target_planet_id` |
| `REPAIR` | Repair damage | `target_planet_id` |
| `RESUPPLY` | Resupply ammunition | `target_planet_id` |

### Order Priorities

Orders are processed in priority order:

- **EMERGENCY**: Emergency orders, process immediately
- **HIGH**: Important tactical orders
- **NORMAL**: Standard operations (default)
- **LOW**: Background tasks

### Issuing Orders

**Basic Move Order:**
```python
from pyaurora4x.core.enums import OrderType, OrderPriority
from pyaurora4x.core.models import Vector3D

success, msg = manager.issue_order(
    fleet_id="fleet_1",
    order_type=OrderType.MOVE_TO,
    parameters={"speed": 0.8},  # 80% maximum speed
    target_position=Vector3D(x=1000, y=0, z=500),
    priority=OrderPriority.NORMAL
)
```

**Attack Order:**
```python
success, msg = manager.issue_order(
    fleet_id="fleet_1",
    order_type=OrderType.ATTACK,
    target_fleet_id="enemy_fleet_1",
    priority=OrderPriority.EMERGENCY
)
```

**Patrol Order:**
```python
waypoints = [
    Vector3D(x=0, y=0, z=0),
    Vector3D(x=1000, y=0, z=0),
    Vector3D(x=1000, y=0, z=1000),
]

success, msg = manager.issue_order(
    fleet_id="fleet_1",
    order_type=OrderType.PATROL,
    parameters={
        "waypoints": waypoints,
        "patrol_speed": 0.5,
        "is_repeating": True
    },
    priority=OrderPriority.NORMAL
)
```

### Order Chaining

Complex operations can be broken into sequential orders:

```python
# 1. Move to staging area
manager.issue_order(
    fleet_id="fleet_1",
    order_type=OrderType.MOVE_TO,
    target_position=staging_position,
    priority=OrderPriority.HIGH
)

# 2. Form up in attack formation
manager.issue_order(
    fleet_id="fleet_1",
    order_type=OrderType.FORM_UP,
    parameters={"formation_template_id": "line_ahead"},
    priority=OrderPriority.HIGH
)

# 3. Attack when ready
manager.issue_order(
    fleet_id="fleet_1",
    order_type=OrderType.ATTACK,
    target_fleet_id="enemy_fleet_1",
    priority=OrderPriority.EMERGENCY,
    preconditions=["formation_ready"]
)
```

### Canceling Orders

Cancel orders before they complete:

```python
success = manager.cancel_order(fleet_id="fleet_1", order_id="order_123")
```

---

## Formation Mechanics

### Available Formations

Default formation templates:

1. **Line Formation**
   - Ships arranged in a line
   - Bonus: +20% detection range
   - Best for: Coordinated broadsides, defensive operations
   
2. **Wedge/Arrow Formation**
   - V-shaped arrangement with flagship at point
   - Bonus: +15% combat effectiveness, +10% speed
   - Best for: Aggressive attacks, breakthrough operations

3. **Box Formation**
   - Ships arranged in a box/square
   - Bonus: +25% defensive coordination
   - Best for: Convoy protection, mutual defense

4. **Scattered Formation**
   - Ships spread out
   - Bonus: +30% against area weapons
   - Best for: Avoiding area-of-effect attacks

### Setting a Formation

```python
# Set formation
success, msg = manager.set_fleet_formation(
    fleet_id="fleet_1",
    formation_template_id="line_ahead"
)

# Check formation status
status = manager.get_fleet_tactical_status("fleet_1")
formation = status["formation"]

print(f"Formation Active: {formation['active']}")
print(f"Formation Integrity: {formation['integrity']:.1%}")
print(f"Formation Cohesion: {formation['cohesion']:.1%}")
```

### Formation Integrity

**Integrity** measures how well ships maintain their assigned positions:

- **1.0 (100%)**: Perfect formation, all bonuses active
- **0.7 (70%)**: Good formation, most bonuses active
- **0.5 (50%)**: Partial formation, reduced bonuses
- **0.0 (0%)**: No formation, no bonuses

Integrity decreases due to:
- Combat maneuvers
- Individual ship damage
- High-speed movement
- Obstacles and terrain

**Maintaining Integrity:**
```python
# Slow down to improve integrity
manager.issue_order(
    fleet_id="fleet_1",
    order_type=OrderType.MOVE_TO,
    parameters={"speed": 0.5},  # Slower = better integrity
    target_position=destination
)

# Reform after combat
manager.issue_order(
    fleet_id="fleet_1",
    order_type=OrderType.FORM_UP,
    parameters={"formation_template_id": "current"},
    priority=OrderPriority.HIGH
)
```

---

## Combat Operations

### Starting Combat

Combat begins automatically when hostile fleets are in range, or manually:

```python
engagement_id = manager.start_combat_engagement(
    attacking_fleet_ids=["player_fleet_1", "player_fleet_2"],
    defending_fleet_ids=["enemy_fleet_1"],
    system_id="alpha_centauri"
)
```

### Combat Factors

**Combat Rating** is determined by:
1. **Firepower:** Total weapon damage output
2. **Defense:** Shields, armor, and ECM
3. **Experience:** Crew experience level (0.0-10.0)
4. **Morale:** Crew morale (0-100)
5. **Formation Bonus:** If in proper formation
6. **Commander Skill:** Commanding officer bonuses

### Combat Status

Monitor ongoing combat:

```python
status = manager.get_fleet_tactical_status("fleet_1")
combat = status["combat"]

if combat["in_combat"]:
    print(f"Combat Rating: {combat['combat_rating']:.1f}")
    print(f"Experience: {combat['experience']:.1f}/10.0")
    print(f"Morale: {combat['morale']:.0f}%")
```

### Experience and Morale

**Experience Gain:**
- Participation in combat: +0.5 per engagement
- Victory: +1.0
- Defeat: +0.2 (learned from mistakes)
- Max experience: 10.0

**Morale Effects:**
- High morale (80-100): +10% combat effectiveness
- Normal morale (50-79): No modifier
- Low morale (20-49): -10% combat effectiveness
- Broken morale (<20): Fleet may retreat

**Improving Morale:**
- Victory in combat: +10
- Rest at friendly port: +5 per day
- Successful mission completion: +3
- Commander bonuses: Varies by officer

---

## Logistics Management

### Fuel Management

Track fuel status:

```python
status = manager.get_fleet_tactical_status("fleet_1")
fuel_pct = status["logistics"]["fuel_status"]

if fuel_pct < 0.2:
    # Critical: Refuel immediately
    manager.issue_order(
        fleet_id="fleet_1",
        order_type=OrderType.REFUEL,
        target_planet_id="earth",
        priority=OrderPriority.EMERGENCY
    )
elif fuel_pct < 0.5:
    # Warning: Plan refueling
    print("Fleet fuel below 50%, consider refueling soon")
```

### Maintenance

Regular maintenance prevents equipment failures:

```python
status = manager.get_fleet_tactical_status("fleet_1")
maintenance_due = status["logistics"]["maintenance_due"]

if maintenance_due > 0.8:
    # Schedule maintenance
    manager.issue_order(
        fleet_id="fleet_1",
        order_type=OrderType.REPAIR,
        target_planet_id="nearest_friendly_port",
        priority=OrderPriority.HIGH
    )
```

### Supply Status

Check ammunition and supplies:

```python
status = manager.get_fleet_tactical_status("fleet_1")
supply_status = status["logistics"]["supply_status"]

for supply_type, percentage in supply_status.items():
    if percentage < 0.3:
        print(f"Low {supply_type}: {percentage:.1%}")
```

---

## Practical Examples

### Example 1: Search and Destroy Mission

```python
from pyaurora4x.core.enums import OrderType, OrderPriority
from pyaurora4x.core.models import Vector3D

# 1. Form up attack formation
manager.issue_order(
    fleet_id="attack_fleet",
    order_type=OrderType.FORM_UP,
    parameters={"formation_template_id": "line_ahead"},
    priority=OrderPriority.HIGH
)

# 2. Move to enemy system
manager.issue_order(
    fleet_id="attack_fleet",
    order_type=OrderType.MOVE_TO,
    target_position=enemy_system_coords,
    parameters={"speed": 0.7},
    priority=OrderPriority.HIGH
)

# 3. Attack enemy fleet on arrival
manager.issue_order(
    fleet_id="attack_fleet",
    order_type=OrderType.ATTACK,
    target_fleet_id="enemy_defense_fleet",
    priority=OrderPriority.EMERGENCY
)

# 4. Return to base for resupply
manager.issue_order(
    fleet_id="attack_fleet",
    order_type=OrderType.MOVE_TO,
    target_position=home_base_coords,
    parameters={"speed": 0.5},
    priority=OrderPriority.NORMAL
)
```

### Example 2: Convoy Escort

```python
# Escort formation for cargo protection
manager.issue_order(
    fleet_id="escort_fleet",
    order_type=OrderType.FORM_UP,
    parameters={"formation_template_id": "box_formation"},
    priority=OrderPriority.HIGH
)

# Escort cargo fleet
manager.issue_order(
    fleet_id="escort_fleet",
    order_type=OrderType.ESCORT,
    target_fleet_id="cargo_fleet",
    priority=OrderPriority.HIGH
)

# Will automatically follow and defend cargo fleet
```

### Example 3: System Defense Patrol

```python
# Define patrol route around important assets
patrol_waypoints = [
    Vector3D(x=0, y=0, z=0),      # Earth
    Vector3D(x=5000, y=0, z=0),    # Mars
    Vector3D(x=10000, y=0, z=0),   # Asteroid Belt
    Vector3D(x=5000, y=0, z=5000), # Jupiter
]

# Defensive formation
manager.issue_order(
    fleet_id="defense_fleet",
    order_type=OrderType.FORM_UP,
    parameters={"formation_template_id": "line_formation"},
    priority=OrderPriority.NORMAL
)

# Continuous patrol
manager.issue_order(
    fleet_id="defense_fleet",
    order_type=OrderType.PATROL,
    parameters={
        "waypoints": patrol_waypoints,
        "patrol_speed": 0.6,
        "is_repeating": True,  # Loop forever
        "max_repeats": None    # Or set a number
    },
    priority=OrderPriority.NORMAL
)
```

---

## Advanced Tactics

### Multi-Fleet Coordination

Coordinate multiple fleets for complex operations:

```python
# Pincer attack: Two fleets attack from different angles
manager.issue_order(
    fleet_id="fleet_alpha",
    order_type=OrderType.MOVE_TO,
    target_position=Vector3D(x=1000, y=0, z=0),
    priority=OrderPriority.HIGH
)

manager.issue_order(
    fleet_id="fleet_beta",
    order_type=OrderType.MOVE_TO,
    target_position=Vector3D(x=1000, y=0, z=1000),
    priority=OrderPriority.HIGH
)

# Both attack when in position
for fleet_id in ["fleet_alpha", "fleet_beta"]:
    manager.issue_order(
        fleet_id=fleet_id,
        order_type=OrderType.ATTACK,
        target_fleet_id="enemy_flagship",
        priority=OrderPriority.EMERGENCY,
        preconditions=["position_reached"]
    )
```

### Feint and Retreat

Draw enemy into trap:

```python
# Bait fleet: Weak formation, visible
manager.set_fleet_formation("bait_fleet", "scattered_formation")
manager.issue_order(
    fleet_id="bait_fleet",
    order_type=OrderType.MOVE_TO,
    target_position=enemy_detection_range,
    priority=OrderPriority.HIGH
)

# Hidden ambush fleet: Strong formation, waiting
manager.set_fleet_formation("ambush_fleet", "line_ahead")
manager.issue_order(
    fleet_id="ambush_fleet",
    order_type=OrderType.DEFEND,
    target_position=ambush_position,
    parameters={"defend_radius": 5000},
    priority=OrderPriority.HIGH
)

# When enemy chases bait, ambush fleet attacks
```

### Formation Switching Mid-Combat

Adapt to tactical situation:

```python
# Start in arrow formation for initial attack
manager.set_fleet_formation("fleet_1", "line_ahead")

# During combat, check situation
status = manager.get_fleet_tactical_status("fleet_1")

if status["combat"]["morale"] < 50:
    # Switch to defensive box formation
    manager.issue_order(
        fleet_id="fleet_1",
        order_type=OrderType.CHANGE_FORMATION,
        parameters={"new_formation_id": "box_formation"},
        priority=OrderPriority.EMERGENCY
    )
```

---

## Troubleshooting

### Formation Won't Form

**Problem:** Fleet won't achieve formation, integrity stays low

**Solutions:**
1. Check ship count meets minimum for formation
2. Reduce fleet speed (try 50% or lower)
3. Ensure ships aren't damaged or low on fuel
4. Verify no obstacles in formation area

```python
# Debug formation issues
status = manager.get_fleet_tactical_status("fleet_1")
print(f"Integrity: {status['formation']['integrity']}")
print(f"Cohesion: {status['formation']['cohesion']}")

# Try slower speed
manager.issue_order(
    fleet_id="fleet_1",
    order_type=OrderType.FORM_UP,
    parameters={
        "formation_template_id": "current",
        "formation_speed": 0.3  # Very slow
    }
)
```

### Orders Not Executing

**Problem:** Orders stuck in queue, not processing

**Solutions:**
1. Check order preconditions are met
2. Verify fleet has sufficient fuel
3. Check for conflicting orders
4. Ensure fleet isn't engaged in combat

```python
status = manager.get_fleet_tactical_status("fleet_1")
print(f"Active Orders: {status['current_orders']}")
print(f"In Combat: {status['combat']['in_combat']}")

# Cancel conflicting orders
manager.cancel_order(fleet_id="fleet_1", order_id=conflicting_order_id)
```

### Combat Performance Poor

**Problem:** Fleet losing battles it should win

**Solutions:**
1. Check morale and experience levels
2. Verify formation bonuses are active
3. Review logistics status (low fuel/supplies hurt performance)
4. Consider crew/officer quality

```python
status = manager.get_fleet_tactical_status("fleet_1")
combat = status["combat"]

print(f"Combat Rating: {combat['combat_rating']}")
print(f"Morale: {combat['morale']}")
print(f"Experience: {combat['experience']}")

# Improve situation
if combat["morale"] < 60:
    # Return to port for shore leave
    manager.issue_order(
        fleet_id="fleet_1",
        order_type=OrderType.MOVE_TO,
        target_planet_id="friendly_port",
        priority=OrderPriority.HIGH
    )
```

---

## Best Practices

### 1. Always Monitor Logistics
Check fuel and supplies regularly, especially before long operations:

```python
status = manager.get_fleet_tactical_status("fleet_1")
if status["logistics"]["fuel_status"] < 0.5:
    print("Consider refueling before next mission")
```

### 2. Use Appropriate Formations
Match formation to mission:
- **Attack:** Arrow/Wedge formation
- **Defense:** Line or Box formation  
- **Escort:** Box formation
- **Retreat:** Scattered formation

### 3. Prioritize Orders Correctly
- **CRITICAL:** Combat, emergencies
- **HIGH:** Tactical positioning
- **NORMAL:** Routine operations
- **LOW:** Background tasks

### 4. Build Experience
Experienced crews perform significantly better:
- Start new fleets with training exercises
- Rotate veteran crews to train new ships
- Don't waste experienced fleets on trivial missions

### 5. Maintain Morale
Keep crews happy for peak performance:
- Regular shore leave at friendly ports
- Avoid overextending operational time
- Provide victories (success breeds confidence)

---

## Related Documentation

- [Fleet Combat](fleet_combat.md) - Basic combat mechanics
- [Gameplay Guide](gameplay_guide.md) - General fleet operations
- [Jump Points](jump_points.md) - FTL travel and jump point mechanics
- [Colony Management](colony_management.md) - Supply chain and logistics

---

## API Reference

For developers working with the fleet command system programmatically, see the comprehensive docstrings in:

- `pyaurora4x/engine/fleet_command_manager.py` - Main manager class
- `pyaurora4x/core/fleet_command.py` - Data models and types
- `pyaurora4x/core/enums.py` - Order types and status enums

---

**Questions or Issues?**

If you encounter problems or have suggestions for this guide, please refer to the [contributing guidelines](contributing.md) or file an issue on the project repository.
