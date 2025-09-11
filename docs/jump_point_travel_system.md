# Jump Point Travel & Exploration System

## Overview

The Jump Point Travel & Exploration System is a comprehensive implementation of interstellar travel and exploration mechanics for PyAurora 4X. This system provides the core 4X expansion gameplay through jump point discovery, fleet travel coordination, fuel management, and progressive system exploration.

## Architecture

### Core Components

The system is built around several interconnected components:

#### 1. Enhanced Jump Point Model (`pyaurora4x.core.models.JumpPoint`)

The `JumpPoint` model has been significantly enhanced from the basic version to include:

- **Discovery and Exploration Status**: Track which empires have discovered and surveyed each jump point
- **Travel Requirements**: Fuel costs, time calculations, and technology prerequisites
- **Strategic Information**: Traffic levels, empire access controls, and usage history
- **Dynamic Properties**: Stability ratings, size classes, and efficiency modifiers

```python
# Example jump point with full features
jump_point = JumpPoint(
    name="JP-Alpha-Centauri",
    position=Vector3D(x=2.5e9, y=1.2e9, z=0.1e9),  # 2.5 AU from origin
    connects_to="alpha_centauri_system_id",
    jump_point_type=JumpPointType.NATURAL,
    status=JumpPointStatus.ACTIVE,
    stability=0.95,
    size_class=3,
    fuel_cost_modifier=0.9,  # 10% more efficient than standard
    travel_time_modifier=1.1,  # 10% longer travel time
    discovered_by="player_empire_id",
    survey_level=2  # Surveyed but not fully mapped
)
```

#### 2. Jump Point Exploration System (`pyaurora4x.engine.jump_point_exploration`)

Manages the discovery and exploration of jump points:

- **Progressive Discovery**: Jump points start unknown and are gradually revealed through exploration
- **Hidden Jump Points**: Some jump points remain hidden until discovered through deep exploration
- **Exploration Missions**: Fleets can conduct exploration and survey missions
- **Empire Knowledge Tracking**: Each empire maintains separate knowledge of discovered jump points

**Key Features:**
- Probabilistic jump point detection based on fleet capabilities and distance
- Mission-based exploration with duration and success calculations
- Hidden jump point generation and revelation mechanics
- Empire-specific exploration progress tracking

#### 3. Fleet Jump Travel System (`pyaurora4x.engine.jump_travel_system`)

Handles the mechanics of fleet travel through jump points:

- **Jump Preparation Phase**: Fleets must prepare before jumping (fuel checks, formation, etc.)
- **Travel Execution**: Actual jump travel with fuel consumption and time passage
- **Fuel Management**: Realistic fuel costs based on fleet mass and jump point characteristics
- **Jump Requirements**: Technology, ship capabilities, and jump point accessibility validation

**Travel Flow:**
1. **Preparation Phase**: Fleet prepares for jump (30-120 seconds depending on fleet size and jump point stability)
2. **Execution Phase**: Fleet jumps through the jump point (5-60 seconds travel time)
3. **Arrival Phase**: Fleet arrives in target system and resumes normal operations

#### 4. Jump Point Manager (`pyaurora4x.engine.jump_point_manager`)

Centralized coordinator for all jump point operations:

- **Network Management**: Maintains jump point connectivity graph and pathfinding
- **Empire Knowledge**: Tracks what each empire knows about the jump network
- **Operation Coordination**: Manages exploration missions and travel operations
- **Network Generation**: Creates enhanced jump point networks during galaxy generation

## Core Mechanics

### Jump Point Discovery

Jump points are discovered through several methods:

1. **Passive Detection**: Moving fleets have a chance to detect nearby jump points
2. **Exploration Missions**: Dedicated exploration missions increase discovery chances
3. **Survey Operations**: Detailed surveys reveal hidden jump points and improve travel efficiency

**Discovery Factors:**
- Distance to jump point (closer = easier to detect)
- Fleet sensor capabilities
- Jump point characteristics (size, stability, type)
- Empire exploration experience
- Random chance factor

### Travel Requirements and Costs

Jump travel has realistic requirements and costs:

**Fuel Costs:**
```python
base_cost = JUMP_FUEL_COST_BASE  # 100 units
per_ship_cost = JUMP_FUEL_COST_PER_SHIP * ship_count
mass_factor = (fleet_mass / 1000.0) ** 0.5
size_factor = jump_point.size_class * 0.8  # Larger jump points more efficient

total_cost = (base_cost + per_ship_cost) * mass_factor * modifier / size_factor
```

**Travel Time:**
```python
base_time = JUMP_TIME_BASE  # 30 seconds
mass_factor = 1.0 + (fleet_mass / 10000.0)
ship_factor = 1.0 + (ship_count * 0.1)
stability_factor = 2.0 - jump_point.stability  # Unstable points take longer

travel_time = base_time * mass_factor * ship_factor * stability_factor
```

### Exploration Progression

Systems are explored progressively:

