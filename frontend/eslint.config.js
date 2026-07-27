import js from '@eslint/js'
import globals from 'globals'
import react from 'eslint-plugin-react'
import reactHooks from 'eslint-plugin-react-hooks'

// Flat config, required by eslint 9. Replaces .eslintrc.js — note that
// package.json sets "type": "module", so this must be genuine ESM rather
// than a renamed CommonJS file.
export default [
  {
    ignores: ['dist/**', 'coverage/**', 'reports/**', '.stryker-tmp/**'],
  },
  js.configs.recommended,
  {
    files: ['src/**/*.{js,jsx}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: globals.browser,
      parserOptions: {
        ecmaFeatures: { jsx: true },
      },
    },
    plugins: {
      react,
      'react-hooks': reactHooks,
    },
    settings: {
      react: { version: 'detect' },
    },
    rules: {
      ...react.configs.flat.recommended.rules,
      ...reactHooks.configs.recommended.rules,
      // The new JSX transform means React need not be in scope.
      'react/react-in-jsx-scope': 'off',
      // Deliberately off. React 19 ignores propTypes entirely (they were
      // removed from the library), so satisfying this rule would mean adding
      // ~64 declarations across five components that are dead on arrival and
      // would have to be deleted again at the React 19 upgrade. This is a
      // small internal dashboard with no external consumers of these
      // components; prop shapes are pinned by the component tests instead.
      'react/prop-types': 'off',
    },
  },
  {
    // Test files run under vitest globals (globals: true in vite.config.js).
    files: ['src/**/*.test.{js,jsx}', 'src/setupTests.js'],
    languageOptions: {
      globals: { ...globals.browser, ...globals.node, vi: 'readonly' },
    },
  },
]
