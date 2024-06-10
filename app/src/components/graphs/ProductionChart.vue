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
import { computed } from "vue";
import { toKiloWattHours } from "@/utils/formatters";
import { oneDayAgo } from "@/utils";
import { graphic } from "echarts";
import { useObservable } from "@vueuse/rxjs";

use([SVGRenderer, BarChart, LineChart]);

const colorMode = useColorMode();

const { sum } = usePowerHubStore();

const hours = [
  0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,
];

const values = useObservable(
  sum.useOverTime("electric/power/production", () => ({
    interval: "h",
    between: [oneDayAgo().toISOString(), new Date().toISOString()].join(","),
  })),
);

const batteryValues = [
  50, 45, 42, 50, 60, 80, 90, 100, 100, 100, 100, 99, 98, 96, 92, 80, 70, 68, 66, 64, 60, 58, 56,
  53,
];

const colorsOfTheDay = [
  "#213b5d",
  "#213b5d",
  "#785883",
  "#785883",
  "#a35c87",
  "#a35c87",
  "#e5949e",
  "#e5949e",
  "#f1aa70",
  "#f1aa70",
  "#f6be4f",
  "#f6be4f",
  "#f3dc7c",
  "#f3dc7c",
  "#f3dc7c",
  "#f3dc7c",
  "#f6be4f",
  "#f6be4f",
  "#f1aa70",
  "#f1aa70",
  "#e5949e",
  "#e5949e",
  "#a35c87",
  "#a35c87",
];

const option = ref({
  backgroundColor: "#f9f8f8",
  grid: {
    left: 20,
    top: 5,
    right: 37,
    bottom: 0,
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
      name: "Production",
      type: "bar",
      barWidth: "50%",
      data: computed(() =>
        values.value
          ?.filter((_, index) => index % 2 === 0)
          .slice(0, 12)
          .map((value, index) => ({
            value: value.value + (values.value?.[index * 2 + 1]?.value ?? 0),
            itemStyle: {
              color: new graphic.LinearGradient(0, 0, 1, 0, [
                {
                  offset: 0,
                  color: colorsOfTheDay[new Date(value.time).getHours()],
                },
                {
                  offset: 1,
                  color: colorsOfTheDay[new Date(value.time).getHours()],
                },
              ]),
            },
          })),
      ),
    },
    {
      name: "Battery level",
      type: "line",
      itemStyle: {
        color: "#746c62",
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
      data: batteryValues.filter((_, index) => index % 2 === 0),
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
