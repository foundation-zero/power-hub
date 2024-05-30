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
import { usePowerHubStore } from "@/stores/power-hub";
import { SVGRenderer } from "echarts/renderers";
import { useColorMode } from "@vueuse/core";
import { BarChart, LineChart } from "echarts/charts";
import VChart from "vue-echarts";
import { ref } from "vue";
import { useObservable } from "@vueuse/rxjs";
import { watch } from "vue";

use([SVGRenderer, BarChart, LineChart]);

const { sum } = usePowerHubStore();

const consumption = useObservable(sum.useOverTime("electric/power/consumption"));

watch(consumption, (val) => console.log("consumption", val));

const colorMode = useColorMode();

const hours = [
  0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,
];

const values = [
  -12, -10, -10, -10, -15, -35, -36, -37, -36, -35, -32, -26, -24, -28, -30, -32, -28, -25, -26,
  -24, -22, -20, -15, -30,
];

const option = ref({
  backgroundColor: "#f9f8f8",
  grid: {
    left: 37,
    top: 12,
    right: 20,
    bottom: 10,
  },
  legend: {
    show: false,
  },
  xAxis: {
    type: "category",
    show: false,
    data: hours.filter((hour) => hour % 2 === 0),
  },
  yAxis: [
    {
      type: "value",
      name: "",
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
    {
      type: "value",
      name: "%",
      min: 0,
      max: 100,
      splitLine: {
        show: false,
      },
      interval: 25,
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
        color: "#8d8780",
        borderRadius: 20,
      },
      barWidth: "40%",
      data: values
        .filter((_, index) => index % 2 === 0)
        .map((val, index) => val + values[index * 2 + 1]),
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
