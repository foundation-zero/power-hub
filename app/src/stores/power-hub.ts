import { MqttClient } from "@/mqtt";
import type { NestedPath, PathValue, HistoricalData } from "@/types";
import type { SensorsTree, ComputedTree, Tree } from "@/types/power-hub";
import { parseValue, pick } from "@/utils";
import { defineStore } from "pinia";
import { map, repeat } from "rxjs";
import { ajax } from "rxjs/ajax";
import type { SnakeCase } from "type-fest";

const DEFAULT_POLLING_INTERVAL = 60 * 1000;

let client: MqttClient;

type PathFn = (path: string) => string;

const useTotals =
  <T>(endpointFn: PathFn) =>
  <K extends NestedPath<T>, V = PathValue<T, K>>(
    topic: K,
    pollingInterval: number = DEFAULT_POLLING_INTERVAL,
  ) =>
    ajax.getJSON<V>(`/api/${endpointFn(topic)}/total`).pipe(repeat({ delay: pollingInterval }));

const useHistory =
  <T>(endpointFn: PathFn) =>
  <K extends NestedPath<T>, V = PathValue<T, K>>(
    topic: K,
    pollingInterval: number = DEFAULT_POLLING_INTERVAL,
  ) =>
    ajax.getJSON<HistoricalData<string, V>[]>(`/api/${endpointFn(topic)}/last_values`).pipe(
      repeat({ delay: pollingInterval }),
      map((data) =>
        data.map(({ time, value }) => ({ time: new Date(time), value }) as HistoricalData<Date, V>),
      ),
    );

const useMqtt =
  <K extends keyof Tree, T = Tree[K]>(topicPath: SnakeCase<K>) =>
  <K extends NestedPath<T>, V = PathValue<T, K>>(topic: K) =>
    client.topic(`power_hub/${topicPath}/${topic}`).pipe(map(parseValue<V>));

export const usePowerHubStore = defineStore("powerHub", () => {
  const sensorsPathFn: PathFn = (path, [applianceName, fieldName] = path.split("/")) =>
    ["appliance_sensors", applianceName, fieldName].join("/");

  const computedPathFn: PathFn = (path, [applianceName, fieldName] = path.split("/")) =>
    ["appliances", applianceName, fieldName].join("/");

  const sensors = {
    useHistory: useHistory<SensorsTree>(sensorsPathFn),
    useMqtt: useMqtt("appliance_sensors"),
  };

  const computed = {
    useHistory: useHistory<ComputedTree>(computedPathFn),
    useTotals: useTotals<ComputedTree>(computedPathFn),
  };

  const connect = async () => {
    client ??= await MqttClient.connect(`ws://${location.host}/ws`);

    return {
      computed,
      sensors,
    };
  };

  return {
    connect,
    computed,
    sensors: pick(sensors, "useHistory"),
  };
});

export type PowerHubStore = Awaited<ReturnType<ReturnType<typeof usePowerHubStore>["connect"]>>;
