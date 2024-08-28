export interface MqttBrokerAuth {
  username?: string;
  password?: string;
}

export interface MqttBrokerOptions {
  url: string;
  name?: string;
  origin?: boolean;
  target?: boolean;
  authentication?: MqttBrokerAuth;
}

export type MqttMessage = string | Buffer;
export type MqttTopicMessage = [topic: string, message: MqttMessage];
