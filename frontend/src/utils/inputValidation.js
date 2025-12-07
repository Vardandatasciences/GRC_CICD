/**
 * Secure Input Validation Utilities
 * Implements allow-list validation pattern for frontend inputs
 */

// Validation patterns (ESLint compliant - no unnecessary escapes or control characters)
const VALIDATION_PATTERNS = {
    // Currency amount pattern (no symbols, just numbers with optional decimals)
    CURRENCY_AMOUNT: /^[0-9]+(\.[0-9]{1,2})?$/,
    
    // Hours pattern (allows decimals up to 2 places)
    HOURS: /^[0-9]+(\.[0-9]{1,2})?$/,
    
    // Safe text pattern (basic printable characters only)
    SAFE_TEXT: /^[a-zA-Z0-9\s\-_.,!?():;@#$%&*+=<>[\]{}|~`"']+$/,
    
    // Basic alphanumeric with spaces and common punctuation
    ALPHANUMERIC_SPACES: /^[a-zA-Z0-9\s\-_.]+$/,
    
    // Email pattern
    EMAIL: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
  };
  
  // Predefined choice lists
  const ALLOWED_CHOICES = {
    IMPACT_SCALES: ['Very Low', 'Low', 'Medium', 'High', 'Very High'],
    YES_NO_MAYBE: ['yes', 'no', 'maybe'],
    YES_NO_PARTIAL: ['yes', 'no', 'partially']
  };
  
  /**
   * Validate currency amount
   * @param {string} value - The value to validate
   * @param {string} fieldName - Field name for error messages
   * @param {boolean} required - Whether field is required
   * @returns {Object} Validation result
   */
  export function validateCurrencyAmount(value, fieldName = 'field', required = false) {
    if (!value || value === '') {
      return required 
        ? { valid: false, error: `${fieldName} is required` }
        : { valid: true, value: null };
    }
  
    const cleanValue = String(value).trim();
    
    if (!VALIDATION_PATTERNS.CURRENCY_AMOUNT.test(cleanValue)) {
      return {
        valid: false,
        error: `${fieldName} must be a valid amount (e.g., 100.50)`
      };
    }
  
    const amount = parseFloat(cleanValue);
    if (amount < 0) {
      return {
        valid: false,
        error: `${fieldName} cannot be negative`
      };
    }
  
    if (amount > 999999999.99) {
      return {
        valid: false,
        error: `${fieldName} exceeds maximum allowed value`
      };
    }
  
    return { valid: true, value: cleanValue };
  }
  
  /**
   * Validate hours input
   * @param {string} value - The value to validate
   * @param {string} fieldName - Field name for error messages
   * @param {boolean} required - Whether field is required
   * @returns {Object} Validation result
   */
  export function validateHours(value, fieldName = 'field', required = false) {
    if (!value || value === '') {
      return required 
        ? { valid: false, error: `${fieldName} is required` }
        : { valid: true, value: null };
    }
  
    const cleanValue = String(value).trim();
    
    if (!VALIDATION_PATTERNS.HOURS.test(cleanValue)) {
      return {
        valid: false,
        error: `${fieldName} must be a valid number of hours (e.g., 8.5)`
      };
    }
  
    const hours = parseFloat(cleanValue);
    if (hours < 0) {
      return {
        valid: false,
        error: `${fieldName} cannot be negative`
      };
    }
  
    if (hours > 8760) {
      return {
        valid: false,
        error: `${fieldName} exceeds reasonable maximum (8760 hours = 1 year)`
      };
    }
  
    return { valid: true, value: cleanValue };
  }
  
  /**
   * Validate text input with length and basic safety checks
   * @param {string} value - The value to validate
   * @param {string} fieldName - Field name for error messages
   * @param {number} maxLength - Maximum allowed length
   * @param {boolean} required - Whether field is required
   * @returns {Object} Validation result
   */
  export function validateSafeText(value, fieldName = 'field', maxLength = 1000, required = false) {
    if (!value || value === '') {
      return required 
        ? { valid: false, error: `${fieldName} is required` }
        : { valid: true, value: null };
    }
  
    const cleanValue = String(value).trim();
    
    if (cleanValue.length > maxLength) {
      return {
        valid: false,
        error: `${fieldName} exceeds maximum length of ${maxLength} characters`
      };
    }
  
    // Check for basic dangerous patterns using simple string methods
    const dangerousStrings = [
      '<script',
      'javascript:',
      'data:',
      'vbscript:',
      'onload=',
      'onerror='
    ];
  
    const lowerValue = cleanValue.toLowerCase();
    for (const dangerous of dangerousStrings) {
      if (lowerValue.includes(dangerous)) {
        return {
          valid: false,
          error: `${fieldName} contains invalid or potentially dangerous characters`
        };
      }
    }
  
    return { valid: true, value: cleanValue };
  }
  
  /**
   * Validate choice from predefined list
   * @param {string} value - The value to validate
   * @param {string} fieldName - Field name for error messages
   * @param {Array} choices - Array of allowed choices
   * @param {boolean} required - Whether field is required
   * @returns {Object} Validation result
   */
  export function validateChoice(value, fieldName = 'field', choices = [], required = false) {
    if (!value || value === '') {
      return required 
        ? { valid: false, error: `${fieldName} is required` }
        : { valid: true, value: null };
    }
  
    if (!choices.includes(value)) {
      return {
        valid: false,
        error: `${fieldName} must be one of: ${choices.join(', ')}`
      };
    }
  
    return { valid: true, value };
  }
  
  /**
   * Validate impact scale selection
   * @param {string} value - The value to validate
   * @param {string} fieldName - Field name for error messages
   * @param {boolean} required - Whether field is required
   * @returns {Object} Validation result
   */
  export function validateImpactScale(value, fieldName = 'field', required = false) {
    return validateChoice(value, fieldName, ALLOWED_CHOICES.IMPACT_SCALES, required);
  }
  
  /**
   * Validate questionnaire data object
   * @param {Object} data - The questionnaire data to validate
   * @returns {Object} Validation result with cleaned data or errors
   */
  export function validateQuestionnaireData(data) {
    const validatedData = {};
    const errors = [];
  
    // Validate cost
    if (data.cost !== undefined && data.cost !== '') {
      const result = validateCurrencyAmount(data.cost, 'Cost');
      if (result.valid) {
        validatedData.cost = result.value;
      } else {
        errors.push(result.error);
      }
    }
  
    // Validate impact
    if (data.impact !== undefined && data.impact !== '') {
      const result = validateImpactScale(data.impact, 'Impact');
      if (result.valid) {
        validatedData.impact = result.value;
      } else {
        errors.push(result.error);
      }
    }
  
    // Validate financial impact
    if (data.financialImpact !== undefined && data.financialImpact !== '') {
      const result = validateImpactScale(data.financialImpact, 'Financial Impact');
      if (result.valid) {
        validatedData.financialImpact = result.value;
      } else {
        errors.push(result.error);
      }
    }
  
    // Validate financial loss
    if (data.financialLoss !== undefined && data.financialLoss !== '') {
      const result = validateCurrencyAmount(data.financialLoss, 'Financial Loss');
      if (result.valid) {
        validatedData.financialLoss = result.value;
      } else {
        errors.push(result.error);
      }
    }
  
    // Validate reputational impact
    if (data.reputationalImpact !== undefined && data.reputationalImpact !== '') {
      const result = validateImpactScale(data.reputationalImpact, 'Reputational Impact');
      if (result.valid) {
        validatedData.reputationalImpact = result.value;
      } else {
        errors.push(result.error);
      }
    }
  
    // Validate operational impact
    if (data.operationalImpact !== undefined && data.operationalImpact !== '') {
      const result = validateImpactScale(data.operationalImpact, 'Operational Impact');
      if (result.valid) {
        validatedData.operationalImpact = result.value;
      } else {
        errors.push(result.error);
      }
    }
  
    // Validate system downtime
    if (data.systemDowntime !== undefined && data.systemDowntime !== '') {
      const result = validateHours(data.systemDowntime, 'System Downtime');
      if (result.valid) {
        validatedData.systemDowntime = result.value;
      } else {
        errors.push(result.error);
      }
    }
  
    // Validate recovery time
    if (data.recoveryTime !== undefined && data.recoveryTime !== '') {
      const result = validateHours(data.recoveryTime, 'Recovery Time');
      if (result.valid) {
        validatedData.recoveryTime = result.value;
      } else {
        errors.push(result.error);
      }
    }
  
    // Validate risk recurrence
    if (data.riskRecurrence !== undefined && data.riskRecurrence !== '') {
      const result = validateChoice(data.riskRecurrence, 'Risk Recurrence', ALLOWED_CHOICES.YES_NO_MAYBE);
      if (result.valid) {
        validatedData.riskRecurrence = result.value;
      } else {
        errors.push(result.error);
      }
    }
  
    // Validate improvement initiative
    if (data.improvementInitiative !== undefined && data.improvementInitiative !== '') {
      const result = validateChoice(data.improvementInitiative, 'Improvement Initiative', ALLOWED_CHOICES.YES_NO_PARTIAL);
      if (result.valid) {
        validatedData.improvementInitiative = result.value;
      } else {
        errors.push(result.error);
      }
    }
  
    return {
      valid: errors.length === 0,
      data: validatedData,
      errors
    };
  }
  
  // Export constants for use in components
  export { VALIDATION_PATTERNS, ALLOWED_CHOICES }; 