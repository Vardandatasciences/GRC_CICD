# ISO 27001 Migration Platform - Vue.js Components

This repository contains Vue.js components that replicate the functionality of the React-based ISO 27001 Migration Platform. The components provide a comprehensive framework for comparing ISO 27001:2013 and 2022 standards, managing migration processes, and tracking compliance gaps.

## Components Overview

### 1. FrameworkMigration.vue
The main dashboard component that provides:
- Overview of migration progress
- Quick access to comparison and migration tools
- Recent activity feed
- Progress tracking with visual indicators

### 2. FrameworkComparison.vue
A comprehensive side-by-side comparison tool featuring:
- Expandable policy trees for both 2013 and 2022 frameworks
- Visual change indicators (new, modified, removed, unchanged)
- Search and filtering capabilities
- Compliance status badges
- Export functionality

### 3. Migration.vue
A step-by-step migration process component with:
- 4-step migration workflow
- Gap assessment tools
- Action planning interface
- Progress tracking
- Status management

### 4. Supporting Components
- **StatusBadge.vue**: Displays compliance status with color-coded badges
- **ChangeBadge.vue**: Shows change types (new, modified, removed, unchanged)
- **iso27001Data.js**: Contains the framework data structure

## Setup Instructions

### Prerequisites
- Node.js (v16 or higher)
- Vue.js 3
- Vue Router
- Tailwind CSS
- Lucide Vue Next (for icons)

### Installation

1. **Install dependencies:**
```bash
npm install vue@next vue-router@4 lucide-vue-next
npm install -D tailwindcss postcss autoprefixer
```

2. **Initialize Tailwind CSS:**
```bash
npx tailwindcss init -p
```

3. **Configure Tailwind CSS** (tailwind.config.js):
```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: "hsl(var(--card))",
        "card-foreground": "hsl(var(--card-foreground))",
        primary: "hsl(var(--primary))",
        "primary-foreground": "hsl(var(--primary-foreground))",
        secondary: "hsl(var(--secondary))",
        "secondary-foreground": "hsl(var(--secondary-foreground))",
        muted: "hsl(var(--muted))",
        "muted-foreground": "hsl(var(--muted-foreground))",
        accent: "hsl(var(--accent))",
        "accent-foreground": "hsl(var(--accent-foreground))",
        destructive: "hsl(var(--destructive))",
        "destructive-foreground": "hsl(var(--destructive-foreground))",
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        // Status colors
        "status-compliant": "hsl(var(--status-compliant))",
        "status-compliant-bg": "hsl(var(--status-compliant-bg))",
        "status-non-compliant": "hsl(var(--status-non-compliant))",
        "status-non-compliant-bg": "hsl(var(--status-non-compliant-bg))",
        "status-partial": "hsl(var(--status-partial))",
        "status-partial-bg": "hsl(var(--status-partial-bg))",
        "status-gap": "hsl(var(--status-gap))",
        "status-gap-bg": "hsl(var(--status-gap-bg))",
        "status-audit": "hsl(var(--status-audit))",
        "status-audit-bg": "hsl(var(--status-audit-bg))",
        // Change colors
        "change-new": "hsl(var(--change-new))",
        "change-new-bg": "hsl(var(--change-new-bg))",
        "change-modified": "hsl(var(--change-modified))",
        "change-modified-bg": "hsl(var(--change-modified-bg))",
        "change-removed": "hsl(var(--change-removed))",
        "change-removed-bg": "hsl(var(--change-removed-bg))",
        "change-unchanged": "hsl(var(--change-unchanged))",
        "change-unchanged-bg": "hsl(var(--change-unchanged-bg))",
      },
    },
  },
  plugins: [],
}
```

4. **Include the design system CSS** in your main CSS file:
```css
@import './design-system.css';
@tailwind base;
@tailwind components;
@tailwind utilities;
```

5. **Set up Vue Router** (router/index.js):
```javascript
import { createRouter, createWebHistory } from 'vue-router'
import FrameworkMigration from '../components/FrameworkMigration.vue'
import FrameworkComparison from '../components/FrameworkComparison.vue'
import Migration from '../components/Migration.vue'

const routes = [
  {
    path: '/',
    redirect: '/framework-migration'
  },
  {
    path: '/framework-migration',
    name: 'FrameworkMigration',
    component: FrameworkMigration
  },
  {
    path: '/framework-migration/comparison',
    name: 'FrameworkComparison',
    component: FrameworkComparison
  },
  {
    path: '/framework-migration/migration',
    name: 'Migration',
    component: Migration
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
```

6. **Update your main.js:**
```javascript
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './index.css'

const app = createApp(App)
app.use(router)
app.mount('#app')
```

## Usage

### Basic Component Usage

```vue
<template>
  <div>
    <FrameworkMigration />
  </div>
</template>

<script>
import FrameworkMigration from './components/FrameworkMigration.vue'

export default {
  name: 'App',
  components: {
    FrameworkMigration
  }
}
</script>
```

### Navigation Between Components

The components are designed to work together with Vue Router. Users can navigate between:

- **Framework Migration Dashboard** (`/framework-migration`)
- **Framework Comparison** (`/framework-migration/comparison`)
- **Migration Process** (`/framework-migration/migration`)

### Customization

#### Styling
The components use a comprehensive design system with CSS custom properties. You can customize colors by modifying the variables in `design-system.css`.

#### Data
The framework data is stored in `iso27001Data.js`. You can extend this data structure to include additional frameworks or modify existing compliance requirements.

#### Functionality
Each component is self-contained and can be extended with additional features such as:
- API integration for real-time data
- Export functionality (PDF, Excel)
- User authentication and role-based access
- Audit logging
- Real-time collaboration features

## Features

### Framework Migration Dashboard
- **Progress Tracking**: Visual progress indicators for migration completion
- **Quick Actions**: Direct access to comparison and migration tools
- **Activity Feed**: Recent actions and updates
- **Statistics**: Overview of new controls, modifications, and removals

### Framework Comparison
- **Side-by-Side View**: Compare 2013 and 2022 frameworks simultaneously
- **Expandable Trees**: Navigate through policies, sub-policies, and controls
- **Change Indicators**: Visual badges showing what changed between versions
- **Search & Filter**: Find specific controls or filter by change type
- **Compliance Status**: Track current compliance status for each control

### Migration Process
- **Step-by-Step Workflow**: Guided migration process
- **Gap Assessment**: Identify current compliance gaps
- **Action Planning**: Create and track remediation actions
- **Status Management**: Update compliance status throughout the process

## Browser Support

The components are built with modern Vue.js 3 features and require:
- Chrome 88+
- Firefox 85+
- Safari 14+
- Edge 88+

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions or support, please open an issue in the repository or contact the development team.
