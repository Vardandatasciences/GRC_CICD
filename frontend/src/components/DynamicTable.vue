<template>
  <div class="dynamic-table-container">
    <!-- Filters Section - Above Table -->
    <div class="filters-section-above" v-if="filters && filters.length > 0">
      <div class="filters-container">
        <CustomDropdown
          v-for="filter in filters"
          :key="filter.name"
          :config="filter"
          v-model="filterValues[filter.name]"
          @change="handleFilterChange"
        />
      </div>
    </div>

    <!-- Table Section -->
    <div class="table-wrapper">
      <table class="dynamic-table">
        <thead>
          <tr>
            <th v-if="showCheckbox">
              <input 
                type="checkbox" 
                :checked="allSelected"
                @change="toggleSelectAll"
              />
            </th>
            <th 
              v-for="column in visibleColumns" 
              :key="column.key"
              :class="[
                column.headerClass, 
                'dynamic-table-header-cell', 
                { 'is-sorted': sortKey === column.key },
                { 'pinned-left': columnPins[column.key] === 'left' },
                { 'pinned-right': columnPins[column.key] === 'right' }
              ]"
              :style="{ width: columnWidths[column.key] ? columnWidths[column.key] + 'px' : (column.width ? column.width : (column.headerStyle && column.headerStyle.width ? column.headerStyle.width : 'auto')) }"
            >
              <div class="header-content">
                <span class="header-label" :title="formatHeaderLabel(column.label)">
                  {{ formatHeaderLabel(column.label) }}
                  <span v-if="sortKey === column.key" class="sort-indicator">
                    <i :class="sortOrder === 'asc' ? 'fas fa-arrow-up' : 'fas fa-arrow-down'"></i>
                  </span>
                </span>
                <div class="header-icons">
                  <button
                    type="button"
                    class="header-icon-btn filter-icon"
                    title="Filter column"
                    @click.stop="openColumnFilter(column, $event)"
                  >
                    <svg class="header-icon-svg" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                      <line x1="5" y1="7" x2="19" y2="7" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
                      <line x1="7" y1="12" x2="17" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
                      <line x1="10" y1="17" x2="14" y2="17" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
                    </svg>
                  </button>
                  <button
                    type="button"
                    class="header-icon-btn menu-icon"
                    title="Column options"
                    @click.stop="openColumnMenu(column, $event)"
                  >
                    <i class="fas fa-ellipsis-v"></i>
                  </button>
                </div>
              </div>
            </th>
            <th v-if="showActions" class="actions-column">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="row in paginatedData" 
            :key="row[uniqueKey] || row.id"
            @click="handleRowClick(row)"
            :class="getRowClass ? getRowClass(row) : 'dynamic-table-row'"
          >
            <td v-if="showCheckbox">
              <input 
                type="checkbox" 
                :checked="selectedRows.includes(row[uniqueKey] || row.id)"
                @change="toggleRowSelection(row)"
              />
            </td>
            <td 
              v-for="column in visibleColumns" 
              :key="column.key"
              :class="[
                column.cellClass,
                { 'pinned-left': columnPins[column.key] === 'left' },
                { 'pinned-right': columnPins[column.key] === 'right' }
              ]"
              :style="{ width: columnWidths[column.key] ? columnWidths[column.key] + 'px' : (column.width ? column.width : (column.headerStyle && column.headerStyle.width ? column.headerStyle.width : 'auto')) }"
              :title="String(row[column.key] || '')"
            >
              <component 
                v-if="column.component"
                :is="column.component"
                :row="row"
                :column="column"
                :value="row[column.key]"
              />
              <template v-else-if="column.slot">
                <slot :name="`cell-${column.key}`" :row="row" :column="column" :value="row[column.key]">
                  {{ row[column.key] }}
                </slot>
              </template>
              <template v-else>
                <div v-if="column.type === 'image'" class="image-cell" :title="column.showText ? String(row[column.textKey] || '') : ''">
                  <img :src="row[column.key]" :alt="column.altKey ? row[column.altKey] : ''" />
                  <span v-if="column.showText">{{ row[column.textKey] }}</span>
                </div>
                <div v-else-if="column.type === 'status'" class="status-cell">
                  <span :class="['status', getStatusClass(row[column.key])]" :title="String(row[column.key] || '')">
                    {{ row[column.key] }}
                  </span>
                </div>
                <div v-else-if="column.type === 'progress'" class="progress-cell" :title="`${row[column.key]}%`">
                  <div class="progress-bar-container">
                    <div 
                      class="progress-bar"
                      :class="getProgressBarColorClass(row[column.key])"
                      :style="{ width: row[column.key] + '%' }"
                    ></div>
                  </div>
                  <span class="progress-value">{{ row[column.key] }}%</span>
                </div>
                <div v-else-if="column.type === 'actions'" class="actions-cell">
                  <button class="action-dots">...</button>
                </div>
                <div v-else class="text-cell">
                  <div 
                    class="cell-content"
                    :title="String(row[column.key] || '')"
                  >
                    {{ row[column.key] }}
                  </div>
                </div>
              </template>
            </td>
            <td v-if="showActions" class="actions-column">
              <slot name="actions" :row="row">
                <button class="action-dots">...</button>
              </slot>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <transition name="fade">
      <div
        v-if="activeFilterColumn"
        ref="columnFilterPopover"
        class="column-filter-popover"
        :style="{
          top: columnFilterPosition.top,
          left: columnFilterPosition.left,
          width: columnFilterPopoverWidth + 'px'
        }"
      >
        <div class="column-filter-header">
          <span class="column-filter-title">{{ activeFilterColumn.label }}</span>
          <button type="button" class="column-filter-close-btn" @click="closeColumnFilter">
            ×
          </button>
        </div>
        <div class="column-filter-search">
          <input
            type="text"
            v-model="columnFilterSearch"
            placeholder="Search..."
          />
        </div>
        <div class="column-filter-select-all">
          <label>
            <input
              type="checkbox"
              :checked="isAllColumnFilterSelected"
              @change="toggleSelectAllColumnFilter"
            />
            <span>Select All</span>
          </label>
        </div>
        <div class="column-filter-options">
          <label
            v-for="option in filteredColumnFilterOptions"
            :key="option.value"
            class="column-filter-option"
          >
            <input
              type="checkbox"
              :value="option.value"
              v-model="columnFilterTempSelection"
              @change="handleColumnFilterOptionChange"
            />
            <span>{{ option.label }}</span>
          </label>
          <div
            v-if="filteredColumnFilterOptions.length === 0"
            class="column-filter-empty"
          >
            No matches found
          </div>
        </div>
        <div class="column-filter-actions">
          <button type="button" class="column-filter-btn apply" @click="applyColumnFilter">Apply</button>
          <button type="button" class="column-filter-btn clear" @click="clearColumnFilter">Clear</button>
        </div>
      </div>
    </transition>

    <!-- Column Menu Dropdown -->
    <transition name="fade">
      <div
        v-if="activeMenuColumn"
        ref="columnMenuPopover"
        class="column-menu-popover"
        :style="{
          top: columnMenuPosition.top,
          left: columnMenuPosition.left
        }"
      >
        <div 
          class="column-menu-item" 
          @click="sortColumn('asc')"
          :class="{ 'disabled': activeMenuColumn && activeMenuColumn.sortable === false }"
          :title="activeMenuColumn && activeMenuColumn.sortable === false ? 'This column is not sortable' : ''"
        >
          <i class="fas fa-arrow-up"></i>
          <span>Sort Ascending</span>
        </div>
        <div 
          class="column-menu-item" 
          @click="sortColumn('desc')"
          :class="{ 'disabled': activeMenuColumn && activeMenuColumn.sortable === false }"
          :title="activeMenuColumn && activeMenuColumn.sortable === false ? 'This column is not sortable' : ''"
        >
          <i class="fas fa-arrow-down"></i>
          <span>Sort Descending</span>
        </div>
        <div class="column-menu-divider"></div>
        <div 
          class="column-menu-item column-menu-item-with-submenu"
          :class="{ 'flip-submenu': shouldFlipSubmenu }"
          @mouseenter="showPinSubmenu = true"
          @mouseleave="showPinSubmenu = false"
        >
          <i class="fas fa-thumbtack"></i>
          <span>Pin Column</span>
          <i class="fas submenu-arrow" :class="shouldFlipSubmenu ? 'fa-chevron-left' : 'fa-chevron-right'"></i>
          <transition name="fade">
            <div v-if="showPinSubmenu" class="column-menu-submenu">
              <div class="column-menu-item submenu-item" @click="pinColumn(null)">
                <i class="fas fa-check" :class="{ invisible: columnPins[activeMenuColumn?.key] !== null && columnPins[activeMenuColumn?.key] !== undefined }"></i>
                <span>No Pin</span>
              </div>
              <div class="column-menu-item submenu-item" @click="pinColumn('left')">
                <i class="fas fa-check" :class="{ invisible: columnPins[activeMenuColumn?.key] !== 'left' }"></i>
                <span>Pin Left</span>
              </div>
              <div class="column-menu-item submenu-item" @click="pinColumn('right')">
                <i class="fas fa-check" :class="{ invisible: columnPins[activeMenuColumn?.key] !== 'right' }"></i>
                <span>Pin Right</span>
              </div>
            </div>
          </transition>
        </div>
        <div class="column-menu-divider"></div>
        <div class="column-menu-item" @click="autosizeColumn">
          <i class="fas fa-arrows-alt-h"></i>
          <span>Autosize This Column</span>
        </div>
        <div class="column-menu-item" @click="autosizeAllColumns">
          <i class="fas fa-expand"></i>
          <span>Autosize All Columns</span>
        </div>
        <div class="column-menu-divider"></div>
        <div class="column-menu-item" @click="openColumnChooser">
          <i class="fas fa-columns"></i>
          <span>Choose Columns</span>
        </div>
        <div class="column-menu-item" @click="resetColumns">
          <i class="fas fa-undo"></i>
          <span>Reset Columns</span>
        </div>
      </div>
    </transition>

    <!-- Pagination Section -->
    <div class="pagination-container" v-if="showPagination">
      <div class="results-info">
        <span v-if="itemsPerPage === 'all'">
          Results: 1 - {{ filteredData.length }} of {{ filteredData.length }}
        </span>
        <span v-else>
          Results: {{ (currentPage - 1) * itemsPerPage + 1 }} - {{ Math.min(currentPage * itemsPerPage, filteredData.length) }} of {{ filteredData.length }}
        </span>
      </div>
      <div class="items-per-page-selector">
        <select v-model="itemsPerPage" @change="currentPage = 1">
          <option v-for="option in pageSizeOptions" :key="option" :value="option">
            {{ option === 'all' ? 'All' : option }}
          </option>
        </select>
      </div>
      <div class="pagination-controls" v-if="itemsPerPage !== 'all'">
        <button @click="prevPage" :disabled="currentPage === 1">&lt;</button>
        <template v-for="page in paginationNumbers" :key="page">
          <button 
            v-if="typeof page === 'number'" 
            @click="changePage(page)" 
            :class="{ active: currentPage === page }"
          >
            {{ page }}
          </button>
          <span v-else class="ellipsis">...</span>
        </template>
        <button @click="nextPage" :disabled="currentPage === totalPages">&gt;</button>
      </div>
    </div>
  </div>
