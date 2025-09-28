# PyEWB - Python Electronics Workbench

A Python-based electronic circuit simulator and schematic editor built with PyQt6, inspired by Electronics Workbench (EWB).

## Features

- **Schematic Editor**: Visual circuit design with drag-and-drop components
- **Component Library**: Resistors, capacitors, inductors, voltage/current sources
- **Wire Drawing**: Interactive wire connection between components
- **Circuit Simulation**: Transient and DC analysis using PySpice
- **Oscilloscope**: Real-time visualization of simulation results
- **Netlist Export**: Export circuits as SPICE netlists

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd PyEWB
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

## Dependencies

- **PyQt6**: GUI framework
- **pyqtgraph**: Plotting and visualization
- **numpy**: Numerical computations
- **networkx**: Graph-based circuit representation
- **PySpice**: SPICE circuit simulation
- **matplotlib**: Additional plotting support

## Usage

### Creating a Circuit

1. **Add Components**: Click on component buttons in the left toolbar to add them to the schematic
2. **Connect Components**: Click on component terminals to start drawing wires, then click on another terminal to complete the connection
3. **Move Components**: Drag components to reposition them
4. **Edit Properties**: Double-click components to edit their values

### Running Simulations

1. **Setup Circuit**: Create your circuit in the schematic editor
2. **Run Simulation**: Use the Simulate menu to run transient or DC analysis
3. **View Results**: Use the oscilloscope widget to visualize simulation results

### Available Components

- **Resistor**: Standard zig-zag symbol with configurable resistance
- **Capacitor**: (Planned)
- **Inductor**: (Planned)
- **Voltage Source**: (Planned)
- **Current Source**: (Planned)
- **Ground**: (Planned)

## Project Structure

```
PyEWB/
├── main.py                 # Main application entry point
├── components/             # Electronic component classes
│   ├── __init__.py
│   ├── base.py            # Base component class
│   ├── resistor.py        # Resistor component
│   └── wire.py            # Wire connection class
├── simulation/             # Circuit simulation
│   ├── __init__.py
│   ├── graph.py           # Circuit graph representation
│   └── engine.py          # Simulation engine
├── ui/                     # User interface components
│   ├── __init__.py
│   ├── schematic_scene.py # Schematic editor scene
│   └── oscilloscope.py    # Oscilloscope widget
├── resources/              # Resources and assets
│   └── icons/             # Component icons
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Development

### Adding New Components

1. Create a new component class in `components/` that inherits from `BaseComponent`
2. Implement the required methods: `paint()`, `boundingRect()`
3. Add terminals using `add_terminal()`
4. Update the main window to include the new component in the toolbar

### Adding New Analysis Types

1. Add new methods to `SimulationEngine` class
2. Implement the analysis using PySpice
3. Update the UI to provide access to the new analysis

## Known Issues

- PySpice integration requires NgSpice to be installed on the system
- Some advanced SPICE features may not be fully supported
- Component library is currently limited

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Inspired by Electronics Workbench (EWB)
- Built with PyQt6 and PySpice
- Uses networkx for circuit graph representation
