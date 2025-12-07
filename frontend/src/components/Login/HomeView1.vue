<template>
  <div class="home-container">
    <main class="main-content">
      <!-- Hero Section -->
      <section class="hero-section">
        <div class="hero-background">
          <div class="hero-gradient"></div>
          <div class="floating-elements">
            <div class="floating-element" v-for="n in 6" :key="n" :style="getFloatingStyle(n)"></div>
          </div>
        </div>
        
        <div class="hero-content">
          <div class="hero-text" data-aos="fade-up">
            <div class="hero-badge">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                <path d="M9 12l2 2 4-4"/>
              </svg>
              Enterprise-Grade Security
            </div>
            
            <h1 class="hero-title">
              <span class="gradient-text">Next-Generation</span>
              <span class="gradient-text"> GRC Platform</span>
              <span class="gradient-text"> for Modern Banking</span>
            </h1>
            
            <p class="hero-description">
              Experience the future of Governance, Risk, and Compliance with our unified platform designed for agility, accuracy, and efficiency. Empower your organization to seamlessly manage audits, assess risks, enforce compliance, and monitor policies.
            </p>
            
            <div class="hero-stats">
              <div class="stat-item" v-for="(stat, index) in heroStats" :key="index" data-aos="fade-up" :data-aos-delay="index * 100">
                <div class="stat-number">{{ stat.number }}</div>
                <div class="stat-label">{{ stat.label }}</div>
        </div>
        </div>
        

        </div>

          <div class="hero-visual" data-aos="fade-left" data-aos-delay="200">
            <div class="dashboard-preview">
              <div class="preview-header">
                <div class="preview-controls">
                  <div class="control red"></div>
                  <div class="control yellow"></div>
                  <div class="control green"></div>
                </div>
                <div class="preview-title">GRC Dashboard</div>
              </div>
              <div class="preview-content">
                <div class="preview-chart">
           <Line :data="lineChartData" :options="chartOptions" />
                </div>
                <div class="preview-metrics">
                  <div class="metric-card" v-for="metric in previewMetrics" :key="metric.title">
                    <div class="metric-icon" :class="metric.color">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path v-if="metric.type === 'document'" d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline v-if="metric.type === 'document'" points="14 2 14 8 20 8"></polyline>
                        <path v-if="metric.type === 'shield'" d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                        <circle v-if="metric.type === 'check'" cx="12" cy="12" r="10"></circle>
                        <path v-if="metric.type === 'check'" d="M9 12l2 2 4-4"></path>
                      </svg>
                    </div>
                    <div class="metric-data">
                      <div class="metric-value">{{ metric.value }}</div>
                      <div class="metric-title">{{ metric.title }}</div>
                      <div class="metric-change" :class="metric.trend">{{ metric.change }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Features Section -->
      <section class="features-section">
        <div class="section-header" data-aos="fade-up">
          <div class="section-badge">Core Capabilities</div>
          <h2 class="section-title">Comprehensive GRC Suite</h2>
          <p class="section-description">
            Our integrated platform provides everything you need to maintain regulatory compliance, 
            manage enterprise risk, and ensure robust governance across your organization.
          </p>
            </div>
        
        <div class="features-grid">
          <div class="feature-card" v-for="(feature, index) in features" :key="index" 
               data-aos="fade-up" :data-aos-delay="index * 100">
            <div class="feature-icon" :class="feature.color">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path v-if="feature.type === 'document'" d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline v-if="feature.type === 'document'" points="14 2 14 8 20 8"></polyline>
                <path v-if="feature.type === 'triangle'" d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                <line v-if="feature.type === 'triangle'" x1="12" y1="9" x2="12" y2="13"></line>
                <line v-if="feature.type === 'triangle'" x1="12" y1="17" x2="12.01" y2="17"></line>
                <circle v-if="feature.type === 'check'" cx="12" cy="12" r="10"></circle>
                <path v-if="feature.type === 'check'" d="M9 12l2 2 4-4"></path>
                <circle v-if="feature.type === 'alert'" cx="12" cy="12" r="10"></circle>
                <line v-if="feature.type === 'alert'" x1="12" y1="8" x2="12" y2="12"></line>
                <line v-if="feature.type === 'alert'" x1="12" y1="16" x2="12.01" y2="16"></line>
                <path v-if="feature.type === 'clipboard'" d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path>
                <rect v-if="feature.type === 'clipboard'" x="8" y="2" width="8" height="4" rx="1" ry="1"></rect>
                <line v-if="feature.type === 'bar-chart'" x1="18" y1="20" x2="18" y2="10"></line>
                <line v-if="feature.type === 'bar-chart'" x1="12" y1="20" x2="12" y2="4"></line>
                <line v-if="feature.type === 'bar-chart'" x1="6" y1="20" x2="6" y2="14"></line>
              </svg>
          </div>
            <h3 class="feature-title">{{ feature.title }}</h3>
            <p class="feature-description">{{ feature.description }}</p>
            <div class="feature-benefits">
              <div class="benefit" v-for="benefit in feature.benefits" :key="benefit">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20 6L9 17l-5-5"/>
                </svg>
                {{ benefit }}
        </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Analytics Section -->
      <section class="analytics-section">
        <div class="analytics-content">
          <div class="analytics-text" data-aos="fade-right">
            <div class="section-badge">Real-time Insights</div>
            <h2 class="section-title">Advanced Analytics & Reporting</h2>
            <p class="section-description">
              Leverage powerful analytics to gain deep insights into your compliance posture, 
              risk exposure, and governance effectiveness.
            </p>
            
            <div class="analytics-features">
              <div class="analytics-feature" v-for="feature in analyticsFeatures" :key="feature.title">
                <div class="feature-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle v-if="feature.type === 'clock'" cx="12" cy="12" r="10"></circle>
                    <polyline v-if="feature.type === 'clock'" points="12 6 12 12 16 14"></polyline>
                    <rect v-if="feature.type === 'monitor'" x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                    <path v-if="feature.type === 'monitor'" d="M9 9h6v6H9z"></path>
                    <path v-if="feature.type === 'document'" d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline v-if="feature.type === 'document'" points="14 2 14 8 20 8"></polyline>
                  </svg>
            </div>
                <div class="feature-content">
                  <h4>{{ feature.title }}</h4>
                  <p>{{ feature.description }}</p>
          </div>
        </div>
            </div>
          </div>
          
          <div class="analytics-visual" data-aos="fade-left">
            <div class="chart-container">
              <div class="chart-header">
                <h3>Compliance Trends</h3>
                
              </div>
              <div class="chart-content">
                <Bar :data="barChartData" :options="chartOptions" />
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Trust Indicators -->
      <section class="trust-section">
        <div class="trust-content" data-aos="fade-up">
          <h2 class="trust-title">Trusted by Leading Financial Institutions</h2>
          <p class="trust-description">
            Our platform meets the highest security and compliance standards, 
            ensuring your data is protected and regulations are met.
          </p>
          
          <div class="trust-indicators">
            <div class="trust-item" v-for="indicator in trustIndicators" :key="indicator.title" 
                 data-aos="zoom-in" :data-aos-delay="indicator.delay">
              <div class="trust-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path v-if="indicator.type === 'shield'" d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                  <path v-if="indicator.type === 'shield'" d="M9 12l2 2 4-4"></path>
                  <rect v-if="indicator.type === 'lock'" x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                  <circle v-if="indicator.type === 'lock'" cx="12" cy="16" r="1"></circle>
                  <path v-if="indicator.type === 'check'" d="M9 12l2 2 4-4"></path>
                  <path v-if="indicator.type === 'check'" d="M21 12c-1 0-3-1-3-3s2-3 3-3 3 1 3 3-2 3-3 3"></path>
                  <path v-if="indicator.type === 'check'" d="M3 12c1 0 3-1 3-3s-2-3-3-3-3 1-3 3 2 3 3 3"></path>
                  <circle v-if="indicator.type === 'clock'" cx="12" cy="12" r="10"></circle>
                  <polyline v-if="indicator.type === 'clock'" points="12 6 12 12 16 14"></polyline>
                </svg>
              </div>
              <div class="trust-content-text">
                <h4>{{ indicator.title }}</h4>
                <p>{{ indicator.description }}</p>
              </div>
            </div>
          </div>
        </div>
      </section>



      <!-- Footer Section -->
      <footer class="footer-section">
        <div class="footer-background">
          <div class="footer-gradient"></div>
        </div>
        <div class="footer-content">
          <!-- Main Footer -->
          <div class="footer-main" data-aos="fade-up">
            <div class="footer-brand">
              <div class="footer-logo">
                <div class="logo-circle">
                  <img src="../../assets/RiskaVaire.png" alt="RiskaVaire Logo" class="logo-image" />
                </div>
              </div>
              <p class="footer-description">
                Advanced Governance, Risk & Compliance platform designed for modern enterprises. 
                Streamline your GRC operations with our comprehensive suite of tools.
              </p>
            </div>

            <div class="footer-links">
              <div class="footer-column">
                <h4>Platform</h4>
                <ul>
                  <li><a href="#" @click="navigateToCompliance">Dashboard</a></li>
                  <li><a href="#" @click="navigateToCompliance">Policy Management</a></li>
                  <li><a href="#" @click="navigateToCompliance">Risk Assessment</a></li>
                  <li><a href="#" @click="navigateToCompliance">Compliance Monitoring</a></li>
                  <li><a href="#" @click="navigateToCompliance">Audit Management</a></li>
                </ul>
              </div>

              <div class="footer-column">
                <h4>Solutions</h4>
                <ul>
                  <li><a href="#" @click="navigateToCompliance">Banking & Finance</a></li>
                  <li><a href="#" @click="navigateToCompliance">Healthcare</a></li>
                  <li><a href="#" @click="navigateToCompliance">Manufacturing</a></li>
                  <li><a href="#" @click="navigateToCompliance">Technology</a></li>
                  <li><a href="#" @click="navigateToCompliance">Government</a></li>
                </ul>
              </div>

              <div class="footer-column">
                <h4>Resources</h4>
                <ul>
                  <li><a href="#" @click="navigateToCompliance">Documentation</a></li>
                  <li><a href="#" @click="navigateToCompliance">API Reference</a></li>
                  <li><a href="#" @click="navigateToCompliance">Best Practices</a></li>
                  <li><a href="#" @click="navigateToCompliance">Case Studies</a></li>
                  <li><a href="#" @click="navigateToCompliance">Webinars</a></li>
                </ul>
              </div>

              <div class="footer-column">
                <h4>Company</h4>
                <ul>
                  <li><a href="#" @click="navigateToCompliance">About Us</a></li>
                  <li><a href="#" @click="navigateToCompliance">Careers</a></li>
                  <li><a href="#" @click="navigateToCompliance">Contact</a></li>
                  <li><a href="#" @click="navigateToCompliance">Privacy Policy</a></li>
                  <li><a href="#" @click="navigateToCompliance">Terms of Service</a></li>
                </ul>
              </div>
              
              <!-- Contact Section -->
              <div class="contact-section">
                <div class="contact-header">
                  <h4>CONTACT US</h4>
                </div>
                <div class="contact-info">
                  <div class="contact-item">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" stroke="currentColor" stroke-width="2"/>
                      <polyline points="22,6 12,13 2,6" stroke="currentColor" stroke-width="2"/>
                    </svg>
                    <a href="mailto:info@vardaanglobal.com" class="contact-link">info@vardaanglobal.com</a>
                  </div>
                  <div class="contact-item">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l1.72 1.71" stroke="currentColor" stroke-width="2"/>
                      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" stroke="currentColor" stroke-width="2"/>
                    </svg>
                    <a href="https://vardaanglobal.com/grc" target="_blank" rel="noopener noreferrer" class="contact-link">vardaanglobal.com/grc</a>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Footer Bottom -->
          <div class="footer-bottom" data-aos="fade-up" data-aos-delay="200">
            <div class="footer-bottom-content">
              <div class="footer-copyright">
                <p>&copy; {{ new Date().getFullYear() }} RiskaVaire. All rights reserved.</p>
              </div>
              <div class="footer-certifications">
                <div class="certification-badge">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                    <path d="m9 12 2 2 4-4"/>
                  </svg>
                  <span>ISO 27001</span>
                </div>
                <div class="certification-badge">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                    <path d="m9 12 2 2 4-4"/>
                  </svg>
                  <span>GDPR Compliant</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </main>
  </div>
</template>

<script setup>
import { Line, Bar } from 'vue-chartjs';
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, PointElement, LineElement } from 'chart.js';
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import AOS from 'aos';
import 'aos/dist/aos.css';

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, PointElement, LineElement);

