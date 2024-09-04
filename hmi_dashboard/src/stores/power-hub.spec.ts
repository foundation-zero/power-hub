import { setActivePinia, createPinia } from "pinia";
import { beforeEach, describe, expect, vi, it } from "vitest";
import { MqttClient } from "@/mqtt";
import { of } from "rxjs";
import { usePowerHubStore, type PowerHubStore } from "./power-hub";
import { useObservable } from "@vueuse/rxjs";
import * as Ajax from "rxjs/ajax";
import { AjaxResponse } from "rxjs/ajax";
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

    describe("last values", () => {
      const mockAndCall = (
        path: Parameters<typeof store.sensors.useLastValues>[0],
        time: string = new Date().toString(),
        value = 5,
      ) => {
        vi.spyOn(Ajax, "ajax").mockReturnValue(
          of({ response: [{ time, value }] } as AjaxResponse<HistoricalData[]>),
        );
        return useObservable(store.sensors.useLastValues(path));
      };

      it("parses the time value to Date object", () => {
        const observable = mockAndCall("chiller_switch_valve/position");
        expect(observable.value?.[0].time).toBeInstanceOf(Date);
      });

      it("calls the correct endpoint", () => {
        mockAndCall("chiller_switch_valve/position");
        expect(Ajax.ajax).toBeCalledTimes(1);
        expect(Ajax.ajax).toBeCalledWith({
          url: `${import.meta.env.VITE_API}/power_hub/appliance_sensors/chiller_switch_valve/position/last_values`,
          headers: HEADERS,
          params: undefined,
        });
      });
    });

    describe("totals", () => {
      const mockAndCall = (path: Parameters<typeof store.sensors.useTotal>[0], value = 5) => {
        vi.spyOn(Ajax, "ajax").mockReturnValue(of({ response: value } as AjaxResponse<number>));
        return useObservable(store.sensors.useTotal(path));
      };

      it("returns the value untouched", () => {
        const observable = mockAndCall("heat_pipes/power");
        expect(observable.value).toBe(5);
      });

      it("calls the correct endpoint", () => {
        mockAndCall("heat_pipes/power");
        expect(Ajax.ajax).toBeCalledTimes(1);
        expect(Ajax.ajax).toBeCalledWith({
          url: `${import.meta.env.VITE_API}/power_hub/appliance_sensors/heat_pipes/power/total`,
          headers: HEADERS,
          queryParams: undefined,
        });
      });
    });
  });
});
