<template>
  <div>
    <v-icon
      :icon="icon ?? 'fa-bell'"
      size="12"
    />
    <span class="text-subtitle-2 ml-1">{{ threshold }}</span>
    <span class="text-caption font-weight-thin ml-1"> {{ unit }}</span>
  </div>
</template>

<script setup lang="ts">
defineProps<{ threshold: number; unit: string; icon?: string }>();
</script>
