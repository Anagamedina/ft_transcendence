export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      colors: {
        // Colores brand AquaGuard (turquesa/azul)
        aqua: {
          50: '#f0fafb',      // Fondo muy claro (backgrounds claros)
          100: '#d4f0f7',     // Fondo claro (secondary backgrounds)
          200: '#a8e1f0',     // Color intermedio (borders, hovers)
          400: '#64c8dc',     // Color logo y accents (muy visible)
          600: '#30a0c8',     // Color primary buttons y elementos clave
          900: '#1f4f6b',     // Color oscuro para forms y backgrounds oscuros
        },
        // Colores de estado (para alertas y feedback)
        success: '#10b981',   // Alertas resueltas, estados OK, checkmarks
        warning: '#f59e0b',   // Alertas warning, precaución, atención
        danger: '#ef4444',    // Alertas críticas, errores, peligro
        info: '#3b82f6',      // Información general, tips
      }
    }
  },
  plugins: [require('daisyui')],
  daisyui: {
    themes: ['light'],
  },
}