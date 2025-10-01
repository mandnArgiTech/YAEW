"""
Wire component for PyEWB
Represents connections between component terminals with right-angle bends
"""

from PyQt6.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from PyQt6.QtCore import QRectF, Qt, QPointF
from PyQt6.QtGui import QPainter, QPainterPath, QPen
from .base import BaseComponent


class Wire(QGraphicsItem):
    """Wire connecting two component terminals with right-angle bends"""
    
    def __init__(self, start_terminal=None, end_terminal=None):
        super().__init__()
        
        self._start_terminal = start_terminal
        self._end_terminal = end_terminal
        self._start_point = QPointF(0, 0)
        self._end_point = QPointF(0, 0)
        self._is_temporary = False  # True when drawing wire
        
        # Multi-segment support for right-angle bends
        self._segments = []  # List of QPointF for segment points
        self._current_drawing_point = QPointF(0, 0)  # Current mouse position during drawing
        
        # Snap feedback
        self._snap_info = {'snapped': False, 'type': 'none', 'distance': 0}
        
        # Enable selection
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, True)
    
    @property
    def start_terminal(self):
        """Get start terminal"""
        return self._start_terminal
    
    @start_terminal.setter
    def start_terminal(self, terminal):
        """Set start terminal"""
        self._start_terminal = terminal
        self.update()
    
    @property
    def end_terminal(self):
        """Get end terminal"""
        return self._end_terminal
    
    @end_terminal.setter
    def end_terminal(self, terminal):
        """Set end terminal"""
        self._end_terminal = terminal
        self.update()
    
    @property
    def start_point(self):
        """Get start point"""
        return self._start_point
    
    @start_point.setter
    def start_point(self, point):
        """Set start point"""
        self._start_point = point
        self.update()
    
    @property
    def end_point(self):
        """Get end point"""
        return self._end_point
    
    @end_point.setter
    def end_point(self, point):
        """Set end point"""
        self._end_point = point
        self.update()
    
    @property
    def is_temporary(self):
        """Check if wire is temporary (being drawn)"""
        return self._is_temporary
    
    @is_temporary.setter
    def is_temporary(self, value):
        """Set temporary state"""
        self._is_temporary = value
        self.update()
    
    def add_segment(self, point: QPointF):
        """Add a segment point for right-angle routing"""
        self._segments.append(point)
        self.update()
    
    def set_current_drawing_point(self, point: QPointF):
        """Set the current mouse position during wire drawing"""
        self._current_drawing_point = point
        self.update()
    
    def set_snap_info(self, snap_info: dict):
        """Set snap information for visual feedback"""
        self._snap_info = snap_info
        self.update()
    
    def clear_segments(self):
        """Clear all segment points"""
        self._segments.clear()
        self.update()
    
    def get_wire_path(self) -> list:
        """Get the complete wire path including segments and current drawing point"""
        path_points = []
        
        # Start from the first terminal
        path_points.append(self._start_point)
        
        # Add all segment points
        path_points.extend(self._segments)
        
        # Add current drawing point if in temporary mode
        if self._is_temporary:
            path_points.append(self._current_drawing_point)
        else:
            # Add end terminal point for completed wires
            path_points.append(self._end_point)
        
        return path_points
    
    def _calculate_right_angle_bend(self, start: QPointF, end: QPointF) -> QPointF:
        """Calculate the intermediate point for a right-angle bend"""
        # Simple right-angle routing: first horizontal, then vertical
        return QPointF(end.x(), start.y())
    
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        """Paint the wire with right-angle bends"""
        # Set up painter
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Set pen based on state and snap feedback
        if self.isSelected():
            pen = QPen(Qt.GlobalColor.red, 3)
        elif self._is_temporary:
            # Show different colors based on snap type
            if self._snap_info.get('snapped', False):
                if self._snap_info.get('type') == 'terminal':
                    pen = QPen(Qt.GlobalColor.blue, 2, Qt.PenStyle.DashLine)  # Blue for terminal snap
                elif self._snap_info.get('type') == 'grid':
                    pen = QPen(Qt.GlobalColor.green, 2, Qt.PenStyle.DashLine)  # Green for grid snap
                else:
                    pen = QPen(Qt.GlobalColor.gray, 2, Qt.PenStyle.DashLine)
            else:
                pen = QPen(Qt.GlobalColor.gray, 2, Qt.PenStyle.DashLine)
        else:
            pen = QPen(Qt.GlobalColor.black, 2)
        
        painter.setPen(pen)
        
        # Get the complete wire path
        path_points = self.get_wire_path()
        
        # Draw the wire with right-angle bends
        if len(path_points) >= 2:
            # Start from first point
            current_point = path_points[0]
            
            # Draw each segment
            for i in range(1, len(path_points)):
                next_point = path_points[i]
                
                # For simple two-point wires, draw direct line
                if len(path_points) == 2:
                    painter.drawLine(current_point, next_point)
                else:
                    # For multi-segment wires, calculate right-angle bends
                    if i == 1:  # First segment from start
                        bend_point = self._calculate_right_angle_bend(current_point, next_point)
                        painter.drawLine(current_point, bend_point)
                        painter.drawLine(bend_point, next_point)
                    elif i == len(path_points) - 1:  # Last segment to end
                        bend_point = self._calculate_right_angle_bend(current_point, next_point)
                        painter.drawLine(current_point, bend_point)
                        painter.drawLine(bend_point, next_point)
                    else:
                        # Intermediate segments - draw direct line
                        painter.drawLine(current_point, next_point)
                
                current_point = next_point
    
    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle of the wire"""
        path_points = self.get_wire_path()
        
        if not path_points:
            return QRectF()
        
        # Calculate bounds from all points
        min_x = min(p.x() for p in path_points)
        min_y = min(p.y() for p in path_points)
        max_x = max(p.x() for p in path_points)
        max_y = max(p.y() for p in path_points)
        
        # Add some margin for the pen width
        margin = 2
        return QRectF(
            min_x - margin,
            min_y - margin,
            max_x - min_x + 2 * margin,
            max_y - min_y + 2 * margin
        )
    
    def shape(self) -> QPainterPath:
        """Return the shape of the wire for collision detection"""
        path = QPainterPath()
        path_points = self.get_wire_path()
        
        if len(path_points) >= 2:
            path.moveTo(path_points[0])
            
            # Create path with all segments
            for i in range(1, len(path_points)):
                path.lineTo(path_points[i])
        
        return path
    
    def update_position(self):
        """Update wire position based on terminal positions"""
        if self._start_terminal and hasattr(self._start_terminal, 'get_terminal_position'):
            # Get terminal position from component using stored terminal index
            start_pos = self._start_terminal.get_terminal_position(self._start_terminal_index)
            self._start_point = QPointF(start_pos[0], start_pos[1])
        
        if self._end_terminal and hasattr(self._end_terminal, 'get_terminal_position'):
            # Get terminal position from component using stored terminal index
            end_pos = self._end_terminal.get_terminal_position(self._end_terminal_index)
            self._end_point = QPointF(end_pos[0], end_pos[1])
        
        # Debug output to verify wire position updates (can be removed in production)
        # print(f"Wire updated: start={self._start_point}, end={self._end_point}")
        
        self.update()
    
    def connect_terminals(self, start_component, end_component, start_terminal_index=0, end_terminal_index=0):
        """Connect wire to two component terminals"""
        self._start_terminal = start_component
        self._end_terminal = end_component
        self._start_terminal_index = start_terminal_index
        self._end_terminal_index = end_terminal_index
        
        # Update positions based on terminal positions
        if start_component and hasattr(start_component, 'get_terminal_position'):
            start_pos = start_component.get_terminal_position(start_terminal_index)
            self._start_point = QPointF(start_pos[0], start_pos[1])
        
        if end_component and hasattr(end_component, 'get_terminal_position'):
            end_pos = end_component.get_terminal_position(end_terminal_index)
            self._end_point = QPointF(end_pos[0], end_pos[1])
        
        # Add wire to terminal connections
        if start_component and hasattr(start_component, 'terminals'):
            if 0 <= start_terminal_index < len(start_component.terminals):
                start_component.terminals[start_terminal_index]['connections'].append(self)
                # print(f"Added wire to {start_component.name} terminal {start_terminal_index}, total connections: {len(start_component.terminals[start_terminal_index]['connections'])}")
        
        if end_component and hasattr(end_component, 'terminals'):
            if 0 <= end_terminal_index < len(end_component.terminals):
                end_component.terminals[end_terminal_index]['connections'].append(self)
                # print(f"Added wire to {end_component.name} terminal {end_terminal_index}, total connections: {len(end_component.terminals[end_terminal_index]['connections'])}")
        
        self.update()
