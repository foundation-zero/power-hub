<template>
  <ComponentBase
    component="heat-storage"
    x="549"
    y="508"
    width="128"
    height="128"
    viewBox="-8 -8 128 128"
  >
    <rect
      width="112"
      height="112"
      rx="56"
      fill="#ECD2D4"
      class="fill"
      stroke="white"
      stroke-width="1"
    />

    <circle
      cx="56"
      cy="56"
      r="62"
      stroke="#D4999D"
      stroke-width="4"
      class="outline"
    />

    <circle
      cx="56"
      cy="56"
      r="62"
      stroke="white"
      stroke-dasharray="5"
      stroke-width="4"
      class="flow"
    />

    <circle
      cx="56"
      cy="56"
      r="46"
      fill="#ECD2D4"
      class="fill"
    />
    <text
      fill="#756B61"
      xml:space="preserve"
      style="white-space: pre"
      font-size="12"
      font-family="Five-Gothic-Bold"
      letter-spacing="0em"
    >
      <tspan
        x="22.4121"
        y="66.961"
      >
        Heat battery
      </tspan>
    </text>
    <rect
      x="49.1667"
      y="28.708"
      width="12.6667"
      height="19.9583"
      rx="1.5"
      stroke="#756B61"
    />
    <rect
      x="51.125"
      y="30.667"
      width="8.75"
      height="16.0417"
      rx="0.8"
      fill="#756B61"
    />
    <path
      fill-rule="evenodd"
      clip-rule="evenodd"
      d="M51.4179 23.6679C51.125 23.9608 51.125 24.4322 51.125 25.375V26.2917H59.875V25.375C59.875 24.4322 59.875 23.9608 59.5821 23.6679C59.2892 23.375 58.8178 23.375 57.875 23.375H53.125C52.1822 23.375 51.7108 23.375 51.4179 23.6679Z"
      fill="#756B61"
    />
    <path
      d="M53.8416 42C53.7721 42 53.6997 41.9834 53.6332 41.9501C53.4218 41.8392 53.3437 41.587 53.4595 41.3846C54.1108 40.2398 54.2903 39.3194 53.995 38.6486C53.8995 38.4296 53.7779 38.291 53.6389 38.1275C53.4652 37.9251 53.2684 37.695 53.1497 37.3291C52.6894 35.932 53.3784 34.8953 54.0298 34.1496C54.1832 33.9722 54.4582 33.95 54.6406 34.0969C54.823 34.2438 54.8491 34.5072 54.6956 34.6818C54.1282 35.3332 53.6476 36.0734 53.9777 37.0769C54.0472 37.2903 54.163 37.4261 54.3106 37.598C54.4698 37.7837 54.6493 37.9944 54.7941 38.3215C55.1994 39.2363 55.0054 40.4005 54.2209 41.7782C54.1427 41.9168 53.9921 41.9945 53.8387 41.9945L53.8416 42Z"
      fill="#ECD2D4"
    />
    <path
      d="M56.8416 42C56.7721 42 56.6997 41.9834 56.6332 41.9501C56.4218 41.8392 56.3437 41.587 56.4595 41.3846C57.1108 40.2398 57.2932 39.3194 56.995 38.6486C56.8995 38.4296 56.7779 38.291 56.6389 38.1275C56.4652 37.9251 56.2684 37.695 56.1497 37.3291C55.6894 35.932 56.3784 34.8953 57.0298 34.1496C57.1832 33.9722 57.4582 33.95 57.6406 34.0969C57.823 34.2438 57.8491 34.5072 57.6956 34.6818C57.1282 35.3332 56.6476 36.0734 56.9777 37.0769C57.0472 37.2903 57.163 37.4261 57.3106 37.598C57.4698 37.7837 57.6493 37.9944 57.7941 38.3215C58.1994 39.2363 58.0054 40.4005 57.2209 41.7782C57.1427 41.9168 56.9921 41.9945 56.8387 41.9945L56.8416 42Z"
      fill="#ECD2D4"
    />
    <text
      fill="#756B61"
      xml:space="preserve"
      style="white-space: pre"
      font-family="DMMono"
      font-size="10"
      letter-spacing="0em"
    >
      <tspan
        text-anchor="end"
        x="56"
        y="82.91"
        >20</tspan
      >
    </text>
    <text
      fill="#756B61"
      xml:space="preserve"
      style="white-space: pre"
      font-size="9"
      letter-spacing="0em"
    >
      <tspan
        x="58"
        y="82.91"
      >
        kWh
      </tspan>
    </text>
  </ComponentBase>
</template>

<script setup lang="ts">
import ComponentBase from "./ComponentBase.vue";
</script>

<style scoped lang="scss">
@keyframes stream {
  from {
    stroke-dashoffset: 100;
  }

  to {
    stroke-dashoffset: 0;
  }
}

.flow {
  animation: stream 2500ms linear infinite;
}

.flow,
.outline {
  will-change: opacity;
  transition: opacity 750ms ease;
}

.component:not(.flowing) .flow,
.component:not(.custom) .outline {
  opacity: 0;
}
</style>
