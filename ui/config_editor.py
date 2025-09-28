"""
Configuration Editor Dialog for PyEWB
Allows administrators to modify component dimensions and settings
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                            QLineEdit, QComboBox, QPushButton, QLabel, QSpinBox, 
                            QDoubleSpinBox, QCheckBox, QTextEdit, QTabWidget,
                            QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
                            QScrollArea, QWidget, QSplitter)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from config.config_manager import config_manager
import json


class ComponentConfigWidget(QWidget):
    """Widget for editing a single component's configuration"""
    
    config_changed = pyqtSignal(str, dict)  # component_name, new_config
    
    def __init__(self, component_name: str, component_config, parent=None):
        super().__init__(parent)
        self.component_name = component_name
        self.config = component_config
        self.setup_ui()
        self.populate_values()
    
    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        
        # Create scroll area for long forms
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Dimensions group
        dim_group = QGroupBox("Dimensions")
        dim_layout = QFormLayout(dim_group)
        
        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(1, 1000)
        self.width_spin.setSuffix(" mils")
        self.width_spin.setDecimals(1)
        dim_layout.addRow("Width:", self.width_spin)
        
        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(1, 1000)
        self.height_spin.setSuffix(" mils")
        self.height_spin.setDecimals(1)
        dim_layout.addRow("Height:", self.height_spin)
        
        scroll_layout.addWidget(dim_group)
        
        # Terminals group
        term_group = QGroupBox("Terminals")
        term_layout = QVBoxLayout(term_group)
        
        # Terminal count
        self.terminal_count_spin = QSpinBox()
        self.terminal_count_spin.setRange(1, 10)
        self.terminal_count_spin.valueChanged.connect(self.update_terminal_table)
        term_layout.addWidget(QLabel("Number of Terminals:"))
        term_layout.addWidget(self.terminal_count_spin)
        
        # Terminal positions table
        self.terminal_table = QTableWidget()
        self.terminal_table.setColumnCount(3)
        self.terminal_table.setHorizontalHeaderLabels(["X Offset (mils)", "Y Offset (mils)", "Name"])
        self.terminal_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        term_layout.addWidget(self.terminal_table)
        
        scroll_layout.addWidget(term_group)
        
        # SVG group
        svg_group = QGroupBox("SVG Configuration")
        svg_layout = QFormLayout(svg_group)
        
        self.svg_file_edit = QLineEdit()
        svg_layout.addRow("SVG File:", self.svg_file_edit)
        
        self.svg_scaling_combo = QComboBox()
        self.svg_scaling_combo.addItems(["fit_within_bounds", "stretch_to_fit", "original_size"])
        svg_layout.addRow("Scaling Mode:", self.svg_scaling_combo)
        
        self.maintain_aspect_check = QCheckBox("Maintain Aspect Ratio")
        svg_layout.addRow(self.maintain_aspect_check)
        
        scroll_layout.addWidget(svg_group)
        
        # Grid group
        grid_group = QGroupBox("Grid Configuration")
        grid_layout = QFormLayout(grid_group)
        
        self.grid_alignment_combo = QComboBox()
        self.grid_alignment_combo.addItems(["component_based", "fixed", "auto"])
        grid_layout.addRow("Alignment:", self.grid_alignment_combo)
        
        self.snap_to_grid_check = QCheckBox("Snap to Grid")
        grid_layout.addRow(self.snap_to_grid_check)
        
        scroll_layout.addWidget(grid_group)
        
        # Debug group
        debug_group = QGroupBox("Debug Configuration")
        debug_layout = QFormLayout(debug_group)
        
        self.show_debug_check = QCheckBox("Show Debug Information")
        debug_layout.addRow(self.show_debug_check)
        
        scroll_layout.addWidget(debug_group)
        
        # Apply button
        apply_btn = QPushButton("Apply Changes")
        apply_btn.clicked.connect(self.apply_changes)
        scroll_layout.addWidget(apply_btn)
        
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
    
    def populate_values(self):
        """Populate the form with current configuration values"""
        if not self.config:
            return
        
        # Dimensions
        self.width_spin.setValue(self.config.width_mils)
        self.height_spin.setValue(self.config.height_mils)
        
        # Terminals
        terminal_positions = self.config.terminal_positions
        self.terminal_count_spin.setValue(len(terminal_positions))
        self.update_terminal_table()
        
        # SVG
        self.svg_file_edit.setText(self.config.svg_file)
        self.svg_scaling_combo.setCurrentText(self.config.svg_scaling)
        self.maintain_aspect_check.setChecked(self.config.maintain_aspect_ratio)
        
        # Grid
        self.grid_alignment_combo.setCurrentText(self.config.grid_alignment)
        self.snap_to_grid_check.setChecked(self.config.snap_to_grid)
        
        # Debug
        from config.config_manager import config_manager
        self.show_debug_check.setChecked(config_manager.is_debug_info_enabled())
    
    def update_terminal_table(self):
        """Update the terminal positions table"""
        count = self.terminal_count_spin.value()
        self.terminal_table.setRowCount(count)
        
        # Populate with current values
        terminal_positions = self.config.terminal_positions if self.config else []
        for i in range(count):
            if i < len(terminal_positions):
                pos = terminal_positions[i]
                self.terminal_table.setItem(i, 0, QTableWidgetItem(str(pos.get('x_offset_mils', 0))))
                self.terminal_table.setItem(i, 1, QTableWidgetItem(str(pos.get('y_offset_mils', 0))))
                self.terminal_table.setItem(i, 2, QTableWidgetItem(pos.get('name', f'Terminal {i+1}')))
            else:
                self.terminal_table.setItem(i, 0, QTableWidgetItem("0"))
                self.terminal_table.setItem(i, 1, QTableWidgetItem("0"))
                self.terminal_table.setItem(i, 2, QTableWidgetItem(f'Terminal {i+1}'))
    
    def apply_changes(self):
        """Apply the changes to the configuration"""
        if not self.config:
            return
        
        # Update dimensions
        self.config.dimensions['width_mils'] = self.width_spin.value()
        self.config.dimensions['height_mils'] = self.height_spin.value()
        
        # Update terminals
        terminal_positions = []
        for i in range(self.terminal_table.rowCount()):
            x_item = self.terminal_table.item(i, 0)
            y_item = self.terminal_table.item(i, 1)
            name_item = self.terminal_table.item(i, 2)
            
            if x_item and y_item and name_item:
                terminal_positions.append({
                    'x_offset_mils': float(x_item.text()),
                    'y_offset_mils': float(y_item.text()),
                    'name': name_item.text()
                })
        
        self.config.terminals['positions'] = terminal_positions
        self.config.terminals['count'] = len(terminal_positions)
        
        # Update SVG
        self.config.svg['file'] = self.svg_file_edit.text()
        self.config.svg['scaling'] = self.svg_scaling_combo.currentText()
        self.config.svg['maintain_aspect_ratio'] = self.maintain_aspect_check.isChecked()
        
        # Update grid
        self.config.grid['alignment'] = self.grid_alignment_combo.currentText()
        self.config.grid['snap_to_grid'] = self.snap_to_grid_check.isChecked()
        
        # Update debug setting
        from config.config_manager import config_manager
        config_manager.set_global_setting('show_debug_info', self.show_debug_check.isChecked())
        
        # Emit signal
        self.config_changed.emit(self.component_name, self.get_config_dict())
    
    def get_config_dict(self):
        """Get the current configuration as a dictionary"""
        return {
            'dimensions': self.config.dimensions,
            'terminals': self.config.terminals,
            'svg': self.config.svg,
            'grid': self.config.grid
        }


