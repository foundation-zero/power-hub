<template>
  <svg
    width="260"
    height="260"
    viewBox="0 0 260 260"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <text
      fill="#756B61"
      xml:space="preserve"
      style="white-space: pre"
      font-size="80"
      font-weight="bold"
      letter-spacing="0em"
    >
      <AnimatedNumber
        text-anchor="end"
        x="150"
        y="136.4"
        tag="tspan"
        :to="value"
        :format="format ?? formattedInt"
      />
    </text>
    <circle
      cx="130"
      cy="130"
      r="104"
      :stroke="stroke"
      stroke-width="8"
    />
    <circle
      cx="130"
      cy="130"
      r="129"
      stroke="#E0E0E0"
      stroke-width="2"
    />
    <slot />
  </svg>
</template>

<script setup lang="ts">
import { formattedInt } from "@/utils/numbers";
import AnimatedNumber from "vue-number-animation";
defineProps<{
  value: number;
  stroke: string;
  format?: (val: number) => string | number;
}>();
</script>

<style scoped lang="scss">
.gauge {
  position: relative;
  width: 260px;
  height: 260px;
}

.value {
  position: absolute;
  top: 56px;
  right: 40%;
  font-size: 80px;
  color: #716b63;
}
</style>
