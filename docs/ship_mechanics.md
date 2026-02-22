# Ship Mechanics Guide

**Version:** 1.0  
**Last Updated:** 2026-01-22

---

## Table of Contents

1. [Overview](#overview)
2. [Ship Components](#ship-components)
3. [Ship Design](#ship-design)
4. [Shipyard Operations](#shipyard-operations)
5. [Ship Combat Mechanics](#ship-combat-mechanics)
6. [Ship Condition and Damage](#ship-condition-and-damage)
7. [Fuel and Logistics](#fuel-and-logistics)
8. [Ship Maintenance](#ship-maintenance)
9. [Practical Examples](#practical-examples)
10. [Advanced Topics](#advanced-topics)

---

## Overview

Ships are the core operational units in PyAurora4X. This guide covers the complete ship lifecycle from component selection through design, construction, operation, combat, maintenance, and eventual retirement or refit.

### Key Ship Systems

- **Component System:** Modular components that define ship capabilities
- **Design System:** Templates combining components into functional ships
- **Shipyard System:** Construction and refit facilities with build points
- **Combat System:** Damage resolution, weapons, and defenses
- **Logistics System:** Fuel consumption, supplies, and maintenance
- **Condition System:** Ship health, damage tracking, and repairs

---

## Ship Components

### Component Types

Components are the building blocks of ship designs. Each component has specific attributes:

| Component Type | Purpose | Key Attributes |
|---------------|---------|----------------|
| **Engine** | Propulsion and speed | power_output, fuel_efficiency, max_speed |
| **Fuel Tank** | Fuel storage | capacity, mass_per_unit |
| **Sensor** | Detection and targeting | range, resolution, power_requirement |
| **Weapon** | Offensive capability | damage, range, accuracy, rate_of_fire |
| **Shield** | Active defense | strength, regeneration_rate, power_cost |
| **Armor** | Passive defense | protection_value, mass |
| **Crew Quarters** | Personnel capacity | crew_capacity, comfort_rating |
| **Cargo Hold** | Storage space | capacity, specialized_type |
| **Jump Drive** | FTL capability | jump_range, charge_time, fuel_cost |
| **Command Center** | Ship control | command_bonus, automation_level |

### Component Attributes

Every component has these core attributes:

```python
class ShipComponent:
    id: str              # Unique identifier
    name: str            # Display name
    component_type: str  # Type category (engine, weapon, etc.)
    mass: float          # Tonnage (affects ship speed and maneuverability)
    cost: int            # Build cost in resources
    power_requirement: float  # Energy consumption
    crew_requirement: int     # Personnel needed to operate
    tech_requirements: List[str]  # Required technologies
    attributes: Dict[str, Any]    # Type-specific attributes
```

### Example: Engine Component

```python
{
    "id": "ion_drive_mk2",
    "name": "Ion Drive Mark II",
    "component_type": "engine",
    "mass": 50.0,
    "cost": 1000,
    "power_requirement": 0.0,  # Engines generate power
    "crew_requirement": 5,
    "tech_requirements": ["Advanced Ion Propulsion"],
    "attributes": {
        "power_output": 100.0,      # Power generation
        "fuel_efficiency": 0.8,      # Lower = more efficient
        "max_acceleration": 5.0,     # m/s²
        "max_speed": 5000.0          # km/s
    }
}
```

### Example: Weapon Component

```python
{
    "id": "railgun_mk1",
    "name": "Railgun Mark I",
    "component_type": "weapon",
    "mass": 25.0,
    "cost": 500,
    "power_requirement": 50.0,
    "crew_requirement": 3,
    "tech_requirements": ["Railgun Technology"],
    "attributes": {
        "damage": 100.0,           # Base damage per shot
        "range": 10000.0,          # Effective range in km
        "accuracy": 0.85,          # Hit probability (0.0-1.0)
        "rate_of_fire": 2.0,       # Shots per minute
        "weapon_type": "kinetic",  # Damage type
        "tracking_speed": 1.5      # Target tracking capability
    }
}
```

---

## Ship Design

### Creating a Ship Design

A ship design combines components into a functional vessel:

```python
from pyaurora4x.core.models import ShipDesign, ShipType

design = ShipDesign(
    id="cruiser_mk1",
    name="Cruiser Mark I",
    ship_type=ShipType.CRUISER,
    components=[
        "ion_drive_mk2",
        "fuel_tank_large",
        "sensor_array_mk1",
        "railgun_mk1",
        "railgun_mk1",  # Two railguns
        "shield_generator_mk1",
        "armor_plate_standard",
        "crew_quarters_standard",
        "command_center_mk1"
    ]
)
```

### Design Validation

When creating a design, the system validates:

1. **Power Balance:** Total power generation ≥ total power consumption
2. **Crew Capacity:** Crew quarters can house required crew
3. **Mass Limits:** Total mass within reasonable limits for ship type
4. **Tech Requirements:** All required technologies are researched
5. **Component Compatibility:** No conflicting component combinations

### Design Statistics

The system automatically calculates:

```python
# Calculated from components
design.total_mass = sum(component.mass for all components)
design.total_cost = sum(component.cost for all components)
design.crew_requirement = sum(component.crew_requirement for all components)

# Combat statistics
max_weapon_range = max(weapon.range for all weapons)
total_firepower = sum(weapon.damage * weapon.rate_of_fire for all weapons)
total_armor = sum(armor.protection_value for all armor)
```

---

## Shipyard Operations

### Build Points (BP) System

Shipyards construct ships using Build Points accumulated over time:

**BP Generation Formula:**
```
effective_bp_per_day = base_bp_per_day × tooling_bonus
```

**Tooling Bonus:**
- Base: 1.0 (100% efficiency)
- After upgrade: Up to 2.0 (200% efficiency)
- Cost scales quadratically with level

### Building a Ship

```python
from pyaurora4x.core.shipyards import BuildOrder

# Create build order
order = BuildOrder(
    id="order_1",
    design_id="cruiser_mk1",
    hull_tonnage=5000,
    total_bp=50000.0,  # Total BP required
    progress_bp=0.0,
    priority=5  # Higher = more urgent
)

# Add to shipyard queue
shipyard.build_queue.append(order)

# Shipyard processes during tick
# BP accumulated = effective_bp_per_day × days_elapsed
# Applied to highest priority order in assigned slipway
```

### Build Time Calculation

```python
# Build time formula
total_bp_required = ship_design.total_mass * bp_per_ton_multiplier
days_to_complete = total_bp_required / shipyard.effective_bp_per_day()

# Example:
# Ship mass: 5000 tons
# BP per ton: 10 (varies by ship type)
# Total BP: 50,000
# Yard BP/day: 500
# Build time: 100 days
```

### Slipways

Slipways are construction berths with tonnage limits:

```python
class Slipway:
    id: str
    max_hull_tonnage: int       # Maximum ship size
    active_order_id: Optional[str]  # Current project
    occupied_until: Optional[float]  # Completion time
```

**Slipway Assignment:**
- Orders assigned to first available slipway that can accommodate tonnage
- Multiple slipways can work simultaneously
- Each slipway handles one order at a time

### Refitting Ships

Refits modify existing ships with new components:

```python
from pyaurora4x.core.shipyards import RefitOrder

# Create refit order
refit = RefitOrder(
    id="refit_1",
    ship_id="ship_alpha",
    from_design_id="cruiser_mk1",
    to_design_id="cruiser_mk2",
    hull_tonnage=5000,
    total_bp=75000.0,  # More BP than new build
    refit_cost_multiplier=1.5,  # 50% extra cost
    components_to_add={"railgun_mk2": 2, "shield_generator_mk2": 1},
    components_to_remove={"railgun_mk1": 2, "shield_generator_mk1": 1}
)

# Add to refit queue
shipyard.refit_queue.append(refit)
```

**Refit Cost Calculation:**
```
base_refit_bp = (new_design.total_mass - old_design.total_mass) * bp_per_ton
refit_cost = base_refit_bp × refit_cost_multiplier
refit_cost = max(refit_cost, minimum_refit_cost)
```

**When to Refit vs Build New:**
- **Refit** if: Minor upgrades, < 30% of components changed
- **Build New** if: Major redesign, > 50% of components changed
- **Consider costs:** Refit is 1.5× cost of difference, but keeps existing ship operational

### Shipyard Management

**Upgrading Tooling:**
```python
# Check upgrade feasibility
upgrade_info = shipyard.upgrade_tooling(cost_multiplier=2.0)

if upgrade_info["feasible"]:
    print(f"Cost: {upgrade_info['tooling_cost']}")
    print(f"New bonus: {upgrade_info['new_bonus']:.1%}")
    print(f"Time: {upgrade_info['time_days']} days")
```

**Retooling for Different Design:**
```python
# Retool for a new ship class
retool_info = shipyard.retool_for_design("destroyer_mk1", cost_multiplier=1.5)

if retool_info["feasible"]:
    print(f"Retool cost: {retool_info['retool_cost']}")
    print(f"Time: {retool_info['retool_time_days']} days")
    print(f"New tooling bonus: {retool_info['new_tooling_bonus']}")
```

---

## Ship Combat Mechanics

### Combat Capabilities

Each ship contributes to fleet combat effectiveness:

```python
class Ship:
    # Combat statistics
    shields: float = 0.0      # Active shield strength
    armor: float = 0.0         # Armor protection value
    structure: float = 100.0   # Hull integrity (0-100%)
```

### Weapon Systems

Weapons have multiple attributes affecting combat:

```python
class WeaponSystem:
    damage: float = 10.0              # Base damage per hit
    range: float = 10000.0            # Effective range (meters)
    accuracy: float = 0.8             # Hit probability (0.0-1.0)
    rate_of_fire: float = 1.0         # Shots per second
    energy_cost: float = 5.0          # Power per shot
    ammunition_capacity: Optional[int]  # For missile weapons
    weapon_type: WeaponType           # BEAM, KINETIC, MISSILE, etc.
```

### Damage Resolution

**Hit Probability:**
```
base_hit_chance = weapon.accuracy
range_modifier = 1.0 - (distance / weapon.range) * 0.5
evasion_modifier = 1.0 - target_speed_factor * 0.3
final_hit_chance = base_hit_chance × range_modifier × evasion_modifier
```

**Damage Application:**
```
if hit:
    # Shields absorb first
    damage_to_shields = min(weapon.damage, target.shields)
    remaining_damage = weapon.damage - damage_to_shields
    target.shields -= damage_to_shields
    
    # Then armor
    if remaining_damage > 0:
        damage_to_armor = min(remaining_damage × 0.5, target.armor)
        remaining_damage -= damage_to_armor
        target.armor -= damage_to_armor
    
    # Finally structure
    if remaining_damage > 0:
        target.structure -= remaining_damage
        
    # Ship destroyed if structure ≤ 0
    if target.structure <= 0:
        target.destroyed = True
```

### Defense Systems

**Shields:**
- Regenerate over time: `shield_regen_per_second`
- Energy cost to maintain: `energy_cost_per_second`
- Effectiveness varies by weapon type

**Armor:**
- Passive protection, reduces damage by percentage
- Does not regenerate (requires repair)
- More effective against kinetic weapons

**Electronic Warfare:**
```python
class CombatCapabilities:
    sensor_strength: float = 100.0  # Detection range
    ecm_strength: float = 0.0       # Electronic countermeasures
    eccm_strength: float = 0.0      # Counter-countermeasures
```

ECM reduces enemy accuracy; ECCM counters enemy ECM.

### Combat Ratings

**Overall Combat Rating:**
```python
combat_rating = (
    (total_firepower × 0.4) +
    (total_defense × 0.3) +
    (sensor_strength × 0.1) +
    (experience_level × 5.0) +
    (morale / 100.0 × 20.0)
)
```

---

## Ship Condition and Damage

### Condition Percentage

Ships have an overall condition (0-100%):

```python
class Ship:
    condition: float = 100.0  # Overall ship condition
    structure: float = 100.0  # Hull integrity
    shields: float = 0.0      # Current shield strength
    armor: float = 0.0        # Current armor value
```

**Condition Effects:**
- **100-80%:** Full operational capability
- **79-50%:** Minor penalties to speed and efficiency (-10%)
- **49-25%:** Significant penalties (-25%), increased failure risk
- **24-1%:** Critical condition (-50%), major systems at risk
- **0%:** Ship destroyed

### Damage Types

1. **Shield Damage:**
   - Temporary, regenerates automatically
   - No permanent effect on ship condition
   
2. **Armor Damage:**
   - Semi-permanent, requires repair
   - Reduces future damage absorption
   
3. **Structure Damage:**
   - Permanent until repaired
   - Directly reduces ship condition
   - Can destroy ship if reaches 0%
   
4. **System Damage:**
   - Individual components can be damaged
   - Reduces component effectiveness
   - Can disable component completely

### Repairing Damage

**At Friendly Port:**
```python
from pyaurora4x.core.enums import OrderType

# Automatic repair order
manager.issue_order(
    fleet_id="damaged_fleet",
    order_type=OrderType.REPAIR,
    target_planet_id="shipyard_planet",
    priority=OrderPriority.HIGH
)

# Repair rate depends on:
# - Shipyard facilities available
# - Spare parts in stock
# - Crew skill level
# - Damage severity
```

**Repair Costs:**
```python
# Cost formula
damage_percentage = 1.0 - (current_structure / max_structure)
repair_cost = (
    ship_design.total_cost × 
    damage_percentage × 
    0.5  # Repairs cost 50% of component value
)

# Time formula
repair_bp_required = ship_design.total_mass × damage_percentage × 5.0
repair_time_days = repair_bp_required / shipyard.effective_bp_per_day()
```

---

## Fuel and Logistics

### Fuel System

**Fuel Capacity:**
Determined by fuel tank components in design:

```python
total_fuel_capacity = sum(
    component.attributes["capacity"] 
    for component in design.components 
    if component.component_type == "fuel_tank"
)
```

**Fuel Consumption:**
```python
# Base consumption
base_consumption = engine.attributes["fuel_efficiency"] × ship.current_mass

# Speed modifier
speed_factor = (current_speed / max_speed) ** 2  # Quadratic

# Final consumption rate
fuel_per_hour = base_consumption × speed_factor

# Example:
# Ship at 50% speed: 0.25× base consumption
# Ship at 100% speed: 1.0× base consumption
```

### Range Calculation

**Operational Range:**
```python
# Maximum range formula
max_range = (
    fuel_capacity / fuel_consumption_rate_at_cruise_speed
) × cruise_speed

# Example:
# Fuel: 1000 units
# Consumption at cruise (50% speed): 5 units/hour
# Cruise speed: 2500 km/s
# Max range: (1000 / 5) × 2500 = 500,000 km
```

### Refueling

```python
# Check fuel status
current_fuel = ship.fuel
fuel_capacity = ship.logistics_requirements.fuel_capacity
fuel_percentage = current_fuel / fuel_capacity

if fuel_percentage < 0.3:
    # Low fuel warning
    print(f"Ship {ship.name} at {fuel_percentage:.1%} fuel")
    
    # Issue refuel order
    manager.issue_order(
        fleet_id=ship.fleet_id,
        order_type=OrderType.REFUEL,
        target_planet_id="nearest_fuel_depot",
        priority=OrderPriority.HIGH
    )
```

### Supply Management

**Supply Types:**
```python
class LogisticsRequirements:
    ammunition_requirements: Dict[str, int]      # By weapon type
    spare_parts_requirements: Dict[str, int]     # By component type
    crew_requirements: int                       # Total crew needed
    supply_status: Dict[LogisticsType, float]    # Current stock levels
```

**Resupply Operations:**
```python
# Check supply status
status = manager.get_fleet_tactical_status(fleet.id)
supplies = status["logistics"]["supply_status"]

for supply_type, percentage in supplies.items():
    if percentage < 0.2:
        print(f"Critical: {supply_type} at {percentage:.1%}")
        
        # Resupply order
        manager.issue_order(
            fleet_id=fleet.id,
            order_type=OrderType.RESUPPLY,
            target_planet_id="supply_depot",
            priority=OrderPriority.EMERGENCY
        )
        break
```

---

## Ship Maintenance

### Maintenance Requirements

Ships require regular maintenance:

```python
class LogisticsRequirements:
    maintenance_interval: float = 720.0  # Hours between maintenance
    last_maintenance: float = 0.0        # Last maintenance time
    maintenance_efficiency: float = 1.0  # Current efficiency (0.0-1.0)
```

### Maintenance Effects

**Efficiency Degradation:**
```
time_since_maintenance = current_time - last_maintenance
degradation_factor = min(1.0, time_since_maintenance / maintenance_interval)

if degradation_factor > 1.0:
    maintenance_efficiency = max(
        0.5,  # Minimum 50% efficiency
        1.0 - (degradation_factor - 1.0) × 0.25
    )
```

**Impact on Performance:**
- Speed reduced by: `(1.0 - maintenance_efficiency) × 20%`
- Fuel consumption increased by: `(1.0 - maintenance_efficiency) × 30%`
- Combat effectiveness reduced by: `(1.0 - maintenance_efficiency) × 15%`

### Performing Maintenance

```python
# Check maintenance status
status = manager.get_fleet_tactical_status(fleet.id)
maintenance_due = status["logistics"]["maintenance_due"]

if maintenance_due > 0.7:  # Over 70% of interval
    # Schedule maintenance
    manager.issue_order(
        fleet_id=fleet.id,
        order_type=OrderType.REPAIR,
        target_planet_id="maintenance_facility",
        priority=OrderPriority.HIGH
    )
```

**Maintenance Time:**
- Basic maintenance: 1-2 days at port
- Major overhaul: 5-10 days
- Emergency field repairs: Possible but less effective

---

## Practical Examples

### Example 1: Designing a Scout Ship

```python
# Scout design: Speed and sensors, minimal weapons
scout_design = ShipDesign(
    id="scout_mk1",
    name="Scout Mark I",
    ship_type=ShipType.FRIGATE,  # Use FRIGATE for light/fast scout ships
    components=[
        "advanced_engine",      # High speed
        "fuel_tank_large",      # Long range
        "sensor_array_long",    # Extended detection
        "light_laser",          # Self-defense only
        "crew_quarters_small",
        "command_center_basic"
    ]
)

# Characteristics:
# - High speed (5000+ km/s)
# - Long range (extended fuel capacity)
# - Excellent sensors (detect at 2× normal range)
# - Weak combat capability
# - Low crew requirement (10-20)
```

### Example 2: Designing a Battleship

```python
# Battleship: Heavy weapons and armor, slower
battleship_design = ShipDesign(
    id="battleship_mk1",
    name="Battleship Mark I",
    ship_type=ShipType.BATTLESHIP,
    components=[
        "fusion_drive",             # Powerful but slower
        "fuel_tank_standard",       # Standard range
        "sensor_array_standard",
        "heavy_railgun", "heavy_railgun", "heavy_railgun",  # 3× heavy weapons
        "missile_launcher", "missile_launcher",              # 2× missile systems
        "shield_generator_heavy",
        "armor_plate_heavy", "armor_plate_heavy",            # 2× armor layers
        "crew_quarters_large",
        "command_center_advanced"
    ]
)

# Characteristics:
# - High firepower (3× heavy + 2× missile)
# - Strong defenses (heavy shields + double armor)
# - Slower speed (2000 km/s)
# - High crew requirement (200+)
# - Expensive to build and maintain
```

### Example 3: Building a Fleet

```python
# Create shipyard with multiple slipways
shipyard = Shipyard(
    id="earth_orbital_yards",
    empire_id="player_empire",
    name="Earth Orbital Shipyards",
    yard_type=YardType.NAVAL,
    bp_per_day=1000.0,
    tooling_bonus=1.5,  # 50% upgraded
    slipways=[
        Slipway(id="slip_1", max_hull_tonnage=10000),
        Slipway(id="slip_2", max_hull_tonnage=10000),
        Slipway(id="slip_3", max_hull_tonnage=5000),
    ]
)

# Queue multiple ships
designs_to_build = [
    ("battleship_mk1", 8000, 80000.0),  # 1× battleship
    ("cruiser_mk1", 5000, 50000.0),      # 2× cruiser
    ("cruiser_mk1", 5000, 50000.0),
    ("destroyer_mk1", 2000, 20000.0),    # 3× destroyer
    ("destroyer_mk1", 2000, 20000.0),
    ("destroyer_mk1", 2000, 20000.0),
]

for i, (design_id, tonnage, bp) in enumerate(designs_to_build):
    order = BuildOrder(
        id=f"order_{i}",
        design_id=design_id,
        hull_tonnage=tonnage,
        total_bp=bp,
        priority=10 - i  # Higher priority for earlier ships
    )
    shipyard.build_queue.append(order)

# Calculate completion times
effective_bp = shipyard.effective_bp_per_day()  # 1500 BP/day
total_bp = sum(bp for _, _, bp in designs_to_build)  # 240,000 BP
total_days = total_bp / effective_bp  # 160 days for full fleet
```

### Example 4: Combat Damage Scenario

```python
# Ship takes damage in combat
ship = fleet.get_ship("cruiser_alpha")

# Initial state
print(f"Shields: {ship.shields}")       # 100.0
print(f"Armor: {ship.armor}")           # 50.0
print(f"Structure: {ship.structure}")   # 100.0

# Enemy fires 3 shots, each 40 damage
for shot in range(3):
    damage = 40.0
    
    # Shot 1: Hits shields
    if ship.shields > 0:
        absorbed = min(damage, ship.shields)
        ship.shields -= absorbed
        damage -= absorbed
    
    # Shot 2-3: Hit armor and structure
    if damage > 0 and ship.armor > 0:
        armor_absorbed = min(damage * 0.5, ship.armor)
        ship.armor -= armor_absorbed
        damage -= armor_absorbed * 2  # Armor reduces damage 50%
    
    if damage > 0:
        ship.structure -= damage

# After combat
print(f"Shields: {ship.shields}")       # 0.0 (depleted)
print(f"Armor: {ship.armor}")           # 30.0 (damaged)
print(f"Structure: {ship.structure}")   # 80.0 (damaged)
print(f"Condition: {ship.condition}")   # 80.0% (needs repair)
```

---

## Advanced Topics

### Power Management

**Power Budget:**
```python
# Calculate power generation
total_power_generation = sum(
    component.attributes.get("power_output", 0.0)
    for component in design.components
    if component.component_type == "engine"
)

# Calculate power consumption
total_power_consumption = sum(
    component.power_requirement
    for component in design.components
)

# Power margin
power_margin = total_power_generation - total_power_consumption

# Design is valid if power_margin ≥ 0
```

**Power States:**
- **Full Power:** All systems operational
- **Reduced Power:** Non-essential systems offline (sensors, luxury)
- **Emergency Power:** Only life support and propulsion
- **No Power:** Ship disabled

### Mass and Speed

**Ship Speed Calculation:**
```python
# Maximum speed formula
max_acceleration = sum(
    engine.attributes["max_acceleration"] 
    for engine in engines
)

# Speed affected by mass
effective_acceleration = max_acceleration / ship.current_mass

# Formation also affects speed
if in_formation:
    effective_speed = max_speed × formation.movement_speed_modifier
```

### Component Damage

Individual components can be damaged:

```python
# After taking structure damage
for component in ship.components:
    damage_chance = structure_damage / 100.0
    if random() < damage_chance:
        component.condition -= random_range(10, 30)
        
        if component.condition <= 0:
            component.operational = False
            print(f"{component.name} destroyed!")
```

**Effects of Component Damage:**
- **Engine damaged:** Reduced speed and acceleration
- **Sensor damaged:** Reduced detection range
- **Weapon damaged:** Lower accuracy or complete failure
- **Shield generator damaged:** Slower regeneration or no shields
- **Life support damaged:** Crew casualties over time

### Experience and Crew Quality

**Experience Levels:**
```python
class CombatCapabilities:
    experience_level: float = 0.0  # 0.0 to 10.0
    morale: float = 100.0          # 0 to 100
```

**Experience Bonuses:**
- **Level 0-2 (Green):** No bonus, -5% accuracy
- **Level 3-5 (Regular):** Standard performance
- **Level 6-8 (Veteran):** +10% accuracy, +5% damage
- **Level 9-10 (Elite):** +20% accuracy, +10% damage, +15% evasion

**Morale Effects:**
- **High (80-100):** +10% overall combat effectiveness
- **Normal (50-79):** Standard performance
- **Low (20-49):** -10% effectiveness, may refuse risky orders
- **Broken (<20):** -25% effectiveness, may retreat or surrender

---

## Optimization Tips

### Design Efficiency

**1. Power-to-Mass Ratio:**
```python
power_per_ton = total_power_generation / ship.total_mass

# Good ratios:
# Scout: 0.5+ (high power for speed)
# Cruiser: 0.3-0.5 (balanced)
# Battleship: 0.2-0.3 (heavy but powerful)
```

**2. Cost-Effectiveness:**
```python
firepower_per_cost = total_firepower / design.total_cost

# Compare designs:
# Design A: 1000 firepower, 10000 cost → 0.10
# Design B: 800 firepower, 6000 cost → 0.13 (more efficient)
```

**3. Role Specialization:**
- Scouts: Speed + sensors, minimal weapons
- Frigates: Anti-fighter, point defense
- Cruisers: Balanced multi-role
- Battleships: Heavy firepower, slow but tough

### Shipyard Efficiency

**1. Tooling Strategy:**
```python
# Upgrade tooling when:
# - Building 3+ ships of same class
# - Long-term production planned
# - Payback period < production time

upgrade_cost = 10000.0
bp_saved_per_ship = 5000.0
ships_to_break_even = upgrade_cost / bp_saved_per_ship  # 2 ships
```

**2. Slipway Utilization:**
- Keep all slipways occupied
- Match ship size to slipway capacity
- Don't waste large slipways on small ships

**3. Build Queue Priority:**
- Urgent military needs: Priority 10
- Fleet expansion: Priority 5-7
- Civilian ships: Priority 3-4
- Experimental designs: Priority 1-2

### Fleet Composition

**Balanced Fleet:**
```
1× Battleship (flagship, heavy firepower)
2× Cruisers (multi-role, fleet backbone)
3× Destroyers (escorts, anti-fighter)
1× Scout (reconnaissance, early warning)
```

**Specialized Fleets:**
- **Strike Fleet:** 100% heavy combat ships
- **Patrol Fleet:** Fast destroyers and frigates
- **Exploration Fleet:** Scouts with science vessels
- **Convoy Fleet:** Cargo ships with escort

---

## Troubleshooting

### Ship Won't Build

**Problem:** Build order stuck at 0% progress

**Solutions:**
1. Check slipway availability (must have free slipway)
2. Verify slipway tonnage limit (must accommodate ship size)
3. Check shipyard BP generation (must be > 0)
4. Verify order isn't paused

```python
# Debug shipyard
print(f"BP/day: {shipyard.effective_bp_per_day()}")
print(f"Free slipways: {sum(1 for s in shipyard.slipways if not s.is_occupied())}")

# Check order status
for order in shipyard.build_queue:
    print(f"{order.id}: {order.completion_percentage():.1f}% complete")
```

### Ship Performance Poor

**Problem:** Ship underperforming in combat or movement

**Solutions:**
1. Check maintenance status (low efficiency affects everything)
2. Verify fuel levels (low fuel reduces speed)
3. Check damage/condition (structure damage reduces effectiveness)
4. Review crew morale (low morale = poor performance)

```python
# Diagnose ship
ship_status = manager.get_fleet_tactical_status(fleet.id)
print(f"Condition: {ship.condition}%")
print(f"Fuel: {ship_status['logistics']['fuel_status']:.1%}")
print(f"Maintenance efficiency: {ship.maintenance_efficiency:.1%}")
print(f"Morale: {ship_status['combat']['morale']}")
```

### Refit Failing

**Problem:** Refit order not completing

**Solutions:**
1. Verify ship is at shipyard location
2. Check slipway availability
3. Ensure target design is valid
4. Verify sufficient resources

```python
# Check refit prerequisites
refit = shipyard.refit_queue[0]
print(f"Ship ID: {refit.ship_id}")
print(f"Progress: {refit.completion_percentage():.1f}%")
print(f"Assigned slipway: {refit.assigned_slipway_id}")
```

---

## Related Documentation

- [Ship Design System Implementation](ship-design-system-implementation.md) - UI/UX for ship designer
- [Advanced Fleet Command](advanced_fleet_command.md) - Fleet-level operations
- [Fleet Combat](fleet_combat.md) - Basic combat overview
- [Shipyard Integration Summary](../SHIPYARD_INTEGRATION_SUMMARY.md) - System integration
- [Colony Management](colony_management.md) - Resource production for shipbuilding

---

## API Reference

For developers, see comprehensive implementation details in:

- `pyaurora4x/core/models.py` - Ship, ShipComponent, ShipDesign models
- `pyaurora4x/core/shipyards.py` - Shipyard, BuildOrder, RefitOrder models
- `pyaurora4x/engine/shipyard_manager.py` - Shipyard processing logic
- `pyaurora4x/core/fleet_command.py` - Combat and logistics systems

---

**Questions or Improvements?**

This guide covers the core ship mechanics. For additional details on specific systems, refer to the implementation documentation or file an issue with your questions.
