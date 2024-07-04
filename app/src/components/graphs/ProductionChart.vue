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
import { graphic } from "echarts";
import { useObservable } from "@vueuse/rxjs";
import { range } from "lodash";
import { useStripes } from "@/utils/charts";
import { map } from "rxjs";
import { toHourlyData } from "@/api";
import { useCombinedHourlyData } from "@/utils";
import { startOfToday, startOfTomorrow } from "date-fns";

use([SVGRenderer, BarChart, LineChart]);

const colorMode = useColorMode();

const { sum } = usePowerHubStore();

const hours = range(0, 24, 1);

const productionPerTwoHours = useObservable(
  useCombinedHourlyData(
    sum
      .useOverTime("electric/power/production", () => ({
        interval: "h",
        between: [startOfToday().toISOString(), startOfTomorrow().toISOString()].join(","),
      }))
      .pipe(map((values) => values.map(toHourlyData))),
    sum.useMeanPerHourOfDay("electric/power/production"),
    1,
    hours,
  ),
);

const batteryValues = hours.map(() => 50 + Math.random() * 50);

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
    left: 27,
    top: 5,
    right: 27,
    bottom: 0,
  },
  legend: {
    show: false,
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
      barWidth: "50%",
      data: computed(() =>
        productionPerTwoHours.value?.map(({ value, hour }) => ({
          value,
          itemStyle: {
            decal: hour >= new Date().getHours() ? useStripes() : undefined,
            color: new graphic.LinearGradient(0, 0, 1, 0, [
              {
                offset: 0,
                color: colorsOfTheDay[hour],
              },
              {
                offset: 1,
                color: colorsOfTheDay[hour],
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
      data: batteryValues,
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
