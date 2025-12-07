<template>
  <div class="kpi-dashboard" :class="{ 'fullscreen': isFullscreen }">
    <!-- Framework Filter Section -->
    <div class="framework-filter-section">
      <div class="filter-header">
        <h2 class="filter-title">Compliance KPI Dashboard</h2>
        <div class="framework-filter-group">
          <label for="framework-select" class="framework-label">Framework:</label>
          <select 
            id="framework-select"
            v-model="selectedFrameworkId" 
            @change="handleFrameworkChange"
            class="framework-select"
          >
            <option value="">All Frameworks</option>
            <option 
              v-for="framework in filteredFrameworks" 
              :key="framework.id" 
              :value="framework.id"
            >
              {{ framework.name }}
            </option>
          </select>
        </div>
      </div>
    </div>

    <!-- Fullscreen Toggle Button -->
    <div class="fullscreen-controls">
      <button 
        @click="toggleFullscreen" 
        class="fullscreen-toggle"
        :title="isFullscreen ? 'Exit Fullscreen' : 'Enter Fullscreen'"
      >
        <span v-if="!isFullscreen">⛶</span>
        <span v-else>⛶</span>
        {{ isFullscreen ? 'Exit Fullscreen' : 'Fullscreen' }}
      </button>
    </div>

    <!-- Two Section Layout: Charts (Left) + Numbers (Right) -->
    <div class="kpi-sections">
      <!-- Left Section: Charts -->
      <div class="charts-section">
        <!-- Maturity Level Chart -->
        <div class="kpi-card maturity-card">
          <div class="kpi-header">
            <h3 class="kpi-title">Maturity Level Distribution</h3>
          </div>

          <div v-if="error" class="error-message">
            {{ error }}
            <button @click="fetchMaturityData">Retry</button>
          </div>

          <div v-else>
            <div class="kpi-chart">
              <Bar
                v-if="chartData && chartData.datasets && chartData.datasets.length && chartData.labels && chartData.labels.length"
                :data="chartData"
                :options="chartOptions"
              />
            </div>

            <div class="maturity-grid">
              <div 
                v-for="level in maturityLevels" 
                :key="level"
                class="maturity-item"
              >
                <div class="maturity-color" :class="level.toLowerCase()"></div>
                <span class="maturity-label">{{ level }}</span>
                <span class="maturity-count">{{ getMaturityCount(level) }}</span>
              </div>
            </div>

            <div class="total-count">
              Total Active & Approved: {{ getTotalCompliances() }}
            </div>
          </div>
        </div>



        <!-- On-Time Mitigation Rate -->
        <div class="kpi-card ontime-mitigation-card">
          <div class="kpi-header">
            <h3 class="kpi-title">On-Time Mitigation Rate</h3>
          </div>

          <div v-if="ontimeMitigationError" class="error-message">
            {{ ontimeMitigationError }}
            <button @click="fetchOntimeMitigationData">Retry</button>
          </div>

          <div v-else class="ontime-mitigation-content">
            <div class="ontime-percentage-circle" :class="{ 'high-rate': ontimeMitigationData.on_time_percentage >= 70 }">
              <div class="percentage-value">{{ Math.round(ontimeMitigationData.on_time_percentage) }}%</div>
              <div class="percentage-label">On Time</div>
            </div>
            
            <div class="ontime-stats">
              <div class="ontime-stat-item">
                <div class="stat-value">{{ ontimeMitigationData.completed_on_time }}</div>
                <div class="stat-label">On Time</div>
              </div>
              <div class="ontime-stat-item">
                <div class="stat-value">{{ ontimeMitigationData.completed_late }}</div>
                <div class="stat-label">Late</div>
              </div>
              <div class="ontime-stat-item">
                <div class="stat-value">{{ ontimeMitigationData.total_completed }}</div>
                <div class="stat-label">Total</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Non-Compliance Repetitions Chart -->
        <div class="kpi-card repetitions-card">
          <div class="kpi-header">
            <h3 class="kpi-title">Non-Compliance Repetitions</h3>
          </div>

          <div v-if="repetitionsError" class="error-message">
            {{ repetitionsError }}
            <button @click="fetchRepetitionsData">Retry</button>
          </div>

          <div v-else>
            <div class="repetitions-chart-container">
              <Bar
                v-if="repetitionsChartData && repetitionsChartData.datasets && repetitionsChartData.datasets.length && repetitionsChartData.labels && repetitionsChartData.labels.length"
                :data="repetitionsChartData"
                :options="repetitionsChartOptions"
              />
            </div>
            <div class="repetitions-stats">
              <div class="repetition-stat-item">
                <div class="repetition-stat-value">
                  {{ repetitionsData.total_items }}
                </div>
                <div class="repetition-stat-label">
                  Total Items
                </div>
              </div>
              <div class="repetition-stat-item">
                <div class="repetition-stat-value">
                  {{ repetitionsData.max_repetitions }}
                </div>
                <div class="repetition-stat-label">
                  Max Repetitions
                </div>
              </div>
              <div class="repetition-stat-item">
                <div class="repetition-stat-value">
                  {{ repetitionsData.avg_repetitions }}
                </div>
                <div class="repetition-stat-label">
                  Avg Repetitions
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Controls Distribution Chart -->
        <div class="kpi-card automated-controls-card">
          <div class="kpi-header">
            <h3 class="kpi-title">Controls Distribution</h3>
          </div>

          <div v-if="automatedError" class="error-message">
            {{ automatedError }}
            <button @click="fetchAutomatedCount">Retry</button>
          </div>

          <div v-else>
            <div class="automated-chart-container">
              <Pie
                v-if="automatedChartData && automatedChartData.datasets && automatedChartData.datasets.length && automatedChartData.labels && automatedChartData.labels.length"
                :data="automatedChartData"
                :options="automatedChartOptions"
              />
            </div>
            <div class="automated-stats">
              <div class="stat-item">
                <div class="stat-value automated-stat">
                  {{ (automatedData?.automated_percentage ?? 0) }}%
                </div>
                <div class="stat-label">
                  Automated
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-value manual-stat">
                  {{ (automatedData?.manual_percentage ?? 0) }}%
                </div>
                <div class="stat-label">
                  Manual
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Compliance Status Overview Chart -->
        <div class="kpi-card status-overview-card">
          <div class="kpi-header">
            <h3 class="kpi-title">Compliance Status Overview</h3>
          </div>

          <div v-if="statusOverviewError" class="error-message">
            {{ statusOverviewError }}
            <button @click="fetchStatusOverview">Retry</button>
          </div>

          <div v-else class="status-overview-content">
            <div class="status-chart-container">
              <Doughnut
                v-if="statusOverviewChartData && statusOverviewChartData.datasets && statusOverviewChartData.datasets.length"
                :data="statusOverviewChartData"
                :options="statusOverviewChartOptions"
              />
            </div>
            <div class="status-stats">
              <div 
                v-for="(count, status) in statusOverviewData.counts" 
                :key="status"
                class="status-stat-item"
                :class="status.toLowerCase().replace(' ', '-')"
              >
                <div class="status-stat-value">{{ count }}</div>
                <div class="status-stat-label">{{ status }}</div>
                <div class="status-stat-percentage">{{ (statusOverviewData?.percentages?.[status] ?? 0) }}%</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Non-Compliance Count Chart -->
        <div class="kpi-card non-compliance-card">
          <div class="kpi-header">
            <h3 class="kpi-title">Non-Compliance Count</h3>
          </div>

          <div v-if="nonComplianceError" class="error-message">
            {{ nonComplianceError }}
            <button @click="fetchNonComplianceCount">Retry</button>
          </div>

          <div v-else>
            <div class="non-compliance-chart-container">
              <Doughnut
                v-if="nonComplianceChartData && nonComplianceChartData.datasets && nonComplianceChartData.datasets.length && nonComplianceChartData.labels && nonComplianceChartData.labels.length"
                :data="nonComplianceChartData"
                :options="nonComplianceChartOptions"
              />
            </div>
            <div class="non-compliance-summary">
              <div class="total-count">
                <div class="count-value">{{ nonComplianceData.total_non_compliance_count }}</div>
                <div class="count-label">Total Non-Compliant Items</div>
              </div>
              <div class="framework-count">
                <div class="count-value">{{ nonComplianceData.framework_count }}</div>
                <div class="count-label">Frameworks</div>
              </div>
            </div>
          </div>
        </div>

        <!-- S22 Control Effectiveness Score (Basel controls) -->
        <!-- <div class="kpi-card control-effectiveness-card">
          <div class="kpi-header">
            <h3 class="kpi-title">Control Effectiveness Score (Basel Controls)</h3>
          </div>

          <div v-if="controlEffectivenessError" class="error-message">
            {{ controlEffectivenessError }}
            <button @click="fetchControlEffectivenessData">Retry</button>
          </div> -->

          <!-- <div v-else class="control-effectiveness-content">
            <div class="effectiveness-score-circle" :class="getEffectivenessClass">
              <div class="score-value">{{ controlEffectivenessData.score }}</div>
              <div class="score-label">Score</div>
            </div> -->
            
            <!-- <div class="effectiveness-radar-container">
              <svg viewBox="0 0 200 120" class="effectiveness-radar">
                <polygon :points="controlEffectivenessData.radarPoints" 
                         fill="rgba(16, 185, 129, 0.3)" stroke="#10b981" stroke-width="2"/>
                <circle v-for="(point, i) in getRadarPoints(controlEffectivenessData.radarPoints)" 
                        :key="i" :cx="point.x" :cy="point.y" r="3" fill="#10b981"/>
              </svg>
            </div> -->
            
            <!-- <div class="effectiveness-stats">
              <div class="effectiveness-stat-item">
                <div class="stat-value">{{ controlEffectivenessData.testsCompleted }}</div>
                <div class="stat-label">Tests Completed</div>
              </div> -->
              <!-- <div class="effectiveness-stat-item">
                <div class="stat-value">{{ controlEffectivenessData.target }}%</div>
                <div class="stat-label">Target</div>
              </div>
            </div>
          </div>
        </div> -->

        <!-- S23 Basel Control Coverage -->
        <!-- <div class="kpi-card basel-coverage-card">
          <div class="kpi-header">
            <h3 class="kpi-title">Basel Control Coverage</h3>
          </div> -->

          <!-- <div v-if="baselCoverageError" class="error-message">
            {{ baselCoverageError }}
            <button @click="fetchBaselCoverageData">Retry</button>
          </div> -->

          <!-- <div v-else class="basel-coverage-content">
            <div class="coverage-gauge-container">
              <svg viewBox="0 0 200 140" class="coverage-gauge"> -->
                <!-- <defs>
                  <linearGradient id="coverageGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" :style="{stopColor: getCoverageGaugeColor}" />
                    <stop offset="100%" :style="{stopColor: getCoverageGaugeColor}" />
                  </linearGradient>
                </defs> -->
                <!-- Background arc (lighter) -->
                <!-- <path d="M 30 120 A 70 70 0 0 1 170 120" fill="none" stroke="#e9ecef" stroke-width="25" stroke-linecap="round"/> -->
                <!-- Progress arc (filled with color) -->
                <!-- <path :d="getCoverageArc" fill="none" stroke="url(#coverageGradient)" stroke-width="25" stroke-linecap="round"/> -->
                <!-- Center text -->
                <!-- <text x="100" y="100" text-anchor="middle" class="gauge-value">{{ baselCoverageData.percentage }}%</text>
                <text x="100" y="120" text-anchor="middle" class="gauge-label">Coverage</text>
              </svg>
            </div> -->
            
            <!-- <div class="coverage-ratio">
              <span class="ratio-mapped">{{ baselCoverageData.controlsMapped }}</span>
              <span class="ratio-separator">/</span>
              <span class="ratio-required">{{ baselCoverageData.controlsRequired }}</span>
              <span class="ratio-label">Mapped / Required</span>
            </div> -->
            
            <!-- <div class="missing-controls-list">
              <h4>Missing Controls</h4>
              <div class="missing-items"> -->
                <!-- <div v-for="(control, i) in baselCoverageData.missingControls" :key="i" class="missing-control-item">
                  <i class="fas fa-exclamation-triangle"></i>
                  <span>{{ control }}</span>
                </div>
              </div>
            </div>
          </div>
        </div> -->

        <!-- S35 Pillar 3 Regulatory Disclosure Completeness -->
        <!-- <div class="kpi-card pillar3-disclosure-card"> -->
          <!-- <div class="kpi-header">
            <h3 class="kpi-title">Pillar 3 Disclosure Completeness</h3>
          </div>

          <div v-if="pillar3Error" class="error-message">
            {{ pillar3Error }}
            <button @click="fetchPillar3Data">Retry</button>
          </div> -->

          <!-- <div v-else class="pillar3-content">
            <div class="pillar3-gauge-container">
              <svg viewBox="0 0 200 140" class="pillar3-gauge"> -->
                <!-- <defs>
                  <linearGradient id="pillar3Gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" :style="{stopColor: getPillar3GaugeColor}" />
                    <stop offset="100%" :style="{stopColor: getPillar3GaugeColor}" />
                  </linearGradient>
                </defs> -->
                <!-- Background arc (lighter) -->
                <!-- <path d="M 30 120 A 70 70 0 0 1 170 120" fill="none" stroke="#e9ecef" stroke-width="25" stroke-linecap="round"/> -->
                <!-- Progress arc (filled with color) -->
                <!-- <path :d="getPillar3Arc" fill="none" stroke="url(#pillar3Gradient)" stroke-width="25" stroke-linecap="round"/> -->
                <!-- Center text -->
                <!-- <text x="100" y="100" text-anchor="middle" class="gauge-value">{{ pillar3Data.completeness }}%</text>
                <text x="100" y="120" text-anchor="middle" class="gauge-label">Complete</text>
              </svg>
            </div> -->
            
            <!-- <div class="pillar3-progress">
              <div class="progress-bar-container">
                <div class="progress-bar" :style="{width: pillar3Data.completeness + '%'}"></div>
              </div>
              <div class="progress-label">
                {{ pillar3Data.sectionsCompleted }} / {{ pillar3Data.sectionsRequired }} Sections
              </div>
            </div> -->
            
            <!-- <div class="pillar3-checklist">
              <h4>Disclosure Checklist</h4>
              <div class="checklist-items">
                <div v-for="(item, i) in pillar3Data.checklist" :key="i" 
                     class="checklist-item" :class="{'completed': item.completed}">
                  <i :class="item.completed ? 'fas fa-check-circle' : 'fas fa-circle'"></i>
                  <span>{{ item.section }}</span>
                </div>
              </div>
            </div> -->
          <!-- </div>
        </div> -->




      </div>

      <!-- Non-Compliant Incidents Row - Full Width with Split Layout -->
      <div class="incidents-row">
        <div class="kpi-card non-compliant-incidents-card">
          <div class="kpi-header">
            <h3 class="kpi-title">Non-Compliant Incidents</h3>
            <div class="period-selector">
              <select v-model="selectedPeriod" @change="fetchNonCompliantIncidents" class="period-dropdown">
                <option value="week">Last 7 Days</option>
                <option value="month">Last 30 Days</option>
                <option value="quarter">Last 3 Months</option>
                <option value="year">Last 12 Months</option>
              </select>
            </div>
          </div>

          <div v-if="nonCompliantIncidentsError" class="error-message">
            {{ nonCompliantIncidentsError }}
            <button @click="fetchNonCompliantIncidents">Retry</button>
          </div>

          <div v-else class="non-compliant-incidents-content">
            <!-- Left Section: Chart -->
            <div class="incidents-chart-section">
              <div class="incidents-chart-container">
                <Bar
                  v-if="nonCompliantIncidentsChartData && nonCompliantIncidentsChartData.datasets && nonCompliantIncidentsChartData.datasets.length && nonCompliantIncidentsChartData.labels && nonCompliantIncidentsChartData.labels.length"
                  :data="nonCompliantIncidentsChartData"
                  :options="nonCompliantIncidentsChartOptions"
                />
              </div>
              <div class="incidents-summary">
                <div class="incidents-count">
                  <div class="count-value">{{ nonCompliantIncidentsData.non_compliant_count }}</div>
                  <div class="count-label">Non-Compliant Incidents</div>
                  <div class="count-period">{{ nonCompliantIncidentsData.period }}</div>
                  <div class="count-change" :class="{ 'positive': nonCompliantIncidentsData.percentage_change.startsWith('+'), 'negative': !nonCompliantIncidentsData.percentage_change.startsWith('+') }">
                    {{ nonCompliantIncidentsData.percentage_change }}
                    <span class="change-label">vs previous period</span>
                  </div>
                </div>
                <div class="unique-incidents">
                  <div class="unique-value">{{ nonCompliantIncidentsData.unique_compliance_items }}</div>
                  <div class="unique-label">Unique Items</div>
                </div>
              </div>
            </div>

            <!-- Right Section: Table -->
            <div class="incidents-table-section">
              <div class="top-incidents" v-if="nonCompliantIncidentsData.top_non_compliant_items.length > 0">
                <div class="top-incidents-header">Top Non-Compliant Items</div>
                <div class="top-incident-item" 
                     v-for="(item, index) in nonCompliantIncidentsData.top_non_compliant_items.slice(0, 5)" 
                     :key="item.compliance_id"
                     :class="getCriticalityClass(item.criticality)">
                  <div class="incident-rank">{{ index + 1 }}</div>
                  <div class="incident-details">
                    <div class="incident-description">{{ truncateText(item.description, 120) }}</div>
                    <div class="incident-meta">
                      <span class="incident-criticality">{{ item.criticality }}</span>
                      <span class="incident-count">{{ item.count }} occurrences</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>


    </div>
  </div>
