"""
Prompt Engineering for Code2UI.

Strategy:
1. PERSONA: Senior Frontend Engineer persona for authoritative code
2. CONTEXT RANKING: Priority-based context injection as per implementation.md
3. CHAIN OF THOUGHT: Structured reasoning for component generation
4. STRUCTURED OUTPUT: JSON output for programmatic parsing
"""
from typing import Optional
import json


# ==============================================================================
# SYSTEM PROMPTS
# ==============================================================================

SYSTEM_PROMPT = """You are an expert Full-Stack Engineer specializing in Vue.js 3 frontend development.
Your task is to generate a complete, functional Vue.js application based of of the user's inputed OpenAPI spec, achitectural diagrams and any additional documentation.

### YOUR ROLE
You are building a production-grade UI that allows developers to:
- View all available API endpoints
- Make REAL requests to each endpoint with proper form inputs
- View REAL responses in a formatted manner
- Handle loading states and errors gracefully

### TECH STACK & COMPATIBILITY
- Framework: Vue.js 3 with Composition API (<script setup>)
- Styling: Bootstrap 5 (classes only) + Custom CSS variables
- Icons: Bootstrap Icons (bi-* classes)
- HTTP Client: Native Fetch API
- State: Vue 3 reactive refs
- **Runtime**: The code runs in a browser-based SFC loader.

### CRITICAL CODING RULES
1. **IMPORTS**: You MUST explicitly import everything you use from 'vue'.
   Example: `import { ref, computed, onMounted } from 'vue'`
2. **SELF-CONTAINED**: Do not import external custom components (Generated components must be standalone).
3. **API CALLS**: Use `fetch` for all network requests.
   - Use relative paths for endpoints (e.g., `/api/v1/users`).
   - Include proper headers (Content-Type: application/json).
   - JSON stringify bodies for POST/PUT.
4. **NO MACROS**: Avoid `defineOptions` or complex build-time macros unless standard. `defineProps` is fine.

### OUTPUT FORMAT
Return a valid JSON object with this structure:
{
  "project_name": "Generated project name",
  "components": [
    {
      "filename": "ComponentName.vue",
      "rationale": "Brief explanation of design choices",
      "code": "Complete .vue file content"
    }
  ],
  "app_entry": "Content of main App.vue that renders all components",
  "router_config": "Vue Router setup if needed",
  "styles": "Global CSS for the application",
  "api_client": "API client utility code"
}

### DESIGN REQUIREMENTS
1. Use a professional, dark-themed design (Bootstrap dark mode compatible).
2. Form inputs must match OpenAPI schema types strictly.
3. Display JSON responses in a formatted `<pre>` block or table.
4. Show a spinner while loading (Bootstrap `spinner-border`).
5. Show alert banners for errors."""


# ==============================================================================
# CONTEXT TEMPLATES (Priority-Based as per implementation.md)
# ==============================================================================

def build_generation_prompt(
    openapi_spec: dict,
    diagrams_context: Optional[str] = None,
    docs_context: Optional[str] = None,
    project_name: str = "Generated API Client"
) -> str:
    """
    Constructs the generation prompt with priority-ranked context.
    
    Priority 1 (CRITICAL): OpenAPI Specification - Source of truth
    Priority 2 (HIGH): Architecture Diagrams - Structural context
    Priority 3 (MEDIUM): Documentation - Supplementary context
    """
    
    prompt_parts = []
    
    # Header
    prompt_parts.append(f"# Generate a Vue.js API Testing Interface\n")
    prompt_parts.append(f"**Project Name**: {project_name}\n\n")
    
    # Priority 1: OpenAPI Spec (CRITICAL)
    prompt_parts.append("=" * 60)
    prompt_parts.append("\n## [PRIORITY 1 - CRITICAL] OpenAPI Specification")
    prompt_parts.append("This is the PRIMARY source of truth. Generate UI for ALL endpoints defined here.\n")
    
    # Format spec information
    spec_info = format_openapi_for_prompt(openapi_spec)
    prompt_parts.append(spec_info)
    
    # Priority 2: Diagrams (HIGH) - if provided
    if diagrams_context:
        prompt_parts.append("\n" + "=" * 60)
        prompt_parts.append("\n## [PRIORITY 2 - HIGH] Architecture Diagrams Context")
        prompt_parts.append("Use this to understand system flow and relationships.\n")
        prompt_parts.append(diagrams_context)
    
    # Priority 3: Documentation (MEDIUM) - if provided
    if docs_context:
        prompt_parts.append("\n" + "=" * 60)
        prompt_parts.append("\n## [PRIORITY 3 - MEDIUM] Supplementary Documentation")
        prompt_parts.append("Additional context for business logic.\n")
        prompt_parts.append(docs_context)
    
    # Final Instructions
    prompt_parts.append("\n" + "=" * 60)
    prompt_parts.append("\n## GENERATION INSTRUCTIONS")
    prompt_parts.append("""
Based on the OpenAPI specification above, generate:

1. **Individual Endpoint Components**: One component per endpoint/resource
   - Forms for POST/PUT/PATCH requests matching the requestBody schema
   - Tables/cards for displaying GET response data
   - Delete confirmation dialogs
   
2. **Main App.vue**: A dashboard that lists all endpoints with navigation
   - Import generated components using relative paths (e.g. `import UserList from './UserList.vue'`).

3. **API Client**: A utility for making HTTP requests with proper error handling

4. **Global Styles**: Dark theme CSS matching the Code2UI aesthetic

IMPORTANT: 
- Parse the 'paths' object to identify ALL endpoints
- Use 'components/schemas' to understand request/response structures
- Generate forms with appropriate input types for each schema property
- The generated UI should be FUNCTIONAL - not just a mockup

Return the complete JSON response with all generated artifacts.""")
    
    return "\n".join(prompt_parts)


