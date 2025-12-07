# Data Services - Centralized Data Management

This directory contains centralized data management services for the GRC application. These services follow the singleton pattern to provide efficient data caching and reduce redundant API calls.

## Overview

The services are designed to:
1. **Fetch data on login** - Load all necessary data once during authentication
2. **Cache in memory** - Store data for instant access throughout the session
3. **Provide instant access** - Components can retrieve cached data without waiting for API calls
4. **Reduce API load** - Minimize redundant requests to the backend

## Available Services

### 1. Risk Service (`riskService.js`)

Manages risk-related data including risks and risk instances.

```javascript
import riskDataService from '@/services/riskService';

// Fetch all risk data (usually called on login)
await riskDataService.fetchAllRiskData();

// Get cached risks
const risks = riskDataService.getData('risks');

// Get cached risk instances
const riskInstances = riskDataService.getData('riskInstances');

// Check if cache is valid
if (!riskDataService.hasValidCache()) {
  await riskDataService.fetchAllRiskData();
}

// Get cache statistics
const stats = riskDataService.getCacheStats();
console.log(`Cached ${stats.risksCount} risks and ${stats.riskInstancesCount} risk instances`);
```

### 2. Integrations Service (`integrationsService.js`)

Manages external integration data including Jira, BambooHR, Gmail, and Microsoft Sentinel.

```javascript
import integrationsDataService from '@/services/integrationsService';

// Fetch all integration data
await integrationsDataService.fetchAllIntegrationData();

// Get all applications
const applications = integrationsDataService.getData('applications');

// Get specific integration data
const jiraData = integrationsDataService.getData('jiraStoredData');
const bamboohrData = integrationsDataService.getData('bamboohrStoredData');

// Update an application's status
integrationsDataService.updateApplication(applicationId, {
  status: 'connected',
  lastSync: new Date().toISOString()
});

// Get cache statistics
const stats = integrationsDataService.getCacheStats();
console.log(`${stats.connectedApplications} applications connected`);
```

### 3. Document Service (`documentService.js`)

Manages document handling data including documents and document counts by module.

```javascript
import documentDataService from '@/services/documentService';

// Fetch all document data
await documentDataService.fetchAllDocumentData();

// Get all documents
const documents = documentDataService.getData('documents');

// Get document counts
const counts = documentDataService.getData('documentCounts');
console.log(`Total documents: ${counts.all}`);

// Filter documents by module
const policyDocs = documentDataService.getDocumentsByModule('policy');

// Search documents
const results = documentDataService.searchDocuments('compliance');

// Upload a document (automatically refreshes cache)
const formData = new FormData();
formData.append('file', file);
formData.append('module', 'policy');
await documentDataService.uploadDocument(formData, (progress) => {
  console.log(`Upload progress: ${progress}%`);
});
```

### 4. Tree Service (`treeService.js`)

Manages hierarchical tree data including frameworks, policies, subpolicies, compliances, and risks.

```javascript
import treeDataService from '@/services/treeService';

// Fetch all tree data (frameworks + selected framework's policies)
await treeDataService.fetchAllTreeData();

// Get all frameworks
const frameworks = treeDataService.getData('frameworks');

// Get policies for a framework
const policies = treeDataService.getPolicies(frameworkId);
// Or fetch if not cached
await treeDataService.fetchPolicies(frameworkId);

// Get subpolicies for a policy
const subpolicies = await treeDataService.fetchSubpolicies(policyId);

// Get compliances for a subpolicy
const compliances = await treeDataService.fetchCompliances(subpolicyId);

// Get risks for a compliance
const risks = await treeDataService.fetchRisks(complianceId);

// Clear cache for a specific framework
treeDataService.clearFrameworkCache(frameworkId);

// Get cache statistics
const stats = treeDataService.getCacheStats();
console.log(`Cached data for ${stats.policiesCached} frameworks`);
```

## Common Methods

All services implement these common methods:

### `fetchAll[Module]Data()`
Fetches all data for the module and caches it. Should be called once on login.

```javascript
await service.fetchAllModuleData();
```

### `getData(key)`
Retrieves cached data by key.

```javascript
const data = service.getData('risks');
```

### `setData(key, value)`
Updates cached data by key.

```javascript
service.setData('risks', updatedRisks);
```

### `hasValidCache()`
Checks if the cache is valid and has data.

```javascript
if (!service.hasValidCache()) {
  await service.fetchAllModuleData();
}
```

### `clearCache()`
Clears all cached data.

```javascript
service.clearCache();
```

### `getCacheStats()`
Returns statistics about the cached data.

```javascript
const stats = service.getCacheStats();
console.log(stats);
```

## Integration with Login Flow

To integrate these services with your login flow, call the fetch methods after successful authentication:

```javascript
// In your login component or authentication service
async function onLoginSuccess() {
  console.log('🚀 Starting data prefetch...');
  
  try {
    await Promise.all([
      riskDataService.fetchAllRiskData(),
      integrationsDataService.fetchAllIntegrationData(),
      documentDataService.fetchAllDocumentData(),
      treeDataService.fetchAllTreeData()
    ]);
    
    console.log('✅ All data prefetched successfully');
  } catch (error) {
    console.error('❌ Error prefetching data:', error);
    // Handle error appropriately
  }
}
```

## Usage in Components

### Vue 3 Composition API

