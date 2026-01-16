<script setup>
import { ref } from 'vue'

const projectName = ref('')
const openApiSource = ref('file') // 'file' or 'url'
const openApiUrl = ref('')
const openApiFile = ref(null)
const contextImages = ref([])
const contextDocs = ref([])

// Validation State
const isValidating = ref(false)
const validationError = ref(null)
const validationSuccess = ref(false)

const handleSpecFileChange = async (e) => {
  const file = e.target.files[0]
  if (!file) return

  openApiFile.value = file
  await validateSpec(file)
}

const validateSpec = async (file) => {
  isValidating.value = true
  validationError.value = null
  validationSuccess.value = false

  try {
    const text = await file.text()
    // Heuristic Check
    if (file.name.endsWith('.json')) {
      JSON.parse(text)
    } else if (file.name.endsWith('.yaml') || file.name.endsWith('.yml')) {
      if (!text.includes('openapi:') && !text.includes('swagger:')) {
        throw new Error('Missing "openapi" or "swagger" definition.')
      }
    } else {
      throw new Error('Unsupported file extension. Please use .json, .yaml, or .yml')
    }
    
    // Additional structure check if JSON
    if (file.name.endsWith('.json')) {
       const json = JSON.parse(text)
       if (!json.openapi && !json.swagger) {
         throw new Error('Invalid OpenAPI spec: Missing root "openapi" or "swagger" field.')
       }
    }

    validationSuccess.value = true
  } catch (err) {
    validationError.value = err.message
  } finally {
    isValidating.value = false
  }
}

const handleImageDrop = (e) => {
  const files = Array.from(e.dataTransfer ? e.dataTransfer.files : e.target.files)
  const imageFiles = files.filter(f => f.type.startsWith('image/'))
  contextImages.value = [...contextImages.value, ...imageFiles]
}

const handleDocDrop = (e) => {
  const files = Array.from(e.dataTransfer ? e.dataTransfer.files : e.target.files)
  const docFiles = files.filter(f => !f.type.startsWith('image/')) // Simple filter
  contextDocs.value = [...contextDocs.value, ...docFiles]
}

const removeFile = (list, index) => {
  list.splice(index, 1)
}

const isGenerating = ref(false)
const generatedResults = ref(null)

