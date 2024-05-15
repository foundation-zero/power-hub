<template>
  <v-app>
    <v-layout>
      <v-main>
        <router-view />
      </v-main>
    </v-layout>
  </v-app>
</template>

<script setup lang="ts">
/* Uncomment to enable auto darkmode
import { useColorMode } from "@vueuse/core";
import vuetify from "./plugins/vuetify";
import { watch } from "vue";

const colorMode = useColorMode();

const setDarkMode = () => (vuetify.theme.global.name.value = colorMode.value);

setDarkMode();
watch(colorMode, setDarkMode);
*/
</script>

<style lang="scss">
@font-face {
  font-family: "DMMono";
  src: url("/DMMono-Regular.ttf");
}

@font-face {
  font-family: "Five-Gothic";
  src: url("/five-gothic.ttf");
}

@font-face {
  font-family: "Five-Gothic-Bold";
  src: url("/five-gothic-bold.ttf");
}

@font-face {
  font-family: "Five-Gothic-DemiBold";
  src: url("/five-gothic-demibold.ttf");
}

.font-mono {
  font-family: "DMMono" !important;
}

.font-weight-bold {
  font-family: "Five-Gothic-Bold" !important;
}

.font-weight-medium {
  font-family: "Five-Gothic-DemiBold" !important;
}
</style>
