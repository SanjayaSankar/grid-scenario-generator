"""
Prompt templates for LLM-based scenario generation and enhancement.
"""
import json
import os
from typing import Dict, List, Any, Optional
import logging
from jinja2 import Template

logger = logging.getLogger(__name__)


class PromptTemplate:
    """Base class for prompt templates."""
    
    def __init__(self, template_str: str, parameters: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize the prompt template.
        
        Args:
            template_str: Template string in Jinja2 format
            parameters: List of parameter definitions
        """
        self.template_str = template_str
        self.template = Template(template_str)
        self.parameters = parameters or []
    
    def render(self, values: Dict[str, Any]) -> str:
        """
        Render the template with parameter values.
        
        Args:
            values: Dictionary of parameter values
            
        Returns:
            Rendered prompt
        """
        return self.template.render(**values)
    
# app/models/prompt_templates.py

    def validate_parameters(self, values: Dict[str, Any]) -> List[str]:
        """
        Validate parameter values against definitions.
        
        Args:
            values: Dictionary of parameter values
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check for required parameters
        for param in self.parameters:
            name = param['name']
            required = param.get('required', False)
            
            if required and name not in values:
                errors.append(f"Missing required parameter: {name}")
        
        # Skip validation of unknown parameters - we'll just ignore them
        # This makes the code more flexible
        
        # Check parameter types for known parameters
        for name, value in values.items():
            param_def = next((p for p in self.parameters if p['name'] == name), None)
            
            if param_def:
                expected_type = param_def.get('type', 'string')
                
                if expected_type == 'integer' and not isinstance(value, int):
                    errors.append(f"Parameter {name} should be an integer")
                elif expected_type == 'number' and not isinstance(value, (int, float)):
                    errors.append(f"Parameter {name} should be a number")
                elif expected_type == 'boolean' and not isinstance(value, bool):
                    errors.append(f"Parameter {name} should be a boolean")
                elif expected_type == 'array' and not isinstance(value, list):
                    errors.append(f"Parameter {name} should be an array")
                elif expected_type == 'object' and not isinstance(value, dict):
                    errors.append(f"Parameter {name} should be an object")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert template to dictionary.
        
        Returns:
            Dictionary representation of the template
        """
        return {
            'template': self.template_str,
            'parameters': self.parameters
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptTemplate':
        """
        Create template from dictionary.
        
        Args:
            data: Dictionary representation of the template
            
        Returns:
            Template instance
        """
        return cls(
            template_str=data['template'],
            parameters=data.get('parameters', [])
        )


class ScenarioGenerationTemplate(PromptTemplate):
    """Template for grid scenario generation."""
    
    @classmethod
    def default_template(cls) -> 'ScenarioGenerationTemplate':
        """
        Create default scenario generation template.
        
        Returns:
            Template instance
        """
        template_str = """
You are an expert in power grid modeling and optimization. Generate a realistic power grid scenario with the following characteristics:

- Number of buses: {{ num_buses }}
- Number of generators: {{ num_generators }}
- Number of loads: {{ num_loads }}
- System base: 100 MVA
{% if peak_load %}
- Peak system load: {{ peak_load }} MW
{% endif %}
{% if voltage_profile %}
- Voltage profile: {{ voltage_profile }}
{% endif %}
{% if reliability_level %}
- Reliability level: {{ reliability_level }}
{% endif %}
{% if congestion_level %}
- Congestion level: {{ congestion_level }}
{% endif %}

{% if similar_examples %}
Here are examples of similar scenarios to use as reference:
{{ similar_examples }}
{% endif %}

The scenario should include:
1. Bus data with voltage magnitudes and angles
2. Branch data with impedances and flow limits
3. Generator data with capacity and cost curves
4. Load data with power consumption profiles

Please create a realistic, physics-consistent scenario that could be used for power system simulations.
"""
        
        parameters = [
            {
                'name': 'num_buses',
                'description': 'Number of buses in the grid',
                'type': 'integer',
                'required': True
            },
            {
                'name': 'num_generators',
                'description': 'Number of generators in the grid',
                'type': 'integer',
                'required': True
            },
            {
                'name': 'num_loads',
                'description': 'Number of loads in the grid',
                'type': 'integer',
                'required': True
            },
            {
                'name': 'peak_load',
                'description': 'Peak system load in MW',
                'type': 'number',
                'required': False
            },
            {
                'name': 'voltage_profile',
                'description': 'Desired voltage profile (e.g., "flat", "varied")',
                'type': 'string',
                'required': False
            },
            {
                'name': 'reliability_level',
                'description': 'Desired reliability level (e.g., "high", "medium", "low")',
                'type': 'string',
                'required': False
            },
            {
                'name': 'congestion_level',
                'description': 'Desired congestion level (e.g., "high", "medium", "low")',
                'type': 'string',
                'required': False
            },
            {
                'name': 'similar_examples',
                'description': 'Examples of similar scenarios to use as reference',
                'type': 'string',
                'required': False
            }
        ]
        
        return cls(template_str, parameters)


class ScenarioEnhancementTemplate(PromptTemplate):
    """Template for enhancing generated scenarios."""
    
    @classmethod
    def default_template(cls) -> 'ScenarioEnhancementTemplate':
        """
        Create default scenario enhancement template.
        
        Returns:
            Template instance
        """
        template_str = """
You are an expert in power grid modeling and optimization. Enhance the following power grid scenario to make it more realistic and useful for {{ purpose }}.

Current scenario:
{{ scenario }}

{% if validation_results %}
Validation results:
{{ validation_results }}
{% endif %}

Please improve the scenario by:
1. Ensuring all physical constraints are satisfied
2. Making the load and generation profiles more realistic
3. Adjusting parameters to better reflect real-world conditions
{% if specific_improvements %}
4. {{ specific_improvements }}
{% endif %}

Provide the enhanced scenario in the same format as the input.
"""
        
        parameters = [
            {
                'name': 'scenario',
                'description': 'Current scenario data',
                'type': 'string',
                'required': True
            },
            {
                'name': 'purpose',
                'description': 'Purpose of the scenario (e.g., "contingency analysis", "market simulation")',
                'type': 'string',
                'required': True
            },
            {
                'name': 'validation_results',
                'description': 'Results of validation checks on the scenario',
                'type': 'string',
                'required': False
            },
            {
                'name': 'specific_improvements',
                'description': 'Specific improvements to make',
                'type': 'string',
                'required': False
            }
        ]
        
        return cls(template_str, parameters)


class TemplateManager:
    """Manager for prompt templates."""
    
    def __init__(self, templates_dir: str):
        """
        Initialize the template manager.
        
        Args:
            templates_dir: Directory for storing templates
        """
        self.templates_dir = templates_dir
        os.makedirs(templates_dir, exist_ok=True)
        self.templates = {}
        self.load_templates()
    
    def load_templates(self) -> None:
        """Load templates from the templates directory."""
        template_files = [f for f in os.listdir(self.templates_dir) if f.endswith('.json')]
        
        for file_name in template_files:
            template_id = file_name.replace('.json', '')
            file_path = os.path.join(self.templates_dir, file_name)
            
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                template = PromptTemplate.from_dict(data)
                self.templates[template_id] = template
                
                logger.info(f"Loaded template: {template_id}")
            except Exception as e:
                logger.error(f"Error loading template {file_path}: {str(e)}")
    
    def save_template(self, template_id: str, template: PromptTemplate) -> None:
        """
        Save a template to disk.
        
        Args:
            template_id: Template identifier
            template: Template instance
        """
        self.templates[template_id] = template
        
        file_path = os.path.join(self.templates_dir, f"{template_id}.json")
        
        with open(file_path, 'w') as f:
            json.dump(template.to_dict(), f, indent=2)
        
        logger.info(f"Saved template: {template_id}")
    
    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """
        Get a template by ID.
        
        Args:
            template_id: Template identifier
            
        Returns:
            Template instance or None if not found
        """
        return self.templates.get(template_id)
    
    def delete_template(self, template_id: str) -> bool:
        """
        Delete a template.
        
        Args:
            template_id: Template identifier
            
        Returns:
            True if template was deleted, False otherwise
        """
        if template_id in self.templates:
            del self.templates[template_id]
            
            file_path = os.path.join(self.templates_dir, f"{template_id}.json")
            
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted template: {template_id}")
                return True
        
        return False
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """
        List all templates.
        
        Returns:
            List of template information
        """
        result = []
        
        for template_id, template in self.templates.items():
            result.append({
                'id': template_id,
                'parameters': template.parameters
            })
        
        return result
    
    def initialize_default_templates(self) -> None:
        """Initialize default templates if they don't exist."""
        # Add scenario generation template
        if 'scenario_generation' not in self.templates:
            template = ScenarioGenerationTemplate.default_template()
            self.save_template('scenario_generation', template)
        
        # Add scenario enhancement template
        if 'scenario_enhancement' not in self.templates:
            template = ScenarioEnhancementTemplate.default_template()
            self.save_template('scenario_enhancement', template)