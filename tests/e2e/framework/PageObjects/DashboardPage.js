/**
 * Dashboard Page Object Model
 * 
 * Represents the main dashboard interface and provides methods
 * for interacting with dashboard elements and functionality.
 */

const testConfig = require('../../config/test.config');

class DashboardPage {
    constructor(page) {
        this.page = page;
        this.config = testConfig;
        
        // Dashboard selectors
        this.selectors = {
            container: this.config.getSelector('dashboardContainer'),
            contractsList: this.config.getSelector('contractsList'),
            analysisResults: this.config.getSelector('analysisResults'),
            systemStatus: this.config.getSelector('systemStatus'),
            statusIndicator: this.config.getSelector('statusIndicator'),
            refreshButton: '[data-action="refresh"]',
            filterInput: '[data-filter="search"]',
            sortDropdown: '[data-sort="dropdown"]',
            
            // Contract list elements
            contractRow: '.contract-row',
            contractName: '.contract-name',
            contractStatus: '.contract-status',
            contractActions: '.contract-actions',
            viewButton: '[data-action="view"]',
            deleteButton: '[data-action="delete"]',
            
            // Analysis results elements
            resultsTable: '.analysis-results-table',
            resultRow: '.result-row',
            resultContract: '.result-contract',
            resultStatus: '.result-status',
            resultScore: '.result-score',
            resultDate: '.result-date',
            resultActions: '.result-actions',
            
            // System status elements
            healthIndicator: '.health-indicator',
            statusText: '.status-text',
            lastUpdate: '.last-update',
            errorCount: '.error-count',
            
            // Navigation elements
            uploadLink: '[data-tab="upload"]',
            promptsLink: '[data-tab="prompts"]',
            settingsLink: '[data-tab="settings"]'
        };
    }
    
    /**
     * Wait for dashboard to load completely
     */
    async waitForLoad() {
        console.log('DashboardPage: Waiting for dashboard to load...');
        
        // Wait for main container
        await this.page.waitForSelector(this.selectors.container, {
            visible: true,
            timeout: this.config.getTimeout('pageLoad')
        });
        
        // Wait for key components to be visible
        await Promise.all([
            this.page.waitForSelector(this.selectors.systemStatus, { visible: true }),
            this.page.waitForSelector(this.selectors.contractsList, { visible: true }),
            this.page.waitForSelector(this.selectors.analysisResults, { visible: true })
        ]);
        
        console.log('DashboardPage: Dashboard loaded successfully');
    }
    
    /**
     * Get system status information
     */
    async getSystemStatus() {
        await this.page.waitForSelector(this.selectors.systemStatus, { visible: true });
        
        const statusElement = await this.page.$(this.selectors.statusIndicator);
        const textElement = await this.page.$(this.selectors.statusText);
        const updateElement = await this.page.$(this.selectors.lastUpdate);
        
        return {
            status: statusElement ? await statusElement.evaluate(el => el.textContent.trim()) : null,
            text: textElement ? await textElement.evaluate(el => el.textContent.trim()) : null,
            lastUpdate: updateElement ? await updateElement.evaluate(el => el.textContent.trim()) : null
        };
    }
    
    /**
     * Get list of contracts
     */
    async getContracts() {
        await this.page.waitForSelector(this.selectors.contractsList, { visible: true });
        
        const contractRows = await this.page.$$(this.selectors.contractRow);
        const contracts = [];
        
        for (const row of contractRows) {
            const nameElement = await row.$(this.selectors.contractName.replace('.', ''));
            const statusElement = await row.$(this.selectors.contractStatus.replace('.', ''));
            
            contracts.push({
                name: nameElement ? await nameElement.evaluate(el => el.textContent.trim()) : 'Unknown',
                status: statusElement ? await statusElement.evaluate(el => el.textContent.trim()) : 'Unknown',
                element: row
            });
        }
        
        return contracts;
    }
    
