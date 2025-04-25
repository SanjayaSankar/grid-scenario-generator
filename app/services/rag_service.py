"""
Service for Retrieval-Augmented Generation (RAG) of power grid scenarios.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class RAGService:
    """Service for Retrieval-Augmented Generation of power grid scenarios."""
    
    def __init__(
        self,
        model_name: str = 'all-MiniLM-L6-v2',
        embedding_dim: int = 384,
        max_context_length: int = 5
    ):
        """
        Initialize the RAG service.
        
        Args:
            model_name: Name of the sentence transformer model
            embedding_dim: Dimension of embeddings
            max_context_length: Maximum number of similar scenarios to retrieve
        """
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = embedding_dim
        self.max_context_length = max_context_length
        self.scenario_embeddings = {}
        self.scenario_data = {}
        
        # Load existing scenarios if available
        self._load_scenarios()
    
    def _load_scenarios(self) -> None:
        """Load existing scenarios and their embeddings."""
        try:
            # Load scenario data
            data_dir = os.path.join('data', 'processed')
            for filename in os.listdir(data_dir):
                if filename.endswith('.json'):
                    with open(os.path.join(data_dir, filename), 'r') as f:
                        scenario = json.load(f)
                        scenario_id = filename.replace('.json', '')
                        self.scenario_data[scenario_id] = scenario
            
            # Load or generate embeddings
            embeddings_file = os.path.join('data', 'embeddings', 'scenario_embeddings.npy')
            if os.path.exists(embeddings_file):
                self.scenario_embeddings = np.load(embeddings_file, allow_pickle=True).item()
            else:
                self._generate_embeddings()
                self._save_embeddings()
        except Exception as e:
            logger.error(f"Error loading scenarios: {str(e)}")
    
    def _generate_embeddings(self) -> None:
        """Generate embeddings for all scenarios."""
        for scenario_id, scenario in self.scenario_data.items():
            # Convert scenario to text
            scenario_text = self._scenario_to_text(scenario)
            
            # Generate embedding
            embedding = self.model.encode(scenario_text)
            self.scenario_embeddings[scenario_id] = embedding
    
    def _save_embeddings(self) -> None:
        """Save scenario embeddings to disk."""
        os.makedirs(os.path.join('data', 'embeddings'), exist_ok=True)
        embeddings_file = os.path.join('data', 'embeddings', 'scenario_embeddings.npy')
        np.save(embeddings_file, self.scenario_embeddings)
    
    def _scenario_to_text(self, scenario: Dict[str, Any]) -> str:
        """
        Convert scenario to text for embedding.
        
        Args:
            scenario: Power grid scenario
            
        Returns:
            Text representation of scenario
        """
        text_parts = []
        
        # Add network information
        network = scenario['network']
        text_parts.append(f"Network with {len(network['bus'])} buses, "
                         f"{len(network['ac_line'])} lines, "
                         f"{len(network['simple_dispatchable_device'])} devices")
        
        # Add bus information
        for bus in network['bus']:
            text_parts.append(f"Bus {bus['uid']}: "
                            f"Base voltage {bus['base_nom_volt']}kV, "
                            f"Voltage {bus['initial_status']['vm']}p.u., "
                            f"Angle {bus['initial_status']['va']}deg")
        
        # Add line information
        for line in network['ac_line']:
            text_parts.append(f"Line {line['uid']}: "
                            f"From {line['fr_bus']} to {line['to_bus']}, "
                            f"R={line['r']}, X={line['x']}, B={line['b']}")
        
        # Add device information
        for device in network['simple_dispatchable_device']:
            text_parts.append(f"Device {device['uid']}: "
                            f"Type {device['device_type']}, "
                            f"Bus {device['bus']}, "
                            f"P={device['initial_status']['p']}, "
                            f"Q={device['initial_status']['q']}")
        
        return ' '.join(text_parts)
    
    def retrieve_context(
        self,
        parameters: Dict[str, Any],
        threshold: float = 0.7,
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve similar scenarios based on parameters.
        
        Args:
            parameters: Generation parameters
            threshold: Similarity threshold
            max_results: Maximum number of results to return
            
        Returns:
            List of similar scenarios
        """
        # Convert parameters to text
        parameters_text = self._parameters_to_text(parameters)
        
        # Generate embedding for parameters
        parameters_embedding = self.model.encode(parameters_text)
        
        # Calculate similarities
        similarities = {}
        for scenario_id, embedding in self.scenario_embeddings.items():
            similarity = cosine_similarity(
                parameters_embedding.reshape(1, -1),
                embedding.reshape(1, -1)
            )[0][0]
            if similarity >= threshold:
                similarities[scenario_id] = similarity
        
        # Sort by similarity
        sorted_scenarios = sorted(
            similarities.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Get top results
        max_results = max_results or self.max_context_length
        top_scenarios = sorted_scenarios[:max_results]
        
        # Return scenario data
        return [
            {
                'scenario': self.scenario_data[scenario_id],
                'similarity': similarity
            }
            for scenario_id, similarity in top_scenarios
        ]
    
    def _parameters_to_text(self, parameters: Dict[str, Any]) -> str:
        """
        Convert parameters to text for embedding.
        
        Args:
            parameters: Generation parameters
            
        Returns:
            Text representation of parameters
        """
        text_parts = []
        
        # Add basic parameters
        if 'num_buses' in parameters:
            text_parts.append(f"{parameters['num_buses']} buses")
        if 'num_generators' in parameters:
            text_parts.append(f"{parameters['num_generators']} generators")
        if 'num_loads' in parameters:
            text_parts.append(f"{parameters['num_loads']} loads")
        
        # Add topology parameters
        if 'topology' in parameters:
            text_parts.append(f"Topology: {parameters['topology']}")
        
        # Add load parameters
        if 'load_profile' in parameters:
            text_parts.append(f"Load profile: {parameters['load_profile']}")
        
        # Add generation parameters
        if 'generation_profile' in parameters:
            text_parts.append(f"Generation profile: {parameters['generation_profile']}")
        
        return ' '.join(text_parts)
    
    def add_scenario(self, scenario: Dict[str, Any], scenario_id: str) -> None:
        """
        Add a new scenario to the RAG system.
        
        Args:
            scenario: Power grid scenario
            scenario_id: Scenario ID
        """
        # Add scenario data
        self.scenario_data[scenario_id] = scenario
        
        # Generate and add embedding
        scenario_text = self._scenario_to_text(scenario)
        embedding = self.model.encode(scenario_text)
        self.scenario_embeddings[scenario_id] = embedding
        
        # Save embeddings
        self._save_embeddings()
    
    def remove_scenario(self, scenario_id: str) -> None:
        """
        Remove a scenario from the RAG system.
        
        Args:
            scenario_id: Scenario ID to remove
        """
        if scenario_id in self.scenario_data:
            del self.scenario_data[scenario_id]
        if scenario_id in self.scenario_embeddings:
            del self.scenario_embeddings[scenario_id]
        
        # Save embeddings
        self._save_embeddings()

# Create a global instance of the RAGService
rag_service = RAGService()