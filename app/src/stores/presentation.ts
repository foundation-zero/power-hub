import type {
  ComponentElement,
  ComponentState,
  Journey,
  JourneyFlow,
  JourneyFlowWithState,
  PipeState,
  StreamState,
} from "@/types";
import type { PowerHubComponent } from "@/types/power-hub";
import { mapFn, sleep } from "@/utils";
import type { Position } from "@vueuse/core";
import { defineStore } from "pinia";
import { computed, ref } from "vue";

import Base from "@/components/slides/water/BaseWater.vue";
import slidesWater from "./slides/water";
import slidesElectrical from "./slides/electrical";

const componentStateFn = (component: PowerHubComponent): ComponentElement => ({
  component,
  state: { active: true },
  position: { x: 0, y: 0 },
});

const streamStateFn = (): StreamState => ({});
const createStreams = (amountOfStreams: number) =>
  new Array(amountOfStreams).fill(null).map(streamStateFn);

const journeyComponents: Record<Journey, [duration: number, ...slides: (typeof Base)[]][]> = {
  electrical: slidesElectrical,
  heat: [],
  water: slidesWater,
};

export const usePresentationStore = defineStore("presentation", () => {
  const slides = ref<(typeof Base)[]>([]);
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

  const startSlideShow = async (journey: Journey) => {
    isRunning.value = true;

    for (const [duration, ...currentSlides] of journeyComponents[journey]) {
      if (!isRunning.value) break;

      slides.value = currentSlides;

      await sleep(duration);
      slides.value = [];
    }

    await sleep(750);
    isRunning.value = false;
  };

  const stopSlideShow = () => {
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
    startSlideShow,
    slides,
    isRunning,
    stopSlideShow,
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
  };
});
