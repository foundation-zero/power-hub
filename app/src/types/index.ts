import type { CamelCase, SnakeCase } from "type-fest";
import type { PowerHubComponent } from "./power-hub";
export * as PowerHub from "./power-hub";

//@see https://stackoverflow.com/questions/58434389/typescript-deep-keyof-of-a-nested-object/76131375#76131375
export type NestedPath<T> = T extends object
  ? {
      [K in keyof T & (string | number)]: K extends string
        ?
            | (T[K] extends string | number | null | Array<unknown> ? SnakeCase<`${K}`> : never)
            | `${SnakeCase<K>}/${NestedPath<T[K]>}`
        : never;
    }[keyof T & (string | number)]
  : never;

export type PathValue<T, P extends NestedPath<T>> = P extends `${infer Key}/${infer Rest}`
  ? CamelCase<Key> extends keyof T
    ? Rest extends NestedPath<T[CamelCase<Key>]>
      ? PathValue<T[CamelCase<Key>], Rest>
      : never
    : never
  : P extends keyof T
    ? T[P]
    : never;

export type HistoricalData<T extends string | Date = string, V = string | number> = {
  time: T;
  value: V;
};

export type Journey = "electrical" | "heat" | "water";

export type ComponentState = {
  active?: boolean;
  muted?: boolean;
  highlighted?: boolean;
};

export type ComponentElement = {
  component: PowerHubComponent;
  state: ComponentState;
  position: {
    x: number;
    y: number;
  };
};

export type JourneyFlow = {
  components: PowerHubComponent[];
  streams: StreamState[];
};

export type JourneyFlowWithState = {
  components: ComponentState[];
  streams: StreamState[];
};

export type StreamState = {
  active?: boolean;
  muted?: boolean;
  flowing?: boolean;
};

export type PipeState = {
  active?: boolean;
};

export type Activatable = {
  active?: boolean;
};

export type Muteable = {
  muted?: boolean;
};

export type Flowable = {
  flowing?: boolean;
};