</template>

<script>
import { Bar, Pie, Doughnut} from 'vue-chartjs'
import { complianceService } from '@/services/api'
import complianceDataService from '@/services/complianceService' // NEW: Use cached compliance data
import AccessUtils from '@/utils/accessUtils'
import axios from 'axios'
import { API_ENDPOINTS } from '@/config/api'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  ArcElement,
  PointElement,
  LineElement
} from 'chart.js'

ChartJS.register(
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  ArcElement,
  PointElement,
  LineElement
)

// Keep default animations to avoid rare runtime errors in some environments
// Disable Chart.js animations globally to prevent race conditions with mount/unmount
ChartJS.defaults.animation = false
ChartJS.defaults.animations = { colors: false, numbers: false }
ChartJS.defaults.responsiveAnimationDuration = 0

export default {
  name: 'ComplianceKPI',
  components: {
    Bar,
    Pie,
    Doughnut
  },
  data() {
    return {
      loading: false,
      error: null,
      frameworkChangeInProgress: false,
      maturityLevels: ['Initial', 'Developing', 'Defined', 'Managed', 'Optimizing'],
      maturityData: null,
      chartData: null,
      chartOptions: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            titleColor: '#1e293b',
            bodyColor: '#475569',
            borderColor: '#e2e8f0',
            borderWidth: 1,
            padding: 8,
            titleFont: {
              size: 13
            },
            bodyFont: {
              size: 12
            },
            callbacks: {
              label: function(context) {
                return `Count: ${context.raw}`;
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: {
              display: true,
              color: '#f1f5f9',
              drawBorder: false
            },
            ticks: {
              precision: 0,
              color: '#64748b',
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
              color: '#64748b',
              font: {
                size: 10
              }
            }
          }
        }
      },
      nonComplianceLoading: false,
      nonComplianceError: null,
      nonComplianceData: {
        total_non_compliance_count: 0,
        framework_breakdown: [],
        framework_count: 0
      },
      nonComplianceChartData: null,
      nonComplianceChartOptions: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '70%',
        radius: '85%',
        animation: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            titleColor: '#1e293b',
            bodyColor: '#475569',
            borderColor: '#e2e8f0',
            borderWidth: 1,
            padding: 12,
            boxPadding: 6,
            usePointStyle: true,
            callbacks: {
              label: function(context) {
                const value = context.raw;
                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                const percentage = ((value / total) * 100).toFixed(1);
                return [
                  `${context.label}: ${value}`,
                  `Percentage: ${percentage}%`
                ];
              }
            }
          }
        },
      },
      automatedLoading: false,
      automatedError: null,
      automatedData: { automated_percentage: 0, manual_percentage: 0 },
      automatedChartData: null,
      automatedChartOptions: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            titleColor: '#1e293b',
            bodyColor: '#475569',
            borderColor: '#e2e8f0',
            borderWidth: 1,
            padding: 8,
            callbacks: {
              label: function(context) {
                return `${context.label}: ${context.raw}%`;
              }
            }
          }
        }
      },
      repetitionsLoading: false,
      repetitionsError: null,
      repetitionsData: { total_items: 0, max_repetitions: 0, avg_repetitions: 0, distribution: [] },
      repetitionsChartData: null,
      repetitionsChartOptions: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            titleColor: '#1e293b',
            bodyColor: '#475569',
            borderColor: '#e2e8f0',
            borderWidth: 1,
            padding: 8,
            callbacks: {
              label: function(context) {
                return `Occurrences: ${context.raw}`;
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Number of Items',
              color: '#64748b'
            },
            ticks: {
              precision: 0,
              color: '#64748b'
            }
          },
          x: {
            title: {
              display: true,
              text: 'Number of Repetitions',
              color: '#64748b'
            },
            ticks: {
              color: '#64748b'
            }
          }
        }
      },
      ontimeMitigationLoading: false,
      ontimeMitigationError: null,
      ontimeMitigationData: {
        on_time_percentage: 0,
        total_completed: 0,
        completed_on_time: 0,
        completed_late: 0
      },
      statusOverviewLoading: false,
      statusOverviewError: null,
      statusOverviewData: {
        counts: {},
        percentages: {},
        total: 0
      },
      statusOverviewChartData: null,
      statusOverviewChartOptions: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '70%',
        radius: '85%',
        animation: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            titleColor: '#1e293b',
            bodyColor: '#475569',
            borderColor: '#e2e8f0',
            borderWidth: 1,
            padding: 12,
            boxPadding: 6,
            usePointStyle: true,
            callbacks: {
              label: function(context) {
                const value = context.raw;
                const dataset = context.dataset;
                const label = context.label;
                return [
                  `${label}: ${value.toFixed(1)}%`,
                  `Count: ${dataset.data[context.dataIndex]}`
                ];
              }
            }
          }
        },
      },
      reputationalLoading: false,
      reputationalError: null,
      reputationalData: {
        impact_counts: {},
        impact_percentages: {},
        timeline_data: {
          dates: [],
          low: [],
          medium: [],
          high: []
        },
        total_risks: 0
      },
      reputationalChartData: null,
      reputationalChartOptions: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        plugins: {
          legend: {
            display: true,
            position: 'top',
            labels: {
              usePointStyle: true,
              padding: 20,
              font: {
                size: 12
              }
            }
          },
          tooltip: {
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            titleColor: '#1e293b',
            bodyColor: '#475569',
            borderColor: '#e2e8f0',
            borderWidth: 1,
            padding: 12,
            usePointStyle: true,
            callbacks: {
              label: function(context) {
                return `${context.dataset.label}: ${context.raw}`;
              }
            }
          }
        },
        scales: {
          x: {
            grid: {
              display: false
            },
            ticks: {
              font: {
                size: 12
              },
              color: '#64748b'
            }
          },
          y: {
            beginAtZero: true,
            grid: {
              color: '#f1f5f9'
            },
            ticks: {
              precision: 0,
              stepSize: 1,
              font: {
                size: 12
              },
              color: '#64748b'
            },
            title: {
              display: true,
              text: 'Number of Risks',
              color: '#64748b',
              font: {
                size: 12,
                weight: 'normal'
              }
            }
          }
        }
      },
      remediationCostLoading: false,
      remediationCostError: null,
      remediationCostData: {
        cost_summary: {
          total_cost: 0,
          average_cost: 0
        },
        category_chart: {
          labels: [],
          values: []
        }
      },
      remediationCostChartData: null,
      remediationCostChartOptions: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        plugins: {
          legend: {
            display: true,
            position: 'top',
            labels: {
              usePointStyle: true,
              padding: 20,
              font: {
                size: 12
              }
            }
          },
          tooltip: {
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            titleColor: '#1e293b',
            bodyColor: '#475569',
            borderColor: '#e2e8f0',
            borderWidth: 1,
            padding: 12,
            usePointStyle: true,
            callbacks: {
              label: function(context) {
                return `$${context.raw.toLocaleString('en-US')}`;
              }
            }
          }
        },
        scales: {
          x: {
            grid: {
              display: false
            },
            ticks: {
              font: {
                size: 12
              },
              color: '#64748b'
            }
          },
          y: {
            beginAtZero: true,
            grid: {
              color: '#f1f5f9'
            },
            ticks: {
              callback: function(value) {
                return '$' + value.toLocaleString('en-US');
              },
              font: {
                size: 12
              },
              color: '#64748b'
            },
            title: {
              display: true,
              text: 'Remediation Cost ($)',
              color: '#64748b',
              font: {
                size: 12,
                weight: 'normal'
              }
            }
          }
        }
      },
      // Non-Compliant Incidents data
      selectedPeriod: 'month',
      nonCompliantIncidentsLoading: false,
      nonCompliantIncidentsError: null,
      nonCompliantIncidentsData: {
        non_compliant_count: 7,
        period: 'Last 30 Days',
        percentage_change: '+12%',
        unique_compliance_items: 5,
        top_non_compliant_items: [
          { compliance_id: 1, description: 'Data Protection Policy - Encryption Standards', criticality: 'High', count: 3 },
          { compliance_id: 2, description: 'Access Control Framework - Multi-factor Authentication', criticality: 'Medium', count: 2 },
          { compliance_id: 3, description: 'Incident Response Procedure - Notification Timeline', criticality: 'Low', count: 2 }
        ],
        trend_data: {
          labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
          values: [2, 1, 3, 1]
        }
      },
      // S22 Control Effectiveness data
      controlEffectivenessLoading: false,
      controlEffectivenessError: null,
      controlEffectivenessData: {
        score: 78,
        target: 80,
        testsCompleted: 23,
        radarPoints: '100,20 130,40 110,70 90,70 80,40'
      },
      // S23 Basel Control Coverage data
      baselCoverageLoading: false,
      baselCoverageError: null,
      baselCoverageData: {
        percentage: 85,
        controlsMapped: 17,
        controlsRequired: 20,
        missingControls: [
          'CC-12: Counterparty Credit Assessment',
          'LC-08: Liquidity Buffer Monitoring'
        ]
      },
      // S35 Pillar 3 Disclosure data
      pillar3Loading: false,
      pillar3Error: null,
      pillar3Data: {
        completeness: 76,
        sectionsCompleted: 19,
        sectionsRequired: 25,
        checklist: [
          { section: 'Capital Structure', completed: true },
          { section: 'Capital Adequacy', completed: true },
          { section: 'Credit Risk', completed: true },
          { section: 'Market Risk', completed: false },
          { section: 'Operational Risk', completed: true },
          { section: 'Liquidity', completed: false },
          { section: 'Leverage Ratio', completed: true },
          { section: 'Remuneration', completed: false }
        ]
      },
      nonCompliantIncidentsChartData: null,
      nonCompliantIncidentsChartOptions: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            titleColor: '#1e293b',
            bodyColor: '#475569',
            borderColor: '#e2e8f0',
            borderWidth: 1,
            padding: 12,
            usePointStyle: true,
            callbacks: {
              label: function(context) {
                return `Incidents: ${context.raw}`;
              }
            }
          }
        },
        scales: {
          x: {
            grid: {
              display: false
            },
            ticks: {
              maxRotation: 45,
              minRotation: 45,
              callback: function(value) {
                // Format date for display
                const date = new Date(this.getLabelForValue(value));
                return date.toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric'
                });
              },
              font: {
                size: 10
              },
              color: '#64748b'
            }
          },
          y: {
            beginAtZero: true,
            grid: {
              color: '#f1f5f9'
            },
            ticks: {
              precision: 0,
              font: {
                size: 11
              },
              color: '#64748b'
            },
            title: {
              display: true,
              text: 'Number of Incidents',
              color: '#64748b',
              font: {
                size: 12,
                weight: 'normal'
              }
            }
          }
        }
      },
      // Sidebar state management
      sidebarObserver: null,
      // Fullscreen state
      isFullscreen: false,
      // Framework session management
      frameworks: [],
      selectedFrameworkId: '',
      sessionFrameworkId: null
    }
  },
  computed: {
    filteredFrameworks() {
      console.log('🔍 Filtering frameworks, sessionFrameworkId:', this.sessionFrameworkId, 'frameworks:', this.frameworks.length)
      console.log('🔍 selectedFrameworkId:', this.selectedFrameworkId)
      console.log('🔍 Available frameworks:', this.frameworks.map(f => ({ 
        id: f.id, 
        name: f.name
      })))
      
      if (this.sessionFrameworkId) {
        // If we have a session framework, show only that framework
        const sessionFramework = this.frameworks.find(f => {
          if (!f || !f.id) return false
          return f.id.toString() === this.sessionFrameworkId.toString()
        })
        if (sessionFramework) {
          console.log('✅ Found session framework:', sessionFramework.name)
          return [sessionFramework]
        } else if (this.frameworks.length === 0) {
          // If no frameworks loaded but we have a session framework, create a placeholder
          console.log('⚠️ No frameworks loaded, creating placeholder for session framework:', this.sessionFrameworkId)
          return [{
            id: this.sessionFrameworkId,
            name: `Framework ${this.sessionFrameworkId}`,
            placeholder: true
          }]
        } else {
          console.log('❌ Session framework not found in available frameworks')
          return this.frameworks
        }
      }
      
      // If no session framework, show all frameworks
      console.log('📋 No session framework, showing all frameworks')
      return this.frameworks
    }
  },
  methods: {
    // Framework session management methods
    async fetchFrameworks() {
      try {
        console.log('🔍 [ComplianceKPI] Checking for cached framework data...')
        
        // Check if prefetch was never started (user came directly to this page)
        if (!window.complianceDataFetchPromise && !complianceDataService.hasFrameworksCache()) {
          console.log('🚀 [ComplianceKPI] Starting prefetch now (user came directly to this page)...')
          window.complianceDataFetchPromise = complianceDataService.fetchAllComplianceData()
        }
        
        // Wait for prefetch if it's running
        if (window.complianceDataFetchPromise) {
          console.log('⏳ [ComplianceKPI] Waiting for prefetch to complete...')
          try {
            await window.complianceDataFetchPromise
            console.log('✅ [ComplianceKPI] Prefetch completed')
          } catch (error) {
            console.warn('⚠️ [ComplianceKPI] Prefetch failed, will fetch directly')
          }
        }
        
        // FIRST: Try to get data from cache
        if (complianceDataService.hasFrameworksCache()) {
          console.log('✅ [ComplianceKPI] Using cached framework data')
          const cachedFrameworks = complianceDataService.getData('frameworks') || []
          
          this.frameworks = cachedFrameworks
            .filter(f => f && (f.id || f.FrameworkId)) // Filter out invalid frameworks
            .map(f => ({
              id: f.id || f.FrameworkId,
              name: f.name || f.FrameworkName || `Framework ${f.id || f.FrameworkId}`,
              ...f
            }))
          
          console.log(`[ComplianceKPI] Loaded ${this.frameworks.length} frameworks from cache (prefetched on Home page)`)
          console.log('📋 Available frameworks:', this.frameworks.map(f => ({ id: f.id || f.FrameworkId, name: f.name || f.FrameworkName })))
        } else {
          // FALLBACK: Fetch from API if cache is empty
          console.log('⚠️ [ComplianceKPI] No cached data found, fetching from API...')
          console.log('🔄 Fetching frameworks from:', API_ENDPOINTS.FRAMEWORKS)
          const response = await axios.get(API_ENDPOINTS.FRAMEWORKS)
          console.log('📋 Frameworks response:', response)
          console.log('📋 Frameworks response data:', response.data)
          
          if (response.data) {
            // Handle different response structures
            if (response.data.success && response.data.data) {
              // Standard structure: { success: true, data: [...] }
              this.frameworks = (response.data.data || [])
                .filter(f => f && (f.id || f.FrameworkId)) // Filter out invalid frameworks
                .map(f => ({
                  id: f.id || f.FrameworkId,
                  name: f.name || f.FrameworkName || `Framework ${f.id || f.FrameworkId}`,
                  ...f
                }))
              console.log('✅ Frameworks loaded (success structure):', this.frameworks.length)
              
              // Update cache
              if (response.data.data && response.data.data.length > 0) {
                complianceDataService.setData('frameworks', response.data.data)
                console.log('ℹ️ [ComplianceKPI] Cache updated after direct API fetch')
              }
            } else if (Array.isArray(response.data)) {
              // Direct array structure: [...]
              this.frameworks = (response.data || [])
                .filter(f => f && (f.id || f.FrameworkId)) // Filter out invalid frameworks
                .map(f => ({
                  id: f.id || f.FrameworkId,
                  name: f.name || f.FrameworkName || `Framework ${f.id || f.FrameworkId}`,
                  ...f
                }))
              console.log('✅ Frameworks loaded (array structure):', this.frameworks.length)
              
              // Update cache
              if (response.data.length > 0) {
                complianceDataService.setData('frameworks', response.data)
                console.log('ℹ️ [ComplianceKPI] Cache updated after direct API fetch')
              }
            } else {
              console.error('❌ Unexpected frameworks response structure:', response.data)
              this.frameworks = []
            }
            
            console.log('📋 Available frameworks:', this.frameworks.map(f => ({ id: f.id || f.FrameworkId, name: f.name || f.FrameworkName })))
          } else {
            console.error('❌ No data in frameworks response')
            this.frameworks = []
          }
          
          console.log(`[ComplianceKPI] Loaded ${this.frameworks.length} frameworks directly from API (cache unavailable)`)
        }
      } catch (error) {
        console.error('❌ Error fetching frameworks:', error)
        console.error('❌ Error details:', error.response?.data || error.message)
        this.frameworks = []
      }
    },

    async checkSelectedFrameworkFromSession() {
      try {
        console.log('🔍 Checking selected framework from session...')
        console.log('📋 Current frameworks loaded:', this.frameworks.length)
        const response = await axios.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED)
        console.log('📋 Session framework response:', response.data)
        
        if (response.data && response.data.success) {
          // Handle different response structures
          let sessionFramework = null
          
          if (response.data.data) {
            // Standard structure: { success: true, data: { id, name, ... } }
            sessionFramework = response.data.data
          } else if (response.data.frameworkId) {
            // Alternative structure: { success: true, frameworkId: '335', ... }
            sessionFramework = { id: response.data.frameworkId }
          }
          
          if (sessionFramework && sessionFramework.id) {
            console.log('✅ Session framework found:', sessionFramework)
            
            // Ensure sessionFramework.id is valid before processing
            const sessionFrameworkId = sessionFramework.id
            if (!sessionFrameworkId) {
              console.log('❌ Session framework ID is invalid:', sessionFrameworkId)
              this.sessionFrameworkId = null
              this.selectedFrameworkId = ''
              return
            }
            
            // Check if the session framework exists in our loaded frameworks
            console.log('🔍 DEBUG: Searching for session framework:', sessionFrameworkId, 'in frameworks:', this.frameworks.map(f => ({ id: f.id, name: f.name })))
            const frameworkExists = this.frameworks.find(f => {
              if (!f || !f.id) {
                console.log('⚠️ DEBUG: Skipping invalid framework:', f)
                return false
              }
              const matches = f.id.toString() === sessionFrameworkId.toString()
              console.log('🔍 DEBUG: Comparing framework ID:', f.id, 'with session ID:', sessionFrameworkId, 'matches:', matches)
              return matches
            })
            
            console.log('🔍 DEBUG: Framework search result:', frameworkExists)
            
            if (frameworkExists) {
              console.log('✅ Session framework exists in available frameworks:', frameworkExists.name)
              this.sessionFrameworkId = sessionFrameworkId
              this.selectedFrameworkId = sessionFrameworkId.toString()
              console.log('🎯 Set selectedFrameworkId to:', this.selectedFrameworkId)
              console.log('🎯 Set sessionFrameworkId to:', this.sessionFrameworkId)
            } else if (this.frameworks.length === 0) {
              // If no frameworks loaded but we have a session framework, use it anyway
              console.log('⚠️ No frameworks loaded, but using session framework anyway:', sessionFrameworkId)
              this.sessionFrameworkId = sessionFrameworkId
              this.selectedFrameworkId = sessionFrameworkId.toString()
              console.log('🎯 Set selectedFrameworkId to:', this.selectedFrameworkId)
              console.log('🎯 Set sessionFrameworkId to:', this.sessionFrameworkId)
            } else {
              console.log('❌ Session framework not found in available frameworks, clearing session')
              console.log('🔍 Available framework IDs:', this.frameworks.map(f => f.id.toString()))
              console.log('🔍 Session framework ID:', sessionFrameworkId.toString())
              this.sessionFrameworkId = null
              this.selectedFrameworkId = ''
            }
          } else {
            console.log('📋 No valid session framework data found')
            this.sessionFrameworkId = null
            this.selectedFrameworkId = ''
          }
        } else {
          console.log('📋 No session framework found')
          this.sessionFrameworkId = null
          this.selectedFrameworkId = ''
        }
      } catch (error) {
        console.error('❌ Error checking session framework:', error)
        this.sessionFrameworkId = null
        this.selectedFrameworkId = ''
      }
    },

    async saveFrameworkToSession(frameworkId) {
      if (!frameworkId) {
        console.log('🧹 Clearing framework from session')
        try {
          // Use the correct parameter name that the backend expects
          await axios.post(API_ENDPOINTS.FRAMEWORK_SET_SELECTED, { frameworkId: null })
          console.log('✅ Framework cleared from session')
        } catch (error) {
          console.error('❌ Error clearing framework from session:', error)
          // If clearing fails, try to set it to empty string or skip the API call
          console.log('⚠️ Skipping framework clearing due to API error')
        }
        return
      }

      try {
        console.log('💾 Saving framework to session:', frameworkId)
        await axios.post(API_ENDPOINTS.FRAMEWORK_SET_SELECTED, { frameworkId: frameworkId })
        console.log('✅ Framework saved to session')
      } catch (error) {
        console.error('❌ Error saving framework to session:', error)
      }
    },

    async handleFrameworkChange() {
      console.log('🔄 Framework changed to:', this.selectedFrameworkId)
      
      // Prevent multiple simultaneous framework changes
      if (this.frameworkChangeInProgress) {
        console.log('⚠️ Framework change already in progress, skipping...')
        return
      }
      
      this.frameworkChangeInProgress = true
      this.loading = true
      
      try {
        // Handle the case where selectedFrameworkId is undefined or empty
        const frameworkId = this.selectedFrameworkId || ''
        
        // Save to session
        await this.saveFrameworkToSession(frameworkId)
        
        // Update session framework ID
        this.sessionFrameworkId = frameworkId || null
        
        // Clear existing data to show loading state
        this.maturityData = null
        this.nonComplianceData = null
        this.automatedData = null
        this.repetitionsData = null
        this.ontimeMitigationData = {
          on_time_percentage: 0,
          total_completed: 0,
          completed_on_time: 0,
          completed_late: 0
        }
        this.statusOverviewData = null
        this.reputationalData = null
        this.remediationCostData = null
        this.nonCompliantIncidentsData = null
        
        // Refresh all KPI data with the new framework filter
        await this.initKpi()
      } catch (error) {
        console.error('❌ Error changing framework:', error)
        this.error = 'Failed to load data for selected framework'
      } finally {
        this.loading = false
        this.frameworkChangeInProgress = false
      }
    },

    async fetchMaturityData() {
      // Don't set loading if framework change is in progress (it's already set)
      if (!this.frameworkChangeInProgress) {
        this.loading = true;
      }
      this.error = null;
      try {
        const params = this.selectedFrameworkId ? { framework_id: this.selectedFrameworkId } : {}
        console.log('🔄 Fetching maturity data with params:', params)
        const response = await complianceService.getMaturityLevelKPI(params);
        console.log('Maturity Level Response:', response);
        if (response.data && response.data.success) {
          this.maturityData = response.data.data;
          this.updateChartData();
        } else {
          throw new Error(response.data?.message || 'Failed to fetch data');
        }
      } catch (error) {
        // Check if it's an access control error
        if (error.response && [401, 403].includes(error.response.status)) {
          AccessUtils.showCompliancePerformanceAnalyticsDenied();
          return;
        }
        
        console.error('Error fetching maturity data:', error);
        this.error = error.response?.data?.message || error.message || 'Failed to load data';
      } finally {
        this.loading = false;
      }
    },
    
    updateChartData() {
      if (!this.maturityData) return;
      
      const totals = this.maturityData.summary.total_by_maturity;
      
      // Client-side filtering: If framework is selected and backend doesn't filter,
      // we need to filter the data on the frontend
      // NOTE: This is a temporary solution until backend adds framework filtering
      
      this.chartData = {
        labels: this.maturityLevels,
        datasets: [{
          data: this.maturityLevels.map(level => totals[level] || 0),
          backgroundColor: [
            '#f43f5e', // Initial
            '#3b82f6', // Developing
            '#f59e0b', // Defined
            '#10b981', // Managed
            '#8b5cf6'  // Optimizing
          ],
          borderRadius: 4,
          maxBarThickness: 32,
          borderSkipped: false
        }]
      };
    },
    
    getMaturityCount(level) {
      if (!this.maturityData) return 0;
      return this.maturityData.summary.total_by_maturity[level] || 0;
    },

    getTotalCompliances() {
      if (!this.maturityData) return 0;
      return this.maturityData.summary.total_compliances || 0;
    },

    async fetchNonComplianceCount() {
      this.nonComplianceLoading = true;
      this.nonComplianceError = null;
      try {
        const params = this.selectedFrameworkId ? { framework_id: this.selectedFrameworkId } : {}
        console.log('🔄 Fetching non-compliance count with params:', params)
        const response = await complianceService.getNonComplianceCount(params);
        console.log('Non-Compliance Response:', response);
        if (response.data && response.data.success) {
          this.nonComplianceData = response.data.data;
          this.updateNonComplianceChartData();
        } else {
          throw new Error(response.data?.message || 'Failed to fetch non-compliance count');
        }
      } catch (error) {
        // Check if it's an access control error
        if (error.response && [401, 403].includes(error.response.status)) {
          AccessUtils.showCompliancePerformanceAnalyticsDenied();
          return;
        }
        
        console.error('Error fetching non-compliance count:', error);
        this.nonComplianceError = error.response?.data?.message || error.message || 'Failed to load non-compliance data';
      } finally {
        this.nonComplianceLoading = false;
      }
    },

    updateNonComplianceChartData() {
      if (!this.nonComplianceData || !this.nonComplianceData.framework_breakdown) return;
      
      const breakdown = this.nonComplianceData.framework_breakdown;
      
      // Add null check for breakdown array
      if (!Array.isArray(breakdown) || breakdown.length === 0) return;
      
      // Modern gradient colors for doughnut chart
      const colors = [
        '#ef4444',  // Red
        '#f97316',  // Orange
        '#eab308',  // Yellow
        '#84cc16',  // Lime
        '#22c55e',  // Green
        '#14b8a6',  // Teal
        '#06b6d4',  // Cyan
        '#3b82f6',  // Blue
        '#8b5cf6',  // Violet
        '#ec4899'   // Pink
      ];
      
      this.nonComplianceChartData = {
        labels: breakdown.map(item => item?.framework_name || 'Unknown'),
        datasets: [{
          data: breakdown.map(item => item?.count || 0),
          backgroundColor: colors.slice(0, breakdown.length),
          borderWidth: 2,
          borderColor: '#ffffff',
          hoverBorderWidth: 3,
          hoverBorderColor: '#f8fafc'
        }]
      };
    },



    async fetchAutomatedCount() {
      this.automatedLoading = true;
      this.automatedError = null;
      try {
        const params = this.selectedFrameworkId ? { framework_id: this.selectedFrameworkId } : {}
        console.log('🔄 Fetching automated controls count with params:', params)
        const response = await complianceService.getAutomatedControlsCount(params);
        console.log('Automated Controls Response:', response);
        if (response.data && response.data.success) {
          this.automatedData = response.data.data;
          this.updateAutomatedChartData();
        } else {
          throw new Error(response.data?.message || 'Failed to fetch automated controls data');
        }
      } catch (error) {
        // Check if it's an access control error
        if (error.response && [401, 403].includes(error.response.status)) {
          AccessUtils.showCompliancePerformanceAnalyticsDenied();
          return;
        }
        
        console.error('Error fetching automated controls data:', error);
        this.automatedError = error.response?.data?.message || error.message || 'Failed to load automated controls data';
      } finally {
        this.automatedLoading = false;
      }
    },

    updateAutomatedChartData() {
      if (!this.automatedData) return;
      
      // Add null checks and default values to prevent null reference errors
      const automatedPercentage = this.automatedData.automated_percentage || 0;
      const manualPercentage = this.automatedData.manual_percentage || 0;
      
      this.automatedChartData = {
        labels: ['Automated', 'Manual'],
        datasets: [{
          data: [automatedPercentage, manualPercentage],
          backgroundColor: [
            '#3b82f6',  // Blue for automated
            '#94a3b8'   // Gray for manual
          ],
          borderWidth: 0
        }]
      };
    },

    async fetchRepetitionsData() {
      this.repetitionsLoading = true;
      this.repetitionsError = null;
      try {
        const params = this.selectedFrameworkId ? { framework_id: this.selectedFrameworkId } : {}
        console.log('🔄 Fetching repetitions data with params:', params)
        const response = await complianceService.getNonComplianceRepetitions(params);
        console.log('Repetitions Response:', response);
        if (response.data && response.data.success) {
          this.repetitionsData = response.data.data;
          this.updateRepetitionsChartData();
        } else {
          throw new Error(response.data?.message || 'Failed to fetch repetitions data');
        }
      } catch (error) {
        // Check if it's an access control error
        if (error.response && [401, 403].includes(error.response.status)) {
          AccessUtils.showCompliancePerformanceAnalyticsDenied();
          return;
        }
        
        console.error('Error fetching repetitions data:', error);
        this.repetitionsError = error.response?.data?.message || error.message || 'Failed to load repetitions data';
      } finally {
        this.repetitionsLoading = false;
      }
    },

    updateRepetitionsChartData() {
      if (!this.repetitionsData || !this.repetitionsData.distribution) return;
      
      const distribution = this.repetitionsData.distribution;
      
      // Add null check for distribution array
      if (!Array.isArray(distribution) || distribution.length === 0) return;
      
      this.repetitionsChartData = {
        labels: distribution.map(item => item?.repetitions || 0),
        datasets: [{
          data: distribution.map(item => item?.occurrences || 0),
          backgroundColor: '#dc2626',  // Red color
          borderRadius: 4,
          maxBarThickness: 32
        }]
      };
    },

    async fetchOntimeMitigationData() {
      this.ontimeMitigationLoading = true;
      this.ontimeMitigationError = null;
      try {
        const params = this.selectedFrameworkId ? { framework_id: this.selectedFrameworkId } : {}
        console.log('🔄 Fetching on-time mitigation data with params:', params)
        const response = await complianceService.getOntimeMitigationPercentage(params);
        console.log('On-time Mitigation Response:', response);
        if (response.data && response.data.success) {
          // Ensure we have all required data with defaults
          this.ontimeMitigationData = {
            on_time_percentage: response.data.data.on_time_percentage || 0,
            total_completed: response.data.data.total_completed || 0,
            completed_on_time: response.data.data.completed_on_time || 0,
            completed_late: response.data.data.completed_late || 0
          };
        } else {
          throw new Error(response.data?.message || 'Failed to fetch on-time mitigation data');
        }
      } catch (error) {
        // Check if it's an access control error
        if (error.response && [401, 403].includes(error.response.status)) {
          AccessUtils.showCompliancePerformanceAnalyticsDenied();
          return;
        }
        
        console.error('Error fetching on-time mitigation data:', error);
        this.ontimeMitigationError = error.response?.data?.message || error.message || 'Failed to load on-time mitigation data';
      } finally {
        this.ontimeMitigationLoading = false;
      }
    },

    async fetchStatusOverview() {
      this.statusOverviewLoading = true;
      this.statusOverviewError = null;
      try {
        const params = this.selectedFrameworkId ? { framework_id: this.selectedFrameworkId } : {}
        console.log('🔄 Fetching status overview with params:', params)
        const response = await complianceService.getComplianceStatusOverview(params);
        if (response.data && response.data.success) {
          this.statusOverviewData = response.data.data;
          this.updateStatusOverviewChart();
        } else {
          throw new Error(response.data?.message || 'Failed to fetch status overview data');
        }
      } catch (error) {
        // Check if it's an access control error
        if (error.response && [401, 403].includes(error.response.status)) {
          AccessUtils.showCompliancePerformanceAnalyticsDenied();
          return;
        }
        
        console.error('Error fetching status overview:', error);
        this.statusOverviewError = error.response?.data?.message || error.message || 'Failed to load status overview';
      } finally {
        this.statusOverviewLoading = false;
      }
    },

    updateStatusOverviewChart() {
      if (!this.statusOverviewData) return;

      // Define colors for each status
      const statusColors = {
        'Approved': '#10B981',
        'Under Review': '#3B82F6',
        'Active': '#F59E0B',
        'Rejected': '#EF4444'
      };

      const hoverColors = {
        'Approved': '#059669',
        'Under Review': '#2563EB',
        'Active': '#D97706',
        'Rejected': '#DC2626'
      };

      const labels = Object.keys(this.statusOverviewData.percentages);
      
      this.statusOverviewChartData = {
        labels,
        datasets: [{
          data: Object.values(this.statusOverviewData.percentages),
          backgroundColor: labels.map(status => statusColors[status]),
          hoverBackgroundColor: labels.map(status => hoverColors[status]),
          borderWidth: 0,
          borderRadius: 4
        }]
      };
    },

    async fetchReputationalData() {
      this.reputationalLoading = true;
      this.reputationalError = null;
      try {
        const params = this.selectedFrameworkId ? { framework_id: this.selectedFrameworkId } : {}
        console.log('🔄 Fetching reputational data with params:', params)
        const response = await complianceService.getReputationalImpact(params);
        console.log('Reputational Impact Response:', response);
        if (response.data && response.data.success) {
          this.reputationalData = response.data.data;
          this.updateReputationalChart();
        } else {
          throw new Error(response.data?.message || 'Failed to fetch reputational impact data');
        }
      } catch (error) {
        console.error('Error fetching reputational impact:', error);
        this.reputationalError = error.response?.data?.message || error.message || 'Failed to load reputational impact data';
        
        // Set default empty data structure to prevent chart errors
        this.reputationalData = {
          impact_counts: { low: 0, medium: 0, high: 0 },
          impact_percentages: { low: 0, medium: 0, high: 0 },
          timeline_data: {
            dates: [],
            low: [],
            medium: [],
            high: []
          },
          total_risks: 0
        };
      } finally {
        this.reputationalLoading = false;
      }
    },

    updateReputationalChart() {
      if (!this.reputationalData?.impact_counts) {
        // Set default empty chart data
        this.reputationalChartData = {
          labels: ['Low', 'Medium', 'High'],
          datasets: [{
            label: 'Impact Count',
            data: [0, 0, 0],
            borderColor: '#3b82f6',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            tension: 0.4,
            fill: true,
            pointBackgroundColor: '#3b82f6',
            pointBorderColor: '#fff',
            pointRadius: 5,
            pointHoverRadius: 7
          }]
        };
        return;
      }

      // Get impact counts directly
      const { low, medium, high } = this.reputationalData.impact_counts;

      // Create line chart data
      this.reputationalChartData = {
        labels: ['Low', 'Medium', 'High'],
        datasets: [{
          label: 'Impact Count',
          data: [low, medium, high],
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          tension: 0.4,
          fill: true,
          pointBackgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
          pointBorderColor: '#fff',
          pointRadius: 6,
          pointHoverRadius: 8
        }]
      };
    },

    async fetchRemediationCost() {
      this.remediationCostLoading = true;
      this.remediationCostError = null;
      try {
        const params = this.selectedFrameworkId ? { framework_id: this.selectedFrameworkId } : {}
        console.log('🔄 Fetching remediation cost with params:', params)
        const response = await complianceService.getRemediationCost(params);
        console.log('Remediation Cost Response:', response);
        if (response.data && response.data.success) {
          this.remediationCostData = response.data.data;
          this.updateRemediationCostChart();
        } else {
          throw new Error(response.data?.message || 'Failed to fetch remediation cost data');
        }
      } catch (error) {
        console.error('Error fetching remediation cost:', error);
        this.remediationCostError = error.response?.data?.message || error.message || 'Failed to load remediation cost data';
      } finally {
        this.remediationCostLoading = false;
      }
    },

    updateRemediationCostChart() {
      if (!this.remediationCostData || !this.remediationCostData.time_series_chart) return;
      
      const timeData = this.remediationCostData.time_series_chart;
      
      this.remediationCostChartData = {
        labels: timeData.labels,
        datasets: [{
          label: 'Remediation Cost',
          data: timeData.values,
          borderColor: '#ef4444',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointBackgroundColor: '#ef4444',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 6
        }]
      };
    },

    async fetchNonCompliantIncidents() {
      this.nonCompliantIncidentsLoading = true;
      this.nonCompliantIncidentsError = null;
      try {
        const params = { period: this.selectedPeriod }
        if (this.selectedFrameworkId) {
          params.framework_id = this.selectedFrameworkId
        }
        console.log('🔄 Fetching non-compliant incidents with params:', params)
        const response = await complianceService.getNonCompliantIncidents(this.selectedPeriod, params);
        console.log('Non-Compliant Incidents Response:', response);
        if (response.data && response.data.success) {
          this.nonCompliantIncidentsData = response.data.data;
          this.updateNonCompliantIncidentsChart();
        } else {
          throw new Error(response.data?.message || 'Failed to fetch non-compliant incidents data');
        }
      } catch (error) {
        console.error('Error fetching non-compliant incidents:', error);
        this.nonCompliantIncidentsError = error.response?.data?.message || error.message || 'Failed to load non-compliant incidents data';
      } finally {
        this.nonCompliantIncidentsLoading = false;
      }
    },
    
    updateNonCompliantIncidentsChart() {
      if (!this.nonCompliantIncidentsData || !this.nonCompliantIncidentsData.trend_data) return;
      
      const trendData = this.nonCompliantIncidentsData.trend_data;
      
      this.nonCompliantIncidentsChartData = {
        labels: trendData.labels,
        datasets: [{
          label: 'Non-Compliant Incidents',
          data: trendData.values,
          backgroundColor: '#dc2626',
          borderRadius: 4,
          maxBarThickness: 32,
          borderSkipped: false
        }]
      };
    },
    
    getCriticalityClass(criticality) {
      if (!criticality) return '';
      
      const lowerCriticality = criticality.toLowerCase();
      if (lowerCriticality === 'high') return 'high-criticality';
      if (lowerCriticality === 'medium') return 'medium-criticality';
      if (lowerCriticality === 'low') return 'low-criticality';
      
      return '';
    },
    
    truncateText(text, maxLength) {
      if (!text) return '';
      return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    },
    
    formatNumber(value) {
      return value.toLocaleString('en-US');
    },

    // Basel KPIs methods (S22, S23, S35)
    fetchControlEffectivenessData() {
      // Static data - replace with API call later
      this.controlEffectivenessLoading = false;
      this.controlEffectivenessError = null;
    },

    fetchBaselCoverageData() {
      // Static data - replace with API call later
      this.baselCoverageLoading = false;
      this.baselCoverageError = null;
    },

    fetchPillar3Data() {
      // Static data - replace with API call later
      this.pillar3Loading = false;
      this.pillar3Error = null;
    },

    getRadarPoints(pointsString) {
      if (!pointsString) return [];
      return pointsString.split(' ').map(p => {
        const [x, y] = p.split(',');
        return { x: parseFloat(x), y: parseFloat(y) };
      });
    },

    getEffectivenessClass() {
      const score = this.controlEffectivenessData.score;
      const target = this.controlEffectivenessData.target;
      if (score >= target + 10) return 'score-excellent';
      if (score >= target) return 'score-good';
      return 'score-warning';
    },

    getCoverageGaugeColor() {
      const percentage = this.baselCoverageData.percentage;
      if (percentage >= 95) return '#28a745';  // Green
      if (percentage >= 85) return '#ffc107';  // Yellow
      return '#dc3545';  // Red
    },

    getCoverageArc() {
      const percentage = Math.min(this.baselCoverageData.percentage, 100) / 100;
      const startAngle = Math.PI;
      const endAngle = startAngle - (Math.PI * percentage);
      
      const radius = 70;
      const centerX = 100;
      const centerY = 120;
      
      const startX = centerX + radius * Math.cos(startAngle);
      const startY = centerY + radius * Math.sin(startAngle);
      const endX = centerX + radius * Math.cos(endAngle);
      const endY = centerY + radius * Math.sin(endAngle);
      
      const largeArcFlag = percentage > 0.5 ? 1 : 0;
      
      return `M ${startX} ${startY} A ${radius} ${radius} 0 ${largeArcFlag} 0 ${endX} ${endY}`;
    },

    getPillar3GaugeColor() {
      const completeness = this.pillar3Data.completeness;
      if (completeness >= 95) return '#28a745';  // Green
      if (completeness >= 75) return '#ffc107';  // Yellow
      return '#dc3545';  // Red
    },

    getPillar3Arc() {
      const percentage = Math.min(this.pillar3Data.completeness, 100) / 100;
      const startAngle = Math.PI;
      const endAngle = startAngle - (Math.PI * percentage);
      
      const radius = 70;
      const centerX = 100;
      const centerY = 120;
      
      const startX = centerX + radius * Math.cos(startAngle);
      const startY = centerY + radius * Math.sin(startAngle);
      const endX = centerX + radius * Math.cos(endAngle);
      const endY = centerY + radius * Math.sin(endAngle);
      
      const largeArcFlag = percentage > 0.5 ? 1 : 0;
      
      return `M ${startX} ${startY} A ${radius} ${radius} 0 ${largeArcFlag} 0 ${endX} ${endY}`;
    },
    // Initialize KPI loading in prioritized batches
    async initKpi() {
      try {
        // Load the most visible/critical cards first in parallel
        const criticalPromises = [
          this.fetchMaturityData(),
          this.fetchNonComplianceCount(),
          this.fetchAutomatedCount(),
          this.fetchStatusOverview()
        ]
        await Promise.allSettled(criticalPromises)

        // Then load the secondary cards in parallel (but wait for them to complete)
        const secondaryPromises = [
          this.fetchRepetitionsData(),
          this.fetchOntimeMitigationData(),
          this.fetchReputationalData(),
          this.fetchRemediationCost(),
          this.fetchNonCompliantIncidents()
        ]
        await Promise.allSettled(secondaryPromises)
      } catch (error) {
        console.error('❌ Error initializing KPI data:', error)
        // Don't throw - let individual fetch methods handle their own errors
      }
    },
    
    setupSidebarListener() {
      // Create a mutation observer to watch for sidebar class changes
      this.sidebarObserver = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
            this.adjustLayoutForSidebar()
          }
        })
      })
      
      // Start observing the sidebar
      const sidebar = document.querySelector('.sidebar')
      if (sidebar) {
        this.sidebarObserver.observe(sidebar, {
          attributes: true,
          attributeFilter: ['class']
        })
        
        // Initial adjustment
        this.adjustLayoutForSidebar()
      }
    },
    
    adjustLayoutForSidebar() {
      const sidebar = document.querySelector('.sidebar')
      const dashboard = document.querySelector('.kpi-dashboard')
      
      if (sidebar && dashboard && !this.isFullscreen) {
        const isCollapsed = sidebar.classList.contains('collapsed')
        
        if (isCollapsed) {
          // Sidebar is collapsed (60px width)
          dashboard.style.paddingLeft = '80px'
          dashboard.style.width = 'calc(100vw - 60px)'
          dashboard.style.maxWidth = 'calc(100vw - 60px)'
        } else {
          // Sidebar is expanded (280px width)
          dashboard.style.paddingLeft = '300px'
          dashboard.style.width = 'calc(100vw - 280px)'
          dashboard.style.maxWidth = 'calc(100vw - 280px)'
        }
      }
    },

    toggleFullscreen() {
      this.isFullscreen = !this.isFullscreen
      
      if (this.isFullscreen) {
        // Enter fullscreen mode
        this.enterFullscreen()
      } else {
        // Exit fullscreen mode
        this.exitFullscreen()
      }
    },

    enterFullscreen() {
      const dashboard = document.querySelector('.kpi-dashboard')
      if (dashboard) {
        dashboard.style.position = 'fixed'
        dashboard.style.top = '0'
        dashboard.style.left = '0'
        dashboard.style.width = '100vw'
        dashboard.style.height = '100vh'
        dashboard.style.maxWidth = '100vw'
        dashboard.style.maxHeight = '100vh'
        dashboard.style.padding = '20px'
        dashboard.style.paddingLeft = '20px'
        dashboard.style.zIndex = '9999'
        dashboard.style.backgroundColor = '#f8fafc'
        dashboard.style.overflow = 'auto'
        
        // Hide sidebar and header if they exist
        const sidebar = document.querySelector('.sidebar')
        const header = document.querySelector('.header, .navbar, .top-bar')
        if (sidebar) sidebar.style.display = 'none'
        if (header) header.style.display = 'none'
        
        // Add escape key listener
        document.addEventListener('keydown', this.handleEscapeKey)
      }
    },

    exitFullscreen() {
      const dashboard = document.querySelector('.kpi-dashboard')
      if (dashboard) {
        dashboard.style.position = ''
        dashboard.style.top = ''
        dashboard.style.left = ''
        dashboard.style.width = ''
        dashboard.style.height = ''
        dashboard.style.maxWidth = ''
        dashboard.style.maxHeight = ''
        dashboard.style.padding = ''
        dashboard.style.paddingLeft = ''
        dashboard.style.zIndex = ''
        dashboard.style.backgroundColor = ''
        dashboard.style.overflow = ''
        
        // Show sidebar and header if they exist
        const sidebar = document.querySelector('.sidebar')
        const header = document.querySelector('.header, .navbar, .top-bar')
        if (sidebar) sidebar.style.display = ''
        if (header) header.style.display = ''
        
        // Remove escape key listener
        document.removeEventListener('keydown', this.handleEscapeKey)
        
        // Re-adjust layout for sidebar
        this.$nextTick(() => {
          this.adjustLayoutForSidebar()
        })
      }
    },

    handleEscapeKey(event) {
      if (event.key === 'Escape' && this.isFullscreen) {
        this.toggleFullscreen()
      }
    }
  },
  async mounted() {
    // Load frameworks first, then check session, then load KPI data
    try {
      console.log('🔄 MOUNTED: Starting framework initialization...')
      await this.fetchFrameworks()
      console.log('✅ MOUNTED: Frameworks loaded, checking session...')
      
      await this.checkSelectedFrameworkFromSession()
      console.log('✅ MOUNTED: Session checked, current state:', {
        sessionFrameworkId: this.sessionFrameworkId,
        selectedFrameworkId: this.selectedFrameworkId
      })
      
      // Ensure selectedFrameworkId is properly set
      if (!this.selectedFrameworkId && this.sessionFrameworkId) {
        this.selectedFrameworkId = this.sessionFrameworkId.toString()
        console.log('🔧 MOUNTED: Fixed selectedFrameworkId:', this.selectedFrameworkId)
      }
      
      // Load KPI data after framework setup is complete
      console.log('🔄 MOUNTED: Loading KPI data with framework:', this.selectedFrameworkId)
      await this.initKpi()
      console.log('✅ MOUNTED: KPI data loaded')
    } catch (error) {
      console.error('❌ MOUNTED: Error during initialization:', error)
    }
    
    // Listen for sidebar state changes
    this.setupSidebarListener()
  },
  
  beforeUnmount() {
    // Clean up sidebar listener
    if (this.sidebarObserver) {
      this.sidebarObserver.disconnect()
    }
    
    // Clean up fullscreen event listener
    document.removeEventListener('keydown', this.handleEscapeKey)
    
    // Exit fullscreen if still active
    if (this.isFullscreen) {
      this.exitFullscreen()
    }
  }
}
</script>

