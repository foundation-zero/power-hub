import type {
  Activatable,
  Flowable,
  Hideable,
  Highlightable,
  Muteable,
  Customizable,
  HistoricalData,
} from "@/types";
import { setHours, startOfHour } from "date-fns";
import { computed, watch, type Ref } from "vue";

export const parseValue = <T>(val: string | number) =>
  (isNaN(Number(val)) ? val : Number(val)) as T;

export const pick = <T, K extends keyof T>(obj: T, ...props: K[]): Pick<T, K> =>
  props.reduce((o, prop) => ({ ...o, [prop]: obj[prop] }), {} as Pick<T, K>);

export const isDefined = <T>(item: T | undefined): item is T => !!item;

export const getCenterPosition = (items: HTMLElement[]) => {
  const x = { min: 10000, max: 0 };
  const y = { min: 10000, max: 0 };

  items.forEach((item) => {
    const { xpos, ypos } = item.dataset;

    x.min = Math.min(x.min, +xpos!);
    x.max = Math.max(x.max, +xpos!);
    y.min = Math.min(y.min, +ypos!);
    y.max = Math.max(y.max, +ypos!);
  });

  return { x: (x.max + x.min) / 2, y: (y.max + y.min) / 2 };
};

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

export const hide = <T extends Hideable>(item: T) => (item.hidden = true);
export const show = <T extends Hideable>(item: T) => (item.hidden = false);
export const activate = <T extends Activatable>(item: T) => (item.active = true);
export const deactivate = <T extends Activatable>(item: T) => (item.active = false);
export const mute = <T extends Muteable>(item: T) => (item.muted = true);
export const unmute = <T extends Muteable>(item: T) => (item.muted = false);
export const startFlow = <T extends Flowable>(item: T) => (item.flowing = true);
export const stopFlow = <T extends Flowable>(item: T) => (item.flowing = false);
export const customize = <T extends Customizable>(item: T) => (item.custom = true);
export const decustomize = <T extends Customizable>(item: T) => (item.custom = false);
export const highlight = <T extends Highlightable>(item: T) => (item.highlighted = true);
export const dehighlight = <T extends Highlightable>(item: T) => (item.highlighted = false);
export const reset = <T extends Record<string, boolean>>(item: T) => {
  Object.entries(item).forEach(([key, val]) => {
    if (key !== "skip" && typeof val === "boolean") delete item[key];
  });
};

export const mapFn = <T, K>(fn: (item: T) => K, ...items: T[]): K[] =>
  items.map((item) => fn(item));

export const useAsValueWithUnit =
  (baseUnit: string) =>
  (value: Ref<number | undefined>, cutoff: number = 1000) => ({
    value: computed(() => {
      if (!value.value) return 0;

      return value.value / (value.value < cutoff ? 1 : 1000);
    }),
    unit: computed(() => ((value.value ?? 0) < cutoff ? baseUnit : `k${baseUnit}`)),
  });

export const useAsWatts = useAsValueWithUnit("W");
export const useAsWattHours = useAsValueWithUnit("Wh");

export const useLastOrNone = (values: HistoricalData<Date, number>[]) =>
  values[values.length - 1]?.value;

export const useStartOfHour = (hour: number, date: Date = new Date()) =>
  startOfHour(setHours(date, hour));
