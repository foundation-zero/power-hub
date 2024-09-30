import { usePowerHubStore, type PowerHubStore } from "@shared/stores/power-hub";
import type { Appliance, Setpoints } from "@shared/types";
import { toSnakeCase } from "@shared/utils";
import { useDateFormat, useLocalStorage, useNow } from "@vueuse/core";
import { defineStore } from "pinia";
import { takeWhile } from "rxjs";
import { computed, ref } from "vue";

type ModFn<T> = (val: T) => Partial<T>;

export const toggleAppliance: ModFn<Appliance> = ({ on }) => ({ on: !on });
export const enableAppliance: ModFn<Appliance> = () => ({ on: true });
export const disableAppliance: ModFn<Appliance> = () => ({ on: false });
export const toggleSetpoint: ModFn<boolean> = (val) => !val;

export const useSetpointsStore = defineStore("control", () => {
  let powerHub: PowerHubStore;
  let values: Setpoints;
  const isActive = ref(false);

  const coolDown = useLocalStorage("set-control-cool-down", 0);
  const isCoolingDown = computed(() => useNow().value.getTime() < coolDown.value);
  const coolDownRemaining = useDateFormat(
    computed(() => {
      const ms = Math.max(0, coolDown.value - useNow().value.getTime());
      return new Date(0, 0, 0, 0, Math.floor(ms / 60_000), Math.floor((ms % 60_000) / 1000));
    }),
    "mm:ss",
  );

  const connect = async () => {
    powerHub ??= await usePowerHubStore().connect();

    if (!isActive.value) {
      isActive.value = true;

      powerHub.setpoints
        .useTopic()
        .pipe(takeWhile(() => isActive.value))
        .forEach((val) => {
          values = val;
        });
    }

    return { setSetpoint };
  };

  const setSetpoint = async <K extends keyof Setpoints>(control: K, modFn: ModFn<Setpoints[K]>) => {
    if (isCoolingDown.value) return;

    coolDown.value = Date.now() + Number(import.meta.env.VITE_SETPOINT_COOL_DOWN_IN_MS);

    powerHub.client.publish<Setpoints>(
      "power_hub/setpoints",
      toSnakeCase({
        ...values,
        [control]: modFn(values[control]),
      }),
      { retain: true },
    );
  };

  const deactivate = () => (isActive.value = false);

  return { connect, isCoolingDown, coolDownRemaining, deactivate };
});
