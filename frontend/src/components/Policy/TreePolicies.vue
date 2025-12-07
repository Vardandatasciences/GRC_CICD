<template>
  <div class="tree-container">
      <div class="tree-header" style="justify-content: center;">
        <div class="dropdown-container">
          <div class="dropdown-label-wrapper">
            <label class="framework-label">Select Framework</label>
            <CustomDropdown 
              :config="frameworkDropdownConfig" 
              v-model="treeSelectedFramework"
              class="framework-dropdown"
            />
          </div>
          <div class="helper-text">{{ frameworkDropdownConfig.helperText }}</div>
        </div>
      </div>
      <div style="display: flex; justify-content: center; gap: 16px; margin-bottom: 24px;">
        <button class="expand-btn" @click="expandAll">EXPAND ALL</button>
        <button class="expand-btn" @click="collapseAll">COLLAPSE</button>
      </div>
    <!-- Error state -->
    <div v-if="error" class="error-message">
      <p>{{ error }}</p>
      <button @click="retryLoad" class="retry-btn">Retry</button>
    </div>
    
    <!-- Tree content -->
    <div v-else-if="selectedFrameworkData && (!selectedFrameworkData.policies || selectedFrameworkData.policies.length === 0)" class="no-policies-message">
      <h3>{{ selectedFrameworkData.FrameworkName }}</h3>
      <p>No policies found for this framework.</p>
    </div>
    
    <svg v-else class="tree-svg" :viewBox="svgViewBox">
      <!-- Always show the framework node -->
      <g v-if="selectedFrameworkData" class="node-group">
        <rect class="framework-big-node" :x="fwX" :y="fwY" width="220" height="80" rx="18"
          fill="#fff" stroke="url(#frameworkBorderGradient)" stroke-width="4"/>
        <foreignObject :x="fwX+10" :y="fwY+10" width="200" height="60">
          <div class="big-node-text framework-text">{{ selectedFrameworkData.FrameworkName }}</div>
        </foreignObject>
      </g>
      <template v-if="level >= 1">
        <defs>
          <linearGradient id="frameworkGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#4f7cff;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#4f46e5;stop-opacity:1" />
          </linearGradient>
          <linearGradient id="policyGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#34d399;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#10b981;stop-opacity:1" />
          </linearGradient>
          <linearGradient id="subpolicyGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#fbbf24;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#f59e0b;stop-opacity:1" />
          </linearGradient>
          <linearGradient id="policyBorderGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#34d399"/>
            <stop offset="100%" stop-color="#10b981"/>
          </linearGradient>
          <linearGradient id="subpolicyBorderGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#fbbf24"/>
            <stop offset="100%" stop-color="#f59e0b"/>
          </linearGradient>
          <linearGradient id="frameworkBorderGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#ff6a3d"/>
            <stop offset="100%" stop-color="#ffd600"/>
          </linearGradient>
        </defs>
        <!-- Central junction logic for framework to policies -->
        <g v-if="policyNodes.length">
          <!-- Vertical trunk from top to bottom policy -->
          <line class="tree-line" :x1="junction.x" :y1="policyNodes[0].y + 34" :x2="junction.x" :y2="policyNodes[policyNodes.length - 1].y + 34" />
          <!-- Horizontal line from Decision to trunk (at framework center) -->
          <line class="tree-line" :x1="fwX + 220" :y1="fwY + 40" :x2="junction.x" :y2="fwY + 40" />
          <!-- Circle at intersection -->
          <circle :cx="junction.x" :cy="fwY + 40" r="6" fill="#6b7280" opacity="0.18" />
          <!-- Horizontal lines from trunk to each policy (90-degree T-junction) -->
          <line v-for="policy in policyNodes" :key="'junction-'+policy.id" class="tree-line"
            :x1="junction.x" :y1="policy.y + 34" :x2="policy.x" :y2="policy.y + 34" />
          <!-- Circle at each T-junction for policies -->
          <circle v-for="policy in policyNodes" :key="'junction-circle-'+policy.id" :cx="junction.x" :cy="policy.y + 34" r="5" fill="#6b7280" opacity="0.18" />
        </g>
        <!-- Special case: single policy, draw right-angle connector with junctions (no extra lines) -->
        <g v-if="policyNodes.length === 1">
          <!-- Horizontal line from framework to junction -->
          <line class="tree-line" :x1="fwX + 220" :y1="fwY + 40" :x2="junction.x - 16" :y2="fwY + 40" />
          <!-- Circle at framework junction -->
          <circle :cx="junction.x - 16" :cy="fwY + 40" r="6" fill="#6b7280" opacity="0.18" />
          <!-- Vertical line from junction to policy level (only if needed) -->
          <line v-if="fwY + 40 !== policyNodes[0].y + 34" class="tree-line" :x1="junction.x - 16" :y1="fwY + 40" :x2="junction.x - 16" :y2="policyNodes[0].y + 34" />
          <!-- Circle at policy junction (only if vertical line exists) -->
          <circle v-if="fwY + 40 !== policyNodes[0].y + 34" :cx="junction.x - 16" :cy="policyNodes[0].y + 34" r="6" fill="#6b7280" opacity="0.18" />
          <!-- Short horizontal line from junction to policy box (with gap) -->
          <line class="tree-line" :x1="junction.x - 16" :y1="policyNodes[0].y + 34" :x2="policyNodes[0].x - 16" :y2="policyNodes[0].y + 34" />
          <line class="tree-line" :x1="policyNodes[0].x - 16" :y1="policyNodes[0].y + 34" :x2="policyNodes[0].x" :y2="policyNodes[0].y + 34" />
        </g>
        <!-- Policy Nodes -->
        <g v-for="policy in policyNodes" :key="policy.id" class="node-group">
          <rect class="big-node" :x="policy.x" :y="policy.y" width="180" height="60" rx="14"
            fill="#fff" stroke="url(#policyBorderGradient)" stroke-width="3"/>
          <foreignObject :x="policy.x+8" :y="policy.y+8" width="164" height="44">
            <div class="big-node-text">{{ policy.title }}</div>
          </foreignObject>
          <!-- Central junction logic for policy to subpolicies -->
          <g v-if="policy.subpolicies && policy.subpolicies.length">
            <!-- Vertical line from policy to subpolicy junction (90-degree) -->
            <line class="tree-line" :x1="policy.x + 180" :y1="policy.y + 34" :x2="policy.x + 180 + 40" :y2="policy.y + 34" />
            <!-- Vertical trunk for subpolicies -->
            <line class="tree-line" :x1="policy.x + 180 + 40" :y1="policy.subpolicies[0].y + 34" :x2="policy.x + 180 + 40" :y2="policy.subpolicies[policy.subpolicies.length - 1].y + 34" />
            <!-- Circle at subpolicy junction (T-junction) -->
            <circle :cx="policy.x + 180 + 40" :cy="policy.y + 34" r="5" fill="#6b7280" opacity="0.18" />
            <!-- Horizontal lines from trunk to each subpolicy (90-degree) -->
            <line v-for="sub in policy.subpolicies" :key="'junction-'+policy.id+'-'+sub.id" class="tree-line"
              :x1="policy.x + 180 + 40" :y1="sub.y + 34" :x2="sub.x" :y2="sub.y + 34" />
            <!-- Circle at each T-junction for subpolicies -->
            <circle v-for="sub in policy.subpolicies" :key="'junction-circle-'+policy.id+'-'+sub.id" :cx="policy.x + 180 + 40" :cy="sub.y + 34" r="4" fill="#6b7280" opacity="0.18" />
          </g>
          <!-- Special case: single subpolicy, draw direct horizontal line with circle -->
          <g v-for="policy in policyNodes" :key="'single-sub-'+policy.id">
            <template v-if="policy.subpolicies && policy.subpolicies.length === 1">
              <line class="tree-line" :x1="policy.x + 180" :y1="policy.y + 34" :x2="policy.subpolicies[0].x" :y2="policy.subpolicies[0].y + 34" />
              <circle :cx="(policy.x + 180 + policy.subpolicies[0].x) / 2" :cy="(policy.y + 34 + policy.subpolicies[0].y + 34) / 2" r="5" fill="#6b7280" opacity="0.18" />
            </template>
          </g>
        </g>
        <!-- Level 2 - Subpolicies -->
        <g v-show="level >= 2 && subpolicyNodes.length" class="fade-in">
          <template v-for="policy in policyNodes" :key="'subs-'+policy.id">
            <g v-for="sub in policy.subpolicies" :key="sub.id" class="node-group">
              <rect class="big-node" :x="sub.x" :y="sub.y" width="180" height="60" rx="14"
                fill="#fff" stroke="url(#subpolicyBorderGradient)" stroke-width="3"/>
              <foreignObject :x="sub.x+8" :y="sub.y+8" width="164" height="44">
                <div class="big-node-text">{{ sub.title }}</div>
              </foreignObject>
            </g>
          </template>
        </g>
      </template>
    </svg>
  </div>
