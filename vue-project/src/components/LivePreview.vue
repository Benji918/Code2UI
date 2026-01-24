<script setup>
/**
 * LivePreview.vue - Render generated Vue components using vue3-sfc-loader
 * 
 * This allows full Vue functionality (script setup, reactivity, imports) 
 * inside a secure iframe sandbox. Supports multi-component imports.
 */
import { ref, watch, onMounted } from 'vue'

const props = defineProps({
  code: {
    type: String, // The entry code to render
    required: true
  },
  filename: {
    type: String,
    default: 'Component.vue'
  },
  projectContext: {
    type: Object, // The entire generatedUI object containing all components
    default: () => ({ components: [] })
  }
})

const iframeRef = ref(null)
const previewError = ref(null)

const buildPreviewDocument = (entryCode) => {
  // Escape backticks for template string injection
  const escapedEntryCode = entryCode.replace(/`/g, '\\`').replace(/\${/g, '\\${')
  
  // Serialize the project context to pass it to the iframe
  const contextJson = JSON.stringify(props.projectContext).replace(/`/g, '\\`').replace(/<\/script>/g, '<\\/script>')
  
  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  
  <!-- Bootstrap 5 & Icons -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
  
  <!-- Vue 3 & SFC Loader -->
  <script src="https://unpkg.com/vue@3/dist/vue.global.js"><\/script>
  <script src="https://cdn.jsdelivr.net/npm/vue3-sfc-loader/dist/vue3-sfc-loader.js"><\/script>
  
  <style>
    :root {
      --color-bg-primary: #030712;
      --color-bg-secondary: #0f172a;
      --color-brand-cyan: #22d3ee;
      --color-text-main: #ffffff;
      --color-text-muted: #94a3b8;
      --glass-bg: #111827;
      --glass-border: rgba(255, 255, 255, 0.1);
    }
    
    body {
      background: var(--color-bg-primary);
      color: var(--color-text-main);
      font-family: 'Inter', system-ui, -apple-system, sans-serif;
      padding: 1rem;
      min-height: 100vh;
    }
    
    /* Code2UI Base Styles injected here for consistency */
    .btn-primary {
      background-color: var(--color-brand-cyan);
      border-color: var(--color-brand-cyan);
      color: #000;
      font-weight: 500;
    }
    .btn-primary:hover {
      background-color: #06b6d4;
      border-color: #06b6d4;
      color: #000;
    }
    
    .form-control, .form-select {
      background-color: var(--glass-bg);
      border-color: var(--glass-border);
      color: var(--color-text-main);
    }
    .form-control:focus, .form-select:focus {
      background-color: var(--glass-bg);
      border-color: var(--color-brand-cyan);
      color: var(--color-text-main);
      box-shadow: 0 0 0 0.25rem rgba(34, 211, 238, 0.25);
    }
    
    .card {
      background-color: var(--glass-bg);
      border-color: var(--glass-border);
    }
    
    .table-dark {
      --bs-table-bg: transparent;
      color: var(--color-text-main);
    }
  </style>
</head>
<body>
  <div id="app"></div>
  
  <script>
    const { loadModule } = window['vue3-sfc-loader'];
    
    // Injected project context
    const projectContext = JSON.parse(\`${contextJson}\`);
    const entryFilename = '${props.filename}';
    const entryCode = \`${escapedEntryCode}\`;
    
    const options = {
      moduleCache: {
        vue: window.Vue
      },
      async getFile(url) {
        // Normalizing path
        const filename = url.replace('./', '').replace('/', '');
        
        // 1. Check if it's the entry file
        if (filename === entryFilename) {
          return entryCode;
        }
        
        // 2. Check components list
        const comp = projectContext.components.find(c => c.filename === filename);
        if (comp) {
          return comp.code;
        }
        
        // 3. Check extra files
        if (filename === 'App.vue') return projectContext.app_entry;
        if (filename === 'apiClient.js') return projectContext.api_client;
        
        return Promise.reject(new Error('File not found: ' + url));
      },
      addStyle(textContent) {
        const style = document.createElement('style');
        style.textContent = textContent;
        document.head.appendChild(style);
      },
      log(type, ...args) {
        console.log(type, ...args);
      }
    }
    
    const app = Vue.createApp(
      Vue.defineAsyncComponent(() => loadModule('./' + entryFilename, options))
    );
    
    app.mount('#app');
    
    window.onerror = function(message) {
      window.parent.postMessage({ type: 'preview-error', message }, '*');
    };
  <\/script>
</body>
</html>`
}

const updateIframe = () => {
  if (iframeRef.value && props.code) {
    try {
      const doc = iframeRef.value.contentDocument || iframeRef.value.contentWindow.document
      doc.open()
      doc.write(buildPreviewDocument(props.code))
      doc.close()
      previewError.value = null
    } catch (e) {
      previewError.value = 'Failed to render preview'
      console.error('Preview error:', e)
    }
  }
}

watch(() => props.code, updateIframe)

onMounted(() => {
  updateIframe()
  // Listen for errors from iframe
  window.addEventListener('message', (e) => {
    if (e.data && e.data.type === 'preview-error') {
      previewError.value = 'Runtime Error: ' + e.data.message
    }
  })
})
</script>

<template>
  <div class="live-preview">
    <div class="preview-header">
      <div class="d-flex align-items-center gap-2">
        <i class="bi bi-play-circle-fill text-success"></i>
        <span class="fw-semibold">Live Preview</span>
        <span class="badge bg-secondary">{{ filename }}</span>
      </div>
      <small class="text-white-50">Fully interactive Vue 3 environment</small>
    </div>
    
    <div class="preview-frame-wrapper">
      <div v-if="previewError" class="preview-error">
        <i class="bi bi-exclamation-triangle-fill text-danger me-2"></i>
        {{ previewError }}
      </div>
      
      <iframe
        ref="iframeRef"
        class="preview-frame"
        sandbox="allow-scripts allow-same-origin allow-forms allow-modals"
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
  background: #000;
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
  top: 1rem;
  left: 50%;
  transform: translateX(-50%);
  padding: 0.75rem 1.5rem;
  background: rgba(220, 38, 38, 0.2);
  border: 1px solid #dc2626;
  border-radius: 8px;
  color: #fca5a5;
  z-index: 10;
  white-space: nowrap;
}
</style>
