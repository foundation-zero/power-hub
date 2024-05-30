import { useLastValues, useMean, useOverTime, useTotal, type PathFn } from "@/api";
import { MqttClient } from "@/mqtt";
import type { HistoricalData, NestedPath } from "@/types";
import { type SumTree, type SensorsTree, type Tree } from "@/types/power-hub";
import { pick } from "@/utils";
import { defineStore } from "pinia";
import { map } from "rxjs";
import type { SnakeCase } from "type-fest";

let client: MqttClient;

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
    useTotal: useTotal<SensorsTree>(sensorsPathFn),
    useMean: useMean<SensorsTree>(sensorsPathFn),
  };

  const sum = {
    useMean: useMean<SumTree>(sumPathFn),
    useOverTime: useOverTime<SumTree>(sumPathFn),
    useMqtt: useMqtt("power_hub"),
  };

  const connect = async () => {
    client ??= await MqttClient.connect(
      import.meta.env.VITE_MQTT.replace("%HOST%", location.host),
      { username: import.meta.env.VITE_MQTT_USER, password: import.meta.env.VITE_MQTT_PASSWORD },
    );

    return {
      sensors,
      sum,
    };
  };

  return {
    connect,
    sensors: pick(sensors, "useLastValues", "useTotal", "useMean"),
    sum: pick(sum, "useMean", "useOverTime"),
  };
});

export type PowerHubStore = Awaited<ReturnType<ReturnType<typeof usePowerHubStore>["connect"]>>;
