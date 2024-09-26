import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "HMI Dashboard",
      component: async () => await import("@dashboard/views/HMIDashboard.vue"),
    },
  ],
});

export default router;
