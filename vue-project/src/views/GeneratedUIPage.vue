<script setup>
/**
 * GeneratedUIPage.vue - Isolated page for rendering generated UI
 * 
 * As per implementation.md, the generated frontend is rendered on a 
 * SEPARATE PAGE to not disrupt the main Code2UI interface.
 * 
 * This page:
 * - Receives generated code from the store/props
 * - Renders components dynamically
 * - Provides code export options
 */
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import CodePreview from '../components/CodePreview.vue'
import LivePreview from '../components/LivePreview.vue'

const route = useRoute()
const router = useRouter()

// State
const generatedUI = ref(null)
const activeTab = ref('preview') // 'preview', 'code', 'export'
const selectedComponent = ref(0)
const isLoading = ref(true)
const error = ref(null)

// Computed
const hasComponents = computed(() => {
  return generatedUI.value?.components?.length > 0
})

const currentComponent = computed(() => {
  if (!hasComponents.value) return null
  return generatedUI.value.components[selectedComponent.value]
})

const componentsList = computed(() => {
  if (!hasComponents.value) return []
  return generatedUI.value.components.map((c, i) => ({
    index: i,
    filename: c.filename,
    rationale: c.rationale
  }))
})

// Load generated UI from localStorage
onMounted(() => {
  loadGeneratedUI()
})

watch(() => route.params.id, () => {
  loadGeneratedUI()
})

const loadGeneratedUI = () => {
  isLoading.value = true
  error.value = null
  
  try {
    const storedData = localStorage.getItem('code2ui_generated')
    if (storedData) {
      generatedUI.value = JSON.parse(storedData)
    } else {
      error.value = 'No generated UI found. Please generate one first.'
    }
  } catch (e) {
    error.value = 'Failed to load generated UI data.'
    console.error('Load error:', e)
  } finally {
    isLoading.value = false
  }
}

const goBack = () => {
  router.push('/')
}

const copyToClipboard = async (code) => {
  try {
    await navigator.clipboard.writeText(code)
    // Show toast or notification
    alert('Code copied to clipboard!')
  } catch (err) {
    console.error('Copy failed:', err)
  }
}

