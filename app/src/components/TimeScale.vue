<template>
  <div>
    <span :style="{ left: `${timeOfDayPercentage}%` }">{{ currentTime }}</span>
  </div>
</template>

<script setup lang="ts">
import { useTimestamp } from "@vueuse/core";
import { format } from "date-fns";
import { computed } from "vue";

const time = useTimestamp();

const currentTime = computed(() => format(time.value, "H:mm"));

const timeOfDayPercentage = computed(() => {
  const date = new Date(time.value);
  return ((date.getMinutes() + date.getHours() * 60) / (24 * 60)) * 100;
});
</script>

<style lang="scss" scoped>
div {
  position: relative;
}

span {
  position: absolute;
  transform: translate(-50%, 0);
  will-change: transform;
  transition: transform 750ms ease;
  color: #756b61;

  &:after {
    left: 50%;
    transform: translate(-50%, 0);
    position: absolute;
    content: "";
    width: 0;
    height: 0;
    bottom: -10px;
    border-left: 10px solid transparent;
    border-right: 10px solid transparent;
    border-top: 10px solid #756b61;
  }
}
</style>
