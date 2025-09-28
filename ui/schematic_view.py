"""
Custom Graphics View for PyEWB
Handles zoom, pan, and other view interactions
"""

from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtCore import Qt, QPoint, QTimer, pyqtSignal
from PyQt6.QtGui import QWheelEvent, QPainter, QCursor

# Try to import OpenGL, fall back to regular widget if not available
try:
    from PyQt6.QtOpenGLWidgets import QOpenGLWidget
    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False


class SchematicView(QGraphicsView):
    """Custom graphics view with enhanced zoom and pan capabilities"""
    
    # Signals
    coordinate_updated = pyqtSignal(str)  # Emitted when mouse moves to update coordinates
    zoom_changed = pyqtSignal(float)  # Emitted when zoom level changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Zoom settings
        self._zoom_factor = 1.0
        self._min_zoom = 0.1
        self._max_zoom = 5.0
        self._zoom_step = 0.1
        
        # Panning state
        self._panning = False
        self._pan_start_pos = QPoint()
        
        # Dragging state
        self._dragging = False
        
        # Level of Detail settings
        self._lod_thresholds = {
            'text': 0.5,      # Show text when zoom > 0.5x
            'details': 0.2,   # Show details when zoom > 0.2x
            'grid': 0.1       # Show fine grid when zoom > 0.1x
        }
        
        # Set up OpenGL viewport for hardware acceleration if available
        if OPENGL_AVAILABLE:
            self.setViewport(QOpenGLWidget())
        
        # Set up view properties
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Enable mouse tracking for better interaction
        self.setMouseTracking(True)
        
        # Set up smooth transitions
        self._transition_timer = QTimer()
        self._transition_timer.timeout.connect(self._update_transition)
        self._transition_duration = 200  # ms
        self._transition_start_time = 0
        self._transition_start_transform = None
        self._transition_target_transform = None
    
    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel events for zooming"""
        # Get the wheel delta
        delta = event.angleDelta().y()
        
        # Determine zoom direction
        if delta > 0:
            # Zoom in
            self.zoom_in()
        else:
            # Zoom out
            self.zoom_out()
        
        event.accept()
    
    def mousePressEvent(self, event):
        """Handle mouse press events for panning and box zoom"""
        if event.button() == Qt.MouseButton.MiddleButton:
            # Start panning
            self._panning = True
            self._pan_start_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        elif event.button() == Qt.MouseButton.LeftButton and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # Start box zoom
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            super().mousePressEvent(event)
        else:
            # Normal left click - check if clicking on an item
            item = self.itemAt(event.pos())
            if item:
                # Check if it's a component that can be dragged
                if hasattr(item, 'setFlag') and item.flags() & item.GraphicsItemFlag.ItemIsMovable:
                    self.set_dragging(True)
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events for panning and coordinate display"""
        if self._panning:
            # Pan the view
            delta = event.pos() - self._pan_start_pos
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            self._pan_start_pos = event.pos()
            event.accept()
        else:
            # Update coordinate display with grid snapping
            scene_pos = self.mapToScene(event.pos())
            
            # Snap to grid if enabled
            if hasattr(self.scene(), 'settings') and hasattr(self.scene(), '_snap_to_grid'):
                if self.scene()._snap_to_grid:
                    snapped_pos = self.scene().settings.snap_to_grid(scene_pos)
                    coord_text = self.scene().settings.format_coordinate(snapped_pos.x(), snapped_pos.y())
                    
                    # Add grid coordinates
                    grid_size_px = self.scene().settings.get_grid_size_pixels()
                    grid_x = round(snapped_pos.x() / grid_size_px)
                    grid_y = round(snapped_pos.y() / grid_size_px)
                    coord_text += f" | Grid: ({grid_x}, {grid_y})"
                else:
                    coord_text = self.scene().settings.format_coordinate(scene_pos.x(), scene_pos.y())
            else:
                coord_text = f"X: {scene_pos.x():.1f}, Y: {scene_pos.y():.1f}"
            
            # Emit signal to update status bar
            self.coordinate_updated.emit(coord_text)
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if event.button() == Qt.MouseButton.MiddleButton:
            # Stop panning
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            # Stop dragging
            self.set_dragging(False)
            super().mouseReleaseEvent(event)
    
    def keyPressEvent(self, event):
        """Handle key press events for spacebar panning"""
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            # Start spacebar panning
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            event.accept()
        else:
            super().keyPressEvent(event)
    
    def keyReleaseEvent(self, event):
        """Handle key release events"""
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            # Stop spacebar panning
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            event.accept()
        else:
            super().keyReleaseEvent(event)
    
    def zoom_in(self):
        """Zoom in by one step"""
        if self._zoom_factor < self._max_zoom:
            self._zoom_factor += self._zoom_step
            self.scale(1 + self._zoom_step, 1 + self._zoom_step)
            self.zoom_changed.emit(self._zoom_factor)
    
    def zoom_out(self):
        """Zoom out by one step"""
        if self._zoom_factor > self._min_zoom:
            self._zoom_factor -= self._zoom_step
            self.scale(1 - self._zoom_step, 1 - self._zoom_step)
            self.zoom_changed.emit(self._zoom_factor)
    
    def zoom_to_fit(self):
        """Zoom to fit all items in the view"""
        self.fitInView(self.scene().itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self._zoom_factor = self.transform().m11()  # Get actual zoom factor
        self.zoom_changed.emit(self._zoom_factor)
    
    def zoom_to_actual_size(self):
        """Reset zoom to 100%"""
        self.resetTransform()
        self._zoom_factor = 1.0
        self.zoom_changed.emit(self._zoom_factor)
    
    def set_optimal_zoom_for_components(self, component_count=25):
        """Set zoom level to show approximately the specified number of components optimally"""
        # Calculate component size (60x60 pixels for resistor)
        component_size = 60  # pixels
        component_spacing = 30  # grid spacing in pixels
        
        # Calculate how many components fit in viewport
        viewport_size = min(self.viewport().width(), self.viewport().height())
        
        # Calculate desired zoom factor to show component_count components
        # Each component takes component_size + spacing
        total_component_width = component_count * (component_size + component_spacing)
        
        # Calculate zoom factor needed
        desired_zoom = viewport_size / total_component_width
        
        # Clamp to valid zoom range
        desired_zoom = max(self._min_zoom, min(self._max_zoom, desired_zoom))
        
        # Apply zoom
        self.resetTransform()
        self.scale(desired_zoom, desired_zoom)
        self._zoom_factor = desired_zoom
        self.zoom_changed.emit(self._zoom_factor)
        
        return desired_zoom
    
    def zoom_to_selection(self):
        """Zoom to fit selected items"""
        selected_items = self.scene().selectedItems()
        if selected_items:
            # Calculate bounding rect of selected items
            from PyQt6.QtCore import QRectF
            rect = QRectF()
            for item in selected_items:
                rect = rect.united(item.boundingRect().translated(item.pos()))
            
            if not rect.isEmpty():
                self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
    
    def get_zoom_factor(self):
        """Get current zoom factor"""
        return self._zoom_factor
    
    def set_zoom_factor(self, factor):
        """Set zoom factor"""
        if self._min_zoom <= factor <= self._max_zoom:
            self.resetTransform()
            self.scale(factor, factor)
            self._zoom_factor = factor
    
    def smooth_zoom_to(self, factor, center_point=None):
        """Smoothly zoom to a specific factor"""
        if self._min_zoom <= factor <= self._max_zoom:
            self._transition_start_transform = self.transform()
            self._transition_target_transform = self.transform()
            self._transition_target_transform.scale(factor / self._zoom_factor, factor / self._zoom_factor)
            self._transition_start_time = 0
            self._transition_timer.start(16)  # ~60 FPS
    
    def _update_transition(self):
        """Update smooth transition animation"""
        if self._transition_start_transform is None or self._transition_target_transform is None:
            self._transition_timer.stop()
            return
        
        elapsed = self._transition_start_time
        progress = min(elapsed / self._transition_duration, 1.0)
        
        # Easing function (ease-out)
        ease_progress = 1 - (1 - progress) ** 3
        
        # Interpolate transform
        current_transform = self._transition_start_transform
        # Apply interpolation here (simplified)
        
        self._transition_start_time += 16
        
        if progress >= 1.0:
            self._transition_timer.stop()
            self.setTransform(self._transition_target_transform)
            self._zoom_factor = self._transition_target_transform.m11()
    
    def get_lod_level(self):
        """Get current Level of Detail based on zoom"""
        zoom = self._zoom_factor
        
        if zoom >= self._lod_thresholds['text']:
            return 'high'      # Show all details including text
        elif zoom >= self._lod_thresholds['details']:
            return 'medium'    # Show symbols but hide text
        else:
            return 'low'       # Show only basic shapes
    
    def should_show_text(self):
        """Check if text should be shown at current zoom level"""
        return self._zoom_factor >= self._lod_thresholds['text']
    
    def should_show_details(self):
        """Check if details should be shown at current zoom level"""
        return self._zoom_factor >= self._lod_thresholds['details']
    
    def should_show_fine_grid(self):
        """Check if fine grid should be shown at current zoom level"""
        return self._zoom_factor >= self._lod_thresholds['grid']
    
    def is_dragging(self) -> bool:
        """Check if currently dragging an item"""
        return self._dragging
    
    def set_dragging(self, dragging: bool):
        """Set the dragging state"""
        self._dragging = dragging
