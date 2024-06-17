/// <reference types="vite/client" />

export interface ImportMetaEnv {
  readonly VITE_MQTT: string;
  readonly VITE_MQTT_USER: string;
  readonly VITE_MQTT_PASSWORD: string;
  readonly VITE_API: string;
  readonly VITE_API_TARGET: string;
  readonly VITE_API_BEARER_TOKEN: string;
}

export interface ImportMeta {
  readonly env: ImportMetaEnv;
}
