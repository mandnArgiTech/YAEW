"""
Oscilloscope widget for PyEWB
Displays simulation results using pyqtgraph
"""

import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QSpinBox, QGroupBox
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

# Try to import pyqtgraph, handle gracefully if not available
try:
    import pyqtgraph as pg
    from pyqtgraph import PlotWidget, mkPen, mkBrush
    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False
    print("Warning: pyqtgraph not available. Oscilloscope features will be limited.")


class OscilloscopeWidget(QWidget):
    """Oscilloscope widget for displaying simulation results"""
    
    # Signals
    channel_selected = pyqtSignal(str)  # Emitted when a channel is selected
    time_range_changed = pyqtSignal(float, float)  # Emitted when time range changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        if not PYQTGRAPH_AVAILABLE:
            self._create_fallback_widget()
            return
        
        self._setup_ui()
        self._setup_plot()
        self._channels = {}  # Store channel data
        self._current_time_range = (0, 1e-3)  # Default time range
    
    def _setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        
        # Control panel
        control_panel = self._create_control_panel()
        layout.addWidget(control_panel)
        
        # Plot widget
        self.plot_widget = PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setLabel('left', 'Voltage', units='V')
        self.plot_widget.setLabel('bottom', 'Time', units='s')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.addLegend()
        
        layout.addWidget(self.plot_widget)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("QLabel { color: gray; }")
        layout.addWidget(self.status_label)
    
    def _create_control_panel(self):
        """Create the control panel"""
        group_box = QGroupBox("Oscilloscope Controls")
        layout = QHBoxLayout(group_box)
        
        # Channel selection
        layout.addWidget(QLabel("Channel:"))
        self.channel_combo = QComboBox()
        self.channel_combo.currentTextChanged.connect(self._on_channel_changed)
        layout.addWidget(self.channel_combo)
        
        # Time range controls
        layout.addWidget(QLabel("Time Range:"))
        self.time_start_spin = QSpinBox()
        self.time_start_spin.setRange(0, 10000)
        self.time_start_spin.setValue(0)
        self.time_start_spin.setSuffix(" μs")
        self.time_start_spin.valueChanged.connect(self._update_time_range)
        layout.addWidget(self.time_start_spin)
        
        layout.addWidget(QLabel("to"))
        self.time_end_spin = QSpinBox()
        self.time_end_spin.setRange(1, 10000)
        self.time_end_spin.setValue(1000)
        self.time_end_spin.setSuffix(" μs")
        self.time_end_spin.valueChanged.connect(self._update_time_range)
        layout.addWidget(self.time_end_spin)
        
        # Auto scale button
        self.auto_scale_btn = QPushButton("Auto Scale")
        self.auto_scale_btn.clicked.connect(self._auto_scale)
        layout.addWidget(self.auto_scale_btn)
        
        # Clear button
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self._clear_plot)
        layout.addWidget(self.clear_btn)
        
        layout.addStretch()
        return group_box
    
    def _setup_plot(self):
        """Set up the plot configuration"""
        # Set up colors for different channels
        self.channel_colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (255, 165, 0),  # Orange
            (128, 0, 128),  # Purple
            (255, 192, 203), # Pink
            (0, 255, 255),  # Cyan
            (255, 255, 0),  # Yellow
        ]
        
        self.channel_plots = {}  # Store plot items for each channel
    
    def _create_fallback_widget(self):
        """Create a fallback widget when pyqtgraph is not available"""
        layout = QVBoxLayout(self)
        
        label = QLabel("Oscilloscope Widget")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("QLabel { font-size: 18px; color: gray; }")
        layout.addWidget(label)
        
        info_label = QLabel("pyqtgraph is not available.\nPlease install it to use the oscilloscope.")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("QLabel { color: gray; }")
        layout.addWidget(info_label)
    
    def plot_data(self, time_data: np.ndarray, voltage_data: np.ndarray, 
                  channel_name: str = "Channel 1", color: tuple = None):
        """
        Plot data on the oscilloscope
        
        Args:
            time_data: Time array
            voltage_data: Voltage array
            channel_name: Name of the channel
            color: RGB color tuple (optional)
        """
        if not PYQTGRAPH_AVAILABLE:
            self.status_label.setText("pyqtgraph not available")
            return
        
        # Store channel data
        self._channels[channel_name] = {
            'time': time_data,
            'voltage': voltage_data
        }
        
        # Update channel combo if new channel
        if channel_name not in [self.channel_combo.itemText(i) for i in range(self.channel_combo.count())]:
            self.channel_combo.addItem(channel_name)
        
        # Get color for this channel
        if color is None:
            channel_index = len(self._channels) - 1
            color = self.channel_colors[channel_index % len(self.channel_colors)]
        
        # Create or update plot
        if channel_name in self.channel_plots:
            # Update existing plot
            plot_item = self.channel_plots[channel_name]
            plot_item.setData(time_data, voltage_data)
        else:
            # Create new plot
            pen = mkPen(color=color, width=2)
            plot_item = self.plot_widget.plot(time_data, voltage_data, 
                                            pen=pen, name=channel_name)
            self.channel_plots[channel_name] = plot_item
        
        # Update status
        self.status_label.setText(f"Plotting {channel_name}: {len(time_data)} points")
        
        # Auto scale if this is the first channel
        if len(self._channels) == 1:
            self._auto_scale()
    
    def plot_multiple_channels(self, data_dict: dict):
        """
        Plot multiple channels at once
        
        Args:
            data_dict: Dictionary with channel names as keys and (time, voltage) tuples as values
        """
        for channel_name, (time_data, voltage_data) in data_dict.items():
            self.plot_data(time_data, voltage_data, channel_name)
    
    def _on_channel_changed(self, channel_name: str):
        """Handle channel selection change"""
        if channel_name in self._channels:
            self.channel_selected.emit(channel_name)
            self.status_label.setText(f"Selected channel: {channel_name}")
    
    def _update_time_range(self):
        """Update the time range of the plot"""
        start_time = self.time_start_spin.value() * 1e-6  # Convert μs to s
        end_time = self.time_end_spin.value() * 1e-6      # Convert μs to s
        
        self.plot_widget.setXRange(start_time, end_time)
        self._current_time_range = (start_time, end_time)
        self.time_range_changed.emit(start_time, end_time)
    
    def _auto_scale(self):
        """Auto scale the plot to fit all data"""
        if not self._channels:
            return
        
        # Find global time and voltage ranges
        all_times = []
        all_voltages = []
        
        for channel_data in self._channels.values():
            all_times.extend(channel_data['time'])
            all_voltages.extend(channel_data['voltage'])
        
        if all_times and all_voltages:
            time_min, time_max = min(all_times), max(all_times)
            voltage_min, voltage_min = min(all_voltages), max(all_voltages)
            
            # Add some margin
            time_margin = (time_max - time_min) * 0.1
            voltage_margin = (voltage_min - voltage_min) * 0.1
            
            self.plot_widget.setXRange(time_min - time_margin, time_max + time_margin)
            self.plot_widget.setYRange(voltage_min - voltage_margin, voltage_min + voltage_margin)
            
            # Update spin boxes
            self.time_start_spin.setValue(int((time_min - time_margin) * 1e6))
            self.time_end_spin.setValue(int((time_max + time_margin) * 1e6))
    
    def _clear_plot(self):
        """Clear all plots"""
        self.plot_widget.clear()
        self.channel_plots.clear()
        self._channels.clear()
        self.channel_combo.clear()
        self.status_label.setText("Plot cleared")
    
    def set_time_range(self, start_time: float, end_time: float):
        """Set the time range programmatically"""
        self.time_start_spin.setValue(int(start_time * 1e6))
        self.time_end_spin.setValue(int(end_time * 1e6))
        self._update_time_range()
    
    def set_voltage_range(self, min_voltage: float, max_voltage: float):
        """Set the voltage range programmatically"""
        if PYQTGRAPH_AVAILABLE:
            self.plot_widget.setYRange(min_voltage, max_voltage)
    
    def get_channel_data(self, channel_name: str) -> tuple:
        """Get data for a specific channel"""
        if channel_name in self._channels:
            return self._channels[channel_name]['time'], self._channels[channel_name]['voltage']
        return None, None
    
    def get_available_channels(self) -> list:
        """Get list of available channels"""
        return list(self._channels.keys())
    
    def export_data(self, filename: str, channel_name: str = None) -> bool:
        """
        Export channel data to file
        
        Args:
            filename: Output filename
            channel_name: Specific channel to export (None for all)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if channel_name:
                if channel_name in self._channels:
                    data = self._channels[channel_name]
                    np.savetxt(filename, np.column_stack((data['time'], data['voltage'])), 
                              header='Time,Voltage', delimiter=',')
                else:
                    return False
            else:
                # Export all channels
                with open(filename, 'w') as f:
                    f.write('Time')
                    for ch_name in self._channels.keys():
                        f.write(f',{ch_name}')
                    f.write('\n')
                    
                    # Find common time base
                    all_times = set()
                    for data in self._channels.values():
                        all_times.update(data['time'])
                    all_times = sorted(all_times)
                    
                    for t in all_times:
                        f.write(f'{t}')
                        for ch_name, data in self._channels.items():
                            # Interpolate voltage at this time
                            voltage = np.interp(t, data['time'], data['voltage'])
                            f.write(f',{voltage}')
                        f.write('\n')
            
            self.status_label.setText(f"Data exported to {filename}")
            return True
            
        except Exception as e:
            self.status_label.setText(f"Export failed: {str(e)}")
            return False
