<template>
  <nav class="navbar navbar-expand-lg navbar-dark py-4">
    <div class="container">
      <a class="navbar-brand fs-3 fw-bold" href="#">
        <i class="bi bi-code-square me-2 text-primary"></i>
        <span class="text-white">Code2</span><span class="text-gradient">UI</span>
      </a>
      <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav ms-auto gap-3">
          <li class="nav-item">
            <a class="nav-link active" href="#">Generator</a>
          </li>
          <li class="nav-item">
            <a class="nav-link" href="#">History</a>
          </li>
          <li class="nav-item">
            <a class="nav-link" href="#">Settings</a>
          </li>
           <li class="nav-item ms-lg-3">
            <a class="btn btn-sm btn-outline-light rounded-pill px-3" href="https://github.com" target="_blank">
              <i class="bi bi-github"></i>
            </a>
          </li>
        </ul>
      </div>
    </div>
  </nav>
</template>

<style scoped>
.navbar-brand .text-gradient {
  font-weight: 800;
}
</style>
