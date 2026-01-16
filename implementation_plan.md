# Implementation Plan: AI-Powered UI Generator (Code2UI)

## 1. Architecture Overview
We will build a **Python/FastAPI** backend to handle the heavy lifting of parsing OpenAPI specs, managing the Vector DB (RAG), and interacting with the Mistral LLM. The Vue.js frontend will communicate with this backend.

### Tech Stack
-   **Frontend**: Vue 3 + Bootstrap (Existing)
-   **Backend**: Python 3.11+ (FastAPI)
-   **LLM**: Mistral AI (via API or local weights)
-   **Orchestration**: LangChain (for RAG & Prompt Chaining)
-   **Vector DB**: ChromaDB (Local, persistent)
-   **Validation**: Pydantic (Output parsing), Black (Code formatting)

## 2. Core Modules

### A. RAG Engine (`backend/rag_service.py`)
*   **Goal**: Retrieve relevant UI component examples based on the API endpoint type (e.g., if parsing a `/users` GET endpoint, retrieve "Data Table" component examples).
*   **Data**: We will seed the Vector DB with high-quality Vue/Bootstrap component snippets ("Golden Examples").

### B. Prompt Engineering Strategy (`backend/prompts.py`)
We will use **Chain-of-Thought (CoT)** and **Few-Shot Prompting**.
1.  **Phase 1: Analysis**: LLM scans the OpenAPI spec to understand the domain, entities, and relationships.
2.  **Phase 2: Blueprinting**: LLM plans the component hierarchy (NavBar, Sidebar, Views provided in the spec).
3.  **Phase 3: Coding**: LLM generates the Vue.js code using the retrieved examples (RAG) as a style guide.

### C. Validation Layer (`backend/validation.py`)
*   **Syntax Check**: Ensure generated code is valid Vue/HTML.
*   **Spec Compliance**: Verify that all parameters in the OpenAPI spec (payloads, query params) are represented in the UI forms.

## 3. Implementation Steps
1.  **Scaffold Backend**: Set up FastAPI structure.
2.  **Define Prompts**: Create the advanced system prompts with structured outputs.
3.  **Setup RAG**: Create a mock vector store seeder with UI component examples.
4.  **Connect Frontend**: Update `GeneratorForm.vue` to `POST` the spec to the backend.

## 4. Prompt Strategy Detail
We will enforce **Structured Outputs** (JSON mode) to ensure the LLM returns code in a predictable format:
```json
{
  "filename": "UserProfile.vue",
  "imports": ["ref", "onMounted"],
  "template": "<div...>",
  "script": "..."
}
```
This allows us to programmatically save and lint the files.
