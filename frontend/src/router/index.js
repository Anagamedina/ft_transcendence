import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";

const routes = [
  {
    path: "/",
    component: () => import("../views/public/LandingView.vue"),
  },
  {
    path: "/login",
    component: () => import("../views/public/LoginView.vue"),
  },
  {
    path: "/register",
    component: () => import("../views/public/RegisterView.vue"),
  },
  {
    path: "/dashboard",
    component: () => import("../views/client/DashboardView.vue"),
    meta: {
      requiresAuth: true, //tells the router: "this route requires authentication" so we can not access directly 
    },
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
  {
    path: "/admin/clients",
    component: () => import("../views/admin/ClientsView.vue"),
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

router.beforeEach(async (to) => {
  const authStore = useAuthStore();

  if (to.meta.requiresAuth) {  //if we try a direct access router checks if authentication is required (protected page), then if user is authenticated
    await authStore.initializeAuth();

    if (!authStore.isAuthenticated) {
      return "/login";
    }
  }
});

export default router;
