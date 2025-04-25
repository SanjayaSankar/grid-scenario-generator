"""
Physics-Informed Neural Network (PINN) model for grid scenario generation.
"""
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import os
import logging
from typing import Dict, List, Tuple, Any, Optional, Union

logger = logging.getLogger(__name__)


class PowerFlowLayer(nn.Module):
    """
    Custom layer that enforces power flow constraints.
    This layer ensures that generated scenarios adhere to physical laws.
    """
    
    def __init__(self, num_buses: int):
        """
        Initialize the power flow layer.
        
        Args:
            num_buses: Number of buses in the grid
        """
        super(PowerFlowLayer, self).__init__()
        self.num_buses = num_buses
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass of the power flow layer.
        
        Args:
            x: Input tensor with grid parameters
            
        Returns:
            Modified tensor respecting power flow constraints
        """
        # Extract voltages and angles
        voltages = x[:, :self.num_buses]
        angles = x[:, self.num_buses:2*self.num_buses]
        other_params = x[:, 2*self.num_buses:]
        
        # Apply voltage constraints (voltages should be positive)
        voltages = torch.clamp(voltages, min=0.95, max=1.05)
        
        # Apply angle constraints
        # For simplicity, we're using a reference bus with angle 0
        # and ensuring other angles are within a reasonable range
        batch_size = angles.shape[0]
        ref_angles = angles[:, 0].view(batch_size, 1)
        angles = angles - ref_angles  # Make first bus the reference
        angles = torch.clamp(angles, min=-0.5, max=0.5)  # Limit angle differences
        angles[:, 0] = 0.0  # Set reference bus angle to 0
        
        # Concatenate and return
        return torch.cat([voltages, angles, other_params], dim=1)


class LineFlowLayer(nn.Module):
    """
    Custom layer that calculates and constrains line flows.
    """
    
    def __init__(self, 
                 num_buses: int, 
                 bus_indices: Dict[str, int],
                 line_indices: Dict[str, int],
                 line_data: List[Dict[str, Any]]):
        """
        Initialize the line flow layer.
        
        Args:
            num_buses: Number of buses in the grid
            bus_indices: Mapping of bus IDs to indices
            line_indices: Mapping of line IDs to indices
            line_data: List of line data dictionaries
        """
        super(LineFlowLayer, self).__init__()
        self.num_buses = num_buses
        self.bus_indices = bus_indices
        self.line_indices = line_indices
        self.num_lines = len(line_data)
        
        # Create line parameters tensors
        line_from_indices = []
        line_to_indices = []
        line_reactances = []
        line_limits = []
        
        for line in line_data:
            from_bus = line['fr_bus']
            to_bus = line['to_bus']
            x = line['x']
            limit = line.get('mva_ub_nom', 999.0)
            
            # Get indices
            from_idx = bus_indices.get(from_bus, 0)
            to_idx = bus_indices.get(to_bus, 0)
            
            line_from_indices.append(from_idx)
            line_to_indices.append(to_idx)
            line_reactances.append(x)
            line_limits.append(limit)
        
        # Register buffers (these won't be trained)
        self.register_buffer('from_indices', torch.tensor(line_from_indices, dtype=torch.long))
        self.register_buffer('to_indices', torch.tensor(line_to_indices, dtype=torch.long))
        self.register_buffer('reactances', torch.tensor(line_reactances, dtype=torch.float))
        self.register_buffer('limits', torch.tensor(line_limits, dtype=torch.float))
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass of the line flow layer.
        
        Args:
            x: Input tensor with grid parameters
            
        Returns:
            Tuple of (modified tensor, line flows)
        """
        # Extract voltages and angles
        voltages = x[:, :self.num_buses]
        angles = x[:, self.num_buses:2*self.num_buses]
        other_params = x[:, 2*self.num_buses:]
        
        batch_size = x.shape[0]
        
        # Calculate line flows
        from_angles = torch.index_select(angles, 1, self.from_indices)
        to_angles = torch.index_select(angles, 1, self.to_indices)
        
        # Calculate angular differences
        angle_diffs = from_angles - to_angles
        
        # Calculate flows (P = angle_diff / reactance)
        flows = angle_diffs / self.reactances.unsqueeze(0)
        
        # Apply flow limits
        flow_ratios = flows / self.limits.unsqueeze(0)
        over_limit_mask = torch.abs(flow_ratios) > 1.0
        
        # If flows are over limit, adjust angles to respect limits
        if over_limit_mask.any():
            # Calculate required angle adjustments
            required_angles = torch.sign(angle_diffs) * self.reactances.unsqueeze(0) * self.limits.unsqueeze(0)
            
            # Apply adjustments where needed
            adjusted_diffs = torch.where(over_limit_mask, required_angles, angle_diffs)
            
            # Compute angle adjustments
            adjustments = adjusted_diffs - angle_diffs
            
            # Adjust angles
            # This is a simplification - a real implementation would distribute the adjustments more carefully
            from_adjustments = torch.zeros_like(angles)
            to_adjustments = torch.zeros_like(angles)
            
            for i in range(self.num_lines):
                from_idx = self.from_indices[i]
                to_idx = self.to_indices[i]
                
                from_adjustments[:, from_idx] += adjustments[:, i] / 2
                to_adjustments[:, to_idx] -= adjustments[:, i] / 2
            
            angles = angles + from_adjustments - to_adjustments
            
            # Recalculate flows with adjusted angles
            from_angles = torch.index_select(angles, 1, self.from_indices)
            to_angles = torch.index_select(angles, 1, self.to_indices)
            angle_diffs = from_angles - to_angles
            flows = angle_diffs / self.reactances.unsqueeze(0)
        
        # Concatenate and return
        return torch.cat([voltages, angles, other_params], dim=1), flows


