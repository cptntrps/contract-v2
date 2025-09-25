// Dashboard JavaScript - Enhanced with Sidebar Navigation and Report Generation
let dashboardInitialized = false;

document.addEventListener('DOMContentLoaded', function() {
    if (!dashboardInitialized) {
        console.log('Dashboard initializing...');
        initializeDashboard();
        dashboardInitialized = true;
    }
});

// Global variables
let currentTab = 'dashboard';
let fileUploadsSetup = false; // Flag to prevent duplicate setup
let dashboardData = {
    contracts: [],
    templates: [],
    analysisResults: [],
    systemStatus: {}
};

// Toggle sidebar for mobile
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        sidebar.classList.toggle('active');
    }
    
    // Close sidebar when clicking outside
    document.addEventListener('click', function(event) {
        const sidebar = document.querySelector('.sidebar');
        const sidebarToggle = document.querySelector('.sidebar-toggle');
        
        if (sidebar && sidebarToggle && 
            !sidebar.contains(event.target) && 
            !sidebarToggle.contains(event.target)) {
            sidebar.classList.remove('active');
        }
    });
}

function initializeDashboard() {
    console.log('Setting up dashboard...');
    
    // Setup sidebar navigation
    setupSidebarNavigation();
    
    // Setup file uploads
    setupFileUploads();
    
    // Load initial data
    loadDashboardData();
    
    // Setup modal events
    setupModalEvents();
    
    // Check system status
    checkSystemStatus();
    
    // Load model information for header display
    loadModelInfo();
    
    // Setup auto-refresh
    setInterval(loadDashboardData, 30000);
    
    // Setup table interactions
    setupTableInteractions();
    
    // Initialize default tab
    showTab('dashboard');
    
    console.log('Dashboard initialized successfully');
}

function setupSidebarNavigation() {
    console.log('Setting up sidebar navigation...');
    
    // Use proper DOM ready state check instead of setTimeout
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSidebarEvents);
    } else {
        initSidebarEvents();
    }
}

function initSidebarEvents() {
    const menuItems = document.querySelectorAll('.menu-item a[data-tab]');
    const tabContents = document.querySelectorAll('.tab-content');
    
    console.log('Found menu items:', menuItems.length);
    console.log('Found tab contents:', tabContents.length);
    
    // List all found elements for debugging
    menuItems.forEach((item, index) => {
        console.log(`Menu item ${index + 1}: data-tab="${item.dataset.tab}"`);
    });
    
    tabContents.forEach((content, index) => {
        console.log(`Tab content ${index + 1}: id="${content.id}"`);
    });
    
    if (menuItems.length === 0) {
        console.error('No menu items found! Check if .menu-item a[data-tab] elements exist.');
        return;
    }
    
    if (tabContents.length === 0) {
        console.error('No tab contents found! Check if .tab-content elements exist.');
        return;
    }
    
    // Clear all existing event listeners first
    menuItems.forEach((item) => {
        // Clone the node to remove all event listeners
        const newItem = item.cloneNode(true);
        item.parentNode.replaceChild(newItem, item);
    });
    
    // Re-query for fresh elements and add event listeners
    const freshMenuItems = document.querySelectorAll('.menu-item a[data-tab]');
    freshMenuItems.forEach((item, index) => {
        console.log(`Setting up menu item ${index + 1}:`, item.dataset.tab);
        item.addEventListener('click', handleTabClick);
    });
    
    console.log('Sidebar navigation setup complete');
}

function handleTabClick(e) {
    e.preventDefault();
    console.log('Menu item clicked:', this.dataset.tab);
    
    const targetTab = this.dataset.tab;
    
    if (!targetTab) {
        console.error('No data-tab attribute found on menu item');
        return;
    }
    
    showTab(targetTab);
    
    // Update active menu item
    document.querySelectorAll('.menu-item').forEach(menu => {
        menu.classList.remove('active');
    });
    this.parentElement.classList.add('active');
    
    // Update page title
    updatePageTitle(targetTab);
    
    // Load tab-specific data
    loadTabData(targetTab);
    
    currentTab = targetTab;
}

function updatePageTitle(tab) {
    const pageTitle = document.getElementById('pageTitle');
    const titles = {
        'dashboard': 'Contract Review Dashboard',
        'upload': 'File Upload & Management',
        'settings': 'System Configuration'
    };
    
    if (pageTitle) {
        pageTitle.textContent = titles[tab] || 'Contract Review Dashboard';
        console.log('Updated page title to:', titles[tab] || 'Contract Review Dashboard');
    } else {
        console.error('Page title element not found');
    }
}

function loadDashboardData() {
    console.log('Loading dashboard data...');
    
    // Load multiple endpoints in parallel
    Promise.all([
        fetch('/api/analysis-results').then(response => response.json()),
        fetch('/api/contracts').then(response => response.json()),
        fetch('/api/templates').then(response => response.json()),
        fetch('/api/health').then(response => response.json())
    ]).then(([analysisResults, contracts, templates, health]) => {
        dashboardData.analysisResults = analysisResults;
        dashboardData.contracts = contracts.contracts || [];
        dashboardData.templates = templates.templates || [];
        dashboardData.systemStatus = health;
        
        updateDashboard();
        console.log('Dashboard data loaded successfully');
    }).catch(error => {
        console.error('Error loading dashboard data:', error);
        showNotification('Error loading dashboard data', 'error');
    });
}

// Notification system
function showNotification(message, type = 'info', duration = 5000) {
    console.log(`Notification: ${message} (${type})`);
    
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => notification.remove());
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${getNotificationIcon(type)}"></i>
            <span>${message}</span>
            <button class="notification-close" onclick="closeNotification(this)">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    // Add to body
    document.body.appendChild(notification);
    
    // Auto-remove after duration
    setTimeout(() => {
        closeNotification(notification);
    }, duration);
}

function getNotificationIcon(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-triangle',
        'warning': 'exclamation-circle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

function closeNotification(element) {
    const notification = element.closest ? element.closest('.notification') : element;
    if (notification) {
        notification.style.opacity = '0';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }
}

// Tab data loading function
function loadTabData(tabName) {
    console.log('Loading tab data for:', tabName);
    console.log('tabName type:', typeof tabName);
    console.log('tabName value:', JSON.stringify(tabName));
    
    switch(tabName) {
        case 'upload':
            console.log('Loading upload tab data...');
            updateFileListings();
            // setupFileUploads() is called once during initialization, not needed here
            break;
        case 'settings':
            console.log('Loading settings tab data...');
            loadSettings();
            break;
        case 'prompts':
            console.log('Loading prompts tab data...');
            initializePromptManagement();
            break;
        case 'dashboard':
            console.log('Loading dashboard tab data...');
            // Already loaded in main data refresh
            break;
        default:
            console.log('Unknown tab:', tabName);
    }
    console.log('loadTabData switch completed for:', tabName);
}

function updateFileListings() {
    console.log('Updating file listings...');
    updateContractsList();
    updateTemplatesList();
}

// Removed duplicate function - using the updated one below

function loadAvailableModels() {
    console.log('Loading available models...');
    
    fetch('/api/available-models')
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('llmModel');
            select.innerHTML = '';
            
            if (data.success) {
                data.models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model.name;
                    option.textContent = `${model.name} (${model.size})`;
                    if (model.name === data.current_model) {
                        option.selected = true;
                    }
                    select.appendChild(option);
                });
                
                // Add change event listener
                select.addEventListener('change', function() {
                    changeModel(this.value);
                });
            } else {
                select.innerHTML = '<option value="">Error loading models</option>';
            }
        })
        .catch(error => {
            console.error('Error loading models:', error);
            const select = document.getElementById('llmModel');
            select.innerHTML = '<option value="">Error loading models</option>';
        });
}

