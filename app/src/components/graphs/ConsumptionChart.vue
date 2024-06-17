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
import { isAfter, startOfToday, startOfTomorrow } from "date-fns";
import { range } from "lodash";
import { useStripes } from "@/utils/charts";
import type { HistoricalData } from "@/types";

use([SVGRenderer, BarChart, LineChart]);

const { sum } = usePowerHubStore();

const hours = range(0, 24);

const currentConsumption = useObservable(
  sum.useOverTime("electric/power/consumption", {
    interval: "h",
    between: [startOfToday().toISOString(), startOfTomorrow().toISOString()].join(","),
  }),
);

const consumptionPerHour = computed(() =>
  hours.map<HistoricalData<Date, number>>((hour) => {
    const currentValue = currentConsumption.value?.find(({ time }) => time.getHours() === hour);

    return (
      currentValue ?? {
        time: new Date(new Date().setHours(hour, 0, 0, 0)),
        value: Math.random() * 1000,
      }
    );
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
        color: "#756B61",
        borderRadius: 20,
      },
      barWidth: "40%",
      data: computed(() =>
        consumptionPerHour.value
          ?.filter((_, index) => index % 2 === 0)
          .map((value, index) => ({
            value: -Math.abs(value.value + (consumptionPerHour.value?.[index * 2 + 1]?.value ?? 0)),
            itemStyle: {
              decal: isAfter(value.time, new Date()) ? useStripes() : undefined,
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
