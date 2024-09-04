import type { HistoricalData, HourlyData } from "@/types";
import { setHours, startOfHour } from "date-fns";
import { merge, range } from "lodash";
import { combineLatest, map, type Observable } from "rxjs";
import { computed, watch, type Ref } from "vue";

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

export const useAsValueWithUnit =
  (baseUnit: string) =>
  (value: Ref<number | undefined>, cutoff: number = 1000) => ({
    value: computed(() => {
      if (!value.value) return 0;

      return value.value / (Math.abs(value.value) < cutoff ? 1 : 1000);
    }),
    unit: computed(() => (Math.abs(value.value ?? 0) < cutoff ? baseUnit : `k${baseUnit}`)),
  });

export const useAsWatts = useAsValueWithUnit("W");
export const useAsWattHours = useAsValueWithUnit("Wh");

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
      const data = merge(a.slice().sort(sortByHour), b.slice().sort(sortByHour));

      return hours.map<HourlyData<number>>((hour) => {
        const value = data.slice(hour, hour + step).reduce((total, { value }) => total + value, 0);

        return { hour, value: Math.max(value, 500) };
      });
    }),
  );
