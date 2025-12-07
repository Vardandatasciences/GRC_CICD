<template>
  <div :class="['CB_change-badge', config.className, className]">
    <component :is="config.icon" class="CB_h-3 CB_w-3" />
    <span>{{ config.label }}</span>
  </div>
</template>

<script>
import { Plus, Edit, Minus, Equal } from 'lucide-vue-next'

export default {
  name: 'ChangeBadge',
  components: {
    Plus,
    Edit,
    Minus,
    Equal
  },
  props: {
    changeType: {
      type: String,
      required: true,
      validator: (value) => ['new', 'modified', 'removed', 'unchanged'].includes(value)
    },
    className: {
      type: String,
      default: ''
    }
  },
  computed: {
    changeConfig() {
      return {
        new: {
          icon: Plus,
          label: "New",
          className: "CB_bg-change-new-bg CB_text-change-new CB_border-change-new/20 CB_shadow-sm"
        },
        modified: {
          icon: Edit,
          label: "Modified",
          className: "CB_bg-change-modified-bg CB_text-change-modified CB_border-change-modified/20 CB_shadow-sm"
        },
        removed: {
          icon: Minus,
          label: "Removed",
          className: "CB_bg-change-removed-bg CB_text-change-removed CB_border-change-removed/20 CB_shadow-sm"
        },
        unchanged: {
          icon: Equal,
          label: "Unchanged",
          className: "CB_bg-change-unchanged-bg CB_text-change-unchanged CB_border-change-unchanged/20 CB_shadow-sm"
        }
      }
    },
    config() {
      return this.changeConfig[this.changeType]
    }
  }
}
</script>

<style scoped>
.CB_change-badge {
  @apply inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border transition-all duration-200;
}

.CB_change-badge:hover {
  @apply shadow-md transform scale-105;
}

/* Change type colors with enhanced styling */
.CB_bg-change-new-bg { @apply bg-change-new-bg; }
.CB_text-change-new { @apply text-change-new; }
.CB_border-change-new\/20 { @apply border-change-new/20; }

.CB_bg-change-modified-bg { @apply bg-change-modified-bg; }
.CB_text-change-modified { @apply text-change-modified; }
.CB_border-change-modified\/20 { @apply border-change-modified/20; }

.CB_bg-change-removed-bg { @apply bg-change-removed-bg; }
.CB_text-change-removed { @apply text-change-removed; }
.CB_border-change-removed\/20 { @apply border-change-removed/20; }

.CB_bg-change-unchanged-bg { @apply bg-change-unchanged-bg; }
.CB_text-change-unchanged { @apply text-change-unchanged; }
.CB_border-change-unchanged\/20 { @apply border-change-unchanged/20; }

/* Additional utility classes with CB_ prefix */
.CB_h-3 { @apply h-3; }
.CB_w-3 { @apply w-3; }
.CB_shadow-sm { @apply shadow-sm; }
</style>
