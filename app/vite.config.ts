import { fileURLToPath, URL } from "node:url";

import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import VueDevTools from "vite-plugin-vue-devtools";

// https://github.com/vuetifyjs/vuetify-loader/tree/next/packages/vite-plugin
import vuetify from "vite-plugin-vuetify";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue(), VueDevTools(), vuetify({ autoImport: true })],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    proxy: {
      "/mqtt": {
        target: "ws://127.0.0.1:9001",
        ws: true,
      },
      "/api": {
        target: "http://0.0.0.0:5001",
        rewrite: (path) => path.replace(/^\/api/, ""),
        headers: {
          Authorization: "Bearer s4fczYTbDrf6ZFlvGHjOg5zFtJqbglZaJ5SOK7FCCdaoGhd6LVA87hHJjBoz2lC4",
        },
      },
    },
  },
});
