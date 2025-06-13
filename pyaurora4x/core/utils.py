"""
Utility functions for PyAurora 4X

Common mathematical and helper functions used throughout the game.
"""

import math
from typing import List, Tuple, Any, Dict
import random
import logging

from pyaurora4x.core.models import Vector3D

logger = logging.getLogger(__name__)


def distance_3d(pos1: Vector3D, pos2: Vector3D) -> float:
    """
    Calculate the 3D distance between two positions.
    
    Args:
        pos1: First position
        pos2: Second position
        
    Returns:
        Distance between the positions
    """
    dx = pos2.x - pos1.x
    dy = pos2.y - pos1.y
    dz = pos2.z - pos1.z
    return math.sqrt(dx*dx + dy*dy + dz*dz)


def angle_between_vectors(v1: Vector3D, v2: Vector3D) -> float:
    """
    Calculate the angle between two vectors in radians.
    
    Args:
        v1: First vector
        v2: Second vector
        
    Returns:
        Angle between vectors in radians
    """
    dot_product = v1.x * v2.x + v1.y * v2.y + v1.z * v2.z
    mag1 = v1.magnitude()
    mag2 = v2.magnitude()
    
    if mag1 == 0 or mag2 == 0:
        return 0.0
    
    cos_angle = dot_product / (mag1 * mag2)
    cos_angle = max(-1.0, min(1.0, cos_angle))  # Clamp to valid range
    return math.acos(cos_angle)


def vector_add(v1: Vector3D, v2: Vector3D) -> Vector3D:
    """Add two vectors."""
    return Vector3D(x=v1.x + v2.x, y=v1.y + v2.y, z=v1.z + v2.z)


def vector_subtract(v1: Vector3D, v2: Vector3D) -> Vector3D:
    """Subtract v2 from v1."""
    return Vector3D(x=v1.x - v2.x, y=v1.y - v2.y, z=v1.z - v2.z)


def vector_multiply(v: Vector3D, scalar: float) -> Vector3D:
    """Multiply a vector by a scalar."""
    return Vector3D(x=v.x * scalar, y=v.y * scalar, z=v.z * scalar)


def vector_divide(v: Vector3D, scalar: float) -> Vector3D:
    """Divide a vector by a scalar."""
    if scalar == 0:
        return Vector3D()
    return Vector3D(x=v.x / scalar, y=v.y / scalar, z=v.z / scalar)


def dot_product(v1: Vector3D, v2: Vector3D) -> float:
    """Calculate the dot product of two vectors."""
    return v1.x * v2.x + v1.y * v2.y + v1.z * v2.z


def cross_product(v1: Vector3D, v2: Vector3D) -> Vector3D:
    """Calculate the cross product of two vectors."""
    return Vector3D(
        x=v1.y * v2.z - v1.z * v2.y,
        y=v1.z * v2.x - v1.x * v2.z,
        z=v1.x * v2.y - v1.y * v2.x
    )


def lerp(a: float, b: float, t: float) -> float:
    """
    Linear interpolation between two values.
    
    Args:
        a: Start value
        b: End value
        t: Interpolation factor (0.0 to 1.0)
        
    Returns:
        Interpolated value
    """
    return a + (b - a) * t


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp a value between minimum and maximum bounds.
    
    Args:
        value: Value to clamp
        min_val: Minimum bound
        max_val: Maximum bound
        
    Returns:
        Clamped value
    """
    return max(min_val, min(max_val, value))


def normalize_angle(angle: float) -> float:
    """
    Normalize an angle to the range [0, 2π).
    
    Args:
        angle: Angle in radians
        
    Returns:
        Normalized angle
    """
    while angle < 0:
        angle += 2 * math.pi
    while angle >= 2 * math.pi:
        angle -= 2 * math.pi
    return angle


def degrees_to_radians(degrees: float) -> float:
    """Convert degrees to radians."""
    return degrees * math.pi / 180.0


def radians_to_degrees(radians: float) -> float:
    """Convert radians to degrees."""
    return radians * 180.0 / math.pi


def format_time(seconds: float) -> str:
    """
    Format time in seconds to a human-readable string.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted time string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f}h"
    elif seconds < 31536000:
        days = seconds / 86400
        return f"{days:.1f}d"
    else:
        years = seconds / 31536000
        return f"{years:.1f}y"


