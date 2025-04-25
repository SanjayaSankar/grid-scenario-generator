"""
Embedding generation for RAG (Retrieval Augmented Generation).
"""
import json
import os
import torch
import numpy as np
from typing import Tuple,Dict, List, Any, Optional, Union
import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class ScenarioEmbedding:
    """
    Generate embeddings for grid scenarios to enable similarity search.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedding model.
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model = SentenceTransformer(model_name)
    
    def _extract_text_representation(self, scenario: Dict[str, Any]) -> str:
        """
        Extract a text representation of a scenario for embedding.
        
        Args:
            scenario: Grid scenario data
            
        Returns:
            Text representation of the scenario
        """
        network = scenario.get('network', {})
        
        # Extract key counts
        num_buses = len(network.get('bus', []))
        num_lines = len(network.get('ac_line', []))
        num_transformers = len(network.get('two_winding_transformer', []))
        
        # Extract device information
        devices = network.get('simple_dispatchable_device', [])
        num_devices = len(devices)
        
        producers = [d for d in devices if d.get('device_type') == 'producer']
        consumers = [d for d in devices if d.get('device_type') == 'consumer']
        
        # Extract reliability information
        reliability = scenario.get('reliability', {})
        contingencies = reliability.get('contingency', [])
        num_contingencies = len(contingencies)
        
        # Extract time series information
        time_series = scenario.get('time_series_input', {})
        general = time_series.get('general', {})
        num_intervals = general.get('time_periods', 0)
        
        # Create text representation
        text = f"Grid scenario with {num_buses} buses, {num_lines} AC lines, and {num_transformers} transformers. "
        text += f"It has {num_devices} devices: {len(producers)} producers and {len(consumers)} consumers. "
        text += f"The reliability model includes {num_contingencies} contingencies. "
        text += f"The time series has {num_intervals} intervals. "
        
        # Add more details about devices
        if producers:
            producer_p_values = [d.get('initial_status', {}).get('p', 0) for d in producers]
            total_generation = sum(producer_p_values)
            text += f"Total generation: {total_generation:.2f} p.u. "
        
        if consumers:
            consumer_p_values = [d.get('initial_status', {}).get('p', 0) for d in consumers]
            total_load = sum(consumer_p_values)
            text += f"Total load: {total_load:.2f} p.u. "
        
        return text
    
    def generate_embedding(self, scenario: Dict[str, Any]) -> np.ndarray:
        """
        Generate an embedding for a grid scenario.
        
        Args:
            scenario: Grid scenario data
            
        Returns:
            Embedding vector
        """
        # Extract text representation
        text = self._extract_text_representation(scenario)
        
        # Generate embedding
        embedding = self.model.encode(text, convert_to_numpy=True)
        
        return embedding
    
    def generate_batch_embeddings(self, scenarios: List[Dict[str, Any]]) -> np.ndarray:
        """
        Generate embeddings for a batch of scenarios.
        
        Args:
            scenarios: List of grid scenario data
            
        Returns:
            Array of embedding vectors
        """
        # Extract text representations
        texts = [self._extract_text_representation(scenario) for scenario in scenarios]
        
        # Generate embeddings
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        
        return embeddings
    
    def save_embeddings(self, embeddings: np.ndarray, ids: List[str], output_dir: str) -> None:
        """
        Save embeddings to disk.
        
        Args:
            embeddings: Array of embedding vectors
            ids: List of scenario IDs
            output_dir: Output directory
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Save embeddings and IDs
        np.save(os.path.join(output_dir, "embeddings.npy"), embeddings)
        
        with open(os.path.join(output_dir, "ids.json"), 'w') as f:
            json.dump(ids, f)
        
        logger.info(f"Saved {len(embeddings)} embeddings to {output_dir}")
    
    def load_embeddings(self, input_dir: str) -> Tuple[np.ndarray, List[str]]:
        """
        Load embeddings from disk.
        
        Args:
            input_dir: Input directory
            
        Returns:
            Tuple of (embeddings, IDs)
        """
        # Load embeddings and IDs
        embeddings = np.load(os.path.join(input_dir, "embeddings.npy"))
        
        with open(os.path.join(input_dir, "ids.json"), 'r') as f:
            ids = json.load(f)
        
        logger.info(f"Loaded {len(embeddings)} embeddings from {input_dir}")
        
        return embeddings, ids
    
    def search_similar_scenarios(
        self, 
        query_embedding: np.ndarray, 
        embeddings: np.ndarray, 
        ids: List[str], 
        top_k: int = 5,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search for similar scenarios based on embeddings.
        
        Args:
            query_embedding: Query embedding vector
            embeddings: Array of embedding vectors
            ids: List of scenario IDs
            top_k: Number of results to return
            threshold: Similarity threshold
            
        Returns:
            List of similar scenario IDs with scores
        """
        # Calculate cosine similarities
        similarities = np.dot(embeddings, query_embedding) / (
            np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Filter by threshold
        results = []
        for idx in top_indices:
            similarity = similarities[idx]
            if similarity >= threshold:
                results.append({
                    "id": ids[idx],
                    "similarity": float(similarity)
                })
        
        return results


def embed_all_scenarios(
    data_dir: str, 
    output_dir: str, 
    model_name: str = "all-MiniLM-L6-v2"
) -> Tuple[np.ndarray, List[str]]:
    """
    Generate embeddings for all scenarios in a directory.
    
    Args:
        data_dir: Directory containing scenario files
        output_dir: Output directory for embeddings
        model_name: Name of the sentence transformer model
        
    Returns:
        Tuple of (embeddings, IDs)
    """
    # Load all scenario files
    scenario_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
    
    # Load scenarios
    scenarios = []
    ids = []
    
    for file_name in scenario_files:
        file_path = os.path.join(data_dir, file_name)
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Extract the scenario data
            if 'scenario' in data:
                scenario = data['scenario']
            else:
                scenario = data
            
            scenarios.append(scenario)
            ids.append(file_name.replace('.json', ''))
        except Exception as e:
            logger.error(f"Error loading {file_path}: {str(e)}")
    
    # Generate embeddings
    embedding_model = ScenarioEmbedding(model_name)
    embeddings = embedding_model.generate_batch_embeddings(scenarios)
    
    # Save embeddings
    embedding_model.save_embeddings(embeddings, ids, output_dir)
    
    return embeddings, ids