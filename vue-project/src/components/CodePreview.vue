<script setup>
/**
 * CodePreview.vue - Syntax-highlighted code display with copy functionality
 */
import { computed } from 'vue'

const props = defineProps({
  code: {
    type: String,
    required: true
  },
  filename: {
    type: String,
    default: 'Component.vue'
  },
  rationale: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['copy'])

const language = computed(() => {
  const ext = props.filename.split('.').pop()
  switch (ext) {
    case 'vue': return 'vue'
    case 'js': return 'javascript'
    case 'css': return 'css'
    case 'json': return 'json'
    default: return 'markup'
  }
})

const copyCode = () => {
  emit('copy', props.code)
}
</script>

<template>
  <div class="code-preview">
    <!-- Header -->
    <div class="preview-header">
      <div class="file-info">
        <i class="bi bi-file-earmark-code me-2"></i>
        <span class="filename">{{ filename }}</span>
      </div>
      <button @click="copyCode" class="btn-copy">
        <i class="bi bi-clipboard me-1"></i>
        Copy
      </button>
    </div>
    
    <!-- Rationale -->
    <div v-if="rationale" class="rationale">
      <i class="bi bi-lightbulb me-2 text-warning"></i>
      <span>{{ rationale }}</span>
    </div>
    
    <!-- Code Block -->
    <div class="code-block">
      <pre><code :class="`language-${language}`">{{ code }}</code></pre>
    </div>
  </div>
</template>

<style scoped>
.code-preview {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: 12px;
  overflow: hidden;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: rgba(0, 0, 0, 0.3);
  border-bottom: 1px solid var(--glass-border);
}

.file-info {
  display: flex;
  align-items: center;
  color: var(--color-text-main);
}

.filename {
  font-weight: 600;
  font-family: 'JetBrains Mono', monospace;
}

.btn-copy {
  background: transparent;
  border: 1px solid var(--glass-border);
  color: var(--color-text-muted);
  padding: 0.375rem 0.75rem;
  border-radius: 6px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-copy:hover {
  background: var(--color-brand-cyan);
  border-color: var(--color-brand-cyan);
  color: #000;
}

.rationale {
  padding: 0.75rem 1.5rem;
  background: rgba(251, 191, 36, 0.1);
  border-bottom: 1px solid var(--glass-border);
  font-size: 0.875rem;
  color: var(--color-text-muted);
}

.code-block {
  flex: 1;
  overflow: auto;
  padding: 1.5rem;
  background: #0d1117;
}

.code-block pre {
  margin: 0;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 0.875rem;
  line-height: 1.7;
  color: #e6edf3;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
