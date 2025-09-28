"""
Voltage source components for PyEWB
Implements DC, AC, and Pulse voltage sources
"""

from PyQt6.QtWidgets import QStyleOptionGraphicsItem, QWidget
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QPainter, QPainterPath, QPen, QFont, QFontMetrics
from .base import BaseComponent


class VoltageSourceBase(BaseComponent):
    """Base class for all voltage sources"""
    
    def __init__(self, name: str = "V", value: str = "5V"):
        super().__init__(name, value)
        
        # Voltage source dimensions - aligned to grid
        # Use 1 grid unit radius (100 mils) and 1 grid unit terminal length
        self._grid_units_radius = 1
        self._grid_units_terminal_length = 1
        
        # Initialize with default grid size, will be updated by scene
        self._radius = 25  # Will be updated by update_dimensions()
        self._terminal_length = 20  # Will be updated by update_dimensions()
        
        # Add terminals at top and bottom
        self.add_terminal(0, -self._radius - self._terminal_length, "Positive")
        self.add_terminal(0, self._radius + self._terminal_length, "Negative")
        
        # Update dimensions based on current grid
        self.update_dimensions()
        
        # Store original terminal positions for rotation
        self._original_terminals = [
            (0, -self._radius - self._terminal_length),
            (0, self._radius + self._terminal_length)
        ]
    
    def update_dimensions(self):
        """Update voltage source dimensions based on current grid size"""
        scene = self.scene()
        if scene and hasattr(scene, 'settings') and scene.settings:
            # Get grid size in pixels
            grid_size_px = scene.settings.get_grid_size_pixels()
            self._radius = self._grid_units_radius * grid_size_px
            self._terminal_length = self._grid_units_terminal_length * grid_size_px
            
            # Update terminal positions
            if len(self._terminals) >= 2:
                self._terminals[0]['x'] = 0
                self._terminals[0]['y'] = -self._radius - self._terminal_length
                self._terminals[1]['x'] = 0
                self._terminals[1]['y'] = self._radius + self._terminal_length
            
            # Update original terminals for rotation
            self._original_terminals = [
                (0, -self._radius - self._terminal_length),
                (0, self._radius + self._terminal_length)
            ]
    
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        """Paint the voltage source symbol"""
        # Set up painter
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Set pen based on selection state
        if self.isSelected():
            pen = QPen(Qt.GlobalColor.red, 2)
        else:
            pen = QPen(Qt.GlobalColor.black, 2)
        painter.setPen(pen)
        
        # Draw the circle
        circle_rect = QRectF(-self._radius, -self._radius, 
                           self._radius * 2, self._radius * 2)
        painter.drawEllipse(circle_rect)
        
        # Draw terminals (connection lines)
        self._draw_terminals(painter)
        
        # Draw the specific symbol inside the circle
        self._draw_source_symbol(painter)
        
        # Draw component name and value
        self._draw_labels(painter)
    
    def _draw_terminals(self, painter: QPainter):
        """Draw connection terminals"""
        terminal_radius = 3
        
        for terminal in self._terminals:
            x = terminal['x']
            y = terminal['y']
            
            # Draw terminal circle
            painter.setBrush(Qt.GlobalColor.red)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(x - terminal_radius, y - terminal_radius, 
                              terminal_radius * 2, terminal_radius * 2)
            
            # Draw connection line
            painter.setPen(Qt.GlobalColor.black)
            if y < 0:  # Top terminal
                painter.drawLine(x, y + terminal_radius, x, y + self._terminal_length)
            else:  # Bottom terminal
                painter.drawLine(x, y - terminal_radius, x, y - self._terminal_length)
    
    def _draw_source_symbol(self, painter: QPainter):
        """Draw the specific source symbol - to be overridden by subclasses"""
        pass
    
    def _draw_labels(self, painter: QPainter):
        """Draw component name and value labels"""
        # Check if we should show text based on zoom level
        scene = self.scene()
        if scene and scene.views():
            view = scene.views()[0]
            if hasattr(view, 'should_show_text') and not view.should_show_text():
                return  # Don't draw text at low zoom levels
        
        # Set up font
        font = QFont("Arial", 8, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(Qt.GlobalColor.black)
        
        # Draw component name
        name_text = self.name if self.name else "V"
        name_rect = QRectF(-self._radius, -self._radius - 20, 
                          self._radius * 2, 12)
        painter.drawText(name_rect, Qt.AlignmentFlag.AlignCenter, name_text)
        
        # Draw voltage value from properties
        voltage_value = self.properties.get('Voltage', self.value or '5V')
        value_rect = QRectF(-self._radius, self._radius + 8, 
                           self._radius * 2, 12)
        painter.drawText(value_rect, Qt.AlignmentFlag.AlignCenter, voltage_value)
    
    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle of the voltage source"""
        margin = 10
        return QRectF(-self._radius - margin, 
                     -self._radius - self._terminal_length - margin, 
                     (self._radius + margin) * 2, 
                     (self._radius + self._terminal_length + margin) * 2)
    
    def shape(self) -> QPainterPath:
        """Return the shape of the voltage source for collision detection"""
        path = QPainterPath()
        
        # Add main circle
        path.addEllipse(-self._radius, -self._radius, 
                       self._radius * 2, self._radius * 2)
        
        # Add terminal areas
        for terminal in self._terminals:
            terminal_rect = QRectF(terminal['x'] - 5, terminal['y'] - 5, 10, 10)
            path.addEllipse(terminal_rect)
        
        return path
    
    def update_terminals_after_rotation(self):
        """Update terminal positions after rotation"""
        # Terminals are now handled automatically in get_terminal_position()
        pass
    
    def get_spice_model(self, node1: str, node2: str) -> str:
        """Get SPICE model string - to be overridden by subclasses"""
        return f"V{self.name} {node1} {node2} 0V"


class DCVoltageSource(VoltageSourceBase):
    """DC Voltage Source component"""
    
    def __init__(self, name: str = "V", value: str = "5V"):
        super().__init__(name, value)
        
        # Initialize DC voltage properties
        self.properties = {
            'Voltage': '5V'
        }
    
    def _draw_source_symbol(self, painter: QPainter):
        """Draw DC voltage source symbol (+ and -)"""
        # Set up font for symbols
        font = QFont("Arial", 16, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(Qt.GlobalColor.black)
        
        # Draw + symbol in top half
        plus_rect = QRectF(-self._radius, -self._radius, 
                          self._radius * 2, self._radius)
        painter.drawText(plus_rect, Qt.AlignmentFlag.AlignCenter, "+")
        
        # Draw - symbol in bottom half
        minus_rect = QRectF(-self._radius, 0, 
                           self._radius * 2, self._radius)
        painter.drawText(minus_rect, Qt.AlignmentFlag.AlignCenter, "−")
    
    def _get_properties_config(self):
        """Get properties configuration for the DC voltage source dialog"""
        return {
            'Voltage': {
                'type': 'text',
                'placeholder': 'e.g., 5V, 12V, 3.3V',
                'tooltip': 'DC voltage value'
            }
        }
    
    def get_spice_model(self, node1: str, node2: str) -> str:
        """Get SPICE model string for DC voltage source"""
        voltage = self.properties.get('Voltage', '5V')
        return f"V{self.name} {node1} {node2} DC {voltage}"


class ACVoltageSource(VoltageSourceBase):
    """AC Voltage Source (Sine Wave) component"""
    
    def __init__(self, name: str = "V", value: str = "5V"):
        super().__init__(name, value)
        
        # Initialize AC voltage properties
        self.properties = {
            'DC Offset': '0V',
            'Amplitude': '5V',
            'Frequency': '1kHz',
            'AC Magnitude': '1V',
            'AC Phase': '0'
        }
    
    def _draw_source_symbol(self, painter: QPainter):
        """Draw AC voltage source symbol (sine wave)"""
        # Set up pen for sine wave
        pen = QPen(Qt.GlobalColor.black, 2)
        painter.setPen(pen)
        
        # Draw sine wave symbol
        wave_rect = QRectF(-self._radius + 5, -self._radius + 5, 
                          (self._radius - 5) * 2, (self._radius - 5) * 2)
        
        # Create sine wave path
        path = QPainterPath()
        center_x = wave_rect.center().x()
        center_y = wave_rect.center().y()
        width = wave_rect.width()
        height = wave_rect.height()
        
        # Draw sine wave
        path.moveTo(center_x - width/2, center_y)
        for i in range(0, int(width)):
            x = center_x - width/2 + i
            y = center_y - (height/4) * (0.7 * (i / width * 4 * 3.14159))
            path.lineTo(x, y)
        
        painter.drawPath(path)
    
    def _get_properties_config(self):
        """Get properties configuration for the AC voltage source dialog"""
        return {
            'DC Offset': {
                'type': 'text',
                'placeholder': 'e.g., 0V, 2.5V',
                'tooltip': 'DC offset voltage'
            },
            'Amplitude': {
                'type': 'text',
                'placeholder': 'e.g., 5V, 10V',
                'tooltip': 'Peak amplitude of sine wave'
            },
            'Frequency': {
                'type': 'text',
                'placeholder': 'e.g., 1kHz, 50Hz',
                'tooltip': 'Frequency of sine wave'
            },
            'AC Magnitude': {
                'type': 'text',
                'placeholder': 'e.g., 1V',
                'tooltip': 'AC magnitude for .ac analysis'
            },
            'AC Phase': {
                'type': 'text',
                'placeholder': 'e.g., 0, 90',
                'tooltip': 'AC phase in degrees'
            }
        }
    
    def get_spice_model(self, node1: str, node2: str) -> str:
        """Get SPICE model string for AC voltage source"""
        dc_offset = self.properties.get('DC Offset', '0V')
        amplitude = self.properties.get('Amplitude', '5V')
        frequency = self.properties.get('Frequency', '1kHz')
        ac_magnitude = self.properties.get('AC Magnitude', '1V')
        ac_phase = self.properties.get('AC Phase', '0')
        
        return f"V{self.name} {node1} {node2} SIN({dc_offset} {amplitude} {frequency}) AC {ac_magnitude} {ac_phase}"


class PulseSource(VoltageSourceBase):
    """Pulse/Square Wave Source component"""
    
    def __init__(self, name: str = "V", value: str = "5V"):
        super().__init__(name, value)
        
        # Initialize pulse source properties
        self.properties = {
            'Initial Value': '0V',
            'Pulsed Value': '5V',
            'Time Delay': '0s',
            'Rise Time': '1ns',
            'Fall Time': '1ns',
            'Pulse Width': '1ms',
            'Period': '2ms'
        }
    
    def _draw_source_symbol(self, painter: QPainter):
        """Draw pulse source symbol (square wave)"""
        # Set up pen for pulse symbol
        pen = QPen(Qt.GlobalColor.black, 2)
        painter.setPen(pen)
        
        # Draw pulse symbol inside circle
        symbol_rect = QRectF(-self._radius + 8, -self._radius + 8, 
                            (self._radius - 8) * 2, (self._radius - 8) * 2)
        
        # Draw square pulse pattern
        left = int(symbol_rect.left())
        right = int(symbol_rect.right())
        top = int(symbol_rect.top())
        bottom = int(symbol_rect.bottom())
        mid_y = int(symbol_rect.center().y())
        
        # Low line
        painter.drawLine(left, mid_y, int(left + symbol_rect.width() * 0.3), mid_y)
        # Vertical up
        painter.drawLine(int(left + symbol_rect.width() * 0.3), mid_y, 
                        int(left + symbol_rect.width() * 0.3), int(top + symbol_rect.height() * 0.2))
        # High line
        painter.drawLine(int(left + symbol_rect.width() * 0.3), int(top + symbol_rect.height() * 0.2),
                        int(left + symbol_rect.width() * 0.7), int(top + symbol_rect.height() * 0.2))
        # Vertical down
        painter.drawLine(int(left + symbol_rect.width() * 0.7), int(top + symbol_rect.height() * 0.2),
                        int(left + symbol_rect.width() * 0.7), mid_y)
        # Low line
        painter.drawLine(int(left + symbol_rect.width() * 0.7), mid_y, right, mid_y)
    
    def _get_properties_config(self):
        """Get properties configuration for the pulse source dialog"""
        return {
            'Initial Value': {
                'type': 'text',
                'placeholder': 'e.g., 0V, 1V',
                'tooltip': 'Initial voltage value'
            },
            'Pulsed Value': {
                'type': 'text',
                'placeholder': 'e.g., 5V, 3.3V',
                'tooltip': 'Pulsed voltage value'
            },
            'Time Delay': {
                'type': 'text',
                'placeholder': 'e.g., 0s, 1ms',
                'tooltip': 'Time delay before pulse starts'
            },
            'Rise Time': {
                'type': 'text',
                'placeholder': 'e.g., 1ns, 100ps',
                'tooltip': 'Rise time of pulse'
            },
            'Fall Time': {
                'type': 'text',
                'placeholder': 'e.g., 1ns, 100ps',
                'tooltip': 'Fall time of pulse'
            },
            'Pulse Width': {
                'type': 'text',
                'placeholder': 'e.g., 1ms, 500us',
                'tooltip': 'Width of the pulse'
            },
            'Period': {
                'type': 'text',
                'placeholder': 'e.g., 2ms, 1s',
                'tooltip': 'Period of the pulse train'
            }
        }
    
    def get_spice_model(self, node1: str, node2: str) -> str:
        """Get SPICE model string for pulse source"""
        initial = self.properties.get('Initial Value', '0V')
        pulsed = self.properties.get('Pulsed Value', '5V')
        delay = self.properties.get('Time Delay', '0s')
        rise = self.properties.get('Rise Time', '1ns')
        fall = self.properties.get('Fall Time', '1ns')
        width = self.properties.get('Pulse Width', '1ms')
        period = self.properties.get('Period', '2ms')
        
        return f"V{self.name} {node1} {node2} PULSE({initial} {pulsed} {delay} {rise} {fall} {width} {period})"
