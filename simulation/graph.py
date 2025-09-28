"""
Circuit graph representation for PyEWB
Manages circuit connectivity using networkx
"""

import networkx as nx
from typing import List, Dict, Any, Optional, Tuple
from components.base import BaseComponent


class CircuitGraph:
    """Manages circuit connectivity as a graph"""
    
    def __init__(self):
        """Initialize the circuit graph"""
        self.graph = nx.Graph()
        self.components = {}  # component_id -> component_instance
        self.node_counter = 1  # Start from 1, 0 is reserved for GND
        self._node_map = {}  # Maps (component_id, terminal) -> node_id
    
    def add_component(self, component: BaseComponent, node1: str = None, node2: str = None) -> Tuple[str, str]:
        """
        Add a component to the circuit graph
        
        Args:
            component: The component instance to add
            node1: First node name (optional, will be auto-generated if not provided)
            node2: Second node name (optional, will be auto-generated if not provided)
            
        Returns:
            Tuple of (node1, node2) that the component was connected to
        """
        # Generate node names if not provided
        if node1 is None:
            node1 = f"N{self.node_counter}"
            self.node_counter += 1
        
        if node2 is None:
            node2 = f"N{self.node_counter}"
            self.node_counter += 1
        
        # Store component
        self.components[component.id] = component
        
        # Add nodes to graph if they don't exist
        if not self.graph.has_node(node1):
            self.graph.add_node(node1)
        
        if not self.graph.has_node(node2):
            self.graph.add_node(node2)
        
        # Add edge (component) between nodes
        self.graph.add_edge(node1, node2, component=component)
        
        # Map component terminals to nodes
        if len(component.terminals) >= 2:
            self._node_map[(component.id, 0)] = node1
            self._node_map[(component.id, 1)] = node2
        
        return node1, node2
    
    def remove_component(self, component_id: str):
        """
        Remove a component from the circuit graph
        
        Args:
            component_id: ID of the component to remove
        """
        if component_id in self.components:
            # Find and remove the edge
            edges_to_remove = []
            for edge in self.graph.edges(data=True):
                if edge[2].get('component', {}).id == component_id:
                    edges_to_remove.append((edge[0], edge[1]))
            
            for edge in edges_to_remove:
                self.graph.remove_edge(edge[0], edge[1])
            
            # Remove component from storage
            del self.components[component_id]
            
            # Clean up node mappings
            keys_to_remove = [key for key in self._node_map.keys() if key[0] == component_id]
            for key in keys_to_remove:
                del self._node_map[key]
    
    def get_component_nodes(self, component_id: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Get the nodes connected to a component
        
        Args:
            component_id: ID of the component
            
        Returns:
            Tuple of (node1, node2) or (None, None) if not found
        """
        if component_id not in self.components:
            return None, None
        
        # Find the edge for this component
        for edge in self.graph.edges(data=True):
            if edge[2].get('component', {}).id == component_id:
                return edge[0], edge[1]
        
        return None, None
    
    def get_components_at_node(self, node: str) -> List[BaseComponent]:
        """
        Get all components connected to a specific node
        
        Args:
            node: Node name
            
        Returns:
            List of components connected to the node
        """
        components = []
        for edge in self.graph.edges(node, data=True):
            component = edge[2].get('component')
            if component:
                components.append(component)
        return components
    
    def generate_pyspice_netlist(self) -> str:
        """
        Generate a PySpice-compatible netlist from the circuit graph
        
        Returns:
            String containing the netlist
        """
        netlist_lines = []
        
        # Add circuit title
        netlist_lines.append("* PyEWB Circuit Netlist")
        netlist_lines.append("* Generated automatically")
        netlist_lines.append("")
        
        # Add components
        for edge in self.graph.edges(data=True):
            component = edge[2].get('component')
            if component:
                node1, node2 = edge[0], edge[1]
                netlist_line = self._component_to_netlist_line(component, node1, node2)
                if netlist_line:
                    netlist_lines.append(netlist_line)
        
        # Add ground reference
        netlist_lines.append("")
        netlist_lines.append("* Ground reference")
        netlist_lines.append(".end")
        
        return "\n".join(netlist_lines)
    
    def _component_to_netlist_line(self, component: BaseComponent, node1: str, node2: str) -> str:
        """
        Convert a component to a netlist line
        
        Args:
            component: Component instance
            node1: First node
            node2: Second node
            
        Returns:
            Netlist line string
        """
        component_type = component.__class__.__name__.upper()
        component_name = component.name or component_type
        
        # Handle different component types
        if component_type == "RESISTOR":
            value = component.value or "1k"
            return f"R{component_name} {node1} {node2} {value}"
        
        elif component_type == "CAPACITOR":
            value = component.value or "1u"
            return f"C{component_name} {node1} {node2} {value}"
        
        elif component_type == "INDUCTOR":
            value = component.value or "1m"
            return f"L{component_name} {node1} {node2} {value}"
        
        elif component_type == "VOLTAGESOURCE":
            value = component.value or "1V"
            return f"V{component_name} {node1} {node2} {value}"
        
        elif component_type == "CURRENTSOURCE":
            value = component.value or "1A"
            return f"I{component_name} {node1} {node2} {value}"
        
        else:
            # Generic component
            value = component.value or "1"
            return f"X{component_name} {node1} {node2} {value}"
    
    def get_circuit_info(self) -> Dict[str, Any]:
        """
        Get information about the circuit
        
        Returns:
            Dictionary with circuit information
        """
        return {
            'num_nodes': self.graph.number_of_nodes(),
            'num_components': len(self.components),
            'num_edges': self.graph.number_of_edges(),
            'is_connected': nx.is_connected(self.graph),
            'components': list(self.components.keys()),
            'nodes': list(self.graph.nodes())
        }
    
    def find_short_circuits(self) -> List[Tuple[str, str]]:
        """
        Find potential short circuits in the circuit
        
        Returns:
            List of node pairs that might be shorted
        """
        short_circuits = []
        
        # Check for multiple components between the same nodes
        edge_counts = {}
        for edge in self.graph.edges():
            edge_key = tuple(sorted(edge))
            edge_counts[edge_key] = edge_counts.get(edge_key, 0) + 1
        
        for edge, count in edge_counts.items():
            if count > 1:
                short_circuits.append(edge)
        
        return short_circuits
    
    def validate_circuit(self) -> Dict[str, Any]:
        """
        Validate the circuit for common issues
        
        Returns:
            Dictionary with validation results
        """
        issues = []
        warnings = []
        
        # Check for short circuits
        short_circuits = self.find_short_circuits()
        if short_circuits:
            issues.append(f"Short circuits detected: {short_circuits}")
        
        # Check for isolated components
        isolated_components = []
        for component_id, component in self.components.items():
            node1, node2 = self.get_component_nodes(component_id)
            if node1 is None or node2 is None:
                isolated_components.append(component_id)
        
        if isolated_components:
            warnings.append(f"Isolated components: {isolated_components}")
        
        # Check for floating nodes
        floating_nodes = []
        for node in self.graph.nodes():
            if self.graph.degree(node) == 0:
                floating_nodes.append(node)
        
        if floating_nodes:
            warnings.append(f"Floating nodes: {floating_nodes}")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'short_circuits': short_circuits,
            'isolated_components': isolated_components,
            'floating_nodes': floating_nodes
        }
