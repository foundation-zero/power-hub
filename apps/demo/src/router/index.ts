import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/display",
      name: "display",
      component: async () => await import("../views/DisplayView.vue"),
    },
    {
      path: "/journeys/:journey(heat|water|electrical)",
      name: "journey",
      component: async () => await import("../views/MapView.vue"),
    },
    {
      path: "/journeys",
      name: "journeys",
      component: async () => await import("../views/MapView.vue"),
    },
    {
      path: "/",
      name: "intro",
      component: async () => await import("../views/MapView.vue"),
    },
  ],
});

export default router;
