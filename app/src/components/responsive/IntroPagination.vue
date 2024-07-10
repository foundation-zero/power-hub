<template>
  <v-pagination
    v-model="currentPage"
    :length="amountOfPages"
  >
    <template #item="{ isActive, page }">
      <span
        :class="{ active: isActive }"
        :data-page="page"
        class="cursor-pointer"
        @click="currentPage = Number(page)"
      ></span>
    </template>
    <template #prev></template>
    <template #next></template>
  </v-pagination>
</template>

<script setup lang="ts">
const currentPage = defineModel<number>();

defineProps<{ amountOfPages: number }>();
</script>

<style scoped lang="scss">
span {
  position: relative;
  display: inline-flex;
  width: 14px;
  height: 14px;
  border-radius: 100%;
  background-color: #fff;

  &.active {
    background-color: #000;
  }
}
</style>
