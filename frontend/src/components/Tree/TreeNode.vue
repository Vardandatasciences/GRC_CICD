<template>
  <div class="tree-branch" :data-level="level" :data-index="siblingIndex" :data-count="siblingCount">
    <!-- Node wrapper with connector -->
    <div class="node-wrapper">
       <div 
        class="node-box" 
        :class="[nodeClass, { 'clickable': hasChildren, 'expanded': isExpanded }]" 
        @click="toggleNode"
      >
         <i :class="nodeIcon"></i>
         <span :title="getNodeTitle()">{{ getNodeTitle() }}</span>
        <i v-if="hasChildren" class="fas fa-chevron-down expand-icon" :class="{ 'rotated': isExpanded }"></i>
      </div>
      
      <!-- Vertical connector line to children -->
      <div v-if="isExpanded && (children.length > 0 || loading)" class="vertical-line"></div>
    </div>
    
    <!-- Children container -->
    <div v-if="isExpanded" :class="['children-wrapper', { 'nested-children': level > 1 }]"><!-- add class for nested styling -->
      <div v-if="loading" class="loading-children">
        <i class="fas fa-spinner fa-spin"></i>
      </div>
      
      <template v-else-if="children.length > 0">
        <!-- Horizontal connector line for multiple children -->
        <div v-if="children.length > 1" class="horizontal-line"></div>
        
        <div class="tree-children">
          <TreeNode 
            v-for="(child, idx) in children" 
            :key="child.id"
            :node="child"
            :level="level + 1"
            :sibling-index="idx"
            :sibling-count="children.length"
            @node-click="$emit('node-click', $event)"
          />
        </div>
      </template>
    </div>
  </div>
</template>

<script>
import { API_ENDPOINTS } from '../../config/api.js'
import axios from 'axios'

export default {
  name: 'TreeNode',
  props: {
    node: {
      type: Object,
      required: true
    },
    level: {
      type: Number,
      default: 1
    },
    siblingIndex: {
      type: Number,
      default: 0
    },
    siblingCount: {
      type: Number,
      default: 1
    }
  },
  data() {
    return {
      isExpanded: false,
      children: [],
      loading: false
    }
  },
  computed: {
    nodeClass() {
      return `${this.node.type}-node`
    },
    nodeIcon() {
      const icons = {
        policy: 'fas fa-file-alt',
        subpolicy: 'fas fa-file',
        compliance: 'fas fa-check-circle',
        risk: 'fas fa-exclamation-triangle'
      }
      return icons[this.node.type] || 'fas fa-circle'
    },
    hasChildren() {
      return this.node.type !== 'risk'
    }
  },
  methods: {
    async toggleNode() {
      console.log('🔵 Node clicked:', this.node)
      console.log('🔵 Has children:', this.hasChildren)
      console.log('🔵 Current expanded state:', this.isExpanded)
      
      if (!this.hasChildren) {
        console.log('⚠️ Node has no children (Risk node)')
        return
      }
      
      this.isExpanded = !this.isExpanded
      console.log('🔵 New expanded state:', this.isExpanded)
      
      if (this.isExpanded && this.children.length === 0) {
        console.log('🔵 Loading children...')
        await this.loadChildren()
      } else {
        console.log('🔵 Children already loaded:', this.children.length)
      }
      
      this.$emit('node-click', this.node)
    },
    
    async loadChildren() {
      this.loading = true
      console.log('📡 Loading children for node type:', this.node.type)
      
      try {
        let endpoint = ''
        switch (this.node.type) {
          case 'policy':
            endpoint = API_ENDPOINTS.TREE_GET_SUBPOLICIES(this.node.PolicyId)
            console.log('📡 Policy ID:', this.node.PolicyId)
            break
          case 'subpolicy':
            endpoint = API_ENDPOINTS.TREE_GET_COMPLIANCES(this.node.SubPolicyId)
            console.log('📡 SubPolicy ID:', this.node.SubPolicyId)
            break
          case 'compliance':
            endpoint = API_ENDPOINTS.TREE_GET_RISKS(this.node.ComplianceId)
            console.log('📡 Compliance ID:', this.node.ComplianceId)
            break
        }
        
        console.log('📡 API Endpoint:', endpoint)
        
        if (endpoint) {
          const response = await axios.get(endpoint)
          console.log('✅ API Response:', response.data)
          
          if (response.data.status === 'success') {
            this.children = response.data.data.map(item => {
              let type = ''
              let id = ''
              if (item.SubPolicyId) {
                type = 'subpolicy'
                id = item.SubPolicyId
              } else if (item.ComplianceId) {
                type = 'compliance'
                id = item.ComplianceId
              } else if (item.RiskId) {
                type = 'risk'
                id = item.RiskId
              }
              return { ...item, type, id }
            })
            console.log('✅ Children loaded:', this.children.length, 'items')
            console.log('✅ Children data:', this.children)
          } else {
            console.log('⚠️ API returned non-success status:', response.data)
          }
        } else {
          console.log('⚠️ No endpoint defined for node type:', this.node.type)
        }
      } catch (err) {
        console.error('❌ Error loading children:', err)
        console.error('❌ Error details:', err.response?.data || err.message)
      } finally {
        this.loading = false
        console.log('📡 Loading complete. Children count:', this.children.length)
      }
    },
    
    getNodeTitle() {
      switch (this.node.type) {
        case 'policy':
          return this.node.PolicyName
        case 'subpolicy':
          return this.node.SubPolicyName
        case 'compliance':
          return this.node.ComplianceTitle || 'Compliance'
        case 'risk':
          return this.node.RiskTitle || 'Risk'
        default:
          return 'Unknown'
      }
    }
  },
  mounted() {
    console.log('🟠 TreeNode mounted:', this.node.type, this.getNodeTitle())
  }
}
</script>
