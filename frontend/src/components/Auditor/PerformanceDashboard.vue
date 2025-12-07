<template>
  <div class="performance-dashboard-container">
    <!-- Empty Performance Dashboard page -->
  </div>
</template>

<script>
import { AccessUtils } from '@/utils/accessUtils';

export default {
  name: 'PerformanceDashboard',
  data() {
    return {
      // Empty data
    }
  },
  methods: {
    // Method to check analytics permission
    checkAnalyticsPermission() {
      AccessUtils.showAuditPerformanceAnalyticsDenied();
    }
  },
  mounted() {
    // Add any future API calls here with access denied checks
    // For example:
    // try {
    //   const response = await api.getAnalyticsData();
    // } catch (error) {
    //   if (AccessUtils.handleApiError(error, 'audit analytics access')) {
    //     return;
    //   }
    // }
  }
}
</script>

<style scoped>
.performance-dashboard-container {
  margin-left: 180px;
  padding: 32px 24px 24px 24px;
  background: #f8f9fb;
  min-height: 100vh;
  font-family: 'Gill Sans', 'Gill Sans MT', Calibri, 'Trebuchet MS', sans-serif;
}
</style> 