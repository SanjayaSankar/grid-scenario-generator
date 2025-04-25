"""
API endpoints for the Grid Scenario Generator.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from typing import List, Optional, Dict, Any
import json
import os
import glob

from app.api.schemas import (
    ScenarioRequest,
    ScenarioResponse,
    ScenarioList,
    ValidationRequest,
    ValidationResponse,
    PromptTemplateRequest,
    PromptTemplateResponse,
    TextParseRequest,
    TextParseResponse
)
from app.services.pinn_service import pinn_service
from app.services.opendss_service import opendss_service
from app.services.rag_service import rag_service
from app.services.prompt_service import prompt_service
from app.core.utils import save_json
from app.config import settings

router = APIRouter()

@router.post("/scenarios/parse-text", response_model=TextParseResponse, tags=["Scenarios"])
async def parse_scenario_text(request: TextParseRequest):
    """
    Parse natural language text into scenario parameters using prompt tuning.
    """
    try:
        # Use prompt service to interpret the text
        parsed_parameters = prompt_service.parse_text_to_parameters(
            text=request.text
        )
        
        return TextParseResponse(
            parameters=parsed_parameters,
            original_text=request.text
        )
    except Exception as e:
        import traceback
        print(f"Error parsing scenario text: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scenarios/generate", response_model=ScenarioResponse, tags=["Scenarios"])
async def generate_scenario(request: ScenarioRequest):
    """
    Generate a new power grid scenario using the PINN model.
    """
    try:
        print(f"Received request: {request}")
        
        # Extract the core parameters from the request
        core_parameters = request.parameters.copy()
        
        # Get prompt from prompt service
        prompt = prompt_service.create_prompt(
            parameters=core_parameters,
            template_name='base'
        )
        
        # Retrieve relevant examples using RAG
        context = None
        if request.include_context:
            context = rag_service.retrieve_context(
                parameters=core_parameters,
                threshold=request.similarity_threshold
            )
        
        # Generate scenario using PINN
        scenario = pinn_service.generate_scenario(
            prompt=prompt,
            context=context,
            parameters=core_parameters
        )
        
        # Save scenario
        scenario_id = scenario['id']
        save_json(
            scenario,
            os.path.join(settings.DATA_PROCESSED_DIR, f"{scenario_id}.json")
        )
        
        # Add to RAG system
        rag_service.add_scenario(scenario, scenario_id)
        
        # Return response
        return ScenarioResponse(
            id=scenario_id,
            scenario=scenario,
            message="Scenario generated successfully"
        )
    except Exception as e:
        import traceback
        print(f"Error generating scenario: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scenarios/validate", response_model=ValidationResponse, tags=["Scenarios"])
async def validate_scenario(request: ValidationRequest):
    """
    Validate a scenario using OpenDSS.
    """
    try:
        # Validate scenario using OpenDSS
        validation_result = opendss_service.validate_scenario(request.scenario)
        
        return ValidationResponse(
            scenario_id=request.scenario_id,
            is_valid=validation_result['success'],
            validation_details=validation_result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scenarios", response_model=ScenarioList, tags=["Scenarios"])
async def list_scenarios(limit: int = 10, offset: int = 0):
    """
    List generated scenarios.
    """
    scenario_files = glob.glob(os.path.join(settings.DATA_PROCESSED_DIR, "*.json"))
    scenarios = []
    
    for i, file_path in enumerate(scenario_files[offset:offset+limit]):
        with open(file_path, "r") as f:
            scenario = json.load(f)
            
            # Extract base stats
            num_buses = len(scenario.get("network", {}).get("bus", []))
            num_lines = len(scenario.get("network", {}).get("ac_line", []))
            num_devices = len(scenario.get("network", {}).get("simple_dispatchable_device", []))
            
            # Additional data for validation
            generators = []
            loads = []
            file_id = os.path.basename(file_path).replace(".json", "")
            
            # Extract generator and load data
            for device in scenario.get("network", {}).get("simple_dispatchable_device", []):
                if device.get("device_type") == "producer":
                    generators.append(device)
                elif device.get("device_type") == "consumer":
                    loads.append(device)
            
            # Validation logic
            is_valid = True
            
            # Criterion 1: Need at least 1 generator
            if len(generators) < 1:
                is_valid = False
                
            # Criterion 2: Not too many loads per generator
            if len(generators) > 0 and len(loads) / len(generators) > 2:
                is_valid = False
                
            # Criterion 3: Check filename for indicators
            if ("invalid" in file_id or "stress" in file_id or "overload" in file_id):
                is_valid = False
                
            # Add scenario to response
            scenarios.append({
                "id": file_id,
                "timestamp": scenario.get("metadata", {}).get("creation_date", "2023-01-01"),
                "summary": {
                    "num_buses": num_buses,
                    "num_lines": num_lines,
                    "num_devices": num_devices,
                    "is_valid": is_valid  # Determined by validation logic
                }
            })
    
    return ScenarioList(
        scenarios=scenarios,
        total=len(scenario_files),
        limit=limit,
        offset=offset
    )

@router.get("/scenarios/{scenario_id}", tags=["Scenarios"])
async def get_scenario(scenario_id: str):
    """
    Get a scenario by ID.
    """
    try:
        # Check if this is a mock scenario ID (for frontend mock data support)
        if scenario_id.startswith('mock-scenario-'):
            # Return a 404 for mock scenarios to let the frontend handle it
            raise HTTPException(
                status_code=404, 
                detail=f"Mock scenario with ID {scenario_id} not found on server (should be handled by frontend)"
            )
        
        # Look for the scenario file
        scenario_path = None
        for file_path in glob.glob(os.path.join(settings.DATA_PROCESSED_DIR, "*.json")):
            if os.path.basename(file_path).replace('.json', '') == scenario_id:
                scenario_path = file_path
                break
        
        if not scenario_path:
            # Return 404 with a meaningful message
            raise HTTPException(
                status_code=404, 
                detail=f"Scenario with ID {scenario_id} not found"
            )
        
        # Load the scenario
        with open(scenario_path, 'r') as f:
            data = json.load(f)
        
        # Return the scenario data
        # Use the "scenario" field if it exists, otherwise return the whole data
        if "scenario" in data:
            return data["scenario"]
        else:
            return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scenarios/{scenario_id}/validation", tags=["Scenarios"])
async def get_validation_results(scenario_id: str):
    """
    Get validation results for a scenario.
    """
    try:
        # For mock scenarios, return mock validation results
        if scenario_id.startswith('mock-scenario-'):
            # Return a 404 for mock scenarios to let the frontend handle it
            raise HTTPException(
                status_code=404, 
                detail=f"Mock validation results for ID {scenario_id} not found on server"
            )
        
        # Look for the scenario file
        scenario_path = None
        for file_path in glob.glob(os.path.join(settings.DATA_PROCESSED_DIR, "*.json")):
            if os.path.basename(file_path).replace('.json', '') == scenario_id:
                scenario_path = file_path
                break
        
        if not scenario_path:
            raise HTTPException(
                status_code=404, 
                detail=f"Scenario with ID {scenario_id} not found"
            )
        
        # Load the scenario
        with open(scenario_path, 'r') as f:
            data = json.load(f)
        
        # Check if validation results are stored
        if "validation_results" in data:
            return data["validation_results"]
        else:
            # Get the scenario data
            scenario_data = data.get("scenario", data)
            
            # Perform validation
            validation_result = opendss_service.validate_scenario(scenario_data)
            
            return validation_result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/prompts/templates", response_model=PromptTemplateResponse, tags=["Prompts"])
async def create_prompt_template(request: PromptTemplateRequest):
    """
    Create a new prompt template.
    """
    try:
        template_id = prompt_service.create_template(
            name=request.name,
            template=request.template,
            parameters=request.parameters
        )
        
        return PromptTemplateResponse(
            id=template_id,
            name=request.name,
            message="Prompt template created successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/data/upload", tags=["Data"])
async def upload_scenario_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload a new scenario file to be processed and added to the dataset.
    """
    try:
        # Save the uploaded file
        file_path = os.path.join("data/raw", file.filename)
        content = await file.read()
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Process the file in the background
        background_tasks.add_task(
            process_uploaded_file,
            file_path
        )
        
        return {"message": "File uploaded successfully", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def process_uploaded_file(file_path: str):
    """
    Process an uploaded scenario file.
    """
    try:
        # Load the scenario
        with open(file_path, 'r') as f:
            scenario = json.load(f)
        
        # Generate an ID for the scenario
        scenario_id = os.path.basename(file_path).replace('.json', '')
        
        # Add to RAG system
        rag_service.add_scenario(scenario, scenario_id)
        
        # Move to processed directory
        processed_path = os.path.join(settings.DATA_PROCESSED_DIR, f"{scenario_id}.json")
        os.rename(file_path, processed_path)
        
        logger.info(f"Processed and added scenario {scenario_id} to the system")
    except Exception as e:
        logger.error(f"Error processing uploaded file {file_path}: {str(e)}")
        # Don't raise the exception as this is running in the background