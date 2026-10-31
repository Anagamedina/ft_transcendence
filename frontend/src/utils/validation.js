// VALIDATION
// The field rules shared by every form where people or organization data is
// typed: register (/prueba), accept an invitation, new client wizard,
// "Hazte cliente", Mi cuenta, edit a user and invite. Same rules and
// messages as the backend (backend/app/shared/fields.py): if you change one,
// change both. Passwords have their own file (passwords.js).
//
// Each *Problem function returns the message in Spanish, or null when the
// value is valid. The normalize functions return what the API will store.

import { FIELD_LIMITS } from "./limits.js";

// Simple shape check; the backend does the strict validation (EmailStr)
export const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const SPACES = /\s+/g;
// Separators people type in tax ids and IBANs
const SEPARATORS = /[\s.-]/g;
const PHONE_SEPARATORS = /[\s.\-()]/g;
// Spanish phone: 9 digits starting with 6 or 7 (mobile) or 8 or 9 (landline)
const PHONE_PATTERN = /^[6789]\d{8}$/;
// NIF, NIE, CIF or a foreign tax id, without separators
const TAX_ID_PATTERN = /^[A-Z0-9]{8,15}$/;
const POSTAL_CODE_PATTERN = /^\d{5}$/;
// Spanish IBAN: ES and 22 digits
const IBAN_PATTERN = /^ES\d{22}$/;
const IBAN_MESSAGE =
  "Revisa el IBAN: tiene que ser español, empieza por ES y tiene 24 caracteres.";
// Letters (accents, ñ, ç included), digits, spaces and the signs of company
// names: "Hotel Mar, S.L.", "Ca n'Oller", "Mar & Sol (Gràcia)"
const ORGANIZATION_NAME_PATTERN = /^[\p{L}\p{N} .,'’&()-]+$/u;
// Letters and spaces, plus ' ’ - . (O'Neill, Pérez-Gil, Laura P.)
const PERSON_NAME_PATTERN = /^[\p{L} '’.-]+$/u;
// A name needs at least one letter (or digit, for an organization): "..." is not one
const HAS_LETTER = /\p{L}/u;
const HAS_LETTER_OR_DIGIT = /[\p{L}\p{N}]/u;

export const ORGANIZATION_NAME_MESSAGE =
  "El nombre solo puede tener letras, números, espacios y los signos . , ' - & ( ).";

// "  Hotel   Mar " → "Hotel Mar". NFC joins a letter and its accent.
export function cleanText(value) {
  return String(value ?? "")
    .normalize("NFC")
    .replace(SPACES, " ")
    .trim();
}

// "b-1234 5678" → "B12345678"
export function compactCode(value) {
  return String(value ?? "")
    .replace(SEPARATORS, "")
    .toUpperCase();
}

export function personNameProblem(value, max = FIELD_LIMITS.username) {
  const name = cleanText(value);
  if (!name) return "El nombre no puede estar vacío.";
  if (name.length > max)
    return `El nombre no puede pasar de ${max} caracteres.`;
  if (!PERSON_NAME_PATTERN.test(name) || !HAS_LETTER.test(name)) {
    return "El nombre solo puede tener letras, espacios, apóstrofos, guiones y puntos.";
  }
  return null;
}

export function organizationNameProblem(
  value,
  max = FIELD_LIMITS.organizationName,
) {
  const name = cleanText(value);
  if (!name) return "El nombre no puede estar vacío.";
  if (name.length > max)
    return `El nombre no puede pasar de ${max} caracteres.`;
  if (
    !ORGANIZATION_NAME_PATTERN.test(name) ||
    !HAS_LETTER_OR_DIGIT.test(name)
  ) {
    return ORGANIZATION_NAME_MESSAGE;
  }
  return null;
}

export function emailProblem(value, { required = true } = {}) {
  const email = String(value ?? "").trim();
  if (!email) return required ? "Escribe el email." : null;
  if (email.length > FIELD_LIMITS.email || !EMAIL_PATTERN.test(email)) {
    return "Escribe un email válido, por ejemplo nombre@empresa.com.";
  }
  return null;
}

export function normalizeEmail(value) {
  return String(value ?? "")
    .trim()
    .toLowerCase();
}

// The 9 digits, without separators or the +34 / 0034 prefix
function phoneDigits(value) {
  const number = String(value ?? "").replace(PHONE_SEPARATORS, "");
  if (number.startsWith("+34")) return number.slice(3);
  if (number.startsWith("0034")) return number.slice(4);
  return number;
}

export function phoneProblem(value) {
  const digits = phoneDigits(value);
  if (!digits) return "El teléfono es obligatorio.";
  if (!PHONE_PATTERN.test(digits)) {
    return "Escribe un teléfono español de 9 cifras, por ejemplo 612 345 678.";
  }
  return null;
}

// "612.34.56.78" → "+34 612 345 678", the format the API stores
export function normalizePhone(value) {
  const digits = phoneDigits(value);
  return `+34 ${digits.slice(0, 3)} ${digits.slice(3, 6)} ${digits.slice(6)}`;
}

export function taxIdProblem(value, { required = true } = {}) {
  const taxId = compactCode(value);
  if (!taxId) return required ? "Escribe el NIF o CIF." : null;
  if (!TAX_ID_PATTERN.test(taxId)) {
    return "Escribe un NIF o CIF válido: entre 8 y 15 letras o números.";
  }
  return null;
}

export function postalCodeProblem(value) {
  return POSTAL_CODE_PATTERN.test(String(value ?? "").trim())
    ? null
    : "Escribe un código postal de 5 cifras.";
}

// Only the shape (ES and 22 digits), not the check digits: there is no real
// charge, and a stricter rule would only stop a sign-up over a typo
export function ibanProblem(value) {
  return IBAN_PATTERN.test(compactCode(value))
    ? null
    : IBAN_MESSAGE;
}

// Required text with the spaces cleaned up, and its maximum length
export function textProblem(value, { max, message }) {
  const text = cleanText(value);
  if (!text || text.length > max) return message;
  return null;
}

// An <input type="number"> gives text: '' stays '' so a rule can say
// "required" instead of reading 0
export function toNumber(text) {
  return text === "" ? "" : Number(text);
}

export function integerProblem(value, min, max) {
  return Number.isInteger(value) && value >= min && value <= max
    ? null
    : `Escribe un número entero entre ${min} y ${max}.`;
}

export function numberProblem(value, min, max) {
  return typeof value === "number" &&
    Number.isFinite(value) &&
    value >= min &&
    value <= max
    ? null
    : `Escribe un número entre ${min} y ${max}.`;
}

// The field a 422 of the API belongs to (details = [{ field, message }])
export function apiErrorField(error) {
  return error?.details?.[0]?.field ?? null;
}
