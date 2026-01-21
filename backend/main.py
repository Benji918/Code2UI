"""
Code2UI Backend - FastAPI Application

Production-grade API for transforming OpenAPI specifications into functional Vue.js UIs.

Features:
- Multi-input ingestion (OpenAPI spec, diagrams, documentation)
- Context ranking as per implementation.md
- Mistral AI integration for UI generation
- Async processing with status tracking
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from sse_starlette.sse import EventSourceResponse
import yaml
import json
import uuid
import base64
from typing import Optional, List, AsyncGenerator
from datetime import datetime
import asyncio
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from models import (
    GenerationResponse, 
    GenerationStatus, 
    GeneratedUI,
    HealthResponse
)
from services.llm_service import MistralService
from services.tasks import generate_ui_task
from celery.result import AsyncResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Application metadata
APP_VERSION = "2.0.0"
APP_TITLE = "Code2UI Backend"
APP_DESCRIPTION = """
Transform OpenAPI specifications into production-ready Vue.js interfaces.

## Features
- **Multi-input Support**: Accept OpenAPI specs, architecture diagrams, and documentation
- **Context Ranking**: Prioritize inputs for optimal AI generation
- **Real-time Generation**: Stream generation progress and results
"""

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration - Allow Vue frontend origins
ALLOWED_ORIGINS = [
    "http://localhost:5173",    # Vite dev server
    "http://localhost:3000",    # Alternative dev port
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services (API key loaded from .env automatically)
llm_service = MistralService()

# In-memory storage for generation jobs (use Redis/DB in production)
generation_jobs: dict[str, GenerationStatus] = {}


# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

def parse_openapi_spec(content: bytes, filename: str) -> dict:
    """
    Parse OpenAPI specification from file content.
    Supports JSON and YAML formats.
    """
    try:
        if filename.endswith('.json'):
            return json.loads(content.decode('utf-8'))
        elif filename.endswith(('.yaml', '.yml')):
            return yaml.safe_load(content.decode('utf-8'))
        else:
            # Try JSON first, then YAML
            try:
                return json.loads(content.decode('utf-8'))
            except json.JSONDecodeError:
                return yaml.safe_load(content.decode('utf-8'))
    except Exception as e:
        raise ValueError(f"Failed to parse OpenAPI specification: {str(e)}")


def validate_openapi_spec(spec: dict) -> None:
    """
    Validate that the parsed content is a valid OpenAPI specification.
    """
    # Check for required OpenAPI fields
    if 'openapi' not in spec and 'swagger' not in spec:
        raise ValueError("Invalid specification: Missing 'openapi' or 'swagger' version field")
    
    if 'paths' not in spec or not spec['paths']:
        raise ValueError("Invalid specification: No API paths defined")
    
    # Validate version format
    version = spec.get('openapi') or spec.get('swagger')
    if not isinstance(version, str):
        raise ValueError("Invalid specification: Version must be a string")


async def extract_image_context(images: List[UploadFile]) -> str:
    """
    Extract context from uploaded architecture diagram images.
    
    In production, this would use vision models to describe images.
    For now, we extract metadata and filenames as context.
    """
    if not images:
        return ""
    
    context_parts = ["Architecture Diagrams Provided:"]
    
    for i, image in enumerate(images, 1):
        content = await image.read()
        await image.seek(0)  # Reset file pointer
        
        # Get image info
        size_kb = len(content) / 1024
        context_parts.append(f"  {i}. {image.filename} ({size_kb:.1f} KB)")
        
        # TODO: In production, use vision model to describe the image
        # For now, we note the file presence
    
    context_parts.append("\nNote: These diagrams show the system architecture and data flow.")
    return "\n".join(context_parts)


async def extract_doc_context(docs: List[UploadFile]) -> str:
    """
    Extract text content from uploaded documentation files.
    Supports .txt, .md, and attempts to read other text files.
    """
    if not docs:
        return ""
    
    context_parts = ["Documentation Content:"]
    
    for doc in docs:
        try:
            content = await doc.read()
            await doc.seek(0)  # Reset file pointer
            
            # Try to decode as UTF-8
            try:
                text = content.decode('utf-8')
            except UnicodeDecodeError:
                text = content.decode('latin-1')
            
            # Truncate very long documents
            if len(text) > 10000:
                text = text[:10000] + "\n... [truncated]"
            
            context_parts.append(f"\n--- {doc.filename} ---")
            context_parts.append(text)
            
        except Exception as e:
            logger.warning(f"Could not read document {doc.filename}: {e}")
            continue
    
    return "\n".join(context_parts)


# ==============================================================================
# API ENDPOINTS
# ==============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring."""
    return HealthResponse(
        status="healthy",
        service=APP_TITLE,
        version=APP_VERSION
    )


