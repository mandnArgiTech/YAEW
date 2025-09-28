#!/usr/bin/env python3
"""
Basic test script for PyEWB
Tests the core functionality without GUI dependencies
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported"""
    try:
        from components.base import BaseComponent
        from components.resistor import Resistor
        from components.wire import Wire
        from simulation.graph import CircuitGraph
        from simulation.engine import SimulationEngine
        print("✓ All core modules imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_circuit_graph():
    """Test circuit graph functionality"""
    try:
        from simulation.graph import CircuitGraph
        from components.resistor import Resistor
        
        # Create circuit graph
        graph = CircuitGraph()
        
        # Create a resistor
        resistor = Resistor("R1", "1k")
        
        # Add resistor to graph
        node1, node2 = graph.add_component(resistor)
        
        # Test netlist generation
        netlist = graph.generate_pyspice_netlist()
        print("✓ Circuit graph functionality works")
        print(f"  Generated netlist:\n{netlist}")
        return True
    except Exception as e:
        print(f"✗ Circuit graph test failed: {e}")
        return False

def test_resistor_component():
    """Test resistor component functionality"""
    try:
        from components.resistor import Resistor
        
        # Create resistor
        resistor = Resistor("R1", "1k")
        
        # Test properties
        assert resistor.name == "R1"
        assert resistor.value == "1k"
        assert len(resistor.terminals) == 2
        
        # Test terminal positions
        pos1 = resistor.get_terminal_position(0)
        pos2 = resistor.get_terminal_position(1)
        
        print("✓ Resistor component functionality works")
        print(f"  Resistor: {resistor.name} = {resistor.value}")
        print(f"  Terminals: {pos1}, {pos2}")
        return True
    except Exception as e:
        print(f"✗ Resistor component test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("PyEWB Basic Tests")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_resistor_component,
        test_circuit_graph,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! PyEWB core functionality is working.")
    else:
        print("❌ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()
