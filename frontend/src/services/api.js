// API FACADE — punto único de llamadas HTTP.
// Flujo: View/Store → api.js → MockAdapter | HttpAdapter (mismo shape OpenAPI).

import axios from 'axios'

const api = axios.create({ //creamos nuestro propio cliente HTTP Axios
  baseURL: import.meta.env.VITE_API_URL, //Usa como URL base de la API el valor que está guardado en la variable de entorno VITE_API_URL
  timeout: 10000,//si servidor no responde, en 10 segundos, Axios considera que la solicitud ha fallado
})

export default api

/*
export class AppError {
  constructor(message, status = null, code = null) {
    this.message = message; // Message lisible pour l'utilisateur
    this.status = status;   // HTTP code (ex: 404, 500)
    this.code = code;       // Code d'erreur métier propre à votre API (ex: 'PASSWORD_TOO_WEAK')
  }
}*/