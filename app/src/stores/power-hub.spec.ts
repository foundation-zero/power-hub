import { setActivePinia, createPinia } from "pinia";
import { beforeEach, describe, expect, vi, it } from "vitest";
import { MqttClient } from "@/mqtt";
import { of } from "rxjs";
import { usePowerHubStore, type PowerHubStore } from "./power-hub";
import { useObservable } from "@vueuse/rxjs";
import { ajax } from "rxjs/ajax";

describe("PowerHubStore", async () => {
  const client = vi.mocked({
    topic: vi.fn(),
  } as unknown as MqttClient);

  let store: PowerHubStore;

  beforeEach(async () => {
    vi.spyOn(MqttClient, "connect").mockResolvedValue(client);
    setActivePinia(createPinia());
    store = await usePowerHubStore().connect();
  });

  describe("appliances", () => {
    describe("MQTT", () => {
      const mockAndCall = (path: Parameters<typeof store.appliances.useMqtt>[0], value = "5") => {
        client.topic.mockReturnValue(of(value));
        return useObservable(store.appliances.useMqtt(path));
      };

      it("creates an observable for each appliance", () => {
        mockAndCall("chiller_switch_valve/position");
        expect(vi.mocked(client).topic).toHaveBeenCalledOnce();
        expect(vi.mocked(client).topic).toHaveBeenCalledWith(
          "power_hub/appliances/chiller_switch_valve/position",
        );
      });

      it("returns the value untouched", () => {
        const appliance = mockAndCall("chiller_switch_valve/position");
        expect(appliance.value).toBe(5);
      });
    });

    describe("historical data", () => {
      const mockAndCall = (
        path: Parameters<typeof store.appliances.useHistory>[0],
        time: string = new Date().toString(),
        value = 5,
      ) => {
        vi.spyOn(ajax, "getJSON").mockReturnValue(of([{ time, value }]));
        return useObservable(store.appliances.useHistory(path));
      };

      it("parses the time value to Date object", () => {
        const observable = mockAndCall("chiller_switch_valve/position");
        expect(observable.value?.[0].time).toBeInstanceOf(Date);
      });

      it("calls the correct endpoint", () => {
        mockAndCall("chiller_switch_valve/position");
        expect(ajax.getJSON).toBeCalledTimes(1);
        expect(ajax.getJSON).toBeCalledWith(
          "/api/appliances/chiller_switch_valve/position/last_values",
        );
      });
    });
  });

  describe("connections", () => {
    describe("MQTT", () => {
      beforeEach(() => {
        client.topic.mockReturnValue(of("5"));
      });

      it("creates an observable for each connection", () => {
        store.connections.useMqtt("chill_mix/a/temperature");
        expect(vi.mocked(client).topic).toHaveBeenCalledOnce();
        expect(vi.mocked(client).topic).toHaveBeenCalledWith(
          "power_hub/connections/chill_mix/a/temperature",
        );
      });

      it("returns the value untouched", () => {
        const connection = useObservable(store.connections.useMqtt("chill_mix/a/temperature"));
        expect(connection.value).toBe(5);
      });
    });

    describe("historical data", () => {
      const mockAndCall = (
        path: Parameters<typeof store.connections.useHistory>[0],
        time: string = new Date().toString(),
        value = 5,
      ) => {
        vi.spyOn(ajax, "getJSON").mockReturnValue(of([{ time, value }]));
        return useObservable(store.connections.useHistory(path));
      };

      it("parses the time value to Date object", () => {
        const observable = mockAndCall("chill_mix/a/temperature");
        expect(observable.value?.[0].time).toBeInstanceOf(Date);
      });

      it("calls the correct endpoint", () => {
        mockAndCall("chill_mix/a/temperature");
        expect(ajax.getJSON).toBeCalledTimes(1);
        expect(ajax.getJSON).toBeCalledWith(
          "/api/appliances/chill_mix/connections/a/temperature/last_values",
        );
      });
    });
  });

  describe("computed", () => {
    describe("historical data", () => {
      const mockAndCall = (
        path: Parameters<typeof store.computed.useHistory>[0],
        time: string = new Date().toString(),
        value = 5,
      ) => {
        vi.spyOn(ajax, "getJSON").mockReturnValue(of([{ time, value }]));
        return useObservable(store.computed.useHistory(path));
      };

      it("parses the time value to Date object", () => {
        const observable = mockAndCall("heat_pipes/power");
        expect(observable.value?.[0].time).toBeInstanceOf(Date);
      });

      it("calls the correct endpoint", () => {
        mockAndCall("heat_pipes/power");
        expect(ajax.getJSON).toBeCalledTimes(1);
        expect(ajax.getJSON).toBeCalledWith("/api/appliances/heat_pipes/power/last_values");
      });
    });

    describe("totals", () => {
      const mockAndCall = (path: Parameters<typeof store.computed.useTotals>[0], value = 5) => {
        vi.spyOn(ajax, "getJSON").mockReturnValue(of(value));
        return useObservable(store.computed.useTotals(path));
      };

      it("returns the value untouched", () => {
        const observable = mockAndCall("heat_pipes/power");
        expect(observable.value).toBe(5);
      });

      it("calls the correct endpoint", () => {
        mockAndCall("heat_pipes/power");
        expect(ajax.getJSON).toBeCalledTimes(1);
        expect(ajax.getJSON).toBeCalledWith("/api/appliances/heat_pipes/power/total");
      });
    });
  });
});
