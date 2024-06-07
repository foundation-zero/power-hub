<template>
  <AnimatedSlide fade>
    <text
      fill="#E6E6E6"
      xml:space="preserve"
      style="white-space: pre"
      font-family="Five-Gothic-Bold"
    >
      <tspan
        x="1177"
        y="410"
      >
        <tspan
          letter-spacing="-0.05em"
          font-size="270"
        >
          {{ heatStored }}
        </tspan>
        <tspan
          text-anchor="end"
          width="30"
          font-size="150"
          letter-spacing="0em"
        >
          kWh
        </tspan>
      </tspan>
    </text>
  </AnimatedSlide>
</template>

<script lang="ts">
import { formattedInt, useRandomNumber } from "@/utils/numbers";
import AnimatedSlide from "../AnimatedSlide.vue";

export default {
  name: "KiloWattHoursStored",
  components: { AnimatedSlide },
  data: () => ({ heatStored: useRandomNumber(10, 20) }),
  methods: { formattedInt },
};
</script>
