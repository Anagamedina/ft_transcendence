// API ERROR
// Spanish text for an error already normalized by the adapter
// ({ code, message }). The adapter's own messages (network, client) are in
// English, so those codes get a fixed text; backend messages are kept.

const MESSAGE_BY_CODE = {
  NETWORK_ERROR: 'No hemos podido conectar con el servidor. Inténtalo de nuevo.',
  CLIENT_ERROR: 'Ha ocurrido un error inesperado. Inténtalo de nuevo.',
  UNKNOWN_ERROR: 'Ha ocurrido un error inesperado. Inténtalo de nuevo.',
}

export function apiErrorMessage(error, fallback) {
  return MESSAGE_BY_CODE[error?.code] || error?.message || fallback
}
