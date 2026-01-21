"""
Pydantic models for Code2UI API.
Production-grade data validation for input/output.
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from enum import Enum


class InputPriority(str, Enum):
    """Priority levels for context ranking as per implementation.md"""
    CRITICAL = "critical"   # Priority 1: OpenAPI Spec
    HIGH = "high"           # Priority 2: Architecture Diagrams
    MEDIUM = "medium"       # Priority 3: Text Documentation


class GeneratedComponent(BaseModel):
    """A single generated Vue.js component"""
    filename: str = Field(..., description="Suggested filename, e.g. 'UserDashboard.vue'")
    rationale: str = Field(..., description="Explanation of design choices")
    code: str = Field(..., description="Complete Vue.js component code")

    @field_validator('code')
    @classmethod
    def validate_code_structure(cls, v: str) -> str:
        if '<script' not in v and '<template>' not in v:
            raise ValueError("Code must include Vue template or script sections")
        return v


class GeneratedUI(BaseModel):
    """Complete generated UI response with all artifacts"""
    project_name: str = Field(..., description="Name of the generated project")
    components: List[GeneratedComponent] = Field(default_factory=list)
    app_entry: Optional[str] = Field(None, description="Main App.vue content")
    router_config: Optional[str] = Field(None, description="Vue Router configuration")
    styles: Optional[str] = Field(None, description="Global CSS styles")
    api_client: Optional[str] = Field(None, description="Generated API client code")


class GenerationRequest(BaseModel):
    """Request payload for UI generation"""
    project_name: str = Field(..., description="Name for the generated project")
    openapi_spec: str = Field(..., description="OpenAPI/Swagger JSON content")
    diagrams_context: Optional[str] = Field(None, description="Text description of architecture diagrams")
    docs_context: Optional[str] = Field(None, description="README or documentation content")


class GenerationResponse(BaseModel):
    """Response from the generation endpoint"""
    status: str = Field(..., description="Status: 'success' or 'error'")
    message: Optional[str] = Field(None, description="Status message or error details")
    generation_id: str = Field(..., description="Unique ID for this generation")
    ui: Optional[GeneratedUI] = Field(None, description="Generated UI artifacts")


class GenerationStatus(BaseModel):
    """Status of an in-progress generation"""
    generation_id: str
    status: str  # 'pending', 'processing', 'completed', 'failed'
    progress: int = Field(default=0, ge=0, le=100)
    message: Optional[str] = None
    result: Optional[GeneratedUI] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
