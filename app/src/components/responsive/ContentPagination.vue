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
  width: 20px;
  height: 20px;
  border-radius: 100%;
  background-color: #d9d9d9;

  &.active {
    background-color: #a9a9a9;
  }

  &:not([data-page="1"]):before {
    content: "";
    width: 10px;
    height: 3px;
    background-color: #d9d9d9;
    left: -10px;
    top: 8.5px;
    position: absolute;
  }
}
</style>
