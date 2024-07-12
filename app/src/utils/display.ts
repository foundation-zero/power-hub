import vuetify from "@/plugins/vuetify";
import { computed, defineAsyncComponent } from "vue";

const { width, height } = vuetify.display;

const ContentModal = defineAsyncComponent(
  async () => await import("@/components/portrait/ContentModal.vue"),
);

const ContentPanel = defineAsyncComponent(
  async () => await import("@/components/portrait/ContentPanel.vue"),
);

const TabletIntroContent = defineAsyncComponent(
  async () => await import("@/components/portrait/tablet/intro/IntroContent.vue"),
);

const PhoneIntroContent = defineAsyncComponent(
  async () => await import("@/components/portrait/phone/intro/IntroContent.vue"),
);

export const isLargeScreen = computed(() => width.value > 600 && height.value > 800);
export const portraitContentWrapper = computed(() =>
  isLargeScreen.value ? ContentModal : ContentPanel,
);

export const portraitIntro = computed(() =>
  isLargeScreen.value ? TabletIntroContent : PhoneIntroContent,
);
