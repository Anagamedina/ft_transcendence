// AquaGuard palette, taken from the redesign mockup (#247).
// Single source of truth: tailwind.config.js builds its classes from here,
// and charts/maps import it directly (Chart.js and MapLibre need plain hex
// values, they cannot use Tailwind classes).

// Brand colors (turquoise/blue)
export const aqua = {
  50: '#f0fafb',  // Very light background (public sections, panels)
  75: '#e6f4f8',  // Footer background on light pages
  100: '#d4f0f7', // Light background, borders on light surfaces
  200: '#a8e1f0', // Light text/accents on dark backgrounds (accessible)
  300: '#a5f3fc', // Light turquoise: water drop highlight
  400: '#06b6d4', // Turquoise: accents, icons, borders on light backgrounds
  500: '#0891b2', // Mid turquoise: hover and secondary accents
  600: '#0369a1', // Primary blue: header, main buttons
  700: '#075985', // Dark blue: body links and text on light backgrounds
  800: '#0f3a5f', // Mid dark blue: hover on Sidebar/Footer
  900: '#0c2340', // Dark navy: Sidebar/Footer background, titles
};

// Status colors (alerts and feedback).
// DEFAULT keeps existing classes working (text-success, border-danger...).
// light + dark are used together in status pills: light background with
// dark text reaches WCAG AA contrast.
export const status = {
  success: { DEFAULT: '#10b981', light: '#d1fae5', dark: '#065f46' },
  warning: { DEFAULT: '#f59e0b', light: '#fef3c7', dark: '#92400e' },
  danger: { DEFAULT: '#ef4444', light: '#fee2e2', dark: '#991b1b' },
  info: { DEFAULT: '#3b82f6', light: '#dbeafe', dark: '#1e40af' },
};

// Chart and map colors (JavaScript only, not exposed as Tailwind classes).
export const chartColors = {
  surface: '#ffffff',  // Card background, gap between pie slices
  ink: '#64748b',      // Axis labels and legend text (slate-500)
  grid: '#e2e8f0',     // Grid lines (slate-200)
  mapMask: '#f1f5f9',  // Area outside Barcelona on the map (slate-100)
  rangeBand: '#ecfdf5', // Allowed pressure range band (green-50)
  // Exception: series colors of the analytics charts. Kept outside the
  // status scale on purpose: tested for contrast between series and
  // against the white surface.
  seriesTotal: '#2a78d6',
  seriesCritical: '#e34948',
  seriesWarning: '#eda100',
};
