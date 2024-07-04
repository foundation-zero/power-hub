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
import { computed } from "vue";
import { startOfToday, startOfTomorrow } from "date-fns";
import { range } from "lodash";
import { useStripes } from "@/utils/charts";
import { useCombinedHourlyData } from "@/utils";
import { map } from "rxjs";
import { toHourlyData } from "@/api";

use([SVGRenderer, BarChart, LineChart]);

const { sum } = usePowerHubStore();

const hours = range(0, 24, 1);

const consumptionPerTwoHours = useObservable(
  useCombinedHourlyData(
    sum
      .useOverTime("electric/power/consumption", {
        interval: "h",
        between: [startOfToday().toISOString(), startOfTomorrow().toISOString()].join(","),
      })
      .pipe(map((values) => values.map(toHourlyData))),
    sum.useMeanPerHourOfDay("electric/power/consumption"),
    1,
    hours,
  ),
);

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
        consumptionPerTwoHours.value?.map(({ value, hour }) => ({
          value: -Math.abs(value),
          itemStyle: {
            decal: hour >= new Date().getHours() ? useStripes() : undefined,
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