    /**
     * Get analysis results
     */
    async getAnalysisResults() {
        await this.page.waitForSelector(this.selectors.analysisResults, { visible: true });
        
        // Check if results table exists
        const resultsTable = await this.page.$(this.selectors.resultsTable);
        if (!resultsTable) {
            return [];
        }
        
        const resultRows = await this.page.$$(this.selectors.resultRow);
        const results = [];
        
        for (const row of resultRows) {
            const contractElement = await row.$(this.selectors.resultContract.replace('.', ''));
            const statusElement = await row.$(this.selectors.resultStatus.replace('.', ''));
            const scoreElement = await row.$(this.selectors.resultScore.replace('.', ''));
            const dateElement = await row.$(this.selectors.resultDate.replace('.', ''));
            
            results.push({
                contract: contractElement ? await contractElement.evaluate(el => el.textContent.trim()) : 'Unknown',
                status: statusElement ? await statusElement.evaluate(el => el.textContent.trim()) : 'Unknown',
                score: scoreElement ? await scoreElement.evaluate(el => el.textContent.trim()) : 'N/A',
                date: dateElement ? await dateElement.evaluate(el => el.textContent.trim()) : 'Unknown',
                element: row
            });
        }
        
        return results;
    }
    
    /**
     * Refresh dashboard data
     */
    async refresh() {
        console.log('DashboardPage: Refreshing dashboard data...');
        
        const refreshButton = await this.page.$(this.selectors.refreshButton);
        if (refreshButton) {
            await refreshButton.click();
        } else {
            // Fallback: use keyboard shortcut
            await this.page.keyboard.down('Control');
            await this.page.keyboard.press('KeyR');
            await this.page.keyboard.up('Control');
        }
        
        // Wait for refresh to complete
        await this.page.waitForFunction(
            () => !document.querySelector('.loading-spinner'),
            { timeout: this.config.getTimeout('apiResponse') }
        );
        
        console.log('DashboardPage: Dashboard refreshed');
    }
    
    /**
     * Filter contracts by search term
     */
    async filterContracts(searchTerm) {
        console.log(`DashboardPage: Filtering contracts by: ${searchTerm}`);
        
        const filterInput = await this.page.$(this.selectors.filterInput);
        if (filterInput) {
            await filterInput.click();
            await filterInput.type(searchTerm);
            
            // Wait for filter to apply
            await this.page.waitForTimeout(1000);
        }
    }
    
    /**
     * Sort contracts by criteria
     */
    async sortContracts(criteria) {
        console.log(`DashboardPage: Sorting contracts by: ${criteria}`);
        
        const sortDropdown = await this.page.$(this.selectors.sortDropdown);
        if (sortDropdown) {
            await sortDropdown.click();
            
            const optionSelector = `[data-sort-option="${criteria}"]`;
            await this.page.waitForSelector(optionSelector, { visible: true });
            await this.page.click(optionSelector);
            
            // Wait for sort to apply
            await this.page.waitForTimeout(1000);
        }
    }
    
    /**
     * View contract details
     */
    async viewContract(contractName) {
        console.log(`DashboardPage: Viewing contract: ${contractName}`);
        
        const contracts = await this.getContracts();
        const targetContract = contracts.find(c => c.name.includes(contractName));
        
        if (!targetContract) {
            throw new Error(`Contract not found: ${contractName}`);
        }
        
        const viewButton = await targetContract.element.$(this.selectors.viewButton.replace(/\[|\]/g, ''));
        if (viewButton) {
            await viewButton.click();
            
            // Wait for contract details to load
            await this.page.waitForSelector('.contract-details', {
                visible: true,
                timeout: this.config.getTimeout('elementVisible')
            });
        }
    }
    
    /**
     * Delete contract
     */
    async deleteContract(contractName) {
        console.log(`DashboardPage: Deleting contract: ${contractName}`);
        
        const contracts = await this.getContracts();
        const targetContract = contracts.find(c => c.name.includes(contractName));
        
        if (!targetContract) {
            throw new Error(`Contract not found: ${contractName}`);
        }
        
        const deleteButton = await targetContract.element.$(this.selectors.deleteButton.replace(/\[|\]/g, ''));
        if (deleteButton) {
            await deleteButton.click();
            
            // Handle confirmation dialog
            await this.page.waitForSelector(this.config.getSelector('confirmButton'), {
                visible: true,
                timeout: this.config.getTimeout('elementVisible')
            });
            await this.page.click(this.config.getSelector('confirmButton'));
            
            // Wait for deletion to complete
            await this.page.waitForFunction(
                () => !document.querySelector('.loading-spinner'),
                { timeout: this.config.getTimeout('apiResponse') }
            );
        }
    }
    
