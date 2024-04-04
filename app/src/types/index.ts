import type { CamelCase, SnakeCase } from "type-fest";
import type { Ref } from "vue";
export * as PowerHub from "./power-hub";

export type DataTableRow = [
  key: string,
  value: string | number | undefined | Ref<string | number | undefined>,
];

export interface DataTable {
  name: string;
  rows: DataTableRow[];
}

export type TopicCache<T> = {
  [K in NestedPath<T>]?: RORef<PathValue<T, K> | undefined>;
};

export type RORef<T> = Readonly<Ref<T>>;

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
