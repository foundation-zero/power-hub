<template>
  <ComponentBase
    component="power-battery"
    journey="electrical"
    width="120"
    height="114"
    viewBox="-1 -1 120 114"
  >
    <rect
      width="112"
      height="112"
      rx="56"
      class="fill"
      fill="#FFEFB9"
      stroke="white"
      stroke-width="1"
    />
    <circle
      cx="56"
      cy="56"
      r="46"
      class="fill"
      fill="#FFF0BA"
    />
    <rect
      x="49.1667"
      y="25.708"
      width="12.6667"
      height="19.9583"
      rx="1.5"
      stroke="#756B61"
    />
    <rect
      x="51.125"
      y="27.667"
      width="8.75"
      height="16.0417"
      rx="0.8"
      fill="#756B61"
    />
    <path
      fill-rule="evenodd"
      clip-rule="evenodd"
      d="M51.4179 20.6679C51.125 20.9608 51.125 21.4322 51.125 22.375V23.2917H59.875V22.375C59.875 21.4322 59.875 20.9608 59.5821 20.6679C59.2892 20.375 58.8178 20.375 57.875 20.375H53.125C52.1822 20.375 51.7108 20.375 51.4179 20.6679Z"
      fill="#756B61"
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
        x="35.771"
        y="64.739"
      >
        Battery
      </tspan>
    </text>
    <text
      fill="#756B61"
      xml:space="preserve"
      style="white-space: pre"
      font-family="DMMono"
      font-size="10"
      letter-spacing="0em"
    >
      <AnimatedNumber
        text-anchor="end"
        x="56"
        y="79.91"
        :from="0"
        :format="formattedInt"
        :to="value"
        tag="tspan"
      />
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
        y="79.91"
      >
        {{ unit }}
      </tspan>
    </text>
  </ComponentBase>
</template>

<script setup lang="ts">
import ComponentBase from "./ComponentBase.vue";

import AnimatedNumber from "vue-number-animation";
import { type PowerHubStore } from "@/stores/power-hub";

import { useAsWattHours } from "@/utils";
import { useObservable } from "@vueuse/rxjs";
import { between, formattedInt } from "@/utils/numbers";
import { map } from "rxjs";
import { add } from "date-fns";

const { powerHub } = defineProps<{ powerHub: PowerHubStore }>();

const BATTERY_CAPACITY = 218000;

const { value, unit } = useAsWattHours(
  useObservable(
    powerHub.sensors
      .useLastValues("electrical/soc_battery_system", () => ({
        between: between(add(new Date(), { seconds: -100 }), new Date()),
      }))
      .pipe(map((val) => (val.slice(-1)[0].value * BATTERY_CAPACITY) / 100)),
  ),
);
</script>
