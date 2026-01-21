<script setup>
/**
 * HomePage.vue - Landing page with generator form
 * 
 * The main entry point where users configure and start UI generation.
 */
import GeneratorForm from '../components/GeneratorForm.vue'
import HeroSection from '../components/HeroSection.vue'
</script>

<template>
  <main class="home-page">
    <div class="container py-5">
      <div class="row align-items-center min-vh-75">
        <div class="col-lg-6 mb-5 mb-lg-0">
          <HeroSection />
        </div>
        
        <div class="col-lg-6">
          <GeneratorForm />
        </div>
      </div>
    </div>
    
    <!-- Features Section -->
    <section class="features-section py-5">
      <div class="container">
        <h2 class="text-center mb-5 fw-bold">
          Why <span class="text-gradient-cyan">Code2UI</span>?
        </h2>
        
        <div class="row g-4">
          <div class="col-md-4">
            <div class="feature-card glass-panel p-4 h-100">
              <div class="feature-icon mb-3">
                <i class="bi bi-lightning-charge-fill fs-1 text-warning"></i>
              </div>
              <h4 class="fw-bold">Instant Generation</h4>
              <p class="text-white-50 mb-0">
                Transform your OpenAPI spec into a fully functional Vue.js interface in seconds, not hours.
              </p>
            </div>
          </div>
          
          <div class="col-md-4">
            <div class="feature-card glass-panel p-4 h-100">
              <div class="feature-icon mb-3">
                <i class="bi bi-cpu-fill fs-1 text-gradient-cyan"></i>
              </div>
              <h4 class="fw-bold">AI-Powered</h4>
              <p class="text-white-50 mb-0">
                Leverages Mistral AI to understand your API structure and generate intelligent, context-aware components.
              </p>
            </div>
          </div>
          
          <div class="col-md-4">
            <div class="feature-card glass-panel p-4 h-100">
              <div class="feature-icon mb-3">
                <i class="bi bi-code-slash fs-1 text-gradient-pink"></i>
              </div>
              <h4 class="fw-bold">Production Ready</h4>
              <p class="text-white-50 mb-0">
                Get clean, maintainable Vue 3 code with proper error handling, loading states, and modern styling.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  </main>
</template>

<style scoped>
.home-page {
  flex: 1;
}

.min-vh-75 {
  min-height: 75vh;
}

.features-section {
  background: rgba(0, 0, 0, 0.3);
  border-top: 1px solid var(--glass-border);
}

.feature-card {
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
}

.feature-icon {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
}
</style>