</template>

<script>
import { PhCaretDown, PhCaretUp } from '@phosphor-icons/vue';
import CustomDropdown from './CustomDropdown.vue';
import CustomButton from './CustomButton.vue';
import './styles/theme.css';

export default {
  name: 'DynamicTable',
  components: {
    PhCaretDown,
    PhCaretUp,
    CustomDropdown,
    CustomButton
  },
  props: {
  // Table configuration
  data: {
    type: Array,
    required: true
  },
  columns: {
    type: Array,
    required: true
  },
  uniqueKey: {
    type: String,
    default: 'id'
  },
  
  // Header configuration
  filters: {
    type: Array,
    default: () => []
  },
  
  // Table features
  showCheckbox: {
    type: Boolean,
    default: false
  },
  showActions: {
    type: Boolean,
    default: false
  },
  showPagination: {
    type: Boolean,
    default: true
  },
  
  // Pagination configuration
  pageSizeOptions: {
    type: Array,
    default: () => [7, 10, 20, 50]
  },
  defaultPageSize: {
    type: Number,
    default: 6
  },
  
  // Row styling
  getRowClass: {
    type: Function,
    default: null
  }
  },
  data() {
    return {
      currentPage: 1,
      itemsPerPage: this.defaultPageSize,
      selectedRows: [],
      filterValues: {},
      sortKey: '',
      sortOrder: 'asc',
      columnWidths: {},
      columnFilters: {},
      activeFilterColumn: null,
      columnFilterSearch: '',
      columnFilterTempSelection: [],
      columnFilterPosition: {
        top: 0,
        left: 0
      },
      columnFilterPopoverWidth: 260,
      lastFilterTrigger: null,
      activeMenuColumn: null,
      columnMenuPosition: {
        top: 0,
        left: 0
      },
      showPinSubmenu: false,
      columnPins: {},
      lastMenuTrigger: null,
      shouldFlipSubmenu: false
    }
  },
  computed: {
    visibleColumns() {
      const visible = this.columns.filter(column => !column.hidden);
      
      // Sort columns by pin position
      const pinnedLeft = [];
      const unpinned = [];
      const pinnedRight = [];
      
      visible.forEach(column => {
        const pin = this.columnPins[column.key];
        if (pin === 'left') {
          pinnedLeft.push(column);
        } else if (pin === 'right') {
          pinnedRight.push(column);
        } else {
          unpinned.push(column);
        }
      });
      
      return [...pinnedLeft, ...unpinned, ...pinnedRight];
    },
    filteredData() {
      let filtered = [...this.data];
      
      console.log('DynamicTable - Original data length:', this.data.length);
      console.log('DynamicTable - Filter values:', this.filterValues);
      console.log('DynamicTable - Filters:', this.filters);
  
  // Apply filters
      Object.entries(this.filterValues).forEach(([filterName, value]) => {
    if (value && value !== 'all') {
          const filter = this.filters.find(f => f.name === filterName);
      if (filter && filter.filterFunction) {
        filtered = filtered.filter(row => filter.filterFunction(row, value));
      }
    }
  });
  
  // Apply column filters
      Object.entries(this.columnFilters).forEach(([columnKey, selectedValues]) => {
    if (Array.isArray(selectedValues) && selectedValues.length > 0) {
          filtered = filtered.filter(row => {
            const normalized = this.normalizeFilterValue(row[columnKey]);
            return selectedValues.includes(normalized);
          });
    }
  });

  // Apply sorting
      if (this.sortKey) {
    filtered.sort((a, b) => {
          let aVal = a[this.sortKey];
          let bVal = b[this.sortKey];
      
          // Handle null/undefined values
          if (aVal === null || aVal === undefined) aVal = '';
          if (bVal === null || bVal === undefined) bVal = '';
          
          // Try to detect and handle different data types
          // Check if both values are numbers
          const aNum = parseFloat(aVal);
          const bNum = parseFloat(bVal);
          if (!isNaN(aNum) && !isNaN(bNum)) {
            return this.sortOrder === 'asc' ? aNum - bNum : bNum - aNum;
          }
          
          // Check if both values are dates
          const aDate = new Date(aVal);
          const bDate = new Date(bVal);
          if (aDate instanceof Date && !isNaN(aDate) && bDate instanceof Date && !isNaN(bDate)) {
            return this.sortOrder === 'asc' ? aDate - bDate : bDate - aDate;
          }
          
          // Default to string comparison
          const aStr = String(aVal).toLowerCase();
          const bStr = String(bVal).toLowerCase();
          
          if (aStr < bStr) return this.sortOrder === 'asc' ? -1 : 1;
          if (aStr > bStr) return this.sortOrder === 'asc' ? 1 : -1;
      return 0;
    });
  }
  
      console.log('DynamicTable - Filtered data length:', filtered.length);
      console.log('DynamicTable - Final filtered data:', filtered);
  
  return filtered;
    },
    totalPages() {
      // If itemsPerPage is 'all', there's only 1 page
      if (this.itemsPerPage === 'all') {
        return 1;
      }
      return Math.ceil(this.filteredData.length / this.itemsPerPage);
    },
    paginatedData() {
      // If itemsPerPage is 'all', return all filtered data
      if (this.itemsPerPage === 'all') {
        return this.filteredData;
      }
      
      const start = (this.currentPage - 1) * this.itemsPerPage;
      const end = start + this.itemsPerPage;
      const paginated = this.filteredData.slice(start, end);
      
      console.log('DynamicTable - Pagination info:', {
        itemsPerPage: this.itemsPerPage,
        currentPage: this.currentPage,
        totalPages: this.totalPages,
        filteredDataLength: this.filteredData.length,
        start: start,
        end: end,
        paginatedLength: paginated.length
      });
      
      return paginated;
    },
    allSelected() {
      return this.selectedRows.length === this.paginatedData.length && this.paginatedData.length > 0;
    },
    paginationNumbers() {
  const pages = [];
      const total = this.totalPages;
      const current = this.currentPage;

  if (total <= 7) {
    for (let i = 1; i <= total; i++) {
      pages.push(i);
    }
  } else {
    pages.push(1);
    if (current > 3) {
      pages.push('...');
    }
    
    let start = Math.max(2, current - 1);
    let end = Math.min(total - 1, current + 1);

    if (current <= 2) {
      start = 2;
      end = 3;
    }

    if (current >= total - 1) {
      start = total - 2;
      end = total - 1;
    }

    for (let i = start; i <= end; i++) {
      pages.push(i);
    }

    if (current < total - 2) {
      pages.push('...');
    }
    pages.push(total);
  }
  return pages.filter((v, i, a) => a.indexOf(v) === i);
    },
    columnFilterOptions() {
      if (!this.activeFilterColumn) {
        return [];
      }
      return this.getColumnFilterOptions(this.activeFilterColumn);
    },
    filteredColumnFilterOptions() {
      const search = this.columnFilterSearch.trim().toLowerCase();
      if (!search) {
        return this.columnFilterOptions;
      }
      return this.columnFilterOptions.filter(option =>
        option.label.toLowerCase().includes(search)
      );
    },
    isAllColumnFilterSelected() {
      if (!this.activeFilterColumn) return false;
      const optionValues = this.columnFilterOptions.map(option => option.value);
      if (optionValues.length === 0) return false;
      return optionValues.every(value =>
        this.columnFilterTempSelection.includes(value)
      );
    }
  },
  watch: {
    data: {
      handler() {
        this.currentPage = 1;
      },
      deep: true
    },
    columns: {
      handler() {
        // Re-initialize column widths when columns change
        this.visibleColumns.forEach(column => {
          if (column.width && !this.columnWidths[column.key]) {
            const widthMatch = column.width.match(/(\d+)px/);
            if (widthMatch) {
              this.columnWidths[column.key] = parseInt(widthMatch[1]);
            }
          }
        });
      },
      deep: true
    }
  },
  mounted() {
    // Initialize filter values
    this.filters.forEach(filter => {
      this.filterValues[filter.name] = filter.defaultValue || '';
    });
    
    // Initialize column widths from width property
    this.visibleColumns.forEach(column => {
      if (column.width && !this.columnWidths[column.key]) {
        // Extract numeric value from width string (e.g., "300px" -> 300)
        const widthMatch = column.width.match(/(\d+)px/);
        if (widthMatch) {
          this.columnWidths[column.key] = parseInt(widthMatch[1]);
        }
      }
    });
    
  },
  beforeUnmount() {
    document.removeEventListener('click', this.handleDocumentClick);
    document.removeEventListener('keydown', this.handleEscapePress);
    document.removeEventListener('click', this.handleMenuDocumentClick);
    document.removeEventListener('keydown', this.handleMenuEscapePress);
  },
  methods: {
    handleFilterChange(filter) {
      this.currentPage = 1;
      this.$emit('filter-change', { filter, values: this.filterValues });
    },
    handleRowClick(row) {
      this.$emit('row-click', row);
    },
    toggleRowSelection(row) {
      const rowId = row[this.uniqueKey] || row.id;
      const index = this.selectedRows.indexOf(rowId);
  
  if (index > -1) {
        this.selectedRows.splice(index, 1);
  } else {
        this.selectedRows.push(rowId);
      }
      
      this.$emit('row-select', { row, selected: this.selectedRows });
    },
    toggleSelectAll() {
      if (this.allSelected) {
        this.selectedRows = [];
  } else {
        this.selectedRows = this.paginatedData.map(row => row[this.uniqueKey] || row.id);
      }
      
      this.$emit('select-all', { selected: this.selectedRows, allSelected: this.allSelected });
    },
    changePage(page) {
      this.currentPage = page;
      this.$emit('page-change', page);
    },
    prevPage() {
      if (this.currentPage > 1) {
        this.currentPage--;
        this.$emit('page-change', this.currentPage);
      }
    },
    nextPage() {
      if (this.currentPage < this.totalPages) {
        this.currentPage++;
        this.$emit('page-change', this.currentPage);
      }
    },
    getStatusClass(status) {
  const statusMap = {
    'On rent': 'status-on-rent',
    'On sell': 'status-on-sell',
    'Renovation': 'status-renovation',
    'On Construction': 'status-on-construction',
    'Active': 'status-active',
    'Inactive': 'status-inactive',
    'Pending': 'status-pending',
    'Approved': 'status-approved',
    'Rejected': 'status-rejected'
  };
  return statusMap[status] || '';
    },
    getProgressBarColorClass(value) {
  if (value > 60) return 'progress-bar-success';
  if (value > 30) return 'progress-bar-warning';
  if (value > 0) return 'progress-bar-danger';
  return 'progress-bar-default';
    },
    // Function to check if text should be truncated
    isTextTruncated(text, column) {
      if (!text || typeof text !== 'string') return false;
      
      // Use column-specific truncation length if defined
      const maxLength = column.maxLength || 50;
      return text.length > maxLength;
    },
    requestColumnRemove(column) {
      this.$emit('remove-column', column);
    },
    openColumnFilter(column, event) {
      if (!column || !event || !event.currentTarget) return;

      const triggerEl = event.currentTarget;
      this.lastFilterTrigger = triggerEl;
      const rect = triggerEl.getBoundingClientRect();
      const tableContainer = this.$el.querySelector('.table-wrapper');
      const containerRect = tableContainer
        ? tableContainer.getBoundingClientRect()
        : { top: 0, left: 0 };
      const width = this.columnFilterPopoverWidth;
      const padding = 16;
      let left = rect.left - containerRect.left;
      const containerWidth = tableContainer ? tableContainer.clientWidth : window.innerWidth;
      if (left + width > containerWidth - padding) {
        left = Math.max(padding, containerWidth - width - padding);
      }
      const headerRow = triggerEl.closest('th');
      const headerRect = headerRow ? headerRow.getBoundingClientRect() : rect;
      const top = headerRect.bottom - containerRect.top + 6;

      this.activeFilterColumn = column;
      this.columnFilterSearch = '';
      const options = this.getColumnFilterOptions(column);
      const existingSelection = this.columnFilters[column.key] || [];
      const defaultSelection =
        existingSelection.length > 0
          ? [...existingSelection]
          : options.map(option => option.value);

      this.columnFilterTempSelection = [...defaultSelection];
      this.columnFilterPosition = {
        top: `${top}px`,
        left: `${left}px`
      };

      document.addEventListener('click', this.handleDocumentClick, true);
      document.addEventListener('keydown', this.handleEscapePress);
    },
    closeColumnFilter() {
      this.activeFilterColumn = null;
      this.columnFilterSearch = '';
      this.columnFilterTempSelection = [];
      document.removeEventListener('click', this.handleDocumentClick, true);
      document.removeEventListener('keydown', this.handleEscapePress);
      this.lastFilterTrigger = null;
    },
    handleDocumentClick(event) {
      const popover = this.$refs.columnFilterPopover;
      const trigger = this.lastFilterTrigger;
      if (
        popover &&
        (popover === event.target || popover.contains(event.target))
      ) {
        return;
      }
      if (
        trigger &&
        (trigger === event.target || trigger.contains(event.target))
      ) {
        return;
      }
      if (!popover || !trigger) {
        this.closeColumnFilter();
        return;
      }
      this.closeColumnFilter();
    },
    handleEscapePress(event) {
      if (event.key === 'Escape') {
        this.closeColumnFilter();
      }
    },
    toggleSelectAllColumnFilter() {
      if (!this.activeFilterColumn) return;
      const optionValues = this.columnFilterOptions.map(option => option.value);
      if (this.isAllColumnFilterSelected) {
        this.columnFilterTempSelection = [];
      } else {
        this.columnFilterTempSelection = [...optionValues];
      }
      this.applyTempColumnFilter();
    },
    applyColumnFilter() {
      this.applyTempColumnFilter();
      this.closeColumnFilter();
    },
    clearColumnFilter() {
      if (!this.activeFilterColumn) return;
      this.columnFilterTempSelection = [];
      this.applyTempColumnFilter();
    },
    handleColumnFilterOptionChange() {
      this.applyTempColumnFilter();
    },
    applyTempColumnFilter() {
      if (!this.activeFilterColumn) return;
      const columnKey = this.activeFilterColumn.key;
      const optionValues = this.columnFilterOptions.map(option => option.value);
      const selected = this.columnFilterTempSelection.filter(value =>
        optionValues.includes(value)
      );

      const updatedFilters = { ...this.columnFilters };
      if (selected.length === 0 || selected.length === optionValues.length) {
        delete updatedFilters[columnKey];
      } else {
        updatedFilters[columnKey] = [...selected];
      }
      this.columnFilters = updatedFilters;
      this.currentPage = 1;
    },
    getColumnFilterOptions(column) {
      if (!column) return [];
      const valueMap = new Map();
      this.data.forEach(row => {
        const rawValue = row[column.key];
        const normalized = this.normalizeFilterValue(rawValue);
        if (!valueMap.has(normalized)) {
          valueMap.set(normalized, {
            value: normalized,
            label: this.formatFilterLabel(rawValue)
          });
        }
      });
      return Array.from(valueMap.values());
    },
    normalizeFilterValue(value) {
      if (value === null || value === undefined) {
        return '__NULL__';
      }
      if (typeof value === 'string') {
        const trimmed = value.trim();
        return trimmed === '' ? '__EMPTY__' : trimmed;
      }
      return String(value);
    },
    formatFilterLabel(value) {
      if (value === null || value === undefined) {
        return 'Not Specified';
      }
      if (typeof value === 'string') {
        const trimmed = value.trim();
        return trimmed === '' ? 'Empty' : trimmed;
      }
      return String(value);
    },
    formatHeaderLabel(label) {
      if (!label || typeof label !== 'string') {
        return label || '';
      }
      const lower = label.toLowerCase();
      return lower.charAt(0).toUpperCase() + lower.slice(1);
    },
    openColumnMenu(column, event) {
      if (!column || !event || !event.currentTarget) return;

      const triggerEl = event.currentTarget;
      this.lastMenuTrigger = triggerEl;
      const rect = triggerEl.getBoundingClientRect();
      const tableContainer = this.$el.querySelector('.table-wrapper');
      const containerRect = tableContainer
        ? tableContainer.getBoundingClientRect()
        : { top: 0, left: 0 };

      const headerRow = triggerEl.closest('th');
      const headerRect = headerRow ? headerRow.getBoundingClientRect() : rect;
      const top = headerRect.bottom - containerRect.top + 6;
      
      // Menu dimensions
      const menuWidth = 220;
      const submenuWidth = 180;
      const viewportWidth = window.innerWidth;
      const padding = 20;
      
      // Check if menu would overflow on the right
      const wouldOverflowRight = rect.right + menuWidth > viewportWidth - padding;
      
      // Position menu to the left if it would overflow
      let left;
      if (wouldOverflowRight) {
        // Align menu to the right edge of the trigger button
        left = rect.right - containerRect.left - menuWidth;
      } else {
        // Default: align to the left edge of the trigger button
        left = rect.left - containerRect.left;
      }
      
      // Ensure menu doesn't go off the left edge
      left = Math.max(padding - containerRect.left, left);
      
      // Check if submenu would overflow (menu is on right side)
      const menuRightEdge = rect.left + menuWidth;
      const submenuWouldOverflow = menuRightEdge + submenuWidth > viewportWidth - padding;
      this.shouldFlipSubmenu = submenuWouldOverflow || wouldOverflowRight;

      this.activeMenuColumn = column;
      this.showPinSubmenu = false;
      this.columnMenuPosition = {
        top: `${top}px`,
        left: `${left}px`
      };

      document.addEventListener('click', this.handleMenuDocumentClick, true);
      document.addEventListener('keydown', this.handleMenuEscapePress);
    },
    closeColumnMenu() {
      this.activeMenuColumn = null;
      this.showPinSubmenu = false;
      document.removeEventListener('click', this.handleMenuDocumentClick, true);
      document.removeEventListener('keydown', this.handleMenuEscapePress);
      this.lastMenuTrigger = null;
    },
    handleMenuDocumentClick(event) {
      const popover = this.$refs.columnMenuPopover;
      const trigger = this.lastMenuTrigger;
      if (
        popover &&
        (popover === event.target || popover.contains(event.target))
      ) {
        return;
      }
      if (
        trigger &&
        (trigger === event.target || trigger.contains(event.target))
      ) {
        return;
      }
      this.closeColumnMenu();
    },
    handleMenuEscapePress(event) {
      if (event.key === 'Escape') {
        this.closeColumnMenu();
      }
    },
    sortColumn(direction) {
      if (!this.activeMenuColumn || this.activeMenuColumn.sortable === false) return;
      
      console.log(`Sorting column: ${this.activeMenuColumn.label} (${this.activeMenuColumn.key}) in ${direction} order`);
      
      this.sortKey = this.activeMenuColumn.key;
      this.sortOrder = direction;
      
      console.log(`Sort state updated - Key: ${this.sortKey}, Order: ${this.sortOrder}`);
      
      this.$emit('sort-change', { key: this.sortKey, order: this.sortOrder });
      this.closeColumnMenu();
    },
    pinColumn(position) {
      if (!this.activeMenuColumn) return;
      const columnKey = this.activeMenuColumn.key;
      
      console.log(`Pinning column: ${this.activeMenuColumn.label} (${columnKey}) to position: ${position}`);
      
      // Create a new object to trigger reactivity
      const newPins = { ...this.columnPins };
      if (position === null) {
        delete newPins[columnKey];
      } else {
        newPins[columnKey] = position;
      }
      this.columnPins = newPins;
      
      console.log('Updated column pins:', this.columnPins);
      
      this.$emit('pin-column', { column: this.activeMenuColumn, position });
      this.closeColumnMenu();
    },
    autosizeColumn() {
      if (!this.activeMenuColumn) return;
      const columnKey = this.activeMenuColumn.key;
      
      console.log(`Autosizing column: ${this.activeMenuColumn.label} (${columnKey})`);
      
      // Calculate optimal width based on content
      let maxWidth = this.activeMenuColumn.label.length * 8 + 60; // Header width
      
      // Check content width
      this.data.forEach(row => {
        const value = String(row[columnKey] || '');
        const contentWidth = value.length * 8 + 30;
        if (contentWidth > maxWidth) {
          maxWidth = contentWidth;
        }
      });
      
      // Limit maximum width
      maxWidth = Math.min(maxWidth, 400);
      maxWidth = Math.max(maxWidth, 100);
      
      console.log(`Calculated width for ${columnKey}: ${maxWidth}px`);
      
      this.columnWidths[columnKey] = maxWidth;
      this.$emit('column-resize', { column: this.activeMenuColumn, width: maxWidth });
      this.closeColumnMenu();
    },
    autosizeAllColumns() {
      console.log('Autosizing all columns...');
      
      this.visibleColumns.forEach(column => {
        const columnKey = column.key;
        let maxWidth = column.label.length * 8 + 60;
        
        this.data.forEach(row => {
          const value = String(row[columnKey] || '');
          const contentWidth = value.length * 8 + 30;
          if (contentWidth > maxWidth) {
            maxWidth = contentWidth;
          }
        });
        
        maxWidth = Math.min(maxWidth, 400);
        maxWidth = Math.max(maxWidth, 100);
        
        this.columnWidths[columnKey] = maxWidth;
        console.log(`  ${column.label}: ${maxWidth}px`);
      });
      
      console.log('All columns autosized:', this.columnWidths);
      
      this.$emit('autosize-all-columns');
      this.closeColumnMenu();
    },
    openColumnChooser() {
      this.$emit('open-column-chooser');
      this.closeColumnMenu();
    },
    resetColumns() {
      console.log('Resetting all columns...');
      
      this.columnWidths = {};
      this.columnPins = {};
      this.sortKey = '';
      this.sortOrder = 'asc';
      
      console.log('Columns reset - All widths, pins, and sorting cleared');
      
      this.$emit('reset-columns');
      this.closeColumnMenu();
    }
  }
}
</script>

