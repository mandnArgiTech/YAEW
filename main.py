#!/usr/bin/env python3
"""
PyEWB - Python Electronics Workbench
A circuit simulator and schematic editor built with PyQt6
"""

import sys
import json
from PyQt6.QtWidgets import QApplication, QMainWindow, QGraphicsView, QToolBar, QMenuBar, QStatusBar, QVBoxLayout, QWidget, QFileDialog, QMessageBox, QLabel, QComboBox
from PyQt6.QtCore import Qt, QMimeData, QTimer
from PyQt6.QtGui import QAction, QKeySequence
from ui.schematic_scene import SchematicScene
from ui.schematic_view import SchematicView
from ui.command_system import CommandManager, AddComponentCommand, RemoveComponentCommand, MoveComponentCommand, RotateComponentCommand, PropertyChangeCommand
from ui.config_editor import show_config_editor
from components.resistor import Resistor
from components.sources import DCVoltageSource, ACVoltageSource, PulseSource


class MainWindow(QMainWindow):
    """Main application window for PyEWB"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyEWB - Python Electronics Workbench")
        self.setGeometry(100, 100, 1200, 800)
        
        # Start maximized for better workspace
        self.setWindowState(self.windowState() | Qt.WindowState.WindowMaximized)
        
        # Set up initial view after window is shown
        QTimer.singleShot(100, self.setup_initial_view)
        
        # Wire mode state
        self.wire_mode = False
        self.wire_action = None
        
        # Command system for undo/redo
        self.command_manager = CommandManager(self)
        self.command_manager.undo_available_changed.connect(self.update_undo_action)
        self.command_manager.redo_available_changed.connect(self.update_redo_action)
        
        # Edit state
        self.clipboard_data = None
        self.current_file = None
        
        # Create the central widget and graphics view
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout for central widget
        layout = QVBoxLayout(central_widget)
        
        # Create graphics scene and view for schematic editor
        self.scene = SchematicScene()
        self.graphics_view = SchematicView()
        self.graphics_view.setScene(self.scene)
        
        layout.addWidget(self.graphics_view)
        
        # Connect scene signals
        self.scene.component_added.connect(self.on_component_added)
        self.scene.wire_added.connect(self.on_wire_added)
        self.graphics_view.coordinate_updated.connect(self.on_coordinate_updated)
        self.graphics_view.zoom_changed.connect(self.update_zoom_display)
        
        # Set focus policy to receive key events
        self.graphics_view.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create component toolbar
        self.create_toolbar()
        
        # Add unit selector to toolbar
        self.unit_selector = QComboBox()
        self.unit_selector.addItems(['mils', 'inch', 'mm'])
        self.unit_selector.setCurrentText('mils')
        self.unit_selector.currentTextChanged.connect(self.on_units_changed)
        self.toolbar.addWidget(QLabel("Units:"))
        self.toolbar.addWidget(self.unit_selector)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Add coordinate label to status bar
        self.coord_label = QLabel("X: 0.00 mils, Y: 0.00 mils")
        self.status_bar.addPermanentWidget(self.coord_label)
        
        # Add component count label
        self.component_count_label = QLabel("Components: 0")
        self.status_bar.addPermanentWidget(self.component_count_label)
        
        # Add grid info label
        self.grid_info_label = QLabel("Grid: 30 mils")
        self.status_bar.addPermanentWidget(self.grid_info_label)
        
        # Add mode label
        self.mode_label = QLabel("Mode: Select")
        self.status_bar.addPermanentWidget(self.mode_label)
        
        # Add zoom level label
        self.zoom_label = QLabel("Zoom: 100%")
        self.status_bar.addPermanentWidget(self.zoom_label)
        
        self.status_bar.showMessage("Ready")
    
    def setup_initial_view(self):
        """Set up the initial view with 160% zoom when no components are present"""
        # Check if there are any components in the scene
        component_count = len(self.scene.get_components())
        
        if component_count == 0:
            # No components - set zoom to 160%
            self.graphics_view.resetTransform()
            self.graphics_view.scale(1.6, 1.6)
            self.graphics_view._zoom_factor = 1.6
            self.update_zoom_display(1.6)
            self.status_bar.showMessage("Initial view set - Zoom: 160% (no components)")
        else:
            # Components present - use optimal zoom for 25 components
            zoom_factor = self.graphics_view.set_optimal_zoom_for_components(25)
            self.update_zoom_display(zoom_factor)
            self.status_bar.showMessage(f"Initial view set - Zoom: {zoom_factor:.2f}x (shows ~25 components)")
    
    def create_menu_bar(self):
        """Create the application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        new_action = QAction('New', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        
        open_action = QAction('Open', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        save_action = QAction('Save', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction('Save As...', self)
        save_as_action.setShortcut('Ctrl+Shift+S')
        save_as_action.triggered.connect(self.save_as_file)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu('Edit')
        
        undo_action = QAction('Undo', self)
        undo_action.setShortcut('Ctrl+Z')
        undo_action.triggered.connect(self.undo_action)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction('Redo', self)
        redo_action.setShortcut('Ctrl+Y')
        redo_action.triggered.connect(self.redo_action)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        copy_action = QAction('Copy', self)
        copy_action.setShortcut('Ctrl+C')
        copy_action.triggered.connect(self.copy_selected)
        edit_menu.addAction(copy_action)
        
        cut_action = QAction('Cut', self)
        cut_action.setShortcut('Ctrl+X')
        cut_action.triggered.connect(self.cut_selected)
        edit_menu.addAction(cut_action)
        
        paste_action = QAction('Paste', self)
        paste_action.setShortcut('Ctrl+V')
        paste_action.triggered.connect(self.paste_items)
        edit_menu.addAction(paste_action)
        
        edit_menu.addSeparator()
        
        delete_action = QAction('Delete', self)
        delete_action.setShortcut('Delete')
        delete_action.triggered.connect(self.delete_selected)
        edit_menu.addAction(delete_action)
        
        edit_menu.addSeparator()
        
        # Rotation actions
        rotate_cw_action = QAction('Rotate 90° Clockwise', self)
        rotate_cw_action.setShortcut('Ctrl+R')
        rotate_cw_action.triggered.connect(self.rotate_selected_clockwise)
        edit_menu.addAction(rotate_cw_action)
        
        rotate_ccw_action = QAction('Rotate 90° Counterclockwise', self)
        rotate_ccw_action.setShortcut('Ctrl+Shift+R')
        rotate_ccw_action.triggered.connect(self.rotate_selected_counterclockwise)
        edit_menu.addAction(rotate_ccw_action)
        
        rotate_180_action = QAction('Rotate 180°', self)
        rotate_180_action.setShortcut('Ctrl+Alt+R')
        rotate_180_action.triggered.connect(self.rotate_selected_180)
        edit_menu.addAction(rotate_180_action)
        
        # Mirror actions
        mirror_h_action = QAction('Mirror Horizontally', self)
        mirror_h_action.setShortcut('Ctrl+M')
        mirror_h_action.triggered.connect(self.mirror_selected_horizontal)
        edit_menu.addAction(mirror_h_action)
        
        mirror_v_action = QAction('Mirror Vertically', self)
        mirror_v_action.setShortcut('Ctrl+Shift+M')
        mirror_v_action.triggered.connect(self.mirror_selected_vertical)
        edit_menu.addAction(mirror_v_action)
        
        # Simulate menu
        simulate_menu = menubar.addMenu('Simulate')
        
        run_simulation_action = QAction('Run Simulation', self)
        run_simulation_action.setShortcut('F5')
        simulate_menu.addAction(run_simulation_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        config_editor_action = QAction('Component Configuration Editor', self)
        config_editor_action.triggered.connect(self.show_config_editor)
        tools_menu.addAction(config_editor_action)
        
        stop_simulation_action = QAction('Stop Simulation', self)
        stop_simulation_action.setShortcut('F6')
        simulate_menu.addAction(stop_simulation_action)
    
    def create_toolbar(self):
        """Create the component toolbar"""
        self.toolbar = QToolBar("Components")
        self.toolbar.setOrientation(Qt.Orientation.Vertical)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.toolbar)
        
        # Add wire tool
        self.wire_action = QAction('Wire Tool', self)
        self.wire_action.triggered.connect(self.toggle_wire_mode)
        self.wire_action.setCheckable(True)
        self.wire_action.setShortcut('W')
        self.wire_action.setToolTip('Wire Tool - Draw connections (W)')
        self.toolbar.addAction(self.wire_action)
        
        self.toolbar.addSeparator()
        
        # Add component actions
        resistor_action = QAction('Resistor', self)
        resistor_action.setToolTip('Add Resistor (R)')
        resistor_action.triggered.connect(self.add_resistor)
        self.toolbar.addAction(resistor_action)
        
        capacitor_action = QAction('Capacitor', self)
        self.toolbar.addAction(capacitor_action)
        
        inductor_action = QAction('Inductor', self)
        self.toolbar.addAction(inductor_action)
        
        # Voltage sources
        dc_voltage_action = QAction('DC Voltage', self)
        dc_voltage_action.triggered.connect(self.add_dc_voltage)
        self.toolbar.addAction(dc_voltage_action)
        
        ac_voltage_action = QAction('AC Voltage', self)
        ac_voltage_action.triggered.connect(self.add_ac_voltage)
        self.toolbar.addAction(ac_voltage_action)
        
        pulse_source_action = QAction('Pulse Source', self)
        pulse_source_action.triggered.connect(self.add_pulse_source)
        self.toolbar.addAction(pulse_source_action)
        
        current_source_action = QAction('Current Source', self)
        self.toolbar.addAction(current_source_action)
        
        ground_action = QAction('Ground', self)
        self.toolbar.addAction(ground_action)
        
        self.toolbar.addSeparator()
        
        # Grid controls
        self.grid_action = QAction('Toggle Grid', self)
        self.grid_action.setCheckable(True)
        self.grid_action.setChecked(True)
        self.grid_action.triggered.connect(self.toggle_grid)
        self.toolbar.addAction(self.grid_action)
        
        self.snap_action = QAction('Snap to Grid', self)
        self.snap_action.setCheckable(True)
        self.snap_action.setChecked(True)
        self.snap_action.triggered.connect(self.toggle_snap_to_grid)
        self.toolbar.addAction(self.snap_action)
        
        self.toolbar.addSeparator()
        
        # Zoom controls
        zoom_in_action = QAction('Zoom In', self)
        zoom_in_action.setShortcut('Ctrl+=')
        zoom_in_action.triggered.connect(self.zoom_in)
        self.toolbar.addAction(zoom_in_action)
        
        zoom_out_action = QAction('Zoom Out', self)
        zoom_out_action.setShortcut('Ctrl+-')
        zoom_out_action.triggered.connect(self.zoom_out)
        self.toolbar.addAction(zoom_out_action)
        
        zoom_fit_action = QAction('Zoom to Fit', self)
        zoom_fit_action.setShortcut('Ctrl+0')
        zoom_fit_action.triggered.connect(self.zoom_to_fit)
        self.toolbar.addAction(zoom_fit_action)
    
    def toggle_wire_mode(self):
        """Toggle wire drawing mode"""
        self.wire_mode = not self.wire_mode
        
        if self.wire_mode:
            # Enter wire mode
            self.graphics_view.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.scene.set_wire_mode(True)
            self.status_bar.showMessage("Wire mode: Click on component terminals to draw wires. Press ESC to exit.")
            self.wire_action.setText("Exit Wire Mode")
            self.update_mode_display("Wire")
        else:
            # Exit wire mode
            self.graphics_view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            self.scene.set_wire_mode(False)
            self.status_bar.showMessage("Ready")
            self.wire_action.setText("Wire Tool")
            self.update_mode_display("Select")
    
    def add_resistor(self):
        """Add a resistor to the scene"""
        # Add resistor at center of view
        view_center = self.graphics_view.mapToScene(self.graphics_view.viewport().rect().center())
        resistor = Resistor("R", "1k")
        
        # Update resistor dimensions based on current grid
        resistor.update_dimensions()
        
        # Create and execute command
        command = AddComponentCommand(self.scene, resistor, view_center)
        self.command_manager.execute_command(command)
        
        self.status_bar.showMessage(f"Added resistor: {resistor.name}")
        self.update_component_count()
    
    def add_dc_voltage(self):
        """Add a DC voltage source to the scene"""
        view_center = self.graphics_view.mapToScene(self.graphics_view.viewport().rect().center())
        dc_source = DCVoltageSource("V", "5V")
        
        # Update dimensions based on current grid
        dc_source.update_dimensions()
        
        # Create and execute command
        command = AddComponentCommand(self.scene, dc_source, view_center)
        self.command_manager.execute_command(command)
        
        self.status_bar.showMessage(f"Added DC voltage source: {dc_source.name}")
        self.update_component_count()
    
    def add_ac_voltage(self):
        """Add an AC voltage source to the scene"""
        view_center = self.graphics_view.mapToScene(self.graphics_view.viewport().rect().center())
        ac_source = ACVoltageSource("V", "5V")
        
        # Update dimensions based on current grid
        ac_source.update_dimensions()
        
        # Create and execute command
        command = AddComponentCommand(self.scene, ac_source, view_center)
        self.command_manager.execute_command(command)
        
        self.status_bar.showMessage(f"Added AC voltage source: {ac_source.name}")
        self.update_component_count()
    
    def add_pulse_source(self):
        """Add a pulse source to the scene"""
        view_center = self.graphics_view.mapToScene(self.graphics_view.viewport().rect().center())
        pulse_source = PulseSource("V", "5V")
        
        # Update dimensions based on current grid
        pulse_source.update_dimensions()
        
        # Create and execute command
        command = AddComponentCommand(self.scene, pulse_source, view_center)
        self.command_manager.execute_command(command)
        
        self.status_bar.showMessage(f"Added pulse source: {pulse_source.name}")
        self.update_component_count()
    
    def on_units_changed(self, unit_text):
        """Handle unit system change"""
        unit_map = {'mils': 'mil', 'inch': 'in', 'mm': 'mm'}
        unit = unit_map.get(unit_text, 'mil')
        
        if hasattr(self.scene, 'settings'):
            self.scene.settings.set_units(unit)
            
            # Update all components to match new grid size
            self.update_all_component_dimensions()
            self.update_grid_info()
            
            # Update coordinate display
            self.update_coordinate_display()
    
    def update_all_component_dimensions(self):
        """Update dimensions of all components when grid size changes"""
        for item in self.scene.items():
            if hasattr(item, 'update_dimensions'):
                item.update_dimensions()
                item.update()  # Trigger repaint
    
    def on_coordinate_updated(self, coord_text):
        """Handle coordinate update from view"""
        self.coord_label.setText(coord_text)
    
    def update_coordinate_display(self, scene_pos=None):
        """Update coordinate display in status bar"""
        if scene_pos is None:
            # Get current mouse position
            mouse_pos = self.graphics_view.mapFromGlobal(self.cursor().pos())
            scene_pos = self.graphics_view.mapToScene(mouse_pos)
        
        if hasattr(self.scene, 'settings'):
            coord_text = self.scene.settings.format_coordinate(scene_pos.x(), scene_pos.y())
            self.coord_label.setText(coord_text)
    
    def toggle_grid(self):
        """Toggle grid visibility"""
        self.scene.toggle_grid()
        self.grid_action.setChecked(self.scene._show_grid)
        status = "Grid ON" if self.scene._show_grid else "Grid OFF"
        self.status_bar.showMessage(status)
    
    def toggle_snap_to_grid(self):
        """Toggle snap to grid"""
        self.scene.toggle_snap_to_grid()
        self.snap_action.setChecked(self.scene._snap_to_grid)
        status = "Snap to Grid ON" if self.scene._snap_to_grid else "Snap to Grid OFF"
        self.status_bar.showMessage(status)
    
    def zoom_in(self):
        """Zoom in"""
        self.graphics_view.zoom_in()
        zoom_factor = self.graphics_view.get_zoom_factor()
        self.update_zoom_display(zoom_factor)
        self.status_bar.showMessage(f"Zoom: {zoom_factor:.1f}x")
    
    def zoom_out(self):
        """Zoom out"""
        self.graphics_view.zoom_out()
        zoom_factor = self.graphics_view.get_zoom_factor()
        self.update_zoom_display(zoom_factor)
        self.status_bar.showMessage(f"Zoom: {zoom_factor:.1f}x")
    
    def zoom_to_fit(self):
        """Zoom to fit all items"""
        self.graphics_view.zoom_to_fit()
        zoom_factor = self.graphics_view.get_zoom_factor()
        self.update_zoom_display(zoom_factor)
        self.status_bar.showMessage("Zoomed to fit")
    
    def on_component_added(self, component):
        """Handle component added signal"""
        self.status_bar.showMessage(f"Component added: {component.name}")
    
    def on_wire_added(self, wire):
        """Handle wire added signal"""
        self.status_bar.showMessage("Wire added")
    
    # File operations
    def new_file(self):
        """Create a new file"""
        if self.ask_save_changes():
            self.scene.clear()
            self.current_file = None
            self.setWindowTitle("PyEWB - Python Electronics Workbench")
            self.status_bar.showMessage("New file created")
    
    def open_file(self):
        """Open a file"""
        if self.ask_save_changes():
            filename, _ = QFileDialog.getOpenFileName(
                self, "Open Circuit", "", "PyEWB Files (*.pyewb);;All Files (*)"
            )
            if filename:
                self.load_file(filename)
    
    def save_file(self):
        """Save the current file"""
        if self.current_file:
            self.save_to_file(self.current_file)
        else:
            self.save_as_file()
    
    def save_as_file(self):
        """Save as a new file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Circuit", "", "PyEWB Files (*.pyewb);;All Files (*)"
        )
        if filename:
            self.save_to_file(filename)
    
    def ask_save_changes(self):
        """Ask user if they want to save changes"""
        # For now, always return True (no changes to save)
        # This could be enhanced to track actual changes
        return True
    
    def load_file(self, filename):
        """Load a file"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            self.scene.clear()
            # Load components and wires from data
            # This is a simplified implementation
            self.current_file = filename
            self.setWindowTitle(f"PyEWB - {filename}")
            self.status_bar.showMessage(f"Loaded {filename}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not load file: {e}")
    
    def save_to_file(self, filename):
        """Save to a file"""
        try:
            # Get all components and wires from scene
            components = []
            wires = []
            
            for item in self.scene.items():
                if hasattr(item, 'name'):  # Component
                    components.append({
                        'type': item.__class__.__name__,
                        'name': item.name,
                        'value': item.value,
                        'x': item.pos().x(),
                        'y': item.pos().y()
                    })
                elif hasattr(item, 'start_point'):  # Wire
                    wires.append({
                        'start_x': item.start_point.x(),
                        'start_y': item.start_point.y(),
                        'end_x': item.end_point.x(),
                        'end_y': item.end_point.y()
                    })
            
            data = {
                'components': components,
                'wires': wires
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.current_file = filename
            self.setWindowTitle(f"PyEWB - {filename}")
            self.status_bar.showMessage(f"Saved {filename}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not save file: {e}")
    
    # Edit operations
    def undo_action(self):
        """Undo last action"""
        self.command_manager.undo()
        self.status_bar.showMessage("Undo")
    
    def redo_action(self):
        """Redo last action"""
        self.command_manager.redo()
        self.status_bar.showMessage("Redo")
    
    def update_undo_action(self, available):
        """Update undo action availability"""
        # Find undo action in menu and enable/disable it
        for action in self.findChildren(QAction):
            if action.text() == "Undo":
                action.setEnabled(available)
                break
    
    def update_redo_action(self, available):
        """Update redo action availability"""
        # Find redo action in menu and enable/disable it
        for action in self.findChildren(QAction):
            if action.text() == "Redo":
                action.setEnabled(available)
                break
    
    def copy_selected(self):
        """Copy selected items"""
        selected_items = self.scene.selectedItems()
        if selected_items:
            self.clipboard_data = []
            for item in selected_items:
                if hasattr(item, 'name'):  # Component
                    self.clipboard_data.append({
                        'type': 'component',
                        'class': item.__class__.__name__,
                        'name': item.name,
                        'value': item.value,
                        'x': item.pos().x(),
                        'y': item.pos().y()
                    })
            self.status_bar.showMessage(f"Copied {len(selected_items)} items")
    
    def cut_selected(self):
        """Cut selected items"""
        self.copy_selected()
        self.delete_selected()
    
    def paste_items(self):
        """Paste items from clipboard"""
        if self.clipboard_data:
            for item_data in self.clipboard_data:
                if item_data['type'] == 'component':
                    # Create new component at current mouse position
                    if item_data['class'] == 'Resistor':
                        component = self.scene.add_resistor(
                            item_data['x'] + 20, item_data['y'] + 20,
                            item_data['name'], item_data['value']
                        )
            self.status_bar.showMessage(f"Pasted {len(self.clipboard_data)} items")
    
    def delete_selected(self):
        """Delete selected items"""
        selected_items = self.scene.selectedItems()
        if selected_items:
            for item in selected_items:
                self.scene.removeItem(item)
            self.status_bar.showMessage(f"Deleted {len(selected_items)} items")
    
    def rotate_selected_clockwise(self):
        """Rotate selected components 90 degrees clockwise"""
        self.rotate_selected_components(90)
    
    def rotate_selected_counterclockwise(self):
        """Rotate selected components 90 degrees counterclockwise"""
        self.rotate_selected_components(-90)
    
    def rotate_selected_180(self):
        """Rotate selected components 180 degrees"""
        self.rotate_selected_components(180)
    
    def rotate_selected_components(self, angle: int):
        """Rotate selected components by specified angle"""
        selected_items = self.scene.selectedItems()
        rotated_count = 0
        
        for item in selected_items:
            if hasattr(item, 'rotate_90_clockwise'):  # Check if it's a component
                if angle == 90:
                    item.rotate_90_clockwise()
                elif angle == -90:
                    item.rotate_90_counterclockwise()
                elif angle == 180:
                    item.rotate_180()
                rotated_count += 1
        
        if rotated_count > 0:
            self.status_bar.showMessage(f"Rotated {rotated_count} components by {angle}°")
        else:
            self.status_bar.showMessage("No components selected for rotation")
    
    def mirror_selected_horizontal(self):
        """Mirror selected components horizontally"""
        self.mirror_selected_components('horizontal')
    
    def mirror_selected_vertical(self):
        """Mirror selected components vertically"""
        self.mirror_selected_components('vertical')
    
    def mirror_selected_components(self, direction: str):
        """Mirror selected components in specified direction"""
        selected_items = self.scene.selectedItems()
        mirrored_count = 0
        
        for item in selected_items:
            if hasattr(item, 'mirror'):  # Check if it's a component with mirror capability
                item.mirror(direction)
                mirrored_count += 1
        
        if mirrored_count > 0:
            self.status_bar.showMessage(f"Mirrored {mirrored_count} components {direction}ly")
        else:
            self.status_bar.showMessage("No components selected for mirroring")
    
    def show_config_editor(self):
        """Show the component configuration editor"""
        try:
            show_config_editor(self)
            self.status_bar.showMessage("Configuration editor closed")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open configuration editor: {e}")
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key.Key_Escape:
            if self.wire_mode:
                self.toggle_wire_mode()
        elif event.key() == Qt.Key.Key_W:
            self.toggle_wire_mode()
        elif event.key() == Qt.Key.Key_Delete:
            self.delete_selected()
        elif event.matches(QKeySequence.StandardKey.Copy):
            self.copy_selected()
        elif event.matches(QKeySequence.StandardKey.Paste):
            self.paste_items()
        elif event.matches(QKeySequence.StandardKey.Cut):
            self.cut_selected()
        elif event.matches(QKeySequence.StandardKey.Undo):
            self.undo_action()
        elif event.matches(QKeySequence.StandardKey.Redo):
            self.redo_action()
        elif event.key() == Qt.Key.Key_R:
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.rotate_selected_clockwise()
            elif event.modifiers() == Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier:
                self.rotate_selected_counterclockwise()
            elif event.modifiers() == Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier:
                self.rotate_selected_180()
        elif event.key() == Qt.Key.Key_M:
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.mirror_selected_horizontal()
            elif event.modifiers() == Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier:
                self.mirror_selected_vertical()
        elif event.key() == Qt.Key.Key_Plus or event.key() == Qt.Key.Key_Equal:
            self.zoom_in()
        elif event.key() == Qt.Key.Key_Minus:
            self.zoom_out()
        elif event.key() == Qt.Key.Key_0 and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.zoom_to_fit()
        elif event.key() == Qt.Key.Key_G:
            self.toggle_grid()
        elif event.key() == Qt.Key.Key_S and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.toggle_snap_to_grid()
        else:
            super().keyPressEvent(event)
    
    def update_component_count(self):
        """Update component count in status bar"""
        count = len(self.scene.get_components())
        self.component_count_label.setText(f"Components: {count}")
    
    def update_grid_info(self):
        """Update grid information in status bar"""
        grid_size = self.scene.settings.grid_size
        unit = self.scene.settings.unit_system
        self.grid_info_label.setText(f"Grid: {grid_size} {unit}")
    
    def update_mode_display(self, mode):
        """Update mode display in status bar"""
        self.mode_label.setText(f"Mode: {mode}")
    
    def update_zoom_display(self, zoom_factor):
        """Update zoom level display in status bar"""
        zoom_percent = int(zoom_factor * 100)
        self.zoom_label.setText(f"Zoom: {zoom_percent}%")
    
    def closeEvent(self, event):
        """Handle application close event - save final label positions"""
        print("\n=== SAVING FINAL LABEL POSITIONS ===")
        
        # Collect label positions from all resistor components
        resistor_components = []
        for item in self.scene.items():
            if hasattr(item, 'component_type') and item.component_type == 'resistor':
                if hasattr(item, 'get_final_label_positions'):
                    positions = item.get_final_label_positions()
                    resistor_components.append({
                        'name': item.name,
                        'positions': positions
                    })
                    print(f"Resistor {item.name}:")
                    print(f"  Name offset: ({positions['name_offset']['x']:.1f}, {positions['name_offset']['y']:.1f})")
                    print(f"  Value offset: ({positions['value_offset']['x']:.1f}, {positions['value_offset']['y']:.1f})")
        
        if resistor_components:
            # Calculate average positions
            avg_name_x = sum(comp['positions']['name_offset']['x'] for comp in resistor_components) / len(resistor_components)
            avg_name_y = sum(comp['positions']['name_offset']['y'] for comp in resistor_components) / len(resistor_components)
            avg_value_x = sum(comp['positions']['value_offset']['x'] for comp in resistor_components) / len(resistor_components)
            avg_value_y = sum(comp['positions']['value_offset']['y'] for comp in resistor_components) / len(resistor_components)
            
            print(f"\n=== AVERAGE LABEL POSITIONS ===")
            print(f"Name offset: ({avg_name_x:.1f}, {avg_name_y:.1f})")
            print(f"Value offset: ({avg_value_x:.1f}, {avg_value_y:.1f})")
            print(f"\n=== CODE TO UPDATE DEFAULTS ===")
            print(f"self._name_offset = QPointF({avg_name_x:.1f}, {avg_name_y:.1f})")
            print(f"self._value_offset = QPointF({avg_value_x:.1f}, {avg_value_y:.1f})")
        else:
            print("No resistor components found to analyze.")
        
        print("=== END LABEL POSITIONS ===\n")
        
        # Call the parent close event
        super().closeEvent(event)


def main():
    """Main entry point for the application"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("PyEWB")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("PyEWB")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