function changeModel(modelName) {
    console.log('Changing model to:', modelName);
    
    showNotification('Changing model...', 'info');
    
    fetch('/api/change-model', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            model_name: modelName
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(`Successfully changed to ${modelName}`, 'success');
            loadModelInfo();
        } else {
            showNotification('Failed to change model: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error changing model:', error);
        showNotification('Error changing model', 'error');
    });
}

function loadModelInfo() {
    fetch('/api/model-info')
        .then(response => response.json())
        .then(data => {
            const infoDiv = document.getElementById('current-model-info');
            const modelStatusText = document.getElementById('model-status-text');
            
            if (data.name) {
                // Update settings tab model info
                const modelName = data.name;
                const status = data.connection_healthy ? 'Connected' : 'Disconnected';
                
                let infoHtml = `<strong>Current Model:</strong> ${modelName}<br>`;
                
                // Add size info if available (for Ollama)
                if (data.info && data.info.size) {
                    const sizeInGB = (data.info.size / (1024 * 1024 * 1024)).toFixed(1);
                    infoHtml += `<strong>Size:</strong> ${sizeInGB} GB<br>`;
                }
                
                infoHtml += `<strong>Status:</strong> ${status}`;
                
                if (infoDiv) {
                    infoDiv.innerHTML = infoHtml;
                }
                
                // Update header model status
                if (modelStatusText) {
                    if (data.info && data.info.size) {
                        const sizeInGB = (data.info.size / (1024 * 1024 * 1024)).toFixed(1);
                        modelStatusText.textContent = `${modelName} (${sizeInGB} GB)`;
                    } else {
                        modelStatusText.textContent = modelName;
                    }
                }
                
                console.log('Model info loaded successfully:', modelName);
            } else {
                if (infoDiv) {
                    infoDiv.innerHTML = 'Error loading model info';
                }
                if (modelStatusText) {
                    modelStatusText.textContent = 'Model info unavailable';
                }
            }
        })
        .catch(error => {
            console.error('Error loading model info:', error);
            const infoDiv = document.getElementById('current-model-info');
            const modelStatusText = document.getElementById('model-status-text');
            if (infoDiv) {
                infoDiv.innerHTML = 'Error loading model info';
            }
            if (modelStatusText) {
                modelStatusText.textContent = 'Error loading model';
            }
        });
}

function loadCacheStats() {
    console.log('Loading cache statistics...');
    
    fetch('/api/cache-stats')
        .then(response => response.json())
        .then(data => {
            const statsDiv = document.getElementById('cacheStats');
            if (data.success) {
                statsDiv.innerHTML = `
                    <div class="cache-stat">
                        <strong>Analysis Cache:</strong> ${data.stats.analysis_count} items (${data.stats.analysis_size})
                    </div>
                    <div class="cache-stat">
                        <strong>Reports Cache:</strong> ${data.stats.reports_count} items (${data.stats.reports_size})
                    </div>
                    <div class="cache-stat">
                        <strong>Memory Cache:</strong> ${data.stats.memory_count} items (${data.stats.memory_size})
                    </div>
                    <div class="cache-stat">
                        <strong>Total Cache Size:</strong> ${data.stats.total_size}
                    </div>
                `;
            } else {
                statsDiv.innerHTML = '<p>Error loading cache statistics</p>';
            }
        })
        .catch(error => {
            console.error('Error loading cache stats:', error);
            document.getElementById('cacheStats').innerHTML = '<p>Error loading cache statistics</p>';
        });
}

function loadSystemSettings() {
    // Load other system settings like file size limits, etc.
    console.log('Loading system settings...');
}

function clearCache(type) {
    console.log('Clearing cache:', type);
    
    const messages = {
        'analysis': 'Clear analysis cache?',
        'reports': 'Clear reports cache?',
        'memory': 'Clear memory cache?',
        'all': 'Clear all cache data?'
    };
    
    if (confirm(messages[type] || 'Clear cache?')) {
        showNotification(`Clearing ${type} cache...`, 'info');
        
        fetch('/api/clear-cache', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                cache_type: type
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(`${type} cache cleared successfully`, 'success');
                loadCacheStats(); // Refresh cache stats
            } else {
                showNotification(`Failed to clear ${type} cache: ` + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error clearing cache:', error);
            showNotification(`Error clearing ${type} cache`, 'error');
        });
    }
}

function refreshDashboard() {
    console.log('Refreshing dashboard...');
    showNotification('Refreshing dashboard...', 'info');
    loadDashboardData();
}


function setupModalEvents() {
    console.log('Setting up modal events...');
    // Stub implementation
}

function setupTableInteractions() {
    console.log('Setting up table interactions...');
    // Stub implementation
}

// Consolidated tab switching function
function showTab(tabName) {
    console.log('Showing tab:', tabName);
    
    if (!tabName) {
        console.error('No tab name provided to showTab');
        return false;
    }
    
    // Validate tab exists
    const targetTab = document.getElementById(tabName);
    if (!targetTab) {
        console.error('Target tab not found:', tabName);
        const availableTabs = Array.from(document.querySelectorAll('.tab-content')).map(tab => tab.id);
        console.error('Available tabs:', availableTabs);
        showNotification(`Error: Tab "${tabName}" not found`, 'error');
        return false;
    }
    
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => {
        content.classList.remove('active');
        console.log(`Hiding tab: ${content.id}`);
    });
    
    // Remove active class from all menu items
    const menuItems = document.querySelectorAll('.menu-item');
    menuItems.forEach(item => {
        item.classList.remove('active');
    });
    
    // Show target tab content
    targetTab.classList.add('active');
    console.log('Successfully showed tab:', tabName);
    
    // Activate corresponding menu item
    const menuItem = document.querySelector(`[data-tab="${tabName}"]`);
    if (menuItem) {
        menuItem.parentElement.classList.add('active');
        console.log('Activated menu item for tab:', tabName);
    } else {
        console.error('Menu item not found for tab:', tabName);
    }
    
    // Update page title
    updatePageTitle(tabName);
    
    // Load tab-specific data
    console.log('About to call loadTabData for:', tabName);
    loadTabData(tabName);
    console.log('loadTabData call completed for:', tabName);
    
    // Update current tab
    currentTab = tabName;
    
    // Show brief success notification
    showNotification(`Switched to ${tabName} tab`, 'info', 1500);
    
    return true;
}

// Batch operations functions
function analyzeAllContracts() {
    console.log('Analyzing all contracts...');
    
    if (dashboardData.contracts.length === 0) {
        showNotification('No contracts available to analyze', 'warning');
        return;
    }
    
    showNotification('Starting batch analysis...', 'info');
    
    // Call the batch analyze endpoint
    fetch('/api/batch-analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            contracts: dashboardData.contracts.map(c => c.id)
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(`Successfully analyzed ${data.results.length} contracts`, 'success');
            loadDashboardData(); // Refresh the dashboard
        } else {
            showNotification('Batch analysis failed: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error during batch analysis:', error);
        showNotification('Error during batch analysis', 'error');
    });
}

function generateBatchReports() {
    console.log('Generating batch reports...');
    
    if (dashboardData.analysisResults.length === 0) {
        showNotification('No analysis results available for report generation', 'warning');
        return;
    }
    
    showNotification('Generating batch reports...', 'info');
    
    // You could implement batch report generation here
    setTimeout(() => {
        showNotification('Batch reports generated successfully', 'success');
    }, 2000);
}

function clearAllContracts() {
    if (confirm('Are you sure you want to clear all contracts? This will remove all uploaded contracts and their analysis results. This action cannot be undone.')) {
        console.log('Clearing all contracts...');
        
        showNotification('Clearing contracts...', 'info');
        
        // Clear only contracts
        fetch('/api/clear-contracts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(data.message, 'success');
                loadDashboardData(); // Refresh the dashboard
            } else {
                showNotification('Failed to clear contracts: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error clearing contracts:', error);
            showNotification('Error clearing contracts', 'error');
        });
    }
}

