<template>
  <v-row>
    <v-col
      v-for="(vnode, index) in $slots.default?.()"
      :key="index"
      cols="12"
    >
      <component :is="vnode" />
    </v-col>
  </v-row>
</template>
