// Styles
import "@mdi/font/css/materialdesignicons.css";
import "@/styles/main.scss";

// Vuetify
import { createVuetify } from "vuetify";

export default createVuetify({
  theme: {
    themes: {
      light: {
        colors: {
          background: "rgba(237,237,237, 1)",
        },
      },
    },
  },
});
// https://vuetifyjs.com/en/introduction/why-vuetify/#feature-guides
