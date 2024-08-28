import { MqttBrokerOptions } from "../types/index.js";
import { MqttBroker } from "./broker.mjs";
import { MqttPublisher } from "./publisher.mjs";

export class MqttBridge {
  public readonly brokers: MqttBroker[] = [];
  private readonly publisher = new MqttPublisher(this);
  private readonly topics: string[] = [];
  private isStarted: boolean = false;

  public add(brokerOptions: MqttBrokerOptions): this {
    this.brokers.push(new MqttBroker(this.publisher, brokerOptions));
    return this;
  }

  public subscribe(...topics: string[]): this {
    this.topics.push(...topics);
    return this;
  }

  public start(): void {
    if (this.isStarted) return;

    if (!this.topics.length) throw "Not subscribed to any topics";

    const origins = this.brokers.filter((broker) => broker.options.origin);
    const targets = this.brokers.filter((broker) => broker.options.target);

    if (!origins.length || !targets.length)
      throw "Configuration should include at least 1 origin and 1 target";

    this.isStarted = true;

    this.brokers.forEach((broker) => broker.connectAndSubscribe(this.topics));
  }
}
