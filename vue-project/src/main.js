/**
 * Code2UI - Vue.js Frontend Entry Point
 * 
 * Sets up Vue 3 with Vue Router for multi-page navigation.
 * The generated UI is rendered on a separate page as per implementation.md.
 */
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap-icons/font/bootstrap-icons.css'
import 'bootstrap'
import './assets/main.css'

import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'

import App from './App.vue'
import HomePage from './views/HomePage.vue'
import GeneratedUIPage from './views/GeneratedUIPage.vue'
import HistoryPage from './views/HistoryPage.vue'

// Define routes
const routes = [
    {
        path: '/',
        name: 'home',
        component: HomePage,
        meta: { title: 'Code2UI - Transform OpenAPI to Production UI' }
    },
    {
        path: '/generated/:id?',
        name: 'generated',
        component: GeneratedUIPage,
        meta: { title: 'Generated UI - Code2UI' },
        props: true
    },
    {
        path: '/history',
        name: 'history',
        component: HistoryPage,
        meta: { title: 'Generation History - Code2UI' }
    }
]

// Create router instance
const router = createRouter({
    history: createWebHistory(),
    routes
})

// Update page title on navigation
router.beforeEach((to, from, next) => {
    document.title = to.meta.title || 'Code2UI'
    next()
})

// Create and mount app
const app = createApp(App)
app.use(router)
app.mount('#app')
