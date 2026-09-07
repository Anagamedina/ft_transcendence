// HTTP ADAPTER — Axios HTTP calls and common error normalization.

import api from './api.js'


/*
 * Axios receives the full error object.
 * response contains the HTTP response.
 * response.data contains the JSON returned by the backend.
 * The backend error is nested inside response.data.error.
 *
 * error = {                    // Full Axios error
 *   response: {                 // HTTP response
 *     status: 404,
 *     data: {                   // JSON returned by the backend
 *       error: {                // Backend error object
 *         code: 'SENSOR_NOT_FOUND',
 *         message: 'Sensor not found',
 *         details: null
 *       }
 *     }
 *   }
 * }
 */

// Normalize API errors into a common format

function normalizeError(error) { //'error' is the error object received from Axios
  // Backend responded with an HTTP error
  if (error.response) {
    const status = error.response.status
    const backendError = error.response.data?.error //if data exists, access data.error, otherwise return undefined instead of throwing an error

    let code = 'UNKNOWN_ERROR'
    let message = 'An error occurred.'
    let details = null

    if (backendError) {
      code = backendError.code || code
      message = backendError.message || message
      details = backendError.details
    }

    return {
      status,
      code,
      message,
      details,
    }
  }

  // Request was sent but the backend did not respond
  if (error.request) {
    return {
      status: null,
      code: 'NETWORK_ERROR',
      message: 'The server is unreachable.',
      details: null,
    }
  }

  // Other frontend / Axios error
  return {
    status: null,
    code: 'CLIENT_ERROR',
    message: error.message || 'An error occurred.',
    details: null,
  }
}


//*** Here we create the HTTP adapter ***

const httpAdapter = {
  async get(url, config = {}) { //async = function will likely have to wait for something that takes time
    try {
      return await api.get(url, config) //await = Wait for this request to complete before continuing
    } catch (error) {
      throw normalizeError(error)
    }
  },

  async post(url, data = {}, config = {}) {
    try {
      return await api.post(url, data, config)
    } catch (error) {
      throw normalizeError(error)
    }
  },

  async patch(url, data = {}, config = {}) {
    try {
      return await api.patch(url, data, config)
    } catch (error) {
      throw normalizeError(error)
    }
  },

  async delete(url, config = {}) {
    try {
      return await api.delete(url, config)
    } catch (error) {
      throw normalizeError(error)
    }
  },
}

export default httpAdapter