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
        // Status colors (alerts and feedback).
        // DEFAULT keeps existing classes working (text-success, border-danger...).
        // light + dark are used together in status pills: light background with
        // dark text reaches WCAG AA contrast.
        success: { DEFAULT: '#10b981', light: '#d1fae5', dark: '#065f46' },
        warning: { DEFAULT: '#f59e0b', light: '#fef3c7', dark: '#92400e' },
        danger: { DEFAULT: '#ef4444', light: '#fee2e2', dark: '#991b1b' },
        info: { DEFAULT: '#3b82f6', light: '#dbeafe', dark: '#1e40af' },
      }
    }
  },
  plugins: [daisyui],
  daisyui: {
    themes: ['light'],
  },
}