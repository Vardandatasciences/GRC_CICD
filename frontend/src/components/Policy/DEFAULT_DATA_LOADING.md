# Default Data Loading from TEMP_MEDIA_ROOT

This document provides information about the integration of the default data loading feature for the `UploadFramework.vue` component, which now loads data from the `TEMP_MEDIA_ROOT` directory.

## Overview

The UploadFramework component now includes a "Load Default PCI DSS 2 Data" option that loads pre-configured data from the `TEMP_MEDIA_ROOT` directory without requiring a file upload. This feature enhances testing and demonstration capabilities.

## Component Changes

The following changes have been made to the `UploadFramework.vue` component:

### Default Data Loading

The `loadDefaultData` function has been updated to call the new `AI_LOAD_DEFAULT_DATA` API endpoint instead of the legacy endpoint. The function:

1. Shows a loading state
2. Calls the backend API to load data from `TEMP_MEDIA_ROOT`
3. Processes the returned sections data
4. Updates the UI with the loaded data
5. Takes the user directly to Step 3 (Content Selection)

```javascript
const loadDefaultData = async () => {
  isLoadingDefault.value = true
  try {
    // Call the backend endpoint for loading default data
    const response = await axios.post(API_ENDPOINTS.AI_LOAD_DEFAULT_DATA)
    // Process the response and update the UI
    // ...
  } catch (error) {
    // Handle errors
  } finally {
    isLoadingDefault.value = false
  }
}
```

### PDF Viewing

The PDF viewing functionality has been updated to handle PDFs from `TEMP_MEDIA_ROOT`:

1. The `getPDFUrl` function now detects if the current task is loading PCI DSS 2 data
2. For PCI DSS 2 data, it uses the `AI_DEFAULT_PDF` endpoint
3. For regular data, it continues to use the existing `CHECKED_SECTIONS_PDF` endpoint

```javascript
const getPDFUrl = (sectionFolder, controlId) => {
  // ...
  if (taskId.value && taskId.value.includes('PCI_DSS_2')) {
    // Use the default data PDF endpoint
    return API_ENDPOINTS.AI_DEFAULT_PDF(sectionFolder, controlId) + `?t=${timestamp}`
  } else {
    // Use the regular checked sections PDF endpoint
    // ...
  }
}
```

### Alternative Paths for PDF Loading

The `tryAlternativePaths` function now provides different fallback paths depending on whether the data is from `TEMP_MEDIA_ROOT` or regular uploaded data:

```javascript
const tryAlternativePaths = async (sectionFolder, controlId) => {
  const isDefaultPciData = taskId.value && taskId.value.includes('PCI_DSS_2')
  let alternativePaths = []
  
  if (isDefaultPciData) {
    // Paths for default PCI DSS 2 data
    // ...
  } else {
    // Paths for regular uploaded data
    // ...
  }
  
  // Try each path...
}
```

### UI Updates

The default data section UI has been updated to clearly indicate it's loading PCI DSS 2 data:

```html
<h3>Load Default PCI DSS 2 Data</h3>
<p>Use pre-loaded PCI DSS 2 framework data from TEMP_MEDIA_ROOT folder for quick testing</p>
<button @click="loadDefaultData" :disabled="isLoadingDefault" class="load-default-btn">
  <i class="fas fa-download"></i>
  {{ isLoadingDefault ? 'Loading PCI DSS 2 Data...' : 'Load PCI DSS 2 Data' }}
</button>
```

## API Integration

The component now uses these API endpoints:

- `AI_LOAD_DEFAULT_DATA` - Loads default data from `TEMP_MEDIA_ROOT`
- `AI_DEFAULT_SECTIONS` - Gets sections data for a specific user
- `AI_DEFAULT_PDF` - Retrieves PDF content for a specific section and control

## Usage

1. Navigate to the Upload Framework screen
2. Click the "Load PCI DSS 2 Data" button in the lower section of Step 1
3. The application will load the data and take you to Step 3
4. Select sections and view PDFs as with regular uploaded data
5. Proceed through the remaining steps as usual

## Error Handling

The component includes error handling for:

- Failed API calls
- Missing or inaccessible PDF files
- Invalid data structures

Error messages are displayed to the user and logged to the console for debugging.

