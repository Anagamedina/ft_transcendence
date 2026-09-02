#!/usr/bin/env bash
#
# launch-frontend
# ----------------
# Lanza el entorno de desarrollo del frontend de AquaGuard (Vite + Vue 3).
# Uso temporal hasta que el Makefile esté implementado.
#
# Uso:
#   ./launch-frontend
#
# Requisitos:
#   - Node.js >=24 <25 y npm >=11 (según "engines" en package.json)
#   - nvm instalado (recomendado, para respetar la versión de Node del equipo)

set -euo pipefail

# --- Localizar la carpeta del proyecto -------------------------------------
# Este script vive en scripts/, así que la raíz del repo es un nivel arriba.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FRONTEND_DIR="$REPO_ROOT/frontend"

if [ ! -d "$FRONTEND_DIR" ]; then
  echo "❌ No se encuentra la carpeta frontend/ en $REPO_ROOT"
  echo "   Ajusta la variable FRONTEND_DIR en este script si la estructura cambió."
  exit 1
fi

cd "$FRONTEND_DIR"

# --- Cargar nvm y usar la versión de Node correcta --------------------------
if [ -s "$HOME/.nvm/nvm.sh" ]; then
  # shellcheck disable=SC1091
  source "$HOME/.nvm/nvm.sh"
  if [ -f ".nvmrc" ]; then
    nvm use > /dev/null
  fi
fi

# --- Comprobar que Node y npm existen ---------------------------------------
if ! command -v node > /dev/null 2>&1; then
  echo "❌ Node.js no está instalado o no está en el PATH."
  exit 1
fi

if ! command -v npm > /dev/null 2>&1; then
  echo "❌ npm no está instalado o no está en el PATH."
  exit 1
fi

echo "📦 Node: $(node -v)  |  npm: $(npm -v)"

# --- Instalar dependencias si falta node_modules o si package.json cambió ---
if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules" ]; then
  echo "📥 Instalando dependencias (npm install)..."
  npm install
fi

# --- Lanzar el servidor de desarrollo ----------------------------------------
echo "🚀 Lanzando frontend AquaGuard (Vite dev server, http://localhost:5173)..."
npm run dev -- --open
