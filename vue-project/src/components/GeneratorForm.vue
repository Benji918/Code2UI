<script setup>
/**
 * GeneratorForm.vue - Production-grade generation form
 * 
 * Handles:
 * - OpenAPI spec upload (file or URL)
 * - Architecture diagrams upload
 * - Documentation files upload
 * - Validation and error handling
 * - API integration with backend
 * - Navigation to generated UI page
 */
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// Form State
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
const specInfo = ref(null)

// Generation State
const isGenerating = ref(false)
const generationProgress = ref(0)
const generationStatus = ref('')

// API Configuration
const API_BASE_URL = 'http://127.0.0.1:8000'

// Computed
const canGenerate = computed(() => {
  return (validationSuccess.value || openApiSource.value === 'url') && 
         projectName.value.trim() !== '' &&
         !isGenerating.value
})

// File Handlers
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
  specInfo.value = null

  try {
    const text = await file.text()
    let spec
    
    // Parse based on file type
    if (file.name.endsWith('.json')) {
      spec = JSON.parse(text)
    } else if (file.name.endsWith('.yaml') || file.name.endsWith('.yml')) {
      // Basic YAML validation - check for openapi/swagger key
      if (!text.includes('openapi:') && !text.includes('swagger:')) {
        throw new Error('Invalid YAML: Missing "openapi" or "swagger" definition')
      }
      // For full parsing, we rely on the backend
      validationSuccess.value = true
      specInfo.value = { title: 'YAML Spec', version: 'Pending validation' }
      return
    } else {
      throw new Error('Unsupported file type. Please use .json, .yaml, or .yml')
    }
    
    // Validate OpenAPI structure
    if (!spec.openapi && !spec.swagger) {
      throw new Error('Invalid OpenAPI spec: Missing root "openapi" or "swagger" field')
    }
    
    if (!spec.paths || Object.keys(spec.paths).length === 0) {
      throw new Error('Invalid OpenAPI spec: No API paths defined')
    }
    
    // Extract spec info
    specInfo.value = {
      title: spec.info?.title || 'Unknown API',
      version: spec.info?.version || '1.0.0',
      pathCount: Object.keys(spec.paths).length,
      description: spec.info?.description?.substring(0, 100)
    }
    
    validationSuccess.value = true
    
    // Auto-fill project name if empty
    if (!projectName.value && spec.info?.title) {
      projectName.value = spec.info.title + ' Client'
    }
    
  } catch (err) {
    validationError.value = err.message
  } finally {
    isValidating.value = false
  }
}

const handleImageDrop = (e) => {
  e.preventDefault()
  const files = Array.from(e.dataTransfer ? e.dataTransfer.files : e.target.files)
  const imageFiles = files.filter(f => f.type.startsWith('image/'))
  contextImages.value = [...contextImages.value, ...imageFiles]
}

const handleDocDrop = (e) => {
  e.preventDefault()
  const files = Array.from(e.dataTransfer ? e.dataTransfer.files : e.target.files)
  const docFiles = files.filter(f => 
    f.name.endsWith('.txt') || 
    f.name.endsWith('.md') || 
    f.name.endsWith('.pdf') ||
    f.name.endsWith('.doc') ||
    f.name.endsWith('.docx')
  )
  contextDocs.value = [...contextDocs.value, ...docFiles]
}

const removeFile = (list, index) => {
  list.splice(index, 1)
}

const triggerImageUpload = () => {
  document.getElementById('imgInput').click()
}

const triggerDocUpload = () => {
  document.getElementById('docInput').click()
}