```javascript
import { ref, onMounted } from 'vue';
import riskDataService from '@/services/riskService';

export default {
  setup() {
    const risks = ref([]);
    const loading = ref(false);
    
    onMounted(async () => {
      // Try to use cached data first
      if (riskDataService.hasValidCache()) {
        risks.value = riskDataService.getData('risks');
        console.log('✅ Using cached risk data');
      } else {
        // Fetch if not cached
        loading.value = true;
        try {
          await riskDataService.fetchAllRiskData();
          risks.value = riskDataService.getData('risks');
          console.log('✅ Fetched and cached risk data');
        } catch (error) {
          console.error('❌ Error fetching risks:', error);
        } finally {
          loading.value = false;
        }
      }
    });
    
    return { risks, loading };
  }
};
```

### Vue 2 Options API

```javascript
import riskDataService from '@/services/riskService';

export default {
  data() {
    return {
      risks: [],
      loading: false
    };
  },
  
  async mounted() {
    // Try to use cached data first
    if (riskDataService.hasValidCache()) {
      this.risks = riskDataService.getData('risks');
      console.log('✅ Using cached risk data');
    } else {
      // Fetch if not cached
      this.loading = true;
      try {
        await riskDataService.fetchAllRiskData();
        this.risks = riskDataService.getData('risks');
        console.log('✅ Fetched and cached risk data');
      } catch (error) {
        console.error('❌ Error fetching risks:', error);
      } finally {
        this.loading = false;
      }
    }
  }
};
```

## Benefits

1. **Improved Performance**: Data is loaded once and cached, eliminating redundant API calls
2. **Faster Load Times**: Components can access cached data instantly
3. **Reduced Server Load**: Fewer API requests mean less load on the backend
4. **Better UX**: Users experience faster page loads and smoother transitions
5. **Centralized Logic**: All data fetching logic is in one place, easier to maintain
6. **Consistent State**: All components share the same cached data

## Best Practices

1. **Call fetch methods on login**: Initialize all services after successful authentication
2. **Check cache validity**: Always check `hasValidCache()` before fetching
3. **Handle errors gracefully**: Wrap fetch calls in try-catch blocks
4. **Clear cache on logout**: Call `clearCache()` on all services during logout
5. **Update cache after mutations**: When creating/updating/deleting data, update the cache accordingly
6. **Monitor cache statistics**: Use `getCacheStats()` for debugging and monitoring

## Cache Management

### When to Fetch
- On initial login
- After logout and re-login
- When cache is invalid or empty
- When explicitly refreshing data

### When to Clear Cache
- On logout
- When switching users
- When receiving authentication errors
- When data becomes stale (optional: implement TTL)

### When to Update Cache
- After creating new records
- After updating existing records
- After deleting records
- After bulk operations

## Example: Complete Integration

```javascript
// auth.js - Authentication service
import riskDataService from '@/services/riskService';
import integrationsDataService from '@/services/integrationsService';
import documentDataService from '@/services/documentService';
import treeDataService from '@/services/treeService';

export async function login(credentials) {
  // Perform login
  const response = await api.login(credentials);
  
  if (response.success) {
    // Store tokens
    localStorage.setItem('jwt_token', response.token);
    
    // Prefetch all data in parallel
    console.log('🚀 Starting data prefetch...');
    const startTime = Date.now();
    
    try {
      await Promise.all([
        riskDataService.fetchAllRiskData(),
        integrationsDataService.fetchAllIntegrationData(),
        documentDataService.fetchAllDocumentData(),
        treeDataService.fetchAllTreeData()
      ]);
      
      const duration = Date.now() - startTime;
      console.log(`✅ All data prefetched in ${duration}ms`);
      
      // Log cache statistics
      console.log('📊 Cache Statistics:');
      console.log('  Risk:', riskDataService.getCacheStats());
      console.log('  Integrations:', integrationsDataService.getCacheStats());
      console.log('  Documents:', documentDataService.getCacheStats());
      console.log('  Tree:', treeDataService.getCacheStats());
      
    } catch (error) {
      console.error('❌ Error during data prefetch:', error);
      // Don't fail login if prefetch fails
    }
  }
  
  return response;
}

export function logout() {
  // Clear all caches
  riskDataService.clearCache();
  integrationsDataService.clearCache();
  documentDataService.clearCache();
  treeDataService.clearCache();
  
  // Clear tokens
  localStorage.removeItem('jwt_token');
  
  console.log('🧹 All caches cleared on logout');
}
```

## Troubleshooting

### Data Not Loading
1. Check if the service is properly imported
2. Verify the fetch method was called on login
3. Check browser console for error messages
4. Verify API endpoints are correct

### Stale Data
1. Clear cache and refresh: `service.clearCache()` then `service.fetchAllModuleData()`
2. Check if cache is being updated after mutations
3. Consider implementing cache expiration (TTL)

### Memory Issues
1. Monitor cache size with `getCacheStats()`
2. Clear cache when switching users
3. Implement selective caching for large datasets

## Future Enhancements

- **Cache Expiration (TTL)**: Automatically invalidate cache after a certain time
- **Partial Updates**: Update specific items in cache without full refetch
- **IndexedDB Storage**: Persist cache across browser sessions
- **Real-time Updates**: WebSocket integration for live data updates
- **Cache Versioning**: Track data versions to detect stale cache
- **Compression**: Compress large datasets in memory