    /**
     * Navigate to upload tab
     */
    async navigateToUpload() {
        console.log('DashboardPage: Navigating to upload tab...');
        
        await this.page.click(this.selectors.uploadLink);
        await this.page.waitForSelector(this.config.getSelector('uploadContainer'), {
            visible: true,
            timeout: this.config.getTimeout('navigation')
        });
    }
    
    /**
     * Navigate to prompts tab
     */
    async navigateToPrompts() {
        console.log('DashboardPage: Navigating to prompts tab...');
        
        await this.page.click(this.selectors.promptsLink);
        await this.page.waitForSelector(this.config.getSelector('promptsContainer'), {
            visible: true,
            timeout: this.config.getTimeout('navigation')
        });
    }
    
    /**
     * Navigate to settings tab
     */
    async navigateToSettings() {
        console.log('DashboardPage: Navigating to settings tab...');
        
        await this.page.click(this.selectors.settingsLink);
        await this.page.waitForSelector(this.config.getSelector('settingsContainer'), {
            visible: true,
            timeout: this.config.getTimeout('navigation')
        });
    }
    
    /**
     * Wait for analysis to complete
     */
    async waitForAnalysisComplete(contractName, timeout = null) {
        timeout = timeout || this.config.getTimeout('analysis');
        console.log(`DashboardPage: Waiting for analysis to complete for: ${contractName}`);
        
        const startTime = Date.now();
        
        while (Date.now() - startTime < timeout) {
            const results = await this.getAnalysisResults();
            const contractResult = results.find(r => r.contract.includes(contractName));
            
            if (contractResult && contractResult.status.toLowerCase() === 'completed') {
                console.log(`DashboardPage: Analysis completed for: ${contractName}`);
                return contractResult;
            }
            
            if (contractResult && contractResult.status.toLowerCase() === 'failed') {
                throw new Error(`Analysis failed for: ${contractName}`);
            }
            
            // Wait before checking again
            await this.page.waitForTimeout(2000);
        }
        
        throw new Error(`Analysis timeout for: ${contractName}`);
    }
    
    /**
     * Get dashboard statistics
     */
    async getStatistics() {
        const contracts = await this.getContracts();
        const results = await this.getAnalysisResults();
        const systemStatus = await this.getSystemStatus();
        
        return {
            totalContracts: contracts.length,
            totalResults: results.length,
            completedAnalyses: results.filter(r => r.status.toLowerCase() === 'completed').length,
            failedAnalyses: results.filter(r => r.status.toLowerCase() === 'failed').length,
            pendingAnalyses: results.filter(r => r.status.toLowerCase() === 'pending').length,
            systemStatus: systemStatus.status,
            lastUpdate: systemStatus.lastUpdate
        };
    }
    
    /**
     * Assert dashboard is fully loaded
     */
    async assertDashboardLoaded() {
        await this.waitForLoad();
        
        // Verify key elements are present
        const container = await this.page.$(this.selectors.container);
        const systemStatus = await this.page.$(this.selectors.systemStatus);
        const contractsList = await this.page.$(this.selectors.contractsList);
        
        if (!container || !systemStatus || !contractsList) {
            throw new Error('Dashboard not fully loaded - missing key elements');
        }
        
        console.log('DashboardPage: Dashboard load assertion passed');
    }
    
    /**
     * Assert system is healthy
     */
    async assertSystemHealthy() {
        const status = await this.getSystemStatus();
        
        if (!status.status || status.status.toLowerCase() !== 'healthy') {
            throw new Error(`System not healthy: ${status.status || 'Unknown status'}`);
        }
        
        console.log('DashboardPage: System health assertion passed');
    }
}

module.exports = DashboardPage;