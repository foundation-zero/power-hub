<template>
  <svg
    width="260"
    height="260"
    viewBox="0 0 260 260"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <circle
      id="inner-ring"
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
    <defs>
      <linearGradient
        id="paint0_linear_106_2182"
        x1="238"
        y1="130"
        x2="22"
        y2="130"
        gradientUnits="userSpaceOnUse"
      >
        <stop stop-color="#A9E8EC" />
        <stop
          offset="1"
          stop-color="#ECD2D4"
        />
      </linearGradient>
    </defs>
  </svg>
</template>

<script setup lang="ts">
defineProps<{ stroke: string }>();
</script>

<style scoped lang="scss">
#inner-ring {
  will-change: stroke;
  transition: stroke 750ms ease;
}
</style>
