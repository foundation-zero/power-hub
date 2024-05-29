import mqtt from "mqtt";
import { fromEvent, merge, Observable } from "rxjs";
import { filter, ignoreElements, map, share } from "rxjs/operators";

type Message = {
  topic: string;
  message: string;
};

type Authentication = {
  username?: string;
  password?: string;
};

export class MqttClient {
  private messages: Observable<Message>;
  private constructor(private client: mqtt.MqttClient) {
    this.messages = fromEvent(client, "message", (topic, msg) => ({
      topic: topic as unknown as string,
      message: msg.toString(),
    })).pipe(share());
  }

  static async connect(url: string, auth: Authentication = {}): Promise<MqttClient> {
    const clientId = `powerhub-${Math.random().toString(16).substring(2, 8)}`;
    const client = await mqtt.connectAsync(url, {
      ...auth,
      clientId,
      will: {
        topic: `health/${clientId}`,
        payload: "disconnected" as unknown as Buffer, // cast because browsers don't Buffer
        qos: 1,
        retain: true,
      },
    });

    await client.publishAsync(`health/${clientId}`, "connected");
    return new MqttClient(client);
  }

  topic(topic: string): Observable<string> {
    return merge(
      new Observable(() => {
        this.client.subscribe(topic);

        return () => {
          this.client.unsubscribe(topic);
        };
      }).pipe(ignoreElements()),
      this.messages.pipe(
        filter((msg) => topic === msg.topic),
        map((msg) => msg.message),
      ),
    );
  }
}
