"""
FastAPI Application Entry Point.
Provides:
- POST /agent: Primary endpoint triggering the autonomous agent pipeline.
- GET /download/{filename}: Secure endpoint for downloading generated .docx reports.
- GET /health: Simple health and provider status endpoint.
"""
import os
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import OUTPUT_DIR, APP_HOST, APP_PORT
from app.models import AgentRequest, AgentResponse
from app.agent import run_agent
from app.llm_client import llm_client

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("autonomous_agent")

app = FastAPI(
    title="Autonomous Agent ",
    description="Minimal, reliable AI Agent that plans, validates, executes, generates DOCX reports, and self-checks.",
    version="1.0.0"
)

# Allow CORS for development convenience
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
@app.get("/health", tags=["Health"])
def health_check():
    """
    Health check and active LLM provider info.
    """
    return {
        "status": "healthy",
        "service": "Autonomous Strategy Agent",
        "llm_provider": llm_client.get_provider_name(),
        "storage_dir": str(OUTPUT_DIR)
    }


@app.post("/agent", response_model=AgentResponse, tags=["Agent"])
def process_agent_request(req: AgentRequest):
    """
    Main autonomous agent endpoint.
    Workflow:
    1. Validate request
    2. LLM Planner creates ordered TODO list & assumptions
    3. Plan validation
    4. Sequential task execution
    5. Professional Word (.docx) generation
    6. Self-check & reflection (with 1 automated repair attempt)
    7. Return full structured status and download link
    """
    try:
        response = run_agent(req.request)
        return response
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request validation or planning error: {str(ve)}"
        )
    except Exception as e:
        logger.error(f"Unhandled error during agent execution: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent internal execution failure: {str(e)}"
        )


@app.get("/download/{filename}", tags=["Documents"])
def download_document(filename: str):
    """
    Safe download endpoint for generated Word documents.
    Protects against path traversal attacks.
    """
    # Strict path traversal prevention: strip any directory components
    safe_name = os.path.basename(filename)
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename: path traversal characters detected."
        )

    file_path = (OUTPUT_DIR / safe_name).resolve()

    # Verify that the target file is strictly inside the OUTPUT_DIR
    try:
        file_path.relative_to(OUTPUT_DIR.resolve())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: cannot access files outside output directory."
        )

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{safe_name}' not found."
        )

    return FileResponse(
        path=str(file_path),
        filename=safe_name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=APP_HOST, port=APP_PORT, reload=True)
