"""
Base component class for PyEWB
Abstract base class for all electronic components
"""

from PyQt6.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QPainter, QPainterPath
import uuid


class BaseComponent(QGraphicsItem):
    """Abstract base class for all electronic components"""
    
    def __init__(self, name: str = "", value: str = ""):
        super().__init__()
        
        # Component properties
        self._name = name
        self._value = value
        self._id = str(uuid.uuid4())
        self._rotation = 0  # Rotation angle in degrees
        
        # Generic properties dictionary for component parameters
        self.properties = {}
        
        # Connection points (terminals/pins)
        self._terminals = []
        
        # Enable item interaction
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        
        # Set initial position
        self.setPos(0, 0)
    
    @property
    def name(self) -> str:
        """Get component name"""
        return self._name
    
    @name.setter
    def name(self, value: str):
        """Set component name"""
        self._name = value
        self.update()
    
    @property
    def value(self) -> str:
        """Get component value"""
        return self._value
    
    @value.setter
    def value(self, value: str):
        """Set component value"""
        self._value = value
        self.update()
    
    @property
    def id(self) -> str:
        """Get unique component ID"""
        return self._id
    
    @property
    def rotation(self) -> float:
        """Get component rotation in degrees"""
        return self._rotation
    
    @rotation.setter
    def rotation(self, angle: float):
        """Set component rotation in degrees"""
        self._rotation = angle
        self.setRotation(angle)
        self.update()
    
    @property
    def terminals(self) -> list:
        """Get list of terminals"""
        return self._terminals
    
    def add_terminal(self, x: float, y: float, name: str = "") -> dict:
        """
        Add a connection terminal to the component
        
        Args:
            x: X coordinate relative to component center
            y: Y coordinate relative to component center
            name: Terminal name (optional)
            
        Returns:
            Dictionary with terminal information
        """
        terminal = {
            'x': x,
            'y': y,
            'name': name,
            'connections': []  # List of connected wires
        }
        self._terminals.append(terminal)
        return terminal
    
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
            
            return (self.pos().x() + rotated_x, 
                   self.pos().y() + rotated_y)
        return (0, 0)
    
    def find_nearest_terminal(self, x: float, y: float, threshold: float = 15.0) -> int:
        """
        Find the nearest terminal to the given coordinates
        
        Args:
            x: X coordinate
            y: Y coordinate
            threshold: Maximum distance to consider
            
        Returns:
            Index of nearest terminal, or -1 if none within threshold
        """
        min_distance = float('inf')
        nearest_index = -1
        
        for i in range(len(self._terminals)):
            term_x, term_y = self.get_terminal_position(i)
            distance = ((x - term_x) ** 2 + (y - term_y) ** 2) ** 0.5
            
            if distance < min_distance and distance <= threshold:
                min_distance = distance
                nearest_index = i
        
        return nearest_index
    
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        """Paint the component on the graphics scene - must be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement paint() method")
    
    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle of the component - must be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement boundingRect() method")
    
    def shape(self) -> QPainterPath:
        """Return the shape of the component for collision detection"""
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path
    
    def itemChange(self, change, value):
        """Handle item changes (position, selection, etc.)"""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            # Update terminal positions when component moves
            self.update()
            # Update all connected wires
            self._update_connected_wires()
        
        return super().itemChange(change, value)
    
    def _update_connected_wires(self):
        """Update all wires connected to this component's terminals"""
        # print(f"Updating connected wires for {self.name}")
        for i, terminal in enumerate(self._terminals):
            # print(f"  Terminal {i} has {len(terminal['connections'])} connections")
            for wire in terminal['connections']:
                if hasattr(wire, 'update_position'):
                    wire.update_position()
    
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Don't force selection - let Qt handle multi-selection properly
            # Only set selected if no modifier keys are pressed (for single selection)
            if not (event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)):
                self.setSelected(True)
            # Store the initial click position for dragging
            self._drag_start_pos = event.pos()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events for dragging with grid snapping"""
        if event.buttons() == Qt.MouseButton.LeftButton:
            # Calculate new position
            new_pos = event.scenePos() - self._drag_start_pos
            
            # Apply grid snapping (always enabled)
            scene = self.scene()
            if scene and hasattr(scene, 'settings') and scene.settings:
                new_pos = scene.settings.snap_to_grid(new_pos)
            
            self.setPos(new_pos)
            
            # Update connected wires during movement
            self._update_connected_wires()
            
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events with final grid snapping"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Apply final grid snapping to ensure perfect alignment
            scene = self.scene()
            if scene and hasattr(scene, 'settings') and scene.settings:
                snapped_pos = scene.settings.snap_to_grid(self.pos())
                self.setPos(snapped_pos)
        super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """Handle double-click events (for editing properties)"""
        self.show_properties_dialog()
        super().mouseDoubleClickEvent(event)
    
    def rotate_90_clockwise(self):
        """Rotate component 90 degrees clockwise"""
        self.rotation = (self._rotation + 90) % 360
        self.update_terminals_after_rotation()
    
    def rotate_90_counterclockwise(self):
        """Rotate component 90 degrees counterclockwise"""
        self.rotation = (self._rotation - 90) % 360
        self.update_terminals_after_rotation()
    
    def rotate_180(self):
        """Rotate component 180 degrees"""
        self.rotation = (self._rotation + 180) % 360
        self.update_terminals_after_rotation()
    
    def mirror(self, direction: str):
        """Mirror component horizontally or vertically"""
        if direction == 'horizontal':
            self.setTransform(self.transform().scale(-1, 1))
        elif direction == 'vertical':
            self.setTransform(self.transform().scale(1, -1))
        self.update_terminals_after_mirror()
    
    def update_terminals_after_mirror(self):
        """Update terminal positions after mirroring"""
        # This method should be overridden by subclasses to handle
        # terminal position updates after mirroring
        pass
    
    def update_terminals_after_rotation(self):
        """Update terminal positions after rotation"""
        # This method should be overridden by subclasses to handle
        # terminal position updates after rotation
        pass
    
    def _get_properties_config(self):
        """Get properties configuration for the component dialog - must be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement _get_properties_config() method")
    
    def show_properties_dialog(self):
        """Show the properties dialog for this component"""
        try:
            from ui.property_dialog import PropertyDialog
            
            config = self._get_properties_config()
            dialog = PropertyDialog(config, self.properties)
            
            if dialog.exec() == PropertyDialog.DialogCode.Accepted:
                # Update properties with new values
                new_properties = dialog.get_values()
                self.properties.update(new_properties)
                
                # Update the component's value property if it exists
                if 'Resistance' in self.properties:
                    self._value = self.properties['Resistance']
                elif 'value' in self.properties:
                    self._value = self.properties['value']
                
                # Trigger repaint
                self.update()
                
        except ImportError:
            print("PropertyDialog not available")
        except Exception as e:
            print(f"Error showing properties dialog: {e}")
