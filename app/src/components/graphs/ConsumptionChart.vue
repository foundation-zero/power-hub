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
import { oneDayAgo } from "@/utils";
import { computed } from "vue";

use([SVGRenderer, BarChart, LineChart]);

const { sum } = usePowerHubStore();

const consumption = useObservable(
  sum.useOverTime("electric/power/consumption", {
    interval: "h",
    between: [oneDayAgo().toISOString(), new Date().toISOString()].join(","),
  }),
);

const colorMode = useColorMode();

const hours = [
  0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,
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
      data: computed(() =>
        consumption.value
          ?.filter((_, index) => index % 2 === 0)
          .map((val, index) => val.value + (consumption.value?.[index * 2 + 1]?.value ?? 0))
          .map((val) => -Math.abs(val)),
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
