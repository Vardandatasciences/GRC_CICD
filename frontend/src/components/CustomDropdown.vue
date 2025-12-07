<template>
  <div class="dropdown-container">
    <button class="filter-btn" @click="toggleDropdown">
      <PhCalendar v-if="showCalendarIcon" :size="16" />
      <span class="text-content">
        <span class="dropdown-label">{{ config.label || config.name }}: </span>
        <span class="dropdown-value">{{ selectedLabel }}</span>
      </span>
      <PhCaretDown :size="16" />
    </button>
    <div v-if="isOpen" class="dropdown-menu">
      <input
        v-if="showSearchBar"
        v-model="searchQuery"
        type="text"
        class="dropdown-search"
        placeholder="Search..."
        @click.stop
      />
      <div 
        v-for="option in filteredOptions" 
        :key="option.value"
        class="dropdown-item"
        @click="selectOption(option)"
      >
        {{ option.label }}
      </div>
      <div v-if="filteredOptions.length === 0" class="dropdown-no-results">
        No results found
      </div>
    </div>
  </div>
</template>

<script>
import { PhCalendar, PhCaretDown } from '@phosphor-icons/vue';

export default {
  name: 'CustomDropdown',
  components: {
    PhCalendar,
    PhCaretDown
  },
  props: {
    config: {
      type: Object,
      required: true
    },
    modelValue: {
      type: String,
      default: ''
    },
    showSearchBar: {
      type: Boolean,
      default: true
    }
  },
  data() {
    return {
      isOpen: false,
      searchQuery: ''
    }
  },
  computed: {
    selectedLabel() {
      const options = this.config.values || this.config.options || [];
      const selectedOption = options.find(option => option.value === this.modelValue);
      if (selectedOption) {
        return selectedOption.label;
      }
      return this.config.defaultValue || this.config.defaultLabel || 'Select...';
    },
    showCalendarIcon() {
      return (this.config.label || this.config.name) === 'Due Date';
    },
    filteredOptions() {
      const options = this.config.values || this.config.options || [];
      if (!this.searchQuery) return options;
      const query = this.searchQuery.toLowerCase();
      return options.filter(option =>
        option.label && option.label.toLowerCase().includes(query)
      );
    }
  },
  mounted() {
    // Add event listener for clicking outside
    document.addEventListener('click', this.closeDropdown);
  },
  // eslint-disable-next-line vue/no-deprecated-destroyed-lifecycle
  beforeDestroy() {
    // Remove event listener
    document.removeEventListener('click', this.closeDropdown);
  },
  methods: {
    toggleDropdown() {
      this.isOpen = !this.isOpen;
      if (this.isOpen) {
        this.searchQuery = '';
      }
    },
    selectOption(option) {
      this.$emit('update:modelValue', option.value);
      this.$emit('change', option);
      this.isOpen = false;
    },
    // Close dropdown when clicking outside
    closeDropdown(event) {
      if (!event.target.closest('.dropdown-container')) {
        this.isOpen = false;
      }
    }
  }
}
</script>

<style scoped>
.dropdown-container {
  position: relative !important;
  display: inline-block !important;
  z-index: 100 !important;
  font-family: var(--font-family, inherit) !important;
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
  margin: 0 !important;
  outline: none !important;
}

.filter-btn {
  display: flex !important;
  align-items: center !important;
  gap: 12px !important;
  padding: 10px 16px !important;
  background: #f1f1f1 !important;
  border: 1px solid #d1d5db !important;
  border-radius: 8px !important;
  cursor: pointer !important;
  font-size: 14px !important;
  color: #374151 !important;
  transition: all 0.3s !important;
  width: 100% !important;
  min-width: 320px !important;
  height: 50px !important;
  justify-content: space-between !important;
  font-family: var(--font-family, inherit) !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15) !important;
}

.filter-btn:hover {
  background: #e5e7eb !important;
  border-color: #9ca3af !important;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2) !important;
  transform: translateY(-2px) !important;
}

.filter-btn:focus {
  outline: none !important;
  border-color: #3b82f6 !important;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
}

.filter-btn:active {
  transform: translateY(0) !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
  background: #f1f5f9 !important;
}

.text-content {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  flex: 1;
  font-family: var(--font-family, inherit);
  min-width: 0;
  overflow: hidden;
}

.dropdown-label {
  color: #374151 !important;
  font-weight: 600 !important;
  font-family: var(--font-family, inherit) !important;
}

.dropdown-value {
  font-weight: 600 !important;
  color: #1f2937 !important;
  font-family: var(--font-family, inherit) !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  max-width: 400px !important;
}

/* Style the caret icon */
.filter-btn svg {
  color: #6b7280 !important;
  transition: color 0.3s !important;
}

.filter-btn:hover svg {
  color: #374151 !important;
}

.dropdown-menu {
  position: absolute !important;
  top: 100% !important;
  left: 0 !important;
  right: 0 !important;
  background: #ffffff !important;
  border: 1px solid #e5e7eb !important;
  border-radius: 8px !important;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05) !important;
  z-index: 99999 !important;
  margin-top: 4px !important;
  width: 100% !important;
  min-width: 320px !important;
  max-width: 500px !important;
  font-family: var(--font-family, inherit) !important;
  max-height: 300px !important; /* Optimized height to prevent overflow */
  overflow-y: auto !important;
  overflow-x: hidden !important; /* Prevent horizontal scrolling */
  padding-top: 0 !important;
  /* Enhanced scrollbar styling for better UX */
  scrollbar-width: thin !important;
  scrollbar-color: #3b82f6 #f1f1f1 !important;
}

.dropdown-search {
  width: 100%;
  box-sizing: border-box;
  padding: 20px 12px;
  border: none;
  border-bottom: 1px solid var(--dropdown-border, #ddd);
  outline: none;
  font-size: 14px;
  border-radius: 8px 8px 0 0;
  margin-bottom: 4px;
  font-family: var(--font-family, inherit);
}

.dropdown-item {
  padding: 12px 16px !important;
  cursor: pointer !important;
  font-size: 14px !important;
  color: #374151 !important;
  transition: all 0.2s !important;
  font-family: var(--font-family, inherit) !important;
  word-wrap: break-word !important;
  overflow-wrap: break-word !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  max-width: 100% !important;
  border: none !important;
}

.dropdown-item:hover {
  background: #f3f4f6 !important;
  color: #1f2937 !important;
}

.dropdown-item:first-child {
  border-radius: 8px 8px 0 0;
}

.dropdown-item:last-child {
  border-radius: 0 0 8px 8px;
}

.dropdown-no-results {
  padding: 10px 16px;
  color: #999;
  font-size: 14px;
  text-align: center;
}

/* Webkit scrollbar styling for better cross-browser support */
.dropdown-menu::-webkit-scrollbar {
  width: 6px !important;
}

.dropdown-menu::-webkit-scrollbar-track {
  background: #f1f1f1 !important;
  border-radius: 3px !important;
}

.dropdown-menu::-webkit-scrollbar-thumb {
  background: #7B6FDD !important;
  border-radius: 3px !important;
  transition: background 0.3s ease !important;
}

.dropdown-menu::-webkit-scrollbar-thumb:hover {
  background: #6B5FCD !important;
}


</style> 