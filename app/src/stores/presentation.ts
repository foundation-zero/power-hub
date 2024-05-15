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

export const SLIDE_DURATION_IN_MS = 7000;

const numberOfSlides: Record<Journey, number> = {
  heat: 1,
  electrical: 1,
  water: 1,
};

const componentStateFn = (component: PowerHubComponent): ComponentElement => ({
  component,
  state: { active: true },
  position: { x: 0, y: 0 },
});

const streamStateFn = (): StreamState => ({});
const createStreams = (amountOfStreams: number) =>
  new Array(amountOfStreams).fill(null).map(streamStateFn);

export const usePresentationStore = defineStore("presentation", () => {
  const slides = ref<string[]>([]);
  const isRunning = ref(false);

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

    for (let slide = 0; slide < numberOfSlides[journey]; slide++) {
      if (!isRunning.value) break;

      slides.value = [`/slides/${journey}/${slide + 1}.svg`];
      await sleep(SLIDE_DURATION_IN_MS);
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

  return {
    startSlideShow,
    slides,
    isRunning,
    stopSlideShow,
    components,
    componentStates,
    journeys,
    streamStates,
    pipes,
    root,
    getFlow,
    getComponent,
    getComponentState,
    getPosition,
    setPosition,
  };
});
