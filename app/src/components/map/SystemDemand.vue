<template>
  <ComponentBase
    component="system-demand"
    x="941"
    y="368"
    width="114"
    height="114"
    viewBox="-1 -1 114 114"
  >
    <rect
      width="112"
      height="112"
      rx="56"
      fill="white"
      stroke="#E6E6E6"
      stroke-width="1"
    />
    <text
      opacity="0.9"
      fill="#767272"
      xml:space="preserve"
      style="white-space: pre"
      font-size="12"
      font-family="Five-Gothic-Bold"
      letter-spacing="0em"
    >
      <tspan
        x="35.998"
        y="60.96"
      >
        Electric
      </tspan>
    </text>
    <text
      opacity="0.9"
      fill="#767272"
      xml:space="preserve"
      style="white-space: pre"
      font-size="12"
      font-family="Five-Gothic-Bold"
      letter-spacing="0em"
    >
      <tspan
        x="33.543"
        y="72.96"
      >
        demand
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
        tag="tspan"
        text-anchor="end"
        x="58"
        y="85.8"
        :to="value"
        :format="formattedInt"
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
        x="60"
        y="85.8"
      >
        {{ unit }}
      </tspan>
    </text>

    <circle
      cx="57"
      cy="56"
      r="44"
      class="fill"
      stroke="#FFEFB9"
      stroke-width="4"
    />
    <path
      d="M55.3765 48.9962C55.5892 47.9056 55.8059 46.8169 56.0107 45.7244C56.0724 45.3964 56.0982 45.0627 56.14 44.7329C56.2136 44.1418 56.146 44.0484 55.5296 44.0598C54.1218 44.0846 52.8891 43.6404 51.8492 42.75C50.7238 41.789 50.0617 40.5687 50.0279 39.1197C49.9782 36.9137 50.016 34.7076 50.0001 32.5016C49.9961 32.0803 50.177 31.9449 50.5946 31.9544C51.3382 31.9735 52.0838 31.9487 52.8294 31.964C53.237 31.9716 53.3902 31.8076 53.3862 31.4244C53.3742 30.3452 53.3802 29.266 53.3842 28.1869C53.3842 28.0286 53.3742 27.8646 53.414 27.714C53.5253 27.285 53.8077 27.0181 54.2849 27.0009C54.7402 26.9837 55.0424 27.2106 55.1737 27.6206C55.2353 27.8131 55.2512 28.0267 55.2532 28.2307C55.2611 29.2946 55.2651 30.3585 55.2532 31.4206C55.2492 31.7924 55.3665 31.9754 55.792 31.9697C56.9333 31.9525 58.0766 31.9563 59.2199 31.9659C59.6056 31.9697 59.7508 31.8114 59.7488 31.4511C59.7388 30.3871 59.7468 29.3232 59.7488 28.2612C59.7488 28.103 59.7408 27.9409 59.7647 27.7865C59.8343 27.3422 60.1047 27.06 60.5719 27.0085C61.0432 26.9571 61.3931 27.1744 61.5244 27.6034C61.6099 27.8856 61.6118 28.1964 61.6158 28.4957C61.6257 29.4472 61.6158 30.4005 61.6218 31.3538C61.6238 31.9315 61.6615 31.964 62.2799 31.964C63.0076 31.964 63.7373 31.9754 64.4651 31.9601C64.8428 31.9525 65.0039 32.0803 64.9999 32.4559C64.9741 34.7248 65.0119 36.9956 64.9284 39.2627C64.8329 41.8405 62.4449 44.0007 59.7508 44.0579C58.7506 44.0789 58.7745 44.0827 58.6135 45.0246C58.3868 46.3536 58.1164 47.6749 57.8658 49H55.3804L55.3765 48.9962ZM55.4481 41.8824C55.5097 41.911 55.5713 41.9377 55.631 41.9663C55.9074 41.6612 56.1877 41.36 56.4561 41.0511C57.5358 39.8118 58.6154 38.5686 59.6872 37.3236C59.7746 37.2225 59.8045 37.0776 59.8621 36.9518C59.713 36.9022 59.5678 36.8183 59.4167 36.8107C58.9216 36.7859 58.4246 36.7783 57.9295 36.784C57.5477 36.7878 57.4165 36.6753 57.5676 36.2997C57.8559 35.5733 58.1144 34.8373 58.3768 34.1032C58.4405 33.9221 58.4703 33.7295 58.516 33.5427C58.4763 33.5198 58.4385 33.495 58.3987 33.4721C58.2675 33.5713 58.1144 33.6514 58.005 33.7715C56.8041 35.1004 55.6071 36.4332 54.4141 37.7698C54.3366 37.8575 54.3107 37.9871 54.261 38.0977C54.3923 38.1473 54.5215 38.2331 54.6547 38.2369C55.1836 38.254 55.7125 38.2521 56.2414 38.2426C56.653 38.235 56.7743 38.3475 56.5993 38.7498C56.2314 39.5982 55.9034 40.462 55.5693 41.3238C55.5017 41.5011 55.4838 41.6956 55.4441 41.8824H55.4481Z"
      fill="#756B61"
    />
  </ComponentBase>
</template>

<script setup lang="ts">
import AnimatedNumber from "vue-number-animation";
import { formattedInt } from "@/utils/numbers";
import { useObservable } from "@vueuse/rxjs";
import ComponentBase from "./ComponentBase.vue";
import { type PowerHubStore } from "@/stores/power-hub";
import { useAsWatts } from "@/utils";
import { watch } from "vue";

const { powerHub } = defineProps<{ powerHub: PowerHubStore }>();

const { value, unit } = useAsWatts(
  useObservable(powerHub.sum.useMean("electric/power/consumption")),
);

watch(value, (val) => console.log("system demand:", val));
</script>
