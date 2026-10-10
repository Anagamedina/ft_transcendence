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
      requiresAuth: true,  //tells the router: "this route requires authentication" so we can not access directly 
      requiresClient: true,
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
    path: "/status",
    component: () => import("../views/public/StatusView.vue"),
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
    meta: {
      requiresAuth: true,
      requiresAdmin: true,
    },
  },
  {
    path: "/admin/clients",
    component: () => import("../views/admin/ClientsView.vue"),
    meta: {
      requiresAuth: true,
      requiresAdmin: true,
    },
  },
  {
    path: "/admin/clients/:id",
    component: () => import("../views/admin/ClientDetailView.vue"),
    props: true,
    meta: {
      requiresAuth: true,
      requiresAdmin: true,
    },
  },
  {
    path: "/admin/sites",
    component: () => import("../views/admin/SitesView.vue"),
    meta: {
      requiresAuth: true,
      requiresAdmin: true,
    },
  },
  // Redirects unknown routes to the 404 page
  {
  path: "/:pathMatch(.*)*",
  component: () => import("../views/public/NotFoundView.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,

  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition;
    }
    return { top: 0 };
  },
});

router.beforeEach(async (to) => {
  const authStore = useAuthStore();

  const requiresAuth = to.matched.some(
    (record) => record.meta.requiresAuth
  );

  const requiresAdmin = to.matched.some(
    (record) => record.meta.requiresAdmin
  );

  const requiresClient = to.matched.some(
    (record) => record.meta.requiresClient
  );

  const isAuthPage = ["/login", "/register"].includes(to.path);

  if (requiresAuth || isAuthPage) {
    await authStore.initializeAuth();
  }

  // Redirect unauthenticated users to the login page.
  if (requiresAuth && !authStore.isAuthenticated) {
    return {
      path: "/login",
      query: { redirect: to.fullPath },
    };
  }

  // Allow only administrators to access admin routes.
  if (requiresAdmin && !authStore.isAdmin) {
    return authStore.isAuthenticated
      ? "/dashboard"
      : "/login";
  }

  // Allow only clients to access the client dashboard.
  if (requiresClient && authStore.isAdmin) {
    return authStore.isAdmin ? "/admin" : "/login";
  }

  // Redirect authenticated users away from login and registration pages.
  if (isAuthPage && authStore.isAuthenticated) {
    return authStore.isAdmin ? "/admin" : "/dashboard";
  }

  return true;
});

export default router;