/**
 * Form Validation and Enhancement Script
 *
 * Provides client-side validation and UX improvements for generated forms.
 */

(function() {
    'use strict';

    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        initializeFormValidation();
        initializeRangeInputs();
        initializeFileInputs();
    });

    /**
     * Initialize form validation
     */
    function initializeFormValidation() {
        const form = document.getElementById('generated-form');
        if (!form) return;

        // Add novalidate to handle custom validation
        form.setAttribute('novalidate', true);

        form.addEventListener('submit', function(e) {
            let isValid = true;
            const fields = form.querySelectorAll('.form-control, input[type="checkbox"], input[type="radio"]');

            fields.forEach(function(field) {
                const formGroup = field.closest('.form-group');
                if (!formGroup) return;

                // Remove previous error state
                formGroup.classList.remove('has-error', 'has-success');
                const existingError = formGroup.querySelector('.error-message');
                if (existingError) existingError.remove();

                // Validate field
                const error = validateField(field);
                if (error) {
                    isValid = false;
                    formGroup.classList.add('has-error');

                    const errorEl = document.createElement('p');
                    errorEl.className = 'error-message';
                    errorEl.textContent = error;
                    formGroup.appendChild(errorEl);
                } else {
                    formGroup.classList.add('has-success');
                }
            });

            if (!isValid) {
                e.preventDefault();

                // Scroll to first error
                const firstError = form.querySelector('.has-error');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        });

        // Real-time validation on blur
        form.addEventListener('blur', function(e) {
            if (e.target.classList.contains('form-control')) {
                const formGroup = e.target.closest('.form-group');
                if (!formGroup) return;

                formGroup.classList.remove('has-error', 'has-success');
                const existingError = formGroup.querySelector('.error-message');
                if (existingError) existingError.remove();

                const error = validateField(e.target);
                if (error) {
                    formGroup.classList.add('has-error');

                    const errorEl = document.createElement('p');
                    errorEl.className = 'error-message';
                    errorEl.textContent = error;
                    formGroup.appendChild(errorEl);
                } else if (e.target.value) {
                    formGroup.classList.add('has-success');
                }
            }
        }, true);
    }

    /**
     * Validate a single field
     */
    function validateField(field) {
        const value = field.value.trim();
        const type = field.type || field.tagName.toLowerCase();

        // Required validation
        if (field.required && !value) {
            const label = getLabelText(field);
            return `${label} is required`;
        }

        // Skip further validation if empty and not required
        if (!value) return null;

        // Type-specific validation
        switch (type) {
            case 'email':
                if (!isValidEmail(value)) {
                    return 'Please enter a valid email address';
                }
                break;

            case 'tel':
                if (!isValidPhone(value)) {
                    return 'Please enter a valid phone number';
                }
                break;

            case 'url':
                if (!isValidURL(value)) {
                    return 'Please enter a valid URL';
                }
                break;

            case 'number':
                if (isNaN(value)) {
                    return 'Please enter a valid number';
                }
                if (field.min && parseFloat(value) < parseFloat(field.min)) {
                    return `Value must be at least ${field.min}`;
                }
                if (field.max && parseFloat(value) > parseFloat(field.max)) {
                    return `Value must be at most ${field.max}`;
                }
                break;

            case 'date':
                if (!isValidDate(value)) {
                    return 'Please enter a valid date';
                }
                break;
        }

        // Pattern validation
        if (field.pattern) {
            const regex = new RegExp(field.pattern);
            if (!regex.test(value)) {
                return field.title || 'Please match the required format';
            }
        }

        // Min/Max length
        if (field.minLength && value.length < field.minLength) {
            return `Must be at least ${field.minLength} characters`;
        }
        if (field.maxLength && value.length > field.maxLength) {
            return `Must be at most ${field.maxLength} characters`;
        }

        return null;
    }

    /**
     * Get label text for a field
     */
    function getLabelText(field) {
        const formGroup = field.closest('.form-group');
        if (formGroup) {
            const label = formGroup.querySelector('label');
            if (label) {
                return label.textContent.replace('*', '').trim();
            }
        }
        return field.name || 'This field';
    }

    /**
     * Validation helpers
     */
    function isValidEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    function isValidPhone(phone) {
        const re = /^[\d\s\-\+\(\)]+$/;
        return re.test(phone) && phone.replace(/\D/g, '').length >= 10;
    }

    function isValidURL(url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    }

    function isValidDate(date) {
        return !isNaN(Date.parse(date));
    }

    /**
     * Initialize range inputs with value display
     */
    function initializeRangeInputs() {
        const rangeInputs = document.querySelectorAll('input[type="range"]');

        rangeInputs.forEach(function(input) {
            // Create value display
            const valueDisplay = document.createElement('div');
            valueDisplay.className = 'range-value';
            valueDisplay.textContent = input.value;
            input.parentNode.insertBefore(valueDisplay, input.nextSibling);

            // Update on input
            input.addEventListener('input', function() {
                valueDisplay.textContent = this.value;
            });
        });
    }

    /**
     * Initialize file inputs with drag and drop
     */
    function initializeFileInputs() {
        const fileInputs = document.querySelectorAll('input[type="file"]');

        fileInputs.forEach(function(input) {
            const formGroup = input.closest('.form-group');
            if (!formGroup) return;

            // Add drag and drop support
            formGroup.addEventListener('dragover', function(e) {
                e.preventDefault();
                this.style.borderColor = '#4a90d9';
            });

            formGroup.addEventListener('dragleave', function(e) {
                e.preventDefault();
                this.style.borderColor = '';
            });

            formGroup.addEventListener('drop', function(e) {
                e.preventDefault();
                this.style.borderColor = '';

                if (e.dataTransfer.files.length) {
                    input.files = e.dataTransfer.files;

                    // Trigger change event
                    const event = new Event('change', { bubbles: true });
                    input.dispatchEvent(event);
                }
            });

            // Show selected file name
            input.addEventListener('change', function() {
                const fileNames = Array.from(this.files).map(f => f.name).join(', ');

                let fileDisplay = formGroup.querySelector('.file-display');
                if (!fileDisplay) {
                    fileDisplay = document.createElement('p');
                    fileDisplay.className = 'file-display field-description';
                    formGroup.appendChild(fileDisplay);
                }

                fileDisplay.textContent = fileNames || 'No file selected';
            });
        });
    }

})();
