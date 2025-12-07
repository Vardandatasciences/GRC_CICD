# Document Handling Component

A comprehensive document management component for viewing and managing uploaded documents across different modules in the GRC system.

## Features

### 📁 Module-based Organization
- **All Documents**: View documents from all modules
- **Policy**: Policy-related documents and frameworks
- **Audit**: Audit reports and compliance documents
- **Incident**: Incident reports and response plans
- **Risk**: Risk assessments and registers

### 🔍 Search and Filter
- **Search**: Search documents by name, uploader, or description
- **File Type Filter**: Filter by PDF, DOC, XLSX, and other file types
- **Real-time Filtering**: Instant results as you type

### 📊 Document Information
- **Document Name**: Clickable file names that open in new tab
- **Upload Time**: Formatted date and time
- **Uploaded By**: User who uploaded the document
- **Module**: Color-coded module badges
- **File Type Icons**: Visual indicators for different file types

### ⚡ Actions
- **View**: Open document in new tab (S3 URL)
- **Download**: Download document to local machine
- **Details**: View comprehensive document information in modal

### 🎨 User Interface
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Modern UI**: Clean, professional interface with smooth animations
- **Dark Theme Support**: Automatic dark mode detection
- **Accessibility**: Keyboard navigation and screen reader support

## Usage

### Navigation
The Document Handling component can be accessed through the sidebar navigation:
```
Sidebar → Document Handling
```

### Route
```
/document-handling
```

### Component Import
```javascript
import DocumentHandling from '@/components/DocumentHandling/DocumentHandling.vue'
```

## Data Structure

The component uses static data for demonstration. In production, this should be replaced with API calls:

```javascript
{
  id: 1,
  name: 'Document Name.pdf',
  fileType: 'pdf',
  fileSize: '2.5 MB',
  uploadTime: '2024-01-15T10:30:00Z',
  uploadedBy: 'John Smith',
  module: 'policy',
  s3Url: 'https://example-s3-bucket.s3.amazonaws.com/path/to/file.pdf',
  description: 'Document description'
}
```

## File Types Supported

- **PDF**: `fas fa-file-pdf` (Red)
- **DOC/DOCX**: `fas fa-file-word` (Blue)
- **XLS/XLSX**: `fas fa-file-excel` (Green)
- **TXT**: `fas fa-file-alt` (Gray)
- **Images**: `fas fa-file-image` (Purple)
- **Other**: `fas fa-file` (Default)

## Module Badge Colors

- **Policy**: Blue (`#1e40af`)
- **Audit**: Green (`#166534`)
- **Incident**: Orange (`#92400e`)
- **Risk**: Red (`#991b1b`)

## Responsive Breakpoints

- **Desktop**: Full grid layout with all columns
- **Tablet**: Adjusted spacing and smaller tabs
- **Mobile**: Single column layout with stacked information

## Browser Support

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## Dependencies

- Vue 3 (Composition API)
- Font Awesome Icons
- CSS Grid and Flexbox
- Modern JavaScript (ES6+)

## Future Enhancements

- [ ] Real-time document upload
- [ ] Document versioning
- [ ] Bulk download functionality
- [ ] Document sharing
- [ ] Advanced search filters
- [ ] Document preview
- [ ] Integration with cloud storage APIs
