<script setup>
/**
 * NavBar.vue - Main navigation component with router links
 */
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const isActive = (path) => {
  return route.path === path
}
</script>

<template>
  <nav class="navbar navbar-expand-lg navbar-dark py-3">
    <div class="container">
      <!-- Brand -->
      <router-link to="/" class="navbar-brand fs-4 fw-bold d-flex align-items-center">
        <div class="brand-icon me-2">
          <i class="bi bi-braces-asterisk"></i>
        </div>
        <span class="text-white">Code2</span><span class="text-gradient-cyan">UI</span>
      </router-link>
      
      <!-- Mobile Toggle -->
      <button 
        class="navbar-toggler border-0" 
        type="button" 
        data-bs-toggle="collapse" 
        data-bs-target="#navbarNav"
      >
        <span class="navbar-toggler-icon"></span>
      </button>
      
      <!-- Nav Links -->
      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav ms-auto gap-1">
          <li class="nav-item">
            <router-link 
              to="/" 
              class="nav-link px-3"
              :class="{ 'active': isActive('/') }"
            >
              <i class="bi bi-lightning-charge me-1"></i>
              Generator
            </router-link>
          </li>
          <li class="nav-item">
            <router-link 
              to="/history" 
              class="nav-link px-3"
              :class="{ 'active': isActive('/history') }"
            >
              <i class="bi bi-clock-history me-1"></i>
              History
            </router-link>
          </li>
          <li class="nav-item ms-lg-3">
            <a 
              href="https://github.com" 
              target="_blank" 
              class="btn btn-sm btn-outline-light rounded-pill px-3"
            >
              <i class="bi bi-github"></i>
            </a>
          </li>
        </ul>
      </div>
    </div>
  </nav>
</template>

<style scoped>
.navbar {
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--glass-border);
}

.brand-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--color-brand-cyan), var(--color-brand-pink));
  border-radius: 8px;
  font-size: 1.25rem;
  color: #000;
}

.nav-link {
  color: var(--color-text-muted);
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.nav-link:hover {
  color: var(--color-text-main);
  background: rgba(255, 255, 255, 0.05);
}

.nav-link.active {
  color: var(--color-brand-cyan);
  background: rgba(34, 211, 238, 0.1);
}
</style>
