// Simple Event Bus for global events
class EventBus {
    constructor() {
        this.events = {}
    }

    on(event, callback) {
        if (!this.events[event]) {
            this.events[event] = []
        }
        this.events[event].push(callback)
    }

    off(event, callback) {
        if (!this.events[event]) return
        this.events[event] = this.events[event].filter(cb => cb !== callback)
    }

    emit(event, data) {
        if (!this.events[event]) return
        this.events[event].forEach(callback => {
            try {
                callback(data)
            } catch (error) {
                console.error('EventBus callback error:', error)
            }
        })
    }

    // Clear all events
    clear() {
        this.events = {}
    }
}

// Create singleton instance
const eventBus = new EventBus()

// Global logout event
export const LOGOUT_EVENT = 'user_logout'
export const LOGIN_EVENT = 'user_login'

export default eventBus
