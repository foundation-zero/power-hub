<template>
  <v-app>
    <router-view />
  </v-app>
</template>

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

.v-card.scrollable {
  display: flex;
  flex: 1 1 100%;
  flex-direction: column;
  max-height: 100%;
  max-width: 100%;

  .v-card-text {
    backface-visibility: hidden;
    overflow-y: auto;
  }
}
</style>
