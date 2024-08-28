declare global {
  namespace NodeJS {
    interface ProcessEnv {
      CONNECTION_TIMEOUT_SECONDS: string;
      MAX_QUEUE_SIZE: string;
      TARGET_CA_FILE: string;
      ORIGIN_URL: string;
      ORIGIN_USERNAME: string;
      ORIGIN_PASSWORD: string;
      ORIGIN_NAME: string;
      ORIGIN_KEEPALIVE: string;
      TARGET_URL: string;
      TARGET_NAME: string;
      TARGET_KEEPALIVE: string;
      TARGET_PROTOCOL: string;
      TARGET_USERNAME: string;
      TARGET_PASSWORD: string;
      SUBSCRIBE_TO: string;
      PUBLISH_INTERVAL_SECONDS: string;
      PUBLISH_TIMEOUT_SECONDS: string;
    }
  }
}

// If this file has no import/export statements (i.e. is a script)
// convert it into a module by adding an empty export statement.
export {};
