"""
Configuration Manager for PyEWB
Handles loading and managing component configurations from JSON/INI/YAML files
"""

import json
import os
from typing import Dict, Any, Optional, List
from PyQt6.QtCore import QObject, pyqtSignal


class ComponentConfig:
    """Configuration for a single component type"""
    
    def __init__(self, config_data: Dict[str, Any]):
        self.dimensions = config_data.get('dimensions', {})
        self.terminals = config_data.get('terminals', {})
        self.svg = config_data.get('svg', {})
        self.grid = config_data.get('grid', {})
    
    @property
    def width_mils(self) -> float:
        """Get component width in mils"""
        return self.dimensions.get('width_mils', 50.0)
    
    @property
    def height_mils(self) -> float:
        """Get component height in mils"""
        return self.dimensions.get('height_mils', 50.0)
    
    @property
    def terminal_positions(self) -> List[Dict[str, Any]]:
        """Get terminal positions configuration"""
        return self.terminals.get('positions', [])
    
    @property
    def svg_file(self) -> str:
        """Get SVG file path"""
        return self.svg.get('file', '')
    
    @property
    def svg_scaling(self) -> str:
        """Get SVG scaling mode"""
        return self.svg.get('scaling', 'fit_within_bounds')
    
    @property
    def maintain_aspect_ratio(self) -> bool:
        """Get whether to maintain SVG aspect ratio"""
        return self.svg.get('maintain_aspect_ratio', True)
    
    @property
    def grid_alignment(self) -> str:
        """Get grid alignment mode"""
        return self.grid.get('alignment', 'component_based')
    
    @property
    def snap_to_grid(self) -> bool:
        """Get whether to snap to grid"""
        return self.grid.get('snap_to_grid', True)


class ConfigManager(QObject):
    """Manages component configurations and global settings"""
    
    # Signals
    config_loaded = pyqtSignal(str)  # Emitted when config is loaded
    config_changed = pyqtSignal(str)  # Emitted when config changes
    
    def __init__(self, config_dir: str = "config"):
        super().__init__()
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "component_config.json")
        self.components: Dict[str, ComponentConfig] = {}
        self.global_settings: Dict[str, Any] = {}
        
        # Load configuration
        self.load_config()
    
    def load_config(self) -> bool:
        """Load configuration from JSON file"""
        try:
            if not os.path.exists(self.config_file):
                print(f"Configuration file not found: {self.config_file}")
                return False
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Load global settings
            self.global_settings = config_data.get('global_settings', {})
            
            # Load component configurations
            components_data = config_data.get('components', {})
            self.components = {}
            
            for component_name, component_data in components_data.items():
                self.components[component_name] = ComponentConfig(component_data)
            
            self.config_loaded.emit(self.config_file)
            print(f"Configuration loaded from {self.config_file}")
            return True
            
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return False
    
    def save_config(self) -> bool:
        """Save current configuration to JSON file"""
        try:
            # Ensure config directory exists
            os.makedirs(self.config_dir, exist_ok=True)
            
            # Prepare configuration data
            config_data = {
                "global_settings": self.global_settings,
                "components": {}
            }
            
            # Convert component configs back to dictionaries
            for name, config in self.components.items():
                config_data["components"][name] = {
                    "dimensions": config.dimensions,
                    "terminals": config.terminals,
                    "svg": config.svg,
                    "grid": config.grid
                }
            
            # Write to file
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.config_changed.emit(self.config_file)
            print(f"Configuration saved to {self.config_file}")
            return True
            
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def get_component_config(self, component_name: str) -> Optional[ComponentConfig]:
        """Get configuration for a specific component"""
        return self.components.get(component_name)
    
    def update_component_config(self, component_name: str, config: ComponentConfig) -> None:
        """Update configuration for a specific component"""
        self.components[component_name] = config
        self.config_changed.emit(component_name)
    
    def get_global_setting(self, key: str, default: Any = None) -> Any:
        """Get a global setting value"""
        return self.global_settings.get(key, default)
    
    def is_debug_info_enabled(self) -> bool:
        """Check if debug info should be shown"""
        return self.global_settings.get('show_debug_info', False)
    
    def set_global_setting(self, key: str, value: Any) -> None:
        """Set a global setting value"""
        self.global_settings[key] = value
        self.config_changed.emit(key)
    
    def get_available_components(self) -> List[str]:
        """Get list of available component types"""
        return list(self.components.keys())
    
    def reload_config(self) -> bool:
        """Reload configuration from file"""
        return self.load_config()
    
    def get_component_dimensions_pixels(self, component_name: str, pixels_per_mil: float = 1.0) -> tuple:
        """Get component dimensions in pixels"""
        config = self.get_component_config(component_name)
        if not config:
            return (50, 50)  # Default fallback
        
        width_pixels = config.width_mils * pixels_per_mil
        height_pixels = config.height_mils * pixels_per_mil
        return (width_pixels, height_pixels)
    
    def get_terminal_positions_pixels(self, component_name: str, pixels_per_mil: float = 1.0) -> List[Dict[str, Any]]:
        """Get terminal positions in pixels"""
        config = self.get_component_config(component_name)
        if not config:
            return []
        
        positions = []
        for terminal in config.terminal_positions:
            pixel_pos = {
                'x': terminal['x_offset_mils'] * pixels_per_mil,
                'y': terminal['y_offset_mils'] * pixels_per_mil,
                'name': terminal.get('name', '')
            }
            positions.append(pixel_pos)
        
        return positions


# Global configuration manager instance
config_manager = ConfigManager()