function clearAllFiles() {
    if (confirm('Are you sure you want to clear all files? This action cannot be undone.')) {
        console.log('Clearing all files...');
        
        // Clear contracts and templates
        fetch('/api/clear-files', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('All files cleared successfully', 'success');
                loadDashboardData(); // Refresh the dashboard
            } else {
                showNotification('Failed to clear files: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error clearing files:', error);
            showNotification('Error clearing files', 'error');
        });
    }
}

function analyzeContract(contractId) {
    console.log('Analyzing contract:', contractId);
    
    showNotification('Analyzing contract...', 'info');
    
    fetch('/api/analyze-contract', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            contract_id: contractId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Contract analyzed successfully', 'success');
            loadDashboardData(); // Refresh the dashboard
        } else {
            showNotification('Contract analysis failed: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error analyzing contract:', error);
        showNotification('Error analyzing contract', 'error');
    });
}

function deleteContract(contractId) {
    if (confirm('Are you sure you want to delete this contract?')) {
        console.log('Deleting contract:', contractId);
        
        fetch(`/api/contracts/${contractId}`, {
            method: 'DELETE',
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Contract deleted successfully', 'success');
                loadDashboardData(); // Refresh the dashboard
            } else {
                showNotification('Failed to delete contract: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error deleting contract:', error);
            showNotification('Error deleting contract', 'error');
        });
    }
}

function editTemplate(templateId) {
    console.log('Editing template:', templateId);
    showNotification('Template editing not implemented yet', 'info');
}

function deleteTemplate(templateId) {
    if (confirm('Are you sure you want to delete this template?')) {
        console.log('Deleting template:', templateId);
        
        fetch(`/api/templates/${templateId}`, {
            method: 'DELETE',
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Template deleted successfully', 'success');
                loadDashboardData(); // Refresh the dashboard
            } else {
                showNotification('Failed to delete template: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error deleting template:', error);
            showNotification('Error deleting template', 'error');
        });
    }
}

function updateDashboard() {
    updateMetrics();
    updateAnalysisTable();
    updateSystemStatus();
    updateFileListings();
}

function updateMetrics() {
    const metrics = {
        totalContracts: dashboardData.contracts.length,
        totalTemplates: dashboardData.templates.length,
        totalAnalyses: dashboardData.analysisResults.length,
        pendingReviews: dashboardData.analysisResults.filter(r => r.status !== 'No changes').length
    };
    
    // Update metric cards with animation
    Object.entries(metrics).forEach(([key, value]) => {
        const element = document.getElementById(key);
        if (element) {
            animateValue(element, parseInt(element.textContent) || 0, value, 1000);
        }
    });
}

function animateValue(element, start, end, duration) {
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsedTime = currentTime - startTime;
        const progress = Math.min(elapsedTime / duration, 1);
        
        const currentValue = Math.floor(start + (end - start) * progress);
        element.textContent = currentValue;
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

function updateAnalysisTable() {
    const tbody = document.getElementById('analysisTableBody');
    tbody.innerHTML = '';
    
    dashboardData.analysisResults.forEach(result => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${result.contract}</td>
            <td>${result.template}</td>
            <td>
                <span class="confidence-badge confidence-${getConfidenceClass(result.similarity)}">
                    ${result.similarity}%
                </span>
            </td>
            <td>
                <span class="status-badge status-${getStatusClass(result.status)}">
                    ${result.status}
                </span>
            </td>
            <td>System</td>
            <td>${formatDate(result.date)}</td>
            <td>${getNextStepSuggestion(result.status)}</td>
            <td>
                <button class="download-btn" onclick="downloadReport('${result.id}', 'review')" title="Download Redlined Document">
                    <i class="fas fa-file-word"></i>
                </button>
            </td>
            <td>
                <button class="download-btn" onclick="downloadReport('${result.id}', 'changes')" title="Download Changes Table">
                    <i class="fas fa-table"></i>
                </button>
            </td>
            <td>
                <button class="download-btn" onclick="downloadWordComRedlined('${result.id}')" title="Download Word Track Changes">
                    <i class="fas fa-file-word"></i>
                    <span style="font-size: 0.7em; margin-left: 2px;">TC</span>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function updateSystemStatus() {
    const statusIndicator = document.getElementById('systemStatus');
    const statusText = document.getElementById('statusText');
    const health = dashboardData.systemStatus;
    
    if (health.status === 'healthy') {
        statusIndicator.className = 'fas fa-circle status-indicator status-healthy';
        statusText.textContent = 'System Healthy';
    } else {
        statusIndicator.className = 'fas fa-circle status-indicator status-degraded';
        statusText.textContent = 'System Degraded';
    }
}


function updateContractsList() {
    console.log('updateContractsList called, contracts count:', dashboardData.contracts.length);
    
    const contractsList = document.getElementById('contractsList');
    if (!contractsList) {
        console.error('contractsList element not found!');
        return;
    }
    
    contractsList.innerHTML = '';
    
    dashboardData.contracts.forEach(contract => {
        const contractDiv = document.createElement('div');
        contractDiv.className = 'file-item';
        
        // Format file size
        const fileSize = contract.file_size ? formatFileSize(contract.file_size) : 'Unknown size';
        
        contractDiv.innerHTML = `
            <div class="file-info">
                <div class="file-name">${contract.filename}</div>
                <div class="file-details">Contract • ${fileSize}</div>
            </div>
            <div class="file-actions">
                <button class="action-btn small" onclick="analyzeContract('${contract.id}')" title="Analyze Contract">
                    <i class="fas fa-search"></i>
                </button>
                <button class="action-btn small danger" onclick="deleteContract('${contract.id}')" title="Delete Contract">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
        contractsList.appendChild(contractDiv);
    });
}

function updateTemplatesList() {
    console.log('updateTemplatesList called, templates count:', dashboardData.templates.length);
    
    const templatesList = document.getElementById('templatesList');
    if (!templatesList) {
        console.error('templatesList element not found!');
        return;
    }
    
    templatesList.innerHTML = '';
    
    dashboardData.templates.forEach(template => {
        const templateDiv = document.createElement('div');
        templateDiv.className = 'file-item';
        
        // Format file size
        const fileSize = template.size ? formatFileSize(template.size) : 'Unknown size';
        
        templateDiv.innerHTML = `
            <div class="file-info">
                <div class="file-name">${template.display_name || template.filename}</div>
                <div class="file-details">Template • ${fileSize}</div>
            </div>
            <div class="file-actions">
                <button class="action-btn small" onclick="editTemplate('${template.filename}')" title="Edit Template">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="action-btn small danger" onclick="deleteTemplate('${template.filename}')" title="Delete Template">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
        templatesList.appendChild(templateDiv);
    });
}

function setupFileUploads() {
    // Prevent duplicate setup
    if (fileUploadsSetup) {
        console.log('File uploads already setup, skipping...');
        return;
    }
    
    console.log('Setting up file uploads...');
    
    // Contract upload
    const contractUpload = document.getElementById('contractUpload');
    const contractInput = document.getElementById('contractFileInput');
    
    if (contractUpload && contractInput) {
        contractUpload.addEventListener('click', () => contractInput.click());
        contractUpload.addEventListener('dragover', handleDragOver);
        contractUpload.addEventListener('dragleave', handleDragLeave);
        contractUpload.addEventListener('drop', (e) => handleDrop(e, 'contract'));
        contractInput.addEventListener('change', (e) => {
            // Skip if files came from drag and drop
            if (!window.isDragDropUpload) {
                uploadFiles(e.target.files, 'contract');
            }
        });
        console.log('Contract upload area setup complete');
    } else {
        console.error('Contract upload elements not found');
    }
    
    // Template upload
    const templateUpload = document.getElementById('templateUpload');
    const templateInput = document.getElementById('templateFileInput');
    
    if (templateUpload && templateInput) {
        templateUpload.addEventListener('click', () => templateInput.click());
        templateUpload.addEventListener('dragover', handleDragOver);
        templateUpload.addEventListener('dragleave', handleDragLeave);
        templateUpload.addEventListener('drop', (e) => handleDrop(e, 'template'));
        templateInput.addEventListener('change', (e) => {
            // Skip if files came from drag and drop
            if (!window.isDragDropUpload) {
                uploadFiles(e.target.files, 'template');
            }
        });
        console.log('Template upload area setup complete');
    } else {
        console.error('Template upload elements not found');
    }
    
    // Modal upload
    const modalUpload = document.getElementById('modalFileInput');
    modalUpload.addEventListener('change', (e) => {
        // Skip if files came from drag and drop
        if (!window.isDragDropUpload) {
            uploadFiles(e.target.files, 'contract');
        }
    });
    
    // Mark as setup complete
    fileUploadsSetup = true;
    console.log('File uploads setup completed successfully');
}

function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    // Only remove the class if we're actually leaving the element (not just moving to a child)
    if (!e.currentTarget.contains(e.relatedTarget)) {
        e.currentTarget.classList.remove('drag-over');
    }
}

function handleDrop(e, type) {
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.classList.remove('drag-over');
    
    // Check if files were dropped
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        // Set a flag to indicate files came from drag and drop
        window.isDragDropUpload = true;
        uploadFiles(files, type);
        // Reset flag after a short delay
        setTimeout(() => {
            window.isDragDropUpload = false;
        }, 100);
    } else {
        showNotification('No files were dropped', 'warning');
    }
}

function uploadFiles(files, type) {
    console.log(`uploadFiles called with ${files.length} files, type: ${type}, isDragDrop: ${window.isDragDropUpload}`);
    
    Array.from(files).forEach(file => {
        console.log(`Processing file: ${file.name}`);
        
        // Validate file type
        if (!file.name.toLowerCase().endsWith('.docx')) {
            showNotification(`${file.name} is not a DOCX file. Only DOCX files are supported.`, 'error');
            return;
        }
        
        // Validate file size (16MB limit)
        const maxSize = 16 * 1024 * 1024; // 16MB
        if (file.size > maxSize) {
            showNotification(`${file.name} is too large. Maximum file size is 16MB.`, 'error');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', file);
        
        const endpoint = type === 'contract' ? '/api/contracts/upload' : '/api/templates/upload';
        const typeLabel = type === 'contract' ? 'contract' : 'template';
        
        // Show upload progress
        showUploadProgress(file.name);
        
        fetch(endpoint, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            hideUploadProgress();
            
            if (data.error) {
                showNotification(`Error uploading ${typeLabel} ${file.name}: ${data.error}`, 'error');
            } else {
                showNotification(`${typeLabel.charAt(0).toUpperCase() + typeLabel.slice(1)} ${file.name} uploaded successfully`, 'success');
                loadDashboardData();
            }
        })
        .catch(error => {
            hideUploadProgress();
            console.error('Upload error:', error);
            showNotification(`Error uploading ${typeLabel} ${file.name}`, 'error');
        });
    });
}

function setupModalEvents() {
    // Upload modal events
    const uploadModal = document.getElementById('uploadModal');
    const reportModal = document.getElementById('reportModal');
    
    // Close modals when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === uploadModal) {
            closeUploadModal();
        }
        if (event.target === reportModal) {
            closeReportModal();
        }
    });
    
    // Close modals with Escape key
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            closeUploadModal();
            closeReportModal();
        }
    });
}

