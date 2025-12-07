<template>
  <CreateFramework :sendPushNotification="sendPushNotification" />
</template>

<script>
import {  API_ENDPOINTS } from '../../config/api.js'

import CreateFramework from './CreateFramework.vue'

export default {
  name: 'FrameworkWrapper',
  components: {
    CreateFramework
  },
  setup() {
    const sendPushNotification = async (notificationData) => {
      try {
        const response = await fetch(API_ENDPOINTS.PUSH_NOTIFICATION, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(notificationData)
        });
        if (response.ok) {
          console.log('Push notification sent successfully');
        } else {
          console.error('Failed to send push notification');
        }
      } catch (error) {
        console.error('Error sending push notification:', error);
      }
    }

    return {
      sendPushNotification
    }
  }
}
</script> 