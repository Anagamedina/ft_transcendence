// HTTP ADAPTER — Axios a /api con withCredentials (cookie httpOnly).

import api from './api.js'

//creamos el adapter 
const httpAdapter = {
  get(url, config = {}) {
    return api.get(url, config)
  },

  post(url, data = {}, config = {}) {
    return api.post(url, data, config)
  },

  patch(url, data = {}, config = {}) {
    return api.patch(url, data, config)
  },

  delete(url, config = {}) {
    return api.delete(url, config)
  },
}

export default httpAdapter