class GridPINN(nn.Module):
    """
    Physics-Informed Neural Network for power grid scenario generation.
    """
    
    def __init__(
        self,
        input_dim: int = 10,
        hidden_dim: int = 64,
        output_dim: int = 8,
        num_layers: int = 3,
        bus_data: List[Dict[str, Any]] = None,
        line_data: List[Dict[str, Any]] = None
    ):
        """
        Initialize the PINN model.
        
        Args:
            input_dim: Dimension of input features
            hidden_dim: Dimension of hidden layers
            output_dim: Dimension of output features
            num_layers: Number of hidden layers
            bus_data: Bus data for physics constraints
            line_data: Line data for physics constraints
        """
        super(GridPINN, self).__init__()
        
        self.bus_data = bus_data or []
        self.line_data = line_data or []
        
        # Create neural network layers
        layers = []
        layers.append(nn.Linear(input_dim, hidden_dim))
        layers.append(nn.ReLU())
        
        for _ in range(num_layers - 1):
            layers.append(nn.Linear(hidden_dim, hidden_dim))
            layers.append(nn.ReLU())
        
        layers.append(nn.Linear(hidden_dim, output_dim))
        self.network = nn.Sequential(*layers)
        
        # Initialize weights
        self.apply(self._init_weights)
    
    def _init_weights(self, module):
        """Initialize weights using Xavier initialization."""
        if isinstance(module, nn.Linear):
            nn.init.xavier_uniform_(module.weight)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the network.
        
        Args:
            x: Input tensor
            
        Returns:
            Output tensor
        """
        return self.network(x)
    
    def physics_loss(
        self,
        predictions: torch.Tensor,
        bus_data: List[Dict[str, Any]],
        line_data: List[Dict[str, Any]]
    ) -> torch.Tensor:
        """
        Calculate physics-based loss terms.
        
        Args:
            predictions: Model predictions
            bus_data: Bus data for constraints
            line_data: Line data for constraints
            
        Returns:
            Physics loss tensor
        """
        # Power flow equations
        power_flow_loss = self._calculate_power_flow_loss(predictions, bus_data, line_data)
        
        # Voltage constraints
        voltage_loss = self._calculate_voltage_constraints(predictions, bus_data)
        
        # Line flow constraints
        line_flow_loss = self._calculate_line_flow_constraints(predictions, line_data)
        
        return power_flow_loss + voltage_loss + line_flow_loss
    
    def _calculate_power_flow_loss(
        self,
        predictions: torch.Tensor,
        bus_data: List[Dict[str, Any]],
        line_data: List[Dict[str, Any]]
    ) -> torch.Tensor:
        """Calculate power flow equation losses."""
        # Implement power flow equations here
        # This is a simplified version
        loss = torch.tensor(0.0, device=predictions.device)
        return loss
    
    def _calculate_voltage_constraints(
        self,
        predictions: torch.Tensor,
        bus_data: List[Dict[str, Any]]
    ) -> torch.Tensor:
        """Calculate voltage constraint losses."""
        # Implement voltage constraints here
        loss = torch.tensor(0.0, device=predictions.device)
        return loss
    
    def _calculate_line_flow_constraints(
        self,
        predictions: torch.Tensor,
        line_data: List[Dict[str, Any]]
    ) -> torch.Tensor:
        """Calculate line flow constraint losses."""
        # Implement line flow constraints here
        loss = torch.tensor(0.0, device=predictions.device)
        return loss
    
    @classmethod
    def load(cls, path: str, bus_data: List[Dict[str, Any]], line_data: List[Dict[str, Any]]) -> 'GridPINN':
        """
        Load a trained model from disk.
        
        Args:
            path: Path to saved model
            bus_data: Bus data for physics constraints
            line_data: Line data for physics constraints
            
        Returns:
            Loaded model
        """
        try:
            # Load state dict with weights_only=True for security
            checkpoint = torch.load(path, weights_only=True)
            
            # Extract model parameters from the checkpoint
            input_dim = checkpoint.get('input_dim', 10)
            hidden_dim = checkpoint.get('hidden_dim', 64)
            output_dim = checkpoint.get('output_dim', 8)
            num_layers = checkpoint.get('num_layers', 3)
            
            # Create model instance with the same architecture as saved model
            model = cls(
                input_dim=input_dim,
                hidden_dim=hidden_dim,
                output_dim=output_dim,
                num_layers=num_layers,
                bus_data=bus_data,
                line_data=line_data
            )
            
            # Get the state dict
            state_dict = checkpoint['model_state_dict']
            
            # Filter out unexpected keys (like line_flow_layer)
            model_state_dict = model.state_dict()
            filtered_state_dict = {k: v for k, v in state_dict.items() 
                                 if k in model_state_dict and 
                                 model_state_dict[k].shape == v.shape}
            
            # Load the filtered state dict
            model.load_state_dict(filtered_state_dict, strict=False)
            logger.info("Model loaded successfully with filtered state dict")
            
            return model
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            # Return a new untrained model as fallback
            return cls(bus_data=bus_data, line_data=line_data)
    
    def save(self, path: str) -> None:
        """
        Save the model to disk.
        
        Args:
            path: Path to save model
        """
        # Create a checkpoint dictionary with model parameters and state dict
        checkpoint = {
            'input_dim': self.network[0].in_features,
            'hidden_dim': self.network[0].out_features,
            'output_dim': self.network[-1].out_features,
            'num_layers': len(self.network) // 2,  # Each layer has a Linear and ReLU
            'model_state_dict': self.state_dict()
        }
        
        torch.save(checkpoint, path)


def train_pinn_model(
    features: np.ndarray,
    targets: np.ndarray,
    num_buses: int,
    bus_data: List[Dict[str, Any]],
    line_data: List[Dict[str, Any]],
    checkpoint_path: str,
    num_epochs: int = 100,
    batch_size: int = 32,
    learning_rate: float = 0.001,
    physics_weight: float = 0.1
) -> GridPINN:
    """
    Train the PINN model.
    
    Args:
        features: Input features
        targets: Target values
        num_buses: Number of buses in the grid
        bus_data: Bus data for physics constraints
        line_data: Line data for physics constraints
        checkpoint_path: Path to save model checkpoints
        num_epochs: Number of training epochs
        batch_size: Batch size for training
        learning_rate: Learning rate
        physics_weight: Weight for physics loss term
        
    Returns:
        Trained model
    """
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    # Convert data to tensors
    features = torch.FloatTensor(features).to(device)
    targets = torch.FloatTensor(targets).to(device)
    
    # Create model
    model = GridPINN(
        input_dim=features.shape[1],
        output_dim=targets.shape[1],
        bus_data=bus_data,
        line_data=line_data
    ).to(device)
    
    # Create optimizer and loss function
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    mse_loss = nn.MSELoss()
    
    # Training loop
    for epoch in range(num_epochs):
        model.train()
        total_loss = 0
        
        for i in range(0, len(features), batch_size):
            batch_features = features[i:i+batch_size]
            batch_targets = targets[i:i+batch_size]
            
            # Forward pass
            predictions = model(batch_features)
            
            # Calculate losses
            data_loss = mse_loss(predictions, batch_targets)
            physics_loss = model.physics_loss(predictions, bus_data, line_data)
            
            # Combined loss
            loss = data_loss + physics_weight * physics_loss
            
            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        # Log progress
        avg_loss = total_loss / (len(features) // batch_size)
        logger.info(f"Epoch {epoch+1}/{num_epochs}, Loss: {avg_loss:.4f}")
        
        # Save checkpoint
        if (epoch + 1) % 10 == 0:
            model.save(checkpoint_path)
    
    return model


def generate_scenario(
    model: GridPINN,
    prompt: str,
    context: List[Dict[str, Any]] = None,
    parameters: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Generate a power grid scenario using the PINN model.
    
    Args:
        model: Trained PINN model
        prompt: Generation prompt
        context: Optional RAG context
        parameters: Generation parameters
        
    Returns:
        Generated scenario
    """
    # Convert prompt and context to input features
    input_features = _process_input(prompt, context, parameters)
    
    # Generate scenario using model
    with torch.no_grad():
        model.eval()
        predictions = model(input_features)
    
    # Convert predictions to scenario format
    scenario = _convert_predictions_to_scenario(predictions, parameters)
    
    return scenario


def _process_input(
    prompt: str,
    context: List[Dict[str, Any]] = None,
    parameters: Dict[str, Any] = None
) -> torch.Tensor:
    """Process input data into model features."""
    # Implement feature processing here
    # This is a placeholder
    return torch.randn(1, 10)  # Example random input


def _convert_predictions_to_scenario(
    predictions: torch.Tensor,
    parameters: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Convert model predictions to scenario format."""
    # Implement conversion here
    # This is a placeholder
    return {
        "network": {
            "bus": [],
            "ac_line": [],
            "simple_dispatchable_device": []
        }
    }