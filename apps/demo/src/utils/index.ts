import type {
  Activatable,
  Customizable,
  Flowable,
  Hideable,
  Highlightable,
  Muteable,
} from "@demo/types";

export const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export const hide = <T extends Hideable>(item: T) => (item.hidden = true);
export const show = <T extends Hideable>(item: T) => (item.hidden = false);
export const activate = <T extends Activatable>(item: T) => (item.active = true);
export const deactivate = <T extends Activatable>(item: T) => (item.active = false);
export const mute = <T extends Muteable>(item: T) => (item.muted = true);
export const unmute = <T extends Muteable>(item: T) => (item.muted = false);
export const startFlow = <T extends Flowable>(item: T) => (item.flowing = true);
export const stopFlow = <T extends Flowable>(item: T) => (item.flowing = false);
export const customize = <T extends Customizable>(item: T) => (item.custom = true);
export const decustomize = <T extends Customizable>(item: T) => (item.custom = false);
export const highlight = <T extends Highlightable>(item: T) => (item.highlighted = true);
export const dehighlight = <T extends Highlightable>(item: T) => (item.highlighted = false);
export const reset = <T extends Record<string, boolean>>(item: T) => {
  Object.entries(item).forEach(([key, val]) => {
    if (key !== "skip" && typeof val === "boolean") delete item[key];
  });
};
