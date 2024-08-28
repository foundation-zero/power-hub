import { MqttClient, connectAsync } from "mqtt";
import { MqttBrokerOptions, MqttMessage, MqttTopicMessage } from "../types/index.js";
import { Rx, Tx } from "./channel.mjs";

const RETRY_TIMEOUT_IN_MS = 10000;

export class MqttBroker {
  public constructor(public readonly options: MqttBrokerOptions) {
    this.subscribeTopics = options.subscribeTopics ?? [];
  }

  public client?: MqttClient;
  private readonly subscribeTopics: string[];
  private readonly retryQueue: MqttTopicMessage[] = [];

  private get name(): string {
    return `MQTT broker [${this.options.name ?? this.options.url}]`;
  }

  public async connectAndSubscribe(tx: Tx<MqttTopicMessage>) {
    if (this.client) return;

    try {
      this.client = await connectAsync(this.options.url, {
        ...(this.options.authentication ?? {}),
        reconnectPeriod: RETRY_TIMEOUT_IN_MS,
        keepalive: this.options.keepalive,
        protocol: this.options.protocol,
        ca: this.options.ca,
      });

      console.info(`Connected to ${this.name}`);

      this.client.on("reconnect", () => console.info(`Reconnecting to ${this.name}`));
      this.client.on("connect", () => console.info(`Reconnected to ${this.name}`));
      this.client.on("disconnect", () => console.warn(`Disconnected from ${this.name}`));
      this.client.on("offline", () =>
        // mqtt automatically reconnects after this event
        console.warn(`Client for ${this.name} went offline`),
      );
      this.client.on("error", (e) =>
        // Could this potentially log duplicate errors for subscribing and publishing?
        console.error(`Error occurred on ${this.name}: ${e}`),
      );

      this.client.on("message", (topic: string, message: Buffer) => {
        tx.queue([topic, message]);
      });
      await this.subscribeToTopics();
    } catch (e) {
      console.error(`Connection to ${this.name} failed: ${e}`);
      setTimeout(() => this.connectAndSubscribe(tx), RETRY_TIMEOUT_IN_MS);
    }
  }

  public async flushQueue(rx: Rx<MqttTopicMessage>) {
    if (!this.isConnected()) return;

    let message: MqttTopicMessage | undefined;
    const retryQueue: MqttTopicMessage[] = [];

    while ((message = rx.shift())) {
      await this.publish(...message, retryQueue);
    }
    while ((message = this.retryQueue.shift())) {
      await this.publish(...message, retryQueue);
    }
    this.retryQueue.push(...retryQueue);
  }

  private async subscribeToTopics() {
    if (!this.client || !this.subscribeTopics.length) return;

    try {
      await this.client.subscribeAsync(this.subscribeTopics);
    } catch (e) {
      console.error(`Subscribing to ${this.name} failed: ${e}`);
      setTimeout(() => this.subscribeToTopics(), RETRY_TIMEOUT_IN_MS);
    }
  }

  public async publish(topic: string, message: MqttMessage, retryQueue: MqttTopicMessage[]) {
    if (!this.client) {
      retryQueue.push([topic, message]);
      return;
    }

    try {
      await this.client.publishAsync(topic, message);
    } catch (e) {
      // If it fails because of a parse error we should not try and publish again, it will yield the same result.
      // All other reasons (sudden disconnect) are already handled internally by the mqtt client.
      console.error(`Publishing to ${this.name} failed: ${e}`);
    }
  }

  public isConnected(): boolean {
    return this.client?.connected ?? false;
  }

  public async publishHealth(): Promise<boolean> {
    if (!this.client || !this.isConnected()) {
      return false;
    }

    try {
      await this.client.publishAsync("health/bridge", "connected", {});
      return true;
    } catch (e) {
      return false;
    }
  }
}
