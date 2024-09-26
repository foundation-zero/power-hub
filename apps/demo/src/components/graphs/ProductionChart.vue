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
import { usePowerHubStore } from "@shared/stores/power-hub";
import { SVGRenderer } from "echarts/renderers";
import { useColorMode } from "@vueuse/core";
import { BarChart, LineChart } from "echarts/charts";
import VChart from "vue-echarts";
import { ref } from "vue";
import { computed } from "vue";
import { toKiloWattHours } from "@shared/utils/formatters";
import { graphic } from "echarts";
import { useObservable } from "@vueuse/rxjs";
import { useStripes } from "@demo/utils/charts";
import { map } from "rxjs";
import { toHourlyData } from "@shared/api";
import { between } from "@shared/utils/numbers";
import { add, startOfTomorrow, startOfYesterday } from "date-fns";
import type { HourlyData } from "@shared/types";

const props = defineProps<{ max?: number; data?: HourlyData[] }>();

use([SVGRenderer, BarChart, LineChart]);

const colorMode = useColorMode();

const { sensors } = usePowerHubStore();

const batteryValues = useObservable(
  sensors
    .useOverTime("electrical/batterySystemSoc", () => ({
      interval: "h",
      between: between(add(startOfYesterday(), { seconds: -1 }), startOfTomorrow()),
    }))
    .pipe(
      map((values) => values.map(toHourlyData)),
      map((values) => {
        const yesterday = values.slice(0, 24);
        const today = values.slice(24);

        if (!today.length) return yesterday;

        // Use the current value as starting point and add delta to yesterdays values
        const delta = today[today.length - 1].value - yesterday[today.length - 1].value;
        const forecastToday = yesterday
          .slice(today.length)
          .map(({ value, hour }) => ({ hour, value: Math.min(1, Math.max(0, value + delta)) }));

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
      max: computed(() => props.max),
    },
    {
      type: "value",
      name: "%",
      min: 0,
      max: 1,
      splitLine: {
        show: false,
      },
      interval: 0.25,
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
        props.data?.map(({ value, hour }) => ({
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
