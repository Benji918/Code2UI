<script setup>
/**
 * HistoryPage.vue - View past generations
 */
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const generations = ref([])
const isLoading = ref(true)

onMounted(() => {
  loadHistory()
})

const loadHistory = () => {
  isLoading.value = true
  try {
    const stored = localStorage.getItem('code2ui_history')
    if (stored) {
      generations.value = JSON.parse(stored)
    }
  } catch (e) {
    console.error('Failed to load history:', e)
  } finally {
    isLoading.value = false
  }
}

const viewGeneration = (gen) => {
  localStorage.setItem('code2ui_generated', JSON.stringify(gen.data))
  router.push('/generated')
}

const deleteGeneration = (index) => {
  generations.value.splice(index, 1)
  localStorage.setItem('code2ui_history', JSON.stringify(generations.value))
}

const clearHistory = () => {
  if (confirm('Are you sure you want to clear all history?')) {
    generations.value = []
    localStorage.removeItem('code2ui_history')
  }
}

const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<template>
  <main class="history-page">
    <div class="container py-5">
      <div class="d-flex justify-content-between align-items-center mb-5">
        <div>
          <h1 class="fw-bold mb-2">Generation History</h1>
          <p class="text-muted mb-0">View and manage your past UI generations</p>
        </div>
        <button 
          v-if="generations.length > 0"
          @click="clearHistory" 
          class="btn btn-outline-danger"
        >
          <i class="bi bi-trash me-2"></i>Clear All
        </button>
      </div>
      
      <!-- Loading -->
      <div v-if="isLoading" class="text-center py-5">
        <div class="spinner-border text-info"></div>
      </div>
      
      <!-- Empty State -->
      <div v-else-if="generations.length === 0" class="empty-state text-center py-5">
        <div class="glass-panel p-5 d-inline-block">
          <i class="bi bi-clock-history display-1 text-muted mb-4"></i>
          <h3 class="fw-bold">No generations yet</h3>
          <p class="text-muted mb-4">Generate your first UI from an OpenAPI spec!</p>
          <router-link to="/" class="btn btn-cyan">
            <i class="bi bi-plus-lg me-2"></i>Start Generating
          </router-link>
        </div>
      </div>
      
      <!-- History List -->
      <div v-else class="history-grid">
        <div 
          v-for="(gen, index) in generations" 
          :key="index"
          class="history-card glass-panel"
        >
          <div class="card-header">
            <h5 class="card-title mb-1">{{ gen.projectName }}</h5>
            <small class="text-muted">{{ formatDate(gen.createdAt) }}</small>
          </div>
          
          <div class="card-body">
            <div class="stats">
              <div class="stat">
                <span class="stat-value">{{ gen.data?.components?.length || 0 }}</span>
                <span class="stat-label">Components</span>
              </div>
              <div class="stat">
                <span class="stat-value">{{ gen.endpoints || 0 }}</span>
                <span class="stat-label">Endpoints</span>
              </div>
            </div>
          </div>
          
          <div class="card-footer">
            <button @click="viewGeneration(gen)" class="btn btn-sm btn-cyan">
              <i class="bi bi-eye me-1"></i>View
            </button>
            <button @click="deleteGeneration(index)" class="btn btn-sm btn-outline-danger">
              <i class="bi bi-trash"></i>
            </button>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<style scoped>
.history-page {
  flex: 1;
  min-height: calc(100vh - 80px);
}

.history-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.history-card {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.card-header {
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--glass-border);
}

.card-title {
  font-weight: 600;
  color: var(--color-text-main);
}

.card-body {
  padding: 1.5rem;
  flex: 1;
}

.stats {
  display: flex;
  gap: 2rem;
}

.stat {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-brand-cyan);
}

.stat-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  color: var(--color-text-muted);
  letter-spacing: 0.5px;
}

.card-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--glass-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
