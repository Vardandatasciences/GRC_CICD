<template>
  <div class="kpi-dashboard-container">
    <!-- Header Section -->
    <div class="kpi-dashboard-header">
      <div class="kpi-dashboard-header-left">
        <h2 class="kpi-dashboard-heading">KPI Dashboard</h2>
      </div>
      <div class="kpi-dashboard-actions">
        <button @click="refreshKPIs" class="kpi-action-btn refresh">
          <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
          Refresh
        </button>
      </div>
    </div>
    
    <p class="kpi-dashboard-subtitle">Monitor key performance indicators across all modules</p>

    <!-- Filters Section -->
    <div class="kpi-filters-section">
      <div class="kpi-dashboard-filters">
        <div class="kpi-filter-group">
          <label>Framework</label>
          <select v-model="selectedFramework" @change="filterKPIs" class="kpi-filter-select">
            <option value="">All Frameworks</option>
            <option v-for="framework in availableFrameworksWithKPIs" :key="framework.FrameworkId" :value="framework.FrameworkId">
              {{ framework.FrameworkName }}
            </option>
          </select>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="kpi-loading-container">
      <div class="loading-spinner"></div>
      <span>Loading KPIs...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="kpi-error-container">
      <i class="fas fa-exclamation-triangle"></i>
      <p>{{ error }}</p>
      <button @click="refreshKPIs" class="kpi-retry-btn">Try Again</button>
    </div>

    <!-- KPI Charts Grid -->
    <div v-else-if="validKPIs.length > 0" class="kpi-charts-grid">
      <div v-for="kpi in validKPIs" :key="kpi.id" class="kpi-chart-card">
        <div class="kpi-card-header">
          <div class="kpi-header-content">
            <h3>{{ kpi.name }}</h3>
          </div>
          <p v-if="kpi.description" class="kpi-description">{{ kpi.description }}</p>
        </div>

        <!-- Chart Display based on DisplayType -->
        <div class="kpi-chart-wrapper">
          <!-- Number Display (only for single numeric values) -->
          <div v-if="(kpi.displayType === 'Number' || kpi.displayType === 'Numeric') && !isArrayData(kpi.value)" class="kpi-number-display">
            <div class="number-highlight">
              <span class="number-value">{{ formatValue(kpi.value, kpi.dataType) }}</span>
            </div>
            <div class="number-sparkline">
              <span></span>
            </div>
            <div v-if="kpi.dataType" class="number-label">{{ kpi.dataType }}</div>
          </div>

          <!-- Percentage Display (only for single percentage values) -->
          <div v-else-if="(kpi.displayType === 'Percentage' || kpi.displayType === 'Ratio') && !isArrayData(kpi.value)" class="kpi-percentage-display">
            <div class="percentage-circle">
              <svg viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="45" class="circle-bg"></circle>
                <circle 
                  cx="50" 
                  cy="50" 
                  r="45" 
                  class="circle-progress"
                  :style="{ strokeDashoffset: calculateStrokeDashoffset(kpi.value) }"
                ></circle>
              </svg>
              <div class="percentage-text">{{ formatPercentage(kpi.value) }}%</div>
            </div>
          </div>

          <!-- Gauge Chart -->
          <div v-else-if="kpi.displayType === 'Gauge' || kpi.displayType === 'Gauge Chart'" class="kpi-gauge-display">
            <canvas :id="'chart-' + kpi.id" class="chart-canvas"></canvas>
          </div>

          <!-- Line Chart -->
          <div v-else-if="kpi.displayType === 'Line Chart' || kpi.displayType === 'Line'" class="kpi-line-display">
            <canvas :id="'chart-' + kpi.id" class="chart-canvas"></canvas>
          </div>

          <!-- Bar Chart -->
          <div v-else-if="kpi.displayType === 'Bar Chart' || kpi.displayType === 'Bar'" class="kpi-bar-chart-display">
            <canvas :id="'chart-' + kpi.id" class="chart-canvas"></canvas>
          </div>

          <!-- Pie Chart -->
          <div v-else-if="kpi.displayType === 'Pie Chart' || kpi.displayType === 'Pie'" class="kpi-pie-display">
            <canvas :id="'chart-' + kpi.id" class="chart-canvas"></canvas>
          </div>

          <!-- Doughnut Chart -->
          <div v-else-if="kpi.displayType === 'Doughnut' || kpi.displayType === 'Donut'" class="kpi-doughnut-display">
            <canvas :id="'chart-' + kpi.id" class="chart-canvas"></canvas>
          </div>

          <!-- Radar Chart -->
          <div v-else-if="kpi.displayType === 'Radar' || kpi.displayType === 'Radar Chart'" class="kpi-radar-display">
            <canvas :id="'chart-' + kpi.id" class="chart-canvas"></canvas>
          </div>

          <!-- Polar Area Chart -->
          <div v-else-if="kpi.displayType === 'Polar' || kpi.displayType === 'Polar Area'" class="kpi-polar-display">
            <canvas :id="'chart-' + kpi.id" class="chart-canvas"></canvas>
          </div>

          <!-- Table Display -->
          <div v-else-if="kpi.displayType === 'Table' && parseTableData(kpi.value)" class="kpi-table-display">
            <div class="kpi-table-wrapper">
              <table class="kpi-table">
                <thead>
                  <tr>
                    <th v-for="header in getTableHeaders(parseTableData(kpi.value))" :key="header">
                      {{ header }}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, index) in parseTableData(kpi.value)" :key="index">
                    <td v-for="header in getTableHeaders(parseTableData(kpi.value))" :key="header">
                      {{ row[header] }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Simple Bar Display (for single values) -->
          <div v-else-if="kpi.displayType === 'Progress Bar' && !isArrayData(kpi.value)" class="kpi-bar-display">
            <div class="bar-wrapper">
              <div class="bar-fill" :style="{ width: formatPercentage(kpi.value) + '%' }"></div>
            </div>
            <div class="bar-value">{{ formatValue(kpi.value, kpi.dataType) }}</div>
          </div>

          <!-- Decimal Display (only for single decimal values) -->
          <div v-else-if="kpi.displayType === 'Decimal' && !isArrayData(kpi.value)" class="kpi-decimal-display">
            <div class="decimal-value">{{ parseFloat(kpi.value).toFixed(2) }}</div>
          </div>

          <!-- Auto-detect chart type for arrays - NO RAW DATA DISPLAY -->
          <div v-else-if="isArrayData(kpi.value)" class="kpi-line-display">
            <canvas :id="'chart-' + kpi.id" class="chart-canvas"></canvas>
          </div>

          <!-- Fallback for single values without specific display type -->
          <div v-else-if="!isArrayData(kpi.value)" class="kpi-number-display">
            <div class="number-highlight">
              <span class="number-value">{{ formatValue(kpi.value, kpi.dataType) }}</span>
            </div>
            <div class="number-sparkline">
              <span></span>
            </div>
          </div>

          <!-- Ultimate fallback (should never reach here) -->
          <div v-else class="kpi-error-display">
            <i class="fas fa-chart-line"></i>
            <p>Unable to visualize data</p>
          </div>
        </div>

        <!-- KPI Footer -->
        <div class="kpi-card-footer">
          <span v-if="kpi.frameworkName" class="kpi-framework-tag">
            <i class="fas fa-sitemap"></i>
            {{ kpi.frameworkName }}
          </span>
          <span v-if="kpi.updatedAt" class="kpi-updated-tag">
            <i class="fas fa-clock"></i>
            {{ formatDate(kpi.updatedAt) }}
          </span>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="kpi-empty-state">
      <i class="fas fa-chart-bar"></i>
      <h3>No KPIs Found</h3>
      <p>There are no KPIs available for the selected filters.</p>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed, nextTick, watch } from 'vue';
