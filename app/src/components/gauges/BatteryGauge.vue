<template>
  <ValueGauge
    :value="9"
    stroke="#ca9c9e"
  >
    <text
      fill="black"
      xml:space="preserve"
      style="white-space: pre"
      font-family="Five Gothic"
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
      font-family="Five Gothic"
      font-size="18"
      font-weight="bold"
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
    <g transform="translate(15, 0)">
      <text
        fill="#756B61"
        xml:space="preserve"
        style="white-space: pre"
        font-family="Five Gothic"
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
    </g>
  </ValueGauge>
</template>

<script setup lang="ts">
import ValueGauge from "../ValueGauge.vue";
</script>
