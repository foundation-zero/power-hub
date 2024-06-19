import type { CamelCase, SnakeCase, SnakeCasedProperties } from "type-fest";
import type { PowerHubComponent } from "./power-hub";
import type BaseWater from "@/components/slides/water/BaseWater.vue";
import type { PresentationStore } from "@/stores/presentation";
import type { AjaxConfig } from "rxjs/ajax";
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

export type ComponentState = Activatable & Highlightable & Hideable & Flowable & Customizable;

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

export type StreamState = Activatable &
  Hideable &
  Muteable &
  Customizable &
  Flowable & {
    skip?: boolean;
  };

export type PipeState = {
  active?: boolean;
  muted?: boolean;
};

export type Hideable = {
  hidden?: boolean;
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

export type Customizable = {
  custom?: boolean;
};

export type Highlightable = {
  highlighted?: boolean;
};

export type PresentationComponent = typeof BaseWater;

export type PresentationAction = (store: PresentationStore) => void | Promise<void>;

export type PresentationItem =
  | PresentationAction
  | [duration: number, ...components: PresentationComponent[]];

export type QueryParams<T extends AjaxConfig["queryParams"] = AjaxConfig["queryParams"]> =
  | T
  | (() => T);

export type WeatherInfo = SnakeCasedProperties<{
  dt: string;
  humidity: number;
  pressure: number;
  temp: number;
  feelsLike: number;
  weather: {
    description: string;
    icon: string;
    main: string;
  }[];
  windSpeed: number;
  windDeg: number;
}>;

export type AppMode = "display" | "portrait" | "landscape";
