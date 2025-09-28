"""
Canvas settings and unit system for PyEWB
Manages grid settings, units, and coordinate conversions
"""

from PyQt6.QtCore import QObject, pyqtSignal


class CanvasSettings(QObject):
    """Manages canvas settings including units and grid configuration"""
    
    # Signals
    units_changed = pyqtSignal(str)  # Emitted when units change
    grid_size_changed = pyqtSignal(float)  # Emitted when grid size changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Unit system configuration
        self.units = 'mil'  # Default unit: mils
        self.grid_size = 100  # Grid spacing in current units (100 mils) - matches resistor width/4
        
        # Conversion factors: pixels per unit
        # 1 inch = 1000 mils = 25.4 mm
        # Assuming 1 pixel = 1 mil for base scale
        self.pixels_per_unit = {
            'mil': 1.0,      # 1 pixel = 1 mil
            'in': 1000.0,    # 1 pixel = 1 mil, so 1 inch = 1000 pixels
            'mm': 39.37      # 1 inch = 25.4 mm, so 1 mm = 39.37 pixels (1000/25.4)
        }
        
        # Unit display names
        self.unit_names = {
            'mil': 'mils',
            'in': 'inch',
            'mm': 'mm'
        }
    
    def get_grid_size_pixels(self):
        """Get grid size in screen pixels"""
        return self.grid_size * self.pixels_per_unit[self.units]
    
    def set_units(self, units: str):
        """Set the current unit system"""
        if units in self.pixels_per_unit:
            self.units = units
            self.units_changed.emit(units)
    
    def set_grid_size(self, size: float):
        """Set grid size in current units"""
        self.grid_size = size
        self.grid_size_changed.emit(size)
    
    def set_grid_size_for_components(self, component_width_units: int = 4):
        """Set grid size to match component dimensions"""
        # Set grid size so that components fit nicely
        # Default: 4 grid units for resistor width (400 mils total, 100 mils per grid)
        self.grid_size = 100  # 100 mils per grid unit
        self.grid_size_changed.emit(self.grid_size)
    
    def set_grid_size_for_component_type(self, component_type: str, config_manager=None):
        """Set grid size based on specific component type configuration"""
        if config_manager:
            component_config = config_manager.get_component_config(component_type)
            if component_config and component_config.grid_alignment == "component_based":
                # Set grid size to match terminal spacing for perfect alignment
                # Terminals are at half the component width from center
                max_dimension = max(component_config.width_mils, component_config.height_mils)
                # Use half the component dimension so terminals align with grid
                self.grid_size = max_dimension // 2
                self.grid_size_changed.emit(self.grid_size)
                return True
        return False
    
    def pixels_to_units(self, pixels: float) -> float:
        """Convert pixels to current units"""
        return pixels / self.pixels_per_unit[self.units]
    
    def units_to_pixels(self, units: float) -> float:
        """Convert current units to pixels"""
        return units * self.pixels_per_unit[self.units]
    
    def snap_to_grid(self, pos):
        """Snap a position to the grid in pixels"""
        grid_size_px = self.get_grid_size_pixels()
        snapped_x = round(pos.x() / grid_size_px) * grid_size_px
        snapped_y = round(pos.y() / grid_size_px) * grid_size_px
        return type(pos)(snapped_x, snapped_y)
    
    def get_unit_display_name(self) -> str:
        """Get display name for current unit"""
        return self.unit_names.get(self.units, 'mil')
    
    def format_coordinate(self, x: float, y: float) -> str:
        """Format coordinates for display in status bar"""
        unit_x = self.pixels_to_units(x)
        unit_y = self.pixels_to_units(y)
        unit_name = self.get_unit_display_name()
        return f"X: {unit_x:.2f} {unit_name}, Y: {unit_y:.2f} {unit_name}"
