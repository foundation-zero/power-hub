import type {
  ComponentElement,
  ComponentState,
  Journey,
  JourneyFlow,
  JourneyFlowWithState,
  PipeState,
  PresentationComponent,
  StreamState,
} from "@/types";
import type { PowerHubComponent } from "@/types/power-hub";
import { mapFn, useSleep } from "@/utils";
import { type Position } from "@vueuse/core";
import { defineStore } from "pinia";
import { computed, ref } from "vue";

import journeyItems from "./slides";
import { isFunction } from "rxjs/internal/util/isFunction";

const componentStateFn = (component: PowerHubComponent): ComponentElement => ({
  component,
  state: { active: true },
  position: { x: 0, y: 0 },
});

const streamStateFn = (): StreamState => ({});
const createStreams = (amountOfStreams: number) =>
  new Array(amountOfStreams).fill(null).map(streamStateFn);

export const usePresentationStore = defineStore("presentation", () => {
  const slides = ref<PresentationComponent[]>([]);
  const isRunning = ref(false);
  const showWidgets = ref(false);
  const showWaves = ref(true);
  const currentJourney = ref<Journey>("electrical");

  const root = ref<SVGSVGElement>();

  const components = ref<ComponentElement[]>(
    mapFn(
      componentStateFn,
      "absorption-chiller",
      "compression-chiller",
      "cooling-demand",
      "heat-storage",
      "heat-tubes",
      "power-battery",
      "sea-water",
      "solar-panels",
      "sun",
      "system-demand",
      "water-demand",
      "water-maker",
      "water-storage",
      "water-treatment",
    ),
  );

  const pipes = ref<PipeState>({
    active: true,
  });

  const journeys = ref<Record<Journey, JourneyFlow>>({
    heat: {
      streams: createStreams(5),
      components: [
        "sun",
        "heat-tubes",
        "heat-storage",
        "absorption-chiller",
        "compression-chiller",
        "cooling-demand",
      ],
    },
    water: {
      streams: createStreams(5),
      components: [
        "sea-water",
        "water-maker",
        "water-storage",
        "water-demand",
        "water-treatment",
        "water-storage",
      ],
    },
    electrical: {
      streams: createStreams(3),
      components: ["sun", "solar-panels", "power-battery", "system-demand"],
    },
  });

  const sleep = useSleep(isRunning);

  const run = async () => {
    if (!isRunning.value) return;

    try {
      for (const item of journeyItems) {
        if (isFunction(item)) {
          await item(usePresentationStore());
        } else {
          const [duration, ...components] = item;
          slides.value = components;

          await sleep(duration);
        }
      }

      slides.value = [];
      setTimeout(run);
    } catch (e) {
      if (e !== "aborted") {
        console.log(e);
        isRunning.value = false;
      }
    }
  };

  const start = async () => {
    isRunning.value = true;
    run();
  };

  const stop = () => {
    isRunning.value = false;
    slides.value = [];
  };

  const getPosition = (component: PowerHubComponent): Position => getComponent(component).position;

  const setPosition = (component: PowerHubComponent, position: Position) => {
    getComponent(component).position = position;
  };

  const getComponent = (component: PowerHubComponent): ComponentElement =>
    components.value.find((el) => el.component === component)!;

  const getComponentState = (component: PowerHubComponent): ComponentState =>
    getComponent(component).state;

  const componentStates = computed(() => components.value.map((component) => component.state));
  const streamStates = computed(() => [
    ...journeys.value.heat.streams,
    ...journeys.value.electrical.streams,
    ...journeys.value.water.streams,
  ]);

  const getFlow = (journey: Journey): JourneyFlowWithState => {
    const { components, streams } = journeys.value[journey];

    return { streams, components: components.map(getComponentState) };
  };

  const setJourney = (journey: Journey) => {
    currentJourney.value = journey;
  };

  return {
    start,
    slides,
    isRunning,
    stop,
    components,
    currentJourney,
    componentStates,
    journeys,
    streamStates,
    pipes,
    root,
    showWidgets,
    showWaves,
    setJourney,
    getFlow,
    getComponent,
    getComponentState,
    getPosition,
    setPosition,
    sleep,
  };
});

export type PresentationStore = ReturnType<typeof usePresentationStore>;
