// Calendar functionality for Employee Leave Management System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize calendar if calendar element exists
    const calendarEl = document.getElementById('calendar');
    if (calendarEl) {
        initializeCalendar();
    }
    
    // Initialize date pickers
    initializeDatePickers();
    
    // Initialize form validations
    initializeFormValidations();
});

function initializeCalendar() {
    const calendarEl = document.getElementById('calendar');
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,listWeek'
        },
        events: function(fetchInfo, successCallback, failureCallback) {
            // Get events from API endpoint
            const apiUrl = calendarEl.dataset.eventsUrl || '/employee/api/calendar_events';
            
            fetch(apiUrl)
                .then(response => response.json())
                .then(data => {
                    successCallback(data);
                })
                .catch(error => {
                    console.error('Error fetching calendar events:', error);
                    failureCallback(error);
                });
        },
        eventDisplay: 'block',
        dayMaxEvents: 3,
        eventClick: function(info) {
            // Show event details in modal or tooltip
            showEventDetails(info.event);
        },
        dateClick: function(info) {
            // Handle date click for adding new events
            handleDateClick(info.date);
        }
    });
    
    calendar.render();
}

function showEventDetails(event) {
    // Create a simple modal or alert with event details
    const details = `
        Event: ${event.title}
        Start: ${event.start.toLocaleDateString()}
        End: ${event.end ? event.end.toLocaleDateString() : 'Same day'}
    `;
    
    alert(details); // In a real app, you'd use a proper modal
}

function handleDateClick(date) {
    // Handle clicking on a date (could open leave application form)
    console.log('Date clicked:', date);
}

function initializeDatePickers() {
    // Set minimum date for leave applications to today
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');
    
    if (startDateInput) {
        const today = new Date().toISOString().split('T')[0];
        startDateInput.min = today;
        
        // Update end date minimum when start date changes
        startDateInput.addEventListener('change', function() {
            if (endDateInput) {
                endDateInput.min = this.value;
                if (endDateInput.value && endDateInput.value < this.value) {
                    endDateInput.value = this.value;
                }
            }
            calculateLeaveDays();
        });
    }
    
    if (endDateInput) {
        endDateInput.addEventListener('change', calculateLeaveDays);
    }
}

function calculateLeaveDays() {
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');
    const daysDisplay = document.getElementById('days-display');
    
    if (startDateInput && endDateInput && startDateInput.value && endDateInput.value) {
        const startDate = new Date(startDateInput.value);
        const endDate = new Date(endDateInput.value);
        
        if (endDate >= startDate) {
            const timeDiff = endDate.getTime() - startDate.getTime();
            const daysDiff = Math.ceil(timeDiff / (1000 * 3600 * 24)) + 1;
            
            if (daysDisplay) {
                daysDisplay.textContent = `${daysDiff} day${daysDiff !== 1 ? 's' : ''}`;
                daysDisplay.className = 'badge bg-info';
            }
        }
    }
}

function initializeFormValidations() {
    // Add custom form validations
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        });
    });
    
    // Real-time validation for leave dates
    const leaveForm = document.getElementById('leave-form');
    if (leaveForm) {
        validateLeaveForm();
    }
}

function validateLeaveForm() {
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');
    const reasonInput = document.getElementById('reason');
    
    if (startDateInput && endDateInput) {
        [startDateInput, endDateInput].forEach(input => {
            input.addEventListener('change', function() {
                validateDateRange();
            });
        });
    }
    
    if (reasonInput) {
        reasonInput.addEventListener('input', function() {
            validateReason();
        });
    }
}

function validateDateRange() {
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');
    
    if (startDateInput.value && endDateInput.value) {
        const startDate = new Date(startDateInput.value);
        const endDate = new Date(endDateInput.value);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        // Check if start date is in the past
        if (startDate < today) {
            showFieldError(startDateInput, 'Start date cannot be in the past');
            return false;
        }
        
        // Check if end date is before start date
        if (endDate < startDate) {
            showFieldError(endDateInput, 'End date must be after start date');
            return false;
        }
        
        // Clear any previous errors
        clearFieldError(startDateInput);
        clearFieldError(endDateInput);
        return true;
    }
}

function validateReason() {
    const reasonInput = document.getElementById('reason');
    const minLength = 10;
    
    if (reasonInput.value.length < minLength) {
        showFieldError(reasonInput, `Reason must be at least ${minLength} characters long`);
        return false;
    }
    
    clearFieldError(reasonInput);
    return true;
}

function showFieldError(field, message) {
    field.classList.add('is-invalid');
    
    let feedback = field.parentNode.querySelector('.invalid-feedback');
    if (!feedback) {
        feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        field.parentNode.appendChild(feedback);
    }
    
    feedback.textContent = message;
}

function clearFieldError(field) {
    field.classList.remove('is-invalid');
    
    const feedback = field.parentNode.querySelector('.invalid-feedback');
    if (feedback) {
        feedback.remove();
    }
}

// Utility functions
function showToast(message, type = 'info') {
    // Create a simple toast notification
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(toast);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 5000);
}

function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Export functions for use in other scripts
window.ELMS = {
    showToast,
    confirmAction,
    calculateLeaveDays,
    validateDateRange,
    validateReason
};