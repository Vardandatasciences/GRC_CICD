<template>
  <div class="active-policies-container">
    <div class="header-container">
      <h2>Active Policies</h2>
      
      <div class="framework-dropdown">
        <select id="framework" v-model="selectedFramework">
          <option value="" disabled selected hidden>Select Framework</option>
          <option value="ISO 27001">ISO 27001</option>
          <option value="NIST">NIST</option>
          <option value="SOC 2">SOC 2</option>
          <option value="GDPR">GDPR</option>
        </select>
      </div>
    </div>

    <div class="policies-table-container">
      <table class="policies-table">
        <thead>
          <tr>
            <th>Policy Name</th>
            <th>Version</th>
            <th>Category</th>
            <th>Framework</th>
            <th>Status</th>
            <th>Created By</th>
            <th>Created On</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="policy in filteredPolicies" :key="policy.id">
            <tr>
              <td @click="togglePolicyDocument(policy.id)" class="policy-name">
                {{ policy.name }}
                <i 
                  v-if="policy.subpolicies && policy.subpolicies.length" 
                  class="fas fa-chevron-right expand-icon" 
                  :class="{ 'rotated': expandedPolicies.includes(policy.id) }"
                  @click.stop="toggleSubpolicies(policy.id)"
                ></i>
              </td>
              <td>{{ policy.version }}</td>
              <td>{{ policy.category }}</td>
              <td>{{ policy.framework }}</td>
              <td>
                <span class="status-badge active">
                  Active
                </span>
              </td>
              <td>{{ policy.createdBy }}</td>
              <td>{{ policy.createdOn }}</td>
            </tr>
            
            <!-- Policy Document Section -->
            <tr v-if="expandedDocuments.includes(policy.id)">
              <td colspan="7">
                <div class="policy-document expanded">
                  <div class="policy-document-section">
                    <h4>Project Description</h4>
                    <p>{{ policy.description || 'This policy establishes guidelines and requirements for ' + policy.name.toLowerCase() + ' within the organization to ensure compliance with relevant regulations and standards.' }}</p>
                  </div>
                  <div class="policy-document-section">
                    <h4>Scope</h4>
                    <p>{{ policy.scope || 'This policy applies to all employees, contractors, and third-party entities that interact with organizational assets and systems.' }}</p>
                  </div>
                  <div class="policy-document-section">
                    <h4>Objectives</h4>
                    <p>{{ policy.objectives || 'To define roles and responsibilities, establish controls, and provide guidance for maintaining compliance with ' + policy.framework + ' standards.' }}</p>
                  </div>
                </div>
              </td>
            </tr>
            
            <!-- Subpolicies -->
            <template v-if="policy.subpolicies && policy.subpolicies.length">
              <template v-for="(subpolicy, index) in getActiveSubpolicies(policy)" :key="`${policy.id}-sub-${index}`">
                <tr class="subpolicy-row" :class="{ 'expanded': expandedPolicies.includes(policy.id) }">
                  <td @click="toggleSubpolicyDocument(`${policy.id}-sub-${index}`)">{{ subpolicy.name }}</td>
                  <td>{{ subpolicy.version || policy.version }}</td>
                  <td>{{ subpolicy.category || policy.category }}</td>
                  <td>{{ subpolicy.framework || policy.framework }}</td>
                  <td>
                    <span class="status-badge active">
                      Active
                    </span>
                  </td>
                  <td>{{ subpolicy.createdBy || policy.createdBy }}</td>
                  <td>{{ subpolicy.createdOn || policy.createdOn }}</td>
                </tr>
                
                <!-- Subpolicy Document Section -->
                <tr v-if="expandedDocuments.includes(`${policy.id}-sub-${index}`)">
                  <td colspan="7">
                    <div class="policy-document expanded">
                      <div class="policy-document-section">
                        <h4>Project Description</h4>
                        <p>{{ subpolicy.description || 'This is a sub-policy of ' + policy.name + ' that focuses specifically on ' + subpolicy.name.toLowerCase() + '.' }}</p>
                      </div>
                      <div class="policy-document-section">
                        <h4>Scope</h4>
                        <p>{{ subpolicy.scope || 'This sub-policy applies to all aspects of ' + subpolicy.name.toLowerCase() + ' within the organization.' }}</p>
                      </div>
                      <div class="policy-document-section">
                        <h4>Objectives</h4>
                        <p>{{ subpolicy.objectives || 'To ensure consistent implementation and management of ' + subpolicy.name + ' controls in alignment with ' + policy.framework + '.' }}</p>
                      </div>
                    </div>
                  </td>
                </tr>
              </template>
            </template>
          </template>
        </tbody>
      </table>
      
      <!-- Empty state when no policies match the filter -->
      <div class="empty-state" v-if="filteredPolicies.length === 0">
        <i class="fas fa-file-alt"></i>
        <p>No active policies found for the selected framework</p>
      </div>
    </div>
  </div>
</template>

<script>
import { API_ENDPOINTS } from '../../config/api.js'
import { ref, computed } from 'vue'
import './ActivePolicies.css'

