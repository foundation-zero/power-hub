import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "responsive",
      component: async () => await import("../views/ResponsiveView.vue"),
    },
    {
      path: "/display",
      name: "display",
      component: async () => await import("../views/DisplayView.vue"),
    },
  ],
});

export default router;
