import daisyui from 'daisyui'
import { aqua, status } from './src/theme/palette.js'

export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      // F29: one font for the whole app (loaded in main.js). The system
      // fonts are only a fallback while it loads.
      fontFamily: {
        sans: [
          '"Inter Variable"',
          'system-ui',
          '-apple-system',
          '"Segoe UI"',
          'Roboto',
          'sans-serif',
        ],
      },
      // Palette from the redesign mockup, defined in src/theme/palette.js
      colors: {
        aqua,
        ...status,
      }
    }
  },
  plugins: [daisyui],
  daisyui: {
    themes: ['light'],
  },
}
