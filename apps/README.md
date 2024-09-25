# org.foundationzero.powerhub

This template should help get you started developing with Vue 3 in Vite.

## Recommended IDE Setup

[VSCode](https://code.visualstudio.com/) + [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Type Support for `.vue` Imports in TS

TypeScript cannot handle type information for `.vue` imports by default, so we replace the `tsc` CLI with `vue-tsc` for type checking. In editors, we need [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) to make the TypeScript language service aware of `.vue` types.

## Customize configuration

See [Vite Configuration Reference](https://vitejs.dev/config/).

## Project Setup

```sh
pnpm install
```

### Compile and Hot-Reload for Development

```sh
pnpm run dev:dashboard
pnpm run dev:demo
```

### Type-Check, Compile and Minify for Production

```sh
pnpm run build:dashboard
pnpm run build:demo
```

### Run Unit Tests with [Vitest](https://vitest.dev/)

```sh
pnpm run test:unit
```

### Run End-to-End Tests with [Playwright](https://playwright.dev)

```sh
# Install browsers for the first run
npx playwright install

# Runs the end-to-end tests
pnpm run test:e2e
# Runs the tests only on Chromium
pnpm run test:e2e -- --project=chromium
# Runs the tests of a specific file
pnpm run test:e2e -- tests/example.spec.ts
# Runs the tests in debug mode
pnpm run test:e2e -- --debug
```

### Lint with [ESLint](https://eslint.org/)

```sh
pnpm run lint
```

### Put this in your `.env.local` for local backend

```sh
VITE_MQTT=ws://%HOST%/mqtt
VITE_API=/api
VITE_API_TARGET=http://0.0.0.0:5001
VITE_API_BEARER_TOKEN=s4fczYTbDrf6ZFlvGHjOg5zFtJqbglZaJ5SOK7FCCdaoGhd6LVA87hHJjBoz2lC4
```
