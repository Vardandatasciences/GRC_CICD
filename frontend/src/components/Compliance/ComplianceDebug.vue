<template>
  <div class="compliance-debug">
    <h2>Compliance API Debug</h2>
    
    <div class="debug-section">
      <h3>Test Frameworks API</h3>
      <button @click="testFrameworks" :disabled="loading">Test Frameworks</button>
      <div v-if="frameworksResult" class="result">
        <h4>Frameworks Result:</h4>
        <pre>{{ JSON.stringify(frameworksResult, null, 2) }}</pre>
      </div>
    </div>

    <div class="debug-section" v-if="selectedFramework">
      <h3>Test Policies API</h3>
      <p>Selected Framework: {{ selectedFramework }}</p>
      <button @click="testPolicies" :disabled="loading">Test Policies</button>
      <div v-if="policiesResult" class="result">
        <h4>Policies Result:</h4>
        <pre>{{ JSON.stringify(policiesResult, null, 2) }}</pre>
      </div>
    </div>

    <div class="debug-section" v-if="selectedPolicy">
      <h3>Test SubPolicies API</h3>
      <p>Selected Policy: {{ selectedPolicy }}</p>
      <button @click="testSubPolicies" :disabled="loading">Test SubPolicies</button>
      <div v-if="subPoliciesResult" class="result">
        <h4>SubPolicies Result:</h4>
        <pre>{{ JSON.stringify(subPoliciesResult, null, 2) }}</pre>
      </div>
    </div>

    <div class="debug-section">
      <h3>Framework Selection</h3>
      <select v-model="selectedFramework" @change="onFrameworkChange">
        <option value="">Select Framework</option>
        <option v-for="fw in frameworks" :key="fw.id" :value="fw.id">
          {{ fw.name }}
        </option>
      </select>
    </div>

    <div class="debug-section" v-if="selectedFramework">
      <h3>Policy Selection</h3>
      <select v-model="selectedPolicy" @change="onPolicyChange">
        <option value="">Select Policy</option>
        <option v-for="policy in policies" :key="policy.id" :value="policy.id">
          {{ policy.name }}
        </option>
      </select>
    </div>

    <div class="debug-section" v-if="selectedPolicy">
      <h3>SubPolicy Selection</h3>
      <select v-model="selectedSubPolicy">
        <option value="">Select SubPolicy</option>
        <option v-for="sp in subPolicies" :key="sp.id" :value="sp.id">
          {{ sp.name }}
        </option>
      </select>
    </div>

    <div v-if="error" class="error">
      <h4>Error:</h4>
      <pre>{{ error }}</pre>
    </div>
  </div>
</template>

<script>
import { complianceService } from '@/services/api';

export default {
  name: 'ComplianceDebug',
  data() {
    return {
      loading: false,
      error: null,
      frameworks: [],
      policies: [],
      subPolicies: [],
      selectedFramework: '',
      selectedPolicy: '',
      selectedSubPolicy: '',
      frameworksResult: null,
      policiesResult: null,
      subPoliciesResult: null
    }
  },
  async mounted() {
    await this.loadFrameworks();
  },
  methods: {
    async testFrameworks() {
      try {
        this.loading = true;
        this.error = null;
        const response = await complianceService.getComplianceFrameworks();
        this.frameworksResult = response.data;
        console.log('Frameworks API Response:', response.data);
      } catch (error) {
        this.error = error.message;
        console.error('Frameworks API Error:', error);
      } finally {
        this.loading = false;
      }
    },
    async testPolicies() {
      if (!this.selectedFramework) return;
      try {
        this.loading = true;
        this.error = null;
        const response = await complianceService.getCompliancePolicies(this.selectedFramework);
        this.policiesResult = response.data;
        console.log('Policies API Response:', response.data);
      } catch (error) {
        this.error = error.message;
        console.error('Policies API Error:', error);
      } finally {
        this.loading = false;
      }
    },
    async testSubPolicies() {
      if (!this.selectedPolicy) return;
      try {
        this.loading = true;
        this.error = null;
        const response = await complianceService.getComplianceSubPolicies(this.selectedPolicy);
        this.subPoliciesResult = response.data;
        console.log('SubPolicies API Response:', response.data);
      } catch (error) {
        this.error = error.message;
        console.error('SubPolicies API Error:', error);
      } finally {
        this.loading = false;
      }
    },
    async loadFrameworks() {
      try {
        const response = await complianceService.getComplianceFrameworks();
        if (response.data.success && response.data.frameworks) {
          this.frameworks = response.data.frameworks.map(fw => ({
            id: fw.id || fw.FrameworkId,
            name: fw.name || fw.FrameworkName
          }));
        } else if (Array.isArray(response.data)) {
          this.frameworks = response.data.map(fw => ({
            id: fw.id || fw.FrameworkId,
            name: fw.name || fw.FrameworkName
          }));
        }
      } catch (error) {
        console.error('Error loading frameworks:', error);
      }
    },
    async onFrameworkChange() {
      this.selectedPolicy = '';
      this.selectedSubPolicy = '';
      this.policies = [];
      this.subPolicies = [];
      if (this.selectedFramework) {
        await this.loadPolicies();
      }
    },
    async onPolicyChange() {
      this.selectedSubPolicy = '';
      this.subPolicies = [];
      if (this.selectedPolicy) {
        await this.loadSubPolicies();
      }
    },
    async loadPolicies() {
      try {
        const response = await complianceService.getCompliancePolicies(this.selectedFramework);
        if (response.data.success && response.data.policies) {
          this.policies = response.data.policies.map(p => ({
            id: p.id || p.PolicyId,
            name: p.name || p.PolicyName
          }));
        } else if (Array.isArray(response.data)) {
          this.policies = response.data.map(p => ({
            id: p.id || p.PolicyId,
            name: p.name || p.PolicyName
          }));
        }
      } catch (error) {
        console.error('Error loading policies:', error);
      }
    },
    async loadSubPolicies() {
      try {
        const response = await complianceService.getComplianceSubPolicies(this.selectedPolicy);
        if (response.data.success && response.data.subpolicies) {
          this.subPolicies = response.data.subpolicies.map(sp => ({
            id: sp.id || sp.SubPolicyId,
            name: sp.name || sp.SubPolicyName
          }));
        } else if (Array.isArray(response.data)) {
          this.subPolicies = response.data.map(sp => ({
            id: sp.id || sp.SubPolicyId,
            name: sp.name || sp.SubPolicyName
          }));
        }
      } catch (error) {
        console.error('Error loading subpolicies:', error);
      }
    }
  }
}
</script>

<style scoped>
.compliance-debug {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.debug-section {
  margin-bottom: 30px;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
}

.debug-section h3 {
  margin-top: 0;
  color: #333;
}

.debug-section button {
  padding: 10px 20px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-right: 10px;
}

.debug-section button:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

.debug-section select {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  min-width: 200px;
}

.result {
  margin-top: 15px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #e9ecef;
}

.result pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 400px;
  overflow-y: auto;
}

.error {
  margin-top: 20px;
  padding: 15px;
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
  color: #721c24;
}

.error pre {
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
