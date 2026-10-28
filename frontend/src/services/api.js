// API FACADE — single entry point for HTTP calls.
// Flow: View/Store → api.js → MockAdapter | HttpAdapter (same OpenAPI shape).

import axios from "axios";

const api = axios.create({
  // Create our own Axios HTTP client.
  baseURL: import.meta.env.VITE_API_URL, // Use the API base URL stored in the VITE_API_URL environment variable.
  timeout: 10000, // If the server does not respond within 10 seconds, Axios considers the request to have failed.
  withCredentials: true, // Include session cookies with requests.
});

let handlingUnauthorized = false;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const status = error.response?.status;
    const requestUrl = error.config?.url ?? "";

    const isAuthRequest =
      requestUrl.includes("/api/auth/login") ||
      requestUrl.includes("/api/auth/register");

    if (status === 401 && !isAuthRequest && !handlingUnauthorized) {
      handlingUnauthorized = true;

      try {
        // Avoid importing the Pinia store here: it can create a circular dependency.
        // Clear the frontend auth state through the app's logout/session flow instead.
        if (typeof window !== "undefined") {
          const currentPath = window.location.pathname;
          const publicPaths = [
            "/",
            "/login",
            "/prueba",
            "/registro",
            "/legal",
            "/status",
          ];

          const isPublicPath = publicPaths.includes(currentPath);

          if (!isPublicPath && currentPath !== "/login") {
            const redirect = encodeURIComponent(
              window.location.pathname +
                window.location.search +
                window.location.hash,
            );

            window.location.replace(`/login?redirect=${redirect}`);
          }
        }
      } finally {
        handlingUnauthorized = false;
      }
    }

    return Promise.reject(error);
  },
);

export default api;
