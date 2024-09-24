import {
  usePollingApi,
  useLastValues,
  useMean,
  useOverTime,
  useTotal,
  type PathFn,
  useCurrent,
  useMeanPerHourOfDay,
} from "@shared/api";
import { MqttClient } from "@shared/mqtt";
import type { NestedPath, PathValue, WeatherInfo } from "@shared/types";
import type { SumTree, SensorsTree, ControlValues } from "@shared/types/power-hub";
import { camelize, findValue, pick } from "@shared/utils";
import { defineStore } from "pinia";
import { map, Observable } from "rxjs";

let client: MqttClient;

const defaultLocation = {
  lat: 41.3874,
  lon: 2.1686,
};

const cache: Record<string, Observable<any>> = {};
const useTopic = <T>(topic: string): Observable<T> =>
  (cache[topic] ??= client
    .topic(`power_hub/${topic}`)
    .pipe(map((val) => camelize(JSON.parse(val)) as T)));

const useMqtt =
  <T>(topicPath: string) =>
  <K extends NestedPath<T>, V = PathValue<T, K>>(key: K): Observable<V> =>
    useTopic<T>(topicPath).pipe(map((val) => findValue<T>(val)(key)));

export const usePowerHubStore = defineStore("powerHub", () => {
  const sensorsPathFn: PathFn = (path, [applianceName, fieldName] = path.split("/")) =>
    ["power_hub/appliance_sensors", applianceName, fieldName].join("/");

  const sumPathFn: PathFn = (path) => ["power_hub", ...path.split("/")].join("/");

  const sensors = {
    useLastValues: useLastValues<SensorsTree>(sensorsPathFn),
    useMqtt: useMqtt<SensorsTree>("enriched_sensor_values"),
    useOverTime: useOverTime<SensorsTree>(sensorsPathFn),
    useTotal: useTotal<SensorsTree>(sensorsPathFn),
    useMean: useMean<SensorsTree>(sensorsPathFn),
    useCurrent: useCurrent<SensorsTree>(sensorsPathFn),
  };

  const controlValues = {
    useMqtt: useMqtt<ControlValues>("control_values"),
  };

  const controlModes = {
    useTopic: () => useTopic<ControlValues>("control_modes"),
  };

  const sum = {
    useMean: useMean<SumTree>(sumPathFn),
    useOverTime: useOverTime<SumTree>(sumPathFn),
    useMqtt: useMqtt<SumTree>("power_hub"),
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
      controlValues,
      controlModes,
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
