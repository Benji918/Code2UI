from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import yaml
import json
from typing import List

from backend.models import GenerationResponse, GeneratedComponent
from backend.services.llm_service import MistralService

app = FastAPI(title="Code2UI Backend", version="1.0.0")

# Allow CORS for Vue frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm_service = MistralService()

@app.post("/api/generate", response_model=GenerationResponse)
async def generate_ui(file: UploadFile = File(...)):
    """
    Receives an OpenAPI spec file, parses it, and uses Mistral LLM (mocked) to generate UI components.
    """
    content = await file.read()
    
    # 1. Parse Spec
    try:
        if file.filename.endswith('.json'):
            spec = json.loads(content)
        elif file.filename.endswith(('.yaml', '.yml')):
            spec = yaml.safe_load(content)
        else:
            raise HTTPException(status_code=400, detail="Invalid file format. Use JSON or YAML.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse spec: {str(e)}")

    # 2. Extract Paths (Simplified RAG/Context mechanism)
    generated_components = []
    paths = spec.get('paths', {})
    
    # Limit to first 3 paths for demo/performance
    for path, methods in list(paths.items())[:3]:
        for method, details in methods.items():
            # 3. Call LLM Service
            component = await llm_service.generate_component(path, method, details)
            generated_components.append(component)

    return GenerationResponse(
        status="success",
        components=generated_components
    )

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Code2UI Backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