const router = useRouter();
const user = ref(null);


// Hero statistics
const heroStats = ref([
  { number: '99.9%', label: 'Uptime' },
  { number: '500+', label: 'Regulations' },
  { number: '24/7', label: 'Monitoring' },
  { number: '< 1s', label: 'Response Time' }
]);

// Preview metrics for hero visual
const previewMetrics = ref([
  {
    title: 'Active Policies',
    value: '1,247',
    change: '+12%',
    trend: 'positive',
    color: 'blue',
    type: 'document'
  },
  {
    title: 'Risk Score',
    value: '7.2',
    change: '-5%',
    trend: 'positive',
    color: 'green',
    type: 'shield'
  },
  {
    title: 'Compliance',
    value: '94%',
    change: '+3%',
    trend: 'positive',
    color: 'purple',
    type: 'check'
  }
]);

// Features data
const features = ref([
  {
    title: 'Policy Management',
    description: 'Centralized policy creation, distribution, and lifecycle management with automated versioning and approval workflows.',
    color: 'blue',
    type: 'document',
    benefits: ['Automated workflows', 'Version control', 'Digital signatures']
  },
  {
    title: 'Risk Assessment',
    description: 'Advanced risk modeling with predictive analytics, heat maps, and real-time monitoring across all business units.',
    color: 'red',
    type: 'triangle',
    benefits: ['Predictive analytics', 'Real-time alerts', 'Risk heat maps']
  },
  {
    title: 'Compliance Monitoring',
    description: 'Continuous compliance monitoring with automated reporting, regulatory mapping, and audit trail management.',
    color: 'green',
    type: 'check',
    benefits: ['Automated reporting', 'Regulatory mapping', 'Audit trails']
  },
  {
    title: 'Incident Management',
    description: 'Streamlined incident response with automated escalation, impact assessment, and resolution tracking.',
    color: 'orange',
    type: 'alert',
    benefits: ['Automated escalation', 'Impact assessment', 'Resolution tracking']
  },
  {
    title: 'Audit Management',
    description: 'End-to-end audit lifecycle management with planning, execution, findings tracking, and remediation.',
    color: 'purple',
    type: 'clipboard',
    benefits: ['Planning tools', 'Findings tracking', 'Remediation workflows']
  },
  {
    title: 'Reporting & Analytics',
    description: 'Comprehensive reporting suite with customizable dashboards, executive summaries, and regulatory reports.',
    color: 'indigo',
    type: 'bar-chart',
    benefits: ['Custom dashboards', 'Executive reports', 'Regulatory submissions']
  }
]);

