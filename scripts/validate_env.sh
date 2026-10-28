#!/bin/sh

set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
ENV_FILE="$ROOT/.env"

fail() {
  echo "config-check: FAIL  $1" >&2
  exit 1
}

[ -f "$ENV_FILE" ] || fail "missing .env. Run: make env"

# shellcheck disable=SC1090
. "$ENV_FILE"

required() {
  eval "value=\${$1-}"
  [ -n "$value" ] || fail "missing required variable: $1"
}

positive_integer() {
  eval "value=\${$1-}"
  case "$value" in
    '' | *[!0-9]*) fail "$1 must be a positive whole number" ;;
  esac
  [ "$value" -gt 0 ] || fail "$1 must be greater than zero"
}

positive_number() {
  eval "value=\${$1-}"
  case "$value" in
    '' | *[!0-9.]*) fail "$1 must be a positive number" ;;
  esac
  awk "BEGIN { exit !($value > 0) }" || fail "$1 must be greater than zero"
}

for variable in POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB SECRET_KEY INGEST_API_KEY \
  ENV COOKIE_SECURE CORS_ORIGINS PUBLIC_BASE_URL DOCUMENTS_DIR; do
  required "$variable"
done

# These were added after the first .env versions. Keep older local files
# usable in development; production is still rejected below unless the key
# and organization scope are explicitly configured.
PUBLIC_API_KEY="${PUBLIC_API_KEY:-dev-only-public-api-key}"
PUBLIC_API_WRITE_KEY="${PUBLIC_API_WRITE_KEY-}"
PUBLIC_API_RATE_LIMIT="${PUBLIC_API_RATE_LIMIT:-60r/m}"

case "$ENV" in
  development|test|production) ;;
  *) fail "ENV must be development, test, or production" ;;
esac

case "$COOKIE_SECURE" in
  true|false) ;;
  *) fail "COOKIE_SECURE must be true or false" ;;
esac

for variable in POSTGRES_PORT MAX_UPLOAD_MB INVITATION_TTL_DAYS TRIAL_DAYS \
  BACKUP_INTERVAL_HOURS BACKUP_KEEP SIMULATOR_MAX_RETRIES; do
  positive_integer "$variable"
done

for variable in SIMULATOR_INTERVAL_SECONDS SIMULATOR_REQUEST_TIMEOUT_SECONDS; do
  positive_number "$variable"
done

case "${PUBLIC_API_RATE_LIMIT-}" in
  *r/*) ;;
  *) fail "PUBLIC_API_RATE_LIMIT must use Nginx format such as 60r/m" ;;
esac

# Emails (B19): all optional. An empty or missing SMTP_HOST just disables them.
[ -z "${SMTP_PORT-}" ] || positive_integer SMTP_PORT

case "${SMTP_STARTTLS-}" in
  '' | true | false) ;;
  *) fail "SMTP_STARTTLS must be true or false" ;;
esac

case "${SMTP_FROM-}" in
  '' | *@*) ;;
  *) fail "SMTP_FROM must be an email address, such as no-reply@aquaguard.dev" ;;
esac

if [ -n "${SMTP_USER-}" ] && [ -z "${SMTP_PASSWORD-}" ]; then
  fail "SMTP_USER is set but SMTP_PASSWORD is empty"
fi

if [ "$ENV" = "production" ]; then
  [ "$SECRET_KEY" != "dev-only-change-me" ] || fail "SECRET_KEY uses the development placeholder"
  [ "$INGEST_API_KEY" != "dev-only-ingest-key" ] || fail "INGEST_API_KEY uses the development placeholder"
  [ "$PUBLIC_API_KEY" != "dev-only-public-api-key" ] || fail "PUBLIC_API_KEY uses the development placeholder"
  [ "$PUBLIC_API_WRITE_KEY" != "dev-only-public-api-write-key" ] || fail "PUBLIC_API_WRITE_KEY uses the development placeholder (set your own or leave it empty)"
  [ -n "${PUBLIC_API_ORGANIZATION_ID-}" ] || fail "PUBLIC_API_ORGANIZATION_ID is required in production"
  [ "$COOKIE_SECURE" = "true" ] || fail "COOKIE_SECURE must be true in production"
fi

case "$PUBLIC_BASE_URL" in
  https://*) ;;
  *) fail "PUBLIC_BASE_URL must use https" ;;
esac

[ -f "$ROOT/frontend/.env.example" ] || fail "missing frontend/.env.example"

echo "config-check: OK    required variables and safe defaults are valid"
