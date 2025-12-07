# Form Components Documentation

This document provides comprehensive documentation for all the reusable form components created for the application.

## Table of Contents

1. [Form Container Components](#form-container-components)
2. [Input Components](#input-components)
3. [Usage Examples](#usage-examples)
4. [Component API Reference](#component-api-reference)

## Form Container Components

### FormContainer

The main form wrapper component that provides header, subheader, and action buttons.

```vue
<FormContainer
  header="Form Title"
  subheader="Form description"
  submit-button-text="Submit"
  reset-button-text="Reset"
  :show-actions="true"
  :reset-button="true"
  :submit-button="true"
  @submit="handleSubmit"
  @reset="handleReset"
>
  <!-- Form content goes here -->
</FormContainer>
```

**Props:**
- `header` (String): Main form title
- `subheader` (String): Form description
- `showActions` (Boolean): Show/hide action buttons (default: true)
- `resetButton` (Boolean): Show/hide reset button (default: true)
- `submitButton` (Boolean): Show/hide submit button (default: true)
- `resetButtonText` (String): Reset button text (default: "Reset Form")
- `submitButtonText` (String): Submit button text (default: "Submit")

**Events:**
- `submit`: Emitted when form is submitted
- `reset`: Emitted when form is reset

### FormSection

Groups related form elements with an optional title.

```vue
<FormSection title="Section Title">
  <!-- Form elements -->
</FormSection>
```

**Props:**
- `title` (String): Section title (optional)

### FormRow

Creates a horizontal layout for form elements.

```vue
<FormRow :responsive="true">
  <!-- Form elements will be displayed side by side -->
</FormRow>
```

**Props:**
- `responsive` (Boolean): Enable responsive layout (default: true)

## Input Components

### BaseInput

Base component that provides common functionality for all input types. Not used directly, but extended by other input components.

### TextInput

For text-based inputs: text, email, password, search, tel, url.

```vue
<TextInput
  id="email"
  v-model="email"
  label="Email Address"
  type="email"
  placeholder="Enter your email"
  required
  helper-text="We'll never share your email"
  error-message="Please enter a valid email"
/>
```

**Props:**
- `id` (String, required): Unique identifier
- `modelValue` (String): Input value
- `type` (String): Input type - 'text', 'email', 'password', 'search', 'tel', 'url'
- `label` (String): Field label
- `placeholder` (String): Placeholder text
- `required` (Boolean): Required field
- `disabled` (Boolean): Disable input
- `readonly` (Boolean): Read-only input
- `helperText` (String): Helper text below input
- `errorMessage` (String): Error message
- `maxlength` (Number): Maximum characters
- `minlength` (Number): Minimum characters
- `pattern` (String): Validation pattern
- `autocomplete` (String): Autocomplete attribute
- `autofocus` (Boolean): Auto-focus on load
- `name` (String): Input name

### NumberInput

For numeric inputs with optional min, max, and step controls.

```vue
<NumberInput
  id="age"
  v-model="age"
  label="Age"
  placeholder="Enter your age"
  :min="0"
  :max="120"
  :step="1"
  required
/>
```

**Props:**
- All BaseInput props
- `min` (Number): Minimum value
- `max` (Number): Maximum value
- `step` (Number/String): Step increment

### DateInput

For date and time inputs: date, time, datetime-local, month, week.

```vue
<DateInput
  id="birthDate"
  v-model="birthDate"
  label="Birth Date"
  type="date"
  required
/>
```

**Props:**
- All BaseInput props
- `type` (String): Input type - 'date', 'time', 'datetime-local', 'month', 'week'
- `min` (String): Minimum date
- `max` (String): Maximum date

### TextareaInput

For multi-line text input.

```vue
<TextareaInput
  id="description"
  v-model="description"
  label="Description"
  placeholder="Enter description"
  :rows="4"
  :cols="50"
  required
/>
```

**Props:**
- All BaseInput props
- `rows` (Number): Number of rows (default: 4)
- `cols` (Number): Number of columns

### SelectInput

For single selection from multiple options.

```vue
<SelectInput
  id="country"
  v-model="country"
  label="Country"
  placeholder="Select a country"
  :options="countryOptions"
  required
/>
```

**Props:**
- All BaseInput props
- `options` (Array): Array of option objects with `value` and `label` properties

### CheckboxInput

For multiple selections (checkboxes).

```vue
<CheckboxInput
  id="interests"
  v-model="interests"
  label="Interests"
  :options="interestOptions"
  :single="false"
/>
```

**Props:**
- All BaseInput props
- `options` (Array): Array of option objects
- `single` (Boolean): Single selection mode (default: false)

### RadioInput

For single selection from multiple options (radio buttons).

```vue
<RadioInput
  id="gender"
  v-model="gender"
  label="Gender"
  :options="genderOptions"
/>
```

**Props:**
- All BaseInput props
- `options` (Array): Array of option objects

### FileInput

For file uploads.

```vue
<FileInput
  id="document"
  v-model="document"
  label="Upload Document"
  accept=".pdf,.doc,.docx"
  :multiple="false"
  required
  helper-text="Accepted formats: PDF, DOC, DOCX (Max 10MB)"
/>
```

**Props:**
- All BaseInput props
- `accept` (String): Accepted file types
- `multiple` (Boolean): Allow multiple file selection

## Usage Examples

### Complete Form Example

```vue
<template>
  <FormContainer
    header="User Registration"
    subheader="Please fill in your details"
    submit-button-text="Register"
    @submit="handleSubmit"
    @reset="handleReset"
  >
    <FormSection title="Personal Information">
      <FormRow>
        <TextInput
          id="firstName"
          v-model="form.firstName"
          label="First Name"
          placeholder="Enter first name"
          required
        />
        
        <TextInput
          id="lastName"
          v-model="form.lastName"
          label="Last Name"
          placeholder="Enter last name"
          required
        />
      </FormRow>

      <TextInput
        id="email"
        v-model="form.email"
        label="Email"
        type="email"
        placeholder="Enter email address"
        required
      />

      <DateInput
        id="birthDate"
        v-model="form.birthDate"
        label="Birth Date"
        type="date"
        required
      />
    </FormSection>

    <FormSection title="Preferences">
      <SelectInput
        id="country"
        v-model="form.country"
        label="Country"
        placeholder="Select country"
        :options="countryOptions"
        required
      />

      <CheckboxInput
        id="interests"
        v-model="form.interests"
        label="Interests"
        :options="interestOptions"
      />

      <RadioInput
        id="newsletter"
        v-model="form.newsletter"
        label="Newsletter Subscription"
        :options="newsletterOptions"
      />
    </FormSection>

    <FormSection title="Documents">
      <FileInput
        id="avatar"
        v-model="form.avatar"
        label="Profile Picture"
        accept="image/*"
        helper-text="Upload a profile picture (JPG, PNG)"
      />
    </FormSection>
  </FormContainer>
</template>

<script setup>
import { reactive } from 'vue';
import {
  FormContainer,
  FormSection,
  FormRow,
  TextInput,
  DateInput,
  SelectInput,
  CheckboxInput,
  RadioInput,
  FileInput
} from '../components';

const form = reactive({
  firstName: '',
  lastName: '',
  email: '',
  birthDate: '',
  country: '',
  interests: [],
  newsletter: '',
  avatar: null
});

const countryOptions = [
  { value: 'us', label: 'United States' },
  { value: 'uk', label: 'United Kingdom' },
  { value: 'ca', label: 'Canada' }
];

const interestOptions = [
  { value: 'sports', label: 'Sports' },
  { value: 'music', label: 'Music' },
  { value: 'reading', label: 'Reading' }
];

const newsletterOptions = [
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' }
];

function handleSubmit() {
  console.log('Form submitted:', form);
}

function handleReset() {
  Object.keys(form).forEach(key => {
    if (Array.isArray(form[key])) {
      form[key] = [];
    } else if (typeof form[key] === 'object') {
      form[key] = null;
    } else {
      form[key] = '';
    }
  });
}
</script>
```

## Component API Reference

### Common Props (All Input Components)

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `id` | String | required | Unique identifier |
| `modelValue` | Various | - | Input value |
| `label` | String | '' | Field label |
| `required` | Boolean | false | Required field |
| `disabled` | Boolean | false | Disable input |
| `helperText` | String | '' | Helper text |
| `errorMessage` | String | '' | Error message |
| `name` | String | '' | Input name |

### Importing Components

```javascript
// Import all components
import {
  FormContainer,
  FormSection,
  FormRow,
  TextInput,
  TextareaInput,
  NumberInput,
  DateInput,
  SelectInput,
  CheckboxInput,
  RadioInput,
  FileInput
} from '../components';

// Or import individual components
import { TextInput } from '../components/inputs/TextInput.vue';
```

### Styling

All components use scoped CSS and follow a consistent design system. The styling can be customized by overriding the CSS variables or modifying the component styles.

### Validation

Components support HTML5 validation attributes and custom error messages. You can implement custom validation logic in your form handlers.

### Accessibility

All components are built with accessibility in mind, including:
- Proper ARIA labels
- Keyboard navigation support
- Screen reader compatibility
- Focus management 