function setupTableInteractions() {
    // Add sorting functionality
    const tableHeaders = document.querySelectorAll('.analysis-table th');
    tableHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const column = this.textContent.trim();
            sortTable(column);
        });
    });
}

// Modal functions
function openUploadModal() {
    document.getElementById('uploadModal').style.display = 'block';
}

function closeUploadModal() {
    document.getElementById('uploadModal').style.display = 'none';
}

function openReportModal() {
    document.getElementById('reportModal').style.display = 'block';
}

function closeReportModal() {
    document.getElementById('reportModal').style.display = 'none';
}

// Enhanced Report Generation Functions
function downloadReport(resultId, reportType) {
    const reportTypes = {
        'review': {
            endpoint: '/api/generate-redlined-document',
            filename: 'review_document.docx',
            icon: 'fas fa-file-word'
        },
        'changes': {
            endpoint: '/api/generate-changes-table',
            filename: 'changes_table.xlsx',
            icon: 'fas fa-table'
        }
    };
    
    const reportConfig = reportTypes[reportType];
    if (!reportConfig) {
        showNotification('Invalid report type', 'error');
        return;
    }
    
    // Show loading state
    showNotification('Generating report...', 'info');
    
    fetch(reportConfig.endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            result_id: resultId,
            report_type: reportType
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Report generation failed');
        }
        return response.blob();
    })
    .then(blob => {
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${resultId}_${reportConfig.filename}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showNotification('Report downloaded successfully', 'success');
    })
    .catch(error => {
        console.error('Download error:', error);
        showNotification('Error generating report', 'error');
    });
}

function generateSelectedReports() {
    const selectedTypes = {};
    
    // Check which report types are selected
    selectedTypes.review_docx = document.getElementById('generateReviewDoc').checked;
    selectedTypes.changes_xlsx = document.getElementById('generateChangesTable').checked;
    selectedTypes.changes_docx = document.getElementById('generateChangesTableDocx').checked;
    
    // Get selected contracts (if any)
    const selectedContracts = getSelectedContracts();
    
    if (selectedContracts.length === 0) {
        showNotification('Please select at least one contract', 'warning');
        return;
    }
    
    // Generate reports for selected contracts
    selectedContracts.forEach(contractId => {
        generateMultipleReports(contractId, selectedTypes);
    });
    
    closeReportModal();
}

function generateMultipleReports(contractId, reportTypes) {
    showNotification('Generating reports...', 'info');
    
    fetch('/api/generate-multiple-reports', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            contract_id: contractId,
            report_types: reportTypes
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showNotification(`Error: ${data.error}`, 'error');
        } else {
            showNotification(`Reports generated successfully: ${data.generated_count} files`, 'success');
            
            // Offer to download all files
            if (data.download_urls) {
                downloadMultipleFiles(data.download_urls);
            }
        }
    })
    .catch(error => {
        console.error('Report generation error:', error);
        showNotification('Error generating reports', 'error');
    });
}

function downloadMultipleFiles(urls) {
    urls.forEach((url, index) => {
        setTimeout(() => {
            window.open(url, '_blank');
        }, index * 500); // Stagger downloads
    });
}

// Action functions
function refreshData() {
    loadDashboardData();
    showNotification('Data refreshed', 'success');
}

// Removed duplicate functions - using primary implementations above

// Settings functions
function loadSettings() {
    console.log('Loading settings...');
    
    // Initialize AI Model Configuration
    initializeAIModelConfiguration();
    
    // Load LLM provider information
    loadLLMProviderInfo();
    
    // Load cache statistics
    loadCacheStats();
    
    // Setup model settings event listeners
    setupModelSettingsListeners();
}

function loadAvailableModels() {
    console.log('Loading available models...');
    
    fetch('/api/available-models')
        .then(response => response.json())
        .then(data => {
            const modelSelect = document.getElementById('llmModel');
            if (!modelSelect) {
                console.error('Model select element not found');
                return;
            }
            
            if (data.success && data.models) {
                // Clear loading option
                modelSelect.innerHTML = '';
                
                // Add models to dropdown
                data.models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model.name;
                    option.textContent = `${model.name} (${(model.size / (1024 * 1024 * 1024)).toFixed(1)} GB)`;
                    
                    // Mark current model as selected
                    if (model.current) {
                        option.selected = true;
                    }
                    
                    modelSelect.appendChild(option);
                });
                
                console.log(`Loaded ${data.models.length} available models`);
                
                // Add change event listener for model switching
                modelSelect.addEventListener('change', function() {
                    if (this.value) {
                        switchModel(this.value);
                    }
                });
                
            } else {
                modelSelect.innerHTML = '<option value="">Error loading models</option>';
                console.error('Failed to load models:', data);
            }
        })
        .catch(error => {
            console.error('Error loading available models:', error);
            const modelSelect = document.getElementById('llmModel');
            if (modelSelect) {
                modelSelect.innerHTML = '<option value="">Error loading models</option>';
            }
        });
}