const downloadAll = () => {
  if (!generatedUI.value) return
  
  // Create a simple zip-like structure as JSON for demo
  const content = JSON.stringify(generatedUI.value, null, 2)
  const blob = new Blob([content], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  
  const a = document.createElement('a')
  a.href = url
  a.download = `${generatedUI.value.project_name || 'generated-ui'}.json`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="generated-page">
    <!-- Header -->
    <header class="generated-header">
      <div class="container">
        <div class="d-flex align-items-center justify-content-between">
          <div class="d-flex align-items-center gap-3">
            <button @click="goBack" class="btn btn-outline-light btn-sm">
              <i class="bi bi-arrow-left me-2"></i>Back
            </button>
            <div v-if="generatedUI">
              <h1 class="h4 mb-0 fw-bold">{{ generatedUI.project_name }}</h1>
              <small class="text-muted">
                Generated UI • {{ generatedUI.components?.length || 0 }} components
              </small>
            </div>
          </div>
          
          <div class="d-flex gap-2" v-if="generatedUI">
            <button @click="downloadAll" class="btn btn-outline-light btn-sm">
              <i class="bi bi-download me-2"></i>Export All
            </button>
          </div>
        </div>
      </div>
    </header>
    
    <!-- Loading State -->
    <div v-if="isLoading" class="loading-state">
      <div class="spinner-border text-info" role="status"></div>
      <p class="mt-3 text-muted">Loading generated UI...</p>
    </div>
    
    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <div class="container text-center py-5">
        <i class="bi bi-exclamation-triangle display-1 text-warning mb-4"></i>
        <h2>{{ error }}</h2>
        <button @click="goBack" class="btn btn-cyan mt-3">
          <i class="bi bi-arrow-left me-2"></i>Go to Generator
        </button>
      </div>
    </div>
    
    <!-- Content -->
    <div v-else-if="generatedUI" class="generated-content">
      <div class="container-fluid h-100">
        <div class="row h-100">
          <!-- Sidebar - Component List -->
          <div class="col-md-3 col-lg-2 sidebar">
            <div class="sidebar-content">
              <h6 class="sidebar-title text-uppercase small fw-bold text-muted mb-3">
                Components
              </h6>
              
              <div class="component-list">
                <button
                  v-for="comp in componentsList"
                  :key="comp.index"
                  @click="selectedComponent = comp.index"
                  class="component-item"
                  :class="{ active: selectedComponent === comp.index }"
                >
                  <i class="bi bi-file-earmark-code me-2"></i>
                  <span class="component-name">{{ comp.filename }}</span>
                </button>
              </div>
              
              <!-- App Entry -->
              <hr class="my-3 border-secondary">
              <h6 class="sidebar-title text-uppercase small fw-bold text-muted mb-3">
                Entry Files
              </h6>
              <button 
                v-if="generatedUI.app_entry"
                @click="selectedComponent = -1"
                class="component-item"
                :class="{ active: selectedComponent === -1 }"
              >
                <i class="bi bi-app me-2"></i>
                <span>App.vue</span>
              </button>
              <button 
                v-if="generatedUI.api_client"
                @click="selectedComponent = -2"
                class="component-item"
                :class="{ active: selectedComponent === -2 }"
              >
                <i class="bi bi-braces me-2"></i>
                <span>apiClient.js</span>
              </button>
              <button 
                v-if="generatedUI.styles"
                @click="selectedComponent = -3"
                class="component-item"
                :class="{ active: selectedComponent === -3 }"
              >
                <i class="bi bi-palette me-2"></i>
                <span>styles.css</span>
              </button>
            </div>
          </div>
          
          <!-- Main Content Area -->
          <div class="col-md-9 col-lg-10 main-area">
            <!-- Tabs -->
            <div class="content-tabs">
              <button 
                @click="activeTab = 'preview'"
                class="tab-btn"
                :class="{ active: activeTab === 'preview' }"
              >
                <i class="bi bi-eye me-2"></i>Preview
              </button>
              <button 
                @click="activeTab = 'code'"
                class="tab-btn"
                :class="{ active: activeTab === 'code' }"
              >
                <i class="bi bi-code-slash me-2"></i>Code
              </button>
            </div>
            
            <!-- Tab Content -->
            <div class="tab-content">
              <!-- Preview Tab -->
              <div v-if="activeTab === 'preview'" class="preview-container">
                <LivePreview 
                  v-if="selectedComponent >= 0 && currentComponent"
                  :code="currentComponent.code"
                  :filename="currentComponent.filename"
                  :project-context="generatedUI"
                />
                <LivePreview 
                  v-else-if="selectedComponent === -1"
                  :code="generatedUI.app_entry"
                  filename="App.vue"
                  :project-context="generatedUI"
                />
                <div v-else class="no-preview text-center py-5">
                  <i class="bi bi-eye-slash display-4 text-muted"></i>
                  <p class="text-muted mt-3">Preview not available for this file type</p>
                </div>
              </div>
              
              <!-- Code Tab -->
              <div v-if="activeTab === 'code'" class="code-container">
                <CodePreview
                  v-if="selectedComponent >= 0 && currentComponent"
                  :code="currentComponent.code"
                  :filename="currentComponent.filename"
                  :rationale="currentComponent.rationale"
                  @copy="copyToClipboard"
                />
                <CodePreview
                  v-else-if="selectedComponent === -1"
                  :code="generatedUI.app_entry"
                  filename="App.vue"
                  rationale="Main application entry point"
                  @copy="copyToClipboard"
                />
                <CodePreview
                  v-else-if="selectedComponent === -2"
                  :code="generatedUI.api_client"
                  filename="apiClient.js"
                  rationale="HTTP client utility for API requests"
                  @copy="copyToClipboard"
                />
                <CodePreview
                  v-else-if="selectedComponent === -3"
                  :code="generatedUI.styles"
                  filename="styles.css"
                  rationale="Global styles for the generated application"
                  @copy="copyToClipboard"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.generated-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-primary);
}

.generated-header {
  background: var(--glass-bg);
  border-bottom: 1px solid var(--glass-border);
  padding: 1rem 0;
  position: sticky;
  top: 0;
  z-index: 100;
}

.loading-state,
.error-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.generated-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.sidebar {
  background: var(--glass-bg);
  border-right: 1px solid var(--glass-border);
  height: calc(100vh - 80px);
  overflow-y: auto;
}

.sidebar-content {
  padding: 1.5rem 1rem;
}

.component-list {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.component-item {
  display: flex;
  align-items: center;
  background: transparent;
  border: none;
  color: var(--color-text-muted);
  padding: 0.75rem 1rem;
  border-radius: 8px;
  text-align: left;
  transition: all 0.2s ease;
  cursor: pointer;
  font-size: 0.875rem;
  width: 100%;
}

.component-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--color-text-main);
}

.component-item.active {
  background: var(--color-brand-cyan);
  color: #000;
  font-weight: 600;
}

.component-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.main-area {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 80px);
  overflow: hidden;
}

.content-tabs {
  display: flex;
  gap: 0.5rem;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--glass-border);
  background: var(--glass-bg);
}

.tab-btn {
  background: transparent;
  border: 1px solid var(--glass-border);
  color: var(--color-text-muted);
  padding: 0.5rem 1.25rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.875rem;
}

.tab-btn:hover {
  border-color: var(--color-brand-cyan);
  color: var(--color-text-main);
}

.tab-btn.active {
  background: var(--color-brand-cyan);
  border-color: var(--color-brand-cyan);
  color: #000;
  font-weight: 600;
}

.tab-content {
  flex: 1;
  overflow: auto;
  padding: 1.5rem;
}

.preview-container,
.code-container {
  height: 100%;
}

.no-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
}
</style>
