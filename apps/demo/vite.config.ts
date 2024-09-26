import { fileURLToPath, URL } from "node:url";

import { defineConfig, loadEnv } from "vite";
import { VitePWA } from "vite-plugin-pwa";
import vue from "@vitejs/plugin-vue";
import VueDevTools from "vite-plugin-vue-devtools";

// https://github.com/vuetifyjs/vuetify-loader/tree/next/packages/vite-plugin
import vuetify from "vite-plugin-vuetify";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd());

  return {
    plugins: [
      vue(),
      VueDevTools(),
      vuetify({ autoImport: true }),
      VitePWA({
        registerType: "autoUpdate",
        workbox: {
          globPatterns: ["**/*.{js,css,html,ico,png,svg,json,vue,txt,woff2,ttf}"],
        },
        manifest: {
          name: "Foundation⁰ Power Hub",
          short_name: "Power Hub",
          display: "standalone",
          icons: [
            {
              src: "./img/icons/android-chrome-192x192.png",
              sizes: "192x192",
              type: "image/png",
              purpose: "any",
            },
            {
              src: "./img/icons/android-chrome-512x512.png",
              sizes: "512x512",
              type: "image/png",
              purpose: "any",
            },
            {
              src: "./img/icons/android-chrome-192x192.png",
              sizes: "192x192",
              type: "image/png",
              purpose: "maskable",
            },
            {
              src: "./img/icons/android-chrome-512x512.png",
              sizes: "512x512",
              type: "image/png",
              purpose: "maskable",
            },
          ],
          start_url: ".",
          background_color: "#fff",
          theme_color: "#fff",
        },
      }),
    ],
    resolve: {
      alias: {
        "@demo": fileURLToPath(new URL("./src", import.meta.url)),
        "@shared": fileURLToPath(new URL("../shared/src", import.meta.url)),
      },
    },
    server: {
      proxy: {
        "/mqtt": {
          target: "ws://127.0.0.1:9001",
          ws: true,
        },
        "/api": {
          target: env.VITE_API_TARGET,
          rewrite: (path) => path.replace(/^\/api/, ""),
        },
      },
    },
  };
});
