// African Health Hub - Main JavaScript File

// Initialize DataTables
document.addEventListener('DOMContentLoaded', function() {
    // Initialize any DataTables on the page
    if (typeof $.fn.DataTable !== 'undefined') {
        $('.datatable').DataTable({
            responsive: true,
            language: {
                search: "Search: ",
                lengthMenu: "Show _MENU_ entries per page",
                info: "Showing _START_ to _END_ of _TOTAL_ entries",
                paginate: {
                    first: "First",
                    last: "Last",
                    next: "Next",
                    previous: "Previous"
                }
            }
        });
    }

    // Initialize date pickers
    if (typeof flatpickr !== 'undefined') {
        flatpickr('.datepicker', {
            enableTime: false,
            dateFormat: "Y-m-d"
        });
        
        flatpickr('.datetimepicker', {
            enableTime: true,
            dateFormat: "Y-m-d H:i",
            time_24hr: true
        });
    }
    
    // Initialize tooltips
    if (typeof bootstrap !== 'undefined' && typeof bootstrap.Tooltip !== 'undefined') {
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    }
});

// Form validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;
    
    let isValid = true;
    const requiredInputs = form.querySelectorAll('[required]');
    
    requiredInputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// Appointment scheduling validation
function validateAppointmentForm() {
    const form = document.getElementById('appointmentForm');
    if (!form) return true;
    
    // Get form fields
    const staffId = form.querySelector('[name="staff_id"]').value;
    const appointmentDate = form.querySelector('[name="appointment_date"]').value;
    const appointmentType = form.querySelector('[name="appointment_type"]').value;
    
    // Validate fields
    let isValid = true;
    if (!staffId) {
        document.getElementById('staffError').textContent = 'Please select a doctor';
        isValid = false;
    }
    
    if (!appointmentDate) {
        document.getElementById('dateError').textContent = 'Please select a date and time';
        isValid = false;
    }
    
    if (!appointmentType) {
        document.getElementById('typeError').textContent = 'Please select an appointment type';
        isValid = false;
    }
    
    return isValid;
}

// Medical record validation
function validateMedicalRecordForm() {
    const form = document.getElementById('medicalRecordForm');
    if (!form) return true;
    
    // Get form fields
    const patientId = form.querySelector('[name="patient_id"]').value;
    const diagnosis = form.querySelector('[name="diagnosis"]').value;
    const treatment = form.querySelector('[name="treatment"]').value;
    
    // Validate fields
    let isValid = true;
    if (!patientId) {
        document.getElementById('patientError').textContent = 'Please select a patient';
        isValid = false;
    }
    
    if (!diagnosis) {
        document.getElementById('diagnosisError').textContent = 'Diagnosis is required';
        isValid = false;
    }
    
    if (!treatment) {
        document.getElementById('treatmentError').textContent = 'Treatment is required';
        isValid = false;
    }
    
    return isValid;
}

// Confirm delete
function confirmDelete(message) {
    return confirm(message || 'Are you sure you want to delete this item?');
}

// Toggle password visibility
function togglePasswordVisibility(inputId, iconId) {
    const passwordInput = document.getElementById(inputId);
    const icon = document.getElementById(iconId);
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        passwordInput.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

// Format date for display
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

// Format datetime for display
function formatDateTime(dateTimeString) {
    const options = { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    return new Date(dateTimeString).toLocaleDateString(undefined, options);
} 