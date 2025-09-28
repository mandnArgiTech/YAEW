"""
Configurable Component base class for PyEWB
Extends BaseComponent with configuration-driven dimensions and properties
"""

from PyQt6.QtWidgets import QStyleOptionGraphicsItem, QWidget
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QPainter, QPainterPath, QPen, QFont, QFontMetrics
from PyQt6.QtSvg import QSvgRenderer
from .base import BaseComponent
from config.config_manager import config_manager
import os


class ConfigurableComponent(BaseComponent):
    """Base class for components with configurable dimensions and properties"""
    
    def __init__(self, component_type: str, name: str = "", value: str = ""):
        super().__init__(name, value)
        
        self.component_type = component_type
        self.config = config_manager.get_component_config(component_type)
        
        if not self.config:
            raise ValueError(f"No configuration found for component type: {component_type}")
        
        # Initialize dimensions from configuration
        self._initialize_dimensions()
        
        # Initialize terminals from configuration
        self._initialize_terminals()
        
        # Load SVG icon
        self._svg_renderer = None
        self._load_svg_icon()
        
        # Store original terminal positions for rotation
        self._original_terminals = self._get_original_terminal_positions()
        
        # Disable Qt's built-in selection rectangle
        self.setFlag(self.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(self.GraphicsItemFlag.ItemIsMovable, True)
        # Don't set ItemSendsGeometryChanges to avoid Qt's selection behavior
    
    def _initialize_dimensions(self):
        """Initialize component dimensions from configuration"""
        # Get current grid settings
        scene = self.scene()
        if scene and hasattr(scene, 'settings') and scene.settings:
            pixels_per_mil = scene.settings.pixels_per_unit.get('mil', 1.0)
        else:
            pixels_per_mil = 1.0  # Default fallback
        
        # Set dimensions in pixels based on configuration
        self._width = self.config.width_mils * pixels_per_mil
        self._height = self.config.height_mils * pixels_per_mil
        
        # Store grid units for dynamic updates
        self._grid_units_width = self.config.width_mils / 100.0  # Convert mils to grid units
        self._grid_units_height = self.config.height_mils / 100.0
    
    def _initialize_terminals(self):
        """Initialize terminals from configuration"""
        # Clear existing terminals
        self._terminals.clear()
        
        # Get current grid settings
        scene = self.scene()
        if scene and hasattr(scene, 'settings') and scene.settings:
            pixels_per_mil = scene.settings.pixels_per_unit.get('mil', 1.0)
        else:
            pixels_per_mil = 1.0  # Default fallback
        
        # Add terminals from configuration
        for terminal_config in self.config.terminal_positions:
            x_pixels = terminal_config['x_offset_mils'] * pixels_per_mil
            y_pixels = terminal_config['y_offset_mils'] * pixels_per_mil
            name = terminal_config.get('name', '')
            self.add_terminal(x_pixels, y_pixels, name)
    
    def _get_original_terminal_positions(self) -> list:
        """Get original terminal positions for rotation calculations"""
        return [(terminal['x'], terminal['y']) for terminal in self._terminals]
    
    def update_dimensions(self):
        """Update component dimensions based on current grid size and configuration"""
        scene = self.scene()
        if scene and hasattr(scene, 'settings') and scene.settings:
            # Get grid size in pixels
            pixels_per_mil = scene.settings.pixels_per_unit.get('mil', 1.0)
            
            # Update dimensions from configuration
            self._width = self.config.width_mils * pixels_per_mil
            self._height = self.config.height_mils * pixels_per_mil
            
            # Update terminal positions
            if len(self._terminals) >= len(self.config.terminal_positions):
                for i, terminal_config in enumerate(self.config.terminal_positions):
                    if i < len(self._terminals):
                        x_pixels = terminal_config['x_offset_mils'] * pixels_per_mil
                        y_pixels = terminal_config['y_offset_mils'] * pixels_per_mil
                        self._terminals[i]['x'] = x_pixels
                        self._terminals[i]['y'] = y_pixels
            
            # Update original terminals for rotation
            self._original_terminals = self._get_original_terminal_positions()
    
    def _load_svg_icon(self):
        """Load the SVG icon for the component"""
        if not self.config.svg_file:
            return
        
        try:
            # Get the path to the SVG file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            svg_path = os.path.join(current_dir, '..', self.config.svg_file)
            svg_path = os.path.normpath(svg_path)
            
            if os.path.exists(svg_path):
                self._svg_renderer = QSvgRenderer(svg_path)
            else:
                print(f"SVG file not found: {svg_path}")
                self._svg_renderer = None
        except Exception as e:
            print(f"Error loading SVG icon: {e}")
            self._svg_renderer = None
    
    def _draw_svg_icon(self, painter: QPainter):
        """Draw the SVG component icon with proper scaling"""
        if not self._svg_renderer or not self._svg_renderer.isValid():
            return
        
        # Set up pen - use black for normal drawing, no red outline
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        
        # Get SVG dimensions
        svg_size = self._svg_renderer.defaultSize()
        svg_width = svg_size.width()
        svg_height = svg_size.height()
        
        # Calculate scale factor based on configuration
        if self.config.svg_scaling == "fit_within_bounds":
            # Scale to fit within component bounds while maintaining aspect ratio
            scale_x = self._width / svg_width
            scale_y = self._height / svg_height
            scale = min(scale_x, scale_y) if self.config.maintain_aspect_ratio else max(scale_x, scale_y)
        elif self.config.svg_scaling == "stretch_to_fit":
            # Stretch to fill component bounds
            scale_x = self._width / svg_width
            scale_y = self._height / svg_height
            scale = max(scale_x, scale_y)
        else:
            # Default to fit within bounds
            scale_x = self._width / svg_width
            scale_y = self._height / svg_height
            scale = min(scale_x, scale_y)
        
        # Calculate actual rendered size
        rendered_width = svg_width * scale
        rendered_height = svg_height * scale
        
        # Center the SVG within the component bounds
        icon_rect = QRectF(-rendered_width // 2, -rendered_height // 2, 
                          rendered_width, rendered_height)
        
        # Render the SVG
        self._svg_renderer.render(painter, icon_rect)
    
    def _draw_debug_info(self, painter: QPainter):
        """Draw debug information for component sizing and configuration"""
        # Check if debug info is enabled in global settings
        if not config_manager.is_debug_info_enabled():
            return
        
        # Only draw debug info if component is selected and not being dragged
        if not self.isSelected():
            return
        
        # Check if we're in a dragging state by looking at the scene's mouse state
        scene = self.scene()
        if scene and scene.views():
            view = scene.views()[0]
            # Don't show debug info during dragging
            if hasattr(view, 'is_dragging') and view.is_dragging():
                return
        
        # Save painter state
        painter.save()
        
        # Draw debug text only (no rectangles to avoid red square issue)
        font = QFont("Arial", 8)
        painter.setFont(font)
        painter.setPen(Qt.GlobalColor.darkGray)
        
        # Component info
        info_text = f"Component: {self._width:.0f}x{self._height:.0f}px ({self.config.width_mils}x{self.config.height_mils}mils)"
        painter.drawText(int(-self._width // 2), int(-self._height // 2 - 10), info_text)
        
        # Configuration info
        config_text = f"Config: {self.component_type} | SVG: {self.config.svg_scaling}"
        painter.drawText(int(-self._width // 2), int(-self._height // 2 - 25), config_text)
        
        # Terminal positions
        if len(self._terminals) >= 2:
            term1_x, term1_y = self.get_terminal_position(0)
            term2_x, term2_y = self.get_terminal_position(1)
            term_text = f"Terminals: ({term1_x:.0f},{term1_y:.0f}) ({term2_x:.0f},{term2_y:.0f})"
            painter.drawText(int(-self._width // 2), int(-self._height // 2 - 40), term_text)
        
        # Restore painter state
        painter.restore()
    
    def update_terminals_after_rotation(self):
        """Update terminal positions after rotation"""
        # Terminals are handled automatically in get_terminal_position()
        # No need to update terminal positions here
        pass
    
    def update_terminals_after_mirror(self):
        """Update terminal positions after mirroring"""
        # Terminals are handled automatically in get_terminal_position()
        # No need to update terminal positions here
        pass
    
    def get_terminal_position(self, terminal_index: int) -> tuple:
        """
        Get the absolute position of a terminal
        
        Args:
            terminal_index: Index of the terminal
            
        Returns:
            Tuple of (x, y) absolute coordinates
        """
        if 0 <= terminal_index < len(self._terminals):
            terminal = self._terminals[terminal_index]
            # Apply rotation transformation to terminal position
            import math
            angle_rad = math.radians(self._rotation)
            cos_angle = math.cos(angle_rad)
            sin_angle = math.sin(angle_rad)
            
            # Rotate the terminal position
            rotated_x = terminal['x'] * cos_angle - terminal['y'] * sin_angle
            rotated_y = terminal['x'] * sin_angle + terminal['y'] * cos_angle
            
            # Calculate absolute position
            abs_x = self.pos().x() + rotated_x
            abs_y = self.pos().y() + rotated_y
            
            return (abs_x, abs_y)
        return (0, 0)
    
    def get_component_type(self) -> str:
        """Get the component type"""
        return self.component_type
    
    def get_configuration(self) -> dict:
        """Get current component configuration"""
        return {
            'dimensions': self.config.dimensions,
            'terminals': self.config.terminals,
            'svg': self.config.svg,
            'grid': self.config.grid
        }
    
    def reload_configuration(self):
        """Reload component configuration from file"""
        self.config = config_manager.get_component_config(self.component_type)
        if self.config:
            self._initialize_dimensions()
            self._initialize_terminals()
            self._load_svg_icon()
            self._original_terminals = self._get_original_terminal_positions()
            self.update()
    
    def _draw_selection_indicator(self, painter: QPainter):
        """Draw a transparent dotted blue selection indicator around the component"""
        if not self.isSelected():
            return
        
        # Save painter state
        painter.save()
        
        # Create a transparent blue dotted pen
        from PyQt6.QtGui import QColor
        blue_color = QColor(0, 0, 255, 128)  # Blue with 50% transparency
        selection_pen = QPen(blue_color, 1, Qt.PenStyle.DotLine)
        painter.setPen(selection_pen)
        
        # Ensure no brush is used - completely transparent
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # Draw selection rectangle slightly outside component bounds
        margin = 3
        x = -self._width // 2 - margin
        y = -self._height // 2 - margin
        w = self._width + 2 * margin
        h = self._height + 2 * margin
        
        # Draw the outline rectangle with dotted lines
        painter.drawRect(int(x), int(y), int(w), int(h))
        
        # Restore painter state
        painter.restore()
    
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        """Override paint to control selection appearance and eliminate red rectangle"""
        # Completely disable Qt's built-in selection rectangle
        # Don't call super().paint() or any parent paint methods
        
        # Call the subclass paint method first to draw the component
        self._paint_component(painter, option, widget)
        
        # Draw our custom selection indicator last (on top) - only if selected
        if self.isSelected():
            self._draw_selection_indicator(painter)
    
    def _paint_component(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        """Paint the component - must be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement _paint_component() method")
    
    def itemChange(self, change, value):
        """Override itemChange to prevent Qt's built-in selection behavior"""
        if change == self.GraphicsItemChange.ItemSelectedChange:
            # Don't let Qt handle selection changes - we'll handle it ourselves
            return value
        
        return super().itemChange(change, value)