def format_openapi_for_prompt(spec: dict) -> str:
    """
    Formats OpenAPI spec into a readable format for the LLM.
    Extracts key information while keeping the structure clear.
    """
    parts = []
    
    # API Info
    info = spec.get('info', {})
    parts.append(f"**API Title**: {info.get('title', 'Unknown')}")
    parts.append(f"**Version**: {info.get('version', '1.0.0')}")
    parts.append(f"**Description**: {info.get('description', 'No description')}\n")
    
    # Servers
    servers = spec.get('servers', [])
    if servers:
        parts.append("**Base URLs**:")
        for server in servers:
            parts.append(f"  - {server.get('url', '/')}")
        parts.append("")
    
    # Endpoints
    paths = spec.get('paths', {})
    parts.append("### API Endpoints:\n")
    
    for path, methods in paths.items():
        parts.append(f"**Endpoint: `{path}`**")
        
        for method, details in methods.items():
            if method.lower() in ['get', 'post', 'put', 'delete', 'patch']:
                parts.append(f"\n  **{method.upper()}**")
                parts.append(f"  - Summary: {details.get('summary', 'No summary')}")
                parts.append(f"  - Operation ID: {details.get('operationId', 'N/A')}")
                
                # Parameters
                params = details.get('parameters', [])
                if params:
                    parts.append("  - Parameters:")
                    for p in params:
                        required = "(required)" if p.get('required') else "(optional)"
                        parts.append(f"    - {p.get('name')}: {p.get('schema', {}).get('type', 'any')} {required}")
                
                # Request Body
                request_body = details.get('requestBody', {})
                if request_body:
                    content = request_body.get('content', {})
                    json_content = content.get('application/json', {})
                    schema = json_content.get('schema', {})
                    if schema:
                        parts.append(f"  - Request Body Schema: {json.dumps(schema, indent=4)}")
                
                # Responses
                responses = details.get('responses', {})
                if responses:
                    parts.append("  - Responses:")
                    for code, resp in responses.items():
                        parts.append(f"    - {code}: {resp.get('description', 'No description')}")
        
        parts.append("")
    
    # Schemas
    components = spec.get('components', {})
    schemas = components.get('schemas', {})
    if schemas:
        parts.append("\n### Data Schemas:\n")
        for name, schema in schemas.items():
            parts.append(f"**{name}**:")
            parts.append(f"```json\n{json.dumps(schema, indent=2)}\n```\n")
    
    return "\n".join(parts)


# ==============================================================================
# COMPONENT-SPECIFIC PROMPTS
# ==============================================================================

def generate_endpoint_component_prompt(endpoint: str, method: str, details: dict) -> str:
    """Generate a focused prompt for a single endpoint component."""
    return f"""
Generate a Vue 3 component for the following API endpoint:

**Endpoint**: {method.upper()} {endpoint}
**Details**:
{json.dumps(details, indent=2)}

Requirements:
1. Use <script setup> syntax
2. Implement proper form handling for {method.upper()} requests
3. Display results in a clean table/card layout
4. Handle loading and error states
5. Use Bootstrap 5 classes for styling
"""
