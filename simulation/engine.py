"""
Simulation engine for PyEWB
Handles circuit simulation using PySpice
"""

import numpy as np
from typing import Dict, Any, Optional, Tuple
import logging
from simulation.graph import CircuitGraph

# Try to import PySpice, handle gracefully if not available
try:
    from PySpice.Spice.Netlist import Circuit
    from PySpice.Unit import *
    from PySpice.Spice.Simulation import TransientAnalysis
    PYSPICE_AVAILABLE = True
except ImportError:
    PYSPICE_AVAILABLE = False
    logging.warning("PySpice not available. Simulation features will be limited.")


class SimulationEngine:
    """Handles circuit simulation using PySpice"""
    
    def __init__(self):
        """Initialize the simulation engine"""
        self.circuit_graph = None
        self.current_circuit = None
        self.simulation_results = None
        self.is_running = False
        
        if not PYSPICE_AVAILABLE:
            logging.warning("PySpice is not available. Please install it for full simulation support.")
    
    def set_circuit_graph(self, circuit_graph: CircuitGraph):
        """Set the circuit graph to simulate"""
        self.circuit_graph = circuit_graph
    
    def create_circuit(self, circuit_name: str = "PyEWB_Circuit") -> bool:
        """
        Create a PySpice circuit from the circuit graph
        
        Args:
            circuit_name: Name for the circuit
            
        Returns:
            True if successful, False otherwise
        """
        if not PYSPICE_AVAILABLE:
            logging.error("PySpice is not available")
            return False
        
        if not self.circuit_graph:
            logging.error("No circuit graph set")
            return False
        
        try:
            # Create new circuit
            self.current_circuit = Circuit(circuit_name)
            
            # Add components from the graph
            for edge in self.circuit_graph.graph.edges(data=True):
                component = edge[2].get('component')
                if component:
                    self._add_component_to_circuit(component, edge[0], edge[1])
            
            logging.info(f"Circuit '{circuit_name}' created successfully")
            return True
            
        except Exception as e:
            logging.error(f"Failed to create circuit: {e}")
            return False
    
    def _add_component_to_circuit(self, component, node1: str, node2: str):
        """Add a component to the PySpice circuit"""
        component_type = component.__class__.__name__.upper()
        component_name = component.name or component_type
        value = component.value or "1k"
        
        # Convert value to appropriate unit
        value_with_unit = self._parse_value_with_unit(value)
        
        if component_type == "RESISTOR":
            self.current_circuit.R(component_name, node1, node2, value_with_unit)
        
        elif component_type == "CAPACITOR":
            self.current_circuit.C(component_name, node1, node2, value_with_unit)
        
        elif component_type == "INDUCTOR":
            self.current_circuit.L(component_name, node1, node2, value_with_unit)
        
        elif component_type == "VOLTAGESOURCE":
            self.current_circuit.V(component_name, node1, node2, value_with_unit)
        
        elif component_type == "CURRENTSOURCE":
            self.current_circuit.I(component_name, node1, node2, value_with_unit)
        
        else:
            logging.warning(f"Unknown component type: {component_type}")
    
    def _parse_value_with_unit(self, value_str: str):
        """Parse a value string and return appropriate PySpice unit"""
        if not PYSPICE_AVAILABLE:
            return value_str
        
        value_str = value_str.strip().upper()
        
        # Handle different unit prefixes
        if value_str.endswith('K'):
            return float(value_str[:-1]) * kΩ
        elif value_str.endswith('M'):
            return float(value_str[:-1]) * mΩ
        elif value_str.endswith('U'):
            return float(value_str[:-1]) * uF
        elif value_str.endswith('N'):
            return float(value_str[:-1]) * nF
        elif value_str.endswith('P'):
            return float(value_str[:-1]) * pF
        elif value_str.endswith('V'):
            return float(value_str[:-1]) * V
        elif value_str.endswith('A'):
            return float(value_str[:-1]) * A
        else:
            # Try to parse as float
            try:
                return float(value_str)
            except ValueError:
                return value_str
    
    def run_transient_analysis(self, stop_time: float = 1e-3, step_time: float = 1e-6) -> Optional[Dict[str, Any]]:
        """
        Run a transient analysis simulation
        
        Args:
            stop_time: Stop time in seconds
            step_time: Time step in seconds
            
        Returns:
            Dictionary with simulation results or None if failed
        """
        if not PYSPICE_AVAILABLE:
            logging.error("PySpice is not available")
            return None
        
        if not self.current_circuit:
            logging.error("No circuit loaded")
            return None
        
        if self.is_running:
            logging.warning("Simulation already running")
            return None
        
        try:
            self.is_running = True
            
            # Create transient analysis
            simulator = self.current_circuit.simulator(temperature=25, nominal_temperature=25)
            analysis = simulator.transient(step_time=step_time, end_time=stop_time)
            
            # Extract results
            time_data = np.array(analysis.time)
            results = {
                'time': time_data,
                'nodes': {},
                'analysis': analysis
            }
            
            # Extract node voltages
            for node in self.current_circuit.nodes:
                if str(node) != '0':  # Skip ground node
                    try:
                        voltage_data = np.array(analysis[str(node)])
                        results['nodes'][str(node)] = voltage_data
                    except Exception as e:
                        logging.warning(f"Could not extract voltage for node {node}: {e}")
            
            # Extract component currents (if available)
            results['currents'] = {}
            for component in self.current_circuit.components:
                try:
                    current_data = np.array(analysis[str(component)])
                    results['currents'][str(component)] = current_data
                except Exception as e:
                    logging.debug(f"Could not extract current for {component}: {e}")
            
            self.simulation_results = results
            logging.info("Transient analysis completed successfully")
            return results
            
        except Exception as e:
            logging.error(f"Simulation failed: {e}")
            return None
        
        finally:
            self.is_running = False
    
    def run_dc_analysis(self, voltage_range: Tuple[float, float] = (0, 5), 
                       voltage_step: float = 0.1) -> Optional[Dict[str, Any]]:
        """
        Run a DC analysis simulation
        
        Args:
            voltage_range: Tuple of (start_voltage, end_voltage)
            voltage_step: Voltage step size
            
        Returns:
            Dictionary with simulation results or None if failed
        """
        if not PYSPICE_AVAILABLE:
            logging.error("PySpice is not available")
            return None
        
        if not self.current_circuit:
            logging.error("No circuit loaded")
            return None
        
        try:
            # Create DC analysis
            simulator = self.current_circuit.simulator(temperature=25, nominal_temperature=25)
            analysis = simulator.dc(Vin=slice(voltage_range[0], voltage_range[1], voltage_step))
            
            # Extract results
            voltage_data = np.array(analysis['Vin'])
            results = {
                'voltage': voltage_data,
                'nodes': {},
                'analysis': analysis
            }
            
            # Extract node voltages
            for node in self.current_circuit.nodes:
                if str(node) != '0':  # Skip ground node
                    try:
                        node_voltage = np.array(analysis[str(node)])
                        results['nodes'][str(node)] = node_voltage
                    except Exception as e:
                        logging.warning(f"Could not extract voltage for node {node}: {e}")
            
            self.simulation_results = results
            logging.info("DC analysis completed successfully")
            return results
            
        except Exception as e:
            logging.error(f"DC analysis failed: {e}")
            return None
    
    def get_simulation_results(self) -> Optional[Dict[str, Any]]:
        """Get the last simulation results"""
        return self.simulation_results
    
    def is_simulation_available(self) -> bool:
        """Check if simulation is available (PySpice installed)"""
        return PYSPICE_AVAILABLE
    
    def get_available_analyses(self) -> list:
        """Get list of available analysis types"""
        if not PYSPICE_AVAILABLE:
            return []
        
        return ['transient', 'dc', 'ac']
    
    def stop_simulation(self):
        """Stop the current simulation"""
        self.is_running = False
        logging.info("Simulation stopped")
    
    def clear_results(self):
        """Clear simulation results"""
        self.simulation_results = None
        logging.info("Simulation results cleared")
    
    def export_netlist(self, filename: str) -> bool:
        """
        Export the circuit as a SPICE netlist file
        
        Args:
            filename: Output filename
            
        Returns:
            True if successful, False otherwise
        """
        if not self.current_circuit:
            logging.error("No circuit loaded")
            return False
        
        try:
            with open(filename, 'w') as f:
                f.write(str(self.current_circuit))
            logging.info(f"Netlist exported to {filename}")
            return True
        except Exception as e:
            logging.error(f"Failed to export netlist: {e}")
            return False
