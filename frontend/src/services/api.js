// API FACADE — punto único de llamadas HTTP.
// Flujo: View/Store → api.js → MockAdapter | HttpAdapter (mismo shape OpenAPI).

import axios from 'axios'

const api = axios.create({ //creamos nuestro propio cliente HTTP Axios
  baseURL: import.meta.env.VITE_API_URL, //Usa como URL base de la API el valor que está guardado en la variable de entorno VITE_API_URL
  timeout: 10000,//si servidor no responde, en 10 segundos, Axios considera que la solicitud ha fallado
  withCredentials: true, //con cookie de sesion
})

export default api