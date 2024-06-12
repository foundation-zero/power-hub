import type { NestedPath, HistoricalData, QueryParams } from "@/types";
import type { DateRange, TimeInterval } from "@/types/power-hub";
import { defer, map, repeat, retry, timer } from "rxjs";
import { ajax } from "rxjs/ajax";

export const DEFAULT_POLLING_INTERVAL = 60 * 1000;

const DEFAULT_HEADERS = {
  Authorization: `Bearer ${import.meta.env.VITE_API_BEARER_TOKEN}`,
};

export type PathFn = (path: string) => string;

export const usePollingApi = <T>(
  endpoint: string,
  pollingInterval: number = DEFAULT_POLLING_INTERVAL,
  queryParams?: QueryParams,
) =>
  defer(() =>
    ajax<T>({
      url: `${import.meta.env.VITE_API}${endpoint}`,
      headers: DEFAULT_HEADERS,
      queryParams: typeof queryParams === "function" ? queryParams() : queryParams,
    }),
  ).pipe(
    repeat({ delay: pollingInterval }),
    retry({
      delay: (error, count) => timer(Math.min(60000, 2 ^ (count * 1000))),
    }),
    map(({ response }) => response),
  );

export const useMean =
  <T>(endpointFn: PathFn) =>
  <K extends NestedPath<T>>(
    topic: K,
    params?: QueryParams<{
      between?: DateRange;
    }>,
    pollingInterval: number = DEFAULT_POLLING_INTERVAL,
  ) =>
    usePollingApi<number>(`/${endpointFn(topic)}/mean`, pollingInterval, params);

export const useTotal =
  <T>(endpointFn: PathFn) =>
  <K extends NestedPath<T>>(
    topic: K,
    params?: QueryParams<{
      between?: DateRange;
    }>,
    pollingInterval: number = DEFAULT_POLLING_INTERVAL,
  ) =>
    usePollingApi<number>(`/${endpointFn(topic)}/total`, pollingInterval, params);

const toHistoricalData = <V>({
  time,
  value,
}: HistoricalData<string, V>): HistoricalData<Date, V> => ({ time: new Date(time), value });

export const useLastValues =
  <T>(endpointFn: PathFn) =>
  <K extends NestedPath<T>>(
    topic: K,
    params?: QueryParams<{
      between?: DateRange;
    }>,
    pollingInterval: number = DEFAULT_POLLING_INTERVAL,
  ) =>
    usePollingApi<HistoricalData<string, number>[]>(
      `/${endpointFn(topic)}/last_values`,
      pollingInterval,
      params,
    ).pipe(map((values) => values.map(toHistoricalData)));

export const useOverTime =
  <T>(endpointFn: PathFn) =>
  <K extends NestedPath<T>>(
    topic: K,
    params?: QueryParams<{
      between?: string;
      interval: TimeInterval;
    }>,
    pollingInterval: number = DEFAULT_POLLING_INTERVAL,
  ) =>
    usePollingApi<HistoricalData<string, number>[]>(
      `/${endpointFn(topic)}/over/time`,
      pollingInterval,
      params,
    ).pipe(map((values) => values.map(toHistoricalData)));
