// PASSWORDS
// The password rule shown in every form where someone chooses a password:
// register (/prueba), accept an invitation and Mi cuenta. Same rule as the
// backend (backend/app/shared/passwords.py); the backend also rejects common
// passwords and answers 422 WEAK_PASSWORD with a message we show as is.

export const PASSWORD_MIN_LENGTH = 12
export const PASSWORD_MAX_LENGTH = 128

// Client-side check before calling the API. Returns the problem in Spanish,
// or null when the password passes what the frontend can check.
export function passwordProblem(password, email = '') {
  if (password.length < PASSWORD_MIN_LENGTH) {
    return `La contraseña tiene que tener al menos ${PASSWORD_MIN_LENGTH} caracteres.`
  }
  if (password.length > PASSWORD_MAX_LENGTH) {
    return `La contraseña no puede pasar de ${PASSWORD_MAX_LENGTH} caracteres.`
  }

  const lower = password.toLowerCase()
  const normalizedEmail = email.trim().toLowerCase()
  const localPart = normalizedEmail.split('@')[0]
  // A 1-3 letter user ("ana") shows up in many passwords by chance
  if (normalizedEmail && (lower.includes(normalizedEmail) || (localPart.length >= 4 && lower.includes(localPart)))) {
    return 'La contraseña no puede contener tu email.'
  }

  return null
}
