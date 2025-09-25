/**
 * Dashboard Module
 * 
 * Handles the main dashboard functionality including metrics display, analysis table,
 * system status, and data visualization. This is the primary interface users see.
 */

class DashboardModule {
    constructor() {
        this.name = 'dashboard';
        this.initialized = false;
        this.refreshInterval = null;
        this.refreshIntervalMs = 30000; // 30 seconds
        this.currentData = null;
    }

    /**
     * Initialize the dashboard module
     */
    async init() {
        console.log('Dashboard: Initializing dashboard...');
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Initialize data
        await this.loadDashboardData();
        
        this.initialized = true;
        console.log('Dashboard: Dashboard initialized successfully');
    }

    /**
     * Handle module events
     */
    handleEvent(eventName, data) {
        switch (eventName) {
            case 'dataUpdated':
                this.updateDisplay(data);
                break;
            case 'tabChanged':
                if (data.currentTab === 'dashboard') {
                    this.onTabActivated();
                }
                break;
        }
    }

    /**
     * Called when dashboard tab is activated
     */
    onTabActivated() {
        console.log('Dashboard: Tab activated, refreshing data...');
        this.loadDashboardData();
    }

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Refresh button
        const refreshButton = document.getElementById('refreshDashboard');
        if (refreshButton) {
            refreshButton.addEventListener('click', () => {
                this.refreshData();
            });
        }

        // Batch operation buttons
        this.setupBatchOperationListeners();
        
        // Analysis table interactions
        this.setupTableInteractions();
        
