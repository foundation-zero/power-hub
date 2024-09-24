import { beforeEach, describe, expect, it, vi } from "vitest";
import { MqttClient } from ".";
import mqtt from "mqtt";

describe("MqttClient", () => {
  const mockClient: mqtt.MqttClient = {
    publishAsync: vi.fn(),
    subscribe: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  } as unknown as mqtt.MqttClient;

  let client: MqttClient;

  beforeEach(async () => {
    vi.spyOn(mqtt, "connectAsync").mockResolvedValue(mockClient);
    client = await MqttClient.connect("");
  });

  describe("subscribing to a topic", () => {
    it("subscribes to the broker", () => {
      const observable = client.topic("some/topic");
      expect(mockClient.subscribe).not.toHaveBeenCalled();
      observable.subscribe();
      expect(mockClient.subscribe).toHaveBeenCalledOnce();
      expect(mockClient.subscribe).toHaveBeenCalledWith("some/topic");
    });
  });
});