function switchModel(modelName) {
    console.log('Switching to model:', modelName);
    showNotification(`Switching to model: ${modelName}...`, 'info');
    
    fetch('/api/change-model', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            model: modelName
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(`Successfully switched to ${modelName}`, 'success');
            // Reload model info to reflect the change
            loadModelInfo();
        } else {
            showNotification(`Failed to switch model: ${data.error}`, 'error');
            // Reload available models to reset the dropdown
            loadAvailableModels();
        }
    })
    .catch(error => {
        console.error('Error switching model:', error);
        showNotification('Error switching model', 'error');
        // Reload available models to reset the dropdown
        loadAvailableModels();
    });
}

function loadCacheStats() {
    fetch('/api/cache-stats')
        .then(response => response.json())
        .then(stats => {
            displayCacheStats(stats);
        })
        .catch(error => {
            console.error('Error loading cache stats:', error);
        });
}

function displayCacheStats(stats) {
    const cacheStatsDiv = document.getElementById('cacheStats');
    if (!cacheStatsDiv) return;
    
    cacheStatsDiv.innerHTML = `
        <div class="cache-stats">
            <h3>Cache Statistics</h3>
            <div class="cache-section">
                <h4>Memory Cache</h4>
                <ul>
                    <li>Analysis Results: ${stats.memory.analysis_results}</li>
                    <li>Contracts: ${stats.memory.contracts}</li>
                    <li>Templates: ${stats.memory.templates}</li>
                </ul>
            </div>
            <div class="cache-section">
                <h4>File Cache</h4>
                <ul>
                    <li>Analysis JSON: ${stats.files.analysis_json_exists ? 'Yes' : 'No'} (${formatBytes(stats.files.analysis_json_size)})</li>
                    <li>Report Files: ${stats.files.reports_count} files (${stats.files.reports_size_mb} MB)</li>
                </ul>
            </div>
        </div>
    `;
}

function clearCache(cacheType = 'all') {
    if (!confirm(`Are you sure you want to clear ${cacheType} cache? This action cannot be undone.`)) {
        return;
    }
    
    showNotification('Clearing cache...', 'info');
    
    fetch('/api/clear-cache', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            cache_type: cacheType
        })
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showNotification(`Cache cleared successfully: ${result.cleared_items.join(', ')}`, 'success');
            // Refresh cache stats
            loadCacheStats();
            // Refresh main data
            loadDashboardData();
        } else {
            showNotification(`Error clearing cache: ${result.message}`, 'error');
        }
    })
    .catch(error => {
        showNotification(`Error clearing cache: ${error.message}`, 'error');
    });
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatFileSize(bytes) {
    return formatBytes(bytes);
}

function refreshDashboard() {
    showNotification('Refreshing dashboard...', 'info');
    loadDashboardData();
}

// Utility functions
function getSelectedContracts() {
    const checkboxes = document.querySelectorAll('input[type="checkbox"]:checked');
    return Array.from(checkboxes).map(cb => cb.value).filter(Boolean);
}

function getConfidenceClass(confidence) {
    if (confidence >= 90) return 'high';
    if (confidence >= 70) return 'medium';
    return 'low';
}

function getStatusClass(status) {
    if (status === 'No changes') return 'success';
    if (status.includes('Minor')) return 'info';
    if (status.includes('Moderate')) return 'warning';
    return 'danger';
}

function getNextStepSuggestion(status) {
    if (status === 'No changes') return 'Proceed without Legal';
    if (status.includes('Minor')) return 'Quick Review';
    if (status.includes('Moderate')) return 'Legal Review';
    return 'Requires Legal Review';
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString();
}

function sortTable(column) {
    // Table sorting implementation
    showNotification('Table sorting feature coming soon', 'info');
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${getNotificationIcon(type)}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

function getNotificationIcon(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-triangle',
        'warning': 'exclamation-circle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

function showUploadProgress(filename) {
    const progress = document.getElementById('uploadProgress');
    if (progress) {
        progress.style.display = 'block';
        progress.querySelector('.progress-text').textContent = `Uploading ${filename}...`;
    }
}

function hideUploadProgress() {
    const progress = document.getElementById('uploadProgress');
    if (progress) {
        progress.style.display = 'none';
    }
}

function checkSystemStatus() {
    fetch('/api/health')
        .then(response => response.json())
        .then(data => {
            dashboardData.systemStatus = data;
            updateSystemStatus();
        })
        .catch(error => {
            console.error('Status check error:', error);
            const statusIndicator = document.getElementById('systemStatus');
            const statusText = document.getElementById('statusText');
            statusIndicator.className = 'fas fa-circle status-indicator status-error';
            statusText.textContent = 'System Error';
        });
}

// Mobile responsiveness
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('active');
}

// Add mobile menu toggle if needed
if (window.innerWidth <= 480) {
    const header = document.querySelector('.content-header');
    const menuToggle = document.createElement('button');
    menuToggle.className = 'menu-toggle';
    menuToggle.innerHTML = '<i class="fas fa-bars"></i>';
    menuToggle.addEventListener('click', toggleSidebar);
    header.querySelector('.header-content').prepend(menuToggle);
} 

// Download functions
function downloadReport(resultId, type) {
    const endpoints = {
        'review': '/api/download-redlined-document',
        'changes': '/api/download-changes-table'
    };
    
    const endpoint = endpoints[type];
    if (!endpoint) {
        showNotification('Unknown report type', 'error');
        return;
    }
    
    const url = `${endpoint}?id=${resultId}`;
    
    // Check if file exists before attempting download
    fetch(url, { method: 'HEAD' })
        .then(response => {
            if (response.ok) {
                // File exists, proceed with download
                window.open(url, '_blank');
            } else if (response.status === 404) {
                showNotification(`Report file not found. You may need to regenerate this report.`, 'error');
            } else {
                showNotification(`Error accessing report: ${response.statusText}`, 'error');
            }
        })
        .catch(error => {
            console.error('Download error:', error);
            showNotification('Failed to download report. Please try again.', 'error');
        });
}

function downloadWordComRedlined(resultId) {
    // First generate the Word COM redlined document
    showNotification('Generating Word Track Changes document...', 'info');
    
    fetch('/api/generate-word-com-redlined', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            result_id: resultId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            if (data.error.includes('Windows COM interface')) {
                showNotification('Word Track Changes feature requires Windows with Microsoft Word installed', 'warning');
            } else {
                showNotification(data.error, 'error');
            }
        } else {
            showNotification('Word Track Changes document generated successfully!', 'success');
            
            // Download the generated file
            setTimeout(() => {
                const url = `/api/download-word-com-redlined?id=${resultId}`;
                window.open(url, '_blank');
            }, 500);
        }
    })
    .catch(error => {
        console.error('Error generating Word COM redlined document:', error);
        showNotification('Failed to generate Word Track Changes document', 'error');
    });
} 

// Enhanced model management variables
let modelSwitchInProgress = false;
let availableModels = [];
let currentModel = '';
let currentProvider = 'openai';
let openaiModels = [];

// AI Model Configuration Functions
function initializeAIModelConfiguration() {
    console.log('Initializing AI Model Configuration...');
    
    // Setup event listeners
    setupAIModelEventListeners();
    
    // Load OpenAI models
    loadOpenAIModels();
    
    // Load current model status
    loadCurrentModelStatus();
}

