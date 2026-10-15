module.exports = {
  root: true,
  env: {
    browser: true,
    node: true,
    es2022: true,
  },
  extends: [
    'eslint:recommended',
    'plugin:vue/essential',
  ],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
  },
  rules: {
    // Vue 3 supports fragments; Sidebar needs fixed controls beside its aside.
    'vue/no-multiple-template-root': 'off',
    // Kept for backwards-compatible imports. New components use descriptive
    // multi-word names, while these five are application primitives.
    'vue/multi-word-component-names': ['error', {
      ignores: ['Footer', 'Header', 'Modal', 'Sidebar', 'Tabs'],
    }],
  },
}
