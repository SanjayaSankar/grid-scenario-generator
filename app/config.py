"""
Configuration settings for the Grid Scenario Generator application.
Load settings from environment variables with defaults.
"""
import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl


class Settings(BaseSettings):
    # API Settings
    API_PREFIX: str = "/api"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # CORS
    CORS_ORIGINS: List[AnyHttpUrl] = ["http://localhost:3000"]
    
    # Data paths
    DATA_RAW_DIR: str = "data/raw"
    DATA_PROCESSED_DIR: str = "data/processed"
    EMBEDDINGS_DIR: str = "data/embeddings"
    
    # Model settings
    MODEL_DIR: str = "models"
    PINN_MODEL_PATH: str = "models/pinn_model.pt"
    
    # OpenDSS settings
    OPENDSS_PATH: str = ""  # Path to OpenDSS executable
    
    # LLM settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LLM_MODEL: str = "gpt-4"  # or any other model you want to use
    
    # Vector database settings
    VECTOR_DB_URL: str = os.getenv("VECTOR_DB_URL", "")
    VECTOR_DB_API_KEY: str = os.getenv("VECTOR_DB_API_KEY", "")
    VECTOR_DB_NAMESPACE: str = "grid_scenarios"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()