<style scoped>
/* Framework Filter Section */
.framework-filter-section {
  margin-bottom: 20px;
  padding: 16px;
  background: transparent;
  border-radius: 0;
  box-shadow: none;
  border: none;
}

.filter-header {
  display: flex;
  flex-direction: column;
  padding-top:40px;
  align-items: flex-start;
  gap: 16px;
}

.filter-title {
  font-size: 1.7rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.framework-filter-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.framework-label {
  font-size: 0.9rem;
  font-weight: 500;
  color: #475569;
  white-space: nowrap;
  margin: 0;
}

.framework-select {
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #ffffff;
  font-size: 0.9rem;
  color: #374151;
  min-width: 250px;
  width: auto;
  height: auto;
  cursor: pointer;
  transition: all 0.2s ease;
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6,9 12,15 18,9'%3e%3c/polyline%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 10px center;
  background-size: 16px;
  padding-right: 35px;
}

.framework-select:hover {
  border-color: #3b82f6;
}

.framework-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* Main Dashboard Container */
.kpi-dashboard {
   padding: 38px 4px 8px 250px !important; /* Minimal right padding to maximize width */
  background: #ffffff !important;
  min-height: 100vh !important;
  margin-left: 0 !important;
  box-sizing: border-box !important;
  width: calc(100vw - 280px) !important; /* Ensure content takes full width minus sidebar */
  max-width: none !important;
  transition: all 0.3s ease !important;
}

/* Fullscreen Controls */
.fullscreen-controls {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 10000;
  display: flex;
  gap: 10px;
}

.fullscreen-toggle {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s ease;
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 6px;
}

.fullscreen-toggle:hover {
  background: rgba(255, 255, 255, 1);
  border-color: #3b82f6;
  color: #3b82f6;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.fullscreen-toggle:active {
  transform: translateY(0);
}

/* Fullscreen Mode Styles */
.kpi-dashboard.fullscreen {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  max-width: 100vw !important;
  max-height: 100vh !important;
  padding: 20px !important;
  padding-left: 20px !important;
  z-index: 9999 !important;
  background-color: #f8fafc !important;
  overflow: auto !important;
  margin: 0 !important;
}

/* Fullscreen specific adjustments */
.kpi-dashboard.fullscreen .charts-section {
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

.kpi-dashboard.fullscreen .kpi-card {
  min-height: 320px;
}

.kpi-dashboard.fullscreen .incidents-row .non-compliant-incidents-card {
  min-height: 600px;
}

/* Hide fullscreen controls when not in fullscreen */
.kpi-dashboard:not(.fullscreen) .fullscreen-controls {
  display: none;
}

/* Multi-Section Layout */
.kpi-sections {
  display: flex !important;
  flex-direction: column !important;
  gap: 12px !important;
  max-width: none !important; /* Remove max-width constraint to allow full width */
  margin: 0 !important;
  width: 100% !important;
}

/* Main Grid Layout */
.charts-section, .numbers-section {
  display: grid !important;
  gap: 12px !important;
  width: 100% !important;
}

.charts-section {
  grid-template-columns: repeat(3, 1fr) !important;
}

.numbers-section {
  grid-template-columns: 1fr;
}

/* Incidents Row Layout */
.incidents-row {
  margin-top: 8px;
  margin-bottom: 8px;
}

.incidents-row .non-compliant-incidents-card {
  min-height: 500px;
}

/* Charts Section - Left Side */
.charts-section {
  display: grid !important;
  grid-template-columns: repeat(3, 1fr) !important;
  gap: 12px !important;
  align-content: start !important;
  width: 100% !important;
  margin-left: 0 !important; /* Ensure no left margin */
  padding-left: 0 !important; /* Ensure no left padding */
  padding-right: 0 !important; /* Ensure no right padding */
  max-width: none !important; /* Remove max-width constraint */
}

/* Ensure individual KPI cards have proper spacing */
.kpi-card {
  background: #ffffff;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e2e8f0;
  padding: 16px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  margin: 0; /* Remove any default margins */
  min-width: 0; /* Allow cards to shrink properly */
  min-height: 280px;
  max-height: 320px;
}

/* Increase height for Basel and Pillar3 cards to show all content */
.basel-coverage-card,
.pillar3-disclosure-card,
.control-effectiveness-card {
  min-height: 380px;
  max-height: 420px;
}

/* Ensure chart containers don't overflow */
.kpi-chart {
  width: 100%;
  max-width: 100%;
  overflow: hidden;
  height: 140px;
}

/* Ensure the first card (maturity chart) has proper left spacing */
.charts-section .kpi-card:first-child {
  margin-left: 0;
  padding-left: 16px;
}

/* KPI Header Styles */
.kpi-header {
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e2e8f0;
}

.kpi-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #1e293b;
}

/* Ensure proper spacing between cards */
.charts-section .kpi-card + .kpi-card {
  margin-left: 0;
}

/* Responsive adjustments for different screen sizes */
@media (max-width: 1600px) {
  .kpi-dashboard:not(.fullscreen) {
    padding-left: 260px !important;
    width: calc(100vw - 260px) !important;
    max-width: none !important;
    padding: 6px 4px 6px 260px !important;
  }
  
  .charts-section {
    grid-template-columns: repeat(3, 1fr) !important; /* Keep 3 columns for better width utilization */
    gap: 10px !important;
  }
}

@media (max-width: 1200px) {
  .kpi-dashboard:not(.fullscreen) {
    padding-left: 240px !important;
    width: calc(100vw - 240px) !important;
    max-width: none !important;
    padding: 4px 2px 4px 240px !important;
  }
  
  .charts-section {
    grid-template-columns: repeat(2, 1fr) !important;
    gap: 8px !important;
  }
  
  .filter-header {
    flex-wrap: wrap;
  }
  
  .framework-select {
    min-width: 220px;
  }
}

@media (max-width: 900px) {
  .filter-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .framework-filter-group {
    margin-left: 0;
  }
  
  .framework-label {
    margin: 0;
  }
  
  .framework-select {
    min-width: 200px;
    width: auto;
  }
}

@media (max-width: 768px) {
  .kpi-dashboard:not(.fullscreen) {
    padding: 6px 2px !important;
    padding-left: 6px !important;
    width: 100vw !important;
    max-width: none !important;
    margin-left: 0 !important;
  }
  
  .filter-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .framework-filter-group {
    margin-left: 0;
  }
  
  .framework-label {
    margin: 0;
  }
  
  .framework-select {
    min-width: 200px;
    width: auto;
  }
  
  .charts-section {
    grid-template-columns: 1fr !important;
    gap: 8px !important;
  }
  
  .kpi-card {
    min-height: 280px !important;
    padding: 12px !important;
  }
  
  .fullscreen-controls {
    top: 10px;
    right: 10px;
  }
  
  .fullscreen-toggle {
    padding: 6px 12px;
    font-size: 12px;
  }
}

/* Handle sidebar collapsed state */
@media (max-width: 1024px) {
  .kpi-dashboard:not(.fullscreen) {
    padding-left: 70px !important; /* Account for collapsed sidebar (60px) + spacing */
    width: calc(100vw - 60px) !important;
    max-width: none !important;
    padding: 4px 2px 4px 70px !important;
  }
}

/* Ensure proper spacing when sidebar is very narrow */
@media (max-width: 600px) {
  .kpi-dashboard:not(.fullscreen) {
    padding-left: 10px !important;
    width: calc(100vw - 10px) !important;
    max-width: none !important;
    padding: 2px 1px 2px 10px !important;
  }
  
  .charts-section {
    gap: 8px !important;
  }
  
  .kpi-card {
    padding: 12px !important;
  }
}

/* Ensure content doesn't get cut off on the right side */
.kpi-dashboard {
  overflow-x: hidden;
  overflow-y: auto;
}

/* Ensure charts section has proper right margin */
.kpi-sections {
  padding-right: 4px !important;
  box-sizing: border-box !important;
}

/* Ensure individual cards don't overflow */
.kpi-card {
  box-sizing: border-box !important;
  max-width: 100% !important;
  overflow: hidden !important;
}

/* Ensure chart containers are properly sized */
.kpi-chart {
  box-sizing: border-box;
  max-width: 100%;
  overflow: hidden;
}

/* Ensure the grid layout respects container boundaries */
.charts-section {
  box-sizing: border-box !important;
  max-width: 100% !important;
  overflow: hidden !important;
}

/* Ensure proper spacing for maturity grid */
.maturity-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
  padding: 6px 4px;
  margin-top: auto;
  box-sizing: border-box;
  max-width: 100%;
}

