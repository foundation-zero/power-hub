<template>
  <ValueGauge
    :value="17"
    stroke="url(#paint0_linear_893_2408)"
  >
    <text
      fill="#6D6D6D"
      xml:space="preserve"
      style="white-space: pre"
      font-family="Five Gothic"
      font-size="18"
      font-weight="bold"
      letter-spacing="0em"
    >
      <tspan
        x="100.114"
        y="174.44"
      >
        Chilling
      </tspan>
      <tspan
        x="104.658"
        y="197.44"
      >
        Power
      </tspan>
    </text>
    <text
      fill="#756B61"
      xml:space="preserve"
      style="white-space: pre"
      font-family="Five Gothic"
      font-size="25"
      letter-spacing="0em"
    >
      <tspan
        x="157.018"
        y="108.25"
      >
        kW
      </tspan>
    </text>
    <path
      d="M194.719 129.03L187.359 129.771L180 129.396V128.683L187.359 127.966L194.719 128.283V128.683V129.03Z"
      fill="#756B61"
    />
    <path
      d="M187.199 136.238L186.458 128.869L186.833 121.5H187.545L188.261 128.869L187.944 136.238H187.545H187.199Z"
      fill="#756B61"
    />
    <path
      d="M192.433 134.193L186.702 129.509L181.76 124.033L182.267 123.525L187.979 128.23L192.96 133.666L192.677 133.949L192.433 134.193Z"
      fill="#756B61"
    />
    <path
      d="M182.022 133.969L186.701 128.23L192.169 123.281L192.676 123.789L187.978 129.508L182.549 134.496L182.266 134.213L182.022 133.969Z"
      fill="#756B61"
    />
    <path
      d="M176.5 118L176.5 139"
      stroke="#6D6D6D"
      stroke-linecap="round"
    />
    <defs>
      <linearGradient
        id="paint0_linear_893_2408"
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
  </ValueGauge>
</template>

<script setup lang="ts">
import ValueGauge from "../ValueGauge.vue";
</script>
