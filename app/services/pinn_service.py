"""
Service for PINN model training and inference.
"""
import os
import json
import torch
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import logging
from app.models.pinn_model import GridPINN, train_pinn_model, generate_scenario
from app.config import settings
from app.core.utils import generate_id, save_json

logger = logging.getLogger(__name__)


class PINNService:
    """Service for interacting with the PINN model."""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the PINN service.
        
        Args:
            model_path: Optional path to a trained model
        """
        self.model_path = model_path or settings.PINN_MODEL_PATH
        self.model = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # Try to load the model if it exists
        if os.path.exists(self.model_path):
            try:
                self.load_model()
            except Exception as e:
                logger.error(f"Error loading model: {str(e)}")
    
    def load_model(self) -> None:
        """Load the PINN model from disk."""
        # For a real implementation, we would load the bus and line data as well
        bus_data = []  # This would come from a database or file
        line_data = []  # This would come from a database or file
        
        self.model = GridPINN.load(self.model_path, bus_data, line_data).to(self.device)
        logger.info(f"Loaded PINN model from {self.model_path}")
    
    def train_model(
        self,
        features: np.ndarray,
        targets: np.ndarray,
        num_buses: int,
        bus_data: List[Dict[str, Any]],
        line_data: List[Dict[str, Any]],
        **kwargs
    ) -> None:
        """
        Train the PINN model.
        
        Args:
            features: Input features
            targets: Target values
            num_buses: Number of buses in the grid
            bus_data: Bus data for physics constraints
            line_data: Line data for physics constraints
            **kwargs: Additional training parameters
        """
        logger.info("Training PINN model...")
        
        # Create model directory if it doesn't exist
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        # Train the model
        self.model = train_pinn_model(
            features=features,
            targets=targets,
            num_buses=num_buses,
            bus_data=bus_data,
            line_data=line_data,
            checkpoint_path=self.model_path,
            **kwargs
        )
        
        logger.info(f"Trained PINN model saved to {self.model_path}")
    
    def generate_scenario(
        self,
        prompt: str,
        context: Optional[List[Dict[str, Any]]] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a grid scenario using the PINN model and prompt engineering.
        
        Args:
            prompt: Generation prompt
            context: Optional RAG context (similar scenarios)
            parameters: Generation parameters
            
        Returns:
            Generated scenario
        """
        # Ensure model is loaded
        if self.model is None:
            raise RuntimeError("Model not loaded. Please train or load a model first.")
        
        logger.info("Generating scenario with PINN model...")
        
        # For demonstration purposes, we'll create a simple scenario
        # In a real implementation, this would use the actual PINN model
        # and incorporate the prompt and context
        
        # Generate a scenario ID
        scenario_id = generate_id()
        
        # Extract parameters or use defaults
        parameters = parameters or {}
        num_buses = parameters.get('num_buses', 3)
        num_generators = parameters.get('num_generators', 2)
        num_loads = parameters.get('num_loads', 1)
        
        # Generate a basic scenario structure
        scenario = {
            "id": scenario_id,
            "network": {
                "general": {
                    "base_norm_mva": 100
                },
                "bus": [],
                "ac_line": [],
                "simple_dispatchable_device": [],
                "two_winding_transformer": [],
                "shunt": [],
                "active_zonal_reserve": [],
                "reactive_zonal_reserve": []
            },
            "reliability": {
                "contingency": []
            },
            "time_series_input": {
                "general": {
                    "time_periods": 18,
                    "interval_duration": [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 
                                         0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 1, 1]
                },
                "simple_dispatchable_device": []
            }
        }
        
        # Add buses
        for i in range(num_buses):
            bus = {
                "uid": f"bus_{i}",
                "base_nom_volt": 230,
                "vm_lb": 0.95,
                "vm_ub": 1.05,
                "initial_status": {
                    "vm": 1.0,
                    "va": 0.0
                },
                "active_reserve_uids": ["prz_0"],
                "reactive_reserve_uids": ["qrz_0"]
            }
            scenario["network"]["bus"].append(bus)
        
        # Add AC lines to connect buses
        for i in range(num_buses - 1):
            line = {
                "uid": f"acl_{i}",
                "fr_bus": f"bus_{i}",
                "to_bus": f"bus_{i+1}",
                "r": 0.003,
                "x": 0.026,
                "b": 0.0275,
                "mva_ub_nom": 10,
                "mva_ub_em": 12,
                "additional_shunt": 0,
                "connection_cost": 1000,
                "disconnection_cost": 1000,
                "initial_status": {
                    "on_status": 1
                }
            }
            scenario["network"]["ac_line"].append(line)
        
        # Add a transformer if there are at least 2 buses
        if num_buses >= 2:
            transformer = {
                "uid": "xfr_0",
                "fr_bus": "bus_0",
                "to_bus": "bus_1",
                "r": 0.002,
                "x": 0.084,
                "b": 0,
                "mva_ub_nom": 12,
                "mva_ub_em": 12,
                "additional_shunt": 0,
                "connection_cost": 1000,
                "disconnection_cost": 1000,
                "ta_lb": 0,
                "ta_ub": 0,
                "tm_lb": 1.00125,
                "tm_ub": 1.00125,
                "initial_status": {
                    "on_status": 1,
                    "ta": 0,
                    "tm": 1.00125
                }
            }
            scenario["network"]["two_winding_transformer"].append(transformer)
        
        # Add generators
        for i in range(num_generators):
            bus_idx = i % num_buses  # Distribute generators across buses
            generator = {
                "uid": f"sd_{i}",
                "bus": f"bus_{bus_idx}",
                "device_type": "producer",
                "p_ramp_up_ub": 0.5,
                "p_ramp_down_ub": 0.5,
                "p_startup_ramp_ub": 0.5,
                "p_shutdown_ramp_ub": 0.5,
                "p_syn_res_ub": 0.05,
                "p_nsyn_res_ub": 0,
                "p_ramp_res_up_online_ub": 0.041666666666666664,
                "p_ramp_res_down_online_ub": 0.041666666666666664,
                "p_ramp_res_up_offline_ub": 0,
                "p_ramp_res_down_offline_ub": 0,
                "p_reg_res_up_ub": 0.016666666666666666,
                "p_reg_res_down_ub": 0.016666666666666666,
                "in_service_time_lb": 0,
                "down_time_lb": 0,
                "q_bound_cap": 0,
                "q_linear_cap": 0,
                "startup_cost": 0,
                "shutdown_cost": 0,
                "on_cost": 0,
                "initial_status": {
                    "on_status": 1,
                    "p": 0.2 + (i * 0.05),  # Vary power slightly
                    "q": 0,
                    "accu_up_time": 24,
                    "accu_down_time": 0
                },
                "energy_req_lb": [],
                "energy_req_ub": [],
                "startup_states": [[0, 12], [0, 48]],
                "startups_ub": [[0, 12, 1], [8, 48, 1]]
            }
            scenario["network"]["simple_dispatchable_device"].append(generator)
            
            # Add time series data for generator
            time_series_data = {
                "uid": f"sd_{i}",
                "on_status_lb": [0] * 18,
                "on_status_ub": [1] * 18,
                "p_lb": [0.05] * 18,
                "p_ub": [0.5] * 18,
                "q_lb": [-0.25] * 18,
                "q_ub": [0.275] * 18,
                "cost": [[[10, 0.25], [20, 0.15], [30, 0.1], [4000, 0.2]]] * 18,
                "p_syn_res_cost": [0] * 18,
                "p_nsyn_res_cost": [0] * 18,
                "p_ramp_res_up_online_cost": [0] * 18,
                "p_ramp_res_down_online_cost": [0] * 18,
                "p_ramp_res_up_offline_cost": [0] * 18,
                "p_ramp_res_down_offline_cost": [0] * 18,
                "p_reg_res_up_cost": [0] * 18,
                "p_reg_res_down_cost": [0] * 18,
                "q_res_up_cost": [0] * 18,
                "q_res_down_cost": [0] * 18
            }
            scenario["time_series_input"]["simple_dispatchable_device"].append(time_series_data)
        
        # Add loads
        for i in range(num_loads):
            load_idx = (i + num_generators) % num_buses  # Distribute loads across buses
            load = {
                "uid": f"sd_{i + num_generators}",
                "bus": f"bus_{load_idx}",
                "device_type": "consumer",
                "p_ramp_up_ub": 0.97,
                "p_ramp_down_ub": 0.97,
                "p_startup_ramp_ub": 0.97,
                "p_shutdown_ramp_ub": 0.97,
                "p_syn_res_ub": 0,
                "p_nsyn_res_ub": 0,
                "p_ramp_res_up_online_ub": 0,
                "p_ramp_res_down_online_ub": 0,
                "p_ramp_res_up_offline_ub": 0,
                "p_ramp_res_down_offline_ub": 0,
                "p_reg_res_up_ub": 0,
                "p_reg_res_down_ub": 0,
                "in_service_time_lb": 0,
                "down_time_lb": 0,
                "q_bound_cap": 0,
                "q_linear_cap": 0,
                "startup_cost": 0,
                "shutdown_cost": 0,
                "on_cost": 0,
                "initial_status": {
                    "on_status": 1,
                    "p": 0.275,
                    "q": 0.009,
                    "accu_up_time": 24,
                    "accu_down_time": 0
                },
                "energy_req_lb": [[0, 12, 0], [6, 48, 0]],
                "energy_req_ub": [[0, 12, 9999], [0, 48, 9999]],
                "startup_states": [[0, 12], [0, 48]],
                "startups_ub": [[0, 12, 1], [0, 48, 3]]
            }
            scenario["network"]["simple_dispatchable_device"].append(load)
            
            # Add time series data for load with realistic profile
            # Create a typical daily load curve
            p_ub_values = []
            for t in range(18):
                if t < 4:  # Early morning (low demand)
                    p_val = 0.22 + (t * 0.01)
                elif t < 8:  # Morning ramp up
                    p_val = 0.25 + ((t-4) * 0.02)
                elif t < 12:  # Midday peak
                    p_val = 0.33 - ((t-8) * 0.005)
                elif t < 16:  # Afternoon
                    p_val = 0.32 + ((t-12) * 0.015)
                else:  # Evening peak
                    p_val = 0.37 - ((t-16) * 0.03)
                p_ub_values.append(p_val)
            
            time_series_data = {
                "uid": f"sd_{i + num_generators}",
                "on_status_lb": [0] * 18,
                "on_status_ub": [1] * 18,
                "p_lb": [0.0281, 0.0284, 0.0285, 0.0287, 0.0274, 0.0278, 0.0276, 0.0274, 
                         0.0273, 0.027, 0.0268, 0.0264, 0.0219, 0.0213, 0.0229, 0.0221, 0.0206, 0.02],
                "p_ub": p_ub_values,
                "q_lb": [0.014] * 18,
                "q_ub": [0.014] * 18,
                "cost": [[[1000, 0.05], [2500, 0.05], [10000, 0.05], [50000, 0.05], [100000, 0.15]]] * 18,
                "p_syn_res_cost": [0] * 18,
                "p_nsyn_res_cost": [0] * 18,
                "p_ramp_res_up_online_cost": [0] * 18,
                "p_ramp_res_down_online_cost": [0] * 18,
                "p_ramp_res_up_offline_cost": [0] * 18,
                "p_ramp_res_down_offline_cost": [0] * 18,
                "p_reg_res_up_cost": [0] * 18,
                "p_reg_res_down_cost": [0] * 18,
                "q_res_up_cost": [0] * 18,
                "q_res_down_cost": [0] * 18
            }
            scenario["time_series_input"]["simple_dispatchable_device"].append(time_series_data)
        
        # Add reserve zones
        active_reserve = {
            "uid": "prz_0",
            "SYN": 0.05,
            "NSYN": 0.05,
            "REG_UP": 0.07,
            "REG_DOWN": 0.07,
            "SYN_vio_cost": 100,
            "NSYN_vio_cost": 100,
            "REG_UP_vio_cost": 100,
            "REG_DOWN_vio_cost": 100,
            "RAMPING_RESERVE_UP_vio_cost": 100,
            "RAMPING_RESERVE_DOWN_vio_cost": 100
        }
        scenario["network"]["active_zonal_reserve"].append(active_reserve)
        
        reactive_reserve = {
            "uid": "qrz_0",
            "REACT_UP_vio_cost": 100,
            "REACT_DOWN_vio_cost": 100
        }
        scenario["network"]["reactive_zonal_reserve"].append(reactive_reserve)
        
        # Add time series for reserves
        active_reserve_ts = {
            "uid": "prz_0",
            "RAMPING_RESERVE_UP": [0.01] * 18,
            "RAMPING_RESERVE_DOWN": [0.01] * 18
        }
        scenario["time_series_input"]["active_zonal_reserve"] = [active_reserve_ts]
        
        reactive_reserve_ts = {
            "uid": "qrz_0",
            "REACT_UP": [0.01] * 18,
            "REACT_DOWN": [0.01] * 18
        }
        scenario["time_series_input"]["reactive_zonal_reserve"] = [reactive_reserve_ts]
        
        # Add contingencies for reliability testing
        if num_buses >= 2:
            contingency1 = {
                "uid": "ctg_0",
                "components": ["xfr_0"]
            }
            contingency2 = {
                "uid": "ctg_1",
                "components": ["acl_0"]
            }
            scenario["reliability"]["contingency"] = [contingency1, contingency2]
        
        # Add violation costs
        scenario["network"]["violation_cost"] = {
            "p_bus_vio_cost": 100000.0,
            "q_bus_vio_cost": 100000.0,
            "s_vio_cost": 100000.0,
            "e_vio_cost": 100000.0
        }
        
        # Add shunts for voltage support
        shunt1 = {
            "uid": "sh_0",
            "bus": "bus_0",
            "gs": 0,
            "bs": -0.05,
            "step_lb": 0,
            "step_ub": 1,
            "initial_status": {
                "step": 1
            }
        }
        shunt2 = {
            "uid": "sh_1",
            "bus": "bus_0",
            "gs": 0,
            "bs": 0.059,
            "step_lb": 0,
            "step_ub": 1,
            "initial_status": {
                "step": 1
            }
        }
        scenario["network"]["shunt"] = [shunt1, shunt2]
        
        # Save scenario to file
        output_dir = os.path.join(settings.DATA_PROCESSED_DIR, "generated")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{scenario_id}.json")
        save_json(scenario, output_path)
        
        logger.info(f"Generated scenario saved to {output_path}")
        
        return scenario
    
    def validate_scenario_physics(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that a scenario respects physical laws.
        
        Args:
            scenario: Grid scenario data
            
        Returns:
            Validation results
        """
        from app.core.utils import validate_scenario_physics
        return validate_scenario_physics(scenario)

# Create a global instance of the PINNService
pinn_service = PINNService()