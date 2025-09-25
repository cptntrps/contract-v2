/**
 * Contract Analyzer Dashboard - Main Entry Point
 * 
 * This file serves as the main entry point for the modular dashboard application.
 * It loads all required modules and initializes the application.
 * 
 * The application is now structured with the following modules:
 * - Core: Application initialization and coordination
 * - Utils: Shared utility functions
 * - Notifications: User feedback system
 * - Navigation: Tab switching and sidebar management
 * - Dashboard: Main dashboard functionality
 * - Upload: File upload and management
 * - Settings: System configuration
 * - Prompts: LLM prompt management
 */

// Ensure we don't initialize multiple times
if (window.dashboardInitialized) {
    console.log('Dashboard: Already initialized, skipping...');
} else {
    console.log('Dashboard: Starting modular initialization...');
    
    // Set initialization flag
    window.dashboardInitialized = true;
    
    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        console.log('Dashboard: DOM ready, modules should initialize automatically via core.js');
        
        // Core module will handle initialization of all other modules
        // No additional initialization needed here as core.js handles everything
        
        console.log('Dashboard: Modular dashboard initialization process started');
    });
}

// Export some global functions for backwards compatibility with existing HTML onclick handlers
window.openUploadModal = function() {
    const uploadModule = window.ContractApp?.modules?.upload;
    if (uploadModule) {
        uploadModule.openUploadModal();
    } else {
        console.warn('Upload module not available');
    }
};

window.closeUploadModal = function() {
    const uploadModule = window.ContractApp?.modules?.upload;
    if (uploadModule) {
        uploadModule.closeUploadModal();
    }
};

window.toggleSidebar = function() {
    const navigationModule = window.ContractApp?.modules?.navigation;
    if (navigationModule) {
        navigationModule.toggleSidebar();
    } else {
        // Fallback for immediate use
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            sidebar.classList.toggle('active');
        }
    }
};

// Expose refresh function globally
window.refreshDashboard = function() {
    const core = window.ContractApp?.core;
    if (core) {
        core.refresh();
    } else {
        console.warn('Core module not available for refresh');
        location.reload(); // Fallback
    }
};

// Debug function for development
window.debugContractApp = function() {
    console.log('=== Contract App Debug Info ===');
    console.log('App State:', window.ContractApp);
    
    if (window.ContractApp?.modules) {
        console.log('Available Modules:');
        Object.entries(window.ContractApp.modules).forEach(([name, module]) => {
            console.log(`  ${name}:`, {
                initialized: module.initialized,
                name: module.name
            });
        });
    }
    
    if (window.ContractApp?.data) {
        console.log('App Data:');
        Object.entries(window.ContractApp.data).forEach(([key, value]) => {
            console.log(`  ${key}: ${Array.isArray(value) ? value.length + ' items' : typeof value}`);
        });
    }
    
    console.log('Current Tab:', window.ContractApp?.currentTab);
    console.log('=== End Debug Info ===');
    
    return window.ContractApp;
};

console.log('Dashboard: Main dashboard.js loaded - modular architecture active');
console.log('Dashboard: Available debug function: window.debugContractApp()');