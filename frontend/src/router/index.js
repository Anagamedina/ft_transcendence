import { createRouter, createWebHistory } from "vue-router";

const routes = [
  {
    path: "/",
    component: () => import("../views/public/LandingView.vue"),
  },
  {
    path: "/privacy",
    component: () => import("../views/public/PrivacyView.vue"),
  },
  {
    path: "/terms",
    component: () => import("../views/public/TermsView.vue"),
  },
  {
    path: "/test",
    component: () => import("../views/public/TestView.vue"),
  },
  {
    path: "/sensors/:id",
    component: () => import("../views/public/SensorDetailView.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