.maturity-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 6px;
  background: #f8fafc;
  border-radius: 4px;
  font-size: 0.8rem;
  box-sizing: border-box;
  max-width: 100%;
  overflow: hidden;
}

.maturity-color {
  width: 10px;
  height: 10px;
  border-radius: 3px;
  flex-shrink: 0;
}

/* Modern color palette for maturity levels */
.initial { background-color: #f43f5e; }
.developing { background-color: #3b82f6; }
.defined { background-color: #f59e0b; }
.managed { background-color: #10b981; }
.optimizing { background-color: #8b5cf6; }

.maturity-label {
  color: #475569;
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 0.75rem;
  max-width: 100%;
}

.maturity-count {
  font-weight: 600;
  color: #1e293b;
  margin-left: 6px;
  font-size: 0.8rem;
}

/* Ensure total count text has proper spacing */
.total-count {
  margin-top: 8px;
  padding: 8px 0;
  text-align: center;
  font-weight: 600;
  color: #1e293b;
  background: #f8fafc;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
  font-size: 0.85rem;
}

/* Ensure on-time mitigation card has proper spacing */
.ontime-mitigation-card {
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  max-width: 100%;
  overflow: hidden;
}

.ontime-mitigation-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 12px 0;
  box-sizing: border-box;
  max-width: 100%;
}

.ontime-percentage-circle {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
  transition: all 0.3s ease;
  margin: 0 auto;
  flex-shrink: 0;
}

.ontime-percentage-circle.high-rate {
  background: linear-gradient(135deg, #10b981, #059669);
}

.percentage-value {
  font-size: 20px;
  font-weight: 700;
  line-height: 1;
}

.percentage-label {
  font-size: 10px;
  font-weight: 500;
  opacity: 0.9;
}

.ontime-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

.ontime-stat-item {
  text-align: center;
  padding: 8px 6px;
  background: #f8fafc;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
  box-sizing: border-box;
  max-width: 100%;
  overflow: hidden;
}

.stat-value {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 2px;
}

.stat-label {
  font-size: 10px;
  color: #64748b;
  font-weight: 500;
}

/* Repetitions Statistics */
.repetitions-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e2e8f0;
}

.repetition-stat-item {
  text-align: center;
  padding: 8px;
  border-radius: 6px;
  background: #fef2f2;
  border: 1px solid #fecaca;
}

.repetition-stat-value {
  font-size: 18px;
  font-weight: 700;
  color: #dc2626;
  margin-bottom: 2px;
}

.repetition-stat-label {
  font-size: 10px;
  color: #7f1d1d;
  font-weight: 500;
}

/* Controls Statistics */
.automated-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e2e8f0;
}

.stat-item {
  text-align: center;
  padding: 10px;
  border-radius: 6px;
  background: #f8fafc;
}

.automated-stat {
  color: #3b82f6;
}

.manual-stat {
  color: #94a3b8;
}

/* Status Statistics */
.status-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e2e8f0;
}

.status-stat-item {
  text-align: center;
  padding: 8px;
  border-radius: 6px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.status-stat-item.approved {
  background: #f0fdf4;
  border-color: #bbf7d0;
}

.status-stat-item.under-review {
  background: #eff6ff;
  border-color: #bfdbfe;
}

.status-stat-item.active {
  background: #fffbeb;
  border-color: #fed7aa;
}

.status-stat-item.rejected {
  background: #fef2f2;
  border-color: #fecaca;
}

.status-stat-value {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 2px;
}

.status-stat-label {
  font-size: 10px;
  color: #64748b;
  font-weight: 500;
  margin-bottom: 2px;
}

.status-stat-percentage {
  font-size: 10px;
  color: #94a3b8;
  font-weight: 500;
}

/* Non-Compliance Summary */
.non-compliance-summary {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e2e8f0;
}

.total-count,
.framework-count {
  text-align: center;
  padding: 10px;
  border-radius: 6px;
  background: #fef2f2;
  border: 1px solid #fecaca;
}

.count-value {
  font-size: 20px;
  font-weight: 700;
  color: #dc2626;
  margin-bottom: 2px;
}

.count-label {
  font-size: 10px;
  color: #7f1d1d;
  font-weight: 500;
}

/* Non-Compliant Incidents Split Layout */
.non-compliant-incidents-content {
  display: flex;
  gap: 24px;
  min-height: calc(100% - 60px);
}

.incidents-chart-section,
.incidents-table-section {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.incidents-chart-section {
  border-right: 1px solid #e2e8f0;
  padding-right: 20px;
}

.incidents-table-section {
  padding-left: 4px;
  overflow-y: visible;
}

/* Incidents Summary */
.incidents-summary {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
  margin-bottom: 16px;
}

.incidents-count {
  text-align: center;
  padding: 16px;
  border-radius: 8px;
  background: #fef2f2;
  border: 1px solid #fecaca;
}

.count-period {
  font-size: 12px;
  color: #7f1d1d;
  margin-top: 4px;
}

.count-change {
  font-size: 14px;
  font-weight: 600;
  margin-top: 8px;
}

.count-change.positive {
  color: #dc2626;
}

.count-change.negative {
  color: #10b981;
}

.change-label {
  font-size: 11px;
  font-weight: 400;
  opacity: 0.8;
}

.unique-incidents {
  text-align: center;
  padding: 12px;
  border-radius: 6px;
  background: #f8fafc;
}

.unique-value {
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 4px;
}

.unique-label {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}

/* Top Incidents */
.top-incidents {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
  max-height: 300px;
  overflow-y: auto;
}

/* Custom scrollbar styling for top-incidents */
.top-incidents::-webkit-scrollbar {
  width: 8px;
}

.top-incidents::-webkit-scrollbar-track {
  background: #f8fafc;
  border-radius: 4px;
}

.top-incidents::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.top-incidents::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* Firefox scrollbar styling */
.top-incidents {
  scrollbar-width: thin;
  scrollbar-color: #cbd5e1 #f8fafc;
}

.top-incidents-header {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 12px;
}

.top-incident-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 10px;
  border-radius: 6px;
  margin-bottom: 10px;
  background: #f8fafc;
  min-height: 60px;
}

.top-incident-item.high-criticality {
  background: #fef2f2;
  border-left: 4px solid #dc2626;
}

.top-incident-item.medium-criticality {
  background: #fffbeb;
  border-left: 4px solid #f59e0b;
}

.top-incident-item.low-criticality {
  background: #f0fdf4;
  border-left: 4px solid #10b981;
}

.incident-rank {
  font-size: 14px;
  font-weight: 700;
  color: #64748b;
  min-width: 20px;
}

.incident-details {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.incident-description {
  font-size: 12px;
  color: #1e293b;
  font-weight: 500;
  margin-bottom: 4px;
  line-height: 1.4;
  word-wrap: break-word;
  hyphens: auto;
}

.incident-meta {
  display: flex;
  gap: 12px;
  font-size: 11px;
}

.incident-criticality {
  font-weight: 600;
  text-transform: uppercase;
}

.incident-count {
  color: #64748b;
}

/* Cost Summary */
.cost-summary {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
  margin-bottom: 16px;
}

.total-cost,
.avg-cost {
  text-align: center;
  padding: 16px;
  border-radius: 8px;
  background: #f0f9ff;
  border: 1px solid #bae6fd;
}

.cost-value {
  font-size: 24px;
  font-weight: 700;
  color: #0c4a6e;
  margin-bottom: 4px;
}

.cost-label {
  font-size: 12px;
  color: #0369a1;
  font-weight: 500;
}

.cost-categories {
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}

.category-label {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 12px;
}

.category-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-radius: 6px;
  background: #f8fafc;
  margin-bottom: 6px;
}

.category-name {
  font-size: 12px;
  color: #475569;
  font-weight: 500;
}

.category-cost {
  font-size: 12px;
  color: #1e293b;
  font-weight: 600;
}

/* Error Message Styles */
.error-message {
  text-align: center;
  padding: 20px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  font-size: 14px;
}

.error-message button {
  margin-top: 12px;
  padding: 8px 16px;
  background: #dc2626;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
}

.error-message button:hover {
  background: #b91c1c;
}

/* Responsive Design */
@media (max-width: 1200px) {
  .charts-section {
    grid-template-columns: repeat(2, 1fr);
  }
  
.maturity-card {
  grid-column: span 2;
}

.ontime-mitigation-card {
    grid-column: span 1;
}

.repetitions-card {
  grid-column: span 2;
  }
  
  .non-compliant-incidents-content {
    flex-direction: column;
  }
  
  .incidents-chart-section {
    border-right: none;
    border-bottom: 1px solid #e2e8f0;
    padding-right: 0;
    padding-bottom: 20px;
    margin-bottom: 20px;
  }
  
  .incidents-table-section {
    padding-left: 0;
  }
}

@media (max-width: 480px) {
  .kpi-dashboard {
    padding: 12px;
  }
  
  .maturity-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .ontime-stats,
  .repetitions-stats,
  .automated-stats,
  .status-stats {
    grid-template-columns: 1fr;
  }
}

/* Loading and Animation States */
.kpi-card.loading {
  opacity: 0.7;
  pointer-events: none;
}

.kpi-card.loading::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
  animation: loading 1.5s infinite;
}

@keyframes loading {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

/* Chart-specific adjustments */
canvas {
  max-height: 100% !important;
}

/* Chart containers */
.repetitions-chart-container,
.automated-chart-container,
.status-chart-container,
.non-compliance-chart-container {
  height: 140px;
  margin: 8px 0;
}

/* Ensure proper chart responsiveness */
.kpi-chart canvas,
.repetitions-chart-container canvas,
.automated-chart-container canvas,
.status-chart-container canvas,
.non-compliance-chart-container canvas,
.incidents-chart-container canvas,
.remediation-chart-container canvas {
  max-width: 100% !important;
  height: auto !important;
}

/* Basel Coverage & Pillar 3 Gauge Styles */
.basel-coverage-content,
.pillar3-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 8px 0;
  overflow-y: auto;
  height: 100%;
}

.coverage-gauge-container,
.pillar3-gauge-container {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 0;
}

.coverage-gauge,
.pillar3-gauge {
  width: 100%;
  max-width: 200px;
  height: auto;
}

.coverage-gauge .gauge-value,
.pillar3-gauge .gauge-value {
  font-size: 1.5rem;
  font-weight: 700;
  fill: #1e293b;
}

.coverage-gauge .gauge-label,
.pillar3-gauge .gauge-label {
  font-size: 0.75rem;
  fill: #64748b;
}

.coverage-ratio,
.pillar3-progress {
  padding: 8px;
  background: #f8fafc;
  border-radius: 6px;
  text-align: center;
}

.missing-controls-list,
.pillar3-checklist {
  flex: 1;
  padding: 8px;
  overflow-y: auto;
  max-height: 120px;
}

.missing-controls-list h4,
.pillar3-checklist h4 {
  font-size: 0.8rem;
  color: #1e293b;
  margin-bottom: 6px;
  font-weight: 600;
}

.missing-items,
.checklist-items {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.missing-control-item,
.checklist-item {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.7rem;
  display: flex;
  align-items: center;
  gap: 6px;
}

.missing-control-item {
  background: #fef2f2;
  border-left: 3px solid #ef4444;
  color: #7f1d1d;
}

.checklist-item {
  color: #64748b;
}

.checklist-item.completed {
  color: #10b981;
}

.ratio-mapped,
.ratio-required {
  font-size: 1.1rem;
  font-weight: 600;
}

.ratio-mapped {
  color: #10b981;
}

.ratio-label {
  font-size: 0.7rem;
  color: #64748b;
  display: block;
  margin-top: 4px;
}

.progress-bar-container {
  width: 100%;
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 6px;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #10b981, #059669);
  border-radius: 4px;
  transition: width 0.5s ease;
}

.progress-label {
  font-size: 0.7rem;
  color: #64748b;
  font-weight: 500;
}
</style>
