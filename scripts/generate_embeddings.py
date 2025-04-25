#!/usr/bin/env python
"""
Script to generate embeddings for grid scenarios to enable RAG.

Usage:
    python generate_embeddings.py --data_dir data/processed --output_dir data/embeddings
"""
import os
import argparse
import logging
from typing import Optional

# Add the project root to the Python path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.embeddings import embed_all_scenarios

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_embeddings(
    data_dir: str, 
    output_dir: str, 
    model_name: str = "all-MiniLM-L6-v2",
    force: bool = False
) -> None:
    """
    Generate embeddings for grid scenarios.
    
    Args:
        data_dir: Directory containing processed scenario files
        output_dir: Output directory for embeddings
        model_name: Name of the sentence transformer model to use
        force: Whether to regenerate existing embeddings
    """
    # Check if embeddings already exist
    if os.path.exists(os.path.join(output_dir, "embeddings.npy")) and not force:
        logger.warning("Embeddings already exist. Use --force to regenerate.")
        return
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Generating embeddings for scenarios in {data_dir}")
    
    # Generate embeddings
    embeddings, ids = embed_all_scenarios(
        data_dir=data_dir,
        output_dir=output_dir,
        model_name=model_name
    )
    
    logger.info(f"Generated embeddings for {len(embeddings)} scenarios")
    logger.info(f"Embeddings saved to {output_dir}")


def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description='Generate embeddings for grid scenarios')
    parser.add_argument('--data_dir', type=str, required=True, help='Directory with processed data')
    parser.add_argument('--output_dir', type=str, required=True, help='Output directory for embeddings')
    parser.add_argument('--model_name', type=str, default="all-MiniLM-L6-v2", help='Sentence transformer model name')
    parser.add_argument('--force', action='store_true', help='Force regeneration of existing embeddings')
    
    args = parser.parse_args()
    
    # Generate embeddings
    generate_embeddings(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        model_name=args.model_name,
        force=args.force
    )
    
    logger.info("Embedding generation complete")


if __name__ == "__main__":
    main()