<script setup>
/**
 * LivePreview.vue - Render generated Vue components in an iframe sandbox
 * 
 * This component creates an isolated environment to preview generated code.
 */
import { ref, computed, watch, onMounted } from 'vue'

const props = defineProps({
  code: {
    type: String,
    required: true
  },
  filename: {
    type: String,
    default: 'Component.vue'
  }
})

const iframeRef = ref(null)
const previewError = ref(null)

// Helper to build the preview document
const buildPreviewDocument = () => {
  // For Vue SFC, we can't directly render without compilation
  // Instead, show a styled representation of what the component would look like
  
  // Extract template section from Vue SFC
  const templateRegex = /<template>([\s\S]*?)<\/template>/
  const templateMatch = props.code.match(templateRegex)
  const templateContent = templateMatch ? templateMatch[1] : '<p>No template found</p>'
  
  // Extract style section
  const styleRegex = /<style[^>]*>([\s\S]*?)<\/style>/
  const styleMatch = props.code.match(styleRegex)
  const styleContent = styleMatch ? styleMatch[1] : ''
  
  // Build HTML parts separately to avoid Vue compiler issues
  const doctype = '<!DOCTYPE html>'
  const htmlOpen = '<html>'
  const htmlClose = '<' + '/html>'
  const headOpen = '<head>'
  const headClose = '<' + '/head>'
  const styleOpen = '<style>'
  const styleClose = '<' + '/style>'
  const bodyOpen = '<body>'
  const bodyClose = '<' + '/body>'
  const scriptOpen = '<script>'
  const scriptClose = '<' + '/script>'
  
  return [
    doctype,
    htmlOpen,
    headOpen,
    '<meta charset="UTF-8">',
    '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
    '<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">',
    '<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">',
    styleOpen,
    `:root {
      --color-bg-primary: #030712;
      --color-bg-secondary: #0f172a;
      --color-brand-cyan: #22d3ee;
      --color-text-main: #ffffff;
      --color-text-muted: #94a3b8;
      --glass-bg: #111827;
      --glass-border: rgba(255, 255, 255, 0.1);
    }
    
    * { box-sizing: border-box; }
    
    body {
      margin: 0;
      padding: 1.5rem;
      background: var(--color-bg-primary);
      color: var(--color-text-main);
      font-family: 'Inter', -apple-system, sans-serif;
      min-height: 100vh;
    }
    
    .btn-primary {
      background: var(--color-brand-cyan);
      border: none;
      color: #000;
    }
    
    .table-dark { --bs-table-bg: transparent; }
    
    .form-control {
      background: rgba(255,255,255,0.05);
      border-color: var(--glass-border);
      color: #fff;
    }
    
    .form-control:focus {
      background: rgba(255,255,255,0.1);
      border-color: var(--color-brand-cyan);
      color: #fff;
      box-shadow: 0 0 0 0.2rem rgba(34, 211, 238, 0.25);
    }
    
    .card {
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
    }
    
    ${styleContent}`,
    styleClose,
    headClose,
    bodyOpen,
    '<div class="preview-wrapper">',
    templateContent,
    '</div>',
    scriptOpen,
    `// Mock Vue reactive data for static preview
    document.querySelectorAll('[v-if]').forEach(function(el) {});
    document.querySelectorAll('[v-for]').forEach(function(el) { el.style.display = 'block'; });`,
    scriptClose,
    bodyClose,
    htmlClose
  ].join('\n')
}

watch(() => props.code, () => {
  updateIframe()
})

onMounted(() => {
  updateIframe()
})

const updateIframe = () => {
  if (iframeRef.value) {
    try {
      const doc = iframeRef.value.contentDocument || iframeRef.value.contentWindow.document
      const htmlContent = buildPreviewDocument()
      doc.open()
      doc.write(htmlContent)
      doc.close()
      previewError.value = null
    } catch (e) {
      previewError.value = 'Failed to render preview'
      console.error('Preview error:', e)
    }
  }
}
</script>

<template>
  <div class="live-preview">
    <div class="preview-header">
      <div class="d-flex align-items-center gap-2">
        <i class="bi bi-eye text-success"></i>
        <span class="fw-semibold">Live Preview</span>
        <span class="badge bg-secondary">{{ filename }}</span>
      </div>
      <small class="text-muted">Static HTML preview (Vue directives not evaluated)</small>
    </div>
    
    <div class="preview-frame-wrapper">
      <div v-if="previewError" class="preview-error">
        <i class="bi bi-exclamation-triangle text-warning me-2"></i>
        {{ previewError }}
      </div>
      
      <iframe
        ref="iframeRef"
        class="preview-frame"
        sandbox="allow-scripts allow-same-origin"
        title="Component Preview"
      ></iframe>
    </div>
  </div>
</template>

<style scoped>
.live-preview {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: 12px;
  overflow: hidden;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: rgba(0, 0, 0, 0.3);
  border-bottom: 1px solid var(--glass-border);
}

.preview-frame-wrapper {
  flex: 1;
  position: relative;
  min-height: 400px;
}

.preview-frame {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: none;
  background: #030712;
}

.preview-error {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  padding: 1rem 2rem;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  color: #fca5a5;
  z-index: 10;
}
</style>