const generate = async () => {
  if (!validationSuccess.value && openApiFile.value) {
     alert('Please provide a valid OpenAPI spec before generating.')
     return
  }
  
  isGenerating.value = true
  generatedResults.value = null
  
  try {
    const formData = new FormData()
    if (openApiSource.value === 'file' && openApiFile.value) {
      formData.append('file', openApiFile.value)
    }
    
    // In a real app, we would also append contextImages and contextDocs to the FormData
    
    const response = await fetch('http://localhost:8000/api/generate', {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) {
      throw new Error(`Generation failed: ${response.statusText}`)
    }
    
    const result = await response.json()
    generatedResults.value = result.components
    
  } catch (error) {
    console.error('Generation Error:', error)
    alert('Failed to generate UI: ' + error.message)
  } finally {
    isGenerating.value = false
  }
}
</script>

<template>
  <div class="glass-panel p-4 p-lg-5 animate-fade-in">
    <div class="mb-4">
      <h3 class="fw-bold mb-2">Configure Generation</h3>
      <p class="text-white-50 small">Upload your resources to get started.</p>
    </div>

    <form @submit.prevent="generate">
      <!-- Project Name -->
      <div class="mb-4">
        <label class="form-label text-light small text-uppercase fw-bold ls-1">Project Name</label>
        <input 
            v-model="projectName" 
            type="text" 
            class="form-control input-dark" 
            placeholder="e.g. CRM Dashboard" 
            required
        >
      </div>

      <!-- OpenAPI Spec Section -->
      <div class="mb-4">
        <label class="form-label text-light small text-uppercase fw-bold ls-1 d-flex justify-content-between">
          <span>OpenAPI Spec</span>
          <span v-if="validationSuccess" class="text-success small"><i class="bi bi-check-circle-fill"></i> Valid Spec</span>
          <span v-if="validationError" class="text-danger small"><i class="bi bi-exclamation-circle-fill"></i> {{ validationError }}</span>
        </label>
        
        <div class="nav nav-pills nav-fill mb-3 p-1 bg-black bg-opacity-25 rounded" id="specTabs" role="tablist">
          <button 
            type="button" 
            class="nav-link btn-sm rounded fs-7" 
            :class="{ active: openApiSource === 'file', 'text-white-50': openApiSource !== 'file' }"
            @click="openApiSource = 'file'"
          >Upload File</button>
          <button 
            type="button" 
            class="nav-link btn-sm rounded fs-7" 
            :class="{ active: openApiSource === 'url', 'text-white-50': openApiSource !== 'url' }"
            @click="openApiSource = 'url'"
          >Import URL</button>
        </div>

        <div v-if="openApiSource === 'file'">
           <input type="file" class="form-control input-dark" @change="handleSpecFileChange" accept=".json,.yaml,.yml">
        </div>
        <div v-else>
          <input v-model="openApiUrl" type="url" class="form-control input-dark" placeholder="https://api.example.com/openapi.json">
        </div>
      </div>

      <!-- Split Drop Zones -->
      <div class="row g-3 mb-4">
        <!-- Images / Diagrams -->
        <div class="col-md-6">
          <label class="form-label text-light small text-uppercase fw-bold ls-1">Architecture Diagrams</label>
          <div 
            class="drop-zone p-3 text-center rounded-3 border-dashed transition-all"
            @dragover.prevent
            @drop.prevent="handleImageDrop"
            style="border: 2px dashed var(--color-border); background: rgba(255,255,255,0.02); min-height: 120px; display: flex; flex-direction: column; justify-content: center;"
          >
            <div v-if="contextImages.length === 0" class="text-white-50 clickable" @click="$refs.imgInput.click()">
              <i class="bi bi-card-image fs-4 mb-2 d-block"></i>
              <span class="small">Drop images or click</span>
            </div>
            <div v-else class="text-start">
               <div v-for="(file, i) in contextImages" :key="i" class="d-flex align-items-center justify-content-between small text-white-50 mb-1 bg-dark bg-opacity-50 p-1 rounded">
                 <span class="text-truncate">{{ file.name }}</span>
                 <i class="bi bi-x cursor-pointer hover-text-danger" @click="removeFile(contextImages, i)"></i>
               </div>
            </div>
            <input type="file" ref="imgInput" class="d-none" @change="handleImageDrop" accept="image/*" multiple>
          </div>
        </div>

        <!-- Text / Docs -->
        <div class="col-md-6">
          <label class="form-label text-light small text-uppercase fw-bold ls-1">Requirements / Docs</label>
           <div 
            class="drop-zone p-3 text-center rounded-3 border-dashed transition-all"
            @dragover.prevent
            @drop.prevent="handleDocDrop"
            style="border: 2px dashed var(--color-border); background: rgba(255,255,255,0.02); min-height: 120px; display: flex; flex-direction: column; justify-content: center;"
          >
            <div v-if="contextDocs.length === 0" class="text-white-50 clickable" @click="$refs.docInput.click()">
               <i class="bi bi-file-text fs-4 mb-2 d-block"></i>
              <span class="small">Drop text files or click</span>
            </div>
             <div v-else class="text-start">
               <div v-for="(file, i) in contextDocs" :key="i" class="d-flex align-items-center justify-content-between small text-white-50 mb-1 bg-dark bg-opacity-50 p-1 rounded">
                 <span class="text-truncate">{{ file.name }}</span>
                 <i class="bi bi-x cursor-pointer hover-text-danger" @click="removeFile(contextDocs, i)"></i>
               </div>
            </div>
             <input type="file" ref="docInput" class="d-none" @change="handleDocDrop" accept=".txt,.md,.pdf,.doc,.docx" multiple>
          </div>
        </div>
      </div>

      <!-- Submit -->
      <div class="d-grid mt-5">
        <button type="submit" class="btn btn-cyan btn-lg">
          Start Generating <i class="bi bi-arrow-right ms-2"></i>
        </button>
      </div>
    </form>
    
    <!-- Results Section -->
    <div v-if="generatedResults" class="mt-5 border-top border-secondary pt-5 animate-fade-in">
      <h3 class="fw-bold mb-4 text-white">Generated Interface <span class="badge bg-gradient-cyan ms-2 text-dark">BETA</span></h3>
      
      <div v-for="(comp, idx) in generatedResults" :key="idx" class="mb-5">
        <div class="d-flex align-items-center justify-content-between mb-3">
           <h5 class="text-gradient-cyan mb-0"><i class="bi bi-file-earmark-code me-2"></i>{{ comp.filename }}</h5>
           <span class="badge bg-secondary">{{ comp.rationale.substring(0, 50) }}...</span>
        </div>
        
        <div class="position-relative bg-dark rounded-3 overflow-hidden border border-secondary">
          <div class="d-flex justify-content-between bg-black bg-opacity-50 px-3 py-2 border-bottom border-secondary">
             <span class="small text-muted font-monospace">Vue 3 Composition API</span>
             <button class="btn btn-sm btn-link text-white-50 text-decoration-none p-0"><i class="bi bi-clipboard"></i> Copy</button>
          </div>
          <pre class="m-0 p-3 text-white small font-monospace" style="overflow-x: auto; max-height: 400px;">{{ comp.code }}</pre>
        </div>
      </div>
    </div>
    
    <div v-if="isGenerating" class="mt-4 text-center">
       <div class="spinner-border text-info" role="status"></div>
       <p class="text-white-50 mt-2 animate-pulse">Consulting Mistral AI & Architecting Solution...</p>
    </div>
  </div>
</template>

<style scoped>
.ls-1 { letter-spacing: 1px; }
.fs-7 { font-size: 0.85rem; }
.cursor-pointer { cursor: pointer; }
.clickable { cursor: pointer; }
.hover-text-danger:hover { color: var(--bs-danger) !important; }

.nav-pills .nav-link.active {
  background-color: var(--color-border);
  color: white;
}
.nav-pills .nav-link {
  color: rgba(255, 255, 255, 0.7);
  transition: color 0.2s;
}
.nav-pills .nav-link:hover {
  color: #fff;
}
</style>
