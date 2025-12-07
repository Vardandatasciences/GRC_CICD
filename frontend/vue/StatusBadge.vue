<template>
  <div :class="['SB_status-badge', config.className, className]">
    <component :is="config.icon" class="SB_h-3 SB_w-3" />
    <span>{{ config.label }}</span>
  </div>
</template>

<script>
import { CheckCircle, XCircle, AlertCircle, Circle, Clock } from 'lucide-vue-next'

export default {
  name: 'StatusBadge',
  components: {
    CheckCircle,
    XCircle,
    AlertCircle,
    Circle,
    Clock
  },
  props: {
    status: {
      type: String,
      required: true,
      validator: (value) => ['compliant', 'non-compliant', 'partial', 'gap', 'audit'].includes(value)
    },
    className: {
      type: String,
      default: ''
    }
  },
  computed: {
    statusConfig() {
      return {
        compliant: {
          icon: CheckCircle,
          label: "Compliant",
          className: "SB_bg-status-compliant-bg SB_text-status-compliant SB_border-status-compliant/20 SB_shadow-sm"
        },
        "non-compliant": {
          icon: XCircle,
          label: "Non-Compliant",
          className: "SB_bg-status-non-compliant-bg SB_text-status-non-compliant SB_border-status-non-compliant/20 SB_shadow-sm"
        },
        partial: {
          icon: AlertCircle,
          label: "Partially Compliant",
          className: "SB_bg-status-partial-bg SB_text-status-partial SB_border-status-partial/20 SB_shadow-sm"
        },
        gap: {
          icon: Circle,
          label: "Gap",
          className: "SB_bg-status-gap-bg SB_text-status-gap SB_border-status-gap/20 SB_shadow-sm"
        },
        audit: {
          icon: Clock,
          label: "Yet to Audit",
          className: "SB_bg-status-audit-bg SB_text-status-audit SB_border-status-audit/20 SB_shadow-sm"
        }
      }
    },
    config() {
      return this.statusConfig[this.status]
    }
  }
}
</script>

<style scoped>
.SB_status-badge {
  @apply inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border transition-all duration-200;
}

.SB_status-badge:hover {
  @apply shadow-md transform scale-105;
}

/* Status colors with enhanced styling */
.SB_bg-status-compliant-bg { @apply bg-status-compliant-bg; }
.SB_text-status-compliant { @apply text-status-compliant; }
.SB_border-status-compliant\/20 { @apply border-status-compliant/20; }

.SB_bg-status-non-compliant-bg { @apply bg-status-non-compliant-bg; }
.SB_text-status-non-compliant { @apply text-status-non-compliant; }
.SB_border-status-non-compliant\/20 { @apply border-status-non-compliant/20; }

.SB_bg-status-partial-bg { @apply bg-status-partial-bg; }
.SB_text-status-partial { @apply text-status-partial; }
.SB_border-status-partial\/20 { @apply border-status-partial/20; }

.SB_bg-status-gap-bg { @apply bg-status-gap-bg; }
.SB_text-status-gap { @apply text-status-gap; }
.SB_border-status-gap\/20 { @apply border-status-gap/20; }

.SB_bg-status-audit-bg { @apply bg-status-audit-bg; }
.SB_text-status-audit { @apply text-status-audit; }
.SB_border-status-audit\/20 { @apply border-status-audit/20; }

/* Additional utility classes with SB_ prefix */
.SB_h-3 { @apply h-3; }
.SB_w-3 { @apply w-3; }
.SB_shadow-sm { @apply shadow-sm; }
</style>
