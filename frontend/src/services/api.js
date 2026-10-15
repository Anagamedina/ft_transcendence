// API FACADE — punto único de llamadas HTTP.
// Flujo: View/Store → api.js → MockAdapter | HttpAdapter (mismo shape OpenAPI).

import axios from "axios";

const api = axios.create({
  //creamos nuestro propio cliente HTTP Axios
  baseURL: import.meta.env.VITE_API_URL, //Usa como URL base de la API el valor que está guardado en la variable de entorno VITE_API_URL
  timeout: 10000, //si servidor no responde, en 10 segundos, Axios considera que la solicitud ha fallado
  withCredentials: true, //con cookie de sesion
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
