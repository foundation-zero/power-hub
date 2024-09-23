/* eslint-env node */
require("@rushstack/eslint-patch/modern-module-resolution");

module.exports = {
  root: true,
  extends: [
    "eslint:recommended",
    "plugin:vue/vue3-recommended",
    "plugin:prettier/recommended",
    "@vue/eslint-config-typescript",
  ],
  plugins: ["prettier"],
  overrides: [
    {
      files: ["e2e/**/*.{test,spec}.{js,ts,jsx,tsx}"],
      extends: ["plugin:playwright/recommended"],
    },
  ],
  rules: {
    "@typescript-eslint/no-unused-vars": [
      "warn",
      {
        argsIgnorePattern: "^_",
        varsIgnorePattern: "^_",
        caughtErrorsIgnorePattern: "^_",
      },
    ],
  },
  parserOptions: {
    ecmaVersion: "latest",
  },
};
