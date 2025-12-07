/**
 * Event Service - Centralized Data Management
 * 
 * This service handles:
 * 1. Fetching all event-related data on login
 * 2. Caching data in memory for instant access
 * 3. Providing cached data to components
 */

import { axiosInstance } from '@/config/api.js';
import { API_ENDPOINTS } from '@/config/api.js';

class EventService {
  constructor() {
    // Centralized data store
    this.dataStore = {
      events: [],
      integrationEvents: [], // NEW: Store integration events separately
      lastFetchTime: null,
      isFetching: false,
      fetchError: null
    };
  }

  /**
   * Fetch all event data and cache it
   */
  async fetchAllEventData() {
    if (this.dataStore.isFetching) {
      console.log('[Event Service] Already fetching, skipping duplicate request');
      return this.dataStore;
    }

    this.dataStore.isFetching = true;
    console.log('[Event Service] 🚀 Starting event data prefetch...');

    try {
      // Fetch all event-related datasets in parallel
      await Promise.all([
        this.fetchEvents(),
        this.fetchIntegrationEvents() // NEW: Also fetch integration events
      ]);

      this.dataStore.lastFetchTime = new Date();
      this.dataStore.fetchError = null;
      
      console.log(`[Event Service] ✅ Prefetch complete - Total events: ${this.dataStore.events.length}, Integration events: ${this.dataStore.integrationEvents.length}`);
      
      return this.dataStore;
    } catch (error) {
      console.error('[Event Service] ❌ Prefetch failed:', error);
      this.dataStore.fetchError = error.message;
      throw error;
    } finally {
      this.dataStore.isFetching = false;
    }
  }

  /**
   * Fetch events from API
   */
  async fetchEvents() {
    try {
      const response = await axiosInstance.get(API_ENDPOINTS.EVENTS_LIST, {
        timeout: 60000
      });

      // Handle both old and new response formats
      if (response.data.success && response.data.events) {
        this.dataStore.events = response.data.events;
      } else if (Array.isArray(response.data)) {
        this.dataStore.events = response.data;
      } else {
        this.dataStore.events = [];
      }

      console.log(`[Event Service] Fetched ${this.dataStore.events.length} events`);
    } catch (error) {
      console.error('[Event Service] Error fetching events:', error);
      this.dataStore.events = [];
      throw error;
    }
  }

  /**
   * Fetch integration events from API (Jira, etc.)
   */
  async fetchIntegrationEvents() {
    try {
      const response = await axiosInstance.get('api/events/integration-events/', {
        timeout: 60000
      });

      // Handle both old and new response formats
      if (response.data.success && response.data.events) {
        this.dataStore.integrationEvents = response.data.events;
      } else if (Array.isArray(response.data)) {
        this.dataStore.integrationEvents = response.data;
      } else {
        this.dataStore.integrationEvents = [];
      }

      console.log(`[Event Service] Fetched ${this.dataStore.integrationEvents.length} integration events`);
    } catch (error) {
      console.error('[Event Service] Error fetching integration events:', error);
      this.dataStore.integrationEvents = [];
      // Don't throw - allow the rest of the prefetch to continue
    }
  }

  /**
   * Get cached data
   * @param {string} key - The data key to retrieve
   * @returns {any} The cached data
   */
  getData(key) {
    return this.dataStore[key];
  }

  /**
   * Set cached data
   * @param {string} key - The data key to set
   * @param {any} value - The value to set
   */
  setData(key, value) {
    if (Object.prototype.hasOwnProperty.call(this.dataStore, key)) {
      this.dataStore[key] = value;
      if (key !== 'lastFetchTime' && key !== 'isFetching' && key !== 'fetchError') {
        this.dataStore.lastFetchTime = new Date();
      }
    }
  }

  /**
   * Check if data is cached and fresh
   * @returns {boolean}
   */
  hasValidCache() {
    return this.dataStore.events.length > 0 && this.dataStore.lastFetchTime !== null;
  }

  /**
   * Check if integration events are cached
   * @returns {boolean}
   */
  hasIntegrationEventsCache() {
    return this.dataStore.integrationEvents.length > 0 && this.dataStore.lastFetchTime !== null;
  }

  /**
   * Clear all cached data
   */
  clearCache() {
    this.dataStore.events = [];
    this.dataStore.integrationEvents = []; // NEW: Clear integration events too
    this.dataStore.lastFetchTime = null;
    this.dataStore.fetchError = null;
    console.log('[Event Service] Cache cleared');
  }

  /**
   * Get cache statistics
   */
  getCacheStats() {
    return {
      eventsCount: this.dataStore.events.length,
      integrationEventsCount: this.dataStore.integrationEvents.length, // NEW
      lastFetchTime: this.dataStore.lastFetchTime,
      isFetching: this.dataStore.isFetching,
      hasError: !!this.dataStore.fetchError
    };
  }

  /**
   * Add a new event to the cache
   * @param {object} event - The event to add
   */
  addEvent(event) {
    this.dataStore.events.push(event);
    this.dataStore.lastFetchTime = new Date();
  }

  /**
   * Update an event in the cache
   * @param {string} eventId - The ID of the event to update
   * @param {object} updatedEvent - The updated event data
   */
  updateEvent(eventId, updatedEvent) {
    const index = this.dataStore.events.findIndex(e => e.id === eventId);
    if (index !== -1) {
      this.dataStore.events[index] = { ...this.dataStore.events[index], ...updatedEvent };
      this.dataStore.lastFetchTime = new Date();
    }
  }

  /**
   * Remove an event from the cache
   * @param {string} eventId - The ID of the event to remove
   */
  removeEvent(eventId) {
    this.dataStore.events = this.dataStore.events.filter(e => e.id !== eventId);
    this.dataStore.lastFetchTime = new Date();
  }
}

// Export singleton instance
const eventDataService = new EventService();
export default eventDataService;

