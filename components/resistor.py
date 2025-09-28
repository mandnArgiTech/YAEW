"""
Resistor component for PyEWB
Implements a resistor with standard zig-zag symbol using configurable dimensions
"""

from PyQt6.QtWidgets import QStyleOptionGraphicsItem, QWidget
from PyQt6.QtCore import QRectF, Qt, QPointF
from PyQt6.QtGui import QPainter, QPainterPath, QPen, QFont, QFontMetrics, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from .configurable_component import ConfigurableComponent
from .movable_label import MovableLabel
import os


class Resistor(ConfigurableComponent):
    """Resistor component with zig-zag symbol using configurable dimensions"""
    
    def __init__(self, name: str = "R1", value: str = "1k"):
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
        
        # Create movable labels
        self._name_label = None
        self._value_label = None
        
        # Initialize label offsets (will be set when labels are created)
        # Position labels: name above component, value below component
        # Updated based on user positioning: Name offset: (-3.8, -38.1), Value offset: (-6.2, 21.9)
        self._name_offset = QPointF(-3.8, -38.1)  # Above component - user positioned
        self._value_offset = QPointF(-6.2, 21.9)  # Below component - user positioned
        
        # Flag to prevent offset recalculation during component movement
        self._updating_label_positions = False
        
        # Store unsnapped position for label positioning
        self._unsnapped_position = QPointF(0, 0)
    
    def update_dimensions(self):
        """Update resistor dimensions based on current grid size and configuration"""
        super().update_dimensions()
        # Update label positions when dimensions change
        self._update_label_positions()
    
    def _create_labels(self):
        """Create movable labels for the component"""
        if not self.scene():
            return  # Can't create labels without a scene
        
        # Create name label (e.g., R1)
        name_text = self.name if self.name else "R1"
        self._name_label = MovableLabel(name_text, self, "name")
        self._name_label.setPos(self.pos() + self._name_offset)
        self.scene().addItem(self._name_label)
        
        # Create value label (e.g., 1K)
        resistance_value = self.properties.get('Resistance', self.value or '1k')
        self._value_label = MovableLabel(resistance_value, self, "value")
        self._value_label.setPos(self.pos() + self._value_offset)
        self.scene().addItem(self._value_label)
    
    def _update_label_positions(self):
        """Update label positions when component moves"""
        # Set flag BEFORE calling setPos to prevent offset recalculation
        self._updating_label_positions = True
        
        # Use component's actual position for label positioning
        # The offsets are already calculated relative to the component's position
        base_pos = self.pos()
        
        if self._name_label:
            new_name_pos = base_pos + self._name_offset
            self._name_label.setPos(new_name_pos)
            self._name_label.update()  # Force visual update
        if self._value_label:
            new_value_pos = base_pos + self._value_offset
            self._value_label.setPos(new_value_pos)
            self._value_label.update()  # Force visual update
            
        # Re-enable offset tracking after all positions are set
        self._updating_label_positions = False
    
    def on_label_moved(self, label, new_position):
        """Handle when a label is moved"""
        # Only update offsets if we're not in the middle of updating label positions
        if self._updating_label_positions:
            return
            
        # Update the label's stored offset relative to component position
        if label == self._name_label:
            self._name_offset = new_position - self.pos()
            # Debug log for name label position
            print(f"DEBUG: Name label moved to offset: {self._name_offset.x():.1f}, {self._name_offset.y():.1f}")
        elif label == self._value_label:
            self._value_offset = new_position - self.pos()
            # Debug log for value label position
            print(f"DEBUG: Value label moved to offset: {self._value_offset.x():.1f}, {self._value_offset.y():.1f}")
    
    def _cleanup_labels(self):
        """Clean up labels when component is removed from scene"""
        if self._name_label and self._name_label.scene():
            self._name_label.scene().removeItem(self._name_label)
            self._name_label = None
        if self._value_label and self._value_label.scene():
            self._value_label.scene().removeItem(self._value_label)
            self._value_label = None
    
    def get_final_label_positions(self):
        """Get the final label positions for saving as defaults"""
        return {
            'name_offset': {
                'x': self._name_offset.x(),
                'y': self._name_offset.y()
            },
            'value_offset': {
                'x': self._value_offset.x(),
                'y': self._value_offset.y()
            }
        }
    
    def mousePressEvent(self, event):
        """Handle mouse press events and store unsnapped position"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Store the unsnapped position for label positioning
            self._unsnapped_position = self.pos()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events with unsnapped position tracking"""
        if event.buttons() == Qt.MouseButton.LeftButton:
            # Calculate new position without snapping
            new_pos = event.scenePos() - self._drag_start_pos
            
            # Store unsnapped position for label positioning
            self._unsnapped_position = new_pos
            
            # Apply grid snapping only to component
            scene = self.scene()
            if scene and hasattr(scene, 'settings') and scene.settings:
                snapped_pos = scene.settings.snap_to_grid(new_pos)
                self.setPos(snapped_pos)
            else:
                self.setPos(new_pos)
            
            # Don't update labels during movement - only after movement is complete
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events with final snapping"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Apply final grid snapping to component
            scene = self.scene()
            if scene and hasattr(scene, 'settings') and scene.settings:
                snapped_pos = scene.settings.snap_to_grid(self.pos())
                self.setPos(snapped_pos)
            
            # Update label positions after component movement is complete
            self._update_label_positions()
        super().mouseReleaseEvent(event)
    
    def itemChange(self, change, value):
        """Handle item changes"""
        if change == self.GraphicsItemChange.ItemPositionChange:
            # Update label positions when component moves
            self._update_label_positions()
        
        return super().itemChange(change, value)
    
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
        # Labels are now handled by separate MovableLabel items
        # This method is kept for compatibility but does nothing
        pass
    
    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle of the resistor"""
        margin = 10  # Smaller margin for closer labels
        return QRectF(-self._width // 2 - margin, 
                     -self._height // 2 - margin - 15,  # Space for name label
                     self._width + 2 * margin, 
                     self._height + 2 * margin + 30)  # Space for value label
    
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
    
    def rotate_label_offsets(self, angle_degrees):
        """Rotate the label offsets when component is rotated"""
        from PyQt6.QtGui import QTransform
        
        # Create rotation transform
        transform = QTransform()
        transform.rotate(angle_degrees)
        
        # Rotate the label offsets
        self._name_offset = transform.map(self._name_offset)
        self._value_offset = transform.map(self._value_offset)
        
        # Update label positions with new rotated offsets
        self._update_label_positions()
    
    def rotate_90_clockwise(self):
        """Rotate component 90 degrees clockwise and update labels"""
        super().rotate_90_clockwise()
        self.rotate_label_offsets(90)
    
    def rotate_90_counterclockwise(self):
        """Rotate component 90 degrees counterclockwise and update labels"""
        super().rotate_90_counterclockwise()
        self.rotate_label_offsets(-90)
    
    def rotate_180(self):
        """Rotate component 180 degrees and update labels"""
        super().rotate_180()
        self.rotate_label_offsets(180)
    
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
