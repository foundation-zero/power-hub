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
          {{ value }}
        </tspan>
        <tspan
          text-anchor="end"
          width="30"
          font-size="150"
          letter-spacing="0em"
        >
          &thinsp;{{ unit }}
        </tspan>
      </tspan>
    </text>
  </AnimatedSlide>
</template>

<script lang="ts">
import AnimatedSlide from "../AnimatedSlide.vue";
import { usePowerHubStore } from "@/stores/power-hub";
import { useObservable } from "@vueuse/rxjs";
import { useAsWattHours } from "@/utils";

export default {
  name: "KiloWattHoursStored",
  components: { AnimatedSlide },
  setup() {
    const { sensors } = usePowerHubStore();
    const { value, unit } = useAsWattHours(useObservable(sensors.useMean("pcm/state_of_charge")));

    return {
      value,
      unit,
    };
  },
};
</script>
