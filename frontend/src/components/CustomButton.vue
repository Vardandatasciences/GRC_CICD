<template>
  <button 
    :class="config.className" 
    :disabled="config.disabled"
    :title="config.iconOnly ? config.name : undefined"
    @click="$emit('click')"
  >
    <component 
      :is="iconComponent" 
      :size="config.iconOnly ? (config.size || 18) : (config.size || 16)" 
      v-if="iconComponent"
    />
    <span v-if="!config.iconOnly">{{ config.name }}</span>
  </button>
</template>

<script>
import { 
  PhPlus, 
  PhCalendar, 
  PhCaretDown, 
  PhFadersHorizontal, 
  PhFlag, 
  PhDotsThree, 
  PhUserCircle, 
  PhCalendarBlank,
  PhArrowClockwise,
  PhCheck,
  PhCaretRight,
  PhFileText,
  PhClock,
  PhEye,
  PhDownload
} from '@phosphor-icons/vue';

export default {
  name: 'CustomButton',
  components: {
    PhPlus, 
    PhCalendar, 
    PhCaretDown, 
    PhFadersHorizontal, 
    PhFlag, 
    PhDotsThree, 
    PhUserCircle, 
    PhCalendarBlank,
    PhArrowClockwise,
    PhCheck,
    PhCaretRight,
    PhFileText,
    PhClock,
    PhEye,
    PhDownload
  },
  props: {
    config: {
      type: Object,
      required: true
    }
  },
  computed: {
    iconComponent() {
      const iconMap = {
        'PhPlus': PhPlus,
        'PhCalendar': PhCalendar,
        'PhCaretDown': PhCaretDown,
        'PhFadersHorizontal': PhFadersHorizontal,
        'PhFlag': PhFlag,
        'PhDotsThree': PhDotsThree,
        'PhUserCircle': PhUserCircle,
        'PhCalendarBlank': PhCalendarBlank,
        'PhArrowClockwise': PhArrowClockwise,
        'PhCheck': PhCheck,
        'PhCaretRight': PhCaretRight,
        'PhFileText': PhFileText,
        'PhClock': PhClock,
        'PhEye': PhEye,
        'PhDownload': PhDownload
      };
      
      return iconMap[this.config.icon] || null;
    }
  }
}
</script>

<style scoped>
.add-new-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--add-new-btn-bg, #7B6FDD);
  color: var(--add-new-btn-text, white);
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background-color 0.2s;
}

.add-new-btn:hover {
  background: var(--add-new-btn-hover-bg, #6A5ED4);
}

.add-new-btn:active {
  background: var(--add-new-btn-hover-bg, #6A5ED4);
}

/* Export button specific styling */
.incident-export-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background-color 0.2s;
}

.incident-export-btn:hover:not(:disabled) {
  background: #218838;
}

.incident-export-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}
</style> 