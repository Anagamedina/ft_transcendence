import daisyui from 'daisyui'

export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      colors: {
        // Colores brand AquaGuard (turquesa/azul) - acordados con el equipo
        aqua: {
          50: '#f0fafb',      // Fondo muy claro (backgrounds claros)
          100: '#d4f0f7',     // Fondo claro (secondary backgrounds)
          200: '#a8e1f0',     // Texto/acentos claros sobre fondos oscuros (accesible)
          400: '#06b6d4',     // Turquesa (accents, iconos, bordes sobre fondo claro)
          600: '#0369a1',     // Azul primary (Header, botones principales)
          800: '#0f3a5f',     // Azul oscuro intermedio (hover sobre Sidebar/Footer)
          900: '#0c2340',     // Azul marino oscuro (fondo Sidebar/Footer)
        },
        // Colores de estado (para alertas y feedback)
        success: '#10b981',
        warning: '#f59e0b',
        danger: '#ef4444',
        info: '#3b82f6',
      }
    }
  },
  plugins: [daisyui],
  daisyui: {
    themes: ['light'],
  },
}