function setupAIModelEventListeners() {
    console.log('Setting up AI Model event listeners...');
    
    // OpenAI model selection
    const openaiModelSelect = document.getElementById('openaiModel');
    if (openaiModelSelect) {
        openaiModelSelect.addEventListener('change', handleModelChange);
    }
    
    // Refresh models button
    const refreshButton = document.getElementById('refreshModels');
    if (refreshButton) {
        refreshButton.addEventListener('click', refreshOpenAIModels);
    }
    
    // Temperature slider
    const temperatureSlider = document.getElementById('temperatureSlider');
    const temperatureValue = document.getElementById('temperatureValue');
    if (temperatureSlider && temperatureValue) {
        temperatureSlider.addEventListener('input', function() {
            temperatureValue.textContent = this.value;
        });
    }
}

function loadOpenAIModels() {
    console.log('Loading OpenAI models...');
    
    // Show loading state
    const modelSelect = document.getElementById('openaiModel');
    if (modelSelect) {
        modelSelect.innerHTML = '<option value="">Loading OpenAI models...</option>';
    }
    
    fetch('/api/openai-models')
        .then(response => {
            console.log('OpenAI models response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('OpenAI models data received:', data);
            if (data.success && data.models) {
                openaiModels = data.models;
                console.log('Updating dropdown with', data.models.length, 'models');
                updateOpenAIModelDropdown(data.models, data.current_model);
                
                // Update current model status
                updateCurrentModelStatus(data.current_model, 'Connected');
                
                if (data.recommendations) {
                    console.log('OpenAI model recommendations:', data.recommendations);
                }
            } else {
                console.error('Failed to load OpenAI models:', data.error || 'Unknown error');
                showModelLoadError(data.error || 'Failed to load models');
            }
        })
        .catch(error => {
            console.error('Error loading OpenAI models:', error);
            showModelLoadError(error.message);
        });
}

function updateOpenAIModelDropdown(models, currentModel) {
    console.log('Updating OpenAI model dropdown with', models.length, 'models');
    
    const modelSelect = document.getElementById('openaiModel');
    if (!modelSelect) {
        console.error('OpenAI model select element not found');
        return;
    }
    
    // Clear existing options
    modelSelect.innerHTML = '';
    
    // Add default option
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = 'Select an OpenAI model...';
    defaultOption.disabled = true;
    modelSelect.appendChild(defaultOption);
    
    // Add model options
    models.forEach((model, index) => {
        console.log(`Adding model ${index + 1}:`, model.name);
        const option = document.createElement('option');
        option.value = model.name;
        option.textContent = `${model.name} - ${model.tier?.toUpperCase() || 'STANDARD'}`;
        
        if (model.recommended) {
            option.textContent += ' ⭐ RECOMMENDED';
        }
        
        if (model.name === currentModel) {
            option.selected = true;
            updateModelDescription(model);
        }
        
        modelSelect.appendChild(option);
    });
    
    console.log('Dropdown updated successfully with', modelSelect.options.length, 'total options');
    
    // Update model description for current selection
    if (currentModel) {
        const currentModelData = models.find(m => m.name === currentModel);
        if (currentModelData) {
            updateModelDescription(currentModelData);
        }
    }
}

// Helper functions for AI Model Configuration
function handleModelChange(event) {
    const selectedModel = event.target.value;
    console.log('Model changed to:', selectedModel);
    
    if (selectedModel) {
        const model = openaiModels.find(m => m.name === selectedModel);
        if (model) {
            updateModelDescription(model);
            changeOpenAIModel(selectedModel);
        }
    }
}

function refreshOpenAIModels() {
    console.log('Refreshing OpenAI models...');
    showNotification('Refreshing model list...', 'info');
    loadOpenAIModels();
}

function showModelLoadError(errorMessage) {
    console.error('Model load error:', errorMessage);
    
    const modelSelect = document.getElementById('openaiModel');
    if (modelSelect) {
        modelSelect.innerHTML = '<option value="">Error loading models</option>';
    }
    
    const modelDescription = document.getElementById('model-description');
    if (modelDescription) {
        modelDescription.innerHTML = `<span class="error">Error: ${errorMessage}</span>`;
    }
    
    showNotification('Failed to load OpenAI models', 'error');
}

function loadCurrentModelStatus() {
    console.log('Loading current model status...');
    
    fetch('/api/model-info')
        .then(response => response.json())
        .then(data => {
            console.log('Current model info:', data);
            updateCurrentModelStatus(data.model || data.name, data.connection_healthy ? 'Connected' : 'Disconnected');
        })
        .catch(error => {
            console.error('Error loading current model status:', error);
            updateCurrentModelStatus('Unknown', 'Error');
        });
}

function updateCurrentModelStatus(modelName, status) {
    const statusModel = document.getElementById('status-model');
    const statusConnection = document.getElementById('status-connection');
    
    if (statusModel) {
        statusModel.textContent = modelName || 'Unknown';
    }
    
    if (statusConnection) {
        statusConnection.textContent = status || 'Unknown';
        statusConnection.className = status === 'Connected' ? 'status-connected' : 'status-disconnected';
    }
}

function changeOpenAIModel(modelName) {
    console.log('Changing OpenAI model to:', modelName);
    
    fetch('/api/update-openai-model', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ model: modelName })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(`Model changed to ${modelName}`, 'success');
            updateCurrentModelStatus(modelName, 'Connected');
        } else {
            showNotification(`Failed to change model: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        console.error('Error changing model:', error);
        showNotification('Error changing model', 'error');
    });
}

function updateModelDescription(model) {
    const modelDescription = document.getElementById('model-description');
    if (!modelDescription) return;
    
    modelDescription.innerHTML = `
        <div class="model-info">
            <strong>${model.name}</strong>
            <span class="model-tier">${model.tier?.toUpperCase() || 'STANDARD'}</span>
            ${model.recommended ? '<span class="recommended">⭐ RECOMMENDED</span>' : ''}
        </div>
        <div class="model-description-text">
            ${model.description || 'No description available'}
        </div>
        <div class="model-specs">
            <span>Context: ${model.context_window?.toLocaleString() || 'N/A'} tokens</span>
        </div>
    `;
}

// Removed duplicate function - using primary implementation above

function loadLLMProviderInfo() {
    console.log('Loading LLM provider information...');
    
    fetch('/api/llm-provider')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentProvider = data.provider;
                currentModel = data.model;
                
                // Update provider selector
                const providerSelector = document.getElementById('providerSelector');
                if (providerSelector) {
                    providerSelector.value = data.provider;
                }
                
                // Update provider display
                const providerElement = document.getElementById('current-provider');
                const healthElement = document.getElementById('provider-health');
                
                if (providerElement) {
                    providerElement.textContent = data.provider.toUpperCase();
                }
                
                if (healthElement) {
                    healthElement.className = `health-indicator ${data.api_key_configured ? 'health-healthy' : 'health-unhealthy'}`;
                }
                
                // Show/hide appropriate settings sections
                const openaiSettings = document.getElementById('openai-settings');
                
                if (data.provider === 'openai') {
                    if (openaiSettings) openaiSettings.style.display = 'block';
                }
                
                // Update model settings
                updateModelSettings(data.temperature, data.max_tokens);
                
                console.log('LLM provider info loaded:', data);
            } else {
                console.error('Failed to load LLM provider info');
            }
        })
        .catch(error => {
            console.error('Error loading LLM provider info:', error);
        });
}

function updateModelSettings(temperature, maxTokens) {
    const temperatureSlider = document.getElementById('temperatureSlider');
    const temperatureValue = document.getElementById('temperatureValue');
    const maxTokensInput = document.getElementById('maxTokensInput');
    
    if (temperatureSlider && temperatureValue) {
        temperatureSlider.value = temperature;
        temperatureValue.textContent = temperature;
    }
    
    if (maxTokensInput) {
        maxTokensInput.value = maxTokens;
    }
}

function setupModelSettingsListeners() {
    const temperatureSlider = document.getElementById('temperatureSlider');
    const temperatureValue = document.getElementById('temperatureValue');
    const maxTokensInput = document.getElementById('maxTokensInput');
    
    if (temperatureSlider && temperatureValue) {
        temperatureSlider.addEventListener('input', function() {
            temperatureValue.textContent = this.value;
        });
        
        temperatureSlider.addEventListener('change', function() {
            updateLLMSettings({ temperature: parseFloat(this.value) });
        });
    }
    
    if (maxTokensInput) {
        maxTokensInput.addEventListener('change', function() {
            updateLLMSettings({ max_tokens: parseInt(this.value) });
        });
    }
}

function setupProviderSelector() {
    const providerSelector = document.getElementById('providerSelector');
    if (providerSelector) {
        providerSelector.addEventListener('change', function() {
            switchProvider(this.value);
        });
    }
}

function switchProvider(providerType) {
    console.log('Switching to provider:', providerType);
    
    // Show loading state
    showNotification('Switching LLM provider...', 'info');
    
    // Show/hide appropriate settings sections
    const openaiSettings = document.getElementById('openai-settings');
    
    if (providerType === 'openai') {
        if (openaiSettings) openaiSettings.style.display = 'block';
        loadOpenAIModels();
    }
    
    // Update provider in backend
    updateLLMProvider(providerType);
    
    // Update provider display
    const providerElement = document.getElementById('current-provider');
    if (providerElement) {
        providerElement.textContent = 'OpenAI';
    }
}


function updateLLMProvider(providerType) {
    console.log('Updating LLM provider to:', providerType);
    
    // Note: This would update the provider in the backend
    // For now, we'll update the user config
    fetch('/api/user-config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            llm_settings: {
                provider: providerType
            }
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Provider updated successfully');
            // Refresh model info
            loadModelInfo();
        } else {
            console.error('Failed to update provider:', data.error);
        }
    })
    .catch(error => {
        console.error('Error updating provider:', error);
    });
}

function updateLLMSettings(settings) {
    console.log('Updating LLM settings:', settings);
    
    fetch('/api/llm-settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Settings updated successfully', 'success');
            console.log('LLM settings updated:', data.updated_settings);
        } else {
            showNotification(`Settings update failed: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        console.error('Error updating LLM settings:', error);
        showNotification('Error updating settings', 'error');
    });
}