1. **Initial Discovery**: System discovered but not explored
2. **Basic Exploration**: General system survey reveals planets and major features  
3. **Detailed Survey**: Comprehensive survey reveals hidden jump points and resources
4. **Complete Mapping**: All jump points surveyed and mapped for efficient travel

### Jump Point Types and Characteristics

#### Natural Jump Points
- **Stability**: 0.8 - 1.0 (most are stable)
- **Size Class**: 1-5 (affects ship size limits and efficiency)
- **Discovery**: Can be found through exploration
- **Usage**: Standard travel costs and times

#### Artificial Jump Gates
- **Stability**: 1.0 (perfectly stable)
- **Size Class**: Usually 4-5 (large)
- **Discovery**: Must be constructed
- **Usage**: More efficient but require advanced technology

#### Unstable Jump Points
- **Stability**: 0.3 - 0.7 (variable)
- **Size Class**: 1-3 (usually smaller)
- **Discovery**: Harder to detect and survey
- **Usage**: Higher fuel costs, longer travel times, occasional failures

#### Dormant Jump Points
- **Stability**: Variable when activated
- **Size Class**: Variable
- **Discovery**: Appear inactive until properly surveyed or activated
- **Usage**: May require special technology or conditions to activate

## API Reference

### Main Simulation Interface

The main simulation provides high-level interfaces for jump point operations:

```python
# Get available jump destinations for a fleet
available_jumps = simulation.get_available_jumps(fleet_id)

# Initiate a jump to a specific system
success, message = simulation.initiate_fleet_jump(fleet_id, jump_point_id)

# Start an exploration mission
success, message = simulation.start_fleet_exploration(fleet_id, mission_type="explore")

# Survey a specific jump point  
success, message = simulation.survey_jump_point(fleet_id, jump_point_id)

# Get current jump/exploration status
jump_status = simulation.get_fleet_jump_status(fleet_id)
exploration_status = simulation.get_system_exploration_status(system_id, empire_id)

# Get empire's known jump network
network = simulation.get_empire_jump_network(empire_id)
```

### Jump Point Manager Interface

For more advanced control, access the jump point manager directly:

```python
manager = simulation.get_jump_point_manager()

# Generate enhanced jump network
manager.generate_enhanced_jump_network(systems, connectivity_level=0.3)

# Process all jump point operations
results = manager.process_turn_update(fleets, systems, ships, current_time, delta_seconds)

# Get detailed jump network for empire
network = manager.get_empire_jump_network(empire_id, systems)
```

### Fleet Jump Travel System

Direct access to travel mechanics:

```python
travel_system = manager.travel_system

# Calculate jump requirements
requirements = travel_system.calculate_jump_requirements(fleet, jump_point, ships, empire_tech)

# Get jump status
status = travel_system.get_jump_status(fleet_id)

# Cancel active jump
success, message = travel_system.cancel_jump_operation(fleet_id)
```

### Exploration System

Direct exploration system access:

```python
exploration_system = manager.exploration_system

# Start exploration mission
success = exploration_system.start_exploration_mission(fleet, system, mission_type, current_time)

# Attempt jump point detection
detected_points = exploration_system.attempt_jump_point_detection(fleet, system, empire_id, current_time)

# Get exploration status
status = exploration_system.get_exploration_status(system_id, empire_id)
```

## UI Integration

### Jump Travel Panel

The `JumpTravelPanel` widget provides a comprehensive interface for jump point operations:

**Features:**
- Display available jump points with status, costs, and travel times
- Initiate jump travel with fuel and time estimates
- Start exploration and survey missions
- View current operation progress with ETA display
- Show system exploration status and statistics

**Usage:**
```python
from pyaurora4x.ui.widgets.jump_travel_panel import JumpTravelPanel

# Create and configure panel
jump_panel = JumpTravelPanel()
jump_panel.update_fleet_data(fleet, system, simulation)
```

### Jump Network Map

The `JumpNetworkMap` widget displays known jump point connections:

**Features:**
- Visual representation of known systems and connections
- Empire-specific view showing only discovered jump points
- Connection status and accessibility information
- Navigation statistics and exploration progress

## AI Integration

AI empires use the jump point system intelligently:

### AI Decision Making

AI fleets make decisions based on priorities:

1. **Jump Exploration** (30% chance): Jump to unexplored systems
2. **System Exploration** (20% chance): Explore current system
3. **Jump Point Survey** (15% chance): Survey discovered jump points
4. **Local Movement** (35% chance): Move within current system

### AI Strategic Behavior

- **Weighted Target Selection**: AI prefers less explored systems
- **Fuel Management**: AI considers fuel costs and fleet capabilities
- **Progressive Exploration**: AI systematically maps jump networks
- **Mission Coordination**: AI coordinates exploration and expansion efforts

### AI Configuration

AI behavior can be influenced by empire personality settings:

```python
empire.ai_expansion = 0.8  # High expansion drive = more jump exploration
empire.ai_aggression = 0.3  # Low aggression = focus on exploration vs military
empire.ai_research_focus = [TechnologyType.SENSORS, TechnologyType.PROPULSION]
```

## Configuration and Constants

Key configuration values in `pyaurora4x.core.enums.CONSTANTS`:

```python
# Jump travel costs and times
"JUMP_FUEL_COST_BASE": 100,      # Base fuel cost for any jump
"JUMP_FUEL_COST_PER_SHIP": 10,   # Additional fuel per ship
"JUMP_TIME_BASE": 30,            # Base jump time in seconds

# Exploration parameters  
"EXPLORATION_BASE_TIME": 300,    # Base exploration mission time
"SURVEY_BASE_TIME": 600,         # Base survey mission time
"JUMP_POINT_DETECTION_RANGE": 2.0,  # Detection range in AU
"EXPLORATION_SUCCESS_BASE": 0.3, # Base exploration success chance
```

## Testing

Comprehensive test suite covers all major functionality:

### Test Categories

1. **Model Tests**: Jump point creation, accessibility, cost calculations
2. **Exploration Tests**: Discovery mechanics, mission creation, status tracking
3. **Travel Tests**: Requirements calculation, jump preparation, execution
4. **Manager Tests**: Network generation, empire knowledge, coordination
5. **Integration Tests**: Simulation integration, AI behavior, UI interaction
6. **Performance Tests**: Large network handling, edge cases, error conditions

### Running Tests

```bash
# Run all jump point system tests
python -m pytest tests/test_jump_point_system.py -v

# Run specific test categories
python -m pytest tests/test_jump_point_system.py::TestJumpPointModel -v
python -m pytest tests/test_jump_point_system.py::TestJumpTravelSystem -v
```

## Best Practices

### For Game Design

1. **Balanced Discovery**: Ensure exploration feels rewarding but not overwhelming
2. **Meaningful Costs**: Jump travel should have strategic costs (fuel, time, risk)
3. **Progressive Revelation**: Gradually reveal the galaxy to maintain mystery
4. **Strategic Depth**: Multiple pathways and connection types add decision depth

### For Development

1. **Modular Design**: Keep exploration, travel, and management systems separate
2. **Empire Privacy**: Ensure empire knowledge is properly isolated
3. **Performance Optimization**: Cache network calculations for large galaxies
4. **Error Handling**: Gracefully handle edge cases (no jump points, fuel exhaustion, etc.)

### For AI Design

1. **Realistic Behavior**: AI should make believable exploration decisions
2. **Difficulty Scaling**: AI exploration effectiveness should match difficulty level
3. **Player Competition**: AI should compete with player for discovery and expansion
4. **Cooperative Possibilities**: Consider diplomatic exploration agreements

## Future Enhancements

### Planned Features

1. **Wormhole Networks**: Temporary connections that appear and disappear
2. **Jump Point Construction**: Artificial jump gate construction projects
3. **Navigation Computers**: Advanced pathfinding and route optimization
4. **Exploration Specialization**: Ships and fleets specialized for exploration
5. **Diplomatic Elements**: Shared jump point access and exploration treaties

### Technical Improvements

1. **Performance Optimization**: Better caching and network algorithms
2. **Save/Load Integration**: Proper persistence of exploration state
3. **Mod Support**: Extensible exploration and jump point mechanics
4. **Visualization**: 3D galaxy map with jump point connections
5. **Analytics**: Exploration statistics and empire comparison metrics

## Troubleshooting

### Common Issues

**Jump Points Not Appearing**
- Check that system has been initialized with jump point manager
- Verify jump point generation parameters
- Ensure empire has exploration data initialized

**Fleets Can't Jump**
- Verify fleet has sufficient fuel
- Check jump point accessibility for empire
- Confirm jump point status is ACTIVE or MAPPED
- Validate fleet has ships with jump capability

**Exploration Not Working**
- Check fleet status - must be IDLE or ORBITING to start exploration
- Verify system hasn't already been fully explored
- Ensure exploration system is properly initialized

**AI Not Exploring**
- Check AI empire settings and expansion preference
- Verify AI has access to jump points
- Ensure AI fleets are not constantly busy with other tasks

### Debug Information

Enable debug logging for detailed information:

```python
import logging
logging.getLogger("pyaurora4x.engine.jump_point_manager").setLevel(logging.DEBUG)
logging.getLogger("pyaurora4x.engine.jump_point_exploration").setLevel(logging.DEBUG)
logging.getLogger("pyaurora4x.engine.jump_travel_system").setLevel(logging.DEBUG)
```

## Conclusion

The Jump Point Travel & Exploration System provides a comprehensive foundation for 4X expansion gameplay in PyAurora 4X. With its modular design, realistic mechanics, and intelligent AI integration, it supports both casual and deep strategic gameplay while maintaining the mystery and excitement of space exploration.

The system successfully implements all required acceptance criteria:
- ✅ Fleets can be ordered to jump between connected systems  
- ✅ Exploration reveals new jump points
- ✅ Jump travel consumes fuel and takes time
- ✅ UI shows jump point connections and travel options
- ✅ Comprehensive tests cover jump mechanics, exploration logic, and UI integration

This implementation provides a strong foundation for future enhancements and expansion of the exploration and travel mechanics in PyAurora 4X.
