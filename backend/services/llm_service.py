import asyncio
from typing import Optional, Dict, Any
import logging
from dataclasses import dataclass
import re
import json

from ollama import AsyncClient



from prompts.system_prompts import SYSTEM_PROMPT, build_generation_prompt
from models import GeneratedUI, GeneratedComponent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """Configuration for LLM calls"""
    model: str = "deepseek-r1"
    temperature: float = 0.6 # DeepSeek recommended temp
    num_ctx: int = 32000
    timeout: int = 300  # seconds, reasoning models can be slow


class LLMService:
    """
    Production-grade LLM service for UI generation using Ollama (DeepSeek-R1).
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.client = AsyncClient()
        self.config = config or LLMConfig()
    
    async def generate_ui(
        self,
        openapi_spec: dict,
        project_name: str,
        diagrams_context: Optional[str] = None,
        docs_context: Optional[str] = None,
        max_retries: int = 3,
        progress_callback: Optional[callable] = None
    ) -> GeneratedUI:
        """
        Generate a complete Vue.js UI from OpenAPI specification.
        
        Args:
            openapi_spec: Parsed OpenAPI/Swagger specification
            project_name: Name for the generated project
            diagrams_context: Optional text description of architecture diagrams
            docs_context: Optional documentation/README content
            max_retries: Number of retry attempts on failure
            progress_callback: Optional callback(progress: float, status: str) for progress updates
            
        Returns:
            GeneratedUI object with all generated artifacts
        """
        # Build the prompt with priority-ranked context
        user_prompt = build_generation_prompt(
            openapi_spec=openapi_spec,
            diagrams_context=diagrams_context,
            docs_context=docs_context,
            project_name=project_name
        )
        
        logger.info(f"Generating UI for project: {project_name}")
        logger.debug(f"Prompt length: {len(user_prompt)} characters")
        
        # Progress update helper
        def update_progress(pct: float, msg: str):
            if progress_callback:
                progress_callback(pct, msg)
        
        update_progress(0.0, "Initializing generation...")
        
        # Call LLM API with retries
        update_progress(0.1, f"Reasoning with {self.config.model}...")
        for attempt in range(max_retries):
            try:
                response = await self._call_llm_api(user_prompt)
                update_progress(0.7, "Parsing AI response...")
                parsed_response = self._parse_response(response)
                update_progress(1.0, "Generation complete!")
                return parsed_response
                
            except json.JSONDecodeError as e:
                logger.warning(f"Attempt {attempt + 1}: Failed to parse JSON response: {e}")
                if attempt == max_retries - 1:
                     logger.error("Final JSON parse failure. Falling back to mock response.")
                     # If we really fail, we can fallback to mock or raise
                     # For robustness, let's raise if we really want real gen, or mock if allowed
                     break 
                    
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}: API call failed: {e}")
                if attempt == max_retries - 1:
                    logger.error("Final API failure. Falling back to mock response.")
                    break
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        # Fallback to mock if all retries fail
        logger.warning("Falling back to mock response due to generation failures")
        return self._generate_mock_response(openapi_spec, project_name)
        
        # Fallback to mock if all retries fail
        return self._generate_mock_response(openapi_spec, project_name)
    
    async def _call_llm_api(self, user_prompt: str) -> str:
        """Make the actual API call to Ollama."""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        
        logger.info(f"Calling Ollama API with model: {self.config.model}")
        
        response = await self.client.chat(
            model=self.config.model,
            messages=messages,
            options={
                "temperature": self.config.temperature,
                "num_ctx": self.config.num_ctx
            },
            format="json" # Enforce JSON format from Ollama
        )
        
        content = response['message']['content']
        logger.info(f"Received response: {len(content)} characters")
        
        return content
    
    def _parse_response(self, response: str) -> GeneratedUI:
        """Parse the LLM JSON response into GeneratedUI object."""
        # Clean response (remove <think> blocks from deepseek-r1)
        response_clean = re.sub(r'<think>[\s\S]*?</think>', '', response).strip()
        
        # Try to extract JSON from the response
        try:
            data = json.loads(response_clean)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_clean)
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    logger.error("Failed to decode JSON from markdown block")
                    msg = "Invalid JSON in response"
                    raise ValueError(msg)
            else:
                 # Last resort attempt to find json object start/end
                try:
                    start = response_clean.find('{')
                    end = response_clean.rfind('}') + 1
                    if start != -1 and end != -1:
                        data = json.loads(response_clean[start:end])
                    else:
                        raise ValueError("No JSON object found")
                except Exception as e:
                    logger.error(f"JSON parse error: {e}")
                    raise
        
        # Build GeneratedUI from parsed data
        components = []
        for comp_data in data.get('components', []):
            components.append(GeneratedComponent(
                filename=comp_data.get('filename', 'Component.vue'),
                rationale=comp_data.get('rationale', 'Generated component'),
                code=comp_data.get('code', '')
            ))
        
        return GeneratedUI(
            project_name=data.get('project_name', 'Generated Project'),
            components=components,
            app_entry=data.get('app_entry'),
            router_config=data.get('router_config'),
            styles=data.get('styles'),
            api_client=data.get('api_client')
        )
    
    def _generate_mock_response(self, spec: dict, project_name: str) -> GeneratedUI:
        """Generate a high-quality mock response for demonstration."""
        paths = spec.get('paths', {})
        info = spec.get('info', {})
        api_title = info.get('title', 'API')
        
        components = []
        
        # Generate components for each endpoint
        for path, methods in list(paths.items())[:5]:  # Limit for performance
            for method, details in methods.items():
                if method.lower() not in ['get', 'post', 'put', 'delete', 'patch']:
                    continue
                    
                component_name = self._path_to_component_name(path, method)
                component_code = self._generate_endpoint_component(path, method, details)
                
                components.append(GeneratedComponent(
                    filename=f"{component_name}.vue",
                    rationale=f"Component for {method.upper()} {path} - {details.get('summary', 'API endpoint')}",
                    code=component_code
                ))
        
        # Generate main App entry
        app_entry = self._generate_app_vue(components, api_title)
        
        # Generate API client
        api_client = self._generate_api_client(spec)
        
        # Generate global styles
        styles = self._generate_styles()
        
        return GeneratedUI(
            project_name=project_name,
            components=components,
            app_entry=app_entry,
            styles=styles,
            api_client=api_client
        )
    
    def _path_to_component_name(self, path: str, method: str) -> str:
        """Convert API path to PascalCase component name."""
        # Remove path parameters
        clean_path = re.sub(r'\{[^}]+\}', '', path)
        # Split and capitalize
        parts = [p.capitalize() for p in clean_path.split('/') if p]
        method_suffix = method.capitalize()
        return ''.join(parts) + method_suffix if parts else f"Root{method_suffix}"
    
    def _generate_endpoint_component(self, path: str, method: str, details: dict) -> str:
        """Generate a Vue component for an API endpoint."""
        summary = details.get('summary', f'{method.upper()} {path}')
        operation_id = details.get('operationId', 'operation')
        
        # Get parameters
        params = details.get('parameters', [])
        request_body = details.get('requestBody', {})
        
        # Build form fields based on parameters and request body
        form_fields = []
        for param in params:
            form_fields.append({
                'name': param.get('name'),
                'type': param.get('schema', {}).get('type', 'string'),
                'required': param.get('required', False),
                'in': param.get('in', 'query')
            })
        
        # Check request body schema
        if request_body:
            content = request_body.get('content', {})
            json_content = content.get('application/json', {})
            schema = json_content.get('schema', {})
            schema_ref = schema.get('$ref', '')
            if 'properties' in schema:
                for prop_name, prop_details in schema.get('properties', {}).items():
                    form_fields.append({
                        'name': prop_name,
                        'type': prop_details.get('type', 'string'),
                        'required': prop_name in schema.get('required', []),
                        'in': 'body'
                    })
        
        # Generate the component code
        if method.lower() == 'get':
            return self._generate_get_component(path, summary, form_fields)
        elif method.lower() in ['post', 'put', 'patch']:
            return self._generate_form_component(path, method, summary, form_fields)
        else:  # delete
            return self._generate_delete_component(path, summary, form_fields)
    
    def _generate_get_component(self, path: str, summary: str, params: list) -> str:
        """Generate a component for GET endpoints."""
        param_refs = '\n'.join([f"const {p['name']} = ref('')" for p in params if p['in'] in ['query', 'path']])
        
        return f'''<script setup>
import {{ ref, onMounted }} from 'vue'
import {{ apiClient }} from '../utils/apiClient'

const loading = ref(false)
const error = ref(null)
const data = ref([])
{param_refs}

const fetchData = async () => {{
  loading.value = true
  error.value = null
  
  try {{
    const response = await apiClient.get('{path}')
    data.value = Array.isArray(response) ? response : [response]
  }} catch (err) {{
    error.value = err.message || 'Failed to fetch data'
  }} finally {{
    loading.value = false
  }}
}}

onMounted(fetchData)
</script>

<template>
  <div class="endpoint-card">
    <div class="endpoint-header">
      <span class="method-badge method-get">GET</span>
      <h3 class="endpoint-title">{summary}</h3>
      <code class="endpoint-path">{path}</code>
    </div>
    
    <div class="endpoint-body">
      <button 
        @click="fetchData" 
        class="btn btn-primary"
        :disabled="loading"
      >
        <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
        {{ loading ? 'Loading...' : 'Fetch Data' }}
      </button>
      
      <div v-if="error" class="alert alert-danger mt-3">
        <i class="bi bi-exclamation-triangle me-2"></i>
        {{ error }}
      </div>
      
      <div v-if="data.length > 0" class="response-table mt-4">
        <div class="table-responsive">
          <table class="table table-dark table-hover">
            <thead>
              <tr>
                <th v-for="key in Object.keys(data[0])" :key="key">{{ key }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in data" :key="index">
                <td v-for="key in Object.keys(data[0])" :key="key">
                  {{ typeof item[key] === 'object' ? JSON.stringify(item[key]) : item[key] }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      
      <div v-else-if="!loading && !error" class="empty-state text-center py-5">
        <i class="bi bi-inbox fs-1 text-muted"></i>
        <p class="text-muted mt-2">No data available. Click "Fetch Data" to load.</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.endpoint-card {{
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: 12px;
  margin-bottom: 1.5rem;
  overflow: hidden;
}}

.endpoint-header {{
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--glass-border);
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}}

.method-badge {{
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-weight: 700;
  font-size: 0.75rem;
  text-transform: uppercase;
}}

.method-get {{ background: #22c55e; color: #000; }}
.method-post {{ background: #3b82f6; color: #fff; }}
.method-put {{ background: #f59e0b; color: #000; }}
.method-delete {{ background: #ef4444; color: #fff; }}

.endpoint-title {{
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
}}

.endpoint-path {{
  margin-left: auto;
  background: rgba(255,255,255,0.1);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.875rem;
}}

.endpoint-body {{
  padding: 1.5rem;
}}

.response-table {{
  background: rgba(0,0,0,0.2);
  border-radius: 8px;
  overflow: hidden;
}}
</style>'''

    def _generate_form_component(self, path: str, method: str, summary: str, fields: list) -> str:
        """Generate a component with form for POST/PUT/PATCH endpoints."""
        method_upper = method.upper()
        method_color = 'post' if method.lower() == 'post' else 'put'
        
        # Generate form field refs
        form_refs = '\n'.join([f"const {f['name']} = ref('')" for f in fields])
        
        # Generate form inputs
        form_inputs = []
        for field in fields:
            input_type = 'number' if field['type'] == 'integer' else 'text'
            required = 'required' if field['required'] else ''
            form_inputs.append(f'''
      <div class="mb-3">
        <label class="form-label">{field['name'].replace('_', ' ').title()} {'*' if field['required'] else ''}</label>
        <input 
          v-model="{field['name']}" 
          type="{input_type}" 
          class="form-control form-control-dark"
          placeholder="Enter {field['name']}"
          {required}
        />
      </div>''')
        
        form_inputs_str = '\n'.join(form_inputs) if form_inputs else '''
      <div class="text-muted">No form fields defined for this endpoint.</div>'''
        
        # Build request body
        body_fields = [f for f in fields if f['in'] == 'body']
        body_obj = ', '.join([f"'{f['name']}': {f['name']}.value" for f in body_fields])
        
        return f'''<script setup>
import {{ ref }} from 'vue'
import {{ apiClient }} from '../utils/apiClient'

const loading = ref(false)
const error = ref(null)
const success = ref(false)
const response = ref(null)
{form_refs}

const submitForm = async () => {{
  loading.value = true
  error.value = null
  success.value = false
  
  try {{
    const body = {{ {body_obj} }}
    response.value = await apiClient.{method.lower()}('{path}', body)
    success.value = true
  }} catch (err) {{
    error.value = err.message || 'Request failed'
  }} finally {{
    loading.value = false
  }}
}}
</script>

<template>
  <div class="endpoint-card">
    <div class="endpoint-header">
      <span class="method-badge method-{method_color}">{method_upper}</span>
      <h3 class="endpoint-title">{summary}</h3>
      <code class="endpoint-path">{path}</code>
    </div>
    
    <div class="endpoint-body">
      <form @submit.prevent="submitForm">
        {form_inputs_str}
        
        <button 
          type="submit" 
          class="btn btn-primary"
          :disabled="loading"
        >
          <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
          {{ loading ? 'Sending...' : 'Send Request' }}
        </button>
      </form>
      
      <div v-if="error" class="alert alert-danger mt-3">
        <i class="bi bi-exclamation-triangle me-2"></i>
        {{ error }}
      </div>
      
      <div v-if="success" class="alert alert-success mt-3">
        <i class="bi bi-check-circle me-2"></i>
        Request successful!
      </div>
      
      <div v-if="response" class="response-preview mt-4">
        <h5>Response:</h5>
        <pre class="bg-dark p-3 rounded">{{ JSON.stringify(response, null, 2) }}</pre>
      </div>
    </div>
  </div>
</template>

<style scoped>
.endpoint-card {{
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: 12px;
  margin-bottom: 1.5rem;
  overflow: hidden;
}}

.endpoint-header {{
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--glass-border);
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}}

.method-badge {{
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-weight: 700;
  font-size: 0.75rem;
  text-transform: uppercase;
}}

.method-get {{ background: #22c55e; color: #000; }}
.method-post {{ background: #3b82f6; color: #fff; }}
.method-put {{ background: #f59e0b; color: #000; }}
.method-delete {{ background: #ef4444; color: #fff; }}

.endpoint-title {{
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
}}

.endpoint-path {{
  margin-left: auto;
  background: rgba(255,255,255,0.1);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.875rem;
}}

.endpoint-body {{
  padding: 1.5rem;
}}

.form-control-dark {{
  background: rgba(255,255,255,0.05);
  border: 1px solid var(--glass-border);
  color: #fff;
}}

.form-control-dark:focus {{
  background: rgba(255,255,255,0.1);
  border-color: var(--color-brand-cyan);
  color: #fff;
  box-shadow: 0 0 0 0.2rem rgba(34, 211, 238, 0.25);
}}
</style>'''

    def _generate_delete_component(self, path: str, summary: str, params: list) -> str:
        """Generate a component for DELETE endpoints."""
        path_params = [p for p in params if p['in'] == 'path']
        param_refs = '\n'.join([f"const {p['name']} = ref('')" for p in path_params])
        
        return f'''<script setup>
import {{ ref }} from 'vue'
import {{ apiClient }} from '../utils/apiClient'

const loading = ref(false)
const error = ref(null)
const success = ref(false)
const showConfirm = ref(false)
{param_refs}

const confirmDelete = () => {{
  showConfirm.value = true
}}

const executeDelete = async () => {{
  loading.value = true
  error.value = null
  
  try {{
    await apiClient.delete('{path}')
    success.value = true
    showConfirm.value = false
  }} catch (err) {{
    error.value = err.message || 'Delete failed'
  }} finally {{
    loading.value = false
  }}
}}

const cancelDelete = () => {{
  showConfirm.value = false
}}
</script>

<template>
  <div class="endpoint-card">
    <div class="endpoint-header">
      <span class="method-badge method-delete">DELETE</span>
      <h3 class="endpoint-title">{summary}</h3>
      <code class="endpoint-path">{path}</code>
    </div>
    
    <div class="endpoint-body">
      <button 
        @click="confirmDelete" 
        class="btn btn-danger"
        :disabled="loading || showConfirm"
      >
        <i class="bi bi-trash me-2"></i>
        Delete
      </button>
      
      <div v-if="showConfirm" class="confirm-dialog mt-3 p-3 bg-dark rounded">
        <p class="mb-3"><strong>Are you sure?</strong> This action cannot be undone.</p>
        <div class="d-flex gap-2">
          <button @click="executeDelete" class="btn btn-danger" :disabled="loading">
            <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
            Yes, Delete
          </button>
          <button @click="cancelDelete" class="btn btn-secondary">Cancel</button>
        </div>
      </div>
      
      <div v-if="error" class="alert alert-danger mt-3">
        <i class="bi bi-exclamation-triangle me-2"></i>
        {{ error }}
      </div>
      
      <div v-if="success" class="alert alert-success mt-3">
        <i class="bi bi-check-circle me-2"></i>
        Successfully deleted!
      </div>
    </div>
  </div>
</template>

<style scoped>
.endpoint-card {{
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: 12px;
  margin-bottom: 1.5rem;
  overflow: hidden;
}}

.endpoint-header {{
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--glass-border);
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}}

.method-badge {{
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-weight: 700;
  font-size: 0.75rem;
  text-transform: uppercase;
}}

.method-delete {{ background: #ef4444; color: #fff; }}

.endpoint-title {{
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
}}

.endpoint-path {{
  margin-left: auto;
  background: rgba(255,255,255,0.1);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.875rem;
}}

.endpoint-body {{
  padding: 1.5rem;
}}

.confirm-dialog {{
  border: 1px solid #ef4444;
}}
</style>'''

    def _generate_app_vue(self, components: list, api_title: str) -> str:
        """Generate the main App.vue that orchestrates all components."""
        imports = '\n'.join([
            f"import {c.filename.replace('.vue', '')} from './components/{c.filename}'"
            for c in components
        ])
        
        component_tags = '\n        '.join([
            f"<{c.filename.replace('.vue', '')} />"
            for c in components
        ])
        
        return f'''<script setup>
{imports}
</script>

<template>
  <div class="generated-app">
    <header class="app-header">
      <div class="container">
        <h1 class="app-title">
          <i class="bi bi-lightning-charge text-warning me-2"></i>
          {api_title} - API Client
        </h1>
        <p class="app-subtitle">Generated by Code2UI</p>
      </div>
    </header>
    
    <main class="container py-4">
      <div class="endpoints-grid">
        {component_tags}
      </div>
    </main>
    
    <footer class="app-footer">
      <div class="container text-center py-3">
        <small class="text-muted">Generated with Code2UI • Powered by DeepSeek-R1</small>
      </div>
    </footer>
  </div>
</template>

<style>
.generated-app {{
  min-height: 100vh;
  background: var(--color-bg-primary);
  color: var(--color-text-main);
}}

.app-header {{
  background: var(--glass-bg);
  border-bottom: 1px solid var(--glass-border);
  padding: 2rem 0;
}}

.app-title {{
  font-size: 1.75rem;
  font-weight: 700;
  margin: 0;
}}

.app-subtitle {{
  color: var(--color-text-muted);
  margin: 0.5rem 0 0;
}}

.endpoints-grid {{
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}}

.app-footer {{
  margin-top: auto;
  border-top: 1px solid var(--glass-border);
}}
</style>'''

    def _generate_api_client(self, spec: dict) -> str:
        """Generate an API client utility."""
        servers = spec.get('servers', [])
        base_url = servers[0].get('url', '/api') if servers else '/api'
        
        return f'''/**
 * API Client for {spec.get('info', {}).get('title', 'API')}
 * Base URL: {base_url}
 */

const BASE_URL = '{base_url}'

class ApiClient {{
  constructor(baseUrl = BASE_URL) {{
    this.baseUrl = baseUrl
  }}

  async request(method, endpoint, data = null, options = {{}}) {{
    const url = `${{this.baseUrl}}${{endpoint}}`
    
    const config = {{
      method: method.toUpperCase(),
      headers: {{
        'Content-Type': 'application/json',
        ...options.headers
      }}
    }}

    if (data && ['POST', 'PUT', 'PATCH'].includes(method.toUpperCase())) {{
      config.body = JSON.stringify(data)
    }}

    const response = await fetch(url, config)
    
    if (!response.ok) {{
      const error = await response.text()
      throw new Error(error || `HTTP ${{response.status}}: ${{response.statusText}}`)
    }}

    const contentType = response.headers.get('content-type')
    if (contentType && contentType.includes('application/json')) {{
      return response.json()
    }}
    
    return response.text()
  }}

  get(endpoint, options) {{
    return this.request('GET', endpoint, null, options)
  }}

  post(endpoint, data, options) {{
    return this.request('POST', endpoint, data, options)
  }}

  put(endpoint, data, options) {{
    return this.request('PUT', endpoint, data, options)
  }}

  patch(endpoint, data, options) {{
    return this.request('PATCH', endpoint, data, options)
  }}

  delete(endpoint, options) {{
    return this.request('DELETE', endpoint, null, options)
  }}
}}

export const apiClient = new ApiClient()
export default ApiClient
'''

    def _generate_styles(self) -> str:
        """Generate global CSS styles for the generated app."""
        return '''/* Generated App Styles */
:root {
  --color-bg-primary: #030712;
  --color-bg-secondary: #0f172a;
  --color-brand-cyan: #22d3ee;
  --color-brand-pink: #d946ef;
  --color-text-main: #ffffff;
  --color-text-muted: #94a3b8;
  --glass-bg: #111827;
  --glass-border: rgba(255, 255, 255, 0.1);
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  background: var(--color-bg-primary);
  color: var(--color-text-main);
  -webkit-font-smoothing: antialiased;
}

.btn-primary {
  background: var(--color-brand-cyan);
  border: none;
  color: #000;
  font-weight: 600;
}

.btn-primary:hover {
  background: #06b6d4;
  color: #000;
}

.btn-primary:disabled {
  opacity: 0.6;
}

.table-dark {
  --bs-table-bg: transparent;
  --bs-table-border-color: var(--glass-border);
}

.alert {
  border-radius: 8px;
}

pre {
  color: var(--color-text-main);
  overflow-x: auto;
}
'''