import axios from 'axios';
import { API_ENDPOINTS } from '../../config/api.js';
import { Chart, registerables } from 'chart.js';
import { useStore } from 'vuex';

// Register all Chart.js components
Chart.register(...registerables);

export default {
  name: 'KPIDashboard',
  setup() {
    const store = useStore();
    const kpis = ref([]);
    const frameworks = ref([]);
    const selectedFramework = ref('');
    const loading = ref(false);
    const error = ref(null);
    const chartInstances = ref({});

    // Computed filtered KPIs
    const filteredKPIs = computed(() => {
      let filtered = kpis.value;
      
      if (selectedFramework.value) {
        filtered = filtered.filter(kpi => kpi.frameworkId == selectedFramework.value);
      }
      
      return filtered;
    });

    // Computed frameworks that have KPI data
    const availableFrameworksWithKPIs = computed(() => frameworks.value);

    // Check if value has valid data (not N/A, null, or invalid)
    const hasValidData = (value) => {
      if (!value || value === 'N/A' || value === 'null') return false;
      
      try {
        const parsed = typeof value === 'string' ? JSON.parse(value) : value;
        
        // Check if it's an empty array or object
        if (Array.isArray(parsed) && parsed.length === 0) return false;
        if (typeof parsed === 'object' && Object.keys(parsed).length === 0) return false;
        
        return true;
      } catch (e) {
        // If it's not JSON, check if it's a valid number or string
        return value !== '' && value !== 'undefined';
      }
    };

    // Computed valid KPIs (filtered + valid data only)
    const validKPIs = computed(() => {
      return filteredKPIs.value.filter(kpi => hasValidData(kpi.value));
    });

    // Parse KPI value - handle JSON arrays and objects for charts
    const parseKPIValue = (value) => {
      if (!value) return null;
      
      try {
        // Try to parse as JSON (for arrays and objects)
        const parsed = JSON.parse(value);
        return parsed;
      } catch (e) {
        // If not JSON, try to convert string to number
        const numValue = parseFloat(value);
        if (!isNaN(numValue)) {
          return numValue;
        }
        // If not JSON or number, return as is
        return value;
      }
    };

    // Check if value is an object (dictionary) that needs to be converted to chart
    const isObjectData = (value) => {
      if (!value) return false;
      
      try {
        const parsed = typeof value === 'string' ? JSON.parse(value) : value;
        return typeof parsed === 'object' && !Array.isArray(parsed) && parsed !== null;
      } catch (e) {
        return false;
      }
    };

    // Convert object to array for charting
    const objectToChartData = (value) => {
      try {
        const parsed = typeof value === 'string' ? JSON.parse(value) : value;
        if (typeof parsed === 'object' && !Array.isArray(parsed)) {
          // Convert object to arrays for labels and data
          const labels = Object.keys(parsed);
          const data = Object.values(parsed);
          return { labels, data };
        }
      } catch (e) {
        console.error('Error converting object to chart data:', e);
      }
      return null;
    };

    // Destroy a chart instance if it exists for a canvas
    const destroyChartForCanvas = (canvas) => {
      if (!canvas) return;
      const existing = Chart.getChart(canvas);
      if (existing) {
        existing.destroy();
      }
    };

    // Destroy all chart instances we are tracking
    const destroyCharts = () => {
      Object.values(chartInstances.value).forEach(chart => {
        if (chart) {
          chart.destroy();
        }
      });
      chartInstances.value = {};
    };

    // Create Line Chart
    const createLineChart = (canvasId, data) => {
      const canvas = document.getElementById(canvasId);
      if (!canvas) return;

      destroyChartForCanvas(canvas);

      const ctx = canvas.getContext('2d');
      
      // Parse data if it's a string
      const parsedData = typeof data === 'string' ? parseKPIValue(data) : data;
      const chartData = Array.isArray(parsedData) ? parsedData : [parsedData];
      
      // Generate labels
      const labels = chartData.map((_, i) => `Point ${i + 1}`);

      chartInstances.value[canvasId] = new Chart(ctx, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [{
            label: 'Value',
            data: chartData,
            borderColor: '#4f6cff',
            backgroundColor: 'rgba(79, 108, 255, 0.1)',
            borderWidth: 3,
            tension: 0.4,
            fill: true,
            pointRadius: 4,
            pointHoverRadius: 6,
            pointBackgroundColor: '#4f6cff',
            pointBorderColor: '#fff',
            pointBorderWidth: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              backgroundColor: 'rgba(255, 255, 255, 0.9)',
              titleColor: '#1f2937',
              bodyColor: '#4b5563',
              borderColor: '#e5e7eb',
              borderWidth: 1,
              padding: 12,
              displayColors: false
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              grid: {
                color: 'rgba(0, 0, 0, 0.05)'
              },
              ticks: {
                color: '#6b7280',
                font: {
                  size: 11
                }
              }
            },
            x: {
              grid: {
                display: false
              },
              ticks: {
                color: '#6b7280',
                font: {
                  size: 11
                }
              }
            }
          }
        }
      });
    };

    // Create Bar Chart
    const createBarChart = (canvasId, data) => {
      const canvas = document.getElementById(canvasId);
      if (!canvas) return;

      destroyChartForCanvas(canvas);

      const ctx = canvas.getContext('2d');
      
      const parsedData = typeof data === 'string' ? parseKPIValue(data) : data;
      
      // Check if it's an object (dictionary) - convert to chart data
      let chartData, labels;
      if (isObjectData(data)) {
        const converted = objectToChartData(data);
        if (converted) {
          labels = converted.labels;
          chartData = converted.data;
        } else {
          return; // Can't chart this data
        }
      } else {
        chartData = Array.isArray(parsedData) ? parsedData : [parsedData];
        labels = chartData.map((_, i) => `Item ${i + 1}`);
      }

      chartInstances.value[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{
            label: 'Value',
            data: chartData,
            backgroundColor: 'rgba(79, 108, 255, 0.8)',
            borderColor: '#4f6cff',
            borderWidth: 2,
            borderRadius: 8,
            borderSkipped: false
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              backgroundColor: 'rgba(255, 255, 255, 0.9)',
              titleColor: '#1f2937',
              bodyColor: '#4b5563',
              borderColor: '#e5e7eb',
              borderWidth: 1,
              padding: 12,
              displayColors: false
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              grid: {
                color: 'rgba(0, 0, 0, 0.05)'
              },
              ticks: {
                color: '#6b7280',
                font: {
                  size: 11
                }
              }
            },
            x: {
              grid: {
                display: false
              },
              ticks: {
                color: '#6b7280',
                font: {
                  size: 11
                },
                maxRotation: 45,
                minRotation: 0
              }
            }
          }
        }
      });
    };

    // Create Pie/Doughnut Chart
    const createPieChart = (canvasId, data, isDoughnut = false) => {
      const canvas = document.getElementById(canvasId);
      if (!canvas) return;

      destroyChartForCanvas(canvas);

      const ctx = canvas.getContext('2d');
      
      const parsedData = typeof data === 'string' ? parseKPIValue(data) : data;
      
      // Check if it's an object (dictionary) - convert to chart data
      let chartData, labels;
      if (isObjectData(data)) {
        const converted = objectToChartData(data);
        if (converted) {
          labels = converted.labels;
          chartData = converted.data;
        } else {
          return; // Can't chart this data
        }
      } else {
        chartData = Array.isArray(parsedData) ? parsedData : [parsedData];
        labels = chartData.map((_, i) => `Segment ${i + 1}`);
      }

      const colors = [
        '#4f6cff', '#60a5fa', '#4ade80', '#fbbf24', 
        '#f87171', '#a78bfa', '#fb923c', '#ec4899'
      ];

      chartInstances.value[canvasId] = new Chart(ctx, {
        type: isDoughnut ? 'doughnut' : 'pie',
        data: {
          labels: labels,
          datasets: [{
            data: chartData,
            backgroundColor: colors.slice(0, chartData.length),
            borderColor: '#ffffff',
            borderWidth: 3,
            hoverOffset: 8
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom',
              labels: {
                padding: 15,
                font: {
                  size: 11
                },
                color: '#4b5563',
                usePointStyle: true,
                pointStyle: 'circle'
              }
            },
            tooltip: {
              backgroundColor: 'rgba(255, 255, 255, 0.9)',
              titleColor: '#1f2937',
              bodyColor: '#4b5563',
              borderColor: '#e5e7eb',
              borderWidth: 1,
              padding: 12
            }
          },
          cutout: isDoughnut ? '65%' : 0
        }
      });
    };

    // Create Gauge Chart (using Doughnut)
    const createGaugeChart = (canvasId, value) => {
      const canvas = document.getElementById(canvasId);
      if (!canvas) return;

      destroyChartForCanvas(canvas);

      const ctx = canvas.getContext('2d');
      const numValue = parseFloat(value) || 0;
      const maxValue = 100;
      const percentage = Math.min(Math.max(numValue, 0), maxValue);

      // Determine color based on value
      let gaugeColor = '#4ade80'; // Green
      if (percentage < 30) {
        gaugeColor = '#f87171'; // Red
      } else if (percentage < 70) {
        gaugeColor = '#fbbf24'; // Yellow
      }

      chartInstances.value[canvasId] = new Chart(ctx, {
        type: 'doughnut',
        data: {
          datasets: [{
            data: [percentage, maxValue - percentage],
            backgroundColor: [gaugeColor, '#e5e7eb'],
            borderWidth: 0,
            circumference: 180,
            rotation: 270
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: '75%',
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              enabled: false
            }
          }
        },
        plugins: [{
          id: 'gaugeText',
          afterDraw: (chart) => {
            const { ctx, chartArea: { width, height } } = chart;
            ctx.save();
            
            // Draw percentage text
            ctx.font = 'bold 32px Inter, sans-serif';
            ctx.fillStyle = '#1f2937';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(`${percentage.toFixed(1)}%`, width / 2, height / 2 + 10);
            
            ctx.restore();
          }
        }]
      });
    };

    // Create Radar Chart
    const createRadarChart = (canvasId, data) => {
      const canvas = document.getElementById(canvasId);
      if (!canvas) return;

      destroyChartForCanvas(canvas);

      const ctx = canvas.getContext('2d');
      
      const parsedData = typeof data === 'string' ? parseKPIValue(data) : data;
      const chartData = Array.isArray(parsedData) ? parsedData : [parsedData];
      const labels = chartData.map((_, i) => `Metric ${i + 1}`);

      chartInstances.value[canvasId] = new Chart(ctx, {
        type: 'radar',
        data: {
          labels: labels,
          datasets: [{
            label: 'Value',
            data: chartData,
            backgroundColor: 'rgba(79, 108, 255, 0.2)',
            borderColor: '#4f6cff',
            borderWidth: 2,
            pointBackgroundColor: '#4f6cff',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: '#4f6cff',
            pointRadius: 4,
            pointHoverRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            }
          },
          scales: {
            r: {
              beginAtZero: true,
              grid: {
                color: 'rgba(0, 0, 0, 0.05)'
              },
              ticks: {
                color: '#6b7280',
                font: {
                  size: 10
                }
              },
              pointLabels: {
                color: '#4b5563',
                font: {
                  size: 11
                }
              }
            }
          }
        }
      });
    };

    // Create Polar Area Chart
    const createPolarChart = (canvasId, data) => {
      const canvas = document.getElementById(canvasId);
      if (!canvas) return;

      destroyChartForCanvas(canvas);

      const ctx = canvas.getContext('2d');
      
      const parsedData = typeof data === 'string' ? parseKPIValue(data) : data;
      const chartData = Array.isArray(parsedData) ? parsedData : [parsedData];
      const labels = chartData.map((_, i) => `Area ${i + 1}`);

      const colors = [
        'rgba(79, 108, 255, 0.7)', 'rgba(96, 165, 250, 0.7)', 
        'rgba(74, 222, 128, 0.7)', 'rgba(251, 191, 36, 0.7)',
        'rgba(248, 113, 113, 0.7)', 'rgba(167, 139, 250, 0.7)'
      ];

      chartInstances.value[canvasId] = new Chart(ctx, {
        type: 'polarArea',
        data: {
          labels: labels,
          datasets: [{
            data: chartData,
            backgroundColor: colors.slice(0, chartData.length),
            borderColor: '#ffffff',
            borderWidth: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom',
              labels: {
                padding: 12,
                font: {
                  size: 11
                },
                color: '#4b5563',
                usePointStyle: true
              }
            }
          },
          scales: {
            r: {
              beginAtZero: true,
              grid: {
                color: 'rgba(0, 0, 0, 0.05)'
              },
              ticks: {
                color: '#6b7280',
                font: {
                  size: 10
                }
              }
            }
          }
        }
      });
    };

    // Render all charts
    const renderCharts = async () => {
      await nextTick();
      
      // Destroy existing charts
      destroyCharts();

      // Wait a bit for DOM to update
      setTimeout(() => {
        validKPIs.value.forEach(kpi => {
          const displayType = kpi.displayType?.toLowerCase();
          const canvasId = `chart-${kpi.id}`;
          
          // Check if this is array/object data that needs visualization
          const isArray = isArrayData(kpi.value);
          const isObject = isObjectData(kpi.value);
          
          // Determine chart type
          let chartType = displayType;
          if ((isArray || isObject) && (!displayType || displayType === 'number' || displayType === 'numeric' || 
              displayType === 'percentage' || displayType === 'decimal' || displayType === 'ratio')) {
            chartType = determineChartType(kpi.value, displayType);
          }
          
          // Render appropriate chart
          if (chartType === 'line chart' || chartType === 'line') {
            createLineChart(canvasId, kpi.value);
          } else if (chartType === 'bar chart' || chartType === 'bar') {
            createBarChart(canvasId, kpi.value);
          } else if (chartType === 'pie chart' || chartType === 'pie') {
            createPieChart(canvasId, kpi.value, false);
          } else if (chartType === 'doughnut' || chartType === 'donut') {
            createPieChart(canvasId, kpi.value, true);
          } else if (chartType === 'gauge' || chartType === 'gauge chart') {
            createGaugeChart(canvasId, kpi.value);
          } else if (chartType === 'radar' || chartType === 'radar chart') {
            createRadarChart(canvasId, kpi.value);
          } else if (chartType === 'polar' || chartType === 'polar area') {
            createPolarChart(canvasId, kpi.value);
          } else if (isArray) {
            // Fallback for any array data without specific type - use line chart
            createLineChart(canvasId, kpi.value);
          } else if (isObject) {
            // Fallback for any object data without specific type - use doughnut chart
            createPieChart(canvasId, kpi.value, true);
          }
        });
      }, 100);
    };

    // Fetch all KPIs
    const fetchKPIs = async () => {
      loading.value = true;
      error.value = null;
      
      try {
        const response = await axios.get(API_ENDPOINTS.KPIS_ALL);
        
        if (response.data.status === 'success') {
          kpis.value = response.data.data;
          
          // Wait for DOM update then render charts
          await nextTick();
          renderCharts();
        } else {
          error.value = 'Failed to load KPIs';
        }
      } catch (err) {
        console.error('Error fetching KPIs:', err);
        error.value = 'Error loading KPIs. Please try again.';
      } finally {
        loading.value = false;
      }
    };

    // Fetch frameworks
    const fetchFrameworks = async () => {
      try {
        const response = await axios.get(API_ENDPOINTS.KPIS_FRAMEWORKS);
        if (response.data.status === 'success') {
          frameworks.value = response.data.data;
          applyGlobalFrameworkSelection();
        }
      } catch (err) {
        console.error('Error fetching frameworks:', err);
      }
    };

    // Filter KPIs
    const filterKPIs = () => {
      renderCharts();
    };

    // Refresh KPIs
    const refreshKPIs = () => {
      fetchKPIs();
    };

    // Format value based on data type
    const formatValue = (value, dataType) => {
      if (!value) return 'N/A';
      
      if (dataType === 'Numeric' || dataType === 'Number') {
        const num = parseFloat(value);
        return isNaN(num) ? value : num.toLocaleString();
      } else if (dataType === 'Decimal') {
        const num = parseFloat(value);
        return isNaN(num) ? value : num.toFixed(2);
      } else if (dataType === 'Percentage' || dataType === 'Ratio') {
        const num = parseFloat(value);
        return isNaN(num) ? value : num.toFixed(1) + '%';
      }
      
      return value;
    };

    // Format percentage
    const formatPercentage = (value) => {
      if (!value) return 0;
      const num = parseFloat(value);
      return Math.min(Math.max(num, 0), 100).toFixed(1);
    };

    // Calculate stroke dash offset for circular progress
    const calculateStrokeDashoffset = (value) => {
      const percentage = parseFloat(value) || 0;
      const circumference = 2 * Math.PI * 45;
      const offset = circumference - (percentage / 100) * circumference;
      return offset;
    };

    // Format date
    const formatDate = (dateString) => {
      if (!dateString) return '';
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
      });
    };

    // Parse table data
    const parseTableData = (value) => {
      try {
        const parsed = JSON.parse(value);
        if (Array.isArray(parsed) && parsed.length > 0 && typeof parsed[0] === 'object') {
          return parsed;
        }
      } catch (e) {
        // Not valid JSON table data
      }
      return null;
    };

    // Get table headers
    const getTableHeaders = (tableData) => {
      if (!tableData || tableData.length === 0) return [];
      return Object.keys(tableData[0]);
    };

    // Check if value is array data (needs to be visualized as chart)
    const isArrayData = (value) => {
      if (!value) return false;
      
      // Try to parse if it's a string
      try {
        const parsed = typeof value === 'string' ? JSON.parse(value) : value;
        // Return true for both arrays and objects (dictionaries)
        return (Array.isArray(parsed) && parsed.length > 1) || 
               (typeof parsed === 'object' && parsed !== null && Object.keys(parsed).length > 1);
      } catch (e) {
        return false;
      }
    };

    // Determine best chart type for array/object data
    const determineChartType = (value, displayType) => {
      // If display type is specified, use it
      if (displayType && displayType !== 'Number' && displayType !== 'Numeric' && 
          displayType !== 'Percentage' && displayType !== 'Decimal' && displayType !== 'Ratio') {
        return displayType.toLowerCase();
      }

      // Auto-detect based on data characteristics
      const parsed = parseKPIValue(value);
      
      // Handle object data (dictionaries)
      if (isObjectData(value)) {
        const converted = objectToChartData(value);
        if (converted && converted.data) {
          const dataLength = converted.data.length;
          // Small dictionaries work great as doughnut/pie charts
          if (dataLength <= 5) {
            return 'doughnut';
          }
          // Medium size dictionaries as bar charts
          return 'bar';
        }
      }

      // Handle array data
      if (!Array.isArray(parsed)) return 'number';

      const dataLength = parsed.length;
      
      // For very long series (time series data), use line chart
      if (dataLength > 20) {
        return 'line';
      }
      
      // For medium length, check if values are mostly positive (use area/bar)
      if (dataLength > 5 && dataLength <= 20) {
        return 'bar';
      }
      
      // For small arrays, use pie/doughnut if all positive
      if (dataLength <= 5) {
        const allPositive = parsed.every(val => typeof val === 'number' && val >= 0);
        if (allPositive) {
          return 'doughnut';
        }
      }
      
      // Default to line chart for mixed data
      return 'line';
    };

    // Watch for valid KPIs changes (triggers when filtered or data changes)
    watch(validKPIs, () => {
      renderCharts();
    });

    const applyGlobalFrameworkSelection = () => {
      const framework = store.getters['framework/selectedFramework'];
      const frameworkId = framework?.id && framework.id !== 'all' ? framework.id : '';
      if (selectedFramework.value !== frameworkId) {
        selectedFramework.value = frameworkId;
        filterKPIs();
      }
    };

    const handleFrameworkChanged = (event) => {
      const { id } = event.detail || {};
      const frameworkId = id && id !== 'all' ? id : '';
      if (selectedFramework.value !== frameworkId) {
        selectedFramework.value = frameworkId;
        filterKPIs();
      }
    };

    // Initialize
    onMounted(() => {
      fetchKPIs();
      fetchFrameworks();
      applyGlobalFrameworkSelection();
      window.addEventListener('framework-changed', handleFrameworkChanged);
    });

    onUnmounted(() => {
      window.removeEventListener('framework-changed', handleFrameworkChanged);
    });

    return {
      kpis,
      frameworks,
      availableFrameworksWithKPIs,
      selectedFramework,
      loading,
      error,
      filteredKPIs,
      validKPIs,
      filterKPIs,
      refreshKPIs,
      formatValue,
      formatPercentage,
      calculateStrokeDashoffset,
      formatDate,
      parseTableData,
      getTableHeaders,
      isArrayData,
      hasValidData
    };
  }
};
</script>

<style scoped src="./kpi.css"></style>

