import { fileURLToPath } from "node:url";
import { mergeConfig, defineConfig, configDefaults } from "vitest/config";
import viteConfig from "./vite.config.mjs";

export default defineConfig((env) =>
  mergeConfig(viteConfig(env), {
    test: {
      environment: "jsdom",
      exclude: [...configDefaults.exclude, "tests/e2e/*"],
      root: fileURLToPath(new URL("./", import.meta.url)),
      deps: {
        optimizer: {
          web: {
            enabled: true,
            include: ["vue-echarts"],
          },
        },
      },
      server: {
        deps: {
          inline: ["vuetify"],
        },
      },
      restoreMocks: true,
    },
  }),
);
