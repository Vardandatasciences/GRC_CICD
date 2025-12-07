<template>
  <div class="relative" ref="dropdownRef">
    <button
      @click="toggleDropdown"
      :disabled="disabled"
      class="custom-dropdown-btn"
    >
      <span class="custom-dropdown-text">{{ selectedText }}</span>
      <svg class="custom-dropdown-chevron" :class="{ 'custom-dropdown-chevron-open': isOpen }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
      </svg>
    </button>
    
    <div
      v-if="isOpen"
      class="custom-dropdown-menu"
    >
      <!-- Search Input -->
      <div class="custom-dropdown-search">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search..."
          class="custom-dropdown-search-input"
          @click.stop
        />
      </div>
      
      <!-- Options List -->
      <div class="custom-dropdown-options">
        <div
          v-for="option in filteredOptions"
          :key="option.value"
          @click="selectOption(option)"
          class="custom-dropdown-option"
          :class="{ 'custom-dropdown-option-selected': option.value === selectedValue }"
        >
          <span class="custom-dropdown-option-text">{{ option.label }}</span>
          <span
            v-if="option.value === selectedValue"
            class="custom-dropdown-option-check"
          >
            <svg class="custom-dropdown-check-icon" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
            </svg>
          </span>
        </div>
        
        <!-- No results message -->
        <div v-if="filteredOptions.length === 0" class="custom-dropdown-no-results">
          No options found
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'

export default {
  name: 'CustomDropdown',
  props: {
    options: {
      type: Array,
      required: true
    },
    modelValue: {
      type: [String, Number],
      default: ''
    },
    placeholder: {
      type: String,
      default: 'Select an option'
    },
    disabled: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:modelValue', 'change'],
  setup(props, { emit }) {
    const isOpen = ref(false)
    const dropdownRef = ref(null)
    const searchQuery = ref('')

    const selectedValue = computed(() => props.modelValue)
    
    const selectedText = computed(() => {
      if (!props.modelValue) return props.placeholder
      const option = props.options.find(opt => opt.value === props.modelValue)
      return option ? option.label : props.placeholder
    })

    const filteredOptions = computed(() => {
      if (!searchQuery.value) return props.options
      return props.options.filter(option =>
        option.label.toLowerCase().includes(searchQuery.value.toLowerCase())
      )
    })

    const toggleDropdown = () => {
      if (!props.disabled) {
        isOpen.value = !isOpen.value
        if (isOpen.value) {
          searchQuery.value = '' // Clear search when opening
        }
      }
    }

    const selectOption = (option) => {
      emit('update:modelValue', option.value)
      emit('change', option.value)
      isOpen.value = false
    }

    const closeDropdown = (event) => {
      if (dropdownRef.value && !dropdownRef.value.contains(event.target)) {
        isOpen.value = false
      }
    }

    onMounted(() => {
      document.addEventListener('click', closeDropdown)
    })

    onUnmounted(() => {
      document.removeEventListener('click', closeDropdown)
    })

    return {
      isOpen,
      dropdownRef,
      searchQuery,
      selectedValue,
      selectedText,
      filteredOptions,
      toggleDropdown,
      selectOption
    }
  }
}
</script>

<style scoped>
/* Modern Custom Dropdown Styling */
.custom-dropdown-btn {
  width: 100%;
  height: 45px;
  padding: 10px 16px;
  font-size: 14px;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  background-color: white;
  transition: all 0.3s ease;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #495057;
  font-weight: 500;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.custom-dropdown-btn:hover:not(:disabled) {
  border-color: #4f8cff;
  box-shadow: 0 0 0 2px rgba(79, 140, 255, 0.1);
  background-color: #f8f9ff;
}

.custom-dropdown-btn:focus {
  outline: none;
  border-color: #4f8cff;
  box-shadow: 0 0 0 3px rgba(79, 140, 255, 0.1);
}

.custom-dropdown-btn:disabled {
  background-color: #f8f9fa;
  color: #adb5bd;
  cursor: not-allowed;
  border-color: #dee2e6;
}

.custom-dropdown-text {
  flex: 1;
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.custom-dropdown-chevron {
  width: 16px;
  height: 16px;
  color: #6c757d;
  flex-shrink: 0;
  transition: transform 0.2s ease;
}

.custom-dropdown-chevron-open {
  transform: rotate(180deg);
}

.custom-dropdown-btn:hover .custom-dropdown-chevron {
  color: #4f8cff;
}

.custom-dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 99999;
  margin-top: 4px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  border: 1px solid #e9ecef;
  overflow: hidden;
  max-height: 240px;
  animation: dropdownSlideIn 0.2s ease-out;
}

.custom-dropdown-search {
  padding: 12px;
  border-bottom: 1px solid #e9ecef;
  background: linear-gradient(135deg, #f8f9ff 0%, #f0f7ff 100%);
}

.custom-dropdown-search-input {
  width: 100%;
  padding: 8px 12px;
  font-size: 0.85rem;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  background: white;
  transition: all 0.2s ease;
  color: #495057;
}

.custom-dropdown-search-input:focus {
  outline: none;
  border-color: #4f8cff;
  box-shadow: 0 0 0 2px rgba(79, 140, 255, 0.1);
}

.custom-dropdown-search-input::placeholder {
  color: #6c757d;
}

.custom-dropdown-options {
  max-height: 192px;
  overflow-y: auto;
}

.custom-dropdown-option {
  padding: 10px 12px;
  font-size: 0.85rem;
  color: #495057;
  transition: all 0.15s ease;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  border-bottom: 1px solid #f8f9fa;
}

.custom-dropdown-option:last-child {
  border-bottom: none;
}

.custom-dropdown-option:hover {
  background: linear-gradient(135deg, #f8f9ff 0%, #f0f7ff 100%);
  color: #4f8cff;
}

.custom-dropdown-option-selected {
  background: linear-gradient(135deg, #e6f2ff 0%, #cce7ff 100%) !important;
  color: #4f8cff !important;
  font-weight: 600;
}

.custom-dropdown-option-text {
  flex: 1;
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.custom-dropdown-option-check {
  display: flex;
  align-items: center;
  margin-left: 8px;
}

.custom-dropdown-check-icon {
  width: 16px;
  height: 16px;
  color: #4f8cff;
}

.custom-dropdown-no-results {
  padding: 16px 12px;
  text-align: center;
  font-size: 0.8rem;
  color: #6c757d;
  font-style: italic;
  background: #f8f9fa;
}

/* Custom scrollbar for dropdown options */
.custom-dropdown-options::-webkit-scrollbar {
  width: 6px;
}

.custom-dropdown-options::-webkit-scrollbar-track {
  background: #f1f3f4;
  border-radius: 3px;
}

.custom-dropdown-options::-webkit-scrollbar-thumb {
  background: #c1c8cd;
  border-radius: 3px;
}

.custom-dropdown-options::-webkit-scrollbar-thumb:hover {
  background: #a8b2ba;
}

/* Animation for dropdown menu */
@keyframes dropdownSlideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Focus states for accessibility */
.custom-dropdown-btn:focus {
  outline: 2px solid #4f8cff;
  outline-offset: 2px;
}

.custom-dropdown-option:focus {
  outline: 2px solid #4f8cff;
  outline-offset: -2px;
}
</style>
