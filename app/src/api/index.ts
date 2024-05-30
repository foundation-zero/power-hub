import type { NestedPath, PathValue, HistoricalData } from "@/types";
import type { DateRange, TimeInterval } from "@/types/power-hub";
import { map, repeat } from "rxjs";
import { ajax } from "rxjs/ajax";

export const DEFAULT_POLLING_INTERVAL = 60 * 1000;

const DEFAULT_HEADERS = {
  Authorization: `Bearer ${import.meta.env.VITE_API_BEARER_TOKEN}`,
};

export type PathFn = (path: string) => string;

export const getQueryParams = (between?: DateRange, interval?: TimeInterval): string => {
  const values: Record<string, string> = {};

  if (between) values.between = between.join(",");
  if (interval) values.interval = interval;

  return new URLSearchParams(values).toString();
};

export const useMean =
  <T>(endpointFn: PathFn) =>
  <K extends NestedPath<T>, V = PathValue<T, K>>(
    topic: K,
    between?: DateRange,
    pollingInterval: number = DEFAULT_POLLING_INTERVAL,
  ) =>
    ajax
      .get<V>(
        `${import.meta.env.VITE_API}/${endpointFn(topic)}/mean${getQueryParams(between)}`,
        DEFAULT_HEADERS,
      )
      .pipe(
        repeat({ delay: pollingInterval }),
        map(({ response }) => response),
      );

export const useTotal =
  <T>(endpointFn: PathFn) =>
  <K extends NestedPath<T>, V = PathValue<T, K>>(
    topic: K,
    between?: DateRange,
    pollingInterval: number = DEFAULT_POLLING_INTERVAL,
  ) =>
    ajax
      .get<V>(
        `${import.meta.env.VITE_API}/${endpointFn(topic)}/total${getQueryParams(between)}`,
        DEFAULT_HEADERS,
      )
      .pipe(
        repeat({ delay: pollingInterval }),
        map(({ response }) => response),
      );

export const useLastValues =
  <T>(endpointFn: PathFn) =>
  <K extends NestedPath<T>, V = PathValue<T, K>>(
    topic: K,
    between?: DateRange,
    pollingInterval: number = DEFAULT_POLLING_INTERVAL,
  ) =>
    ajax
      .get<
        HistoricalData<string, V>[]
      >(`${import.meta.env.VITE_API}/${endpointFn(topic)}/last_values${getQueryParams(between)}`, DEFAULT_HEADERS)
      .pipe(
        repeat({ delay: pollingInterval }),
        map(({ response }) =>
          response.map(
            ({ time, value }) => ({ time: new Date(time), value }) as HistoricalData<Date, V>,
          ),
        ),
      );

export const useOverTime =
  <T>(endpointFn: PathFn) =>
  <K extends NestedPath<T>, V = PathValue<T, K>>(
    topic: K,
    between?: DateRange,
    interval: TimeInterval = "h",
    pollingInterval: number = DEFAULT_POLLING_INTERVAL,
  ) =>
    ajax
      .get<
        HistoricalData<string, V>[]
      >(`${import.meta.env.VITE_API}/${endpointFn(topic)}/over/time${getQueryParams(between, interval)}`, DEFAULT_HEADERS)
      .pipe(
        repeat({ delay: pollingInterval }),
        map(({ response }) =>
          response.map(
            ({ time, value }) => ({ time: new Date(time), value }) as HistoricalData<Date, V>,
          ),
        ),
      );
