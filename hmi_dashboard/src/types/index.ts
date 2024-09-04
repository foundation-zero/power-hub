import type { CamelCase, SnakeCase, SnakeCasedProperties } from "type-fest";
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

export type HourlyData<V extends string | number = number> = {
  hour: number;
  value: V;
};

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

export type Direction = "up" | "down" | "left" | "right";
