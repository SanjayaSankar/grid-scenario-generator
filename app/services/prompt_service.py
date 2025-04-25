"""
Service for generating prompts for power grid scenario generation.
"""
import os
import json
import logging
import re
from typing import Dict, Any, List, Optional
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

class PromptService:
    """Service for generating prompts for power grid scenario generation."""
    
    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialize the prompt service.
        
        Args:
            templates_dir: Directory containing prompt templates
        """
        self.templates_dir = templates_dir or os.path.join('app', 'templates')
        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=True
        )
        self.templates = {}
        
        # Load templates
        self._load_templates()
    
    def _load_templates(self) -> None:
        """Load prompt templates from directory."""
        try:
            if not os.path.exists(self.templates_dir):
                os.makedirs(self.templates_dir)
                logger.info(f"Created templates directory: {self.templates_dir}")
            
            # Load default templates
            default_templates = {
                'base': self._create_base_template(),
                'physics': self._create_physics_template(),
                'reliability': self._create_reliability_template(),
                'text_parser': self._create_text_parser_template()
            }
            
            # Save default templates if they don't exist
            for name, template in default_templates.items():
                template_path = os.path.join(self.templates_dir, f"{name}.jinja2")
                if not os.path.exists(template_path):
                    with open(template_path, 'w') as f:
                        f.write(template)
            
            # Load all templates
            for filename in os.listdir(self.templates_dir):
                if filename.endswith('.jinja2'):
                    name = filename.replace('.jinja2', '')
                    self.templates[name] = self.env.get_template(filename)
            
            logger.info(f"Loaded {len(self.templates)} prompt templates")
        except Exception as e:
            logger.error(f"Error loading templates: {str(e)}")
    
    def _create_base_template(self) -> str:
        """Create base prompt template."""
        return """Generate a power grid scenario with the following specifications:

Network Configuration:
- Number of buses: {{ num_buses }}
- Number of generators: {{ num_generators }}
- Number of loads: {{ num_loads }}
{% if topology %}
- Topology: {{ topology }}
{% endif %}

Generation:
{% if generation_profile %}
- Generation profile: {{ generation_profile }}
{% endif %}
{% if generator_types %}
- Generator types: {{ generator_types|join(', ') }}
{% endif %}

Load:
{% if load_profile %}
- Load profile: {{ load_profile }}
{% endif %}
{% if load_types %}
- Load types: {{ load_types|join(', ') }}
{% endif %}

Constraints:
- Voltage limits: 0.95-1.05 p.u.
- Line flow limits: As specified in line data
- Generator limits: As specified in generator data

Please generate a scenario that meets these specifications while maintaining power flow balance and respecting all constraints."""
    
    def _create_physics_template(self) -> str:
        """Create physics-based prompt template."""
        return """Generate a power grid scenario that satisfies the following physics-based constraints:

Power Flow Equations:
- Active power balance at each bus
- Reactive power balance at each bus
- Line flow equations
- Transformer equations

Voltage Constraints:
- Bus voltage magnitudes: 0.95-1.05 p.u.
- Voltage angle differences: Within stability limits

Line Flow Constraints:
- Active power flow: Within thermal limits
- Reactive power flow: Within voltage stability limits

Generation Constraints:
- Active power limits
- Reactive power limits
- Ramp rate limits
- Minimum up/down times

Load Constraints:
- Active power demand
- Reactive power demand
- Power factor limits

Please ensure the generated scenario satisfies all these physics-based constraints."""
    
    def _create_reliability_template(self) -> str:
        """Create reliability-based prompt template."""
        return """Generate a power grid scenario that meets the following reliability requirements:

System Reliability:
- N-1 contingency criteria
- Voltage stability margin
- Frequency stability margin
- Spinning reserve requirements

Component Reliability:
- Generator availability
- Line availability
- Transformer availability
- Load reliability requirements

Reliability Metrics:
- Expected Energy Not Served (EENS)
- Loss of Load Probability (LOLP)
- Expected Interruption Frequency (EIF)
- Expected Interruption Duration (EID)

Please generate a scenario that meets these reliability requirements while maintaining system stability."""
    
    def _create_text_parser_template(self) -> str:
        """Create text parsing prompt template."""
        return """Extract the following parameters from the text description of a power grid scenario.
ALWAYS provide values for all the required parameters, making reasonable assumptions if the information is not explicitly stated.

Text description: {{ text }}

