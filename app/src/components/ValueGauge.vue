<template>
  <div class="gauge">
    <GaugeRings :stroke="stroke">
      <template #default>
        <component :is="content" />
      </template>
    </GaugeRings>
    <div class="value font-weight-bold">{{ value }}</div>
  </div>
</template>

<script setup lang="ts">
import GaugeRings from "./graphics/GaugeRings.vue";
import HeatPipesPower from "./graphics/HeatPipesPower.vue";
import ChillingPower from "./graphics/ChillingPower.vue";
import { computed } from "vue";
import type { PowerHubComponent } from "@/types/power-hub";

const props = defineProps<{
  component: PowerHubComponent;
  value: number;
}>();

const stroke = computed(() => {
  console.log("stroke?", props.component);
  switch (props.component) {
    case "absorption-chiller":
      return "url(#paint0_linear_106_2182)";
    case "heat-tubes":
      return "#F4DA98";
    case "heat-storage":
      return "#ca9c9e";
    case "cooling-demand":
      return "#bbe6ea";
    default:
      return "#E0E0E0";
  }
});

const content = computed(() => {
  switch (props.component) {
    case "absorption-chiller":
      return ChillingPower;
    case "heat-tubes":
      return HeatPipesPower;
    default:
      return null;
  }
});
</script>

<style scoped lang="scss">
.gauge {
  position: relative;
  width: 260px;
  height: 260px;
}

.value {
  position: absolute;
  top: 56px;
  right: 40%;
  font-size: 80px;
  color: #716b63;
}
</style>
