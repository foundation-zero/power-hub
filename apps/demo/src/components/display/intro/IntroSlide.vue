<template>
  <div>
    <svg
      width="1920"
      height="1080"
      viewBox="0 0 1920 1080"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      xmlns:xlink="http://www.w3.org/1999/xlink"
    >
      <slot />
    </svg>
  </div>
</template>

<style scoped lang="scss">
.slide-enter-active,
.slide-leave-active {
  will-change: transform;
  transition: transform 750ms ease;
}

.slide-enter-from {
  transform: translate(100%, 0);
}

.slide-leave-to {
  transform: translate(-100%, 0);
}
</style>
