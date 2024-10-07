import { IPublishPacket, MqttProtocol } from "mqtt";

export interface MqttBrokerAuth {
  username?: string;
  password?: string;
}

export interface MqttBrokerOptions {
  url: string;
  name?: string;
  authentication?: MqttBrokerAuth;
  subscribeTopics?: string[];
  keepalive: number;
  ca?: Buffer;
  protocol: MqttProtocol;
}

export type MqttMessage = string | Buffer;
export type MqttTopicMessage = [topic: string, message: MqttMessage, packet?: IPublishPacket];

export interface MqttBridgeOptions {
  connectionTimeoutSeconds: number;
  maxQueueSize: number;
  publishIntervalSeconds: number;
  publishTimeoutSeconds: number;
  subscribeTimeoutSeconds: number;
}
