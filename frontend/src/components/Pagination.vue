<template>
  <div class="pagination-bar">
    <div class="results-info">
      Results: {{ startResult }} - {{ endResult }} of {{ totalItems }}
    </div>
    <div class="page-size-selector">
      <select v-model.number="localPageSize" @change="onPageSizeChange">
        <option v-for="option in pageSizeOptions" :key="option" :value="option">
          {{ option }}
        </option>
      </select>
    </div>
    <div class="pagination-controls">
      <button :disabled="currentPage === 1" @click="$emit('update:page', currentPage - 1)">&lt;</button>
      <template v-for="page in paginationNumbers" :key="page">
        <button
          v-if="typeof page === 'number'"
          :class="{ active: page === currentPage }"
          @click="$emit('update:page', page)"
        >
          {{ page }}
        </button>
        <span v-else class="ellipsis">...</span>
      </template>
      <button :disabled="currentPage === totalPages" @click="$emit('update:page', currentPage + 1)">&gt;</button>
    </div>
  </div>
</template>

<script>
import { computed, ref, watch } from 'vue';

export default {
  name: 'PaginationComponent',
  props: {
    currentPage: { type: Number, required: true },
    totalPages: { type: Number, required: true },
    pageSize: { type: Number, required: true },
    totalItems: { type: Number, required: true },
    pageSizeOptions: { type: Array, default: () => [6, 15, 30, 50] }
  },
  emits: ['update:page', 'update:pageSize'],
  setup(props, { emit }) {
    console.log('Pagination component props:', props);
    
    const localPageSize = ref(props.pageSize);
    
    watch(() => props.pageSize, (val) => { 
      localPageSize.value = val; 
    });

    const startResult = computed(() => (props.totalItems === 0 ? 0 : (props.currentPage - 1) * props.pageSize + 1));
    const endResult = computed(() => Math.min(props.currentPage * props.pageSize, props.totalItems));

    const paginationNumbers = computed(() => {
      const pages = [];
      const total = props.totalPages;
      const current = props.currentPage;
      if (total <= 7) {
        for (let i = 1; i <= total; i++) pages.push(i);
      } else {
        pages.push(1);
        if (current > 3) pages.push('...');
        let start = Math.max(2, current - 1);
        let end = Math.min(total - 1, current + 1);
        if (current <= 2) { start = 2; end = 3; }
        if (current >= total - 1) { start = total - 2; end = total - 1; }
        for (let i = start; i <= end; i++) pages.push(i);
        if (current < total - 2) pages.push('...');
        pages.push(total);
      }
      return pages.filter((v, i, a) => a.indexOf(v) === i);
    });

    function onPageSizeChange() {
      emit('update:pageSize', localPageSize.value);
    }

    return {
      localPageSize,
      startResult,
      endResult,
      paginationNumbers,
      onPageSizeChange
    };
  }
}
</script>

<style scoped>
.pagination-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 2rem;
  background: var(--pagination-bg);
  border-radius: var(--pagination-radius);
  padding: 16px 24px;
  box-shadow: var(--pagination-shadow);
  margin-top: 24px;
}
.results-info {
  font-size: 16px;
  color: var(--pagination-info-color);
  min-width: 180px;
}
.page-size-selector {
  flex: 1;
  display: flex;
  justify-content: center;
}
.page-size-selector select {
  padding: 6px 24px 6px 12px;
  border: 1px solid var(--pagination-select-border);
  border-radius: 6px;
  background: var(--pagination-select-bg);
  font-size: 16px;
  color: var(--pagination-select-color);
  appearance: none;
  min-width: 60px;
  cursor: pointer;
}
.pagination-controls {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 4px;
}
.pagination-controls button {
  padding: 6px 14px;
  border: 1px solid var(--pagination-btn-border);
  background: var(--pagination-btn-bg);
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
  color: var(--pagination-btn-color);
  transition: all 0.2s;
}
.pagination-controls button.active {
  background: var(--pagination-btn-active-bg);
  border-color: var(--pagination-btn-active-bg);
  color: var(--pagination-btn-active-color);
}
.pagination-controls button:disabled {
  opacity: var(--pagination-btn-disabled-opacity);
  cursor: not-allowed;
}
.ellipsis {
  padding: 6px 8px;
  color: var(--pagination-ellipsis-color);
  font-size: 18px;
}
</style> 