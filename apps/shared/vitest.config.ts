import { fileURLToPath } from "node:url";
import { mergeConfig, defineConfig, configDefaults } from "vitest/config";
import viteConfig from "./vite.config.js";

export default defineConfig((env) =>
  mergeConfig(viteConfig(env), {
    test: {
      environment: "jsdom",
      exclude: [...configDefaults.exclude],
      root: fileURLToPath(new URL("./", import.meta.url)),
      restoreMocks: true,
    },
  }),
);
