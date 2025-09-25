/**
 * Core Application Module
 * 
 * Handles application initialization, coordination between modules, and global state management.
 * This is the main entry point that orchestrates all other modules.
 */

// Global application state
window.ContractApp = {
    initialized: false,
    currentTab: 'dashboard',
    modules: {},
    data: {
        contracts: [],
        templates: [],
        analysisResults: [],
        systemStatus: {}
    }
};

/**
 * Core Application Class
 */
class CoreModule {
    constructor() {
        this.initialized = false;
        this.moduleLoadOrder = [
            'utils',
            'notifications', 
            'navigation',
            'dashboard',
            'upload',
            'settings',
            'prompts'
        ];
    }

    /**
     * Initialize the application
     */
    async init() {
        if (this.initialized) {
            console.warn('Application already initialized');
            return;
        }

        console.log('Core: Initializing Contract Analyzer Application...');

        try {
            // Wait for DOM to be ready
            await this.waitForDOM();
            
            // Initialize modules in order
            await this.initializeModules();
            
            // Set up global event handlers
            this.setupGlobalEventHandlers();
            
            // Load initial data
            await this.loadInitialData();
            
            // Start periodic updates
            this.startPeriodicUpdates();
            
            // Show initial tab
            this.showInitialTab();
            
            this.initialized = true;
            window.ContractApp.initialized = true;
            
            console.log('Core: Application initialization completed successfully');
            
        } catch (error) {
            console.error('Core: Application initialization failed:', error);
            this.handleInitializationError(error);
        }
    }

    /**
     * Wait for DOM to be fully ready
     */
    waitForDOM() {
        return new Promise((resolve) => {
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', resolve);
            } else {
                resolve();
            }
        });
    }

    /**
     * Initialize all modules in the correct order
     */
    async initializeModules() {
        console.log('Core: Initializing modules...');
        
        for (const moduleName of this.moduleLoadOrder) {
            try {
                console.log(`Core: Initializing ${moduleName} module...`);
                
                // Get module constructor from global scope
                const ModuleClass = window[this.capitalizeFirst(moduleName) + 'Module'];
                
                if (!ModuleClass) {
                    console.warn(`Core: Module ${moduleName} not found, skipping...`);
                    continue;
                }
                
                // Create and initialize module instance
                const moduleInstance = new ModuleClass();
                await moduleInstance.init();
                
                // Store module reference
                window.ContractApp.modules[moduleName] = moduleInstance;
                
                console.log(`Core: ${moduleName} module initialized successfully`);
                
            } catch (error) {
                console.error(`Core: Failed to initialize ${moduleName} module:`, error);
                // Continue with other modules rather than failing completely
            }
        }
    }

    /**
     * Set up global event handlers
     */
    setupGlobalEventHandlers() {
        // Handle window resize for responsive design
        window.addEventListener('resize', this.handleWindowResize.bind(this));
        
        // Handle keyboard shortcuts
        document.addEventListener('keydown', this.handleKeyboardShortcuts.bind(this));
        
        // Handle browser back/forward
        window.addEventListener('popstate', this.handlePopState.bind(this));
        
        // Handle visibility change (tab switching)
        document.addEventListener('visibilitychange', this.handleVisibilityChange.bind(this));
        
        console.log('Core: Global event handlers setup complete');
    }

    /**
     * Load initial application data
     */
    async loadInitialData() {
        console.log('Core: Loading initial data...');
        
        try {
            // Load data from multiple endpoints in parallel
            const [analysisResults, contracts, templates, health] = await Promise.all([
                this.fetchData('/api/analysis-results'),
                this.fetchData('/api/contracts'),
                this.fetchData('/api/templates'),
                this.fetchData('/api/health')
            ]);
            
            // Update global data state
            window.ContractApp.data = {
                analysisResults: analysisResults,
                contracts: contracts.contracts || [],
                templates: templates.templates || [],
                systemStatus: health
            };
            
            // Notify modules about data update
            this.notifyModules('dataUpdated', window.ContractApp.data);
            
            console.log('Core: Initial data loaded successfully');
            
        } catch (error) {
            console.error('Core: Error loading initial data:', error);
            this.getModule('notifications').show('Error loading application data', 'error');
        }
    }

    /**
     * Fetch data from API endpoint
     */
    async fetchData(endpoint) {
        try {
            const response = await fetch(endpoint);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`Core: Error fetching ${endpoint}:`, error);
            return null;
        }
    }

    /**
     * Start periodic data updates
     */
    startPeriodicUpdates() {
        // Update data every 30 seconds
        setInterval(() => {
            if (!document.hidden) {
                this.loadInitialData();
            }
        }, 30000);
        
        console.log('Core: Periodic updates started');
    }

    /**
     * Show the initial tab
     */
    showInitialTab() {
        const navigation = this.getModule('navigation');
        if (navigation) {
            navigation.showTab('dashboard');
        }
    }

    /**
     * Handle initialization errors
     */
    handleInitializationError(error) {
        // Show error message to user
        const errorMessage = `Application failed to initialize: ${error.message}`;
        
        // Try to show notification if available
        try {
            if (window.ContractApp.modules.notifications) {
                window.ContractApp.modules.notifications.show(errorMessage, 'error');
            } else {
                alert(errorMessage);
            }
        } catch (e) {
            alert(errorMessage);
        }
    }

    /**
     * Get a module instance
     */
    getModule(moduleName) {
        return window.ContractApp.modules[moduleName] || null;
    }

    /**
     * Notify all modules about an event
     */
    notifyModules(eventName, data = null) {
        Object.values(window.ContractApp.modules).forEach(module => {
            if (typeof module.handleEvent === 'function') {
                try {
                    module.handleEvent(eventName, data);
                } catch (error) {
                    console.error(`Core: Error notifying module about ${eventName}:`, error);
                }
            }
        });
    }

    /**
     * Handle window resize
     */
    handleWindowResize() {
        this.notifyModules('windowResize', {
            width: window.innerWidth,
            height: window.innerHeight
        });
    }

    /**
     * Handle keyboard shortcuts
     */
    handleKeyboardShortcuts(event) {
        // Ctrl/Cmd + R: Refresh data
        if ((event.ctrlKey || event.metaKey) && event.key === 'r' && !event.shiftKey) {
            event.preventDefault();
            this.loadInitialData();
            this.getModule('notifications').show('Data refreshed', 'info');
            return;
        }
        
        // Escape: Close modals or reset state
        if (event.key === 'Escape') {
            this.notifyModules('escapePressed');
            return;
        }
    }

    /**
     * Handle browser back/forward
     */
    handlePopState(event) {
        // Handle browser navigation if needed
        console.log('Core: Browser navigation detected');
    }

    /**
     * Handle tab visibility change
     */
    handleVisibilityChange() {
        if (!document.hidden) {
            // Tab became visible - refresh data
            this.loadInitialData();
        }
    }

    /**
     * Utility: Capitalize first letter
     */
    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    /**
     * Public API for manual data refresh
     */
    async refresh() {
        await this.loadInitialData();
        this.getModule('notifications').show('Application data refreshed', 'success');
    }

    /**
     * Public API for getting application data
     */
    getData() {
        return window.ContractApp.data;
    }

    /**
     * Public API for updating application data
     */
    updateData(newData) {
        window.ContractApp.data = { ...window.ContractApp.data, ...newData };
        this.notifyModules('dataUpdated', window.ContractApp.data);
    }
}

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    if (!window.ContractApp.initialized) {
        const core = new CoreModule();
        await core.init();
        
        // Store core reference globally
        window.ContractApp.core = core;
    }
});

// Export for module use
window.CoreModule = CoreModule;