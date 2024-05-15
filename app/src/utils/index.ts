import type { Activatable, Flowable, Muteable } from "@/types";
import { watch, type Ref } from "vue";

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

export const deactivate = (item: Activatable) => (item.active = false);
export const activate = (item: Activatable) => (item.active = true);
export const mute = (item: Muteable) => (item.muted = true);
export const unmute = (item: Muteable) => (item.muted = false);
export const startFlow = (item: Flowable) => (item.flowing = true);
export const stopFlow = (item: Flowable) => (item.flowing = false);

export const mapFn = <T, K>(fn: (item: T) => K, ...items: T[]): K[] =>
  items.map((item) => fn(item));
