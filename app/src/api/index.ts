import type { NestedPath, HistoricalData, QueryParams, HourlyData } from "@/types";
import type { TimeInterval } from "@/types/power-hub";
import { Observable, defer, map, repeat, retry, timer } from "rxjs";
import { ajax } from "rxjs/ajax";

export const DEFAULT_POLLING_INTERVAL = 5 * 60 * 1000;

const DEFAULT_HEADERS = {
  Authorization: `Bearer ${import.meta.env.VITE_API_BEARER_TOKEN}`,
};

export type PathFn = (path: string) => string;

const cache: Record<string, Observable<unknown>> = {};

export const usePollingApi = <T>(
  endpoint: string,
  pollingInterval: number = DEFAULT_POLLING_INTERVAL,
  queryParams?: QueryParams,
) =>
  ((<Observable<T>>cache[endpoint]) ??= defer(() =>
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
  ));

export const useMean =
  <T>(endpointFn: PathFn) =>
  <K extends NestedPath<T>>(
    topic: K,
    params?: QueryParams<{
      between?: string;
    }>,
    pollingInterval: number = DEFAULT_POLLING_INTERVAL,
  ) =>
    usePollingApi<number>(`/${endpointFn(topic)}/mean`, pollingInterval, params);

export const useCurrent =
  <T>(endpointFn: PathFn) =>
  <K extends NestedPath<T>>(
    topic: K,
    params?: QueryParams<{
      between?: string;
    }>,
    pollingInterval: number = DEFAULT_POLLING_INTERVAL,
  ) =>
    usePollingApi<number>(`/${endpointFn(topic)}/current`, pollingInterval, params);

export const useTotal =
  <T>(endpointFn: PathFn) =>
  <K extends NestedPath<T>>(
    topic: K,
    params?: QueryParams<{
      between?: string;
    }>,
    pollingInterval: number = DEFAULT_POLLING_INTERVAL,
  ) =>
    usePollingApi<number>(`/${endpointFn(topic)}/total`, pollingInterval, params);

export const toHistoricalData = <V>({
  time,
  value,
}: HistoricalData<string, V>): HistoricalData<Date, V> => ({ time: new Date(time), value });

export const toHourlyData = ({
  time,
  value,
}: HistoricalData<string | Date, number>): HourlyData => ({
  hour: new Date(time).getHours(),
  value: Math.min(value, 100),
});

export const useLastValues =
  <T>(endpointFn: PathFn) =>
  <K extends NestedPath<T>>(
    topic: K,
    params?: QueryParams<{
      between?: string;
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

export const useMeanPerHourOfDay =
  <T>(endpointFn: PathFn) =>
  <K extends NestedPath<T>>(topic: K, pollingInterval: number = DEFAULT_POLLING_INTERVAL) =>
    usePollingApi<HourlyData<number>[]>(
      `/${endpointFn(topic)}/mean/per/hour_of_day`,
      pollingInterval,
    );
