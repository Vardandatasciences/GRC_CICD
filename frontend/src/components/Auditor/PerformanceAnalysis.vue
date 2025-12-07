<template>
  <div class="performance-analysis-container">
    <router-view></router-view>
  </div>
</template>

<script>
import { AccessUtils } from '@/utils/accessUtils';

export default {
  name: 'PerformanceAnalysis',
  methods: {
    // Method to check performance analytics permission
    checkPerformanceAnalyticsPermission() {
      AccessUtils.showAuditPerformanceAnalyticsDenied();
    }
  },
  mounted() {
    // Add any future API calls here with access denied checks
    // For example:
    // try {
    //   const response = await api.getPerformanceAnalytics();
    // } catch (error) {
    //   if (AccessUtils.handleApiError(error, 'audit performance analytics access')) {
    //     return;
    //   }
    // }
  }
}
</script>

<style scoped>
.performance-analysis-container {
  width: 100%;
  height: 100%;
}
</style> 