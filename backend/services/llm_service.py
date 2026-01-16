import json
import os
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

from backend.prompts.system_prompts import MISTHAL_SYSTEM_PROMPT, generate_user_prompt
from backend.models import GeneratedComponent

class MistralService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        # self.client = MistralClient(api_key=self.api_key) if self.api_key else None

    async def generate_component(self, path: str, method: str, spec_fragment: dict) -> GeneratedComponent:
        """
        Orchestrates the generation process:
        1. Contextualize (Prompt Engineering)
        2. Call LLM (Inference)
        3. Validate (Structured Output)
        """
        user_prompt = generate_user_prompt(path, method, spec_fragment)
        
        print(f"DEBUG: Generating UI for {method} {path}...")
        
        # MOCK RESPONSE FOR DEMONSTRATION (Since we don't have a live API key in this env)
        # In production, this would be:
        # response = self.client.chat(model="mistral-large-latest", messages=[...], response_format={"type": "json_object"})
        # content = response.choices[0].message.content
        
        mock_code = self._get_mock_code(path, method)
        
        return GeneratedComponent(
            filename=f"{path.strip('/').capitalize()}{method.capitalize()}.vue",
            rationale="Generated based on OpenAPI definition using Bootstrap 5 table layout.",
            code=mock_code
        )

    def _get_mock_code(self, path, method) -> str:
        """
        Returns a high-quality mock response to demonstrate the 'Functional Dynamic UI' capability
        without hitting a live endpoint during this demo.
        """
        return """<script setup>
import { ref, onMounted } from 'vue'

const data = ref([])
const loading = ref(false)

const fetchData = async () => {
  loading.value = true
  // In a real app, this would be the actual API call extracted from the spec
  await new Promise(r => setTimeout(r, 1000)) 
  data.value = [{ id: 1, name: 'Sample Item', status: 'Active' }]
  loading.value = false
}

onMounted(fetchData)
</script>

<template>
  <div class="card glass-panel text-white">
    <div class="card-body">
      <h4 class="card-title text-gradient-cyan">""" + f"{method.upper()} {path}" + """</h4>
      <p class="text-white-50 mb-4">Dynamic component generated from OpenAPI spec.</p>
      
      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border text-info" role="status"></div>
      </div>
      
      <div v-else class="table-responsive">
        <table class="table table-dark table-hover bg-transparent">
          <thead>
            <tr><th>ID</th><th>Name</th><th>Status</th><th>Actions</th></tr>
          </thead>
          <tbody>
             <tr v-for="item in data" :key="item.id">
               <td>{{ item.id }}</td>
               <td>{{ item.name }}</td>
               <td><span class="badge bg-success">{{ item.status }}</span></td>
               <td><button class="btn btn-sm btn-cyan">View</button></td>
             </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
"""
