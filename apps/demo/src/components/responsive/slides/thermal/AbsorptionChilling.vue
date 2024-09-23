<template>
  <TextSlide journey="heat">
    <template #title>Absorption Chilling</template>
    <template #body>
      <p class="font-weight-bold">
        The reason we harvest heat at all is to use it to cool the compound. Of course we can't use
        the heat itself for this, but we can use the heat in an absorption chiller to cool down our
        cooling medium.
      </p>

      <p>
        An absorption chiller works by evaporating water in a vacuum, exchanging the cooling this
        provides to our cooling medium. Then a salt solution is used to condense that water vapour
        back to a liquid. Then the saline is pumped to a different chamber where the heat is used to
        boil it. This serves to separate water out of the saline. This concentrates the salt
        solution back to its original level. At the same time the water vapour from the boiling is
        condensed by cooling it down. This results in waste heat. That then condensed water is ready
        again to be evaporated, completing the cycle.
      </p>

      <p>
        The beauty of absorption chilling is how little electricity is needed: just the electricity
        to run the pumps. While we're using sunlight to harvest heat, plenty of applications will
        already have a source of heat. Usually that's treated as waste heat to be removed, but
        instead it can be used to either replace or aid a typical compression chiller.
      </p>
    </template>
  </TextSlide>
</template>

<script setup lang="ts">
import TextSlide from "../../TextSlide.vue";
</script>
