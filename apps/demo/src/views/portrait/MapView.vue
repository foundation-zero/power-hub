<template>
  <v-layout @touchmove.stop.prevent>
    <AppBar />

    <v-main>
      <div
        class="d-flex flex-column justify-end align-center pt-5 px-3"
        style="height: calc(100vh - 64px)"
      >
        <PortraitMap />
      </div>

      <ToggleWidgetsButton
        id="toggle-widgets-button"
        width="61"
        height="61"
        @click="showWidgets = true"
      />
    </v-main>

    <component
      :is="portraitContentWrapper"
      v-model="showJourneyContent"
    >
      <JourneyContent
        v-model="showJourneyContent"
        class="py-5"
        :class="{ 'px-15': $vuetify.display.mdAndUp, 'px-8': $vuetify.display.smAndDown }"
        scrollable
        :journey="currentJourney"
      />
    </component>

    <component
      :is="portraitContentWrapper"
      v-model="showWidgets"
    >
      <Suspense>
        <WidgetsCarousel
          v-model="showWidgets"
          class="py-5"
          :class="{ 'px-15': $vuetify.display.mdAndUp, 'px-8': $vuetify.display.smAndDown }"
          scrollable
        />
      </Suspense>
    </component>

    <IntroPanel v-model="showIntro">
      <component
        :is="portraitIntro"
        v-model="showIntro"
      />
    </IntroPanel>
  </v-layout>
</template>

<script setup lang="ts">
import { usePresentationStore } from "@demo/stores/presentation";
import { toRefs } from "vue";
import AppBar from "@demo/components/portrait/AppBar.vue";
import JourneyContent from "@demo/components/responsive/JourneyContent.vue";
import { computed } from "vue";
import ToggleWidgetsButton from "@demo/components/responsive/ToggleWidgetsButton.vue";
import { useRouter } from "vue-router";
import WidgetsCarousel from "@demo/components/responsive/WidgetsCarousel.vue";
import { portraitContentWrapper, portraitIntro } from "@demo/utils/display";
import PortraitMap from "@demo/components/portrait/PortraitMap.vue";
import IntroPanel from "@demo/components/portrait/IntroPanel.vue";

const { currentJourney, showWidgets } = toRefs(usePresentationStore());
const router = useRouter();

const showJourneyContent = computed({
  get() {
    return !!currentJourney.value;
  },
  set(val: boolean) {
    if (!val) {
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
  bottom: 20px;
  right: 20px;
}
</style>
