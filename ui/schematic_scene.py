"""
Schematic scene for PyEWB
Handles component placement and wire drawing
"""

from PyQt6.QtWidgets import QGraphicsScene, QGraphicsItem, QMenu
from PyQt6.QtCore import Qt, QPointF, pyqtSignal, QRectF
from PyQt6.QtGui import QPen, QPainter, QAction, QFont
from components.resistor import Resistor
from components.wire import Wire
from components.base import BaseComponent
from ui.canvas_settings import CanvasSettings
from config.config_manager import config_manager


class SchematicScene(QGraphicsScene):
    """Graphics scene for the schematic editor"""
    
    # Signals
    component_added = pyqtSignal(object)  # Emitted when a component is added
    wire_added = pyqtSignal(object)       # Emitted when a wire is added
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Wire drawing state
        self._wire_mode = False
        self._wire_drawing_mode = False
        self._current_wire = None
        self._start_component = None
        self._start_terminal_index = -1
        
        # Canvas settings with unit system
        self.settings = CanvasSettings(self)
        
        # Set grid size to match component dimensions using configuration
        self.settings.set_grid_size_for_component_type("resistor", config_manager)
        
        # Grid settings (legacy - now managed by settings)
        self._grid_size = 20
        self._show_grid = True
        self._snap_to_grid = True  # Always enable grid snapping
        
        # Set up scene properties
        self.setSceneRect(-2000, -2000, 4000, 4000)
        self.setBackgroundBrush(Qt.GlobalColor.white)
    
    def drawBackground(self, painter, rect):
        """Draw the background grid with dots and Level of Detail"""
        super().drawBackground(painter, rect)
        
        if self._show_grid:
            # Get current zoom level from view
            view = self.views()[0] if self.views() else None
            if view and hasattr(view, 'should_show_fine_grid'):
                show_fine_grid = view.should_show_fine_grid()
            else:
                show_fine_grid = True
            
            # Get grid size in pixels from settings
            grid_size_px = self.settings.get_grid_size_pixels()
            
            # Set up grid pen for dots - make them thinner and more subtle
            if show_fine_grid:
                grid_pen = QPen(Qt.GlobalColor.lightGray, 1)  # Thinner dots
            else:
                # Coarse grid for low zoom
                grid_pen = QPen(Qt.GlobalColor.lightGray, 2)  # Slightly thicker for low zoom
                grid_size_px = grid_size_px * 4  # Larger grid spacing
            
            painter.setPen(grid_pen)
            
            # Get the visible area
            left = int(rect.left()) - (int(rect.left()) % int(grid_size_px))
            top = int(rect.top()) - (int(rect.top()) % int(grid_size_px))
            right = int(rect.right())
            bottom = int(rect.bottom())
            
            # Draw grid dots instead of lines - use circles for better visibility
            x = left
            while x <= right:
                y = top
                while y <= bottom:
                    # Draw circular dots - smaller and more subtle
                    dot_radius = 1.0 if show_fine_grid else 1.5
                    painter.drawEllipse(int(x - dot_radius), int(y - dot_radius), 
                                      int(dot_radius * 2), int(dot_radius * 2))
                    y += int(grid_size_px)
                x += int(grid_size_px)
    
    def snap_to_grid(self, point: QPointF) -> QPointF:
        """Snap a point to the grid using unit system"""
        if not self._snap_to_grid:
            return point
        
        return self.settings.snap_to_grid(point)
    
    def snap_to_terminal(self, point: QPointF, threshold: float = 20.0) -> QPointF:
        """Snap to the nearest terminal if within threshold"""
        min_distance = float('inf')
        nearest_point = point
        
        for item in self.items():
            if hasattr(item, 'find_nearest_terminal'):
                terminal_index = item.find_nearest_terminal(point.x(), point.y(), threshold)
                if terminal_index >= 0:
                    term_x, term_y = item.get_terminal_position(terminal_index)
                    distance = ((point.x() - term_x) ** 2 + (point.y() - term_y) ** 2) ** 0.5
                    
                    if distance < min_distance:
                        min_distance = distance
                        nearest_point = QPointF(term_x, term_y)
        
        return nearest_point
    
    def smart_snap(self, point: QPointF) -> QPointF:
        """Smart snapping that prioritizes terminals over grid"""
        # First try to snap to terminal
        snapped_point = self.snap_to_terminal(point)
        
        # If we didn't snap to a terminal, try grid
        if snapped_point == point:
            snapped_point = self.snap_to_grid(point)
        
        return snapped_point
    
    def set_grid_size(self, size: int):
        """Set the grid size"""
        self._grid_size = size
        self.update()
    
    def set_show_grid(self, show: bool):
        """Show or hide the grid"""
        self._show_grid = show
        self.update()
    
    def set_snap_to_grid(self, snap: bool):
        """Enable or disable snap to grid"""
        self._snap_to_grid = snap
    
    def toggle_grid(self):
        """Toggle grid visibility"""
        self._show_grid = not self._show_grid
        self.update()
    
    def toggle_snap_to_grid(self):
        """Toggle snap to grid"""
        self._snap_to_grid = not self._snap_to_grid
    
    def set_wire_mode(self, enabled: bool):
        """Set wire mode on/off"""
        self._wire_mode = enabled
        if not enabled:
            # Cancel any active wire drawing
            self.cancel_wire_drawing()
    
    def add_resistor(self, x: float, y: float, name: str = "R", value: str = "1k") -> Resistor:
        """Add a resistor to the scene"""
        resistor = Resistor(name, value)
        # Snap to grid
        snapped_pos = self.snap_to_grid(QPointF(x, y))
        resistor.setPos(snapped_pos)
        self.addItem(resistor)
        self.component_added.emit(resistor)
        return resistor
    
    def start_wire_drawing(self, component, terminal_index: int):
        """Start drawing a wire from a component terminal"""
        if not self._wire_drawing_mode:
            self._wire_drawing_mode = True
            self._start_component = component
            self._start_terminal_index = terminal_index
            
            # Create temporary wire
            self._current_wire = Wire()
            self._current_wire.is_temporary = True
            self.addItem(self._current_wire)
            
            # Set start point
            start_pos = component.get_terminal_position(terminal_index)
            self._current_wire.start_point = QPointF(start_pos[0], start_pos[1])
            
            print(f"Started wire drawing from {component.name} terminal {terminal_index} at {start_pos}")
    
    def update_wire_drawing(self, mouse_pos: QPointF):
        """Update wire drawing as mouse moves"""
        if self._wire_drawing_mode and self._current_wire:
            # mouse_pos is already in scene coordinates
            self._current_wire.end_point = mouse_pos
    
    def finish_wire_drawing(self, component=None, terminal_index: int = -1):
        """Finish drawing a wire"""
        if self._wire_drawing_mode and self._current_wire:
            if component and terminal_index >= 0:
                # Complete the wire connection
                self._current_wire.is_temporary = False
                self._current_wire.connect_terminals(self._start_component, component)
                self.wire_added.emit(self._current_wire)
            else:
                # Cancel wire drawing
                self.removeItem(self._current_wire)
            
            # Reset wire drawing state
            self._wire_drawing_mode = False
            self._current_wire = None
            self._start_component = None
            self._start_terminal_index = -1
    
    def cancel_wire_drawing(self):
        """Cancel current wire drawing"""
        if self._wire_drawing_mode and self._current_wire:
            self.removeItem(self._current_wire)
            self._wire_drawing_mode = False
            self._current_wire = None
            self._start_component = None
            self._start_terminal_index = -1
    
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.LeftButton and self._wire_mode:
            # Get item under mouse
            # Get the view's transform for proper item detection
            if self.views():
                view_transform = self.views()[0].transform()
                item = self.itemAt(event.scenePos(), view_transform)
            else:
                item = None
            print(f"Mouse press at {event.scenePos()}, item: {item}")
            
            if self._wire_drawing_mode:
                # Finish wire drawing
                if item and hasattr(item, 'find_nearest_terminal'):
                    terminal_index = item.find_nearest_terminal(
                        event.scenePos().x(), event.scenePos().y()
                    )
                    print(f"Found terminal index: {terminal_index}")
                    if terminal_index >= 0:
                        self.finish_wire_drawing(item, terminal_index)
                    else:
                        self.cancel_wire_drawing()
                else:
                    self.cancel_wire_drawing()
            else:
                # Start wire drawing if clicking on a component terminal
                if item and hasattr(item, 'find_nearest_terminal'):
                    terminal_index = item.find_nearest_terminal(
                        event.scenePos().x(), event.scenePos().y()
                    )
                    print(f"Found terminal index: {terminal_index}")
                    if terminal_index >= 0:
                        self.start_wire_drawing(item, terminal_index)
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events"""
        if self._wire_drawing_mode:
            self.update_wire_drawing(event.scenePos())
        
        # Update coordinate display for debugging
        self._update_coordinate_display(event.scenePos())
        
        super().mouseMoveEvent(event)
    
    def _update_coordinate_display(self, scene_pos):
        """Update coordinate display for debugging"""
        if hasattr(self, 'settings') and self.settings:
            # Convert to grid coordinates
            grid_size_px = self.settings.get_grid_size_pixels()
            grid_x = round(scene_pos.x() / grid_size_px)
            grid_y = round(scene_pos.y() / grid_size_px)
            
            # Convert to units
            unit_x = self.settings.pixels_to_units(scene_pos.x())
            unit_y = self.settings.pixels_to_units(scene_pos.y())
            unit_name = self.settings.get_unit_display_name()
            
            # Update status bar if available
            if self.views():
                view = self.views()[0]
                if hasattr(view, 'coordinate_updated'):
                    coord_text = f"X: {unit_x:.2f} {unit_name}, Y: {unit_y:.2f} {unit_name} | Grid: ({grid_x}, {grid_y})"
                    view.coordinate_updated.emit(coord_text)
    
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key.Key_Escape:
            if self._wire_drawing_mode:
                self.cancel_wire_drawing()
        
        super().keyPressEvent(event)
    
    def contextMenuEvent(self, event):
        """Handle context menu events"""
        if not self._wire_mode:  # Only show context menu when not in wire mode
            # Get item under mouse with proper transform
            if self.views():
                view_transform = self.views()[0].transform()
                item = self.itemAt(event.scenePos(), view_transform)
            else:
                item = None
                
            if item and hasattr(item, 'rotate_90_clockwise'):  # Component
                # Convert scene position to global position
                if self.views():
                    global_pos = self.views()[0].mapToGlobal(
                        self.views()[0].mapFromScene(event.scenePos())
                    )
                    self.show_component_context_menu(global_pos, item)
            else:
                # Convert scene position to global position
                if self.views():
                    global_pos = self.views()[0].mapToGlobal(
                        self.views()[0].mapFromScene(event.scenePos())
                    )
                    self.show_scene_context_menu(global_pos)
        else:
            super().contextMenuEvent(event)
    
    def show_component_context_menu(self, global_pos, component):
        """Show context menu for a component"""
        menu = QMenu()
        
        # Rotation actions
        rotate_cw_action = QAction("Rotate 90° Clockwise", self)
        rotate_cw_action.triggered.connect(lambda: component.rotate_90_clockwise())
        menu.addAction(rotate_cw_action)
        
        rotate_ccw_action = QAction("Rotate 90° Counterclockwise", self)
        rotate_ccw_action.triggered.connect(lambda: component.rotate_90_counterclockwise())
        menu.addAction(rotate_ccw_action)
        
        rotate_180_action = QAction("Rotate 180°", self)
        rotate_180_action.triggered.connect(lambda: component.rotate_180())
        menu.addAction(rotate_180_action)
        
        menu.addSeparator()
        
        # Delete action
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.removeItem(component))
        menu.addAction(delete_action)
        
        menu.exec(global_pos)
    
    def show_scene_context_menu(self, global_pos):
        """Show context menu for the scene"""
        menu = QMenu()
        
        # Add component actions
        add_resistor_action = QAction("Add Resistor", self)
        add_resistor_action.triggered.connect(self.add_resistor_at_cursor)
        menu.addAction(add_resistor_action)
        
        menu.exec(global_pos)
    
    def add_resistor_at_cursor(self):
        """Add resistor at cursor position"""
        # This would need to be connected to the main window
        pass
    
    def get_components(self):
        """Get all components in the scene (excluding wires)"""
        components = []
        for item in self.items():
            if isinstance(item, BaseComponent) and not isinstance(item, Wire):
                components.append(item)
        return components
    
    def get_wires(self):
        """Get all wires in the scene"""
        wires = []
        for item in self.items():
            if isinstance(item, Wire):
                wires.append(item)
        return wires
