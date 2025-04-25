"""
Service for interfacing with language models.
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
import requests
from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for generating text using language models."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the LLM service.
        
        Args:
            api_key: API key for LLM provider
            model: Model identifier
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.LLM_MODEL
        
        if not self.api_key:
            logger.warning("No API key provided for LLM service")
    
    def generate_text(
        self, 
        prompt: str, 
        max_tokens: int = 1000, 
        temperature: float = 0.7,
        top_p: float = 0.95,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        stop: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate text using the language model.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            frequency_penalty: Frequency penalty
            presence_penalty: Presence penalty
            stop: Optional stop sequences
            
        Returns:
            LLM response
        """
        if not self.api_key:
            raise ValueError("API key is required for LLM service")
        
        try:
            # Call OpenAI API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "frequency_penalty": frequency_penalty,
                "presence_penalty": presence_penalty
            }
            
            if stop:
                data["stop"] = stop
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30  # 30-second timeout
            )
            
            # Check for errors
            response.raise_for_status()
            
            result = response.json()
            
            # Extract the generated text
            generated_text = result["choices"][0]["message"]["content"]
            
            return {
                "text": generated_text,
                "usage": result.get("usage", {}),
                "model": result.get("model", self.model)
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling LLM API: {str(e)}")
            return {
                "error": str(e),
                "text": ""
            }
    
    def generate_scenario(self, prompt: str) -> Dict[str, Any]:
        """
        Generate a grid scenario using the language model.
        
        Args:
            prompt: Input prompt
            
        Returns:
            Generated scenario or error
        """
        try:
            # Generate text
            response = self.generate_text(
                prompt=prompt,
                max_tokens=4000,  # Scenarios can be large
                temperature=0.7,   # Balanced creativity
                top_p=0.95
            )
            
            generated_text = response.get("text", "")
            
            # Try to parse as JSON
            try:
                # Extract JSON if it's embedded in markdown code blocks
                if "```json" in generated_text:
                    json_parts = generated_text.split("```json")
                    for part in json_parts[1:]:
                        if "```" in part:
                            json_text = part.split("```")[0].strip()
                            try:
                                return json.loads(json_text)
                            except json.JSONDecodeError:
                                continue
                
                # Try to parse the whole thing as JSON
                return json.loads(generated_text)
            
            except json.JSONDecodeError:
                logger.error("Generated text is not valid JSON")
                return {
                    "error": "Generated text is not valid JSON",
                    "raw_text": generated_text
                }
        
        except Exception as e:
            logger.error(f"Error generating scenario: {str(e)}")
            return {
                "error": str(e)
            }
    
    def enhance_scenario(self, scenario: Dict[str, Any], validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance a scenario based on validation results.
        
        Args:
            scenario: Original scenario
            validation_results: Validation results
            
        Returns:
            Enhanced scenario
        """
        # Create a prompt
        prompt = f"""
You are an expert in power grid modeling. Please enhance the following grid scenario to fix these validation issues:

VALIDATION RESULTS:
{json.dumps(validation_results, indent=2)}

CURRENT SCENARIO:
{json.dumps(scenario, indent=2)}

Please provide an improved version of the scenario that fixes the validation issues. 
Return only the JSON of the enhanced scenario without any additional text or explanations.
"""
        
        # Generate enhanced scenario
        return self.generate_scenario(prompt)
    
    def parse_scenario_from_text(self, text: str) -> Dict[str, Any]:
        """
        Parse a scenario from text.
        
        Args:
            text: Text to parse
            
        Returns:
            Parsed scenario
        """
        # Try to extract JSON
        try:
            # Check for JSON code blocks
            if "```json" in text:
                json_parts = text.split("```json")
                for part in json_parts[1:]:
                    if "```" in part:
                        json_text = part.split("```")[0].strip()
                        try:
                            return json.loads(json_text)
                        except json.JSONDecodeError:
                            continue
            
            # Try to find JSON object using braces
            start_idx = text.find("{")
            end_idx = text.rfind("}")
            
            if start_idx >= 0 and end_idx > start_idx:
                json_text = text[start_idx:end_idx+1]
                try:
                    return json.loads(json_text)
                except json.JSONDecodeError:
                    pass
            
            # If that fails, ask the LLM to extract the JSON
            prompt = f"""
The following text contains a description of a power grid scenario. Please extract the scenario as valid JSON:

{text}

Return only the JSON of the scenario without any additional text or explanations.
"""
            
            response = self.generate_text(
                prompt=prompt,
                max_tokens=4000,
                temperature=0.2  # Low temperature for deterministic output
            )
            
            generated_text = response.get("text", "")
            
            # Try to parse the generated text as JSON
            return json.loads(generated_text)
        
        except Exception as e:
            logger.error(f"Error parsing scenario from text: {str(e)}")
            return {
                "error": str(e),
                "raw_text": text
            }