"""
Movable Label Component for PyEWB
Allows component labels to be moved independently by mouse
"""

from PyQt6.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QFont, QPen, QBrush, QFontMetrics


class MovableLabel(QGraphicsItem):
    """A movable text label that can be positioned independently"""
    
    def __init__(self, text: str, parent_component=None, label_type="name"):
        super().__init__()
        self.text = text
        self.parent_component = parent_component
        self.label_type = label_type  # "name" or "value"
        
        # Set up the label
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        
        # Font settings
        self.font = QFont("Arial", 10, QFont.Weight.Bold)
        self.font_metrics = QFontMetrics(self.font)
        
        # Calculate initial size
        self._update_size()
        
        # Initialize drag tracking
        self._drag_start_pos = QPointF(0, 0)
        
        # Default position offset from parent
        self.default_offset = QPointF(0, 0)
        if label_type == "name":
            self.default_offset = QPointF(0, -15)  # Above component
        elif label_type == "value":
            self.default_offset = QPointF(0, 15)   # Below component
    
    def _update_size(self):
        """Update the size based on current text"""
        self.text_rect = self.font_metrics.boundingRect(self.text)
        self._width = self.text_rect.width() + 4  # Add padding
        self._height = self.text_rect.height() + 4
    
    def set_text(self, text: str):
        """Update the label text"""
        self.text = text
        self._update_size()
        self.update()
    
    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle of the label"""
        return QRectF(0, 0, self._width, self._height)
    
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        """Paint the label"""
        painter.setFont(self.font)
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.setBrush(QBrush(Qt.GlobalColor.white, Qt.BrushStyle.SolidPattern))
        
        # Draw background rectangle
        painter.drawRect(0, 0, self._width, self._height)
        
        # Draw text centered in the rectangle
        text_rect = QRectF(0, 0, self._width, self._height)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.text)
    
    def itemChange(self, change, value):
        """Handle item changes"""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            # Notify parent component if it exists
            if self.parent_component and hasattr(self.parent_component, 'on_label_moved'):
                self.parent_component.on_label_moved(self, value)
        
        return super().itemChange(change, value)
    
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Store the initial click position in scene coordinates
            self._drag_start_pos = event.scenePos() - self.pos()
            # Bring to front when clicked
            self.setZValue(1000)
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events for dragging"""
        if event.buttons() == Qt.MouseButton.LeftButton:
            # Calculate new position - mouse position in scene coordinates
            new_pos = event.scenePos() - self._drag_start_pos
            self.setPos(new_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Labels don't snap to grid - they maintain their exact positions
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def reset_position(self):
        """Reset label to default position relative to parent"""
        if self.parent_component:
            parent_pos = self.parent_component.pos()
            self.setPos(parent_pos + self.default_offset)
    
    def get_offset_from_parent(self):
        """Get the current offset from parent component"""
        if self.parent_component:
            return self.pos() - self.parent_component.pos()
        return QPointF(0, 0)