// Analytics features
const analyticsFeatures = ref([
  {
    title: 'Predictive Analytics',
    description: 'AI-powered insights to predict potential compliance issues and risks before they occur.',
    type: 'clock'
  },
  {
    title: 'Real-time Dashboards',
    description: 'Live monitoring dashboards with customizable widgets and automated alerts.',
    type: 'monitor'
  },
  {
    title: 'Automated Reporting',
    description: 'Schedule and distribute reports automatically to stakeholders and regulators.',
    type: 'document'
  }
]);

// Trust indicators
const trustIndicators = ref([
  {
    title: 'SOC 2 Type II',
    description: 'Certified for security, availability, and confidentiality',
    type: 'shield',
    delay: 0
  },
  {
    title: 'ISO 27001',
    description: 'Information security management systems certified',
    type: 'lock',
    delay: 100
  },
  {
    title: 'GDPR Compliant',
    description: 'Full compliance with data protection regulations',
    type: 'check',
    delay: 200
  },
  {
    title: '99.9% Uptime',
    description: 'Enterprise-grade reliability and performance',
    type: 'clock',
    delay: 300
  }
]);

// Chart data
const lineChartData = ref({
  labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
  datasets: [
    {
      label: 'Compliance Score',
      data: [85, 88, 92, 89, 94, 96],
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59, 130, 246, 0.15)',
      tension: 0.4,
      fill: true,
      pointBackgroundColor: '#3b82f6',
      pointBorderColor: 'white',
      pointBorderWidth: 2,
      pointRadius: 4,
      pointHoverRadius: 6,
    },
  ],
});

