import type { NestedPath, PathValue, HistoricalData } from "@/types";
import type { DateRange, TimeInterval } from "@/types/power-hub";
import { map, repeat, retry, timer } from "rxjs";
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

  const params = new URLSearchParams(values).toString();

  return params ? `?${params}` : "";
};

const useApi = <T>(endpoint: string, pollingInterval: number) =>
  ajax.get<T>(`${import.meta.env.VITE_API}${endpoint}`, DEFAULT_HEADERS).pipe(
    repeat({ delay: pollingInterval }),
    retry({
      delay: (error, count) => timer(Math.min(60000, 2 ^ (count * 1000))),
    }),
    map(({ response }) => response),
  );

export const useMean =
  <T>(endpointFn: PathFn) =>
  <K extends NestedPath<T>, V = PathValue<T, K>>(
    topic: K,
    between?: DateRange,
    pollingInterval: number = DEFAULT_POLLING_INTERVAL,
  ) =>
    useApi<V>(`/${endpointFn(topic)}/mean${getQueryParams(between)}`, pollingInterval);

export const useTotal =
  <T>(endpointFn: PathFn) =>
  <K extends NestedPath<T>, V = PathValue<T, K>>(
    topic: K,
    between?: DateRange,
    pollingInterval: number = DEFAULT_POLLING_INTERVAL,
  ) =>
    useApi<V>(`/${endpointFn(topic)}/total${getQueryParams(between)}`, pollingInterval);

const toHistoricalData = <V>({ time, value }: HistoricalData<string, V>) =>
  ({ time: new Date(time), value }) as HistoricalData<Date, V>;

export const useLastValues =
  <T>(endpointFn: PathFn) =>
  <K extends NestedPath<T>, V = PathValue<T, K>>(
    topic: K,
    between?: DateRange,
    pollingInterval: number = DEFAULT_POLLING_INTERVAL,
  ) =>
    useApi<HistoricalData<string, V>[]>(
      `/${endpointFn(topic)}/last_values${getQueryParams(between)}`,
      pollingInterval,
    ).pipe(map((values) => values.map(toHistoricalData)));

export const useOverTime =
  <T>(endpointFn: PathFn) =>
  <K extends NestedPath<T>, V = PathValue<T, K>>(
    topic: K,
    between?: DateRange,
    interval: TimeInterval = "h",
    pollingInterval: number = DEFAULT_POLLING_INTERVAL,
  ) =>
    useApi<HistoricalData<string, V>[]>(
      `/${endpointFn(topic)}/over/time${getQueryParams(between, interval)}`,
      pollingInterval,
    ).pipe(map((values) => values.map(toHistoricalData)));
