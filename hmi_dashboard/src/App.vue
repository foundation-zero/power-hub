<template>
  <v-app>
    <Suspense>
      <router-view />
      <template #fallback>
        <h1>Connecting to MQTT broker...</h1>
      </template>
    </Suspense>
  </v-app>
</template>

<style lang="scss">
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

.font-mono {
  font-family: monospace !important;
}

.text-overflow-ellipsis {
  text-overflow: ellipsis;
}
</style>