<style scoped>
.dynamic-table-container {
  background: transparent !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  border: none !important;
  padding: 0 !important;
  margin: 0 !important;
  overflow: visible !important;
  font-family: var(--font-family, inherit) !important;
}

.dynamic-table-container .table-wrapper {
  margin-top: 0 !important;
  position: relative;
}


/* Filters Section Above Table */
.filters-section-above {
  padding: 0 !important;
  margin: 0 0 5px 0 !important;
  display: flex !important;
  align-items: flex-start !important;
  box-shadow: none !important;
  border-radius: 0 !important;
  background: transparent !important;
  border: none !important;
  outline: none !important;
}

.filters-container {
  display: flex !important;
  gap: 16px !important;
  flex-wrap: nowrap !important;
  align-items: flex-start !important;
  box-shadow: none !important;
  border-radius: 0 !important;
  background: transparent !important;
  border: none !important;
  padding: 0 !important;
  margin: 0 !important;
  outline: none !important;
}

.filters-container > * {
  flex: 0 0 auto !important;
  min-width: 320px !important;
  max-width: 500px !important;
  width: auto !important;
  margin-right: 0 !important;
  margin-bottom: 0 !important;
}

.filters-container .filter-btn, .filters-container .CustomDropdown {
  min-width: 320px !important;
  max-width: 500px !important;
  width: 100% !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  height: 40px !important;
  line-height: 40px !important;
  display: flex !important;
  align-items: center !important;
}