@app.post("/api/generate", response_model=GenerationResponse)
async def generate_ui(
    background_tasks: BackgroundTasks,
    spec_file: UploadFile = File(..., description="OpenAPI/Swagger specification file (JSON or YAML)"),
    project_name: str = Form("Generated API Client", description="Name for the generated project"),
    diagrams: List[UploadFile] = File(default=[], description="Architecture diagram images"),
    docs: List[UploadFile] = File(default=[], description="Documentation/README files"),
):
    """
    Generate a Vue.js UI from an OpenAPI specification.
    
    This endpoint accepts:
    - **spec_file** (required): OpenAPI/Swagger JSON or YAML file
    - **project_name**: Name for the generated project
    - **diagrams**: Optional architecture diagram images for context
    - **docs**: Optional documentation files for additional context
    
    Context is ranked by priority:
    1. OpenAPI Specification (Critical)
    2. Architecture Diagrams (High)
    3. Documentation (Medium)
    """
    generation_id = str(uuid.uuid4())
    
    try:
        # 1. Parse and validate OpenAPI spec (Priority 1 - Critical)
        logger.info(f"[{generation_id}] Parsing OpenAPI spec: {spec_file.filename}")
        spec_content = await spec_file.read()
        spec = parse_openapi_spec(spec_content, spec_file.filename)
        validate_openapi_spec(spec)
        
        # 2. Extract diagram context (Priority 2 - High)
        diagrams_context = await extract_image_context(diagrams) if diagrams else None
        logger.info(f"[{generation_id}] Diagrams context: {len(diagrams)} files")
        
        # 3. Extract documentation context (Priority 3 - Medium)
        docs_context = await extract_doc_context(docs) if docs else None
        logger.info(f"[{generation_id}] Docs context: {len(docs)} files")
        
        # 4. Generate UI using Mistral AI
        logger.info(f"[{generation_id}] Starting UI generation for project: {project_name}")
        
        generated_ui = await llm_service.generate_ui(
            openapi_spec=spec,
            project_name=project_name,
            diagrams_context=diagrams_context,
            docs_context=docs_context
        )
        
        logger.info(f"[{generation_id}] Generation complete: {len(generated_ui.components)} components")
        
        return GenerationResponse(
            status="success",
            message=f"Successfully generated {len(generated_ui.components)} components",
            generation_id=generation_id,
            ui=generated_ui
        )
        
    except ValueError as e:
        logger.error(f"[{generation_id}] Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"[{generation_id}] Generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.post("/api/generate/async", response_model=dict)
async def generate_ui_async(
    background_tasks: BackgroundTasks,
    spec_file: UploadFile = File(...),
    project_name: str = Form("Generated API Client"),
    diagrams: List[UploadFile] = File(default=[]),
    docs: List[UploadFile] = File(default=[]),
):
    """
    Start an asynchronous UI generation job.
    Returns a generation_id to poll for status.
    """
    generation_id = str(uuid.uuid4())
    
    # Store initial status
    generation_jobs[generation_id] = GenerationStatus(
        generation_id=generation_id,
        status="pending",
        progress=0,
        message="Generation queued"
    )
    
    # Read all file contents before background task
    spec_content = await spec_file.read()
    spec_filename = spec_file.filename
    
    diagram_contents = []
    for d in diagrams:
        diagram_contents.append({
            'filename': d.filename,
            'content': await d.read()
        })
    
    doc_contents = []
    for d in docs:
        doc_contents.append({
            'filename': d.filename,
            'content': await d.read()
        })
    
    # Add background task
    background_tasks.add_task(
        run_generation_job,
        generation_id,
        spec_content,
        spec_filename,
        project_name,
        diagram_contents,
        doc_contents
    )
    
    return {
        "generation_id": generation_id,
        "status": "pending",
        "message": "Generation job started. Poll /api/generate/status/{generation_id} for updates."
    }


async def run_generation_job(
    generation_id: str,
    spec_content: bytes,
    spec_filename: str,
    project_name: str,
    diagrams: list,
    docs: list
):
    """Background task to run the generation job."""
    try:
        # Update status
        generation_jobs[generation_id].status = "processing"
        generation_jobs[generation_id].progress = 10
        generation_jobs[generation_id].message = "Parsing specification..."
        
        # Parse spec
        spec = parse_openapi_spec(spec_content, spec_filename)
        validate_openapi_spec(spec)
        
        generation_jobs[generation_id].progress = 30
        generation_jobs[generation_id].message = "Processing context..."
        
        # Process diagrams context
        diagrams_context = None
        if diagrams:
            context_parts = ["Architecture Diagrams:"]
            for d in diagrams:
                context_parts.append(f"  - {d['filename']}")
            diagrams_context = "\n".join(context_parts)
        
        # Process docs context
        docs_context = None
        if docs:
            context_parts = []
            for d in docs:
                try:
                    text = d['content'].decode('utf-8')
                    context_parts.append(f"--- {d['filename']} ---\n{text}")
                except:
                    pass
            docs_context = "\n".join(context_parts) if context_parts else None
        
        generation_jobs[generation_id].progress = 50
        generation_jobs[generation_id].message = "Generating UI with AI..."
        
        # Generate UI
        generated_ui = await llm_service.generate_ui(
            openapi_spec=spec,
            project_name=project_name,
            diagrams_context=diagrams_context,
            docs_context=docs_context
        )
        
        generation_jobs[generation_id].progress = 100
        generation_jobs[generation_id].status = "completed"
        generation_jobs[generation_id].message = "Generation complete"
        generation_jobs[generation_id].result = generated_ui
        
    except Exception as e:
        logger.error(f"[{generation_id}] Background job failed: {e}")
        generation_jobs[generation_id].status = "failed"
        generation_jobs[generation_id].message = str(e)


@app.get("/api/generate/status/{generation_id}", response_model=GenerationStatus)
async def get_generation_status(generation_id: str):
    """Get the status of an async generation job."""
    if generation_id not in generation_jobs:
        raise HTTPException(status_code=404, detail="Generation job not found")
    
    return generation_jobs[generation_id]


@app.get("/api/generations", response_model=List[GenerationStatus])
async def list_generations():
    """List all generation jobs (for debugging/admin)."""
    return list(generation_jobs.values())


# ==============================================================================
# STREAMING ENDPOINTS (SSE)
# ==============================================================================

@app.post("/api/generate/stream")
async def generate_ui_stream(
    spec_file: UploadFile = File(...),
    project_name: str = Form("Generated API Client"),
    diagrams: List[UploadFile] = File(default=[]),
    docs: List[UploadFile] = File(default=[]),
):
    """
    Start a UI generation job with Celery and return task ID for streaming.
    The frontend should then connect to /api/stream/{task_id} for progress.
    """
    try:
        # Parse and validate OpenAPI spec
        spec_content = await spec_file.read()
        spec = parse_openapi_spec(spec_content, spec_file.filename)
        validate_openapi_spec(spec)
        
        # Extract context
        diagrams_context = await extract_image_context(diagrams) if diagrams else None
        docs_context = await extract_doc_context(docs) if docs else None
        
        # Start Celery task
        task = generate_ui_task.delay(
            openapi_spec=spec,
            project_name=project_name,
            diagrams_context=diagrams_context,
            docs_context=docs_context
        )
        
        return {
            "task_id": task.id,
            "status": "started",
            "message": "Connect to /api/stream/{task_id} for real-time progress"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start generation: {str(e)}")


@app.get("/api/stream/{task_id}")
async def stream_task_progress(request: Request, task_id: str):
    """
    Stream task progress using Server-Sent Events (SSE).
    Frontend connects here to receive real-time updates.
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events for task progress."""
        task = AsyncResult(task_id)
        
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                logger.info(f"Client disconnected from task {task_id}")
                break
            
            # Get task state
            state = task.state
            
            if state == 'PENDING':
                yield {
                    "event": "progress",
                    "data": json.dumps({
                        "status": "pending",
                        "progress": 0,
                        "message": "Task is queued..."
                    })
                }
            
            elif state == 'PROGRESS':
                meta = task.info
                yield {
                    "event": "progress",
                    "data": json.dumps({
                        "status": "processing",
                        "progress": meta.get('current', 0),
                        "message": meta.get('status', 'Processing...')
                    })
                }
            
            elif state == 'SUCCESS':
                result = task.result
                yield {
                    "event": "complete",
                    "data": json.dumps({
                        "status": "completed",
                        "progress": 100,
                        "result": result.get('result')
                    })
                }
                break
            
            elif state == 'FAILURE':
                yield {
                    "event": "error",
                    "data": json.dumps({
                        "status": "failed",
                        "progress": 0,
                        "message": str(task.info)
                    })
                }
                break
            
            # Wait before next update
            await asyncio.sleep(0.5)
    
    return EventSourceResponse(event_generator())


# ==============================================================================
# ERROR HANDLERS
# ==============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "An unexpected error occurred",
            "detail": str(exc) if app.debug else None
        }
    )


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
