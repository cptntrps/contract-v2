/**
 * Navigation Module
 * 
 * Handles sidebar navigation, tab switching, and mobile menu functionality.
 * Coordinates navigation state and ensures proper UI updates when tabs change.
 */

class NavigationModule {
    constructor() {
        this.name = 'navigation';
        this.initialized = false;
        this.currentTab = 'dashboard';
        this.tabs = ['dashboard', 'upload', 'prompts', 'settings'];
        this.sidebarVisible = true;
        this.isMobile = false;
    }

    /**
     * Initialize the navigation module
     */
    async init() {
        console.log('Navigation: Initializing navigation system...');
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Set up mobile detection
        this.checkMobileState();
        
        // Set up keyboard shortcuts
        this.setupKeyboardShortcuts();
        
        // Initialize sidebar state
        this.initializeSidebarState();
        
        this.initialized = true;
        console.log('Navigation: Navigation system initialized successfully');
    }

    /**
     * Handle module events
     */
    handleEvent(eventName, data) {
        switch (eventName) {
            case 'windowResize':
                this.handleWindowResize(data);
                break;
            case 'escapePressed':
                this.closeMobileSidebar();
                break;
        }
    }

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Sidebar menu items
        this.setupMenuItemListeners();
        
        // Mobile menu toggle
        this.setupMobileToggleListeners();
        
        // Outside click to close mobile menu
        this.setupOutsideClickListener();
        
