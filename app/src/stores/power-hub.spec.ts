import { setActivePinia, createPinia } from "pinia";
import { beforeEach, describe, expect, vi, it } from "vitest";
import { MqttClient } from "@/mqtt";
import { of } from "rxjs";
import { usePowerHubStore, type PowerHubStore } from "./power-hub";

describe("PowerHubStore", async () => {
  const client = vi.mocked({
    topic: vi.fn(),
  } as unknown as MqttClient);

  let store: PowerHubStore;

  beforeEach(async () => {
    vi.spyOn(MqttClient, "connect").mockResolvedValue(client);
    client.topic.mockReturnValue(of("5"));
    setActivePinia(createPinia());
    store = await usePowerHubStore().connect();
  });

  describe("appliances", () => {
    it("creates an observable for each appliance", () => {
      store.useAppliance("chiller_switch_valve/position");
      expect(vi.mocked(client).topic).toHaveBeenCalledOnce();
      expect(vi.mocked(client).topic).toHaveBeenCalledWith(
        "power_hub/appliances/chiller_switch_valve/position",
      );
    });

    it("returns a ref", () => {
      const appliance = store.useAppliance("chiller_switch_valve/position");
      expect(appliance.value).toBe(5);
    });
  });

  describe("connections", () => {
    it("creates an observable for each connection", () => {
      store.useConnection("chill_mix/A/temperature");
      expect(vi.mocked(client).topic).toHaveBeenCalledOnce();
      expect(vi.mocked(client).topic).toHaveBeenCalledWith(
        "power_hub/connections/chill_mix/A/temperature",
      );
    });

    it("returns a ref", () => {
      const connection = store.useConnection("chill_mix/A/temperature");
      expect(connection.value).toBe(5);
    });
  });
});
