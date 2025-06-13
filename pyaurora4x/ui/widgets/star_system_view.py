"""
Star System View Widget for PyAurora 4X

Displays an ASCII/Unicode representation of a star system with planets,
orbits, and fleet positions.
"""

import math
from typing import Optional, List, Tuple
from textual.widgets import Static
from textual.app import ComposeResult
from textual.containers import Container
from textual.reactive import reactive

from pyaurora4x.core.models import StarSystem, Fleet, Planet, Vector3D
from pyaurora4x.core.utils import distance_3d, format_distance


class StarSystemView(Static):
    """
    Widget that displays a star system with ASCII art.
    
    Shows the star, planetary orbits, current planet positions,
    and fleet locations in a 2D projection.
    """
    
    star_system = reactive(None)
    fleets = reactive([])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.system: Optional[StarSystem] = None
        self.system_fleets: List[Fleet] = []
        self.scale_factor = 1.0
        self.center_x = 40
        self.center_y = 15
        self.max_radius = 30
    
    def compose(self) -> ComposeResult:
        """Compose the star system view."""
        with Container(id="system_display"):
            yield Static("", id="system_ascii", classes="system-map")
            yield Static("", id="system_info", classes="system-info")
    
    def update_system(self, star_system: StarSystem, fleets: Optional[List[Fleet]] = None) -> None:
        """
        Update the displayed star system.
        
        Args:
            star_system: The star system to display
            fleets: List of fleets in the system
        """
        self.system = star_system
        self.system_fleets = fleets or []
        self._calculate_scale()
        self._render_system()
    
    def _calculate_scale(self) -> None:
        """Calculate the scale factor for display."""
        if not self.system or not self.system.planets:
            self.scale_factor = 1.0
            return
        
        # Find the maximum orbital distance
        max_distance = max(planet.orbital_distance for planet in self.system.planets)
        
        # Scale to fit within display area
        if max_distance > 0:
            self.scale_factor = self.max_radius / (max_distance * 149597870.7)  # Convert AU to km
        else:
            self.scale_factor = 1.0
    
    def _render_system(self) -> None:
        """Render the star system as ASCII art."""
        if not self.system:
            self._update_display("No star system loaded", "")
            return
        
        # Create display grid
        width, height = 80, 30
        display = [[' ' for _ in range(width)] for _ in range(height)]
        
        # Draw the central star
        star_char = self._get_star_character(self.system.star_type)
        if 0 <= self.center_y < height and 0 <= self.center_x < width:
            display[self.center_y][self.center_x] = star_char
        
        # Draw planetary orbits and planets
        for i, planet in enumerate(self.system.planets):
            self._draw_planet_orbit(display, planet, i)
            self._draw_planet(display, planet, i)
        
        # Draw fleets
        for fleet in self.system_fleets:
            self._draw_fleet(display, fleet)
        
        # Convert display grid to string
        ascii_display = '\n'.join(''.join(row) for row in display)
        
        # Generate system info
        info_text = self._generate_system_info()
        
        self._update_display(ascii_display, info_text)
    
    def _get_star_character(self, star_type) -> str:
        """Get the character to represent the star."""
        star_chars = {
            'M': '•',  # M dwarf - small dot
            'K': '●',  # K dwarf - medium dot
            'G': '☉',  # G dwarf - sun symbol
            'F': '○',  # F dwarf - open circle
            'A': '◉',  # A star - large circle
        }
        return star_chars.get(star_type.value if hasattr(star_type, 'value') else str(star_type), '☉')
    
    def _draw_planet_orbit(self, display: List[List[str]], planet: Planet, index: int) -> None:
        """Draw a planet's orbit as a circle."""
        if not planet.orbital_distance:
            return
        
        # Calculate orbit radius in display units
        orbit_radius_km = planet.orbital_distance * 149597870.7  # AU to km
        orbit_radius_display = orbit_radius_km * self.scale_factor
        
        if orbit_radius_display < 1 or orbit_radius_display > self.max_radius:
            return
        
        # Draw orbit circle (simplified - just a few points)
        points = 24  # Number of points to draw
        for i in range(points):
            angle = (2 * math.pi * i) / points
            x = int(self.center_x + orbit_radius_display * math.cos(angle))
            y = int(self.center_y + orbit_radius_display * math.sin(angle) * 0.5)  # Flatten for ASCII
            
            if 0 <= y < len(display) and 0 <= x < len(display[0]):
                if display[y][x] == ' ':  # Don't overwrite other objects
                    display[y][x] = '·'
    
    def _draw_planet(self, display: List[List[str]], planet: Planet, index: int) -> None:
        """Draw a planet at its current position."""
        if not planet.position:
            return
        
        # Convert 3D position to 2D display coordinates
        x_km = planet.position.x
        y_km = planet.position.y
        
        x_display = int(self.center_x + x_km * self.scale_factor)
        y_display = int(self.center_y + y_km * self.scale_factor * 0.5)  # Flatten for ASCII
        
        if 0 <= y_display < len(display) and 0 <= x_display < len(display[0]):
            planet_char = self._get_planet_character(planet, index)
            display[y_display][x_display] = planet_char
    
    def _get_planet_character(self, planet: Planet, index: int) -> str:
        """Get the character to represent a planet."""
        planet_chars = {
            'terrestrial': ['🜨', '♁', '♂', '♀', '☿'],  # Earth-like symbols
            'gas_giant': ['♃', '♄', '⊕', '⊗', '⊙'],    # Jupiter/Saturn-like
            'ice_giant': ['♆', '⛢', '❅', '❆', '❈'],    # Neptune-like
        }
        
        planet_type = planet.planet_type.value if hasattr(planet.planet_type, 'value') else str(planet.planet_type)
        chars = planet_chars.get(planet_type, ['○'])
        
        # Use index to select character, cycling if needed
        char_index = index % len(chars)
        return chars[char_index]
    
    def _draw_fleet(self, display: List[List[str]], fleet: Fleet) -> None:
        """Draw a fleet at its current position."""
        if not fleet.position:
            return
        
        # Convert 3D position to 2D display coordinates
        x_km = fleet.position.x
        y_km = fleet.position.y
        
        x_display = int(self.center_x + x_km * self.scale_factor)
        y_display = int(self.center_y + y_km * self.scale_factor * 0.5)
        
        if 0 <= y_display < len(display) and 0 <= x_display < len(display[0]):
            fleet_char = '▲' if fleet.empire_id == "player" else '△'
            display[y_display][x_display] = fleet_char
    
    def _generate_system_info(self) -> str:
        """Generate information text about the system."""
        if not self.system:
            return "No system data available"
        
        info_lines = []
        info_lines.append(f"System: {self.system.name}")
        info_lines.append(f"Star: {self.system.star_type.value if hasattr(self.system.star_type, 'value') else self.system.star_type}")
        info_lines.append(f"Mass: {self.system.star_mass:.2f} M☉")
        info_lines.append(f"Luminosity: {self.system.star_luminosity:.2f} L☉")
        info_lines.append("")
        
        info_lines.append(f"Planets: {len(self.system.planets)}")
        for i, planet in enumerate(self.system.planets):
            distance_str = f"{planet.orbital_distance:.2f} AU"
            planet_type = planet.planet_type.value if hasattr(planet.planet_type, 'value') else str(planet.planet_type)
            info_lines.append(f"  {i+1}. {planet.name} ({planet_type}) - {distance_str}")
        
        if self.system_fleets:
            info_lines.append("")
            info_lines.append(f"Fleets: {len(self.system_fleets)}")
            for fleet in self.system_fleets:
                status = fleet.status.value if hasattr(fleet.status, 'value') else str(fleet.status)
                info_lines.append(f"  {fleet.name} ({status})")
        
        # Add habitable zone info
        info_lines.append("")
        info_lines.append("Habitable Zone:")
        info_lines.append(f"  Inner: {self.system.habitable_zone_inner:.2f} AU")
        info_lines.append(f"  Outer: {self.system.habitable_zone_outer:.2f} AU")
        
        return '\n'.join(info_lines)
    
    def _update_display(self, ascii_art: str, info_text: str) -> None:
        """Update the display widgets."""
        try:
            ascii_widget = self.query_one("#system_ascii", Static)
            info_widget = self.query_one("#system_info", Static)
            
            ascii_widget.update(ascii_art)
            info_widget.update(info_text)
        except Exception:
            # Widgets might not be ready yet
            pass
    
    def on_mount(self) -> None:
        """Initialize the widget when mounted."""
        if not self.system:
            self._update_display("Loading star system...", "Initializing display...")

