import "dotenv/config";
import { MqttBridge } from "./src/bridge.mjs";

const bridge = new MqttBridge();

bridge
  .add({
    url: process.env.ORIGIN_URL!,
    authentication: {
      username: process.env.ORIGIN_USERNAME,
      password: process.env.ORIGIN_PASSWORD,
    },
    origin: true,
    name: process.env.ORIGIN_NAME,
  })
  .add({
    url: process.env.TARGET_URL!,
    authentication: {
      username: process.env.TARGET_USERNAME,
      password: process.env.TARGET_PASSWORD,
    },
    target: true,
    name: process.env.TARGET_NAME,
  })
  .subscribe(process.env.SUBSCRIBE_TO)
  .start();
