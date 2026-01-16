from pydantic import BaseModel, Field, validator
from typing import List, Optional

class GeneratedComponent(BaseModel):
    filename: str = Field(..., description="The suggested filename for the component, e.g. 'UserDashboard.vue'")
    rationale: str = Field(..., description="Explanation of why this UI structure was chosen")
    code: str = Field(..., description="The complete Vue.js component code")

    @validator('code')
    def validate_code_structure(cls, v):
        if '<script setup>' not in v:
            raise ValueError("Code must use Vue 3 <script setup> syntax")
        if '<template>' not in v:
            raise ValueError("Code must include a <template> section")
        return v

class OpenApiSpecPayload(BaseModel):
    spec_content: str
    project_name: str

class GenerationResponse(BaseModel):
    status: str
    components: List[GeneratedComponent]