.filters-container .dropdown-value {
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  max-width: 400px !important;
  display: inline-block !important;
}

.dynamic-table {
  width: 100%;
  border-collapse: collapse;
  background: #fefefe !important;
  font-family: var(--font-family, inherit);
  table-layout: fixed;
  border-radius: 6px !important;
  overflow: hidden !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
  border: 1px solid #9ca3af !important;
}

.dynamic-table th {
  padding: 8px 6px;
  text-align: left;
  font-weight: 700 !important;
  font-size: 10px;
  color: #374151 !important;
  border-right: 1px solid #e8e8e8 !important;
  border-left: none;
  border-top: none;
  border-bottom: 2px solid #e0e0e0 !important;
  white-space: nowrap;
  position: sticky;
  top: 0;
  z-index: 2;
  background: #f8f8f8 !important;
  font-family: var(--font-family, inherit);
  text-transform: none;
  letter-spacing: 0.02em;
  line-height: 1.2;
  width: auto;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dynamic-table th.pinned-left {
  position: sticky;
  left: 0;
  z-index: 3;
  background: #f0f4ff !important;
  box-shadow: 2px 0 4px rgba(0, 0, 0, 0.1);
}

.dynamic-table th.pinned-right {
  position: sticky;
  right: 0;
  z-index: 3;
  background: #f0f4ff !important;
  box-shadow: -2px 0 4px rgba(0, 0, 0, 0.1);
}

.dynamic-table td.pinned-left {
  position: sticky;
  left: 0;
  z-index: 1;
  background: #fcfcfc !important;
  box-shadow: 2px 0 4px rgba(0, 0, 0, 0.05);
}

.dynamic-table td.pinned-right {
  position: sticky;
  right: 0;
  z-index: 1;
  background: #fcfcfc !important;
  box-shadow: -2px 0 4px rgba(0, 0, 0, 0.05);
}

.dynamic-table-header-cell {
  position: relative;
}

.header-content {
  position: relative;
  display: flex;
  align-items: center;
  gap: 2px;
  min-height: 26px;
  padding-right: 0;
  width: 100%;
}

.header-label {
  flex: 1 1 0;
  display: inline-block;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
  cursor: default;
}

.sort-indicator {
  display: inline;
  color: #4f8cff;
  font-size: 10px;
  margin-left: 4px;
  vertical-align: middle;
}

.sort-indicator i {
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.dynamic-table-header-cell.is-sorted {
  background: #f0f4ff !important;
}

.header-icons {
  display: inline-flex;
  align-items: center;
  gap: 1px;
  border-left: 1px solid #d1d5db;
  padding-left: 3px;
  margin-left: 1px;
  flex-shrink: 0;
}

.header-icon-btn {
  background: transparent;
  border: none;
  color: #1f2937;
  cursor: pointer;
  padding: 1px !important;
  margin: 0 !important;
  border-radius: 2px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  transition: color 0.2s ease, background-color 0.2s ease;
  width: 18px;
  height: 18px;
}

.header-icon-btn:hover {
  color: #111827;
  background-color: rgba(107, 114, 128, 0.15);
}

.header-icon-btn:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(79, 140, 255, 0.3);
}

.header-icon-svg {
  width: 11px;
  height: 11px;
  display: block;
  color: inherit;
  padding: 0 !important;
  margin: 0 !important;
}

.column-filter-popover {
  position: absolute;
  z-index: 9999;
  background: #ffffff;
  border: 1px solid #d1d5db;
  border-radius: 10px;
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.18);
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 360px;
  backdrop-filter: blur(6px);
}

