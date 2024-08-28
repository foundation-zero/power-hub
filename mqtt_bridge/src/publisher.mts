import { MqttMessage } from "../types/index.js";
import { MqttBridge } from "./bridge.mjs";
import { MqttBroker } from "./broker.mjs";

export class MqttPublisher {
  public readonly id: string = `fz-mqtt-bridge-${Math.random().toString(16).substring(2, 8)}`;

  public constructor(private readonly bridge: MqttBridge) {}

  public publish(origin: MqttBroker, topic: string, message: MqttMessage): void {
    this.bridge.brokers.forEach((broker) => broker !== origin && broker.publish(topic, message));
  }
}