const barChartData = ref({
  labels: ['IT Security', 'Finance', 'HR', 'Operations', 'Risk Mgmt'],
  datasets: [
    {
      label: 'Compliance %',
      data: [93, 88, 92, 87, 95],
      backgroundColor: [
        'rgba(59, 130, 246, 0.9)',
        'rgba(16, 185, 129, 0.9)',
        'rgba(139, 92, 246, 0.9)',
        'rgba(245, 158, 11, 0.9)',
        'rgba(239, 68, 68, 0.9)',
      ],
      borderColor: [
        '#3b82f6',
        '#10b981',
        '#8b5cf6',
        '#f59e0b',
        '#ef4444',
      ],
      borderWidth: 2,
      borderRadius: 8,
      borderSkipped: false,
    },
  ],
});

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false,
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      titleColor: 'white',
      bodyColor: 'white',
      borderColor: 'rgba(59, 130, 246, 0.3)',
      borderWidth: 1,
      cornerRadius: 8,
      displayColors: false,
    },
  },
  scales: {
    y: {
      beginAtZero: true,
      grid: {
        color: 'rgba(0, 0, 0, 0.05)',
        drawBorder: false,
      },
      ticks: {
        color: '#6b7280',
        font: {
          size: 12,
          weight: '500',
        },
      },
    },
    x: {
      grid: {
        display: false,
      },
      ticks: {
        color: '#6b7280',
        font: {
          size: 12,
          weight: '500',
        },
      },
    },
  },
  elements: {
    point: {
      radius: 4,
      hoverRadius: 6,
      backgroundColor: '#3b82f6',
      borderColor: 'white',
      borderWidth: 2,
    },
    line: {
      borderWidth: 3,
      tension: 0.4,
    },
    bar: {
      borderRadius: 6,
    },
  },
};

