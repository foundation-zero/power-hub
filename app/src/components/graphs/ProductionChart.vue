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
import { between, todayRangeFn } from "@/utils/numbers";
import { add, startOfTomorrow, startOfYesterday } from "date-fns";

use([SVGRenderer, BarChart, LineChart]);

const colorMode = useColorMode();

const { sum, sensors } = usePowerHubStore();

const hours = range(0, 24, 1);

const productionPerTwoHours = useObservable(
  useCombinedHourlyData(
    sum
      .useOverTime("electric/power/production", todayRangeFn)
      .pipe(map((values) => values.map(toHourlyData))),
    sum.useMeanPerHourOfDay("electric/power/production"),
    1,
    hours,
  ),
);

const batteryValues = useObservable(
  sensors
    .useOverTime("electrical/battery_system_soc", () => ({
      interval: "h",
      between: between(add(startOfYesterday(), { seconds: -1 }), startOfTomorrow()),
    }))
    .pipe(
      map((values) => values.map(toHourlyData)),
      map((values) => {
        const yesterday = values.slice(0, 24);
        const today = values.slice(24);

        // Use the current value as starting point and add delta to yesterdays values
        const delta = today[today.length - 1].value - yesterday[today.length - 1].value;
        const forecastToday = yesterday
          .slice(today.length)
          .map(({ value, hour }) => ({ hour, value: Math.min(100, Math.max(0, value + delta)) }));

        return today.concat(forecastToday);
      }),
    ),
);

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
            decal: hour > new Date().getHours() ? useStripes() : undefined,
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
        color: new graphic.LinearGradient(0, 0, 1, 0, [
          {
            offset: 0,
            color: "#746c62",
          },
          {
            offset: (new Date().getHours() + 1) / 24,
            color: "#746c62",
          },
          {
            offset: (new Date().getHours() + 1) / 24,
            color: "rgba(116, 108, 98, 0.5)",
          },
        ]),
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
