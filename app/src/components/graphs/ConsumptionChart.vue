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
import { BarChart, LineChart } from "echarts/charts";
import VChart from "vue-echarts";
import { ref } from "vue";
import { computed } from "vue";
import { useStripes } from "@/utils/charts";
import type { HourlyData } from "@/types";

use([SVGRenderer, BarChart, LineChart]);

const props = defineProps<{
  max?: number;
  data?: HourlyData[];
}>();

const colorMode = useColorMode();

const option = ref({
  backgroundColor: "#f9f8f8",
  grid: {
    left: 27,
    top: 6,
    right: 27,
    bottom: 10,
  },
  legend: {
    show: false,
  },
  xAxis: {
    type: "category",
    show: false,
  },
  yAxis: [
    {
      type: "value",
      name: "",
      min: computed(() => -(props.max ?? 0)),
      max: 0,
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
  ],
  series: [
    {
      name: "Consumption",
      type: "bar",
      itemStyle: {
        color: "#756B61",
        borderRadius: 20,
      },
      barWidth: "40%",
      data: computed(() =>
        props.data?.map(({ value, hour }) => ({
          value: -Math.abs(value),
          itemStyle: {
            decal: hour > new Date().getHours() ? useStripes() : undefined,
          },
        })),
      ),
    },
  ],
});
</script>

<style scoped lang="scss">
.chart {
  height: 150px;

  text {
    font-family: "Roboto" !important;
  }
}
</style>
