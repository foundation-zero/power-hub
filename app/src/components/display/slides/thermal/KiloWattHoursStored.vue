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
        <AnimatedNumber
          letter-spacing="-0.05em"
          tag="tspan"
          font-size="270"
          :from="0"
          :to="value"
          :format="formattedInt"
        />
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
import AnimatedNumber from "vue-number-animation";
import { formattedInt, jouleToWattHour } from "@/utils/numbers";
import { map } from "rxjs";

export default {
  name: "KiloWattHoursStored",
  components: { AnimatedSlide, AnimatedNumber },
  setup() {
    const { sensors } = usePowerHubStore();
    const { value, unit } = useAsWattHours(
      useObservable(sensors.useCurrent("pcm/fill").pipe(map(jouleToWattHour))),
    );

    return {
      value,
      unit,
    };
  },
  methods: { formattedInt },
};
</script>
