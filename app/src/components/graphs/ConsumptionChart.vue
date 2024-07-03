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
import type { HistoricalData } from "@/types";
import { useStartOfHour } from "@/utils";

use([SVGRenderer, BarChart, LineChart]);

const { sum } = usePowerHubStore();

const hours = range(0, 24, 2);

const currentConsumption = useObservable(
  sum.useOverTime("electric/power/consumption", {
    interval: "h",
    between: [startOfToday().toISOString(), startOfTomorrow().toISOString()].join(","),
  }),
);

const consumptionPerTwoHours = computed(() =>
  hours.map<HistoricalData<Date, number>>((hour) => {
    const [current, next] =
      currentConsumption.value?.filter(({ time }) => time.getHours() === hour) ?? [];

    if (!current)
      return {
        time: useStartOfHour(hour),
        value: Math.random() * 1000,
      };

    return {
      time: current.time,
      value: current.value + (next?.value ?? 0),
    };
  }),
);

const colorMode = useColorMode();

const option = ref({
  backgroundColor: "#f9f8f8",
  grid: {
    left: 37,
    top: 12,
    right: 37,
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
        consumptionPerTwoHours.value.map(({ value, time }) => ({
          value: -Math.abs(value),
          itemStyle: {
            decal: time.getHours() >= new Date().getHours() ? useStripes() : undefined,
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
