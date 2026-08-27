import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    component: () => import('../views/public/LandingView.vue')
  },
  {
  path: '/test',
  component: () => import('../views/public/TestView.vue')
}
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
