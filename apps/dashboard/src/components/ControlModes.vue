<script setup lang="ts">
import type { PowerHubStore } from "@shared/stores/power-hub";
import { useObservable } from "@vueuse/rxjs";
import { replaceAll } from "@shared/utils";
import { snakeCase } from "lodash";
import type { ControlModes } from "@shared/types";
import { computed, ref } from "vue";

const { powerHub } = defineProps<{ powerHub: PowerHubStore }>();
const controlModes = useObservable(powerHub.controlModes.useTopic());

const toPrettyString = (input: string | number) => {
  if (typeof input === "string") return replaceAll(snakeCase(input), "_", " ");
  return new Date(input).toLocaleString();
};

const showDiagram = computed({
  get() {
    return !!diagram.value;
  },
  set(val: boolean) {
    if (!val) {
      diagram.value = undefined;
    }
  },
});

const diagram = ref<string>();

type ControlRow = {
  key: keyof ControlModes;
  name: string;
  diagram: string;
};

const rows: ControlRow[] = [
  {
    key: "hotControl",
    name: "Hot control",
    diagram: "hot.svg",
  },
  {
    key: "chillControl",
    name: "Chill control",
    diagram: "chill.svg",
  },
  {
    key: "wasteControl",
    name: "Waste control",
    diagram: "waste.svg",
  },
  {
    key: "freshWaterControl",
    name: "Fresh water control",
    diagram: "fresh_water.svg",
  },
  {
    key: "technicalWaterControl",
    name: "Technical water control",
    diagram: "technical_water.svg",
  },
  {
    key: "waterTreatmentControl",
    name: "Water treatment control",
    diagram: "water_treatment.svg",
  },
  {
    key: "coolingSupplyControl",
    name: "Cooling supply control",
    diagram: "cooling_supply.svg",
  },
];
</script>

<template>
  <v-dialog v-model="showDiagram">
    <v-img
      width="100%"
      height="100%"
      :src="`/control-graphs/${diagram}`"
    />
  </v-dialog>
  <v-card class="pa-8">
    <h3 class="text-h4 font-weight-thin mb-8 d-flex align-center">
      <v-icon
        size="24"
        icon="fa-gear"
        class="mr-5"
      />
      Control modes
    </h3>

    <v-table v-if="controlModes">
      <tbody class="text-capitalize">
        <tr
          v-for="row in rows"
          :key="row.key"
        >
          <th>{{ row.name }}</th>
          <td>{{ toPrettyString(controlModes[row.key]) }}</td>
          <td>
            <v-btn
              icon="fa-diagram-project"
              size="small"
              @click="diagram = row.diagram"
            ></v-btn>
          </td>
        </tr>
      </tbody>
    </v-table>
  </v-card>
</template>
