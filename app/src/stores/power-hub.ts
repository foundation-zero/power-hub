import { MqttClient } from "@/mqtt";
import type { PowerHub, NestedPath, PathValue, RORef, TopicCache } from "@/types";
import { useObservable } from "@vueuse/rxjs";
import { defineStore } from "pinia";
import { map } from "rxjs";

export const usePowerHubStore = defineStore("powerHub", () => {
  let client: MqttClient;

  const useTopic = <P extends keyof PowerHub.Tree, T = PowerHub.Tree[P]>(path: P) => {
    const powerhubValues: TopicCache<T> = {};

    return <K extends NestedPath<T>>(topic: K): RORef<PathValue<T, K> | undefined> => {
      const cachedValue = powerhubValues[topic];

      if (cachedValue) return cachedValue;

      const observable = client
        .topic(`power_hub/${path}/${topic}`)
        .pipe(map((val) => (isNaN(Number(val)) ? val : Number(val)) as PathValue<T, K>));

      const observedValue = useObservable(observable);
      powerhubValues[topic] = observedValue;
      return observedValue;
    };
  };

  const useAppliance = useTopic("appliances");
  const useConnection = useTopic("connections");

  const connect = async () => {
    client ??= await MqttClient.connect(`ws://${location.host}/ws`);

    return {
      useAppliance,
      useConnection,
    };
  };

  return { connect };
});

export type PowerHubStore = Awaited<ReturnType<ReturnType<typeof usePowerHubStore>["connect"]>>;
