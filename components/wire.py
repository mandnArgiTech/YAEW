"""
Wire component for PyEWB
Represents connections between component terminals
"""

from PyQt6.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from PyQt6.QtCore import QRectF, Qt, QPointF
from PyQt6.QtGui import QPainter, QPainterPath, QPen
from .base import BaseComponent


class Wire(QGraphicsItem):
    """Wire connecting two component terminals"""
    
    def __init__(self, start_terminal=None, end_terminal=None):
        super().__init__()
        
        self._start_terminal = start_terminal
        self._end_terminal = end_terminal
        self._start_point = QPointF(0, 0)
        self._end_point = QPointF(0, 0)
        self._is_temporary = False  # True when drawing wire
        
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
    
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        """Paint the wire"""
        # Set up painter
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Set pen based on state
        if self.isSelected():
            pen = QPen(Qt.GlobalColor.red, 3)
        elif self._is_temporary:
            pen = QPen(Qt.GlobalColor.gray, 2, Qt.PenStyle.DashLine)
        else:
            pen = QPen(Qt.GlobalColor.black, 2)
        
        painter.setPen(pen)
        
        # Draw the wire line
        painter.drawLine(self._start_point, self._end_point)
    
    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle of the wire"""
        # Add some margin for the pen width
        margin = 2
        return QRectF(
            min(self._start_point.x(), self._end_point.x()) - margin,
            min(self._start_point.y(), self._end_point.y()) - margin,
            abs(self._end_point.x() - self._start_point.x()) + 2 * margin,
            abs(self._end_point.y() - self._start_point.y()) + 2 * margin
        )
    
    def shape(self) -> QPainterPath:
        """Return the shape of the wire for collision detection"""
        path = QPainterPath()
        path.moveTo(self._start_point)
        path.lineTo(self._end_point)
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