// Floating elements positioning
const getFloatingStyle = (index) => {
  const positions = [
    { top: '10%', left: '10%', animationDelay: '0s' },
    { top: '20%', right: '15%', animationDelay: '2s' },
    { top: '60%', left: '5%', animationDelay: '4s' },
    { top: '70%', right: '10%', animationDelay: '1s' },
    { top: '40%', left: '80%', animationDelay: '3s' },
    { top: '85%', left: '60%', animationDelay: '5s' },
  ];
  
  return positions[index - 1] || {};
};





// Navigation functions
const navigateToCompliance = () => {
  router.push({ name: 'ComplianceDashboard' });
};



onMounted(() => {
  // Initialize AOS
  AOS.init({
    duration: 800,
    easing: 'ease-out-cubic',
    once: true,
    offset: 100,
  });
  
  // Get user data
  const userData = localStorage.getItem('user');
  if (userData) {
    user.value = JSON.parse(userData);
  }
  

});
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* Global Styles */
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

.home-container {
  font-family: 'Inter', sans-serif;
  background: #fafbfc;
  margin-left: 260px; /* Account for sidebar width */
  overflow-x: hidden;
}



/* Main Content */
.main-content {
  padding-top: 0;
}

/* Hero Section */
.hero-section {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  overflow: hidden;
}

.hero-background {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
}

.hero-gradient {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, 
    rgba(30, 64, 175, 0.05) 0%, 
    rgba(59, 130, 246, 0.08) 50%, 
    rgba(147, 197, 253, 0.05) 100%);
}

.floating-elements {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.floating-element {
  position: absolute;
  width: 60px;
  height: 60px;
  background: rgba(30, 64, 175, 0.08);
  border-radius: 50%;
  animation: float 6s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0px) rotate(0deg); }
  50% { transform: translateY(-20px) rotate(180deg); }
}

.hero-content {
  position: relative;
  z-index: 10;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4rem;
  align-items: center;
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(30, 64, 175, 0.1);
  border: 1px solid rgba(30, 64, 175, 0.2);
  color: #1e40af;
  padding: 0.5rem 1rem;
  border-radius: 50px;
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 1.5rem;
}

.hero-title {
  font-size: 3.5rem;
  font-weight: 800;
  line-height: 1.1;
  color: #1f2937;
  margin-bottom: 1.5rem;
  letter-spacing: -0.02em;
}

