"""
Main entry point for the Grid Scenario Generator application.
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.config import settings
from app.services.pinn_service import PINNService
from app.services.opendss_service import OpenDSSService
from app.services.rag_service import RAGService
from app.services.prompt_service import PromptService

# Initialize services
pinn_service = PINNService()
opendss_service = OpenDSSService()
rag_service = RAGService()
prompt_service = PromptService()

app = FastAPI(
    title="Grid Scenario Generator",
    description="API for generating synthetic power grid scenarios using PINN and RAG",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "services": {
            "pinn": pinn_service.model is not None,
            "opendss": True,  # OpenDSS is always available
            "rag": len(rag_service.scenario_data) > 0,
            "prompt": len(prompt_service.templates) > 0
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )