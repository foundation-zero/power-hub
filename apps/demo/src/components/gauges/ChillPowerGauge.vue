<template>
  <svg
    width="496"
    height="260"
    viewBox="0 0 496 260"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <text
      fill="#756B61"
      xml:space="preserve"
      style="white-space: pre"
      font-size="80"
      font-family="Five-Gothic-Bold"
      letter-spacing="0em"
    >
      <tspan
        x="154"
        y="142.4"
        text-anchor="end"
      >
        <AnimatedNumber
          :to="chillingPower"
          tag="tspan"
        />
      </tspan>
    </text>
    <text
      fill="#6D6D6D"
      xml:space="preserve"
      style="white-space: pre"
      font-size="18"
      font-family="Five-Gothic-Bold"
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
    <circle
      cx="130"
      cy="130"
      r="104"
      stroke="url(#paint0_linear_910_2582)"
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
      font-size="25"
      letter-spacing="0em"
    >
      <tspan
        x="157.018"
        y="108.25"
      >
        {{ chillingPowerUnit }}
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
    <text
      fill="#756B61"
      xml:space="preserve"
      style="white-space: pre"
      font-size="20"
      font-family="Five-Gothic-Bold"
      letter-spacing="0em"
    >
      <tspan
        x="375.727"
        y="96.6"
      >
        <AnimatedNumber
          :to="heatPower"
          tag="tspan"
        />
        <tspan
          font-size="16"
          text-anchor="end"
          width="30"
        >
          {{ heatPowerUnit }}
        </tspan>
      </tspan>
    </text>
    <text
      fill="#5A5A5A"
      xml:space="preserve"
      style="white-space: pre"
      font-size="14"
      font-family="Five-Gothic-Bold"
      letter-spacing="0em"
    >
      <tspan
        x="341"
        y="117.62"
      >
        Heat power
      </tspan>
    </text>
    <path
      d="M346.262 97.5C346.158 97.5 346.05 97.4709 345.95 97.4127C345.633 97.2186 345.515 96.7772 345.689 96.4231C346.666 94.4196 346.936 92.809 346.493 91.635C346.349 91.2518 346.167 91.0093 345.958 90.723C345.698 90.3689 345.403 89.9663 345.225 89.3259C344.534 86.881 345.568 85.0667 346.545 83.7618C346.775 83.4513 347.187 83.4125 347.461 83.6696C347.735 83.9267 347.774 84.3875 347.543 84.6932C346.692 85.8332 345.971 87.1284 346.467 88.8845C346.571 89.258 346.744 89.4957 346.966 89.7965C347.205 90.1215 347.474 90.4902 347.691 91.0626C348.299 92.6635 348.008 94.7009 346.831 97.1119C346.714 97.3545 346.488 97.4903 346.258 97.4903L346.262 97.5Z"
      fill="#756B61"
    />
    <path
      d="M342.262 97.5C342.158 97.5 342.05 97.4709 341.95 97.4127C341.633 97.2186 341.515 96.7772 341.689 96.4231C342.666 94.4196 342.936 92.809 342.493 91.635C342.349 91.2518 342.167 91.0093 341.958 90.723C341.698 90.3689 341.403 89.9663 341.225 89.3259C340.534 86.881 341.568 85.0667 342.545 83.7618C342.775 83.4513 343.187 83.4125 343.461 83.6696C343.735 83.9267 343.774 84.3875 343.543 84.6932C342.692 85.8332 341.971 87.1284 342.467 88.8845C342.571 89.258 342.744 89.4957 342.966 89.7965C343.205 90.1215 343.474 90.4902 343.691 91.0626C344.299 92.6635 344.008 94.7009 342.831 97.1119C342.714 97.3545 342.488 97.4903 342.258 97.4903L342.262 97.5Z"
      fill="#756B61"
    />
    <path
      d="M350.262 97.5C350.158 97.5 350.05 97.4709 349.95 97.4127C349.633 97.2186 349.515 96.7772 349.689 96.4231C350.666 94.4196 350.94 92.809 350.493 91.635C350.349 91.2518 350.167 91.0093 349.958 90.723C349.698 90.3689 349.403 89.9663 349.225 89.3259C348.534 86.881 349.568 85.0667 350.545 83.7618C350.775 83.4513 351.187 83.4125 351.461 83.6696C351.735 83.9267 351.774 84.3875 351.543 84.6932C350.692 85.8332 349.971 87.1284 350.467 88.8845C350.571 89.258 350.744 89.4957 350.966 89.7965C351.205 90.1215 351.474 90.4902 351.691 91.0626C352.299 92.6635 352.008 94.7009 350.831 97.1119C350.714 97.3545 350.488 97.4903 350.258 97.4903L350.262 97.5Z"
      fill="#756B61"
    />
    <path
      d="M358.5 80L358.5 101"
      stroke="#6D6D6D"
      stroke-linecap="round"
    />
    <path
      d="M301 1L300 254"
      stroke="#9A9A9A"
      stroke-dasharray="5 5"
    />
    <text
      fill="#5A5A5A"
      xml:space="preserve"
      style="white-space: pre"
      font-size="14"
      font-family="Five-Gothic-Bold"
      letter-spacing="0em"
    >
      <tspan
        x="363"
        y="174.62"
      >
        Output temp
      </tspan>
    </text>

    <text
      fill="#756B61"
      xml:space="preserve"
      style="white-space: pre"
      font-size="20"
      font-family="Five-Gothic-Bold"
      letter-spacing="0em"
    >
      <tspan
        x="363"
        y="157.1"
      >
        <AnimatedNumber
          :to="outputTemperature"
          tag="tspan"
        />
        <tspan
          width="30"
          text-anchor="end"
        >
          &#8451;
        </tspan>
      </tspan>
    </text>
    <g clip-path="url(#clip0_910_2582)">
      <path
        d="M350.315 154.674C350.315 157.743 350.323 160.814 350.306 163.883C350.303 164.361 350.426 164.695 350.792 165.036C353.599 167.651 353.741 171.971 351.141 174.77C348.538 177.571 344.181 177.754 341.319 175.186C338.461 172.615 338.205 168.332 340.771 165.469C341.132 165.067 341.271 164.684 341.271 164.158C341.257 158.018 341.257 151.882 341.265 145.742C341.268 143.427 342.599 141.65 344.672 141.138C347.573 140.423 350.278 142.51 350.306 145.534C350.338 148.58 350.312 151.626 350.315 154.672V154.674ZM348.864 155.015H348.861C348.861 151.828 348.881 148.642 348.853 145.455C348.836 143.408 346.903 142.007 344.93 142.561C343.582 142.941 342.727 144.113 342.724 145.641C342.719 152.014 342.716 158.387 342.73 164.76C342.73 165.317 342.571 165.719 342.16 166.113C339.835 168.338 339.883 171.853 342.239 174.058C344.524 176.198 348.052 176.033 350.159 173.69C352.245 171.367 351.958 167.783 349.489 165.809C349.006 165.424 348.85 165.016 348.853 164.431C348.873 161.292 348.861 158.151 348.861 155.012L348.864 155.015Z"
        fill="#646464"
      />
      <path
        d="M347.425 161.817C347.425 163.409 347.453 163.803 347.411 165.395C347.397 165.935 347.573 166.25 348.024 166.523C349.054 167.148 349.753 168.031 350 169.229C350.4 171.153 349.395 173.054 347.57 173.808C345.733 174.564 343.65 173.9 342.548 172.202C341.492 170.579 341.685 168.405 343.196 167.159C344.01 166.487 344.2 165.789 344.183 164.822C344.135 161.778 344.163 164.733 344.166 161.689C344.166 159.8 344.183 160.166 345.268 160.156C347.593 160.133 347.439 159.669 347.428 161.885C347.422 163.196 347.428 160.109 347.428 161.42L347.425 161.817Z"
        fill="#646464"
      />
      <path
        d="M345.739 159.205C345.432 159.205 345.086 159.295 344.833 159.179C344.563 159.055 344.243 158.757 344.214 158.501C344.189 158.293 344.535 157.869 344.756 157.838C345.426 157.748 346.125 157.739 346.792 157.835C347.03 157.869 347.376 158.299 347.368 158.541C347.359 158.769 346.99 159.075 346.715 159.182C346.431 159.295 346.068 159.207 345.739 159.207C345.739 159.207 345.739 159.207 345.739 159.205Z"
        fill="#646464"
      />
    </g>
    <defs>
      <linearGradient
        id="paint0_linear_910_2582"
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
      <clipPath id="clip0_910_2582">
        <rect
          width="14"
          height="36"
          fill="white"
          transform="translate(339 141)"
        />
      </clipPath>
    </defs>
  </svg>
</template>

<script setup lang="ts">
import { usePowerHubStore } from "@shared/stores/power-hub";
import { useAsWatts } from "@shared/utils";
import { clampAtZero } from "@shared/utils/numbers";
import { useObservable } from "@vueuse/rxjs";
import AnimatedNumber from "@demo/components/AnimatedInt.vue";
import { map } from "rxjs";

const { sensors } = usePowerHubStore();

const { value: chillingPower, unit: chillingPowerUnit } = useAsWatts(
  useObservable(sensors.useMean("yazaki/chillPower").pipe(map(clampAtZero))),
  100,
);
const { value: heatPower, unit: heatPowerUnit } = useAsWatts(
  useObservable(sensors.useMean("yazaki/usedPower")),
);
const outputTemperature = useObservable(sensors.useMean("yazaki/chilledOutputTemperature"));
</script>
