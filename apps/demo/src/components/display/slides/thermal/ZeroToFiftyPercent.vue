<template>
  <AnimatedSlide fade>
    <text
      fill="#E6E6E6"
      xml:space="preserve"
      style="white-space: pre"
      font-size="270"
      font-family="Five-Gothic-Bold"
      letter-spacing="0em"
    >
      <tspan
        x="1176"
        y="413.6"
      >
        <AnimatedNumber
          tag="tspan"
          :from="0"
          :to="50"
          :format="formattedInt"
        ></AnimatedNumber
        >%
      </tspan>
    </text>
  </AnimatedSlide>
</template>

<script lang="ts">
import AnimatedNumber from "vue-number-animation";
import AnimatedSlide from "../AnimatedSlide.vue";
import { formattedInt } from "@shared/utils/numbers";

export default {
  name: "ZeroPercent",
  components: { AnimatedSlide, AnimatedNumber },
  methods: { formattedInt },
};
</script>
