<script setup>
/**
 * HeroSection.vue - Landing page hero content
 */
</script>

<template>
  <div class="hero-section animate-fade-in delay-100">
    <h1 class="display-3 fw-bold mb-4 lh-tight text-white">
      Transform Your <br />
      <span class="text-gradient-cyan">OpenAPI Spec</span> <br />
      Into Production <span class="text-gradient-pink">UI</span>
    </h1>
    
    <p class="lead text-white mb-5" style="opacity: 0.9;">
      Upload your OpenAPI/Swagger JSON spec with supporting docs and diagrams. 
      Get production-ready Vue components, admin dashboards, and API testing interfaces in seconds.
    </p>
    
    <div class="d-flex gap-3 mb-5">
      <a href="#generator" class="btn btn-cyan">
        Start Generating <i class="bi bi-arrow-right ms-2"></i>
      </a>
      <router-link to="/history" class="btn btn-outline-light px-4">
        View History
      </router-link>
    </div>
    
    <!-- Code Preview Decoration -->
    <div class="code-preview-box">
      <div class="code-header">
        <span class="dot dot-red"></span>
        <span class="dot dot-yellow"></span>
        <span class="dot dot-green"></span>
        <span class="code-filename">openapi.json</span>
      </div>
      <div class="code-content">
        <pre><code>{
  <span class="code-key">"openapi"</span>: <span class="code-string">"3.0.0"</span>,
  <span class="code-key">"paths"</span>: {
    <span class="code-key">"/users"</span>: { ... }
  }
}</code></pre>
      </div>
    </div>
  </div>
</template>

<style scoped>
.hero-section {
  padding-right: 2rem;
}

.code-preview-box {
  max-width: 400px;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--glass-border);
  background: rgba(0, 0, 0, 0.5);
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}

.code-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: rgba(0, 0, 0, 0.3);
  border-bottom: 1px solid var(--glass-border);
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.dot-red { background: #ef4444; }
.dot-yellow { background: #f59e0b; }
.dot-green { background: #22c55e; }

.code-filename {
  margin-left: auto;
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.code-content {
  padding: 1rem;
}

.code-content pre {
  margin: 0;
  font-size: 0.875rem;
  line-height: 1.6;
  color: #a5b4fc;
}

.code-key {
  color: #6ee7b7;
}

.code-string {
  color: #fca5a5;
}
</style>
