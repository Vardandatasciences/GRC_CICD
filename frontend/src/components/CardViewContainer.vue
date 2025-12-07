<template>
  <div class="card-view-container">
    <header class="card-view-header">
      <h1 class="card-view-title">{{ title }}</h1>
      <div class="card-view-search">
        <input
          v-model="searchQuery"
          :placeholder="searchPlaceholder"
          @input="onSearch"
        />
        <PhMagnifyingGlass class="search-icon" :size="20" />
      </div>
    </header>
    <main class="card-grid">
      <CardContainer
        v-for="(card, idx) in paginatedCards"
        :key="card.id || idx"
        :card-data="card"
        :columns="columns"
        :buttons="buttons"
      />
    </main>
    <Pagination
      v-if="filteredCards.length > 0"
      :current-page="currentPage"
      :total-pages="totalPages"
      :page-size="pageSize"
      :total-items="filteredCards.length"
      :page-size-options="pageSizeOptions"
      @update:page="onPageChange"
      @update:pageSize="onPageSizeChange"
    />
  </div>
</template>

<script setup>
/* eslint-disable no-undef */
import { ref, computed, watch } from 'vue';
import { PhMagnifyingGlass } from '@phosphor-icons/vue';
import CardContainer from './CardContainer.vue';
import Pagination from './Pagination.vue';

const props = defineProps({
  title: { type: String, default: 'Card View' },
  searchPlaceholder: { type: String, default: 'Search...' },
  cards: { type: Array, required: true },
  columns: { type: Array, required: true }, // [{ label, key }]
  buttons: { type: Array, default: () => [] } // [{ name, icon, className, ... }]
});

const searchQuery = ref('');
const currentPage = ref(1);
const pageSize = ref(7); // Default page size, can be changed by user
const pageSizeOptions = [7, 10, 20, 50];

const filteredCards = computed(() => {
  if (!searchQuery.value) return props.cards;
  return props.cards.filter(card =>
    card.name?.toLowerCase().includes(searchQuery.value.toLowerCase())
  );
});

const totalPages = computed(() => {
  return Math.ceil(filteredCards.value.length / pageSize.value) || 1;
});

const paginatedCards = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  return filteredCards.value.slice(start, start + pageSize.value);
});

watch([filteredCards, pageSize], () => {
  currentPage.value = 1; // Reset to first page on search/filter/page size change
});

function onSearch() {
  // Optionally emit search event
}

function onPageChange(page) {
  currentPage.value = page;
}

function onPageSizeChange(newSize) {
  pageSize.value = newSize;
}
</script>

<style scoped>
.card-view-container {
  padding: 24px;
  background-color: var(--card-view-bg);
  min-height: 100vh;
  border-radius: var(--card-view-radius);
  box-shadow: var(--card-view-shadow);
}
.card-view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  background: var(--card-view-header-bg);
  border-bottom: var(--card-view-header-border);
}
.card-view-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--card-view-title-color);
}
.card-view-search {
  position: relative;
}
.card-view-search input {
  padding: 8px 16px;
  padding-right: 40px;
  border: 1px solid var(--card-view-search-border);
  border-radius: 4px;
  width: 240px;
  font-size: 14px;
  background: var(--card-view-search-bg);
  color: var(--card-view-search-text);
}
.card-view-search input::placeholder {
  color: var(--card-view-search-placeholder);
}
.search-icon {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--card-view-search-placeholder);
}
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--card-grid-gap);
  margin-bottom: 0;
}
</style> 