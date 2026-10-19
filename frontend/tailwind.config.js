import daisyui from 'daisyui'
import { aqua, status } from './src/theme/palette.js'

export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
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
