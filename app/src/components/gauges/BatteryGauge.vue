<template>
  <svg
    width="498"
    height="260"
    viewBox="0 0 498 260"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <text
      fill="black"
      xml:space="preserve"
      style="white-space: pre"
      font-size="14"
      letter-spacing="0em"
    >
      <tspan
        x="121.352"
        y="66.62"
      >
        Net
      </tspan>
    </text>
    <text
      fill="#5A5A5A"
      xml:space="preserve"
      style="white-space: pre"
      font-size="18"
      font-weight="600"
      letter-spacing="0em"
    >
      <tspan
        x="93.1797"
        y="170.44"
      >
        Charging
      </tspan>
      <tspan
        x="101.512"
        y="193.44"
      >
        battery
      </tspan>
    </text>
    <circle
      cx="130"
      cy="130"
      r="104"
      stroke="#D4999D"
      stroke-width="8"
    />
    <circle
      cx="130"
      cy="130"
      r="129"
      stroke="#E0E0E0"
      stroke-width="2"
    />
    <text
      fill="#756B61"
      xml:space="preserve"
      style="white-space: pre"
      font-size="80"
      font-weight="bold"
      letter-spacing="0em"
    >
      <tspan
        text-anchor="end"
        x="138"
        y="137.4"
      >
        <AnimatedNumber
          :to="netValue"
          :format="formattedInt"
          tag="tspan"
        />
      </tspan>
    </text>
    <text
      fill="#756B61"
      xml:space="preserve"
      style="white-space: pre"
      font-size="25"
      letter-spacing="0em"
    >
      <tspan
        x="139"
        y="106.25"
      >
        kW
      </tspan>
    </text>
    <rect
      x="144.167"
      y="115.708"
      width="12.6667"
      height="19.9583"
      rx="1.5"
      stroke="#756B61"
    />
    <rect
      x="146.125"
      y="117.667"
      width="8.75"
      height="16.0417"
      rx="0.8"
      fill="#756B61"
    />
    <path
      fill-rule="evenodd"
      clip-rule="evenodd"
      d="M146.418 110.668C146.125 110.961 146.125 111.432 146.125 112.375V113.292H154.875V112.375C154.875 111.432 154.875 110.961 154.582 110.668C154.289 110.375 153.818 110.375 152.875 110.375H148.125C147.182 110.375 146.711 110.375 146.418 110.668Z"
      fill="#756B61"
    />
    <rect
      x="149"
      y="124"
      width="3"
      height="6"
      fill="#F6F6F6"
    />
    <path
      d="M150.5 120L153 124L148 124L150.5 120Z"
      fill="#F6F6F6"
    />
    <text
      fill="#756B61"
      xml:space="preserve"
      style="white-space: pre"
      font-size="20"
      font-weight="600"
      letter-spacing="0em"
    >
      <tspan
        x="362.295"
        y="71.6"
      >
        <AnimatedNumber
          :to="charging"
          :format="formattedInt"
          tag="tspan"
        />
        <tspan
          font-size="16"
          width="30"
          text-anchor="end"
        >
          kW
        </tspan>
      </tspan>
    </text>
    <text
      fill="#5A5A5A"
      xml:space="preserve"
      style="white-space: pre"
      font-size="14"
      font-weight="600"
      letter-spacing="0em"
    >
      <tspan
        x="364"
        y="87.62"
      >
        Charging
      </tspan>
    </text>
    <rect
      x="343.167"
      y="62.708"
      width="12.6667"
      height="19.9583"
      rx="1.5"
      stroke="#756B61"
    />
    <rect
      x="345.125"
      y="64.667"
      width="8.75"
      height="16.0417"
      rx="0.8"
      fill="#756B61"
    />
    <path
      fill-rule="evenodd"
      clip-rule="evenodd"
      d="M345.418 57.6679C345.125 57.9608 345.125 58.4322 345.125 59.375V60.2917H353.875V59.375C353.875 58.4322 353.875 57.9608 353.582 57.6679C353.289 57.375 352.818 57.375 351.875 57.375H347.125C346.182 57.375 345.711 57.375 345.418 57.6679Z"
      fill="#756B61"
    />
    <rect
      x="348"
      y="71"
      width="3"
      height="6"
      fill="#F6F6F6"
    />
    <path
      d="M349.5 67L352 71L347 71L349.5 67Z"
      fill="#F6F6F6"
    />
    <text
      fill="#756B61"
      xml:space="preserve"
      style="white-space: pre"
      font-size="20"
      font-weight="600"
      letter-spacing="0em"
    >
      <tspan
        x="363.309"
        y="124.6"
      >
        <AnimatedNumber
          :to="discharging"
          :format="formattedInt"
          tag="tspan"
        />
        <tspan
          font-size="16"
          width="30"
          text-anchor="end"
        >
          kW
        </tspan>
      </tspan>
    </text>
    <text
      fill="#5A5A5A"
      xml:space="preserve"
      style="white-space: pre"
      font-size="14"
      font-weight="600"
      letter-spacing="0em"
    >
      <tspan
        x="363.467"
        y="140.62"
      >
        Discharging
      </tspan>
    </text>
    <rect
      x="343.167"
      y="115.708"
      width="12.6667"
      height="19.9583"
      rx="1.5"
      stroke="#756B61"
    />
    <rect
      x="345.125"
      y="117.667"
      width="8.75"
      height="16.0417"
      rx="0.8"
      fill="#756B61"
    />
    <path
      fill-rule="evenodd"
      clip-rule="evenodd"
      d="M345.418 110.668C345.125 110.961 345.125 111.432 345.125 112.375V113.292H353.875V112.375C353.875 111.432 353.875 110.961 353.582 110.668C353.289 110.375 352.818 110.375 351.875 110.375H347.125C346.182 110.375 345.711 110.375 345.418 110.668Z"
      fill="#756B61"
    />
    <rect
      x="351"
      y="128"
      width="3"
      height="6"
      transform="rotate(-180 351 128)"
      fill="#F6F6F6"
    />
    <path
      d="M349.5 132L347 128L352 128L349.5 132Z"
      fill="#F6F6F6"
    />
    <path
      d="M293 1L292 254"
      stroke="#9A9A9A"
      stroke-dasharray="5 5"
    />
    <text
      fill="#756B61"
      xml:space="preserve"
      style="white-space: pre"
      font-size="20"
      font-weight="600"
      letter-spacing="0em"
    >
      <tspan
        x="365.42"
        y="179.1"
      >
        <AnimatedNumber
          tag="tspan"
          :to="internalTemperature"
          :format="formattedInt"
        />
        <tspan
          width="30"
          text-anchor="end"
        >
          &#8451;
        </tspan>
      </tspan>
    </text>
    <g clip-path="url(#clip0_910_2529)">
      <path
        d="M353.315 176.674C353.315 179.743 353.323 182.814 353.306 185.883C353.303 186.361 353.426 186.695 353.792 187.036C356.599 189.651 356.741 193.971 354.141 196.77C351.538 199.571 347.181 199.754 344.319 197.186C341.461 194.615 341.205 190.332 343.771 187.469C344.132 187.067 344.271 186.684 344.271 186.158C344.257 180.018 344.257 173.882 344.265 167.742C344.268 165.427 345.599 163.65 347.672 163.138C350.573 162.423 353.278 164.51 353.306 167.534C353.338 170.58 353.312 173.626 353.315 176.672V176.674ZM351.864 177.015H351.861C351.861 173.828 351.881 170.642 351.853 167.455C351.836 165.408 349.903 164.007 347.93 164.561C346.582 164.941 345.727 166.113 345.724 167.641C345.719 174.014 345.716 180.387 345.73 186.76C345.73 187.317 345.571 187.719 345.16 188.113C342.835 190.338 342.883 193.853 345.239 196.058C347.524 198.198 351.052 198.033 353.159 195.69C355.245 193.367 354.958 189.783 352.489 187.809C352.006 187.424 351.85 187.016 351.853 186.431C351.873 183.292 351.861 180.151 351.861 177.012L351.864 177.015Z"
        fill="#646464"
      />
      <path
        d="M350.425 183.817C350.425 185.409 350.453 185.803 350.411 187.395C350.397 187.935 350.573 188.25 351.024 188.523C352.054 189.148 352.753 190.031 353 191.229C353.4 193.153 352.395 195.054 350.57 195.808C348.733 196.564 346.65 195.9 345.548 194.202C344.492 192.579 344.685 190.405 346.196 189.159C347.01 188.487 347.2 187.789 347.183 186.822C347.135 183.778 347.163 186.733 347.166 183.689C347.166 181.8 347.183 182.166 348.268 182.156C350.593 182.133 350.439 181.669 350.428 183.885C350.422 185.196 350.428 182.109 350.428 183.42L350.425 183.817Z"
        fill="#646464"
      />
      <path
        d="M348.739 181.205C348.432 181.205 348.086 181.295 347.833 181.179C347.563 181.055 347.243 180.757 347.214 180.501C347.189 180.293 347.535 179.869 347.756 179.838C348.426 179.748 349.125 179.739 349.792 179.835C350.03 179.869 350.376 180.299 350.368 180.541C350.359 180.769 349.99 181.075 349.715 181.182C349.431 181.295 349.068 181.207 348.739 181.207C348.739 181.207 348.739 181.207 348.739 181.205Z"
        fill="#646464"
      />
    </g>
    <text
      fill="#5A5A5A"
      xml:space="preserve"
      style="white-space: pre"
      font-size="14"
      font-weight="600"
      letter-spacing="0em"
    >
      <tspan
        x="365"
        y="196.62"
      >
        Internal battery
      </tspan>
    </text>
    <defs>
      <clipPath id="clip0_910_2529">
        <rect
          width="14"
          height="36"
          fill="white"
          transform="translate(342 163)"
        />
      </clipPath>
    </defs>
  </svg>
</template>

<script setup lang="ts">
import { formattedInt, useRandomNumber } from "@/utils/numbers";
import { computed } from "vue";
import AnimatedNumber from "vue-number-animation";

defineProps<{ outline?: boolean }>();

const charging = useRandomNumber(4, 12);
const discharging = useRandomNumber(10, 20);
const netValue = computed(() => Math.abs(charging.value - discharging.value));
const internalTemperature = useRandomNumber(30, 60);
</script>