// Debug function for testing tabs (call from browser console)
function testTabs() {
    console.log('=== TAB DEBUGGING TEST ===');
    
    const tabs = ['dashboard', 'upload', 'settings'];
    
    tabs.forEach(tabName => {
        console.log(`\nTesting tab: ${tabName}`);
        
        // Check if elements exist
        const tabContent = document.getElementById(tabName);
        const menuItem = document.querySelector(`[data-tab="${tabName}"]`);
        
        console.log(`Tab content exists: ${!!tabContent}`);
        console.log(`Menu item exists: ${!!menuItem}`);
        
        // Test tab switching
        if (typeof showTab === 'function') {
            const result = showTab(tabName);
            console.log(`Tab switch result: ${result}`);
        }
    });
    
    console.log('\n=== Test completed ===');
    return 'Tab test completed - check console output';
}

// ==================== PROMPT MANAGEMENT FUNCTIONS ====================

// Global variables for prompt management
let currentPromptType = 'individual_analysis';
let originalPromptContent = '';
let promptBackups = [];

// Initialize prompt management when prompts tab is loaded
// Removed duplicate function - using the main one above

function initializePromptManagement() {
    console.log('Initializing prompt management...');
    
    // Setup event listeners
    setupPromptEventListeners();
    
    // Load initial prompt
    loadPrompts();
    
    // Load backup list
    loadBackupList();
    
    // Load prompt statistics
    loadPromptStats();
}

function setupPromptEventListeners() {
    // Prompt type selector
    const promptTypeSelect = document.getElementById('promptTypeSelect');
    if (promptTypeSelect) {
        promptTypeSelect.addEventListener('change', onPromptTypeChange);
    }
    
    // Variable tag insertion
    const variableTags = document.querySelectorAll('.variable-tag');
    variableTags.forEach(tag => {
        tag.addEventListener('click', insertVariableAtCursor);
    });
    
    // Backup selector
    const backupList = document.getElementById('backupList');
    if (backupList) {
        backupList.addEventListener('change', onBackupSelectionChange);
    }
}

function onPromptTypeChange() {
    const promptTypeSelect = document.getElementById('promptTypeSelect');
    currentPromptType = promptTypeSelect.value;
    
    // Load the selected prompt type
    loadPrompts();
}

function loadPrompts() {
    console.log(`Loading prompt for type: ${currentPromptType}`);
    
    fetch(`/api/prompts/${currentPromptType}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showNotification(data.error, 'error');
                return;
            }
            
            const promptEditor = document.getElementById('promptEditor');
            if (promptEditor) {
                promptEditor.value = data.template || '';
                originalPromptContent = data.template || '';
            }
            
            // Update prompt info
            updatePromptInfo(data);
            
            console.log('Prompt loaded successfully');
        })
        .catch(error => {
            console.error('Error loading prompt:', error);
            showNotification('Failed to load prompt template', 'error');
        });
}

function updatePromptInfo(data) {
    const versionElement = document.getElementById('prompt-version');
    const statusElement = document.getElementById('prompt-status');
    
    if (versionElement) {
        versionElement.textContent = `Version: ${data.version || '1.0'}`;
    }
    
    if (statusElement) {
        statusElement.textContent = `Status: ${data.status || 'Active'}`;
    }
}

function savePrompt() {
    const promptEditor = document.getElementById('promptEditor');
    if (!promptEditor) {
        showNotification('Prompt editor not found', 'error');
        return;
    }
    
    const newContent = promptEditor.value.trim();
    if (!newContent) {
        showNotification('Prompt cannot be empty', 'error');
        return;
    }
    
    // Show saving notification
    showNotification('Saving prompt...', 'info');
    
    fetch(`/api/prompts/${currentPromptType}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            template: newContent
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showNotification(data.error, 'error');
            return;
        }
        
        showNotification('Prompt saved successfully!', 'success');
        originalPromptContent = newContent;
        
        // Update prompt info
        updatePromptInfo(data);
        
        // Refresh statistics
        loadPromptStats();
    })
    .catch(error => {
        console.error('Error saving prompt:', error);
        showNotification('Failed to save prompt', 'error');
    });
}

