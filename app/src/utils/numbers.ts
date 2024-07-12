import type { Direction } from "@/types";
import { useTimeout } from "@vueuse/core";
import { ref } from "vue";

export const JOULE_TO_WATT_HOUR = 3600;

export const jouleToWattHour = (val: number) => val / JOULE_TO_WATT_HOUR;

export const formattedNumber =
  (digits: number = 1) =>
  (val: number = 0) =>
    +val.toLocaleString("nl-NL", {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    });

export const formattedInt = formattedNumber(0);

export const formattedTemperature = formattedNumber;

export const useRandomNumber = (min: number, max: number, timeout?: number) => {
  const val = ref(0);
  const dx = max - min;

  const random = () => {
    val.value = Math.round(min + Math.random() * dx);
    useTimeout(timeout ?? 5000 + Math.random() * 5000, { callback: random });
  };

  random();

  return val;
};

export const useCounter = (timeout: number = 1000) => {
  const val = ref(0);

  const next = () => {
    val.value += 1;
    useTimeout(timeout, { callback: next });
  };

  next();

  return val;
};

export const useRevolvingNumber = (
  min: number,
  max: number,
  start = max,
  stepSize = 1,
  direction: Direction = "down",
  timeout = 1000,
) => {
  const val = ref(start);

  const step = () => {
    if (direction === "down") val.value -= stepSize;
    else val.value += stepSize;

    if (val.value <= min) direction = "up";
    else if (val.value >= max) direction = "down";
    useTimeout(timeout, { callback: step });
  };

  step();

  return val;
};