        console.log('Dashboard: Event listeners setup complete');
    }

    /**
     * Set up batch operation listeners
     */
    setupBatchOperationListeners() {
        const buttons = {
            'analyzeAllContracts': () => this.analyzeAllContracts(),
            'generateBatchReports': () => this.generateBatchReports(),
            'clearAllContracts': () => this.clearAllContracts(),
            'clearAllFiles': () => this.clearAllFiles()
        };

        Object.entries(buttons).forEach(([id, handler]) => {
            const button = document.getElementById(id);
            if (button) {
                button.addEventListener('click', handler);
            }
        });
    }

    /**
     * Set up table interactions
     */
    setupTableInteractions() {
        // Add sorting functionality to table headers
        const tableHeaders = document.querySelectorAll('.analysis-table th[data-sortable]');
        
        tableHeaders.forEach(header => {
            header.addEventListener('click', () => {
                const column = header.dataset.column;
                if (column) {
                    this.sortTable(column);
                }
            });
            
            // Add visual indicator that column is sortable
            header.style.cursor = 'pointer';
            header.title = `Click to sort by ${header.textContent}`;
        });
    }

    /**
     * Load dashboard data
     */
    async loadDashboardData() {
        console.log('Dashboard: Loading dashboard data...');
        
        const notifications = window.ContractApp?.modules?.notifications;
        const utils = window.ContractApp?.modules?.utils;
        
        if (!utils) {
            console.error('Dashboard: Utils module not available');
            return;
        }

        try {
            // Get data from global state (updated by core module)
            const appData = window.ContractApp?.data;
            if (appData) {
                this.currentData = appData;
                this.updateDisplay(appData);
            } else {
                console.warn('Dashboard: No data available in global state');
            }

        } catch (error) {
            console.error('Dashboard: Error loading dashboard data:', error);
            if (notifications) {
                notifications.error('Failed to load dashboard data');
            }
        }
    }

    /**
     * Update dashboard display with new data
     */
    updateDisplay(data) {
        console.log('Dashboard: Updating display with new data');
        
        try {
            this.updateMetrics(data);
            this.updateAnalysisTable(data);
            this.updateSystemStatus(data);
            
            console.log('Dashboard: Display updated successfully');
            
        } catch (error) {
            console.error('Dashboard: Error updating display:', error);
        }
    }

    /**
     * Update metrics cards
     */
    updateMetrics(data) {
        const utils = window.ContractApp?.modules?.utils;
        
        const metrics = {
            totalContracts: data.contracts?.length || 0,
            totalTemplates: data.templates?.length || 0,
            totalAnalyses: data.analysisResults?.length || 0,
            pendingReviews: this.calculatePendingReviews(data.analysisResults)
        };

        // Update each metric with animation
        Object.entries(metrics).forEach(([key, value]) => {
            const element = document.getElementById(key);
            if (element && utils) {
                const currentValue = parseInt(element.textContent) || 0;
                utils.animateValue(element, currentValue, value, 1000);
            }
        });

        console.log('Dashboard: Metrics updated:', metrics);
    }

    /**
     * Calculate number of pending reviews
     */
    calculatePendingReviews(analysisResults) {
        if (!Array.isArray(analysisResults)) return 0;
        
        return analysisResults.filter(result => {
            return result.status && result.status !== 'No changes' && result.status !== 'Completed';
        }).length;
    }

    /**
     * Update analysis results table
     */
    updateAnalysisTable(data) {
        const tableBody = document.getElementById('analysisTableBody');
        if (!tableBody) {
            console.warn('Dashboard: Analysis table body not found');
            return;
        }

        // Clear existing rows
        tableBody.innerHTML = '';

        if (!data.analysisResults || data.analysisResults.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td colspan="10" class="text-center">
                    <div class="empty-state">
                        <i class="fas fa-search fa-3x text-muted mb-3"></i>
                        <h4>No Analysis Results</h4>
                        <p>Upload contracts and templates to start analysis</p>
                    </div>
                </td>
            `;
            tableBody.appendChild(row);
            return;
        }

        // Add rows for each analysis result
        data.analysisResults.forEach(result => {
            const row = this.createAnalysisTableRow(result);
            tableBody.appendChild(row);
        });

        console.log(`Dashboard: Analysis table updated with ${data.analysisResults.length} results`);
    }

    /**
     * Create analysis table row
     */
    createAnalysisTableRow(result) {
        const utils = window.ContractApp?.modules?.utils;
        
        const row = document.createElement('tr');
        row.className = 'analysis-row';
        row.dataset.id = result.id || result.analysis_id;

        // Build row HTML
        row.innerHTML = `
            <td class="contract-name">${this.sanitizeText(result.contract || result.contract_name || 'Unknown')}</td>
            <td class="template-name">${this.sanitizeText(result.template || result.template_name || 'Unknown')}</td>
            <td class="similarity-score">
                <span class="confidence-badge confidence-${utils ? utils.getConfidenceClass(result.similarity) : 'medium'}">
                    ${result.similarity || 0}%
                </span>
            </td>
            <td class="status">
                <span class="status-badge status-${utils ? utils.getStatusClass(result.status) : 'default'}">
                    ${this.sanitizeText(result.status || 'Unknown')}
                </span>
            </td>
            <td class="reviewer">${this.sanitizeText(result.reviewer || 'System')}</td>
            <td class="date">${utils ? utils.formatDateShort(result.date || result.created_at) : 'N/A'}</td>
            <td class="next-step">${utils ? utils.getNextStepSuggestion(result.status) : 'Review Required'}</td>
            <td class="action-download">
                <button class="download-btn" onclick="window.ContractApp.modules.dashboard.downloadReport('${result.id}', 'review')" 
                        title="Download Redlined Document">
                    <i class="fas fa-file-word"></i>
                </button>
            </td>
            <td class="action-changes">
                <button class="download-btn" onclick="window.ContractApp.modules.dashboard.downloadReport('${result.id}', 'changes')" 
                        title="Download Changes Table">
                    <i class="fas fa-table"></i>
                </button>
            </td>
            <td class="action-track">
                <button class="download-btn" onclick="window.ContractApp.modules.dashboard.downloadWordComRedlined('${result.id}')" 
                        title="Download Word Track Changes">
                    <i class="fas fa-file-word"></i>
                    <span style="font-size: 0.7em; margin-left: 2px;">TC</span>
                </button>
            </td>
        `;

        return row;
    }

    /**
     * Update system status indicator
     */
    updateSystemStatus(data) {
        const statusIndicator = document.getElementById('systemStatus');
        const statusText = document.getElementById('statusText');
        
        if (!statusIndicator || !statusText) {
            console.warn('Dashboard: System status elements not found');
            return;
        }

        const health = data.systemStatus;
        const isHealthy = health && health.status === 'healthy';

        statusIndicator.className = `fas fa-circle status-indicator ${isHealthy ? 'status-healthy' : 'status-degraded'}`;
        statusText.textContent = isHealthy ? 'System Healthy' : 'System Degraded';

        console.log(`Dashboard: System status updated: ${isHealthy ? 'Healthy' : 'Degraded'}`);
    }

    /**
     * Refresh dashboard data manually
     */
    async refreshData() {
        const notifications = window.ContractApp?.modules?.notifications;
        
        if (notifications) {
            notifications.info('Refreshing dashboard...');
        }
        
        // Trigger data refresh from core module
        const core = window.ContractApp?.core;
        if (core) {
            await core.refresh();
        } else {
            await this.loadDashboardData();
        }
        
        console.log('Dashboard: Manual refresh completed');
    }

    /**
     * Batch operations
     */
    async analyzeAllContracts() {
        const notifications = window.ContractApp?.modules?.notifications;
        const utils = window.ContractApp?.modules?.utils;
        
        if (!this.currentData?.contracts?.length) {
            notifications?.warning('No contracts available to analyze');
            return;
        }

        if (!confirm(`Analyze all ${this.currentData.contracts.length} contracts?`)) {
            return;
        }

        console.log('Dashboard: Starting batch analysis...');
        notifications?.info('Starting batch analysis...');

        try {
            const response = await utils?.apiRequest('/api/async/batch-analysis', {
                method: 'POST',
                body: JSON.stringify({
                    contract_ids: this.currentData.contracts.map(c => c.id),
                    template_id: 'auto' // Let system auto-select templates
                })
            });

            if (response?.success) {
                notifications?.success(`Successfully analyzed ${response.results.length} contracts`);
                this.refreshData();
            } else {
                throw new Error(response?.error || 'Batch analysis failed');
            }

        } catch (error) {
            console.error('Dashboard: Batch analysis error:', error);
            notifications?.error(`Batch analysis failed: ${error.message}`);
        }
    }

    async generateBatchReports() {
        const notifications = window.ContractApp?.modules?.notifications;
        
        if (!this.currentData?.analysisResults?.length) {
            notifications?.warning('No analysis results available for report generation');
            return;
        }

        notifications?.info('Generating batch reports...');
        
        // Simulate batch report generation (replace with actual API call)
        setTimeout(() => {
            notifications?.success('Batch reports generated successfully');
        }, 2000);
    }

    async clearAllContracts() {
        const notifications = window.ContractApp?.modules?.notifications;
        const utils = window.ContractApp?.modules?.utils;
        
        const confirmed = confirm('Are you sure you want to clear all contracts? This will remove all uploaded contracts and their analysis results. This action cannot be undone.');
        
        if (!confirmed) return;

        console.log('Dashboard: Clearing all contracts...');
        notifications?.info('Clearing contracts...');

        try {
            const response = await utils?.apiRequest('/api/clear-contracts', {
                method: 'POST'
            });

            if (response?.success) {
                notifications?.success(response.message || 'All contracts cleared successfully');
                this.refreshData();
            } else {
                throw new Error(response?.error || 'Failed to clear contracts');
            }

        } catch (error) {
            console.error('Dashboard: Error clearing contracts:', error);
            notifications?.error(`Failed to clear contracts: ${error.message}`);
        }
    }

    async clearAllFiles() {
        const notifications = window.ContractApp?.modules?.notifications;
        const utils = window.ContractApp?.modules?.utils;
        
        const confirmed = confirm('Are you sure you want to clear all files? This action cannot be undone.');
        
        if (!confirmed) return;

        console.log('Dashboard: Clearing all files...');
        notifications?.info('Clearing all files...');

        try {
            const response = await utils?.apiRequest('/api/clear-files', {
                method: 'POST'
            });

            if (response?.success) {
                notifications?.success('All files cleared successfully');
                this.refreshData();
            } else {
                throw new Error(response?.error || 'Failed to clear files');
            }

        } catch (error) {
            console.error('Dashboard: Error clearing files:', error);
            notifications?.error(`Failed to clear files: ${error.message}`);
        }
    }

    /**
     * Download report
     */
    async downloadReport(resultId, reportType) {
        const notifications = window.ContractApp?.modules?.notifications;
        const utils = window.ContractApp?.modules?.utils;
        
        const reportTypes = {
            'review': {
                endpoint: '/api/download-redlined-document',
                filename: 'review_document.docx'
            },
            'changes': {
                endpoint: '/api/download-changes-table',
                filename: 'changes_table.xlsx'
            }
        };

        const reportConfig = reportTypes[reportType];
        if (!reportConfig) {
            notifications?.error('Invalid report type');
            return;
        }

        console.log(`Dashboard: Generating ${reportType} report for ${resultId}...`);
        notifications?.info('Generating report...');

        try {
            // First, generate the report files
            const generateResponse = await fetch('/api/reports/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    id: resultId,
                    report_type: reportType === 'review' ? 'redlined_document' : 'changes_table'
                })
            });
            
            if (!generateResponse.ok) {
                throw new Error('Report generation failed');
            }
            
            // Now download the generated report
            const url = new URL(reportConfig.endpoint, window.location.origin);
            url.searchParams.set('id', resultId);
            
            const response = await fetch(url, {
                method: 'GET'
            });

            if (!response.ok) {
                throw new Error('Report download failed');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            
            if (utils) {
                utils.downloadFile(url, `${resultId}_${reportConfig.filename}`);
            }
            
            window.URL.revokeObjectURL(url);
            
            notifications?.success('Report downloaded successfully');

        } catch (error) {
            console.error('Dashboard: Download error:', error);
            notifications?.error('Error generating report');
        }
    }

    /**
     * Download Word COM redlined document
     */
    async downloadWordComRedlined(resultId) {
        const notifications = window.ContractApp?.modules?.notifications;
        const utils = window.ContractApp?.modules?.utils;
        
        console.log(`Dashboard: Generating Word Track Changes document for ${resultId}...`);
        notifications?.info('Generating Word Track Changes document...');

        try {
            const response = await utils?.apiRequest('/api/generate-word-com-redlined', {
                method: 'POST',
                body: JSON.stringify({ result_id: resultId })
            });

            if (response?.error) {
                if (response.error.includes('Windows COM interface')) {
                    notifications?.warning('Word Track Changes feature requires Windows with Microsoft Word installed');
                } else {
                    notifications?.error(response.error);
                }
                return;
            }

            notifications?.success('Word Track Changes document generated successfully!');

            // Download the generated file after a brief delay
            setTimeout(() => {
                const downloadUrl = `/api/download-word-com-redlined?id=${resultId}`;
                window.open(downloadUrl, '_blank');
            }, 500);

        } catch (error) {
            console.error('Dashboard: Error generating Word COM redlined document:', error);
            notifications?.error('Failed to generate Word Track Changes document');
        }
    }

    /**
     * Sort table by column
     */
    sortTable(column) {
        const notifications = window.ContractApp?.modules?.notifications;
        
        // TODO: Implement actual table sorting
        console.log(`Dashboard: Sorting table by ${column}`);
        notifications?.info('Table sorting feature coming soon');
    }

    /**
     * Sanitize text for display
     */
    sanitizeText(text) {
        const utils = window.ContractApp?.modules?.utils;
        return utils ? utils.sanitizeHTML(text) : String(text || '');
    }

    /**
     * Get current dashboard data
     */
    getCurrentData() {
        return this.currentData;
    }

    /**
     * Start auto-refresh (called when tab becomes active)
     */
    startAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }

        this.refreshInterval = setInterval(() => {
            if (!document.hidden && window.ContractApp.currentTab === 'dashboard') {
                this.loadDashboardData();
            }
        }, this.refreshIntervalMs);

        console.log('Dashboard: Auto-refresh started');
    }

    /**
     * Stop auto-refresh (called when tab becomes inactive)
     */
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
            console.log('Dashboard: Auto-refresh stopped');
        }
    }
}

// Export for global use
window.DashboardModule = DashboardModule;

// Export functions for global onclick handlers
window.analyzeAllContracts = function() {
    const dashboardModule = window.ContractApp?.modules?.dashboard;
    if (dashboardModule && typeof dashboardModule.analyzeAllContracts === 'function') {
        dashboardModule.analyzeAllContracts();
    } else {
        console.error('Dashboard module or analyzeAllContracts function not available');
    }
};

window.generateBatchReports = function() {
    const dashboardModule = window.ContractApp?.modules?.dashboard;
    if (dashboardModule && typeof dashboardModule.generateBatchReports === 'function') {
        dashboardModule.generateBatchReports();
    } else {
        console.error('Dashboard module or generateBatchReports function not available');
    }
};

window.clearAllContracts = function() {
    const dashboardModule = window.ContractApp?.modules?.dashboard;
    if (dashboardModule && typeof dashboardModule.clearAllContracts === 'function') {
        dashboardModule.clearAllContracts();
    } else {
        console.error('Dashboard module or clearAllContracts function not available');
    }
};