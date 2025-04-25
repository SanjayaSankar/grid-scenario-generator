"""
Utility functions for the grid scenario generator.
"""
import os
import json
import uuid
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)


def generate_id() -> str:
    """
    Generate a unique identifier.
    
    Returns:
        String UUID
    """
    return str(uuid.uuid4())


def save_json(data: Dict[str, Any], file_path: str) -> None:
    """
    Save data as JSON to a file.
    
    Args:
        data: Data to save
        file_path: Output file path
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)


def load_json(file_path: str) -> Dict[str, Any]:
    """
    Load JSON data from a file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Loaded data
    """
    with open(file_path, 'r') as f:
        return json.load(f)


def ensure_directory(directory: str) -> None:
    """
    Ensure a directory exists.
    
    Args:
        directory: Directory path
    """
    os.makedirs(directory, exist_ok=True)


def calculate_power_flow(
    buses: List[Dict[str, Any]],
    lines: List[Dict[str, Any]],
    transformers: List[Dict[str, Any]],
    loads: List[Dict[str, Any]],
    generators: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calculate DC power flow for a grid scenario.
    This is a simplified implementation - a real system would use a proper power flow solver.
    
    Args:
        buses: List of bus data
        lines: List of line data
        transformers: List of transformer data
        loads: List of load data
        generators: List of generator data
        
    Returns:
        Dictionary with power flow results
    """
    # Create a mapping of bus IDs to indices
    bus_indices = {bus['uid']: i for i, bus in enumerate(buses)}
    num_buses = len(buses)
    
    # Initialize admittance matrix (Y-bus)
    Y = np.zeros((num_buses, num_buses), dtype=complex)
    
    # Add lines to admittance matrix
    for line in lines:
        if line.get('initial_status', {}).get('on_status', 0) == 1:
            from_bus = line['fr_bus']
            to_bus = line['to_bus']
            
            # Get indices
            from_idx = bus_indices[from_bus]
            to_idx = bus_indices[to_bus]
            
            # Calculate admittance
            r = line['r']
            x = line['x']
            b = line.get('b', 0)
            
            # Line admittance
            y = 1 / complex(r, x)
            
            # Add to Y-bus matrix
            Y[from_idx, to_idx] -= y
            Y[to_idx, from_idx] -= y
            Y[from_idx, from_idx] += y + complex(0, b/2)
            Y[to_idx, to_idx] += y + complex(0, b/2)
    
    # Add transformers to admittance matrix
    for transformer in transformers:
        if transformer.get('initial_status', {}).get('on_status', 0) == 1:
            from_bus = transformer['fr_bus']
            to_bus = transformer['to_bus']
            
            # Get indices
            from_idx = bus_indices[from_bus]
            to_idx = bus_indices[to_bus]
            
            # Calculate admittance
            r = transformer['r']
            x = transformer['x']
            
            # Transformer admittance
            y = 1 / complex(r, x)
            
            # Add to Y-bus matrix
            Y[from_idx, to_idx] -= y
            Y[to_idx, from_idx] -= y
            Y[from_idx, from_idx] += y
            Y[to_idx, to_idx] += y
    
    # Initialize power injection vector
    P = np.zeros(num_buses)
    
    # Add loads
    for load in loads:
        bus = load['bus']
        bus_idx = bus_indices[bus]
        
        # Subtract load (since load consumes power)
        P[bus_idx] -= load.get('initial_status', {}).get('p', 0)
    
    # Add generators
    for generator in generators:
        bus = generator['bus']
        bus_idx = bus_indices[bus]
        
        # Add generation
        P[bus_idx] += generator.get('initial_status', {}).get('p', 0)
    
    # Solve DC power flow
    # In a DC power flow, we solve: P = B' * theta
    # where B' is the imaginary part of the Y-bus matrix
    
    # Extract B' (ignoring diagonal elements)
    B_prime = -np.imag(Y)
    
    # Set reference bus (slack bus) - assume the first bus
    ref_idx = 0
    
    # Remove reference bus from equations
    B_prime_reduced = np.delete(np.delete(B_prime, ref_idx, 0), ref_idx, 1)
    P_reduced = np.delete(P, ref_idx)
    
    # Solve for voltage angles
    try:
        theta_reduced = np.linalg.solve(B_prime_reduced, P_reduced)
        
        # Insert reference bus angle (zero)
        theta = np.zeros(num_buses)
        theta[1:] = theta_reduced  # Assuming ref_idx = 0
        
        # Calculate line flows
        flows = {}
        
        for line in lines:
            if line.get('initial_status', {}).get('on_status', 0) == 1:
                from_bus = line['fr_bus']
                to_bus = line['to_bus']
                
                # Get indices
                from_idx = bus_indices[from_bus]
                to_idx = bus_indices[to_bus]
                
                # Line reactance
                x = line['x']
                
                # Calculate flow
                flow = (theta[from_idx] - theta[to_idx]) / x
                
                # Store flow
                line_id = line['uid']
                flows[line_id] = flow
        
        return {
            'success': True,
            'theta': theta.tolist(),
            'flows': flows,
        }
    except np.linalg.LinAlgError:
        logger.error("Failed to solve DC power flow - singular matrix")
        return {
            'success': False,
            'error': "Singular matrix - check if the grid is connected",
        }


def validate_scenario_physics(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that a scenario respects physical constraints.
    
    Args:
        scenario: Scenario data
        
    Returns:
        Dictionary with validation results
    """
    network = scenario.get('network', {})
    
    # Extract components
    buses = network.get('bus', [])
    ac_lines = network.get('ac_line', [])
    transformers = network.get('two_winding_transformer', [])
    devices = network.get('simple_dispatchable_device', [])
    
    # Split devices into loads and generators
    loads = []
    generators = []
    
    for device in devices:
        if device.get('device_type') == 'consumer':
            loads.append(device)
        elif device.get('device_type') == 'producer':
            generators.append(device)
    
    # Validate bus voltage constraints
    voltage_violations = []
    
    for bus in buses:
        vm_lb = bus.get('vm_lb', 0.95)
        vm_ub = bus.get('vm_ub', 1.05)
        vm = bus.get('initial_status', {}).get('vm', 1.0)
        
        if vm < vm_lb:
            voltage_violations.append({
                'bus_id': bus['uid'],
                'type': 'Low voltage',
                'value': vm,
                'limit': vm_lb,
            })
        elif vm > vm_ub:
            voltage_violations.append({
                'bus_id': bus['uid'],
                'type': 'High voltage',
                'value': vm,
                'limit': vm_ub,
            })
    
    # Validate line flow constraints
    line_violations = []
    
    # Calculate power flow
    flow_results = calculate_power_flow(buses, ac_lines, transformers, loads, generators)
    
    if flow_results.get('success', False):
        flows = flow_results.get('flows', {})
        
        for line in ac_lines:
            line_id = line['uid']
            if line_id in flows:
                flow = abs(flows[line_id])
                limit = line.get('mva_ub_nom', float('inf'))
                
                if flow > limit:
                    line_violations.append({
                        'line_id': line_id,
                        'type': 'Flow exceeds limit',
                        'value': flow,
                        'limit': limit,
                    })
    
    # Check overall validation result
    is_valid = len(voltage_violations) == 0 and len(line_violations) == 0
    
    return {
        'is_valid': is_valid,
        'voltage_violations': voltage_violations,
        'line_violations': line_violations,
        'flow_results': flow_results,
    }