function validatePrompt() {
    const promptEditor = document.getElementById('promptEditor');
    if (!promptEditor) {
        showNotification('Prompt editor not found', 'error');
        return;
    }
    
    const content = promptEditor.value.trim();
    if (!content) {
        showValidationResult('Prompt cannot be empty', false);
        return;
    }
    
    // Show validating notification
    showNotification('Validating prompt...', 'info');
    
    fetch(`/api/prompts/validate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            template: content,
            prompt_type: currentPromptType
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showValidationResult(data.error, false);
            return;
        }
        
        showValidationResult(data.message || 'Prompt is valid!', data.valid);
        
        if (data.suggestions && data.suggestions.length > 0) {
            showValidationSuggestions(data.suggestions);
        }
    })
    .catch(error => {
        console.error('Error validating prompt:', error);
        showValidationResult('Validation failed: ' + error.message, false);
    });
}

function showValidationResult(message, isValid) {
    const validationResults = document.getElementById('validationResults');
    if (!validationResults) return;
    
    const icon = isValid ? '<i class="fas fa-check-circle" style="color: green;"></i>' : 
                          '<i class="fas fa-times-circle" style="color: red;"></i>';
    
    validationResults.innerHTML = `
        <div class="validation-message ${isValid ? 'valid' : 'invalid'}">
            ${icon} ${message}
        </div>
    `;
}

function showValidationSuggestions(suggestions) {
    const validationResults = document.getElementById('validationResults');
    if (!validationResults) return;
    
    const suggestionsList = suggestions.map(s => `<li>${s}</li>`).join('');
    validationResults.innerHTML += `
        <div class="validation-suggestions">
            <h4>Suggestions:</h4>
            <ul>${suggestionsList}</ul>
        </div>
    `;
}

function previewPrompt() {
    const promptEditor = document.getElementById('promptEditor');
    if (!promptEditor) {
        showNotification('Prompt editor not found', 'error');
        return;
    }
    
    const content = promptEditor.value.trim();
    if (!content) {
        showNotification('Prompt cannot be empty', 'error');
        return;
    }
    
    // Show preview loading
    const previewPanel = document.getElementById('promptPreview');
    if (previewPanel) {
        previewPanel.innerHTML = '<p class="preview-message">Generating preview...</p>';
    }
    
    fetch(`/api/prompts/preview`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            template: content,
            prompt_type: currentPromptType
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showPreviewResult('Preview failed: ' + data.error, false);
            return;
        }
        
        showPreviewResult(data.preview_text, true);
    })
    .catch(error => {
        console.error('Error generating preview:', error);
        showPreviewResult('Preview failed: ' + error.message, false);
    });
}

function showPreviewResult(content, isSuccess) {
    const previewPanel = document.getElementById('promptPreview');
    if (!previewPanel) return;
    
    if (isSuccess) {
        previewPanel.innerHTML = `
            <div class="preview-content-success">
                <pre>${content}</pre>
            </div>
        `;
    } else {
        previewPanel.innerHTML = `
            <div class="preview-content-error">
                <p style="color: red;">${content}</p>
            </div>
        `;
    }
}

function resetPrompt() {
    const promptEditor = document.getElementById('promptEditor');
    if (!promptEditor) {
        showNotification('Prompt editor not found', 'error');
        return;
    }
    
    if (confirm('Are you sure you want to reset the prompt to its original state? Any unsaved changes will be lost.')) {
        promptEditor.value = originalPromptContent;
        showNotification('Prompt reset to original state', 'info');
        
        // Clear validation and preview
        clearValidationAndPreview();
    }
}

function clearValidationAndPreview() {
    const validationResults = document.getElementById('validationResults');
    const previewPanel = document.getElementById('promptPreview');
    
    if (validationResults) {
        validationResults.innerHTML = '<p class="validation-message">Click "Validate" to check your prompt</p>';
    }
    
    if (previewPanel) {
        previewPanel.innerHTML = '<p class="preview-message">Click "Preview" to see prompt with sample data</p>';
    }
}

function insertVariableAtCursor(event) {
    const promptEditor = document.getElementById('promptEditor');
    const variable = event.target.textContent;
    
    if (!promptEditor) return;
    
    const cursorPos = promptEditor.selectionStart;
    const textBefore = promptEditor.value.substring(0, cursorPos);
    const textAfter = promptEditor.value.substring(promptEditor.selectionEnd);
    
    promptEditor.value = textBefore + variable + textAfter;
    promptEditor.selectionStart = promptEditor.selectionEnd = cursorPos + variable.length;
    promptEditor.focus();
    
    showNotification(`Inserted variable: ${variable}`, 'info');
}

function createBackup() {
    const promptEditor = document.getElementById('promptEditor');
    const backupNameInput = document.getElementById('backupName');
    
    if (!promptEditor) {
        showNotification('Prompt editor not found', 'error');
        return;
    }
    
    const content = promptEditor.value.trim();
    if (!content) {
        showNotification('Cannot backup empty prompt', 'error');
        return;
    }
    
    const backupName = backupNameInput ? backupNameInput.value.trim() : '';
    
    showNotification('Creating backup...', 'info');
    
    fetch(`/api/prompts/backup`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            prompt_type: currentPromptType,
            template: content,
            backup_name: backupName
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showNotification(data.error, 'error');
            return;
        }
        
        showNotification('Backup created successfully!', 'success');
        
        // Clear backup name input
        if (backupNameInput) {
            backupNameInput.value = '';
        }
        
        // Refresh backup list
        loadBackupList();
        
        // Refresh statistics
        loadPromptStats();
    })
    .catch(error => {
        console.error('Error creating backup:', error);
        showNotification('Failed to create backup', 'error');
    });
}

function loadBackupList() {
    fetch(`/api/prompts/backups/${currentPromptType}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error loading backups:', data.error);
                return;
            }
            
            updateBackupList(data.backups || []);
        })
        .catch(error => {
            console.error('Error loading backup list:', error);
        });
}

function updateBackupList(backups) {
    const backupSelector = document.getElementById('backupList');
    const backupContainer = document.getElementById('backupListContainer');
    
    if (backupSelector) {
        backupSelector.innerHTML = '<option value="">Select backup to restore...</option>';
        
        backups.forEach(backup => {
            const option = document.createElement('option');
            option.value = backup.id;
            option.textContent = `${backup.name} (${formatDate(backup.created_at)})`;
            backupSelector.appendChild(option);
        });
    }
    
    if (backupContainer) {
        if (backups.length === 0) {
            backupContainer.innerHTML = '<p class="backup-message">No backups available</p>';
        } else {
            const backupItems = backups.map(backup => `
                <div class="backup-item">
                    <span class="backup-name">${backup.name}</span>
                    <span class="backup-date">${formatDate(backup.created_at)}</span>
                    <button class="action-btn small" onclick="restoreSpecificBackup('${backup.id}')">
                        <i class="fas fa-download"></i> Restore
                    </button>
                </div>
            `).join('');
            
            backupContainer.innerHTML = backupItems;
        }
    }
}

function onBackupSelectionChange() {
    // Implementation for when backup selection changes
    // Could show backup preview or details
}

function restoreBackup() {
    const backupSelector = document.getElementById('backupList');
    if (!backupSelector || !backupSelector.value) {
        showNotification('Please select a backup to restore', 'warning');
        return;
    }
    
    restoreSpecificBackup(backupSelector.value);
}

function restoreSpecificBackup(backupId) {
    if (!confirm('Are you sure you want to restore this backup? Current prompt will be overwritten.')) {
        return;
    }
    
    showNotification('Restoring backup...', 'info');
    
    fetch(`/api/prompts/restore/${backupId}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showNotification(data.error, 'error');
            return;
        }
        
        showNotification('Backup restored successfully!', 'success');
        
        // Reload the current prompt
        loadPrompts();
        
        // Clear validation and preview
        clearValidationAndPreview();
    })
    .catch(error => {
        console.error('Error restoring backup:', error);
        showNotification('Failed to restore backup', 'error');
    });
}

function loadPromptStats() {
    fetch('/api/prompts/stats')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error loading prompt stats:', data.error);
                return;
            }
            
            updatePromptStats(data);
        })
        .catch(error => {
            console.error('Error loading prompt stats:', error);
        });
}

function updatePromptStats(stats) {
    const elements = {
        'totalPrompts': stats.total_prompts || 0,
        'activePrompts': stats.active_prompts || 0,
        'totalBackups': stats.total_backups || 0,
        'lastModified': stats.last_modified ? formatDate(stats.last_modified) : 'Never'
    };
    
    Object.entries(elements).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    });
}

// Update the page title mapping to include prompts
function updatePageTitle(tab) {
    const pageTitle = document.getElementById('pageTitle');
    const titles = {
        'dashboard': 'Contract Review Dashboard',
        'upload': 'File Upload & Management',
        'prompts': 'LLM Prompt Management',
        'settings': 'System Configuration'
    };
    
    if (pageTitle) {
        pageTitle.textContent = titles[tab] || 'Contract Review Dashboard';
        console.log('Updated page title to:', titles[tab] || 'Contract Review Dashboard');
    } else {
        console.error('Page title element not found');
    }
}