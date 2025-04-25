"""
Data processing utilities for grid scenario data.
"""
import os
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional
from app.core.data_loader import GridScenarioDataLoader
from app.config import settings

logger = logging.getLogger(__name__)


class GridScenarioProcessor:
    """
    Processor for grid scenario data.
    Extracts features and prepares data for the PINN model.
    """
    
    def __init__(self, data_loader: GridScenarioDataLoader):
        """
        Initialize the processor.
        
        Args:
            data_loader: Data loader instance
        """
        self.data_loader = data_loader
        self.output_dir = settings.DATA_PROCESSED_DIR
        os.makedirs(self.output_dir, exist_ok=True)
    
    def extract_network_features(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract network features from a scenario.
        
        Args:
            scenario: Scenario data
            
        Returns:
            Dictionary of extracted features
        """
        network = scenario.get('network', {})
        
        # Extract bus information
        buses = network.get('bus', [])
        num_buses = len(buses)
        
        # Extract line information
        ac_lines = network.get('ac_line', [])
        num_ac_lines = len(ac_lines)
        
        # Extract transformer information
        transformers = network.get('two_winding_transformer', [])
        num_transformers = len(transformers)
        
        # Extract device information
        devices = network.get('simple_dispatchable_device', [])
        num_devices = len(devices)
        
        # Count device types
        device_types = {}
        for device in devices:
            device_type = device.get('device_type', 'unknown')
            device_types[device_type] = device_types.get(device_type, 0) + 1
        
        # Extract reserve information
        active_reserves = network.get('active_zonal_reserve', [])
        reactive_reserves = network.get('reactive_zonal_reserve', [])
        
        return {
            'num_buses': num_buses,
            'num_ac_lines': num_ac_lines,
            'num_transformers': num_transformers,
            'num_devices': num_devices,
            'device_types': device_types,
            'has_active_reserves': len(active_reserves) > 0,
            'has_reactive_reserves': len(reactive_reserves) > 0,
        }
    
    def extract_time_series_features(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract time series features from a scenario.
        
        Args:
            scenario: Scenario data
            
        Returns:
            Dictionary of extracted features
        """
        time_series = scenario.get('time_series_input', {})
        
        # Get general time series info
        general = time_series.get('general', {})
        num_intervals = general.get('time_periods', 0)
        interval_durations = general.get('interval_duration', [])
        
        # Extract device time series
        devices = time_series.get('simple_dispatchable_device', [])
        
        return {
            'num_intervals': num_intervals,
            'interval_durations': interval_durations,
            'total_duration': sum(interval_durations) if interval_durations else 0,
            'num_device_time_series': len(devices),
        }
    
    def extract_reliability_features(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract reliability features from a scenario.
        
        Args:
            scenario: Scenario data
            
        Returns:
            Dictionary of extracted features
        """
        reliability = scenario.get('reliability', {})
        
        # Extract contingency information
        contingencies = reliability.get('contingency', [])
        num_contingencies = len(contingencies)
        
        # Classify contingencies
        contingency_types = {}
        for contingency in contingencies:
            components = contingency.get('components', [])
            for component in components:
                component_type = component.split('_')[0]  # Assuming component IDs follow pattern type_id
                contingency_types[component_type] = contingency_types.get(component_type, 0) + 1
        
        return {
            'num_contingencies': num_contingencies,
            'contingency_types': contingency_types,
        }
    
    def extract_features(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract all features from a scenario.
        
        Args:
            scenario: Scenario data
            
        Returns:
            Dictionary of extracted features
        """
        network_features = self.extract_network_features(scenario)
        time_series_features = self.extract_time_series_features(scenario)
        reliability_features = self.extract_reliability_features(scenario)
        
        return {
            **network_features,
            **time_series_features,
            **reliability_features,
        }
    
    def normalize_features(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize features to suitable ranges for the PINN model.
        
        Args:
            features: Extracted features
            
        Returns:
            Dictionary of normalized features
        """
        # This is a simplified normalization - in a real application this would
        # use statistics from the training dataset
        
        normalized = {}
        
        # Normalize counts to 0-1 range (assuming typical max values)
        max_values = {
            'num_buses': 1000,
            'num_ac_lines': 2000,
            'num_transformers': 500,
            'num_devices': 500,
            'num_intervals': 100,
            'total_duration': 48,  # Assuming 48 hours max
            'num_contingencies': 100,
        }
        
        for key, max_val in max_values.items():
            if key in features:
                normalized[f'{key}_normalized'] = min(features[key] / max_val, 1.0)
        
        # Pass through other features
        for key, value in features.items():
            if key not in max_values:
                normalized[key] = value
        
        return normalized
    
    def process_scenario(
        self, 
        scenario: Dict[str, Any], 
        solution: Optional[Dict[str, Any]] = None,
        log: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a scenario to extract and normalize features.
        
        Args:
            scenario: Scenario data
            solution: Optional solution data
            log: Optional log data
            
        Returns:
            Dictionary with processed data
        """
        # Extract features
        features = self.extract_features(scenario)
        
        # Normalize features
        normalized_features = self.normalize_features(features)
        
        # Create processed data
        processed = {
            'features': features,
            'normalized_features': normalized_features,
            'scenario': scenario,
        }
        
        # Add solution and log if available
        if solution is not None:
            processed['solution'] = solution
        
        if log is not None:
            # Extract key metrics from log if needed
            # For simplicity, we're just storing the raw log
            processed['log'] = log
        
        return processed
    
    def process_all_scenarios(self, output_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Process all scenarios and save results.
        
        Args:
            output_dir: Optional output directory (uses default if None)
            
        Returns:
            List of processed scenarios
        """
        if output_dir is None:
            output_dir = self.output_dir
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Load all scenarios
        all_data = self.data_loader.load_all_scenarios()
        
        processed_scenarios = []
        for i, (scenario, solution, log) in enumerate(all_data):
            try:
                # Process the scenario
                processed = self.process_scenario(scenario, solution, log)
                processed_scenarios.append(processed)
                
                # Save processed data
                scenario_id = f"scenario_{i:05d}"
                output_path = os.path.join(output_dir, f"{scenario_id}.json")
                
                with open(output_path, 'w') as f:
                    json.dump(processed, f, indent=2)
                
                logger.info(f"Processed and saved scenario {i+1}/{len(all_data)}")
            except Exception as e:
                logger.error(f"Error processing scenario {i+1}: {str(e)}")
        
        return processed_scenarios


def process_scenario_file(file_path: str) -> Dict[str, Any]:
    """
    Process a single scenario file.
    
    Args:
        file_path: Path to the scenario file
        
    Returns:
        Processed data
    """
    # Get the directory containing the file
    file_dir = os.path.dirname(file_path)
    
    # Create a data loader for this directory
    loader = GridScenarioDataLoader(file_dir)
    
    # Load the scenario, solution, and log
    scenario, solution, log = loader.load_scenario_with_solution(file_path)
    
    # Create a processor and process the scenario
    processor = GridScenarioProcessor(loader)
    processed = processor.process_scenario(scenario, solution, log)
    
    # Generate output path
    file_name = os.path.basename(file_path)
    output_path = os.path.join(settings.DATA_PROCESSED_DIR, f"processed_{file_name}")
    
    # Save processed data
    with open(output_path, 'w') as f:
        json.dump(processed, f, indent=2)
    
    logger.info(f"Processed and saved scenario to {output_path}")
    
    return processed


def create_training_dataset(processed_dir: str, output_file: str = "training_data.npz"):
    """
    Create a consolidated training dataset from processed scenarios.
    
    Args:
        processed_dir: Directory containing processed scenario files
        output_file: Output file for the consolidated dataset
    """
    # Get all processed scenario files
    scenario_files = [f for f in os.listdir(processed_dir) if f.endswith('.json')]
    
    features_list = []
    targets_list = []
    
    for scenario_file in scenario_files:
        file_path = os.path.join(processed_dir, scenario_file)
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Extract features
        normalized_features = data.get('normalized_features', {})
        features = []
        
        # Convert features to a fixed-length vector
        # This is a simplified version - in reality, you'd need to ensure consistent feature ordering
        for key in sorted(normalized_features.keys()):
            if isinstance(normalized_features[key], (int, float)):
                features.append(normalized_features[key])
        
        # Extract targets from solution if available
        targets = []
        solution = data.get('solution', {})
        
        if solution:
            # Extract time series output values as targets
            # This is a simplified version - you'd need to decide what aspects to predict
            time_series = solution.get('time_series_output', {})
            
            # For example, extract power values from simple dispatchable devices
            devices = time_series.get('simple_dispatchable_device', [])
            for device in devices:
                if 'p_on' in device:
                    # Take the first few values as targets
                    targets.extend(device['p_on'][:5])
        
        if features and targets:
            features_list.append(features)
            targets_list.append(targets)
    
    # Convert to numpy arrays
    if features_list and targets_list:
        # Ensure all feature and target vectors have the same length
        min_feature_len = min(len(f) for f in features_list)
        min_target_len = min(len(t) for t in targets_list)
        
        features_array = np.array([f[:min_feature_len] for f in features_list])
        targets_array = np.array([t[:min_target_len] for t in targets_list])
        
        # Save dataset
        np.savez(
            output_file,
            features=features_array,
            targets=targets_array
        )
        
        logger.info(f"Created training dataset with {len(features_array)} samples")
        logger.info(f"Feature shape: {features_array.shape}, Target shape: {targets_array.shape}")
        
        return features_array, targets_array
    else:
        logger.warning("No valid data found for training dataset")
        return None, None