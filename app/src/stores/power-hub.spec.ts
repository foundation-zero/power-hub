import { setActivePinia, createPinia } from "pinia";
import { beforeEach, describe, expect, vi, it } from "vitest";
import { MqttClient } from "@/mqtt";
import { of } from "rxjs";
import { usePowerHubStore, type PowerHubStore } from "./power-hub";
import { useObservable } from "@vueuse/rxjs";
import { AjaxResponse, ajax } from "rxjs/ajax";
import type { HistoricalData } from "@/types";

const HEADERS = {
  Authorization: `Bearer ${import.meta.env.VITE_API_BEARER_TOKEN}`,
};

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

  describe("sensors", () => {
    describe("MQTT", () => {
      const mockAndCall = (path: Parameters<typeof store.sensors.useMqtt>[0], value = "5") => {
        client.topic.mockReturnValue(of(value));
        return useObservable(store.sensors.useMqtt(path));
      };

      it("creates an observable for each appliance", () => {
        mockAndCall("chiller_switch_valve/position");
        expect(vi.mocked(client).topic).toHaveBeenCalledOnce();
        expect(vi.mocked(client).topic).toHaveBeenCalledWith(
          "power_hub/appliance_sensors/chiller_switch_valve/position",
        );
      });

      it("returns the value untouched", () => {
        const appliance = mockAndCall("chiller_switch_valve/position");
        expect(appliance.value).toBe(5);
      });
    });

    describe("historical data", () => {
      const mockAndCall = (
        path: Parameters<typeof store.sensors.useHistory>[0],
        time: string = new Date().toString(),
        value = 5,
      ) => {
        vi.spyOn(ajax, "get").mockReturnValue(
          of({ response: [{ time, value }] } as AjaxResponse<HistoricalData[]>),
        );
        return useObservable(store.sensors.useHistory(path));
      };

      it("parses the time value to Date object", () => {
        const observable = mockAndCall("chiller_switch_valve/position");
        expect(observable.value?.[0].time).toBeInstanceOf(Date);
      });

      it("calls the correct endpoint", () => {
        mockAndCall("chiller_switch_valve/position");
        expect(ajax.get).toBeCalledTimes(1);
        expect(ajax.get).toBeCalledWith(
          `${import.meta.env.VITE_API}/power_hub/appliance_sensors/chiller_switch_valve/position/last_values`,
          HEADERS,
        );
      });
    });

    describe("totals", () => {
      const mockAndCall = (path: Parameters<typeof store.sensors.useTotals>[0], value = 5) => {
        vi.spyOn(ajax, "get").mockReturnValue(of({ response: value } as AjaxResponse<number>));
        return useObservable(store.sensors.useTotals(path));
      };

      it("returns the value untouched", () => {
        const observable = mockAndCall("heat_pipes/power");
        expect(observable.value).toBe(5);
      });

      it("calls the correct endpoint", () => {
        mockAndCall("heat_pipes/power");
        expect(ajax.get).toBeCalledTimes(1);
        expect(ajax.get).toBeCalledWith(
          `${import.meta.env.VITE_API}/power_hub/appliance_sensors/heat_pipes/power/total`,
          HEADERS,
        );
      });
    });
  });
});
