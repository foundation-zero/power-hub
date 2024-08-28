declare global {
  namespace NodeJS {
    interface ProcessEnv {
      ORIGIN_URL: string;
      ORIGIN_USERNAME: string;
      ORIGIN_PASSWORD: string;
      ORIGIN_NAME: string;
      TARGET_URL: string;
      TARGET_USERNAME: string;
      TARGET_PASSWORD: string;
      TARGET_NAME: string;
      SUBSCRIBE_TO: string;
    }
  }
}

// If this file has no import/export statements (i.e. is a script)
// convert it into a module by adding an empty export statement.
export {};