</template>
  
<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import axios from 'axios'
import CustomDropdown from '../CustomDropdown.vue'
import { API_ENDPOINTS, API_BASE_URL } from '@/config/api.js'
import policyDataService from '@/services/policyService'
const fwY = computed(() => {
  // Vertically center the framework node regardless of policy count
  const height = Number(svgViewBox.value.split(' ')[3]);
  return height / 2 - 40; // 40 = half of node height (80)
});
const level = ref(1)

const frameworks = ref([])
      const treeSelectedFramework = ref('')
const selectedFrameworkData = ref(null)
      const error = ref(null)

const svgViewBox = computed(() => {
  const minHeight = 700;
  const policyCount = treePolicies.value.length || 1;
  const policyGap = 120;
  const height = Math.max(minHeight, policyCount * policyGap + 200);
  return `0 0 1200 ${height}`;
});

const fwX = 60; // Framework node on the far left

// Fetch frameworks
const fetchFrameworks = async () => {
  try {
    error.value = null
    console.log('🔍 [TreePolicies] Checking for cached frameworks...')

    if (!window.policyDataFetchPromise && !policyDataService.hasFrameworksListCache()) {
      console.log('🚀 [TreePolicies] Starting policy prefetch (user navigated directly)...')
      window.policyDataFetchPromise = policyDataService.fetchAllPolicyData()
    }

    if (window.policyDataFetchPromise) {
      console.log('⏳ [TreePolicies] Waiting for policy prefetch to complete...')
      try {
        await window.policyDataFetchPromise
        console.log('✅ [TreePolicies] Prefetch completed')
      } catch (prefetchError) {
        console.warn('⚠️ [TreePolicies] Prefetch failed, will fetch directly from API', prefetchError)
      }
    }

    if (policyDataService.hasFrameworksListCache()) {
      console.log('✅ [TreePolicies] Using cached frameworks')
      const cachedFrameworks = policyDataService.getFrameworksList() || []
      frameworks.value = cachedFrameworks.map(fw => ({
        id: fw.FrameworkId || fw.id,
        title: fw.FrameworkName || fw.name
      }))

      await checkSelectedFrameworkFromSession()
      return
    }

    console.log('⚠️ [TreePolicies] No cached data found, fetching frameworks from API...')
    const response = await axios.get(API_ENDPOINTS.FRAMEWORKS)
    frameworks.value = response.data.map(fw => ({
      id: fw.FrameworkId,
      title: fw.FrameworkName
    }))

    policyDataService.setFrameworksList(response.data)

    await checkSelectedFrameworkFromSession()
  } catch (err) {
    console.error('Error fetching frameworks:', err)
    error.value = 'Failed to load frameworks. Please try again.'
  }
}

      // Check for selected framework from session and set it as default
      const checkSelectedFrameworkFromSession = async () => {
        try {
          console.log('🔍 DEBUG: Checking for selected framework from session in TreePolicies...')
          const response = await axios.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED)
          console.log('📊 DEBUG: Selected framework response:', response.data)
          
          if (response.data && response.data.success) {
            // Check if a framework is selected (not null)
            if (response.data.frameworkId) {
              const sessionFrameworkId = response.data.frameworkId
              console.log('✅ DEBUG: Found selected framework in session:', sessionFrameworkId)
              
              // Check if this framework exists in our loaded frameworks
              const frameworkExists = frameworks.value.find(f => f.id == sessionFrameworkId)
              
              if (frameworkExists) {
                treeSelectedFramework.value = frameworkExists.title
                console.log('✅ DEBUG: Set treeSelectedFramework from session:', frameworkExists.title)
                
                // Load framework details
                await fetchFrameworkDetails(frameworkExists.id)
              } else {
                console.log('⚠️ DEBUG: Framework from session not found in loaded frameworks')
              }
            } else {
              // "All Frameworks" is selected (frameworkId is null)
              console.log('ℹ️ DEBUG: No framework selected in session (All Frameworks selected)')
              console.log('🌐 DEBUG: Clearing framework selection to show all frameworks')
              treeSelectedFramework.value = null
              selectedFrameworkData.value = null
            }
          } else {
            console.log('ℹ️ DEBUG: No framework found in session')
            treeSelectedFramework.value = null
          }
        } catch (error) {
          console.error('❌ DEBUG: Error checking selected framework from session:', error)
          treeSelectedFramework.value = null
        }
      }
  
      // Fetch framework details including policies
      const fetchFrameworkDetails = async (frameworkId) => {
        try {
          const url = API_ENDPOINTS.FRAMEWORK_GET_POLICIES_LIST(frameworkId)
          console.log('Calling API endpoint:', url)
          const response = await axios.get(url)
          console.log('Framework policies response:', response.data)
          console.log('Response structure:', {
            hasData: !!response.data,
            hasFramework: !!response.data?.framework,
            hasPolicies: !!response.data?.policies,
            policiesType: typeof response.data?.policies,
            policiesLength: response.data?.policies?.length
          })
          
          // Check if response has the expected structure
          if (!response.data) {
            throw new Error('No data received from API')
          }
          
          if (!response.data.framework) {
            console.error('Missing framework data in response:', response.data)
            throw new Error('Framework data not found in API response')
          }
          
          if (!response.data.policies) {
            console.error('Missing policies data in response:', response.data)
            // If no policies, create empty array instead of throwing error
            response.data.policies = []
          }
          
          // Ensure policies is an array
          if (!Array.isArray(response.data.policies)) {
            console.error('Policies is not an array:', response.data.policies)
            response.data.policies = []
          }
          
          // Transform the response to match expected structure
          const policies = await Promise.all((response.data.policies || []).map(async (policy) => {
            // Fetch subpolicies for each policy
            let subpolicies = []
            try {
              const subpoliciesResponse = await axios.get(`${API_BASE_URL}/api/policies/${policy.id}/get-subpolicies/`)
              subpolicies = subpoliciesResponse.data.map(subpolicy => ({
                SubPolicyId: subpolicy.SubPolicyId,
                SubPolicyName: subpolicy.SubPolicyName,
                Description: subpolicy.Description,
                Status: subpolicy.Status,
                CreatedByName: subpolicy.CreatedByName,
                CreatedByDate: subpolicy.CreatedByDate,
                Identifier: subpolicy.Identifier,
                PermanentTemporary: subpolicy.PermanentTemporary,
                Control: subpolicy.Control
              }))
            } catch (subpolicyError) {
              console.warn(`Could not fetch subpolicies for policy ${policy.id}:`, subpolicyError)
            }
            
            return {
              PolicyId: policy.id,
              PolicyName: policy.name,
              PolicyDescription: policy.description,
              Department: policy.category,
              ActiveInactive: policy.status,
              Entities: policy.Entities,
              subpolicies: subpolicies
            }
          }))
          
          selectedFrameworkData.value = {
            FrameworkId: response.data.framework.id,
            FrameworkName: response.data.framework.name,
            FrameworkDescription: response.data.framework.description,
            Category: response.data.framework.category,
            policies: policies
          }
        } catch (err) {
          console.error('Error fetching framework details:', err)
          error.value = 'Failed to load framework details. Please try again.'
          selectedFrameworkData.value = null
        }
      }
  