.column-filter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.column-filter-title {
  font-weight: 600;
  font-size: 14px;
  color: #111827;
}

.column-filter-close-btn {
  background: transparent;
  border: none;
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
  color: #6b7280;
  padding: 0;
}

.column-filter-close-btn:hover {
  color: #111827;
}

.column-filter-search input {
  width: 100%;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 6px 10px;
  font-size: 13px;
  color: #111827;
  outline: none;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.column-filter-search input:focus {
  border-color: #4f8cff;
  box-shadow: 0 0 0 2px rgba(79, 140, 255, 0.2);
}

.column-filter-select-all {
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 6px;
  margin-bottom: 4px;
}

.column-filter-select-all label,
.column-filter-option {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #1f2937;
}

.column-filter-options {
  flex: 1 1 auto;
  overflow-y: auto;
  max-height: 180px;
  padding-right: 4px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.column-filter-option input[type="checkbox"] {
  width: 14px;
  height: 14px;
}

.column-filter-empty {
  font-size: 12px;
  color: #6b7280;
  text-align: center;
  padding: 12px 0;
}

.column-filter-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 4px;
  border-top: 1px solid #e5e7eb;
}

.column-filter-btn {
  border: none;
  border-radius: 6px;
  padding: 6px 14px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.column-filter-btn.apply {
  background: #2563eb;
  color: #ffffff;
}

.column-filter-btn.apply:hover {
  background: #1d4ed8;
}

.column-filter-btn.clear {
  background: #e5e7eb;
  color: #1f2937;
}

.column-filter-btn.clear:hover {
  background: #d1d5db;
}

/* Column Menu Styles */
.column-menu-popover {
  position: absolute;
  z-index: 9999;
  background: #ffffff;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  min-width: 220px;
  padding: 6px 0;
  font-size: 14px;
}

.column-menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  color: #1f2937;
  cursor: pointer;
  transition: background-color 0.15s ease;
  position: relative;
  user-select: none;
}

.column-menu-item:hover {
  background-color: #f3f4f6;
}

.column-menu-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}

