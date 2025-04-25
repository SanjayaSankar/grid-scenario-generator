#!/usr/bin/env python
"""
Script to evaluate generated grid scenarios.

Usage:
    python evaluate_scenarios.py --scenarios_dir data/processed/generated --output_file results/evaluation_results.json
"""
import os
import argparse
import logging
import json
from typing import Dict, List, Any, Optional
from concurrent.futures import ProcessPoolExecutor

# Add the project root to the Python path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.opendss_service import OpenDSSService
from app.core.utils import validate_scenario_physics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def evaluate_scenario(file_path: str) -> Dict[str, Any]:
    """
    Evaluate a single scenario.
    
    Args:
        file_path: Path to scenario file
        
    Returns:
        Evaluation results
    """
    logger.info(f"Evaluating scenario: {file_path}")
    
    try:
        # Load scenario
        with open(file_path, 'r') as f:
            scenario_data = json.load(f)
        
        # Extract scenario ID
        scenario_id = os.path.basename(file_path).replace('.json', '')
        
        # Perform physics validation
        physics_results = validate_scenario_physics(scenario_data)
        
        # Create OpenDSS service
        opendss_service = OpenDSSService()
        
        # Perform OpenDSS validation
        opendss_results = opendss_service.validate_scenario(scenario_data)
        
        # Combine results
        evaluation_results = {
            'scenario_id': scenario_id,
            'file_path': file_path,
            'physics_validation': physics_results,
            'opendss_validation': opendss_results,
            'overall_valid': physics_results.get('is_valid', False) and opendss_results.get('is_valid', False)
        }
        
        logger.info(f"Evaluation complete for {scenario_id}: {'VALID' if evaluation_results['overall_valid'] else 'INVALID'}")
        
        return evaluation_results
    
    except Exception as e:
        logger.error(f"Error evaluating scenario {file_path}: {str(e)}")
        return {
            'scenario_id': os.path.basename(file_path).replace('.json', ''),
            'file_path': file_path,
            'error': str(e),
            'overall_valid': False
        }


def evaluate_scenarios(scenarios_dir: str, output_file: str, max_workers: int = 4) -> None:
    """
    Evaluate all scenarios in a directory.
    
    Args:
        scenarios_dir: Directory containing scenario files
        output_file: Output file for evaluation results
        max_workers: Maximum number of worker processes
    """
    # Find all scenario files
    scenario_files = [
        os.path.join(scenarios_dir, f) 
        for f in os.listdir(scenarios_dir) 
        if f.endswith('.json')
    ]
    
    if not scenario_files:
        logger.warning(f"No scenario files found in {scenarios_dir}")
        return
    
    logger.info(f"Evaluating {len(scenario_files)} scenarios using {max_workers} workers")
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Evaluate scenarios in parallel
    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(evaluate_scenario, scenario_files))
    
    # Calculate summary statistics
    total_scenarios = len(results)
    valid_scenarios = sum(1 for r in results if r.get('overall_valid', False))
    invalid_scenarios = total_scenarios - valid_scenarios
    
    # Create summary
    summary = {
        'total_scenarios': total_scenarios,
        'valid_scenarios': valid_scenarios,
        'invalid_scenarios': invalid_scenarios,
        'valid_percentage': (valid_scenarios / total_scenarios) * 100 if total_scenarios > 0 else 0,
        'results': results
    }
    
    # Save results
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Evaluation complete: {valid_scenarios}/{total_scenarios} valid scenarios ({summary['valid_percentage']:.2f}%)")
    logger.info(f"Results saved to {output_file}")


def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description='Evaluate generated grid scenarios')
    parser.add_argument('--scenarios_dir', type=str, required=True, help='Directory containing scenario files')
    parser.add_argument('--output_file', type=str, required=True, help='Output file for evaluation results')
    parser.add_argument('--max_workers', type=int, default=4, help='Maximum number of worker processes')
    
    args = parser.parse_args()
    
    # Evaluate scenarios
    evaluate_scenarios(
        scenarios_dir=args.scenarios_dir,
        output_file=args.output_file,
        max_workers=args.max_workers
    )


if __name__ == "__main__":
    main()