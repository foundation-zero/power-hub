<template>
  <TextSlide journey="electrical">
    <template #title>Powered by the sun</template>
    <template #body>
      <p>
        We have 200 m² of photo-voltaic solar panels capable of delivering 40 kW in ideal
        conditions. That's enough to run 80 washing machines at the same time. However this varies
        throughout the day and seasons. In ideal conditions the sun is pointed straight at the solar
        panels, but as the sun transitions from east to west and from the horizon to higher in the
        sky the energy it supplies will change.
        <span class="text-decoration-line-through"
          >Efforts to convince the sun to stay at a fixed point in the sky have so far proved
          unsuccessful.</span
        >
      </p>

      <p>
        The physical principle by which solar panels convert light to electricty is the same the
        principle used by LEDs to convert electricity to light. Electricity is formed by electron
        moving along a conductor. By mixing the materials that conductor is made from, we can create
        a gap for the electron to jump across. Then when a wave of light hits the electron just
        right, it can yeet it across the gap and send it on its way.
      </p>
    </template>
  </TextSlide>
</template>

<script setup lang="ts">
import TextSlide from "../../TextSlide.vue";
</script>
