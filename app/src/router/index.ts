import { createRouter, createWebHistory } from "vue-router";
import ReadingsView from "../views/ReadingsView.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "home",
      component: ReadingsView,
    },
  ],
});

export default router;
