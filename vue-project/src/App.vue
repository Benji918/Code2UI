<script setup>
import NavBar from './components/NavBar.vue'
import GeneratorForm from './components/GeneratorForm.vue'
</script>

<template>
  <div class="app-container">
    <NavBar />

    <main class="container py-5">
      <div class="row align-items-center min-vh-75">
        <div class="col-lg-6 mb-5 mb-lg-0">
          <div class="pe-lg-5 animate-fade-in delay-100">
            <h1 class="display-3 fw-bold mb-4 lh-tight text-white">
              Transform Your <br />
              <span class="text-gradient-cyan">OpenAPI Spec</span> <br />
              Into Production <span class="text-gradient-pink">UI</span>
            </h1>
            <p class="lead text-white mb-5" style="opacity: 0.9;">
              Upload your OpenAPI/Swagger JSON spec with supporting docs and diagrams. Get production-ready Vue components, admin dashboards, and API testing interfaces in seconds.
            </p>
            
            <div class="d-flex gap-3">
              <a href="#" class="btn btn-cyan">Start Generating <i class="bi bi-arrow-right"></i></a>
              <a href="#" class="btn btn-outline-light px-4">View Examples</a>
            </div>
            
             <!-- Mock Code Preview decoration similar to image -->
             <div class="mt-5 p-3 rounded-3 border border-secondary bg-black bg-opacity-50 font-monospace small text-white-75" style="max-width: 400px; border-color: var(--color-border) !important;">
               <div class="d-flex gap-2 mb-2">
                 <span class="rounded-circle bg-danger" style="width:10px;height:10px"></span>
                 <span class="rounded-circle bg-warning" style="width:10px;height:10px"></span>
                 <span class="rounded-circle bg-success" style="width:10px;height:10px"></span>
                 <span class="ms-auto text-white-50">openapi.json</span>
               </div>
               <div style="color: #a5b4fc">
                 {<br>
                 &nbsp;&nbsp;<span style="color: #6ee7b7">"openapi"</span>: <span style="color: #fca5a5">"3.0.0"</span>,<br>
                 &nbsp;&nbsp;<span style="color: #6ee7b7">"paths"</span>: {<br>
                 &nbsp;&nbsp;&nbsp;&nbsp;<span style="color: #6ee7b7">"/users"</span>: { ... }<br>
                 &nbsp;&nbsp;}<br>
                 }
               </div>
             </div>
          </div>
        </div>
        
        <div class="col-lg-6">
          <GeneratorForm />
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.app-container {
  min-height: 100vh;
}

.min-vh-75 {
  min-height: 75vh;
}
</style>
