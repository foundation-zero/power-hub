<template>
  <v-layout>
    <v-main>
      <div
        class="d-flex flex-column justify-center align-center position-relative"
        style="height: 100vh"
      >
        <LandscapeMap ref="map" />
        <div
          :style="{ width: `${width}px`, top: 0 }"
          class="position-absolute"
        >
          <RouterLink
            id="intro-button"
            to="/"
            xmlns="http://www.w3.org/1999/xhtml"
          >
            <FZLogo />
          </RouterLink>

          <a
            id="home-button"
            href="https://www.foundationzero.org/insights/power-hub"
            target="_self"
          >
            <HomeIcon />
          </a>
        </div>
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
import { usePresentationStore } from "@demo/stores/presentation";
import { toRefs, computed, ref, onMounted } from "vue";

import ContentPanel from "@demo/components/landscape/ContentPanel.vue";
import JourneyContent from "@demo/components/responsive/JourneyContent.vue";
import ToggleWidgetsButton from "@demo/components/responsive/ToggleWidgetsButton.vue";
import { RouterLink, useRouter } from "vue-router";
import WidgetsCarousel from "@demo/components/responsive/WidgetsCarousel.vue";
import LandscapeMap from "@demo/components/landscape/LandscapeMap.vue";
import IntroModal from "@demo/components/landscape/IntroModal.vue";
import IntroContent from "@demo/components/landscape/intro/IntroContent.vue";
import FZLogo from "@demo/components/FZLogo.vue";
import HomeIcon from "@demo/components/responsive/HomeIcon.vue";

const router = useRouter();
let lastRouteChange: number;

// We need this silly hack because the VNavigationDrawer will set modelValue to false on route change. This does not happen with VBottomSheet and VDialog.
router.beforeEach(() => {
  lastRouteChange = Date.now();
});

const map = ref<InstanceType<typeof LandscapeMap>>();
const width = ref(0);

const setWidth = () =>
  (width.value = (map.value?.$el as SVGElement)?.getBoundingClientRect().width ?? 0);

onMounted(() => setTimeout(setWidth));
window.addEventListener("resize", setWidth);

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
.v-card {
  padding: 56px;
}

#intro-button,
#home-button {
  position: absolute;
  top: 70px;
}

#intro-button {
  left: 90px;
}

#home-button {
  right: 90px;
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
