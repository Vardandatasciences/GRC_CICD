<template>
  <div class="min-h-screen event-handling-layout">
    <!-- Main Content - Account for sidebar -->
    <main class="w-full m-0 p-0">
      <router-view />
    </main>
  </div>
</template>

<script>
export default {
  name: 'EventHandlingLayout'
}
</script>

<style scoped>
.event-handling-layout {
  padding-left: 280px; /* Account for main sidebar width */
  min-height: 100vh;
  box-sizing: border-box;
}
</style>
