import { usePowerHubStore, type PowerHubStore } from "@/stores/power-hub";
import type { HistoricalData, HourlyData, NestedPath, PathValue, Unit } from "@/types";
import { add, setHours, startOfHour } from "date-fns";
import { camelCase, merge, range } from "lodash";
import { combineLatest, map, type Observable } from "rxjs";
import { computed, watch, type Ref } from "vue";
import { between } from "./numbers";

export const camelize = <T extends Object>(obj: T): T => {
  const copy = {} as Partial<T>;

  Object.entries(obj).forEach(([key, val]) => {
    copy[camelCase(key) as keyof T] =
      typeof val === "object" && !Array.isArray(val) ? camelize(val) : val;
  });

  return copy as T;
};

export const findValue =
  <T>(obj: T) =>
  <K extends NestedPath<T>, V = PathValue<T, K>>(key: K): V =>
    (<string>key).split("/").reduce<any>((obj, key) => obj?.[key], obj);

export const parseValue = <T>(val: string | number) =>
  (isNaN(Number(val)) ? val : Number(val)) as T;

export const pick = <T, K extends keyof T>(obj: T, ...props: K[]): Pick<T, K> =>
  props.reduce((o, prop) => ({ ...o, [prop]: obj[prop] }), {} as Pick<T, K>);

export const isDefined = <T>(item: T | undefined): item is T => !!item;

export const useSleep = (isRunning: Ref<boolean>) => {
  let timeout: NodeJS.Timeout;
  let _reject: (reason?: any) => void;

  watch(isRunning, (value) => {
    if (!value) {
      clearTimeout(timeout);
      _reject?.("aborted");
    }
  });

  return (ms?: number) => {
    if (!isRunning.value) return Promise.reject();

    return new Promise<void>((resolve, reject) => {
      _reject = reject;
      timeout = setTimeout(resolve, ms);
    });
  };
};

export const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export const mapFn = <T, K>(fn: (item: T) => K, ...items: T[]): K[] =>
  items.map((item) => fn(item));

export type ValueWithUnit = {
  value: Ref<number>;
  unit: Ref<Unit> | Unit;
};

export const useAsValueWithUnit =
  (smallUnit: Unit, bigUnit: Unit) =>
  (value: Ref<number | undefined>, cutoff: number = 1000): ValueWithUnit => ({
    value: computed(() => {
      if (!value.value) return 0;

      return value.value / (Math.abs(value.value) < cutoff ? 1 : 1000);
    }),
    unit: computed(() => (Math.abs(value.value ?? 0) < cutoff ? smallUnit : bigUnit)),
  });

export const useAsWatts = useAsValueWithUnit("W", "kW");
export const useAsWattHours = useAsValueWithUnit("Wh", "kWh");
export const useAsPercentage = (max: number, value: Ref<number>): ValueWithUnit => ({
  value: computed(() => (value.value / max) * 100),
  unit: "%",
});

export const useLastOrNone = (values: HistoricalData<Date, number>[]) =>
  values[values.length - 1]?.value;

export const useStartOfHour = (hour: number, date: Date = new Date()) =>
  startOfHour(setHours(date, hour));

export const sortByHour = <T extends { hour: number }>(a: T, b: T) => a.hour - b.hour;

export const useCombinedHourlyData = (
  a: Observable<HourlyData[]>,
  b: Observable<HourlyData[]>,
  step: number = 1,
  hours = range(0, 24, step),
) =>
  combineLatest([a, b]).pipe(
    map(([a, b]) => {
      const data = merge(a, b);

      return hours.map<HourlyData<number>>((hour) => {
        const value = data.slice(hour, hour + step).reduce((total, { value }) => total + value, 0);

        return { hour, value };
      });
    }),
  );

export const useLast24Hours = <T extends Parameters<PowerHubStore["sensors"]["useOverTime"]>[0]>(
  topic: T,
) =>
  usePowerHubStore().sensors.useOverTime(topic, () => ({
    interval: "h",
    between: between(add(new Date(), { hours: -24 }), new Date()),
  }));

export const useLastHour = <T extends Parameters<PowerHubStore["sensors"]["useOverTime"]>[0]>(
  topic: T,
) =>
  usePowerHubStore().sensors.useOverTime(topic, () => ({
    interval: "min",
    between: between(add(new Date(), { hours: -1 }), new Date()),
  }));

export const useSensorValue =
  (powerHub: PowerHubStore) =>
  <T extends Parameters<PowerHubStore["sensors"]["useMqtt"]>[0]>(topic: T) =>
    powerHub.sensors.useMqtt(topic);

export const useActiveState = (val: boolean) => (val ? "Active" : "Idle");
export const useChargeState = (value: number) => {
  if (value > 0) return "Charging";
  if (value < 0) return "Discharging";

  return "Idle";
};

export const replaceAll = (str: string, find: string, replace: string) =>
  str.replace(new RegExp(find, "g"), replace);