Please extract the following parameters in JSON format:
{
  "num_buses": <integer between 2 and 10>,
  "num_generators": <integer between 1 and 5>,
  "num_loads": <integer between 1 and 5>,
  "peak_load": <integer between 10 and 1000>,
  "voltage_profile": <one of: "flat", "varied", "stressed">,
  "reliability_level": <one of: "high", "medium", "low">,
  "congestion_level": <one of: "high", "medium", "low">
}

Output ONLY the JSON object with no additional text."""
    
    def create_prompt(
        self,
        parameters: Dict[str, Any],
        template_name: str = 'base',
        context: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Create a prompt for scenario generation.
        
        Args:
            parameters: Generation parameters
            template_name: Name of template to use
            context: Optional RAG context
            
        Returns:
            Generated prompt
        """
        try:
            # Get template
            template = self.templates.get(template_name)
            if not template:
                raise ValueError(f"Template '{template_name}' not found")
            
            # Add context if available
            if context:
                parameters['context'] = self._format_context(context)
            
            # Render template
            prompt = template.render(**parameters)
            
            return prompt
        except Exception as e:
            logger.error(f"Error creating prompt: {str(e)}")
            raise
    
    def _format_context(self, context: List[Dict[str, Any]]) -> str:
        """
        Format RAG context for inclusion in prompt.
        
        Args:
            context: List of similar scenarios
            
        Returns:
            Formatted context text
        """
        context_parts = ["Similar Scenarios:"]
        
        for item in context:
            scenario = item['scenario']
            similarity = item['similarity']
            
            # Extract key information
            network = scenario['network']
            buses = network['bus']
            lines = network['ac_line']
            devices = network['simple_dispatchable_device']
            
            # Format scenario information
            scenario_text = [
                f"Scenario (similarity: {similarity:.4f}):",
                f"- Buses: {len(buses)}",
                f"- Lines: {len(lines)}",
                f"- Devices: {len(devices)}"
            ]
            
            # Add bus information
            for bus in buses[:3]:  # Limit to first 3 buses
                scenario_text.append(
                    f"- Bus {bus['uid']}: "
                    f"V={bus['initial_status']['vm']:.4f} p.u., "
                    f"θ={bus['initial_status']['va']:.4f} rad"
                )
            
            if len(buses) > 3:
                scenario_text.append(f"- ... and {len(buses) - 3} more buses")
            
            context_parts.append('\n'.join(scenario_text))
        
        return '\n\n'.join(context_parts)
    
    def parse_text_to_parameters(self, text: str) -> Dict[str, Any]:
        """
        Parse natural language text to scenario parameters.
        
        Args:
            text: Natural language description of scenario
            
        Returns:
            Extracted parameters
        """
        try:
            logger.info(f"Parsing text to parameters: {text}")
            
            # First try using regex pattern matching
            parameters = self._text_parsing_patterns(text)
            
            # If missing critical parameters, apply prompt tuning
            if not all(k in parameters for k in ['num_buses', 'num_generators', 'num_loads']):
                parameters = self._prompt_tuning_for_parameters(text)
            
            logger.info(f"Extracted parameters: {parameters}")
            return parameters
        except Exception as e:
            logger.error(f"Error parsing text to parameters: {str(e)}")
            # Fall back to default values if all else fails
            return {
                "num_buses": 2,
                "num_generators": 1,
                "num_loads": 1,
                "peak_load": 10,
                "voltage_profile": "flat",
                "reliability_level": "high",
                "congestion_level": "low"
            }
    
    def _text_parsing_patterns(self, text: str) -> Dict[str, Any]:
        """
        Extract parameters from text using regex patterns.
        
        Args:
            text: Natural language description of scenario
            
        Returns:
            Extracted parameters
        """
        parameters = {}
        
        # Extract numerical values
        num_buses_match = re.search(r'(\d+)\s+bus(es)?', text, re.IGNORECASE)
        if num_buses_match:
            parameters['num_buses'] = min(max(int(num_buses_match.group(1)), 2), 10)
        
        num_generators_match = re.search(r'(\d+)\s+generator', text, re.IGNORECASE)
        if num_generators_match:
            parameters['num_generators'] = min(max(int(num_generators_match.group(1)), 1), 5)
        
        num_loads_match = re.search(r'(\d+)\s+load', text, re.IGNORECASE)
        if num_loads_match:
            parameters['num_loads'] = min(max(int(num_loads_match.group(1)), 1), 5)
        
        peak_load_match = re.search(r'(\d+)\s+MW', text, re.IGNORECASE)
        if peak_load_match:
            parameters['peak_load'] = min(max(int(peak_load_match.group(1)), 10), 1000)
        
        # Extract categorical values
        if re.search(r'flat\s+voltage', text, re.IGNORECASE):
            parameters['voltage_profile'] = 'flat'
        elif re.search(r'varied\s+voltage', text, re.IGNORECASE):
            parameters['voltage_profile'] = 'varied'
        elif re.search(r'stressed\s+voltage', text, re.IGNORECASE):
            parameters['voltage_profile'] = 'stressed'
        
        if re.search(r'high\s+reliability', text, re.IGNORECASE):
            parameters['reliability_level'] = 'high'
        elif re.search(r'medium\s+reliability', text, re.IGNORECASE):
            parameters['reliability_level'] = 'medium'
        elif re.search(r'low\s+reliability', text, re.IGNORECASE):
            parameters['reliability_level'] = 'low'
        
        if re.search(r'high\s+congestion', text, re.IGNORECASE):
            parameters['congestion_level'] = 'high'
        elif re.search(r'medium\s+congestion', text, re.IGNORECASE):
            parameters['congestion_level'] = 'medium'
        elif re.search(r'low\s+congestion', text, re.IGNORECASE):
            parameters['congestion_level'] = 'low'
        
        return parameters
    
    def _prompt_tuning_for_parameters(self, text: str) -> Dict[str, Any]:
        """
        Extract parameters using prompt tuning (LLM approach).
        In a real implementation, this would use an LLM API call.
        
        Args:
            text: Natural language description of scenario
            
        Returns:
            Extracted parameters
        """
        # In a real implementation, this would use an LLM API (like OpenAI GPT)
        # to extract parameters from the text description
        
        # For this demonstration, we'll use a mock implementation
        # that applies simple rules based on keywords in the text
        
        params = {
            "num_buses": 2,
            "num_generators": 1,
            "num_loads": 1,
            "peak_load": 10,
            "voltage_profile": "flat",
            "reliability_level": "high",
            "congestion_level": "low"
        }
        
        # Apply basic logic for a more sophisticated mock
        if "large" in text.lower() or "big" in text.lower():
            params["num_buses"] = 8
            params["num_generators"] = 3
            params["num_loads"] = 4
            params["peak_load"] = 500
        elif "medium" in text.lower():
            params["num_buses"] = 5
            params["num_generators"] = 2
            params["num_loads"] = 2
            params["peak_load"] = 100
        elif "small" in text.lower():
            params["num_buses"] = 3
            params["num_generators"] = 1
            params["num_loads"] = 1
            params["peak_load"] = 30
        
        # Check for reliability indicators
        if "reliable" in text.lower() or "robust" in text.lower():
            params["reliability_level"] = "high"
        elif "unreliable" in text.lower() or "fragile" in text.lower():
            params["reliability_level"] = "low"
        
        # Check for congestion indicators
        if "congested" in text.lower() or "overloaded" in text.lower():
            params["congestion_level"] = "high"
        elif "uncongested" in text.lower() or "underutilized" in text.lower():
            params["congestion_level"] = "low"
        
        # Update with any parameters already extracted from regex
        regex_params = self._text_parsing_patterns(text)
        params.update(regex_params)
        
        return params
    
    def create_template(
        self,
        name: str,
        template: str,
        parameters: List[str]
    ) -> str:
        """
        Create a new prompt template.
        
        Args:
            name: Template name
            template: Template text
            parameters: List of required parameters
            
        Returns:
            Template ID
        """
        try:
            # Validate template
            self.env.from_string(template)
        
        # Save template
            template_path = os.path.join(self.templates_dir, f"{name}.jinja2")
            with open(template_path, 'w') as f:
                f.write(template)
            
            # Reload templates
            self._load_templates()
            
            return name
        except Exception as e:
            logger.error(f"Error creating template: {str(e)}")
            raise
    
    def get_template(self, name: str) -> Optional[str]:
        """
        Get a template by name.
        
        Args:
            name: Template name
            
        Returns:
            Template text or None if not found
        """
        template = self.templates.get(name)
        if template:
            return template.template
        return None
    
    def list_templates(self) -> List[str]:
        """
        List all available templates.
            
        Returns:
            List of template names
        """
        return list(self.templates.keys())

# Create a global instance of the PromptService
prompt_service = PromptService()