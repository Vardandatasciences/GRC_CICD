# Popup Module

A reusable popup module for Vue.js applications that provides a consistent and customizable way to display popups throughout your application.

## Features

- Multiple popup types (success, error, warning, info, confirm, comment)
- Customizable styling and themes
- Responsive design
- Keyboard support (ESC to close)
- Callback support for user actions
- Auto-close functionality
- Comment input support

## Installation

The popup module is already included in your project. To use it in a component:

```javascript
import { PopupService } from '@/modules/popup';
```

## Usage

### Basic Usage

```javascript
// Show a success popup
PopupService.success('Operation completed successfully');

// Show an error popup
PopupService.error('Something went wrong');

// Show a warning popup
PopupService.warning('Please be careful');

// Show a confirmation popup
PopupService.confirm(
  'Are you sure you want to proceed?',
  'Confirm Action',
  () => {
    // Handle confirmation
    console.log('User confirmed');
  },
  () => {
    // Handle cancellation
    console.log('User cancelled');
  }
);

// Show a comment popup
PopupService.comment(
  'Please enter your feedback',
  'Feedback',
  (comment) => {
    // Handle comment submission
    console.log('User comment:', comment);
  }
);
```

### Custom Popup

```javascript
PopupService.show({
  type: 'info',
  heading: 'Custom Popup',
  message: 'This is a custom popup message',
  buttons: [
    { label: 'OK', action: 'ok', class: 'success' },
    { label: 'Cancel', action: 'cancel', class: 'error' }
  ],
  autoClose: 5000 // Auto close after 5 seconds
});
```

## Popup Types

- `success`: Green theme, checkmark icon
- `error`: Red theme, X icon
- `warning`: Yellow theme, warning icon
- `info`: Blue theme, info icon
- `confirm`: Purple theme, question mark icon
- `comment`: Purple theme, comment icon

## Styling

The popup module comes with a default theme that can be customized by modifying the styles in `styles.css`. The module uses CSS variables for easy customization.

## API Reference

### PopupService

#### Methods

- `show(config)`: Show a custom popup
- `hide()`: Hide the current popup
- `success(message, heading)`: Show a success popup
- `error(message, heading)`: Show an error popup
- `warning(message, heading)`: Show a warning popup
- `confirm(message, heading, onConfirm, onCancel)`: Show a confirmation popup
- `comment(message, heading, onSubmit)`: Show a comment popup

### Configuration Options

```javascript
{
  type: 'info',           // Popup type
  heading: '',            // Popup heading
  message: '',            // Popup message
  buttons: [],            // Array of button configurations
  autoClose: 0,           // Auto close timeout in milliseconds
  inputPlaceholder: ''    // Placeholder for comment input
}
```

## Contributing

Feel free to submit issues and enhancement requests. 