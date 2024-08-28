import { MqttBridgeOptions, MqttBrokerOptions, MqttTopicMessage } from "../types/index.js";
import { MqttBroker } from "./broker.mjs";
import { Channel, Rx } from "./channel.mjs";
import { differenceInSeconds } from "date-fns";

const wait = (milliseconds: number): Promise<void> =>
  new Promise((resolve) => setTimeout(resolve, milliseconds));

export class MqttBridge {
  public readonly origins: MqttBroker[] = [];
  public readonly targets: MqttBroker[] = [];
  private isStarted: boolean = false;
  private notAllConnectedStamp: Date | null = null;
  private lastPublish: Date | null = null;

  constructor(private readonly options: MqttBridgeOptions) {}

  public addOrigin(brokerOptions: MqttBrokerOptions): this {
    this.origins.push(new MqttBroker(brokerOptions));
    return this;
  }

  public addTarget(brokerOptions: MqttBrokerOptions): this {
    this.targets.push(new MqttBroker(brokerOptions));
    return this;
  }

  private get brokers(): MqttBroker[] {
    return [...this.origins, ...this.targets];
  }

  public async start(): Promise<void> {
    if (this.isStarted) return;

    if (!this.origins.length || !this.targets.length)
      throw "Configuration should include at least 1 origin and 1 target";

    this.isStarted = true;

    const [messagesTx, messagesRx] = new Channel<MqttTopicMessage>().split();

    await Promise.all(this.brokers.map((broker) => broker.connectAndSubscribe(messagesTx)));

    const healths = await Promise.all(this.brokers.map((broker) => broker.publishHealth()));
    if (!healths.every((health) => health)) {
      console.error("failed to publish initial health");
      process.exit();
    }
    this.lastPublish = new Date();

    await Promise.all([this.message(messagesRx), this.runHealthChecks(messagesRx)]);
  }

  private async message(rx: Rx<MqttTopicMessage>): Promise<void> {
    while (true) {
      await Promise.all(this.targets.map((target) => target.flushQueue(rx)));
      await wait(50);
    }
  }

  private async runHealthChecks(rx: Rx<MqttTopicMessage>): Promise<void> {
    while (true) {
      await this.healthChecks(rx);
      await wait(50);
    }
  }

  private async healthChecks(rx: Rx<MqttTopicMessage>): Promise<void> {
    this.checkConnections();
    this.checkQueue(rx);
    await this.publishHealth();
  }

  private checkConnections() {
    const notAllConnected = !this.brokers.every((broker) => broker.isConnected());

    if (notAllConnected) {
      if (
        this.notAllConnectedStamp &&
        differenceInSeconds(new Date(), this.notAllConnectedStamp) >
          this.options.connectionTimeoutSeconds
      ) {
        console.error(`client has disconnected for ${this.options.connectionTimeoutSeconds}`);
        process.exit(); // depend on docker compose for restart
      }
      this.notAllConnectedStamp ??= new Date();
    } else {
      this.notAllConnectedStamp = null;
    }
  }

  private checkQueue(rx: Rx<MqttTopicMessage>) {
    if (rx.size() > this.options.maxQueueSize) {
      console.error(`queue size too large ${rx.size()} > ${this.options.maxQueueSize}`);
      process.exit();
    }
  }

  private async publishHealth() {
    if (!this.lastPublish) {
      console.error("never published");
      process.exit();
    }
    if (differenceInSeconds(new Date(), this.lastPublish) > this.options.publishIntervalSeconds) {
      const healths = await Promise.all(
        [...this.origins, ...this.targets].map((broker) => broker.publishHealth()),
      );
      if (healths.every((health) => health)) {
        this.lastPublish = new Date();
      }
    }
    if (differenceInSeconds(new Date(), this.lastPublish) > this.options.publishTimeoutSeconds) {
      console.error(`failed to publish health message for ${this.options.publishTimeoutSeconds}`);
      process.exit();
    }
  }
}
