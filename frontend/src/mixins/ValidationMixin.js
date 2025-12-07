export default {
  methods: {
    validateString(value, options = {}) {
      const {
        required = true,
        minLength = 1,
        maxLength = 255,
        fieldName = 'Field'
      } = options;

      if (!value && required) {
        return `${fieldName} is required`;
      }

      if (value) {
        if (value.length < minLength) {
          return `${fieldName} must be at least ${minLength} characters`;
        }
        if (value.length > maxLength) {
          return `${fieldName} cannot exceed ${maxLength} characters`;
        }
      }

      return null;
    },

    validateId(value, fieldName = 'ID') {
      if (!value) {
        return `${fieldName} is required`;
      }
      
      const id = parseInt(value);
      if (isNaN(id) || id < 1) {
        return `${fieldName} must be a valid positive number`;
      }

      return null;
    },

    validateDate(value, fieldName = 'Date') {
      if (!value) {
        return `${fieldName} is required`;
      }

      const date = new Date(value);
      if (isNaN(date.getTime())) {
        return `${fieldName} must be a valid date`;
      }

      // Check if date is not in the past
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      if (date < today) {
        return `${fieldName} cannot be in the past`;
      }

      return null;
    },

    validateAuditType(value) {
      const validTypes = ['I', 'E', 'S'];
      if (!validTypes.includes(value)) {
        return 'Invalid audit type. Must be Internal, External, or Self-Audit';
      }
      return null;
    },

    validateFrequency(value) {
      const validFrequencies = ['0', '1', '60', '120', '182', '365', '365a'];
      if (!validFrequencies.includes(value)) {
        return 'Invalid frequency value';
      }
      return null;
    },

    validateTeamMember(member) {
      const errors = {};

      // Basic info validation
      const auditorError = this.validateId(member.auditor, 'Auditor');
      if (auditorError) errors.auditor = auditorError;

      const roleError = this.validateString(member.role, { 
        fieldName: 'Role',
        minLength: 2,
        maxLength: 100
      });
      if (roleError) errors.role = roleError;

      const responsibilitiesError = this.validateString(member.responsibilities, {
        fieldName: 'Responsibilities',
        minLength: 10,
        maxLength: 500
      });
      if (responsibilitiesError) errors.responsibilities = responsibilitiesError;

      // Policy assignment validation
      const policyError = this.validateId(member.assignedPolicy, 'Policy');
      if (policyError) errors.assignedPolicy = policyError;

      const reviewerError = this.validateId(member.reviewer, 'Reviewer');
      if (reviewerError) errors.reviewer = reviewerError;

      // Audit details validation
      const scopeError = this.validateString(member.scope, {
        fieldName: 'Scope',
        minLength: 10,
        maxLength: 1000
      });
      if (scopeError) errors.scope = scopeError;

      const objectiveError = this.validateString(member.objective, {
        fieldName: 'Objective',
        minLength: 10,
        maxLength: 1000
      });
      if (objectiveError) errors.objective = objectiveError;

      const typeError = this.validateAuditType(member.type);
      if (typeError) errors.type = typeError;

      const frequencyError = this.validateFrequency(member.frequency);
      if (frequencyError) errors.frequency = frequencyError;

      const dueDateError = this.validateDate(member.dueDate, 'Due Date');
      if (dueDateError) errors.dueDate = dueDateError;

      return Object.keys(errors).length > 0 ? errors : null;
    }
  }
}; 