import { MqttClient } from "@/mqtt";
import type { NestedPath, PathValue, HistoricalData } from "@/types";
import type { AppliancesTree, ComputedTree, ConnectionsTree, Tree } from "@/types/power-hub";
import { parseValue, pick } from "@/utils";
import { defineStore } from "pinia";
import { map, repeat } from "rxjs";
import { ajax } from "rxjs/ajax";

const DEFAULT_POLLING_INTERVAL = 60 * 1000;

let client: MqttClient;

type PathFn = (path: string) => string;
const defaultPathFn: PathFn = (path) => path;

const useTotals =
  <T>(endpointFn: PathFn = defaultPathFn) =>
  <K extends NestedPath<T>, V = PathValue<T, K>>(
    topic: K,
    pollingInterval: number = DEFAULT_POLLING_INTERVAL,
  ) =>
    ajax
      .getJSON<V>(`/api/appliances/${endpointFn(topic)}/total`)
      .pipe(repeat({ delay: pollingInterval }));

const useHistory =
  <T>(endpointFn: PathFn = defaultPathFn) =>
  <K extends NestedPath<T>, V = PathValue<T, K>>(
    topic: K,
    pollingInterval: number = DEFAULT_POLLING_INTERVAL,
  ) =>
    ajax
      .getJSON<HistoricalData<string, V>[]>(`/api/appliances/${endpointFn(topic)}/last_values`)
      .pipe(
        repeat({ delay: pollingInterval }),
        map((data) =>
          data.map(
            ({ time, value }) => ({ time: new Date(time), value }) as HistoricalData<Date, V>,
          ),
        ),
      );

const useMqtt =
  <T>(topicPath: keyof Tree) =>
  <K extends NestedPath<T>, V = PathValue<T, K>>(topic: K) =>
    client.topic(`power_hub/${topicPath}/${topic}`).pipe(map(parseValue<V>));

export const usePowerHubStore = defineStore("powerHub", () => {
  const connectionsPathFn: PathFn = (
    path,
    [applianceName, connectionName, fieldName] = path.split("/"),
  ) => [applianceName, "connections", connectionName, fieldName].join("/");

  const appliances = {
    useHistory: useHistory<AppliancesTree>(),
    useMqtt: useMqtt<AppliancesTree>("appliances"),
  };

  const connections = {
    useHistory: useHistory<ConnectionsTree>(connectionsPathFn),
    useMqtt: useMqtt<ConnectionsTree>("connections"),
  };

  const computed = {
    useHistory: useHistory<ComputedTree>(),
    useTotals: useTotals<ComputedTree>(),
  };

  const connect = async () => {
    client ??= await MqttClient.connect(`ws://${location.host}/ws`);

    return {
      computed,
      appliances,
      connections,
    };
  };

  return {
    connect,
    computed,
    connections: pick(connections, "useHistory"),
    appliances: pick(appliances, "useHistory"),
  };
});

export type PowerHubStore = Awaited<ReturnType<ReturnType<typeof usePowerHubStore>["connect"]>>;
