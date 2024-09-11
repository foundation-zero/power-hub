<template>
  <v-chart
    class="chart"
    :option="option"
    :theme="colorMode"
    autoresize
  />
</template>

<script setup lang="ts">
import { use } from "echarts/core";
import { SVGRenderer } from "echarts/renderers";
import { useColorMode } from "@vueuse/core";
import { LineChart } from "echarts/charts";
import { GridComponent, LegendComponent } from "echarts/components";
import VChart from "vue-echarts";
import { ref, toRefs } from "vue";
import type { ValueObject } from "@/types";

const props = defineProps<{
  max?: number;
  min?: number;
  data?: ValueObject[];
}>();
const { max, data, min } = toRefs(props);

use([SVGRenderer, LineChart, GridComponent, LegendComponent]);

const colorMode = useColorMode();

const option = ref({
  backgroundColor: "transparent",
  grid: {
    left: -6,
    top: 0,
    right: -6,
    bottom: 0,
    tooltip: {
      show: true,
    },
  },
  legend: {
    show: false,
  },
  xAxis: {
    type: "category",
    show: false,
  },
  yAxis: {
    type: "value",
    min,
    max,
    splitLine: {
      show: false,
    },
    nameTextStyle: {
      show: false,
    },
    axisLabel: {
      show: false,
    },
  },
  series: [
    {
      smooth: true,
      type: "line",
      showSymbol: false,
      data,
      lineStyle: {
        width: 0,
      },
      areaStyle: {
        color: "currentColor",
        opacity: 0.12,
      },
    },
  ],
});
</script>
