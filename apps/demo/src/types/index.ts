import type { SnakeCasedProperties } from "type-fest";
import type BaseWater from "@demo/components/display/intro/WelcomeToThePowerHub.vue";
import type { PresentationStore } from "@demo/stores/presentation";
import type { AjaxConfig } from "rxjs/ajax";
import type { PowerHubComponent } from "@shared/types";

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
export type Direction = "up" | "down" | "left" | "right";
export type MaybeCustomPath<T extends string> = T | `custom:${string}`;