        console.log('Navigation: Event listeners setup complete');
    }

    /**
     * Set up menu item event listeners
     */
    setupMenuItemListeners() {
        const menuItems = document.querySelectorAll('.menu-item a[data-tab]');
        
        if (menuItems.length === 0) {
            console.warn('Navigation: No menu items found');
            return;
        }
        
        menuItems.forEach((item, index) => {
            // Remove any existing listeners by cloning the node
            const newItem = item.cloneNode(true);
            item.parentNode.replaceChild(newItem, item);
            
            // Add new listener
            newItem.addEventListener('click', this.handleMenuClick.bind(this));
            
            console.log(`Navigation: Setup listener for menu item ${index + 1}: ${newItem.dataset.tab}`);
        });
        
        console.log(`Navigation: Setup ${menuItems.length} menu item listeners`);
    }

    /**
     * Set up mobile toggle listeners
     */
    setupMobileToggleListeners() {
        const toggleButtons = document.querySelectorAll('.sidebar-toggle, .menu-toggle');
        
        toggleButtons.forEach(button => {
            button.addEventListener('click', this.toggleSidebar.bind(this));
        });
        
        console.log(`Navigation: Setup ${toggleButtons.length} mobile toggle listeners`);
    }

    /**
     * Set up outside click listener for mobile
     */
    setupOutsideClickListener() {
        document.addEventListener('click', (event) => {
            if (this.isMobile && this.sidebarVisible) {
                const sidebar = document.querySelector('.sidebar');
                const toggleButtons = document.querySelectorAll('.sidebar-toggle, .menu-toggle');
                
                // Check if click was outside sidebar and not on toggle buttons
                const isOutsideSidebar = sidebar && !sidebar.contains(event.target);
                const isNotToggle = !Array.from(toggleButtons).some(button => button.contains(event.target));
                
                if (isOutsideSidebar && isNotToggle) {
                    this.closeMobileSidebar();
                }
            }
        });
    }

    /**
     * Handle menu item click
     */
    handleMenuClick(event) {
        event.preventDefault();
        
        const targetTab = event.currentTarget.dataset.tab;
        if (!targetTab) {
            console.error('Navigation: No data-tab attribute found on menu item');
            return;
        }
        
        console.log(`Navigation: Menu clicked - ${targetTab}`);
        this.showTab(targetTab);
        
        // Close mobile sidebar after navigation
        if (this.isMobile) {
            this.closeMobileSidebar();
        }
    }

    /**
     * Show specific tab
     */
    showTab(tabName) {
        if (!tabName || !this.tabs.includes(tabName)) {
            console.error(`Navigation: Invalid tab name: ${tabName}`);
            const notifications = window.ContractApp?.modules?.notifications;
            if (notifications) {
                notifications.error(`Invalid tab: ${tabName}`);
            }
            return false;
        }

        console.log(`Navigation: Switching to tab: ${tabName}`);

        try {
            // Hide all tab contents
            this.hideAllTabs();
            
            // Show target tab
            const targetTab = document.getElementById(tabName);
            if (!targetTab) {
                throw new Error(`Tab content element not found: ${tabName}`);
            }
            
            targetTab.classList.add('active');
            
            // Update menu active state
            this.updateMenuActiveState(tabName);
            
            // Update page title
            this.updatePageTitle(tabName);
            
            // Update current tab
            this.currentTab = tabName;
            window.ContractApp.currentTab = tabName;
            
            // Load tab-specific data
            this.loadTabData(tabName);
            
            // Notify other modules about tab change
            const core = window.ContractApp?.core;
            if (core) {
                core.notifyModules('tabChanged', { 
                    currentTab: tabName,
                    previousTab: this.currentTab 
                });
            }
            
            console.log(`Navigation: Successfully switched to tab: ${tabName}`);
            return true;
            
        } catch (error) {
            console.error(`Navigation: Error switching to tab ${tabName}:`, error);
            
            const notifications = window.ContractApp?.modules?.notifications;
            if (notifications) {
                notifications.error(`Error switching to ${tabName} tab`);
            }
            
            return false;
        }
    }

    /**
     * Hide all tabs
     */
    hideAllTabs() {
        const tabContents = document.querySelectorAll('.tab-content');
        tabContents.forEach(content => {
            content.classList.remove('active');
        });
    }

    /**
     * Update menu active state
     */
    updateMenuActiveState(activeTab) {
        // Remove active class from all menu items
        const menuItems = document.querySelectorAll('.menu-item');
        menuItems.forEach(item => {
            item.classList.remove('active');
        });
        
        // Add active class to current menu item
        const activeMenuItem = document.querySelector(`[data-tab="${activeTab}"]`);
        if (activeMenuItem) {
            activeMenuItem.parentElement.classList.add('active');
        } else {
            console.warn(`Navigation: Menu item not found for tab: ${activeTab}`);
        }
    }

    /**
     * Update page title based on tab
     */
    updatePageTitle(tab) {
        const titleElement = document.getElementById('pageTitle');
        if (!titleElement) {
            console.warn('Navigation: Page title element not found');
            return;
        }
        
        const titles = {
            'dashboard': 'Contract Review Dashboard',
            'upload': 'File Upload & Management', 
            'prompts': 'LLM Prompt Management',
            'settings': 'System Configuration'
        };
        
        const newTitle = titles[tab] || 'Contract Review Dashboard';
        titleElement.textContent = newTitle;
        
        // Also update browser title
        document.title = `${newTitle} - Contract Analyzer`;
        
        console.log(`Navigation: Updated page title to: ${newTitle}`);
    }

    /**
     * Load tab-specific data
     */
    loadTabData(tabName) {
        console.log(`Navigation: Loading data for tab: ${tabName}`);
        
        try {
            // Get appropriate module and trigger data loading
            const moduleName = tabName;
            const module = window.ContractApp?.modules?.[moduleName];
            
            if (module && typeof module.onTabActivated === 'function') {
                module.onTabActivated();
                console.log(`Navigation: Triggered data loading for ${moduleName} module`);
            } else {
                console.log(`Navigation: No data loading required for tab: ${tabName}`);
            }
            
        } catch (error) {
            console.error(`Navigation: Error loading tab data for ${tabName}:`, error);
        }
    }

    /**
     * Toggle sidebar visibility
     */
    toggleSidebar() {
        const sidebar = document.querySelector('.sidebar');
        if (!sidebar) {
            console.warn('Navigation: Sidebar element not found');
            return;
        }
        
        this.sidebarVisible = !this.sidebarVisible;
        
        if (this.sidebarVisible) {
            sidebar.classList.add('active');
        } else {
            sidebar.classList.remove('active');
        }
        
        console.log(`Navigation: Sidebar ${this.sidebarVisible ? 'opened' : 'closed'}`);
    }

    /**
     * Close mobile sidebar
     */
    closeMobileSidebar() {
        if (this.isMobile && this.sidebarVisible) {
            const sidebar = document.querySelector('.sidebar');
            if (sidebar) {
                sidebar.classList.remove('active');
                this.sidebarVisible = false;
                console.log('Navigation: Mobile sidebar closed');
            }
        }
    }

    /**
     * Open mobile sidebar
     */
    openMobileSidebar() {
        if (this.isMobile && !this.sidebarVisible) {
            const sidebar = document.querySelector('.sidebar');
            if (sidebar) {
                sidebar.classList.add('active');
                this.sidebarVisible = true;
                console.log('Navigation: Mobile sidebar opened');
            }
        }
    }

    /**
     * Check mobile state and update UI accordingly
     */
    checkMobileState() {
        const utils = window.ContractApp?.modules?.utils;
        const wasMobile = this.isMobile;
        
        this.isMobile = utils ? utils.isMobile() : window.innerWidth <= 768;
        
        if (wasMobile !== this.isMobile) {
            console.log(`Navigation: Mobile state changed: ${this.isMobile}`);
            this.updateMobileUI();
        }
    }

    /**
     * Update UI for mobile/desktop
     */
    updateMobileUI() {
        const sidebar = document.querySelector('.sidebar');
        if (!sidebar) return;
        
        if (this.isMobile) {
            // On mobile, hide sidebar by default
            sidebar.classList.remove('active');
            this.sidebarVisible = false;
        } else {
            // On desktop, show sidebar
            sidebar.classList.add('active');
            this.sidebarVisible = true;
        }
    }

    /**
     * Handle window resize
     */
    handleWindowResize(data) {
        this.checkMobileState();
    }

    /**
     * Set up keyboard shortcuts
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (event) => {
            // Alt + number keys for quick tab switching
            if (event.altKey && !event.ctrlKey && !event.shiftKey) {
                const keyMap = {
                    '1': 'dashboard',
                    '2': 'upload',
                    '3': 'prompts',
                    '4': 'settings'
                };
                
                const targetTab = keyMap[event.key];
                if (targetTab) {
                    event.preventDefault();
                    this.showTab(targetTab);
                }
            }
        });
        
        console.log('Navigation: Keyboard shortcuts enabled (Alt+1-4 for tabs)');
    }

    /**
     * Initialize sidebar state based on screen size
     */
    initializeSidebarState() {
        this.checkMobileState();
        this.updateMobileUI();
    }

    /**
     * Get current tab
     */
    getCurrentTab() {
        return this.currentTab;
    }

    /**
     * Get available tabs
     */
    getAvailableTabs() {
        return [...this.tabs];
    }

    /**
     * Add new tab (for dynamic tabs)
     */
    addTab(tabName) {
        if (!this.tabs.includes(tabName)) {
            this.tabs.push(tabName);
            console.log(`Navigation: Added new tab: ${tabName}`);
        }
    }

    /**
     * Remove tab (for dynamic tabs)
     */
    removeTab(tabName) {
        const index = this.tabs.indexOf(tabName);
        if (index > -1) {
            this.tabs.splice(index, 1);
            
            // If removing current tab, switch to dashboard
            if (this.currentTab === tabName) {
                this.showTab('dashboard');
            }
            
            console.log(`Navigation: Removed tab: ${tabName}`);
        }
    }

    /**
     * Check if tab exists
     */
    hasTab(tabName) {
        return this.tabs.includes(tabName);
    }
}

// Export for global use
window.NavigationModule = NavigationModule;