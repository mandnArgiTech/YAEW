"""
Resistor component for PyEWB
Implements a resistor with standard zig-zag symbol using configurable dimensions
"""

from PyQt6.QtWidgets import QStyleOptionGraphicsItem, QWidget
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QPainter, QPainterPath, QPen, QFont, QFontMetrics, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from .configurable_component import ConfigurableComponent
import os


class Resistor(ConfigurableComponent):
    """Resistor component with zig-zag symbol using configurable dimensions"""
    
    def __init__(self, name: str = "R", value: str = "1k"):
        super().__init__("resistor", name, value)
        
        # Resistor-specific properties
        self._segment_count = 4  # Number of zig-zag segments
        
        # Initialize realistic resistor properties
        self.properties = {
            'Resistance': '1k',
            'Tolerance': '±5%',
            'Power Rating (W)': '0.25',
            'Temp. Coefficient (ppm/K)': '100'
        }
    
    def update_dimensions(self):
        """Update resistor dimensions based on current grid size and configuration"""
        super().update_dimensions()
    
    def _paint_component(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        """Paint the resistor symbol"""
        # Set up painter
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw the SVG icon if available
        if self._svg_renderer and self._svg_renderer.isValid():
            self._draw_svg_icon(painter)
        else:
            # Fallback to drawn symbol
            self._draw_fallback_symbol(painter)
        
        # Draw terminals
        self._draw_terminals(painter)
        
        # Draw component name and value
        self._draw_labels(painter)
        
        # Draw debug information only when enabled in configuration
        self._draw_debug_info(painter)
    
    def _draw_svg_icon(self, painter: QPainter):
        """Draw the SVG resistor icon with proper scaling"""
        super()._draw_svg_icon(painter)
    
    
    def _draw_fallback_symbol(self, painter: QPainter):
        """Draw fallback resistor symbol if SVG is not available"""
        # Use black pen for normal drawing, no red selection outline
        pen = QPen(Qt.GlobalColor.black, 2)
        painter.setPen(pen)
        
        # Draw the zig-zag resistor symbol
        self._draw_resistor_symbol(painter)
    
    def _draw_resistor_symbol(self, painter: QPainter):
        """Draw the zig-zag resistor symbol"""
        # Calculate segment dimensions
        segment_width = self._width / (self._segment_count * 2)
        segment_height = self._height * 0.8
        
        # Start position
        start_x = -self._width // 2
        start_y = 0
        
        # Create path for zig-zag
        path = QPainterPath()
        path.moveTo(start_x, start_y)
        
        current_x = start_x
        current_y = start_y
        
        # Draw zig-zag pattern
        for i in range(self._segment_count):
            # Move right
            current_x += segment_width
            path.lineTo(current_x, current_y)
            
            # Zig up or down
            if i % 2 == 0:
                current_y -= segment_height / 2
            else:
                current_y += segment_height / 2
            
            current_x += segment_width
            path.lineTo(current_x, current_y)
        
        # Draw the path
        painter.drawPath(path)
    
    def _draw_terminals(self, painter: QPainter):
        """Draw connection terminals"""
        terminal_radius = 5  # Made larger for easier clicking
        
        for terminal in self._terminals:
            x = terminal['x']
            y = terminal['y']
            
            # Draw terminal circle with better visibility
            painter.setBrush(Qt.GlobalColor.red)
            painter.setPen(Qt.GlobalColor.darkRed)
            painter.drawEllipse(int(x - terminal_radius), int(y - terminal_radius), 
                              int(terminal_radius * 2), int(terminal_radius * 2))
    
    def _draw_labels(self, painter: QPainter):
        """Draw component name and value labels with Level of Detail"""
        # Check if we should show text based on zoom level
        scene = self.scene()
        if scene and scene.views():
            view = scene.views()[0]
            if hasattr(view, 'should_show_text') and not view.should_show_text():
                return  # Don't draw text at low zoom levels
        
        # Set up font with larger size
        font = QFont("Arial", 10, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(Qt.GlobalColor.black)
        
        # Draw component name
        name_text = self.name if self.name else "R"
        name_rect = QRectF(-self._width // 2, -self._height - 20, 
                          self._width, 15)
        painter.drawText(name_rect, Qt.AlignmentFlag.AlignCenter, name_text)
        
        # Draw resistance value from properties
        resistance_value = self.properties.get('Resistance', self.value or '1k')
        value_rect = QRectF(-self._width // 2, self._height + 8, 
                           self._width, 15)
        painter.drawText(value_rect, Qt.AlignmentFlag.AlignCenter, resistance_value)
        
        # Draw tolerance if available and zoom level is high enough
        tolerance = self.properties.get('Tolerance', '')
        if tolerance and scene and scene.views():
            view = scene.views()[0]
            if hasattr(view, 'should_show_details') and view.should_show_details():
                # Use smaller font for tolerance
                tolerance_font = QFont("Arial", 8)
                painter.setFont(tolerance_font)
                tolerance_rect = QRectF(-self._width // 2, self._height + 25, 
                                       self._width, 12)
                painter.drawText(tolerance_rect, Qt.AlignmentFlag.AlignCenter, tolerance)
                # Reset font for other text
                painter.setFont(font)
    
    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle of the resistor"""
        margin = 15  # Extra margin for larger labels
        # Extra space for tolerance label
        extra_height = 20 if self.properties.get('Tolerance', '') else 0
        return QRectF(-self._width // 2 - margin, 
                     -self._height - margin - 5,  # Extra space for name
                     self._width + 2 * margin, 
                     self._height * 2 + 2 * margin + extra_height + 10)
    
    def shape(self) -> QPainterPath:
        """Return the shape of the resistor for collision detection"""
        path = QPainterPath()
        
        # Add main resistor body
        path.addRect(-self._width // 2, -self._height // 2, 
                    self._width, self._height)
        
        # Add terminal areas
        for terminal in self._terminals:
            terminal_rect = QRectF(terminal['x'] - 5, terminal['y'] - 5, 10, 10)
            path.addEllipse(terminal_rect)
        
        return path
    
    def update_terminals_after_rotation(self):
        """Update terminal positions after rotation"""
        # Terminals are now handled automatically in get_terminal_position()
        # No need to update terminal positions here
        pass
    
    def _get_properties_config(self):
        """Get properties configuration for the resistor dialog"""
        return {
            'Resistance': {
                'type': 'text',
                'placeholder': 'e.g., 1k, 10M, 470R',
                'tooltip': 'Resistance value (use standard notation: R, k, M, G)'
            },
            'Tolerance': {
                'type': 'combo',
                'options': ['±0.1%', '±0.25%', '±0.5%', '±1%', '±2%', '±5%', '±10%', '±20%']
            },
            'Power Rating (W)': {
                'type': 'combo',
                'options': ['0.125', '0.25', '0.5', '1', '2', '5', '10', '25', '50']
            },
            'Temp. Coefficient (ppm/K)': {
                'type': 'text',
                'placeholder': 'e.g., 100, 50, 25',
                'tooltip': 'Temperature coefficient in parts per million per Kelvin'
            }
        }