export default {
  name: 'ActivePolicies',
  setup() {
    const selectedFramework = ref('')
    const expandedPolicies = ref([])
    const expandedDocuments = ref([])
    
    // Sample policies data with subpolicies (only active policies)
    const policies = [
      {
        id: 'POL-001',
        name: 'Information Security Policy',
        version: '1.2',
        category: 'Security',
        framework: 'ISO 27001',
        status: 'Approved',
        createdBy: 'John Smith',
        createdOn: '2023-10-15',
        description: 'This policy outlines the organization\'s approach to information security management.',
        scope: 'All information assets owned, controlled, or processed by the organization.',
        objectives: 'To establish a framework for protecting the confidentiality, integrity, and availability of information.',
        subpolicies: [
          {
            name: 'Data Classification Policy',
            version: '1.1',
            status: 'Approved',
            description: 'Guidelines for classifying organizational data based on sensitivity and criticality.'
          },
          {
            name: 'Access Control Policy',
            version: '1.0',
            status: 'Approved',
            description: 'Rules and guidelines for controlling access to information systems and data.'
          }
        ]
      },
      {
        id: 'POL-002',
        name: 'Data Protection Policy',
        version: '2.0',
        category: 'Privacy',
        framework: 'GDPR',
        status: 'Under Review',
        createdBy: 'Sarah Johnson',
        createdOn: '2023-11-03',
        subpolicies: [
          {
            name: 'Data Subject Rights Procedure',
            version: '1.2',
            status: 'Under Review',
            description: 'Procedures for handling data subject access requests and other rights.'
          }
        ]
      },
      {
        id: 'POL-005',
        name: 'Risk Management Policy',
        version: '1.3',
        category: 'Governance',
        framework: 'SOC 2',
        status: 'Under Review',
        createdBy: 'David Wilson',
        createdOn: '2023-11-18'
      },
      {
        id: 'POL-006',
        name: 'Business Continuity Policy',
        version: '2.1',
        category: 'Operations',
        framework: 'ISO 27001',
        status: 'Approved',
        createdBy: 'Jennifer Lee',
        createdOn: '2023-10-30'
      }
    ]
    
    const isActivePolicy = (status) => {
      return status === 'Approved' || status === 'Under Review';
    }
    
    const filteredPolicies = computed(() => {      
      return policies.filter(policy => {
        const matchesFramework = selectedFramework.value === '' || policy.framework === selectedFramework.value;
        return isActivePolicy(policy.status) && matchesFramework;
      });
    });
    
    const getActiveSubpolicies = (policy) => {
      if (!policy.subpolicies) return [];
      return policy.subpolicies.filter(subpolicy => isActivePolicy(subpolicy.status));
    }
    
    const toggleSubpolicies = (policyId) => {
      if (expandedPolicies.value.includes(policyId)) {
        expandedPolicies.value = expandedPolicies.value.filter(id => id !== policyId);
      } else {
        expandedPolicies.value.push(policyId);
        sendPushNotification({
          title: 'Policy Expanded',
          message: `Subpolicies for policy ${policyId} are now visible`,
          category: 'policy',
          priority: 'low',
          user_id: 'default_user'
        });
      }
    }
    
    const togglePolicyDocument = (policyId) => {
      if (expandedDocuments.value.includes(policyId)) {
        expandedDocuments.value = expandedDocuments.value.filter(id => id !== policyId);
      } else {
        expandedDocuments.value.push(policyId);
        const policy = policies.find(p => p.id === policyId);
        if (policy) {
          sendPushNotification({
            title: 'Policy Document Opened',
            message: `Details for policy "${policy.name}" are now visible`,
            category: 'policy',
            priority: 'low',
            user_id: 'default_user'
          });
        }
      }
    }
    
    const toggleSubpolicyDocument = (subpolicyId) => {
      if (expandedDocuments.value.includes(subpolicyId)) {
        expandedDocuments.value = expandedDocuments.value.filter(id => id !== subpolicyId);
      } else {
        expandedDocuments.value.push(subpolicyId);
        const [policyId, , index] = subpolicyId.split('-');
        const policy = policies.find(p => p.id === policyId);
        if (policy && policy.subpolicies && policy.subpolicies[index]) {
          sendPushNotification({
            title: 'Subpolicy Document Opened',
            message: `Details for subpolicy "${policy.subpolicies[index].name}" are now visible`,
            category: 'policy',
            priority: 'low',
            user_id: 'default_user'
          });
        }
      }
    }
    
    const sendPushNotification = async (notificationData) => {
      try {
        const response = await fetch(API_ENDPOINTS.PUSH_NOTIFICATION, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(notificationData)
        });
        if (response.ok) {
          console.log('Push notification sent successfully');
        } else {
          console.error('Failed to send push notification');
        }
      } catch (error) {
        console.error('Error sending push notification:', error);
      }
    }
    
    return {
      selectedFramework,
      policies,
      filteredPolicies,
      expandedPolicies,
      expandedDocuments,
      toggleSubpolicies,
      togglePolicyDocument,
      toggleSubpolicyDocument,
      getActiveSubpolicies,
      sendPushNotification
    }
  }
}
</script> 