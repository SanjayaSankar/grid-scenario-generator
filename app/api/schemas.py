"""
Pydantic models for API request/response schemas.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class ScenarioParameter(BaseModel):
    name: str
    value: Any


# app/api/schemas.py

class ScenarioRequest(BaseModel):
    """Request model for generating a new grid scenario."""
    parameters: Dict[str, Any] = Field(
        ..., 
        description="Parameters for scenario generation"
    )
    similarity_threshold: Optional[float] = Field(
        0.7, 
        description="Threshold for RAG similarity search"
    )
    include_context: Optional[bool] = Field(
        True, 
        description="Whether to include context from similar scenarios"
    )

    class Config:
        # Allow extra fields (important for flexibility)
        extra = "allow"


class ScenarioSummary(BaseModel):
    """Summary information about a grid scenario."""
    num_buses: int
    num_lines: int
    num_devices: int
    is_valid: bool = True


class ScenarioResponse(BaseModel):
    """Response model for a generated grid scenario."""
    id: str
    scenario: Dict[str, Any]
    message: str


class ScenarioListItem(BaseModel):
    """Item in the list of scenarios."""
    id: str
    summary: ScenarioSummary
    timestamp: str = "2023-01-01"  # Add timestamp field with default value


class ScenarioList(BaseModel):
    """List of scenarios with pagination."""
    scenarios: List[ScenarioListItem]
    total: int
    limit: int
    offset: int


class ValidationRequest(BaseModel):
    """Request model for validating a scenario with OpenDSS."""
    scenario_id: str
    scenario: Dict[str, Any]


class ValidationResponse(BaseModel):
    """Response model for scenario validation."""
    scenario_id: str
    is_valid: bool
    validation_details: Dict[str, Any]


class TextParseRequest(BaseModel):
    """Request model for parsing natural language into scenario parameters."""
    text: str = Field(
        ...,
        description="Natural language description of the desired scenario"
    )


class TextParseResponse(BaseModel):
    """Response model for text parsing results."""
    parameters: Dict[str, Any] = Field(
        ...,
        description="Extracted parameters from the text description"
    )
    original_text: str = Field(
        ..., 
        description="Original text that was parsed"
    )


class PromptTemplateParameter(BaseModel):
    """Parameter definition for a prompt template."""
    name: str
    description: str
    type: str = "string"
    required: bool = True
    default: Optional[Any] = None


class PromptTemplateRequest(BaseModel):
    """Request model for creating a prompt template."""
    name: str
    template: str
    parameters: List[PromptTemplateParameter]


class PromptTemplateResponse(BaseModel):
    """Response model for a prompt template."""
    id: str
    name: str
    message: str