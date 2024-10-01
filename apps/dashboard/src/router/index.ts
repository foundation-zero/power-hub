import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "HMI Dashboard",
      component: async () => await import("@dashboard/views/HMIDashboard.vue"),
    },
    {
      path: "/setpoints",
      name: "HMI Setpoints",
      component: async () => await import("@dashboard/views/HMISetpoints.vue"),
      beforeEnter: () => {
        return !!import.meta.env.VITE_ENABLE_SETPOINTS;
      },
    },
  ],
});

export default router;
