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
  {
    path: "/admin",
    component: () => import("../views/admin/DashboardView.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition // browser back/forward: restore previous scroll position
    }
    return { top: 0 } // any other navigation: scroll to top
  },
})

export default router;
