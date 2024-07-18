import {
  usePollingApi,
  useLastValues,
  useMean,
  useOverTime,
  useTotal,
  type PathFn,
  useCurrent,
  useMeanPerHourOfDay,
} from "@/api";
import { MqttClient } from "@/mqtt";
import type { HistoricalData, NestedPath, WeatherInfo } from "@/types";
import { type SumTree, type SensorsTree, type Tree } from "@/types/power-hub";
import { pick } from "@/utils";
import { defineStore } from "pinia";
import { map } from "rxjs";
import type { SnakeCase } from "type-fest";

let client: MqttClient;

const defaultLocation = {
  lat: 41.3874,
  lon: 2.1686,
};

const useMqtt =
  <K extends keyof Tree, T = Tree[K]>(topicPath: SnakeCase<K>) =>
  <K extends NestedPath<T>>(topic: K) =>
    client
      .topic(`power_hub/${topicPath}/${topic}`)
      .pipe(map((val) => <HistoricalData<string, number>>JSON.parse(val)));

export const usePowerHubStore = defineStore("powerHub", () => {
  const sensorsPathFn: PathFn = (path, [applianceName, fieldName] = path.split("/")) =>
    ["power_hub/appliance_sensors", applianceName, fieldName].join("/");

  const sumPathFn: PathFn = (path) => ["power_hub", ...path.split("/")].join("/");

  const sensors = {
    useLastValues: useLastValues<SensorsTree>(sensorsPathFn),
    useMqtt: useMqtt("appliance_sensors"),
    useOverTime: useOverTime<SensorsTree>(sensorsPathFn),
    useTotal: useTotal<SensorsTree>(sensorsPathFn),
    useMean: useMean<SensorsTree>(sensorsPathFn),
    useCurrent: useCurrent<SensorsTree>(sensorsPathFn),
  };

  const sum = {
    useMean: useMean<SumTree>(sumPathFn),
    useOverTime: useOverTime<SumTree>(sumPathFn),
    useMqtt: useMqtt("power_hub"),
    useMeanPerHourOfDay: useMeanPerHourOfDay<SumTree>(sumPathFn),
  };

  const weather = {
    current: (pollingInterval?: number) =>
      usePollingApi<WeatherInfo>("/weather/current", pollingInterval, defaultLocation),
  };

  const connect = async () => {
    client ??= await MqttClient.connect(
      import.meta.env.VITE_MQTT.replace("%HOST%", location.host),
      { username: import.meta.env.VITE_MQTT_USER, password: import.meta.env.VITE_MQTT_PASSWORD },
    );

    return {
      sensors,
      sum,
      weather,
    };
  };

  return {
    connect,
    sensors: pick(sensors, "useLastValues", "useTotal", "useMean", "useCurrent", "useOverTime"),
    sum: pick(sum, "useMean", "useOverTime", "useMeanPerHourOfDay"),
    weather,
  };
});

export type PowerHubStore = Awaited<ReturnType<ReturnType<typeof usePowerHubStore>["connect"]>>;