.gradient-text {
  background: linear-gradient(135deg, #1e40af, #3b82f6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-description {
  font-size: 1.25rem;
  color: #6b7280;
  line-height: 1.6;
  margin-bottom: 2rem;
  max-width: 600px;
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 2rem;
  margin-bottom: 2.5rem;
}

.stat-item {
  text-align: center;
  padding: 1.5rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.stat-number {
  font-size: 2rem;
  font-weight: 700;
  color: #1e40af;
  margin-bottom: 0.25rem;
}

.stat-label {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

.hero-actions {
  display: flex;
  gap: 1rem;
}

.cta-primary {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #1e40af;
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: 12px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.cta-primary:hover {
  background: #1d4ed8;
  transform: translateY(-2px);
  box-shadow: 0 10px 40px rgba(30, 64, 175, 0.3);
}

.cta-secondary {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: white;
  color: #1e40af;
  border: 2px solid #1e40af;
  padding: 1rem 2rem;
  border-radius: 12px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.cta-secondary:hover {
  background: #1e40af;
  color: white;
  transform: translateY(-2px);
}

/* Hero Visual */
.hero-visual {
  position: relative;
}

.dashboard-preview {
  background: white;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 25px 80px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.dashboard-preview:hover {
  transform: translateY(-4px);
  box-shadow: 0 30px 100px rgba(0, 0, 0, 0.2);
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  background: #f8fafc;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.preview-controls {
  display: flex;
  gap: 0.5rem;
}

.control {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.control.red { background: #ef4444; }
.control.yellow { background: #f59e0b; }
.control.green { background: #10b981; }

.preview-title {
  font-weight: 600;
  color: #374151;
}

.preview-content {
  padding: 1.5rem;
}

.preview-chart {
  height: 200px;
  margin-bottom: 1.5rem;
  position: relative;
  overflow: hidden;
  border-radius: 8px;
  background: #f8fafc;
  border: 1px solid rgba(0, 0, 0, 0.05);
  padding: 1rem;
}

.preview-chart canvas {
  max-height: 100% !important;
  max-width: 100% !important;
}

.preview-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

.metric-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.metric-card:hover {
  background: #f1f5f9;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.metric-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.metric-icon.blue { background: #1e40af; }
.metric-icon.green { background: #10b981; }
.metric-icon.purple { background: #7c3aed; }

.metric-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
}

.metric-title {
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 500;
}

.metric-change {
  font-size: 0.75rem;
  font-weight: 600;
}

.metric-change.positive { color: #10b981; }
.metric-change.negative { color: #ef4444; }

/* Features Section */
.features-section {
  padding: 6rem 2rem;
  max-width: 1400px;
  margin: 0 auto;
  background: white;
}

.section-header {
  text-align: center;
  margin-bottom: 4rem;
}

.section-badge {
  display: inline-block;
  background: rgba(30, 64, 175, 0.1);
  color: #1e40af;
  padding: 0.5rem 1rem;
  border-radius: 50px;
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.section-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 0.75rem;
  letter-spacing: -0.02em;
}

.section-description {
  font-size: 1.125rem;
  color: #6b7280;
  line-height: 1.6;
  max-width: 700px;
  margin: 0 auto 1.5rem;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 2rem;
}

.feature-card {
  background: white;
  padding: 2rem;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.12);
}

.feature-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin-bottom: 1.5rem;
}

.feature-icon.blue { background: #1e40af; }
.feature-icon.red { background: #dc2626; }
.feature-icon.green { background: #059669; }
.feature-icon.orange { background: #ea580c; }
.feature-icon.purple { background: #7c3aed; }
.feature-icon.indigo { background: #4f46e5; }

.feature-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.75rem;
}

.feature-description {
  color: #6b7280;
  line-height: 1.6;
  margin-bottom: 1.5rem;
}

.feature-benefits {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.benefit {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #374151;
}

.benefit svg {
  color: #10b981;
  flex-shrink: 0;
}

/* Analytics Section */
.analytics-section {
  background: #f8fafc;
  padding: 6rem 2rem;
}

.analytics-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4rem;
  align-items: stretch;
  max-width: 1400px;
  margin: 0 auto;
}

.analytics-features {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1rem;
  height: 100%;
  justify-content: space-evenly;
}

.analytics-feature {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1.5rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  flex: 1;
  min-height: 0;
}

.analytics-text {
  display: flex;
  flex-direction: column;
  height: 100%;
  justify-content: space-between;
}

.analytics-feature .feature-icon {
  width: 48px;
  height: 48px;
  background: rgba(30, 64, 175, 0.1);
  color: #1e40af;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0;
}

.analytics-feature h4 {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.analytics-feature p {
  color: #6b7280;
  line-height: 1.5;
}

.chart-container {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(0, 0, 0, 0.05);
  overflow: hidden;
  transition: all 0.3s ease;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chart-container:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.chart-header h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
}

.chart-controls {
  display: flex;
  gap: 0.5rem;
}

.chart-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #e5e7eb;
  background: white;
  color: #6b7280;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.chart-btn.active {
  background: #1e40af;
  color: white;
  border-color: #1e40af;
}

.chart-content {
  height: 400px;
  position: relative;
  overflow: hidden;
  border-radius: 8px;
  background: #f8fafc;
  border: 1px solid rgba(0, 0, 0, 0.05);
  padding: 1rem;
}

.chart-content canvas {
  max-height: 100% !important;
  max-width: 100% !important;
  height: 100% !important;
  width: 100% !important;
}

/* Trust Section */
.trust-section {
  padding: 6rem 2rem;
  background: white;
}

.trust-content {
  max-width: 1200px;
  margin: 0 auto;
  text-align: center;
}

.trust-title {
  font-size: 2.25rem;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 1rem;
}

.trust-description {
  font-size: 1.125rem;
  color: #6b7280;
  line-height: 1.6;
  max-width: 600px;
  margin: 0 auto 3rem;
}

.trust-indicators {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 2rem;
}

.trust-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 2rem;
  background: #f8fafc;
  border-radius: 12px;
  text-align: left;
  transition: all 0.3s ease;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.trust-item:hover {
  background: #f1f5f9;
  transform: translateY(-2px);
}

.trust-item .trust-icon {
  width: 60px;
  height: 60px;
  background: #1e40af;
  color: white;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.trust-content-text h4 {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.trust-content-text p {
  color: #6b7280;
  line-height: 1.5;
}

/* CTA Section */
.cta-section {
  position: relative;
  padding: 6rem 2rem;
  overflow: hidden;
}

.cta-background {
  position: absolute;
  inset: 0;
  background: #1f2937;
}

.cta-gradient {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, 
    rgba(30, 64, 175, 0.9) 0%, 
    rgba(59, 130, 246, 0.8) 100%);
}

.cta-content {
  position: relative;
  z-index: 10;
  text-align: center;
  max-width: 800px;
  margin: 0 auto;
}

.cta-title {
  font-size: 3rem;
  font-weight: 700;
  color: white;
  margin-bottom: 1rem;
  line-height: 1.2;
}

.cta-description {
  font-size: 1.25rem;
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.6;
  margin-bottom: 2.5rem;
}

.cta-actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
}



/* Footer Section */
.footer-section {
  position: relative;
  padding: 6rem 2rem;
  overflow: hidden;
}

.footer-background {
  position: absolute;
  inset: 0;
  background: #f8fafc;
}

.footer-gradient {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, 
    rgba(248, 250, 252, 0.9) 0%, 
    rgba(241, 245, 249, 0.8) 100%);
}

.footer-content {
  position: relative;
  z-index: 10;
  max-width: 1400px;
  margin: 0 auto;
}

.footer-main {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 4rem;
  margin-bottom: 4rem;
}

.footer-brand {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.footer-logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.logo-circle {
  width: 200px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: transparent;
  border: none;
  border-radius: 0;
  box-shadow: none;
  overflow: visible;
  padding: 0;
  margin: 0 0 20px 0;
}

.logo-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: transparent;
  border: none;
  box-shadow: none;
  border-radius: 0;
  display: block;
  margin: 0;
  padding: 0;
  line-height: 0;
}

.logo-text h3 {
  font-size: 1.875rem;
  font-weight: 800;
  color: #1f2937;
  line-height: 1;
}

.logo-text span {
  font-size: 0.875rem;
  color: rgba(31, 41, 55, 0.8);
}

.footer-description {
  font-size: 1.125rem;
  color: rgba(31, 41, 55, 0.8);
  line-height: 1.6;
  margin-bottom: 2rem;
}

.footer-social {
  display: flex;
  gap: 1rem;
}

.social-link {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  transition: all 0.3s ease;
}

.social-link:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
}

.footer-links {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 2rem;
  margin-bottom: 4rem;
}

.footer-column h4 {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1.5rem;
}

.footer-column ul {
  list-style: none;
}

.footer-column li {
  margin-bottom: 0.75rem;
}

.footer-column a {
  color: rgba(31, 41, 55, 0.7);
  text-decoration: none;
  font-size: 0.9375rem;
  transition: color 0.3s ease;
}

.footer-column a:hover {
  color: #1f2937;
}

.footer-bottom {
  border-top: 1px solid rgba(31, 41, 55, 0.1);
  padding-top: 2rem;
  text-align: center;
}

.footer-bottom-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.footer-copyright {
  font-size: 0.875rem;
  color: rgba(31, 41, 55, 0.7);
}

.footer-certifications {
  display: flex;
  justify-content: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.certification-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(31, 41, 55, 0.1);
  color: #1f2937;
  padding: 0.5rem 1rem;
  border-radius: 50px;
  font-size: 0.75rem;
  font-weight: 500;
}

.certification-badge svg {
  width: 16px;
  height: 16px;
  color: #10b981; /* Green color for certifications */
}

/* Contact Section */
.contact-section {
  margin-top: 2.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid rgba(31, 41, 55, 0.1);
  text-align: right;
  margin-left: auto;
  margin-right: 0;
  width: fit-content;
}

.contact-header h4 {
  font-size: 1rem;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 1rem;
  letter-spacing: 0.05em;
}

.contact-info {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  align-items: flex-end;
}

.contact-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0;
  transition: all 0.3s ease;
  cursor: pointer;
}

.contact-item:hover {
  transform: translateX(5px);
}

.contact-item svg {
  color: rgba(31, 41, 55, 0.8);
  flex-shrink: 0;
}

.contact-link {
  color: rgba(31, 41, 55, 0.8);
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  transition: color 0.3s ease;
}

.contact-link:hover {
  color: #1f2937;
  text-decoration: underline;
}

/* Responsive Design */
@media (max-width: 1024px) {
  .home-container {
    margin-left: 0;
  }
  
  .main-header {
    left: 0;
  }
  
  .hero-content {
    grid-template-columns: 1fr;
    text-align: center;
  }
  
  .analytics-content {
    grid-template-columns: 1fr;
  }
  
  .hero-title {
    font-size: 2.5rem;
  }
  
  .hero-stats {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .footer-main {
    grid-template-columns: 1fr 2fr;
    gap: 3rem;
  }
  
  .footer-links {
    grid-template-columns: repeat(4, 1fr);
    gap: 2rem;
  }
  
  .chart-content {
    height: 350px;
  }
  
  .preview-chart {
    height: 180px;
  }
}

@media (max-width: 768px) {
  .header-content {
    padding: 1rem;
  }
  
  .main-nav {
    display: none;
  }
  
  .hero-title {
    font-size: 2rem;
  }
  
  .hero-stats {
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
  }
  
  .cta-actions {
    flex-direction: column;
    align-items: center;
  }
  
  .section-title {
    font-size: 2rem;
  }
  
  .cta-title {
    font-size: 2rem;
  }
  
  .footer-main {
    grid-template-columns: 1fr 1fr;
    gap: 3rem;
  }
  
  .footer-links {
    grid-template-columns: repeat(2, 1fr);
    gap: 2rem;
  }
  
  .footer-bottom-content {
    flex-direction: column;
    gap: 1.5rem;
  }
  

}

@media (max-width: 480px) {
  .hero-content,
  .features-section,
  .analytics-section,
  .trust-section,
  .cta-section,
  .footer-section {
    padding-left: 1rem;
    padding-right: 1rem;
  }
  
  .hero-title {
    font-size: 1.75rem;
  }
  
  .preview-metrics {
    grid-template-columns: 1fr;
  }
  
  .feature-card {
    padding: 1.5rem;
  }
  
  .footer-main {
    grid-template-columns: 1fr;
    gap: 2rem;
  }
  
  .footer-links {
    grid-template-columns: repeat(2, 1fr);
    gap: 1.5rem;
  }
  
  .footer-certifications {
    flex-direction: column;
    align-items: center;
  }
  
  .footer-bottom-content {
    flex-direction: column;
    gap: 1.5rem;
  }
  

}
</style> 