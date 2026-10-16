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
  // Public sign-up with a 7-day trial (F15-P, #166)
  {
    path: "/prueba",
    component: () => import("../views/public/TrialView.vue"),
  },
  {
    path: "/register",
    redirect: "/prueba",
  },
  // Accept an invitation: /registro?invitacion=CODE (F6, #167).
  // Public, and not in the guard's auth pages: the view itself tells a user
  // who is already logged in to log out first, instead of redirecting them.
  {
    path: "/registro",
    component: () => import("../views/public/AcceptInvitationView.vue"),
  },
  {
    path: "/legal",
    component: () => import("../views/public/LegalView.vue"),
    // LegalView scrolls to its own anchors, after switching to the right tab
    meta: { handlesHashScroll: true },
  },
  {
    path: "/privacy",
    redirect: "/legal",
  },
  {
    path: "/terms",
    redirect: "/legal",
  },
  {
    path: "/status",
    component: () => import("../views/public/StatusView.vue"),
  },

  // Old client home, kept so existing links and bookmarks still work
  {
    path: "/dashboard",
    redirect: "/app",
  },

  // Client routes
  {
    path: "/app", ///app becomes the client's home page
    component: () => import("../layouts/ClientLayout.vue"),
    meta: {
      requiresAuth: true,
      role: "client",
    },
    children: [
      {
        path: "",
        component: () => import("../views/client/DashboardView.vue"),
      },
      {
        path: "account",
        component: () => import("../views/client/AccountView.vue"),
      },
      {
        path: "alerts",
        name: "ClientAlerts",
        component: () => import("../views/client/AlertsView.vue"),
      },
      {
        path: "documents",
        name: "ClientDocuments",
        component: () => import("../views/client/DocumentsView.vue"),
      },
    ],
  },

  // Admin routes
  {
    path: "/admin",
    component: () => import("../views/admin/DashboardView.vue"),
    meta: {
      requiresAuth: true,
      role: "admin",
    },
  },
  {
    path: "/admin/clients",
    component: () => import("../views/admin/ClientsView.vue"),
    meta: {
      requiresAuth: true,
      role: "admin",
    },
  },
  {
    path: "/admin/clients/:id",
    component: () => import("../views/admin/ClientDetailView.vue"),
    props: true,
    meta: {
      requiresAuth: true,
      role: "admin",
    },
  },
  {
    path: "/admin/sites",
    component: () => import("../views/admin/SitesView.vue"),
    meta: {
      requiresAuth: true,
      role: "admin",
    },
  },
  {
    path: "/admin/sensors",
    name: "AdminSensors",
    component: () => import("../views/admin/SensorsView.vue"),
    meta: {
      requiresAuth: true,
      role: "admin",
    },
  },
  {
    path: "/admin/alerts",
    name: "AdminAlerts",
    component: () => import("../views/admin/AlertsView.vue"),
    meta: {
      requiresAuth: true,
      role: "admin",
    },
  },

  {
    path: "/admin/account",
    component: () => import("../views/admin/AccountView.vue"),
    meta: {
      requiresAuth: true,
      role: "admin",
    },
  },

  // 404 must be last
  // Redirects unknown routes to the 404 page
  {
    path: "/:pathMatch(.*)*",
    name: "NotFound",
    component: () => import("../views/public/NotFoundView.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,

  scrollBehavior(to, from, savedPosition) {
    // Checked first: on reload the saved position would override the view's scroll
    if (to.hash && to.meta.handlesHashScroll) {
      return false;
    }

    if (savedPosition) {
      return savedPosition;
    }

    if (to.hash) {
      return {
        el: to.hash,
        top: 80,
        behavior: "smooth",
      };
    }

    return { top: 0 };
  },
});

router.beforeEach(async (to) => {
  const authStore = useAuthStore();

  const requiresAuth = to.matched.some(
    (record) => record.meta.requiresAuth
  );

//meta.role replaces the old requiresAdmin and requiresClient
  const requiredRole = [...to.matched]
    .reverse()
    .find((record) => record.meta.role)?.meta.role;

  const isAuthPage = ["/login", "/prueba"].includes(to.path);

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

  // Protected route: authenticated user must have the required role
  //A client attempting to access an admin page is redirected to /app, and vice versa
  if (requiredRole && authStore.role !== requiredRole) {
    if (authStore.isAdmin) {
      return "/admin";
    }

    if (authStore.isClient) {
      return "/app";
    }

  // Avoid redirecting indefinitely between protected and login routes
    return { name: "NotFound" };
  }

  // Logged-in users should go to their role-specific home page
  if (isAuthPage && authStore.isAuthenticated) {
    return authStore.isAdmin ? "/admin" : "/app";
  }

  return true;
});

export default router;
