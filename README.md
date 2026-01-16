# Code2UI 🚀

**Transform your OpenAPI Specifications into Production-Ready UI components instantly.**

Code2UI is an intelligent, AI-powered development tool designed to radically accelerate the frontend development lifecycle. By analyzing your **OpenAPI/Swagger specifications**, architectural diagrams, and requirement documents, it generates fully functional, aesthetically premium **Vue.js 3 components** using the latest Mistral LLM technology.

![Status Beta](https://img.shields.io/badge/Status-Beta-cyan)
![Vue 3](https://img.shields.io/badge/Frontend-Vue_3-success)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)
![Mistral AI](https://img.shields.io/badge/AI-Mistral-purple)

---

## 🎯 The Problem

In modern software development, a significant bottleneck exists in the "hand-off" between backend and frontend engineering:
1.  **Duplicate Effort**: Backend engineers define data structures in APIs, and frontend engineers manually recreate these same structures in UI forms and tables.
2.  **Stale Integration**: Frontend code often drifts from the backend spec (API) as the project evolves, leading to runtime errors and "it works on my machine" bugs.
3.  **Boilerplate Fatigue**: Writing the same CRUD (Create, Read, Update, Delete) interfaces for every new entity is tedious, time-consuming, and prone to copy-paste errors.
4.  **Design Inconsistency**: Without a strict design system enforcement, rapid prototyping often results in "Frankenstein" UIs that look different across various modules.

## 💡 The Solution: Code2UI

Code2UI acts as an **AI-driven bridge** that automates the translation of technical specifications into working user interfaces.

It doesn't just "guess" what the UI should look like; it deterministically parses your **OpenAPI 3.0+** specs to understand:
*   **Data Types**: Automatically generating correct form inputs (e.g., date pickers for `format: date`, toggles for `type: boolean`).
*   **Validation Rules**: Enforcing backend constraints (e.g., `maxLength`, `required`) directly in the frontend code.
*   **Relationships**: Understanding nested objects to create sub-forms or detailed views.

**Why Code2UI?**
*   **For Backend Developers**: Visualize your API immediately. Test your endpoints with a real UI, not just curl commands.
*   **For Frontend Developers**: Skip the boilerplate. Get a 80% complete Vue.js component that handles loading states, error handling, and types—so you can focus on the complex business logic and polish.
*   **For Architects**: Ensure adherence to design patterns by supplying "Context Diagrams" that the AI uses to structure the generated application.

---

## ✨ Key Features

*   **⚡ Instant UI Generation**: Upload your `openapi.json` or `swagger.yaml` and get ready-to-use Vue components in seconds.
*   **🧠 AI-Powered Architecture**: Uses **Mistral AI** with advanced Chain-of-Thought prompting to understand not just the *schema*, but the *intent* of your API.
*   **🎨 Premium Aesthetics**: Generated UIs are styled with **Bootstrap 5** and custom "Pro" CSS (Glassmorphism, Gradients, Dark Mode) out of the box.
*   **📁 Context-Aware**: Drag & drop architectural diagrams and text requirements to give the AI context about your design system and business logic.
*   **🛡️ Robust Validation**: Integrated **Pydantic** validation ensures generated code is syntactically correct and structurally sound.
*   **🔒 Secure & Private**: Designed to run locally or self-hosted, keeping your API specs private.

---

## 🏗️ Architecture

Code2UI operates on a modern, decoupled architecture:

### Frontend (User Interface)
*   **Framework**: Vue.js 3 (Composition API)
*   **Build Tool**: Vite
*   **Styling**: Bootstrap 5 + Custom CSS Variables (Dark Theme)
*   **Features**:
    *   Modern Glassmorphism Design
    *   Drag-and-Drop File Uploads
    *   Real-time Code Highlighting & Preview

### Backend (Intelligence Layer)
*   **Framework**: FastAPI (Python 3.9+)
*   **AI Engine**: Mistral AI (via API or Local Weights)
*   **Validation**: Pydantic models for structured JSON output
*   **Orchestration**: Custom Prompt Engineering with Few-Shot examples

---

## 🚀 Getting Started

### Prerequisites
*   Node.js (v18+)
*   Python (v3.9+)
*   Mistral API Key (Optional for mock mode, required for live generation)

### Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/your-username/code2ui.git
    cd code2ui
    ```

2.  **Setup Backend**
    ```bash
    cd backend
    pip install -r requirements.txt
    
    # Set your Mistral API Key (Optional)
    # export MISTRAL_API_KEY=your_key_here
    
    # Run the server
    python -m uvicorn main:app --reload
    ```
    The backend will start at `http://localhost:8000`.

3.  **Setup Frontend**
    Open a new terminal:
    ```bash
    cd vue-project
    npm install
    npm run dev
    ```
    The frontend will launch at `http://localhost:5173`.

---

## 📖 Usage Guide

1.  **Navigate to the Web App**: Open `http://localhost:5173` in your browser.
2.  **Name Your Project**: Enter a name for your generated dashboard context.
3.  **Upload OpenAPI Spec**:
    *   Click "Upload File" to select your `openapi.json` / `swagger.yaml`.
    *   *Or* enter a URL to import it directly.
4.  **Add Context (Optional)**:
    *   Drag architectural diagrams into the "Architecture Diagrams" zone.
    *   Drop requirements text files into the "Requirements / Docs" zone.
5.  **Generate**: Click **Start Generating**.
6.  **Review & Export**: The AI will generate Vue components. You can view the code, copy it to your clipboard, and drop it directly into your codebase.

---

## 🛠️ Configuration

### Environment Variables (.env)
Create a `.env` file in the `backend` directory:

```env
MISTRAL_API_KEY=your_actual_api_key_here
CHROMA_DB_PATH=./chroma_db
```

### Customizing Prompts
You can tweak the system prompts in `backend/prompts/system_prompts.py` to adjust:
*   **Coding Style**: Prefer Tailwind over Bootstrap? Edit the "Golden Example".
*   **Tone**: Make error messages friendlier or more technical.

---

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

## 📞 Support

Project Link: [https://github.com/your-username/code2ui](https://github.com/your-username/code2ui)
