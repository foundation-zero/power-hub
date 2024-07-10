<template>
  <v-layout>
    <v-main>
      <div
        class="d-flex flex-column justify-center align-center position-relative"
        style="height: 100vh"
      >
        <LandscapeMap />
      </div>
      <ToggleWidgetsButton
        id="toggle-widgets-button"
        @click="showWidgets = true"
      />
    </v-main>
    <ContentPanel v-model="showJourneyContent">
      <JourneyContent
        v-model="showJourneyContent"
        :journey="currentJourney"
        scrollable
      />
    </ContentPanel>
    <ContentPanel v-model="showWidgets">
      <Suspense>
        <WidgetsCarousel
          v-model="showWidgets"
          scrollable
        />
      </Suspense>
    </ContentPanel>

    <IntroModal v-model="showIntro">
      <IntroContent />
    </IntroModal>
  </v-layout>
</template>

<script setup lang="ts">
import { usePresentationStore } from "@/stores/presentation";
import { toRefs, computed } from "vue";

import ContentPanel from "@/components/landscape/ContentPanel.vue";
import JourneyContent from "@/components/responsive/JourneyContent.vue";
import ToggleWidgetsButton from "@/components/responsive/ToggleWidgetsButton.vue";
import { useRouter } from "vue-router";
import WidgetsCarousel from "@/components/responsive/WidgetsCarousel.vue";
import LandscapeMap from "@/components/landscape/LandscapeMap.vue";
import IntroModal from "@/components/landscape/IntroModal.vue";
import IntroContent from "@/components/landscape/intro/IntroContent.vue";

const router = useRouter();
let lastRouteChange: number;

// We need this silly hack because the VNavigationDrawer will set modelValue to false on route change. This does not happen with VBottomSheet and VDialog.
router.beforeEach(() => {
  lastRouteChange = Date.now();
});

const { currentJourney, showWidgets } = toRefs(usePresentationStore());

const showJourneyContent = computed({
  get() {
    return !!currentJourney.value;
  },
  set(val: boolean) {
    if (!val && (!lastRouteChange || Date.now() > lastRouteChange + 100)) {
      router.push("/journeys");
    }
  },
});

const showIntro = computed({
  get() {
    return router.currentRoute.value.path === "/";
  },
  set(val: boolean) {
    if (!val) {
      router.push("/journeys");
    }
  },
});
</script>

<style scoped>
a {
  position: absolute;
  top: px;
  left: 107px;
}
</style>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: transform 750ms ease;
}

.fade-enter-from,
.fade-leave-to {
  transform: translateX(100%);
}

#toggle-widgets-button {
  position: absolute;
  right: 48px;
  bottom: 48px;
}
</style>
