// Styles
import "@/styles/main.scss";

// Vuetify
import { createVuetify } from "vuetify";
import { aliases, fa } from "vuetify/iconsets/fa-svg";
import "@mdi/font/css/materialdesignicons.css";
import { mdi } from "vuetify/iconsets/mdi";

export default createVuetify({
  icons: {
    defaultSet: "fa",
    aliases,
    sets: {
      fa,
      mdi,
    },
  },
  theme: {
    defaultTheme: "dark",
    themes: {
      light: {
        colors: {},
      },
    },
  },
});
// https://vuetifyjs.com/en/introduction/why-vuetify/#feature-guides