class ConfigEditorDialog(QDialog):
    """Main configuration editor dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Component Configuration Editor")
        self.setModal(True)
        self.resize(800, 600)
        
        self.setup_ui()
        self.load_configurations()
    
    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        
        # Create tab widget for different components
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        self.reload_btn = QPushButton("Reload from File")
        self.reload_btn.clicked.connect(self.reload_configurations)
        button_layout.addWidget(self.reload_btn)
        
        self.save_btn = QPushButton("Save to File")
        self.save_btn.clicked.connect(self.save_configurations)
        button_layout.addWidget(self.save_btn)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def load_configurations(self):
        """Load all component configurations"""
        self.tab_widget.clear()
        self.component_widgets = {}
        
        for component_name in config_manager.get_available_components():
            component_config = config_manager.get_component_config(component_name)
            if component_config:
                widget = ComponentConfigWidget(component_name, component_config)
                widget.config_changed.connect(self.on_config_changed)
                self.tab_widget.addTab(widget, component_name.title())
                self.component_widgets[component_name] = widget
    
    def reload_configurations(self):
        """Reload configurations from file"""
        if config_manager.reload_config():
            self.load_configurations()
            self.show_message("Configurations reloaded from file")
        else:
            self.show_message("Failed to reload configurations", error=True)
    
    def save_configurations(self):
        """Save configurations to file"""
        if config_manager.save_config():
            self.show_message("Configurations saved to file")
        else:
            self.show_message("Failed to save configurations", error=True)
    
    def on_config_changed(self, component_name: str, new_config: dict):
        """Handle configuration changes"""
        # Update the configuration manager
        component_config = config_manager.get_component_config(component_name)
        if component_config:
            component_config.dimensions = new_config['dimensions']
            component_config.terminals = new_config['terminals']
            component_config.svg = new_config['svg']
            component_config.grid = new_config['grid']
            
            # Update the configuration manager
            config_manager.update_component_config(component_name, component_config)
    
    def show_message(self, message: str, error: bool = False):
        """Show a message to the user"""
        # This could be enhanced with a proper message box or status bar
        print(f"{'ERROR:' if error else 'INFO:'} {message}")


def show_config_editor(parent=None):
    """Show the configuration editor dialog"""
    dialog = ConfigEditorDialog(parent)
    return dialog.exec()
