import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/Home.vue'),
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('../views/Settings.vue'),
  },
  {
    path: '/files',
    name: 'files',
    component: () => import('../views/Files.vue'),
  },
  {
    path: '/files/:path(.*)',
    name: 'file-viewer',
    component: () => import('../views/FileViewer.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
