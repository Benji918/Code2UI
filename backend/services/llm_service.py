import asyncio
from typing import Optional, Dict, Any
import logging
from dataclasses import dataclass
import re
import json

import os
from ollama import AsyncClient
from prompts.system_prompts import SYSTEM_PROMPT, build_generation_prompt
from models import GeneratedUI, GeneratedComponent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMService:
    """
    Production-grade LLM service for UI generation using Ollama.
    """
    
    def __init__(self):
        self.client = AsyncClient(
            host="https://ollama.com",
            headers={'Authorization': 'Bearer ' + os.environ.get('OLLAMA_API_KEY')}
        )
    
    async def generate_ui(
        self,
        openapi_spec: dict,
        project_name: str,
        diagrams_context: Optional[str] = None,
        docs_context: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> GeneratedUI:
        """
        Generate a complete Vue.js UI from OpenAPI specification.
        
        Args:
            openapi_spec: Parsed OpenAPI/Swagger specification
            project_name: Name for the generated project
            diagrams_context: Optional text description of architecture diagrams
            docs_context: Optional documentation/README content
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
        
        # Call LLM API
        update_progress(0.1, f"Reasoning with model...")
        
        try:
            response = await self._call_llm_api(user_prompt)
            update_progress(0.7, "Parsing AI response...")
            parsed_response = self._parse_response(response)
            update_progress(1.0, "Generation complete!")
            return parsed_response
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise ValueError(f"AI Response was not valid JSON: {e}")
            
        except Exception as e:
            logger.error(f"API call failed: {e}")
            raise RuntimeError(f"UI Generation failed: {e}")
    
    async def _call_llm_api(self, user_prompt: str) -> str:
        """Make the actual API call to Ollama."""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        
        logger.info("Calling Ollama API with model")
        
        # Call with stream=False to avoid async iterator issues
        # Using cloud model as requested
        response = await self.client.chat(
            model="gpt-oss:120b",
            messages=messages,
            format="json", 
            stream=False,
        )
        
        full_content = response['message']['content']
            
        logger.info(f"Received response: {len(full_content)} characters")
        
        return full_content
    
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
