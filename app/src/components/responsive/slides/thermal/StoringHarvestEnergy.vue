<template>
  <TextSlide journey="heat">
    <template #title>Storing harvested energy in the heat battery</template>
    <template #body>
      <HeatBatteryGauge
        width="100%"
        :height="undefined"
      />
      <p>
        Bacon ipsum dolor amet capicola shankle doner kielbasa chislic prosciutto bresaola bacon
        tongue ball tip fatback. Sausage ribeye ham hock spare ribs beef ribs. Alcatra jowl strip
        steak frankfurter venison. Shoulder pork chop shank ground round. Tri-tip picanha leberkas
        t-bone, hamburger alcatra ground round short loin rump. Corned beef jowl jerky, shankle
        venison hamburger tongue bresaola swine shoulder. Brisket corned beef shankle biltong
        boudin.
      </p>

      <p>
        Beef short loin fatback boudin, rump cupim salami jerky ham spare ribs drumstick short ribs
        flank kielbasa chuck. Jerky strip steak bacon, pork chop landjaeger leberkas shoulder beef
        beef ribs burgdoggen. Rump fatback t-bone cow sausage filet mignon brisket buffalo hamburger
        shankle. Ribeye pork pancetta, boudin kevin flank landjaeger short ribs chicken capicola
        doner t-bone rump. Tongue kielbasa strip steak hamburger, biltong swine ham porchetta turkey
        jerky pork belly beef ribs kevin. Prosciutto shankle drumstick chislic.
      </p>

      <p>
        Buffalo pork chop meatloaf beef rump. Shankle andouille jowl short ribs, kevin biltong pig
        pancetta fatback beef bresaola porchetta. Kielbasa fatback doner tri-tip short loin cupim,
        picanha beef pork belly shankle strip steak biltong. Salami tri-tip shank landjaeger.
        Brisket ground round leberkas t-bone, turkey frankfurter doner. Beef ribs ground round ham
        hock shankle beef pork. Sausage biltong pancetta flank kevin ground round, fatback meatball
        chuck.
      </p>

      <p>
        Turducken t-bone ribeye pig strip steak pork chop chicken picanha. Turkey shank chicken
        biltong picanha meatloaf salami. Salami burgdoggen beef drumstick biltong alcatra doner
        sirloin strip steak meatball t-bone chicken boudin cupim fatback. Pork belly short loin
        alcatra bresaola tail ball tip.
      </p>

      <p>
        Jowl chislic cupim pork belly filet mignon shank. Cupim filet mignon jerky pig sausage short
        ribs short loin ham venison. Chuck short loin filet mignon chislic. Chislic spare ribs
        burgdoggen ground round t-bone pancetta strip steak pork, bresaola meatball tenderloin.
        Kevin porchetta shankle pancetta bacon chislic t-bone picanha andouille spare ribs drumstick
        jerky landjaeger short ribs.
      </p>
    </template>
  </TextSlide>
</template>

<script setup lang="ts">
import HeatBatteryGauge from "@/components/gauges/BatteryGauge.vue";
import TextSlide from "../../TextSlide.vue";
</script>
