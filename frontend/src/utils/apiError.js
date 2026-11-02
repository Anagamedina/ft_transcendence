// API ERROR
// Spanish text for an error already normalized by the adapter
// ({ code, message }). The adapter's own messages (network, client) are in
// English, so those codes get a fixed text; backend messages are kept.
// Every form shows its general error (<FormError>) with this function.

const MESSAGE_BY_CODE = {
  NETWORK_ERROR:
    "No hemos podido conectar con el servidor. Inténtalo de nuevo.",
  CLIENT_ERROR: "Ha ocurrido un error inesperado. Inténtalo de nuevo.",
  UNKNOWN_ERROR: "Ha ocurrido un error inesperado. Inténtalo de nuevo.",
  // Nginx rate limit of the public forms (login, register, invitations)
  TOO_MANY_REQUESTS: "Demasiados intentos, prueba en unos minutos.",
};

export function apiErrorMessage(error, fallback) {
  return MESSAGE_BY_CODE[error?.code] || error?.message || fallback;
}
