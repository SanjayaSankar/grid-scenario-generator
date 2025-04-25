#!/usr/bin/env python
"""
Script to train a Physics-Informed Neural Network (PINN) for grid scenario generation.

Usage:
    python train_pinn.py --data_dir data/processed --output_dir models
"""
import os
import argparse
import logging
import numpy as np
import json
from typing import Dict, List, Any, Optional, Tuple

# Add the project root to the Python path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.pinn_model import train_pinn_model
from app.core.data_loader import GridScenarioDataLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_training_data(data_dir: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load training data from the processed directory.
    
    Args:
        data_dir: Directory containing processed data
        
    Returns:
        Tuple of (features, targets)
    """
    data_path = os.path.join(data_dir, "training_data.npz")
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Training data not found at {data_path}")
    
    data = np.load(data_path)
    features = data['features']
    targets = data['targets']
    
    logger.info(f"Loaded training data with {len(features)} samples")
    logger.info(f"Feature shape: {features.shape}, Target shape: {targets.shape}")
    
    return features, targets


def load_grid_data(data_dir: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Load grid data (buses and lines) from the processed directory.
    
    Args:
        data_dir: Directory containing processed data
        
    Returns:
        Tuple of (bus_data, line_data)
    """
    # Find the first scenario file to extract bus and line data
    scenario_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
    
    if not scenario_files:
        raise FileNotFoundError(f"No scenario files found in {data_dir}")
    
    file_path = os.path.join(data_dir, scenario_files[0])
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Extract scenario data
    if 'scenario' in data:
        scenario = data['scenario']
    else:
        scenario = data
    
    network = scenario.get('network', {})
    bus_data = network.get('bus', [])
    line_data = network.get('ac_line', [])
    
    logger.info(f"Loaded grid data with {len(bus_data)} buses and {len(line_data)} lines")
    
    return bus_data, line_data


def train_model(
    features: np.ndarray,
    targets: np.ndarray,
    bus_data: List[Dict[str, Any]],
    line_data: List[Dict[str, Any]],
    output_dir: str,
    num_epochs: int = 1000,
    batch_size: int = 32,
    learning_rate: float = 1e-3,
    hidden_dim: int = 256,
    num_hidden_layers: int = 4,
    physics_weight: float = 0.5
) -> None:
    """
    Train a PINN model on the provided data.
    
    Args:
        features: Input features
        targets: Target values
        bus_data: Bus data for physics constraints
        line_data: Line data for physics constraints
        output_dir: Output directory for the trained model
        num_epochs: Number of training epochs
        batch_size: Training batch size
        learning_rate: Learning rate for optimization
        hidden_dim: Hidden dimension size
        num_hidden_layers: Number of hidden layers
        physics_weight: Weight for physics-based loss term
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Define output path
    output_path = os.path.join(output_dir, "pinn_model.pt")
    
    logger.info("Training PINN model...")
    
    # Train the model
    model = train_pinn_model(
        features=features,
        targets=targets,
        num_buses=len(bus_data),
        bus_data=bus_data,
        line_data=line_data,
        hidden_dim=hidden_dim,
        num_hidden_layers=num_hidden_layers,
        learning_rate=learning_rate,
        num_epochs=num_epochs,
        batch_size=batch_size,
        checkpoint_path=output_path,
        physics_weight=physics_weight
    )
    
    logger.info(f"Model training complete. Model saved to {output_path}")


def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description='Train PINN model for grid scenario generation')
    parser.add_argument('--data_dir', type=str, required=True, help='Directory with processed data')
    parser.add_argument('--output_dir', type=str, required=True, help='Output directory for trained model')
    parser.add_argument('--num_epochs', type=int, default=1000, help='Number of training epochs')
    parser.add_argument('--batch_size', type=int, default=32, help='Training batch size')
    parser.add_argument('--learning_rate', type=float, default=1e-3, help='Learning rate')
    parser.add_argument('--hidden_dim', type=int, default=256, help='Hidden dimension size')
    parser.add_argument('--num_hidden_layers', type=int, default=4, help='Number of hidden layers')
    parser.add_argument('--physics_weight', type=float, default=0.5, help='Weight for physics-based loss')
    
    args = parser.parse_args()
    
    # Load training data
    features, targets = load_training_data(args.data_dir)
    
    # Load grid data
    bus_data, line_data = load_grid_data(args.data_dir)
    
    # Train the model
    train_model(
        features=features,
        targets=targets,
        bus_data=bus_data,
        line_data=line_data,
        output_dir=args.output_dir,
        num_epochs=args.num_epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        hidden_dim=args.hidden_dim,
        num_hidden_layers=args.num_hidden_layers,
        physics_weight=args.physics_weight
    )
    
    logger.info("Training complete")


if __name__ == "__main__":
    main()