onMounted(async () => {
  await fetchFrameworks()
  // Framework selection is now handled by checkSelectedFrameworkFromSession
})

      watch(treeSelectedFramework, async (newFramework) => {
        if (newFramework) {
          const framework = frameworks.value.find(f => f.title === newFramework)
          if (framework) {
            // Save the selected framework to session
            try {
              const userId = localStorage.getItem('user_id') || 'default_user'
              console.log('🔍 DEBUG: Saving framework to session in TreePolicies:', framework.id)
              
              const response = await axios.post(API_ENDPOINTS.FRAMEWORK_SET_SELECTED, {
                frameworkId: framework.id,
                userId: userId
              })
              
              if (response.data && response.data.success) {
                console.log('✅ DEBUG: Framework saved to session successfully in TreePolicies')
                console.log('🔑 DEBUG: Session key:', response.data.sessionKey)
              } else {
                console.error('❌ DEBUG: Failed to save framework to session in TreePolicies')
              }
            } catch (error) {
              console.error('❌ DEBUG: Error saving framework to session in TreePolicies:', error)
            }
            
            await fetchFrameworkDetails(framework.id)
          }
        } else {
          selectedFrameworkData.value = null
        }
      })
      
      const treePolicies = computed(() => {
        if (!selectedFrameworkData.value) return []
  return selectedFrameworkData.value.policies || []
})