// Generation with SSE Streaming
const generate = async () => {
  if (!canGenerate.value) {
    if (!projectName.value.trim()) {
      alert('Please enter a project name')
      return
    }
    if (!validationSuccess.value && openApiSource.value === 'file') {
      alert('Please provide a valid OpenAPI spec before generating')
      return
    }
  }
  
  isGenerating.value = true
  generationProgress.value = 0
  generationStatus.value = 'Starting generation...'
  
  try {
    const formData = new FormData()
    formData.append('project_name', projectName.value)
    
    // Add OpenAPI spec
    if (openApiSource.value === 'file' && openApiFile.value) {
      formData.append('spec_file', openApiFile.value)
    } else if (openApiSource.value === 'url' && openApiUrl.value) {
      // Fetch URL content first
      generationStatus.value = 'Fetching spec from URL...'
      const response = await fetch(openApiUrl.value)
      const specText = await response.text()
      const specBlob = new Blob([specText], { type: 'application/json' })
      formData.append('spec_file', specBlob, 'openapi.json')
    }
    
    // Add diagrams and docs
    for (const img of contextImages.value) {
      formData.append('diagrams', img)
    }
    for (const doc of contextDocs.value) {
      formData.append('docs', doc)
    }
    
    generationProgress.value = 10
    generationStatus.value = 'Sending to server...'
    
    // Start the streaming generation
    const response = await fetch(`${API_BASE_URL}/api/generate/stream`, {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `Failed: ${response.statusText}`)
    }
    
    const { task_id } = await response.json()
    
    // Connect to SSE stream for real-time updates
    await connectToStream(task_id)
    
  } catch (error) {
    console.error('Generation Error:', error)
    generationStatus.value = 'Error: ' + error.message
    alert('Failed to generate UI: ' + error.message)
    isGenerating.value = false
  }
}

// Connect to Server-Sent Events stream
const connectToStream = (taskId) => {
  return new Promise((resolve, reject) => {
    const eventSource = new EventSource(`${API_BASE_URL}/api/stream/${taskId}`)
    
    eventSource.addEventListener('progress', (event) => {
      const data = JSON.parse(event.data)
      generationProgress.value = data.progress
      generationStatus.value = data.message
    })
    
    eventSource.addEventListener('complete', (event) => {
      const data = JSON.parse(event.data)
      const result = data.result
      
      if (result) {
        // Store generated UI
        localStorage.setItem('code2ui_generated', JSON.stringify(result))
        
        // Save to history
        saveToHistory(result)
        
        generationProgress.value = 100
        generationStatus.value = 'Complete!'
        
        // Navigate to generated page
        setTimeout(() => {
          router.push('/generated')
        }, 500)
      }
      
      eventSource.close()
      isGenerating.value = false
      resolve()
    })
    
    eventSource.addEventListener('error', (event) => {
      const data = JSON.parse(event.data)
      generationStatus.value = data.message || 'Generation failed'
      alert('Generation failed: ' + generationStatus.value)
      
      eventSource.close()
      isGenerating.value = false
      reject(new Error(data.message))
    })
    
    eventSource.onerror = (error) => {
      console.error('SSE Error:', error)
      generationStatus.value = 'Connection error'
      alert('Lost connection to server')
      
      eventSource.close()
      isGenerating.value = false
      reject(error)
    }
  })
}

const saveToHistory = (ui) => {
  try {
    const history = JSON.parse(localStorage.getItem('code2ui_history') || '[]')
    history.unshift({
      projectName: projectName.value,
      createdAt: new Date().toISOString(),
      endpoints: specInfo.value?.pathCount || 0,
      data: ui
    })
    // Keep only last 20 generations
    localStorage.setItem('code2ui_history', JSON.stringify(history.slice(0, 20)))
  } catch (e) {
    console.error('Failed to save history:', e)
  }
}

const resetForm = () => {
  projectName.value = ''
  openApiFile.value = null
  openApiUrl.value = ''
  contextImages.value = []
  contextDocs.value = []
  validationSuccess.value = false
  validationError.value = null
  specInfo.value = null
}
</script>

