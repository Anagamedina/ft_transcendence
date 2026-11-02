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
    // Vue 2 rule: in Vue 3 the key of a <template v-for> goes on the template itself.
    'vue/no-v-for-template-key': 'off',
    // Kept for backwards-compatible imports. New components use descriptive
    // multi-word names, while these five are application primitives.
    'vue/multi-word-component-names': ['error', {
      ignores: ['Footer', 'Header', 'Modal', 'Sidebar', 'Tabs'],
    }],
  },
}