const policyNodes = computed(() => {
  const policies = treePolicies.value;
  if (!policies.length) return [];
  const count = policies.length;
  const startY = 100;
  const endY = Number(svgViewBox.value.split(' ')[3]) - 100 - 48;
  const gap = (endY - startY) / (count > 1 ? count - 1 : 1) + 30;
  return policies.map((policy, idx) => {
    const y = startY + idx * gap;
    return {
      id: policy.PolicyId,
      title: policy.PolicyName,
      x: 320, // Policies in a vertical column to the right
      y,
      subpolicies: (policy.subpolicies || []).map((sub, sIdx) => {
        const subCount = policy.subpolicies.length;
        const subStartY = y - (subCount > 1 ? 40 : 0);
        const subGap = subCount > 1 ? 110 : 0;
        return {
          id: sub.SubPolicyId,
          title: sub.SubPolicyName,
          x: 600, // Subpolicies further right
          y: subStartY + sIdx * subGap
        };
      })
    };
  });
});

const subpolicyNodes = computed(() => {
  return policyNodes.value.flatMap(p => p.subpolicies);
});

      const frameworkDropdownConfig = computed(() => {
        // Only show the user's stored framework in the dropdown if it exists
        const sessionFrameworkId = treeSelectedFramework.value;
        const sessionFramework = frameworks.value.find(f => f.title === sessionFrameworkId);
        
        // Create values array based on whether we have a stored framework
        let values = [];
        
        if (sessionFramework) {
          // If we have a stored framework, only show that one
          values = [
            { value: sessionFramework.title, label: sessionFramework.title }
          ];
        } else {
          // If no framework is selected, show all frameworks
          values = frameworks.value.map(fw => ({
            value: fw.title,
            label: fw.title
          }));
        }
        
        return {
          label: '',
          name: 'framework',
          defaultValue: 'Choose a framework...',
          values: values,
          helperText: sessionFramework ? 
            `Currently viewing: ${sessionFramework.title}` : 
            'Please select a framework to view its policies and subpolicies.'
        };
      })
      
