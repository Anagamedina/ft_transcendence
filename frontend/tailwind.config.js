import daisyui from 'daisyui'

export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      colors: {
        // AquaGuard brand colors (turquoise/blue), agreed with the team
        aqua: {
          50: '#f0fafb',      // Very light background
          100: '#d4f0f7',     // Light background, borders on light surfaces
          200: '#a8e1f0',     // Light text/accents on dark backgrounds (accessible)
          400: '#06b6d4',     // Turquoise: accents, icons, borders on light backgrounds
          500: '#0891b2',     // Mid turquoise: hover and secondary accents
          600: '#0369a1',     // Primary blue: header, main buttons
          700: '#075985',     // Dark blue: body links and text on light backgrounds
          800: '#0f3a5f',     // Mid dark blue: hover on Sidebar/Footer
          900: '#0c2340',     // Dark navy: Sidebar/Footer background, titles
        },
        // Status colors (alerts and feedback)
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