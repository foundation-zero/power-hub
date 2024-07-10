<template>
  <TextSlide journey="water">
    <template #title>Treating water</template>
    <template #body>
      <p class="font-weight-bold">
        Because making water is such an energy intensive process, it can be very worthwhile to
        recycle water. Plenty of water we dump into the sewer could very well be used to flush a
        toilet or to wash down the boat.
      </p>
      <p>
        To do this we collect the usable waste water. Then that water is treated. An important part
        of the treatment is to force the tiny particles in the water out of suspension. Often this
        is done by adding chemicals, while effective this requires that chemicals to be refilled
        from time to time.
      </p>

      <p>
        Our water treatment in contrast uses electricity to statically charge the particles. Since
        different charges attract, this then lets the particles clump up to larger particles until
        their size is too large to hold then in suspension.
      </p></template
    >
  </TextSlide>
</template>

<script setup lang="ts">
import TextSlide from "../../TextSlide.vue";
</script>
