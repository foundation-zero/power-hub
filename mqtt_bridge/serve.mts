import "dotenv/config";
import { MqttBridge } from "./src/bridge.mjs";
import { readFileSync } from "node:fs";
import { MqttProtocol } from "mqtt";

const bridge = new MqttBridge({
  connectionTimeoutSeconds: parseInt(process.env.CONNECTION_TIMEOUT_SECONDS ?? "30"),
  maxQueueSize: parseInt(process.env.MAX_QUEUE_SIZE ?? "120"),
  publishIntervalSeconds: parseInt(process.env.PUBLISH_INTERVAL_SECONDS ?? "5"),
  publishTimeoutSeconds: parseInt(process.env.PUBLISH_TIMEOUT_SECONDS ?? "60"),
  subscribeTimeoutSeconds: parseInt(process.env.SUBSCRIBE_TIMEOUT_SECONDS ?? "60"),
});

const readCaFile = (file: string | undefined) => {
  if (file) {
    return readFileSync(file);
  }
  return undefined;
};

bridge
  .addOrigin({
    url: process.env.ORIGIN_URL!,
    authentication: {
      username: process.env.ORIGIN_USERNAME,
      password: process.env.ORIGIN_PASSWORD,
    },
    subscribeTopics: process.env.SUBSCRIBE_TO.split(","),
    name: process.env.ORIGIN_NAME,
    keepalive: parseInt(process.env.ORIGIN_KEEPALIVE ?? "30"),
    ca: readCaFile(process.env.ORIGIN_CA_FILE),
    protocol: (process.env.ORIGIN_PROTOCOL ?? "mqtt") as MqttProtocol,
  })
  .addTarget({
    url: process.env.TARGET_URL!,
    authentication: {
      username: process.env.TARGET_USERNAME,
      password: process.env.TARGET_PASSWORD,
    },
    name: process.env.TARGET_NAME,
    keepalive: parseInt(process.env.TARGET_KEEPALIVE ?? "30"),
    protocol: (process.env.TARGET_PROTOCOL ?? "mqtt") as MqttProtocol,
  })
  .start();