.column-menu-item i {
  width: 16px;
  text-align: center;
  color: #6b7280;
  font-size: 13px;
}

.column-menu-item span {
  flex: 1;
}

.column-menu-item.submenu-item {
  padding-left: 20px;
}

.column-menu-item-with-submenu {
  position: relative;
}

.submenu-arrow {
  margin-left: auto;
  font-size: 10px !important;
  color: #9ca3af !important;
}

.column-menu-submenu {
  position: absolute;
  right: auto;
  left: 100%;
  top: -6px;
  background: #ffffff;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  min-width: 180px;
  padding: 6px 0;
  margin-left: 4px;
  z-index: 10000;
}

/* When parent menu is on right side, position submenu to the left */
.column-menu-popover[style*="right"] .column-menu-submenu,
.column-menu-item-with-submenu.flip-submenu .column-menu-submenu {
  left: auto;
  right: 100%;
  margin-left: 0;
  margin-right: 4px;
}

/* Detect and flip submenu if it would overflow viewport */
@media (min-width: 1024px) {
  .column-menu-item-with-submenu:hover .column-menu-submenu {
    animation: fadeIn 0.15s ease;
  }
}

@keyframes fadeInSubmenu {
  from {
    opacity: 0;
    transform: translateX(-5px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.column-menu-divider {
  height: 1px;
  background-color: #e5e7eb;
  margin: 6px 0;
}

.invisible {
  visibility: hidden;
}

.dynamic-table td {
  padding: 10px 6px !important;
  border-bottom: 1px solid #e0e0e0;
  border-right: 1px solid #f5f5f5 !important;
  border-left: none;
  border-top: none;
  border-bottom: 1px solid #f0f0f0 !important;
  font-size: 12px !important;
  color: #374151 !important;
  font-family: var(--font-family, inherit);
  vertical-align: middle !important;
  height: auto;
  min-height: 42px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 500 !important;
  line-height: 1.4 !important;
  background: inherit !important;
  width: auto;
}

/* Table row styling */
.dynamic-table tbody tr {
  background: #fcfcfc !important;
  transition: all 0.2s !important;
}

.dynamic-table tbody tr:nth-child(even) {
  background: #fdfdfd !important;
}

.dynamic-table tbody tr:hover {
  background: #f9f9f9 !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
}

/* Specific styling for Risk Title column (1st column) */
.dynamic-table td:first-child,
.dynamic-table th:first-child {
  width: 20% !important;
}

.dynamic-table td:first-child {
  overflow: hidden !important;
  white-space: nowrap !important;
  text-overflow: ellipsis !important;
}

.dynamic-table td:first-child * {
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  display: inline !important;
}

/* Additional First Column Styling - Black Color */
.dynamic-table td:first-child {
  color: #1a1a1a !important;
  font-weight: 600 !important;
}

.dynamic-table tbody tr:hover {
  background: var(--dynamic-table-row-hover-bg, #f8f9fa);
}

/* Clickable row styling */
.dynamic-table-row {
  cursor: pointer;
  transition: all 0.2s ease;
}

.dynamic-table-row:hover {
  background: var(--dynamic-table-row-hover-bg, #f8f9fa);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}


/* Text cell with truncation */
.text-cell {
  width: 100%;
  overflow: hidden;
}

.cell-content {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-height: 24px;
  cursor: default;
}


.image-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.image-cell img {
  width: 32px;
  height: 32px;
  border-radius: 4px;
  object-fit: cover;
}

.status-cell .status {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
  font-family: var(--font-family, inherit);
}

.status-on-rent {
  background: var(--status-on-rent-bg, #dbeafe);
  color: var(--status-on-rent-text, #1e40af);
}

.status-on-sell {
  background: var(--status-on-sell-bg, #fef3c7);
  color: var(--status-on-sell-text, #d97706);
}

.status-renovation {
  background: var(--status-renovation-bg, #fce7f3);
  color: var(--status-renovation-text, #be185d);
}

.progress-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-bar-container {
  flex: 1;
  height: 8px;
  background: var(--progress-bar-container-bg, #e5e7eb);
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-bar-success {
  background-color: var(--progress-bar-success-bg, #10b981);
}
.progress-bar-warning {
  background-color: var(--progress-bar-warning-bg, #f59e0b);
}
.progress-bar-danger {
  background-color: var(--progress-bar-danger-bg, #ef4444);
}
.progress-bar-default {
  background-color: var(--progress-bar-default-bg, #6b7280);
}

.progress-value {
  font-size: 12px;
  color: #6b7280;
  min-width: 30px;
  text-align: right;
}

.actions-cell {
  text-align: center;
}

.action-dots {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  color: #6b7280;
  transition: background-color 0.2s;
}

.action-dots:hover {
  background: #f3f4f6;
}

.actions-column {
  width: 80px;
  text-align: center;
}

.pagination-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-top: 1px solid var(--dynamic-table-border-color, #dee2e6);
  background: var(--dynamic-table-pagination-bg, #f9fafb);
  font-family: var(--font-family, inherit);
}

.results-info {
  font-size: 14px;
  color: var(--dynamic-table-pagination-text-color, #6b7280);
}

.items-per-page-selector select {
  padding: 6px 12px;
  border: 1px solid var(--dynamic-table-pagination-btn-border, #d1d5db);
  border-radius: 6px;
  background: var(--dynamic-table-pagination-btn-bg, white);
  font-size: 14px;
  color: var(--dynamic-table-pagination-btn-text, #374151);
  font-family: var(--font-family, inherit);
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 4px;
}

.pagination-controls button {
  padding: 6px 12px;
  border: 1px solid var(--dynamic-table-pagination-btn-border, #d1d5db);
  background: var(--dynamic-table-pagination-btn-bg, white);
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  color: var(--dynamic-table-pagination-btn-text, #374151);
  transition: all 0.2s;
  font-family: var(--font-family, inherit);
}

.pagination-controls button:hover:not(:disabled) {
  background: var(--dynamic-table-pagination-btn-hover-bg, #f3f4f6);
  border-color: #9ca3af;
}

.pagination-controls button.active {
  background: var(--dynamic-table-pagination-btn-active-bg, #7B6FDD);
  border-color: var(--dynamic-table-pagination-btn-active-bg, #7B6FDD);
  color: var(--dynamic-table-pagination-btn-active-text, white);
}

.pagination-controls button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ellipsis {
  padding: 6px 8px;
  color: var(--dynamic-table-pagination-text-color, #6b7280);
}


@media (max-width: 768px) {
  .table-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
  
  .header-actions {
    width: 100%;
    flex-direction: column;
    gap: 12px;
  }
  
  .filters-container {
    width: 100%;
    flex-wrap: wrap;
  }
  
  .pagination-container {
    flex-direction: column;
    gap: 16px;
  }
  
  .dynamic-table td {
    padding: 8px 10px;
    font-size: 13px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .dynamic-table th {
    padding: 8px 10px;
    font-size: 13px;
    white-space: nowrap;
  }
  
  .cell-content {
    font-size: 12px;
    line-height: 1.3;
  }
}

@media (max-width: 900px) {
  .filters-section-above {
    flex-direction: column;
    align-items: stretch;
  }
  .filters-container {
    flex-wrap: wrap;
    gap: 12px;
  }
  .filters-container > * {
    max-width: 100%;
  }
}

.dynamic-table .dropdown-menu {
  z-index: 99999 !important;
  position: absolute !important;
}
.table-wrapper {
  width: 100%;
  overflow-x: hidden;
  overflow-y: visible;
  max-width: 100%;
}

/* Additional text overflow improvements */
.dynamic-table td > * {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dynamic-table td span,
.dynamic-table td div,
.dynamic-table td button,
.dynamic-table td select {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}
</style> 