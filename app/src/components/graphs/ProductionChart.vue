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
import { toKiloWattHours } from "@/utils/formatters";
import { graphic } from "echarts";
import _ from "lodash";

use([SVGRenderer, BarChart, LineChart]);

const colorMode = useColorMode();

const hours = _.range(0, 23);
const values = [
  1, 1, 1, 1, 1, 2, 5, 10, 20, 30, 30, 35, 36, 35, 30, 30, 28, 25, 20, 10, 5, 3, 1, 1, 1,
];
const colorsOfTheDay = [
  "#4d607b",
  "#4d607b",
  "#4d607b",
  "#4d607b",
  "#4d607b",
  "#6e6c8c",
  "#8f7799",
  "#b17b9d",
  "#e4a7af",
  "#eeb98a",
  "#f2c96d",
  "#f2e093",
  "#f2e093",
  "#f2e093",
  "#f2e093",
  "#f2e093",
  "#f2e093",
  "#f2c96d",
  "#f2c96d",
  "#eeb98a",
  "#e4a7af",
  "#b17b9d",
  "#8f7799",
  "#6e6c8c",
  "#4d607b",
];

const option = ref({
  backgroundColor: "rgb(246,246,246)",
  grid: {
    left: 10,
    top: 10,
    right: 10,
    bottom: 0,
  },
  legend: {
    show: false,
    textStyle: {
      fontSize: 16,
      color: "#333",
    },
  },
  xAxis: {
    type: "category",
    show: false,
    data: hours,
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
      name: "Production",
      type: "bar",
      barWidth: "80%",
      itemStyle: {
        color: new graphic.LinearGradient(
          0,
          0,
          1,
          0,
          colorsOfTheDay.map((color, index) => ({ color, offset: index * (1 / 24) })),
        ),
      },
      data: computed(() =>
        values.slice(0, 24).map((value, index) => ({
          value,
          itemStyle: {
            color: new graphic.LinearGradient(0, 0, 1, 0, [
              {
                offset: 0,
                color: colorsOfTheDay[index],
              },
              {
                offset: 1,
                color: colorsOfTheDay[index + 1],
              },
            ]),
          },
        })),
      ),
    },
    {
      name: "Consumption",
      type: "bar",
      itemStyle: {
        color: "#8d8780",
        borderRadius: 20,
      },
      barWidth: "60%",
      barGap: "-90%",
      data: [
        -12, -10, -10, -10, -15, -35, -36, -37, -36, -35, -32, -26, -24, -28, -30, -32, -28, -25,
        -26, -24, -22, -20, -15, -30,
      ],
    },
    {
      name: "Battery level",
      type: "line",
      itemStyle: {
        color: "#333",
      },
      showSymbol: false,
      lineStyle: {
        width: 3,
        join: "round",
        type: "dotted",
      },
      yAxisIndex: 1,
      tooltip: {
        valueFormatter: toKiloWattHours,
      },
      data: [
        50, 45, 42, 50, 60, 80, 90, 100, 100, 100, 100, 99, 98, 96, 92, 80, 70, 68, 66, 64, 60, 58,
        56, 53,
      ],
    },
  ],
});
</script>

<style scoped lang="scss">
.chart {
  height: 300px;

  text {
    font-family: "Roboto" !important;
  }
}
</style>
