"""
Data loading utilities for grid scenario JSON files.
"""
import json
import os
import logging
from typing import Dict, List, Any, Optional, Tuple
import glob

logger = logging.getLogger(__name__)


class GridScenarioDataLoader:
    """
    Loader for grid scenario JSON files.
    Handles both scenario files and solution files.
    """
    
    def __init__(self, data_dir: str):
        """
        Initialize the data loader.
        
        Args:
            data_dir: Directory containing the scenario data
        """
        self.data_dir = data_dir
    
    def load_scenario(self, file_path: str) -> Dict[str, Any]:
        """
        Load a scenario JSON file.
        
        Args:
            file_path: Path to the scenario JSON file
            
        Returns:
            Dictionary containing the scenario data
        """
        try:
            with open(file_path, 'r') as f:
                scenario_data = json.load(f)
            return scenario_data
        except Exception as e:
            logger.error(f"Error loading scenario file {file_path}: {str(e)}")
            raise
    
    def load_solution(self, scenario_path: str) -> Optional[Dict[str, Any]]:
        """
        Load the solution file corresponding to a scenario.
        
        Args:
            scenario_path: Path to the scenario file
            
        Returns:
            Dictionary containing the solution data or None if not found
        """
        solution_path = f"{scenario_path}.pop_solution.json"
        if os.path.exists(solution_path):
            try:
                with open(solution_path, 'r') as f:
                    solution_data = json.load(f)
                return solution_data
            except Exception as e:
                logger.error(f"Error loading solution file {solution_path}: {str(e)}")
        else:
            logger.warning(f"Solution file not found: {solution_path}")
        return None
    
    def load_log(self, scenario_path: str) -> Optional[str]:
        """
        Load the log file corresponding to a scenario.
        
        Args:
            scenario_path: Path to the scenario file
            
        Returns:
            String containing the log data or None if not found
        """
        log_path = f"{scenario_path}.popsolution.log"
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r') as f:
                    log_data = f.read()
                return log_data
            except Exception as e:
                logger.error(f"Error loading log file {log_path}: {str(e)}")
        else:
            logger.warning(f"Log file not found: {log_path}")
        return None
    
    def load_scenario_with_solution(self, scenario_path: str) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]], Optional[str]]:
        """
        Load a scenario file along with its solution and log if available.
        
        Args:
            scenario_path: Path to the scenario file
            
        Returns:
            Tuple of (scenario_data, solution_data, log_data)
        """
        scenario_data = self.load_scenario(scenario_path)
        solution_data = self.load_solution(scenario_path)
        log_data = self.load_log(scenario_path)
        
        return scenario_data, solution_data, log_data
    
    def find_all_scenarios(self) -> List[str]:
        """
        Find all scenario files in the data directory.
        
        Returns:
            List of paths to scenario files
        """
        # Pattern to match scenario files but not solution or log files
        pattern = os.path.join(self.data_dir, "**", "scenario_*.json")
        # Exclude files with .pop_solution.json or .popsolution.log
        all_files = glob.glob(pattern, recursive=True)
        scenario_files = [f for f in all_files if not (f.endswith('.pop_solution.json') or f.endswith('.popsolution.log'))]
        return scenario_files
    
    def load_all_scenarios(self, max_scenarios: Optional[int] = None) -> List[Tuple[Dict[str, Any], Optional[Dict[str, Any]], Optional[str]]]:
        """
        Load all scenarios along with their solutions and logs.
        
        Args:
            max_scenarios: Maximum number of scenarios to load (None for all)
            
        Returns:
            List of tuples containing (scenario_data, solution_data, log_data)
        """
        scenario_files = self.find_all_scenarios()
        
        if max_scenarios is not None:
            scenario_files = scenario_files[:max_scenarios]
        
        results = []
        for scenario_file in scenario_files:
            try:
                data = self.load_scenario_with_solution(scenario_file)
                results.append(data)
            except Exception as e:
                logger.error(f"Error loading scenario {scenario_file}: {str(e)}")
        
        return results