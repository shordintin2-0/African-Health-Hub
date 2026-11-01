/**
 * Delete Confirmation Functionality
 * 
 * This script handles the delete confirmation modals throughout the application.
 * It intercepts delete actions and prompts the user to confirm before proceeding.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if the delete confirmation modal exists
    const deleteConfirmationModal = document.getElementById('deleteConfirmationModal');
    if (!deleteConfirmationModal) return; // Exit if modal doesn't exist
    
    // Create Bootstrap modal instance
    const modalInstance = new bootstrap.Modal(deleteConfirmationModal);
    
    // Find all delete buttons across the application
    const deleteButtons = document.querySelectorAll('[data-delete-url]');
    
    // Attach event listener to each delete button
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            
            // Get data attributes
            const deleteUrl = this.getAttribute('data-delete-url');
            const itemName = this.getAttribute('data-item-name') || 'this item';
            const itemType = this.getAttribute('data-item-type') || 'item';
            
            // Set modal content
            const deleteItemNameEl = deleteConfirmationModal.querySelector('#deleteItemName');
            const deleteForm = deleteConfirmationModal.querySelector('#deleteForm');
            
            if (deleteItemNameEl) deleteItemNameEl.textContent = `${itemType}: ${itemName}`;
            if (deleteForm) deleteForm.action = deleteUrl;
            
            // Show the modal
            modalInstance.show();
        });
    });
    
    // Add event listener for modal shown
    deleteConfirmationModal.addEventListener('shown.bs.modal', function() {
        // Focus on the cancel button to prevent accidental deletion
        const cancelButton = this.querySelector('button.btn-secondary');
        if (cancelButton) cancelButton.focus();
    });
    
    // Log deletion attempt
    const deleteForm = deleteConfirmationModal.querySelector('#deleteForm');
    if (deleteForm) {
        deleteForm.addEventListener('submit', function() {
            console.log('Delete action confirmed');
            // You could add analytics tracking here
        });
    }
}); 