def format_distance(distance_km: float) -> str:
    """
    Format distance in kilometers to a human-readable string.
    
    Args:
        distance_km: Distance in kilometers
        
    Returns:
        Formatted distance string
    """
    if distance_km < 1000:
        return f"{distance_km:.1f} km"
    elif distance_km < 1e6:
        return f"{distance_km/1000:.1f} Mm"
    elif distance_km < 1.496e8:
        return f"{distance_km/1e6:.1f} Gm"
    else:
        au = distance_km / 1.496e8
        return f"{au:.2f} AU"


def format_mass(mass_kg: float) -> str:
    """
    Format mass in kilograms to a human-readable string.
    
    Args:
        mass_kg: Mass in kilograms
        
    Returns:
        Formatted mass string
    """
    earth_mass = 5.972e24
    
    if mass_kg < earth_mass:
        ratio = mass_kg / earth_mass
        return f"{ratio:.2f} M⊕"
    else:
        solar_mass = 1.989e30
        ratio = mass_kg / solar_mass
        if ratio < 0.1:
            return f"{mass_kg/earth_mass:.1f} M⊕"
        else:
            return f"{ratio:.2f} M☉"


def weighted_random_choice(choices: List[Tuple[Any, float]]) -> Any:
    """
    Select a random item from weighted choices.
    
    Args:
        choices: List of (item, weight) tuples
        
    Returns:
        Selected item
    """
    total_weight = sum(weight for _, weight in choices)
    if total_weight <= 0:
        return None
    
    r = random.uniform(0, total_weight)
    cumulative = 0
    
    for item, weight in choices:
        cumulative += weight
        if r <= cumulative:
            return item
    
    return choices[-1][0]  # Fallback to last item


def generate_uuid() -> str:
    """Generate a unique identifier string."""
    import uuid
    return str(uuid.uuid4())


def deep_merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """
    Deep merge two dictionaries.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary (takes precedence)
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def calculate_travel_time(distance: float, max_speed: float, acceleration: float = None) -> float:
    """
    Calculate travel time for a given distance and speed.
    
    Args:
        distance: Distance to travel
        max_speed: Maximum speed
        acceleration: Acceleration (optional, for more realistic calculation)
        
    Returns:
        Travel time
    """
    if acceleration is None or acceleration <= 0:
        # Simple constant speed
        return distance / max_speed if max_speed > 0 else float('inf')
    
    # Time to reach max speed
    time_to_max = max_speed / acceleration
    distance_to_max = 0.5 * acceleration * time_to_max ** 2
    
    if distance <= 2 * distance_to_max:
        # Never reach max speed - triangular velocity profile
        return 2 * math.sqrt(distance / acceleration)
    else:
        # Trapezoidal velocity profile
        cruise_distance = distance - 2 * distance_to_max
        cruise_time = cruise_distance / max_speed
        return 2 * time_to_max + cruise_time


def orbital_period(semi_major_axis: float, central_mass: float) -> float:
    """
    Calculate orbital period using Kepler's third law.
    
    Args:
        semi_major_axis: Semi-major axis in meters
        central_mass: Central mass in kilograms
        
    Returns:
        Orbital period in seconds
    """
    G = 6.67430e-11  # Gravitational constant
    return 2 * math.pi * math.sqrt(semi_major_axis**3 / (G * central_mass))


def escape_velocity(mass: float, radius: float) -> float:
    """
    Calculate escape velocity from a celestial body.
    
    Args:
        mass: Mass in kilograms
        radius: Radius in meters
        
    Returns:
        Escape velocity in m/s
    """
    G = 6.67430e-11  # Gravitational constant
    return math.sqrt(2 * G * mass / radius)


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if denominator is zero.
    
    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if division by zero
        
    Returns:
        Division result or default
    """
    return numerator / denominator if denominator != 0 else default


def exponential_decay(initial_value: float, decay_rate: float, time: float) -> float:
    """
    Calculate exponential decay.
    
    Args:
        initial_value: Initial value
        decay_rate: Decay rate (higher = faster decay)
        time: Time elapsed
        
    Returns:
        Decayed value
    """
    return initial_value * math.exp(-decay_rate * time)


def sigmoid(x: float, steepness: float = 1.0, midpoint: float = 0.0) -> float:
    """
    Sigmoid function for smooth transitions.
    
    Args:
        x: Input value
        steepness: Steepness of the curve
        midpoint: X value at the curve's midpoint
        
    Returns:
        Sigmoid output (0 to 1)
    """
    return 1.0 / (1.0 + math.exp(-steepness * (x - midpoint)))
