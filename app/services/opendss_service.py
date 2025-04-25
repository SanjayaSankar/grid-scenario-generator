"""
Service for validating power grid scenarios using OpenDSS.
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional
import numpy as np
import dss

logger = logging.getLogger(__name__)

class OpenDSSService:
    """Service for validating power grid scenarios using OpenDSS."""
    
    def __init__(self, dss_path: Optional[str] = None):
        """
        Initialize the OpenDSS service.
        
        Args:
            dss_path: Optional path to OpenDSS installation
        """
        try:
            # Initialize OpenDSS with default settings
            self.dss = dss.DSS
            self.dss_path = dss_path or os.getenv('OPENDSS_PATH')
            
            if self.dss_path:
                self.dss.Text.Command = f'Set DSSPath="{self.dss_path}"'
            
            # Initialize a new circuit
            self.dss.Text.Command = 'Clear'
            self.dss.Text.Command = 'New Circuit.Default'
            
            # Set basic circuit parameters
            self.dss.Text.Command = 'Set DefaultBaseFrequency=60'
            self.dss.Text.Command = 'Set VoltageBases=[115, 12.47]'
            self.dss.Text.Command = 'Set Mode=Snap'
            self.dss.Text.Command = 'Set ControlMode=Static'
            
            logger.info("OpenDSS service initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing OpenDSS: {str(e)}")
            raise
    
    def validate_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a power grid scenario using OpenDSS.
        
        Args:
            scenario: Power grid scenario to validate
            
        Returns:
            Validation results
        """
        try:
            # Create temporary OpenDSS script
            script_path = self._create_opendss_script(scenario)
            
            # Clear existing circuit and create new one
            self.dss.Text.Command = 'Clear'
            self.dss.Text.Command = 'New Circuit.Scenario'
            
            # Run OpenDSS simulation
            self.dss.Text.Command = f'Compile "{script_path}"'
            
            # Set solution parameters
            self.dss.Text.Command = 'Set Mode=Snap'
            self.dss.Text.Command = 'Set ControlMode=Static'
            self.dss.Text.Command = 'Set MaxIterations=100'
            self.dss.Text.Command = 'Set Tolerance=0.0001'
            
            # Solve the circuit
            self.dss.Text.Command = 'Solve'
            
            # Get simulation results
            results = self._get_simulation_results()
            
            # Clean up temporary files
            os.remove(script_path)
            
            return results
        except Exception as e:
            logger.error(f"Error validating scenario: {str(e)}")
            raise
    
    def _create_opendss_script(self, scenario: Dict[str, Any]) -> str:
        """
        Create OpenDSS script from scenario.
        
        Args:
            scenario: Power grid scenario
            
        Returns:
            Path to created script
        """
        script_lines = []
        
        # Log scenario structure for debugging
        logger.info(f"Creating OpenDSS script for scenario: {json.dumps(scenario['network'].keys())}")
        
        # Add base settings
        script_lines.extend([
            'Clear',
            'New Circuit.Scenario BasekV=115',  # Define base circuit with voltage
            'Set DefaultBaseFrequency=60',
            'CalcVoltageBases',  # Calculate voltage bases
            'Set Mode=Snap',
            'Set ControlMode=OFF'  # Turn off controls for initial solution
        ])
        
        # Debug log bus data
        logger.info(f"Bus data structure: {json.dumps(scenario['network']['bus'][0]) if scenario['network']['bus'] else 'No buses'}")
        
        # Add buses - Add nodes to existing circuit
        for bus in scenario['network']['bus']:
            bus_id = bus["uid"]
            base_kv = bus.get("base_nom_volt", 115.0)  # Default to 115 kV if not specified
            
            # Basic bus definition with the circuit already established
            script_lines.append(f'New Load.Load_{bus_id} Bus1={bus_id} kV={base_kv} kW=0.001 kvar=0 phases=3')
            
        # Add lines
        for line in scenario['network']['ac_line']:
            fr_bus = line["fr_bus"]
            to_bus = line["to_bus"]
            r = line.get("r", 0.01)
            x = line.get("x", 0.1)
            b = line.get("b", 0.01)
            norm_amps = line.get("mva_ub_nom", 100)
            
            script_lines.append(
                f'New Line.{line["uid"]} '
                f'Bus1={fr_bus} '
                f'Bus2={to_bus} '
                f'R1={r} '
                f'X1={x} '
                f'B1={b} '
                f'Phases=3 '
                f'NormAmps={norm_amps}'
            )
        
        # Add transformers
        for xfmr in scenario['network'].get('two_winding_transformer', []):
            script_lines.append(
                f'New Transformer.{xfmr["uid"]} '
                f'Bus1={xfmr["fr_bus"]} '
                f'Bus2={xfmr["to_bus"]} '
                f'R1={xfmr["r"]} '
                f'X1={xfmr["x"]} '
                f'B1={xfmr["b"]} '
                f'NormAmps={xfmr["mva_ub_nom"]} '
                f'EmergAmps={xfmr["mva_ub_em"]}'
            )
        
        # Add generators
        for gen in scenario['network']['simple_dispatchable_device']:
            if gen['device_type'] == 'producer':
                bus_id = gen["bus"]
                kw = gen["initial_status"].get("p", 100) * 1000  # Convert to kW
                kvar = gen["initial_status"].get("q", 20) * 1000  # Convert to kVAR
                kv = gen.get("vg", 1.0) * 115  # Use voltage in kV
                
                script_lines.append(
                    f'New Generator.{gen["uid"]} '
                    f'Bus1={bus_id} '
                    f'kV={kv} '
                    f'kW={kw} '
                    f'kvar={kvar} '
                    f'Model=3'  # Constant PQ model
                )
        
        # Add loads
        for load in scenario['network']['simple_dispatchable_device']:
            if load['device_type'] == 'consumer':
                bus_id = load["bus"]
                kw = load["initial_status"].get("p", 100) * 1000  # Convert to kW
                kvar = load["initial_status"].get("q", 20) * 1000  # Convert to kVAR
                
                script_lines.append(
                    f'New Load.{load["uid"]} '
                    f'Bus1={bus_id} '
                    f'kW={kw} '
                    f'kvar={kvar} '
                    f'Model=1'  # Constant power load model
                )
        
        # Add solution commands
        script_lines.extend([
            'Set VoltageBases=[115, 13.8]',
            'CalcVoltageBases',
            'Solve',
            'Show Voltages LN Nodes',
            'Show Currents Elements',
            'Show Powers kVA Elements'
        ])
        
        # Save script to temporary file
        script_path = 'temp_scenario.dss'
        with open(script_path, 'w') as f:
            f.write('\n'.join(script_lines))
        
        # Log the script for debugging
        logger.info(f"Generated OpenDSS script saved to {script_path}")
        
        return script_path
    
    def _get_simulation_results(self) -> Dict[str, Any]:
        """
        Get results from OpenDSS simulation.
        
        Returns:
            Simulation results
        """
        results = {
            'success': True,
            'voltage_violations': [],
            'thermal_violations': [],
            'convergence': True,
            'power_flow': {}
        }
        
        # Check convergence
        if not self.dss.Solution.Converged:
            results['success'] = False
            results['convergence'] = False
            return results
        
        # Check voltage violations
        for bus in self.dss.ActiveCircuit.Buses:
            voltage = bus.VMagAngle[0]
            if voltage < 0.95 or voltage > 1.05:
                results['voltage_violations'].append({
                    'bus': bus.Name,
                    'voltage': voltage,
                    'limit': '0.95-1.05 p.u.'
                })
        
        # Check thermal violations
        for line in self.dss.ActiveCircuit.Lines:
            current = line.Currents[0]
            norm_amps = line.NormAmps
            if current > norm_amps:
                results['thermal_violations'].append({
                    'line': line.Name,
                    'current': current,
                    'limit': norm_amps
                })
        
        # Get power flow results
        results['power_flow'] = {
            'total_losses': self.dss.ActiveCircuit.Losses[0],
            'total_generation': self.dss.ActiveCircuit.TotalPower[0],
            'total_load': self.dss.ActiveCircuit.TotalPower[1]
        }
        
        return results
    
    def validate_time_series(
        self,
        scenario: Dict[str, Any],
        time_steps: List[float]
    ) -> Dict[str, Any]:
        """
        Validate scenario over multiple time steps.
        
        Args:
            scenario: Power grid scenario
            time_steps: List of time steps to validate
            
        Returns:
            Time series validation results
        """
        results = {
            'success': True,
            'time_steps': [],
            'voltage_violations': [],
            'thermal_violations': []
        }
        
        for t in time_steps:
            # Update scenario for time step
            updated_scenario = self._update_scenario_for_time_step(scenario, t)
            
            # Validate scenario
            step_results = self.validate_scenario(updated_scenario)
            
            # Record results
            results['time_steps'].append({
                'time': t,
                'success': step_results['success'],
                'convergence': step_results['convergence']
            })
            
            # Record violations
            for violation in step_results['voltage_violations']:
                violation['time'] = t
                results['voltage_violations'].append(violation)
            
            for violation in step_results['thermal_violations']:
                violation['time'] = t
                results['thermal_violations'].append(violation)
        
        return results
    
    def _update_scenario_for_time_step(
        self,
        scenario: Dict[str, Any],
        time_step: float
    ) -> Dict[str, Any]:
        """
        Update scenario for a specific time step.
        
        Args:
            scenario: Power grid scenario
            time_step: Time step to update for
            
        Returns:
            Updated scenario
        """
        updated_scenario = scenario.copy()
        
        # Update generator outputs
        for gen in updated_scenario['network']['simple_dispatchable_device']:
            if gen['device_type'] == 'producer':
                # For demonstration, we'll just scale the power output
                gen['initial_status']['p'] *= (1 + 0.1 * np.sin(time_step))
        
        # Update load demands
        for load in updated_scenario['network']['simple_dispatchable_device']:
            if load['device_type'] == 'consumer':
                # For demonstration, we'll just scale the power demand
                load['initial_status']['p'] *= (1 + 0.1 * np.cos(time_step))
        
        return updated_scenario

# Create a global instance of the OpenDSSService
opendss_service = OpenDSSService()