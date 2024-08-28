import { MqttClient, connectAsync } from "mqtt";
import { MqttPublisher } from "./publisher.mjs";
import { MqttBrokerOptions, MqttMessage, MqttTopicMessage } from "../types/index.js";

const RETRY_TIMEOUT_IN_MS = 10000;

export class MqttBroker {
  public constructor(
    private readonly publisher: MqttPublisher,
    public readonly options: MqttBrokerOptions,
  ) {}

  private client?: MqttClient;
  private readonly queue: MqttTopicMessage[] = [];

  private get name(): string {
    return `MQTT broker [${this.options.name ?? this.options.url}]`;
  }

  public async connectAndSubscribe(topics: string[]) {
    if (this.client) return;

    try {
      this.client = await connectAsync(this.options.url, {
        ...(this.options.authentication ?? {}),
        clientId: this.publisher.id,
        reconnectPeriod: RETRY_TIMEOUT_IN_MS,
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

      if (this.options.origin) {
        this.client.on("message", this.onMessage.bind(this));
        this.subscribeToTopics(topics);
      }

      if (this.options.target) {
        this.flushQueue();
      }
    } catch (e) {
      console.error(`Connection to ${this.name} failed: ${e}`);
      setTimeout(() => this.connectAndSubscribe(topics), RETRY_TIMEOUT_IN_MS);
    }
  }

  private async flushQueue() {
    if (!this.client || !this.queue.length) return;

    let message: MqttTopicMessage | undefined;

    while ((message = this.queue.shift())) {
      await this.publish(...message);
    }
  }

  private async subscribeToTopics(topics: string[]) {
    if (!this.client) return;

    try {
      await this.client.subscribeAsync(topics);
    } catch (e) {
      console.error(`Subscribing to ${this.name} failed: ${e}`);
      setTimeout(() => this.subscribeToTopics(topics), RETRY_TIMEOUT_IN_MS);
    }
  }

  public async publish(topic: string, message: MqttMessage) {
    if (!this.options.target) return;

    if (!this.client) {
      this.queue.push([topic, message]);
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

  private onMessage(topic: string, message: Buffer): void {
    this.publisher.publish(this, topic, message);
  }
}
