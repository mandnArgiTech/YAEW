"""
Generic Property Dialog for PyEWB
A reusable dialog for editing component properties
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                            QLineEdit, QComboBox, QPushButton, QLabel, QSpinBox, 
                            QDoubleSpinBox, QCheckBox, QTextEdit)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class PropertyDialog(QDialog):
    """Generic dialog for editing component properties"""
    
    def __init__(self, config: dict, current_values: dict, parent=None):
        super().__init__(parent)
        
        self.config = config
        self.current_values = current_values
        self.widgets = {}  # Store references to widgets
        
        self.setWindowTitle("Component Properties")
        self.setModal(True)
        self.resize(400, 300)
        
        self.setup_ui()
        self.populate_values()
    
    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        
        # Create form layout
        form_layout = QFormLayout()
        
        # Create widgets based on config
        for property_name, property_config in self.config.items():
            widget = self.create_widget(property_name, property_config)
            if widget:
                form_layout.addRow(property_name + ":", widget)
                self.widgets[property_name] = widget
        
        layout.addLayout(form_layout)
        
        # Add buttons
        button_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setDefault(True)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def create_widget(self, property_name: str, property_config: dict):
        """Create a widget based on property configuration"""
        widget_type = property_config.get('type', 'text')
        
        if widget_type == 'text':
            widget = QLineEdit()
            widget.setPlaceholderText(property_config.get('placeholder', ''))
            
        elif widget_type == 'combo':
            widget = QComboBox()
            options = property_config.get('options', [])
            widget.addItems(options)
            widget.setEditable(property_config.get('editable', False))
            
        elif widget_type == 'spinbox':
            widget = QSpinBox()
            widget.setRange(
                property_config.get('min', 0),
                property_config.get('max', 999999)
            )
            widget.setSuffix(property_config.get('suffix', ''))
            
        elif widget_type == 'doublespinbox':
            widget = QDoubleSpinBox()
            widget.setRange(
                property_config.get('min', 0.0),
                property_config.get('max', 999999.0)
            )
            widget.setDecimals(property_config.get('decimals', 2))
            widget.setSuffix(property_config.get('suffix', ''))
            
        elif widget_type == 'checkbox':
            widget = QCheckBox()
            
        elif widget_type == 'textarea':
            widget = QTextEdit()
            widget.setMaximumHeight(100)
            
        else:
            # Default to text input
            widget = QLineEdit()
        
        # Set tooltip if provided
        if 'tooltip' in property_config:
            widget.setToolTip(property_config['tooltip'])
        
        return widget
    
    def populate_values(self):
        """Populate widgets with current values"""
        for property_name, widget in self.widgets.items():
            current_value = self.current_values.get(property_name, '')
            
            if isinstance(widget, QLineEdit):
                widget.setText(str(current_value))
                
            elif isinstance(widget, QComboBox):
                # Try to find and select the current value
                index = widget.findText(str(current_value))
                if index >= 0:
                    widget.setCurrentIndex(index)
                else:
                    widget.setCurrentIndex(0)
                    
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                try:
                    widget.setValue(float(current_value))
                except (ValueError, TypeError):
                    widget.setValue(0)
                    
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(current_value))
                
            elif isinstance(widget, QTextEdit):
                widget.setPlainText(str(current_value))
    
    def get_values(self):
        """Get values from all widgets"""
        values = {}
        
        for property_name, widget in self.widgets.items():
            if isinstance(widget, QLineEdit):
                values[property_name] = widget.text()
                
            elif isinstance(widget, QComboBox):
                values[property_name] = widget.currentText()
                
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                values[property_name] = str(widget.value())
                
            elif isinstance(widget, QCheckBox):
                values[property_name] = str(widget.isChecked())
                
            elif isinstance(widget, QTextEdit):
                values[property_name] = widget.toPlainText()
        
        return values
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.accept()
        elif event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
