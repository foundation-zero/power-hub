import { describe, expect, it, beforeEach, vitest } from "vitest";
import { MqttBridge } from "./bridge.mjs";
import { MqttBroker } from "./broker.mjs";

describe(MqttBridge, () => {
  let bridge: MqttBridge;

  beforeEach(() => {
    bridge = new MqttBridge();
  });

  describe("starting the bridge", () => {
    beforeEach(() => {
      vitest.spyOn(MqttBroker.prototype, "connectAndSubscribe").mockResolvedValue();
    });

    describe("with valid configuration", () => {
      it("connects to all brokers", () => {
        bridge
          .add({ url: "mqtt://origin", origin: true })
          .add({ url: "mqtt://target", target: true })
          .subscribe("#")
          .start();

        expect(MqttBroker.prototype.connectAndSubscribe).toHaveBeenCalledTimes(2);
      });
    });

    describe("without origins", () => {
      it.fails("throws an error", () => {
        bridge.add({ url: "origin", target: true }).add({ url: "target", target: true });
        bridge.start();
      });
    });

    describe("without targets", () => {
      it.fails("throws an error", () => {
        bridge.add({ url: "origin", origin: true }).add({ url: "target", origin: true });
        bridge.start();
      });
    });
  });
});
