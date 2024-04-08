<template>
  <v-app>
    <v-layout>
      <v-main>
        <suspense>
          <router-view />
        </suspense>
      </v-main>
    </v-layout>
  </v-app>
</template>

<script setup lang="ts">
import { useColorMode } from "@vueuse/core";
import vuetify from "./plugins/vuetify";
import { watch } from "vue";

const colorMode = useColorMode();

const setDarkMode = () => (vuetify.theme.global.name.value = colorMode.value);

setDarkMode();
watch(colorMode, setDarkMode);
</script>

<style lang="scss">
@font-face {
  font-family: "DMMono";
  src: url("/DMMono-Regular.ttf");
}

@font-face {
  font-family: "Five-Gothic";
  src: url("/five-gothic.woff2");
}

.font-mono {
  font-family: "DMMono" !important;
}
</style>