<template>
  <div id="generator" class="glass-panel p-4 p-lg-5 animate-fade-in">
    <div class="mb-4">
      <h3 class="fw-bold mb-2">Configure Generation</h3>
      <p class="text-white-50 small mb-0">Upload your resources to get started.</p>
    </div>

    <form @submit.prevent="generate">
      <!-- Project Name -->
      <div class="mb-4">
        <label class="form-label text-light small text-uppercase fw-bold ls-1">
          Project Name <span class="text-danger">*</span>
        </label>
        <input 
          v-model="projectName" 
          type="text" 
          class="form-control input-dark" 
          placeholder="e.g. CRM Dashboard Client"
          :disabled="isGenerating"
        >
      </div>

      <!-- OpenAPI Spec Section -->
      <div class="mb-4">
        <label class="form-label text-light small text-uppercase fw-bold ls-1 d-flex justify-content-between align-items-center">
          <span>OpenAPI Spec <span class="text-danger">*</span></span>
          <span v-if="isValidating" class="text-info small">
            <span class="spinner-border spinner-border-sm me-1"></span> Validating...
          </span>
          <span v-else-if="validationSuccess" class="text-success small">
            <i class="bi bi-check-circle-fill me-1"></i> Valid Spec
          </span>
          <span v-else-if="validationError" class="text-danger small" :title="validationError">
            <i class="bi bi-exclamation-circle-fill me-1"></i> Invalid
          </span>
        </label>
        
        <!-- Source Toggle -->
        <div class="nav nav-pills nav-fill mb-3 p-1 bg-black bg-opacity-25 rounded">
          <button 
            type="button" 
            class="nav-link btn-sm rounded" 
            :class="{ active: openApiSource === 'file', 'text-white-50': openApiSource !== 'file' }"
            @click="openApiSource = 'file'"
            :disabled="isGenerating"
          >
            <i class="bi bi-file-earmark-arrow-up me-1"></i> Upload File
          </button>
          <button 
            type="button" 
            class="nav-link btn-sm rounded" 
            :class="{ active: openApiSource === 'url', 'text-white-50': openApiSource !== 'url' }"
            @click="openApiSource = 'url'"
            :disabled="isGenerating"
          >
            <i class="bi bi-link-45deg me-1"></i> Import URL
          </button>
        </div>

        <!-- File Input -->
        <div v-if="openApiSource === 'file'">
          <input 
            type="file" 
            class="form-control input-dark" 
            @change="handleSpecFileChange" 
            accept=".json,.yaml,.yml"
            :disabled="isGenerating"
          >
          
          <!-- Spec Info Preview -->
          <div v-if="specInfo" class="spec-info mt-3 p-3 bg-dark bg-opacity-50 rounded">
            <div class="d-flex justify-content-between align-items-start">
              <div>
                <h6 class="mb-1 text-white">{{ specInfo.title }}</h6>
                <small class="text-muted">Version {{ specInfo.version }}</small>
              </div>
              <span class="badge bg-gradient-cyan text-dark">
                {{ specInfo.pathCount }} endpoints
              </span>
            </div>
            <p v-if="specInfo.description" class="text-muted small mb-0 mt-2">
              {{ specInfo.description }}...
            </p>
          </div>
        </div>
        
        <!-- URL Input -->
        <div v-else>
          <input 
            v-model="openApiUrl" 
            type="url" 
            class="form-control input-dark" 
            placeholder="https://api.example.com/openapi.json"
            :disabled="isGenerating"
          >
        </div>
      </div>

      <!-- Context Files -->
      <div class="row g-3 mb-4">
        <!-- Architecture Diagrams (Priority 2) -->
        <div class="col-md-6">
          <label class="form-label text-light small text-uppercase fw-bold ls-1">
            <i class="bi bi-diagram-3 me-1 text-warning"></i>
            Architecture Diagrams
            <span class="badge bg-warning text-dark ms-1">P2</span>
          </label>
          <div 
            class="drop-zone"
            @dragover.prevent
            @drop="handleImageDrop"
            @click="triggerImageUpload"
          >
            <div v-if="contextImages.length === 0" class="drop-zone-content">
              <i class="bi bi-card-image fs-3 mb-2"></i>
              <span class="small">Drop images or click</span>
            </div>
            <div v-else class="file-list">
              <div 
                v-for="(file, i) in contextImages" 
                :key="i" 
                class="file-item"
              >
                <i class="bi bi-image me-2"></i>
                <span class="text-truncate flex-grow-1">{{ file.name }}</span>
                <button 
                  type="button"
                  class="btn-remove" 
                  @click.stop="removeFile(contextImages, i)"
                >
                  <i class="bi bi-x"></i>
                </button>
              </div>
            </div>
            <input 
              type="file" 
              id="imgInput"
              class="d-none" 
              @change="handleImageDrop" 
              accept="image/*" 
              multiple
              :disabled="isGenerating"
            >
          </div>
        </div>

        <!-- Documentation (Priority 3) -->
        <div class="col-md-6">
          <label class="form-label text-light small text-uppercase fw-bold ls-1">
            <i class="bi bi-file-text me-1 text-info"></i>
            Requirements / Docs
            <span class="badge bg-info text-dark ms-1">P3</span>
          </label>
          <div 
            class="drop-zone"
            @dragover.prevent
            @drop="handleDocDrop"
            @click="triggerDocUpload"
          >
            <div v-if="contextDocs.length === 0" class="drop-zone-content">
              <i class="bi bi-file-text fs-3 mb-2"></i>
              <span class="small">Drop text files or click</span>
            </div>
            <div v-else class="file-list">
              <div 
                v-for="(file, i) in contextDocs" 
                :key="i" 
                class="file-item"
              >
                <i class="bi bi-file-earmark-text me-2"></i>
                <span class="text-truncate flex-grow-1">{{ file.name }}</span>
                <button 
                  type="button"
                  class="btn-remove" 
                  @click.stop="removeFile(contextDocs, i)"
                >
                  <i class="bi bi-x"></i>
                </button>
              </div>
            </div>
            <input 
              type="file" 
              id="docInput"
              class="d-none" 
              @change="handleDocDrop" 
              accept=".txt,.md,.pdf,.doc,.docx" 
              multiple
              :disabled="isGenerating"
            >
          </div>
        </div>
      </div>

      <!-- Submit Button -->
      <div class="d-grid mt-5">
        <button 
          type="submit" 
          class="btn btn-cyan btn-lg"
          :disabled="!canGenerate"
        >
          <span v-if="isGenerating" class="d-flex align-items-center justify-content-center">
            <span class="spinner-border spinner-border-sm me-2"></span>
            {{ generationStatus }}
          </span>
          <span v-else>
            Start Generating <i class="bi bi-arrow-right ms-2"></i>
          </span>
        </button>
      </div>
      
      <!-- Progress Bar -->
      <div v-if="isGenerating" class="mt-3">
        <div class="progress" style="height: 4px; background: rgba(255,255,255,0.1);">
          <div 
            class="progress-bar bg-gradient-cyan" 
            role="progressbar"
            :style="{ width: generationProgress + '%' }"
          ></div>
        </div>
      </div>
    </form>
  </div>
