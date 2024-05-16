<template>
  <div class="daily-weather bar d-flex py-3">
    <div
      class="part d-flex justify-center align-center"
      style="width: 15%"
    >
      <v-icon
        size="28"
        color="rgba(0,0,0,0.7)"
        icon="mdi-weather-night"
      />
    </div>
    <div
      class="part d-flex justify-center align-center"
      style="width: 20%"
    >
      <v-icon
        size="28"
        color="rgba(0,0,0,0.7)"
        icon="mdi-weather-sunset-up"
      />
    </div>
    <div
      class="part d-flex justify-center align-center"
      style="width: 30%"
    >
      <v-icon
        size="28"
        color="rgba(0,0,0,0.7)"
        icon="mdi-weather-sunny"
      />
    </div>
    <div
      class="part d-flex justify-center align-center"
      style="width: 20%"
    >
      <v-icon
        size="28"
        color="rgba(0,0,0,0.7)"
        icon="mdi-weather-sunset"
      />
    </div>
  </div>
</template>

<style scoped lang="scss">
.bar {
  background-color: rgb(246, 246, 246);
}

.part {
  height: 100%;
}
</style>
