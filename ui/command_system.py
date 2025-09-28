"""
Command Pattern Implementation for PyEWB
Provides unlimited undo/redo functionality
"""

from abc import ABC, abstractmethod
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QGraphicsItem


class Command(ABC):
    """Abstract base class for all commands"""
    
    @abstractmethod
    def execute(self):
        """Execute the command"""
        pass
    
    @abstractmethod
    def undo(self):
        """Undo the command"""
        pass
    
    @abstractmethod
    def redo(self):
        """Redo the command (same as execute)"""
        pass


class CommandManager(QObject):
    """Manages the command stack for undo/redo functionality"""
    
    # Signals
    undo_available_changed = pyqtSignal(bool)
    redo_available_changed = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._undo_stack = []
        self._redo_stack = []
        self._max_stack_size = 100  # Limit stack size to prevent memory issues
    
    def execute_command(self, command: Command):
        """Execute a command and add it to the undo stack"""
        command.execute()
        self._undo_stack.append(command)
        
        # Clear redo stack when new command is executed
        self._redo_stack.clear()
        
        # Limit stack size
        if len(self._undo_stack) > self._max_stack_size:
            self._undo_stack.pop(0)
        
        self._update_availability()
    
    def undo(self):
        """Undo the last command"""
        if self._undo_stack:
            command = self._undo_stack.pop()
            command.undo()
            self._redo_stack.append(command)
            self._update_availability()
    
    def redo(self):
        """Redo the last undone command"""
        if self._redo_stack:
            command = self._redo_stack.pop()
            command.redo()
            self._undo_stack.append(command)
            self._update_availability()
    
    def can_undo(self) -> bool:
        """Check if undo is available"""
        return len(self._undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is available"""
        return len(self._redo_stack) > 0
    
    def clear(self):
        """Clear all commands"""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._update_availability()
    
    def _update_availability(self):
        """Update signal availability"""
        self.undo_available_changed.emit(self.can_undo())
        self.redo_available_changed.emit(self.can_redo())


class AddComponentCommand(Command):
    """Command for adding a component"""
    
    def __init__(self, scene, component, position):
        self.scene = scene
        self.component = component
        self.position = position
    
    def execute(self):
        """Add component to scene"""
        # Snap component to grid for perfect alignment
        snapped_pos = self.scene.snap_to_grid(self.position)
        self.component.setPos(snapped_pos)
        self.scene.addItem(self.component)
    
    def undo(self):
        """Remove component from scene"""
        self.scene.removeItem(self.component)
    
    def redo(self):
        """Re-add component to scene"""
        self.execute()


class RemoveComponentCommand(Command):
    """Command for removing a component"""
    
    def __init__(self, scene, component):
        self.scene = scene
        self.component = component
        self.position = component.pos()
    
    def execute(self):
        """Remove component from scene"""
        self.scene.removeItem(self.component)
    
    def undo(self):
        """Re-add component to scene"""
        self.component.setPos(self.position)
        self.scene.addItem(self.component)
    
    def redo(self):
        """Remove component from scene"""
        self.execute()


class MoveComponentCommand(Command):
    """Command for moving a component"""
    
    def __init__(self, component, old_position, new_position):
        self.component = component
        self.old_position = old_position
        self.new_position = new_position
    
    def execute(self):
        """Move component to new position"""
        self.component.setPos(self.new_position)
    
    def undo(self):
        """Move component back to old position"""
        self.component.setPos(self.old_position)
    
    def redo(self):
        """Move component to new position"""
        self.execute()


class RotateComponentCommand(Command):
    """Command for rotating a component"""
    
    def __init__(self, component, old_rotation, new_rotation):
        self.component = component
        self.old_rotation = old_rotation
        self.new_rotation = new_rotation
    
    def execute(self):
        """Rotate component to new angle"""
        self.component.rotation = self.new_rotation
    
    def undo(self):
        """Rotate component back to old angle"""
        self.component.rotation = self.old_rotation
    
    def redo(self):
        """Rotate component to new angle"""
        self.execute()


class AddWireCommand(Command):
    """Command for adding a wire"""
    
    def __init__(self, scene, wire):
        self.scene = scene
        self.wire = wire
    
    def execute(self):
        """Add wire to scene"""
        self.scene.addItem(self.wire)
    
    def undo(self):
        """Remove wire from scene"""
        self.scene.removeItem(self.wire)
    
    def redo(self):
        """Add wire to scene"""
        self.execute()


class PropertyChangeCommand(Command):
    """Command for changing component properties"""
    
    def __init__(self, component, old_properties, new_properties):
        self.component = component
        self.old_properties = old_properties.copy()
        self.new_properties = new_properties.copy()
    
    def execute(self):
        """Apply new properties"""
        self.component.properties.update(self.new_properties)
        self.component.update()
    
    def undo(self):
        """Restore old properties"""
        self.component.properties = self.old_properties.copy()
        self.component.update()
    
    def redo(self):
        """Apply new properties"""
        self.execute()