</template>

<style scoped>
.ls-1 { letter-spacing: 1px; }

.drop-zone {
  border: 2px dashed var(--glass-border);
  background: rgba(255, 255, 255, 0.02);
  border-radius: 12px;
  min-height: 120px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.drop-zone:hover {
  border-color: var(--color-brand-cyan);
  background: rgba(34, 211, 238, 0.05);
}

.drop-zone-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1.5rem;
  color: var(--color-text-muted);
}

.file-list {
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.file-item {
  display: flex;
  align-items: center;
  padding: 0.5rem 0.75rem;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  font-size: 0.875rem;
  color: var(--color-text-muted);
}

.btn-remove {
  background: transparent;
  border: none;
  color: var(--color-text-muted);
  padding: 0.25rem;
  cursor: pointer;
  line-height: 1;
  transition: color 0.2s;
}

.btn-remove:hover {
  color: #ef4444;
}

.nav-pills .nav-link.active {
  background-color: var(--color-brand-cyan);
  color: #000;
}

.nav-pills .nav-link {
  color: rgba(255, 255, 255, 0.7);
  transition: all 0.2s;
}

.nav-pills .nav-link:hover:not(.active) {
  color: #fff;
  background: rgba(255, 255, 255, 0.05);
}

.spec-info {
  border: 1px solid var(--glass-border);
}
</style>