function expandAll() {
  level.value = 2
}

function collapseAll() {
  level.value = 0;
}

// Retry function
const retryLoad = async () => {
  error.value = null
  await fetchFrameworks()
  if (frameworks.value.length > 0 && treeSelectedFramework.value) {
    const framework = frameworks.value.find(f => f.title === treeSelectedFramework.value)
    if (framework) {
      await fetchFrameworkDetails(framework.id)
    }
  }
}

// Add a computed for the junction point
const junction = computed(() => {
  // Junction is to the right of the framework node, vertically centered between top and bottom policy
  if (!policyNodes.value.length) return { x: fwX + 220 + 40, y: fwY.value + 40 };
  const top = policyNodes.value[0].y + 30;
  const bottom = policyNodes.value[policyNodes.value.length - 1].y + 30;
  const x = fwX + 220 + 40; // 40px to the right of framework node
  const y = (top + bottom) / 2;
  return { x, y };
});
  </script>
  
  <style scoped>
@import './TreePolicies.css';

.tree-container {
  width: 100%;
  min-height: 100vh;
  background:  #ffffff;
  padding: 0;
  margin: 0;
  overflow-x: visible;
}
.tree-svg {
  width: 100%;
  height: 700px;
  display: block;
  margin: 0 auto;
  min-width: 0;
}
.framework-node, .policy-node, .subpolicy-node {
  filter: drop-shadow(0 8px 24px rgba(79, 124, 255, 0.10));
  transition: filter 0.2s, transform 0.2s;
}
.node-group:hover .framework-node,
.node-group:hover .policy-node,
.node-group:hover .subpolicy-node {
  transform: scale(1.07);
  filter: drop-shadow(0 12px 32px rgba(79, 124, 255, 0.18));
}
.framework-text, .policy-text, .subpolicy-text {
  font-size: 1.25rem;
  font-weight: 700;
  letter-spacing: 0.5px;
}
.framework-text {
  font-size: 1.5rem;
}
.policy-text {
  font-size: 1.25rem;
}
.subpolicy-text {
  font-size: 1.1rem;
}
.framework-big-node {
  /* SVG rect, so style via attributes */
  filter: drop-shadow(0 4px 16px rgba(255, 106, 61, 0.12));
  transition: filter 0.2s, transform 0.2s;
}
.framework-text {
  font-size: 1.1rem;
  font-weight: 700;
  color: #222;
  text-align: center;
    width: 100%;
  height: 100%;
    display: flex;
    align-items: center;
  justify-content: center;
  word-break: break-word;
  white-space: pre-line;
}
.big-node {
  /* SVG rect, so style via attributes */
  filter: drop-shadow(0 2px 8px rgba(52, 211, 153, 0.10));
  transition: filter 0.2s, transform 0.2s;
}
.big-node-text {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  font-size: 1.15rem;
  font-weight: 600;
  color: #374151;
  word-break: break-word;
  overflow-wrap: anywhere;
  white-space: normal;
  padding: 10px 12px;
  line-height: 1.5;
}
  </style> 