#!/usr/bin/env python
"""
Script to process the raw grid scenario dataset.

Usage:
    python process_dataset.py --input_dir data/raw --output_dir data/processed
"""
import os
import argparse
import logging
from typing import Optional

# Add the project root to the Python path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.data_loader import GridScenarioDataLoader
from app.core.data_processor import GridScenarioProcessor, create_training_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_dataset(input_dir: str, output_dir: str, max_scenarios: Optional[int] = None) -> None:
    """
    Process the dataset from input directory to output directory.
    
    Args:
        input_dir: Input directory with raw data
        output_dir: Output directory for processed data
        max_scenarios: Maximum number of scenarios to process (None for all)
    """
    logger.info(f"Processing dataset from {input_dir} to {output_dir}")
    
    # Create data loader
    data_loader = GridScenarioDataLoader(input_dir)
    
    # Create data processor
    processor = GridScenarioProcessor(data_loader)
    
    # Process all scenarios
    processed_scenarios = processor.process_all_scenarios(output_dir=output_dir)
    
    logger.info(f"Processed {len(processed_scenarios)} scenarios")
    
    # Create training dataset
    features, targets = create_training_dataset(
        processed_dir=output_dir,
        output_file=os.path.join(output_dir, "training_data.npz")
    )
    
    if features is not None and targets is not None:
        logger.info(f"Created training dataset with {len(features)} samples")
        logger.info(f"Feature shape: {features.shape}, Target shape: {targets.shape}")


def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description='Process grid scenario dataset')
    parser.add_argument('--input_dir', type=str, required=True, help='Input directory with raw data')
    parser.add_argument('--output_dir', type=str, required=True, help='Output directory for processed data')
    parser.add_argument('--max_scenarios', type=int, default=None, help='Maximum number of scenarios to process')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Process the dataset
    process_dataset(args.input_dir, args.output_dir, args.max_scenarios)
    
    logger.info("Dataset processing complete")


if __name__ == "__main__":
    main()