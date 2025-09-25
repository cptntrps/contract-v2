/**
 * Test Configuration for Contract Analyzer E2E Tests
 * 
 * Centralized configuration for test data, endpoints, and test behavior.
 * Supports different environments and testing scenarios.
 */

const path = require('path');

class TestConfig {
    constructor() {
        this.environment = process.env.NODE_ENV || 'development';
        
        this.baseUrls = {
            development: 'http://localhost:5000',
            staging: process.env.STAGING_URL || 'http://staging.contractanalyzer.local',
            production: process.env.PROD_URL || 'https://contractanalyzer.com'
        };
        
        this.apiEndpoints = {
            health: '/api/health',
            contracts: '/api/contracts',
            upload: '/api/contracts/upload',
            templates: '/api/templates',
            analysis: '/api/analysis',
            analyzeContract: '/api/analyze-contract',
            analysisResults: '/api/analysis-results',
            reports: '/api/reports',
            prompts: '/api/prompts',
            settings: '/api/settings'
        };
        
        this.selectors = {
            // Navigation
            sidebar: '.sidebar',
            dashboardTab: '[data-tab="dashboard"]',
            uploadTab: '[data-tab="upload"]',
            promptsTab: '[data-tab="prompts"]',
            settingsTab: '[data-tab="settings"]',
            
            // Dashboard
            dashboardContainer: '#dashboard',
            contractsList: '#contractsList',
            analysisResults: '#analysisTableBody',
            systemStatus: '#systemStatus',
            statusIndicator: '.status-indicator',
            
            // Upload
            uploadContainer: '#upload',
            fileInput: '#contractFileInput',
            uploadButton: '.upload-btn',
            templateSelect: '#templateFileInput',
            uploadProgress: '#uploadProgress',
            uploadStatus: '.progress-text',
            
            // Analysis
            analysisContainer: '.analysis-container',
            analyzeButton: '.analyze-button',
            analysisProgress: '.analysis-progress',
            analysisResults: '.analysis-results-container',
            resultsTable: '.results-table',
            
            // Reports
            reportsSection: '.reports-section',
            generateReportButton: '.generate-report-button',
            reportTypeSelect: '.report-type-select',
            downloadButton: '.download-button',
            
            // Prompts
            promptsContainer: '#prompts-content',
            promptEditor: '.prompt-editor',
            promptSaveButton: '.prompt-save-button',
            promptsList: '.prompts-list',
            promptPreview: '.prompt-preview',
            
            // Settings
            settingsContainer: '#settings-content',
            modelSelect: '#model-select',
            apiKeyInput: '#api-key-input',
            saveSettingsButton: '.save-settings-button',
            
            // Common UI elements
            notifications: '.notification',
            loadingSpinner: '.loading-spinner',
            errorMessage: '.error-message',
            successMessage: '.success-message',
            modal: '.modal',
            confirmButton: '.confirm-button',
            cancelButton: '.cancel-button'
        };
        
        this.testData = {
            files: {
                validContract: path.join(__dirname, '../fixtures/test-contract.docx'),
                invalidFile: path.join(__dirname, '../fixtures/invalid-file.txt'),
                largeContract: path.join(__dirname, '../fixtures/large-contract.docx'),
                corruptedFile: path.join(__dirname, '../fixtures/corrupted.docx')
            },
            
            contracts: {
                sample: {
                    name: 'Sample Service Agreement',
                    type: 'SOW',
                    expectedChanges: 15
                },
                complex: {
                    name: 'Complex Multi-Party Agreement',
                    type: 'CHANGEORDER',
                    expectedChanges: 45
                }
            },
            
            prompts: {
                custom: {
                    name: 'Custom Analysis Prompt',
                    description: 'Custom prompt for specialized analysis',
                    template: 'Analyze the following contract changes: {changes_summary}',
                    variables: ['changes_summary']
                }
            },
            
            settings: {
                models: ['gpt-4o', 'gpt-3.5-turbo'],
                apiKey: process.env.TEST_OPENAI_API_KEY || 'test-api-key'
            }
        };
        
        this.timeouts = {
            navigation: 5000,
            elementVisible: 10000,
            fileUpload: 30000,
            analysis: 120000, // 2 minutes for analysis
            reportGeneration: 60000,
            apiResponse: 30000,
            download: 45000,
            pageLoad: 15000
        };
        
        this.retryConfig = {
            maxRetries: 3,
            retryDelay: 1000, // 1 second
            exponentialBackoff: true
        };
        
        this.performance = {
            thresholds: {
                pageLoadTime: 5000, // 5 seconds
                apiResponseTime: 2000, // 2 seconds
                fileUploadTime: 10000, // 10 seconds per MB
                analysisTime: 60000 // 1 minute base time
            }
        };
        
        this.assertions = {
            contractUpload: {
                successMessage: 'Contract uploaded successfully',
                errorMessage: 'Upload failed'
            },
            analysis: {
                startMessage: 'Analysis started',
                completeMessage: 'Analysis completed',
                errorMessage: 'Analysis failed'
            },
            reports: {
                generatedMessage: 'Report generated successfully',
                downloadStarted: 'Download started'
            }
        };
    }
    
    /**
     * Get base URL for current environment
     */
    getBaseUrl() {
        return this.baseUrls[this.environment];
    }
    
    /**
     * Get full URL for an endpoint
     */
    getUrl(endpoint) {
        const baseUrl = this.getBaseUrl();
        const apiEndpoint = this.apiEndpoints[endpoint] || endpoint;
        return `${baseUrl}${apiEndpoint}`;
    }
    
    /**
     * Get selector by name
     */
    getSelector(name) {
        return this.selectors[name];
    }
    
    /**
     * Get timeout by name
     */
    getTimeout(name) {
        return this.timeouts[name];
    }
    
    /**
     * Get test file path
     */
    getTestFile(fileName) {
        return this.testData.files[fileName];
    }
    
    /**
     * Get test data by category and name
     */
    getTestData(category, name = null) {
        const data = this.testData[category];
        return name ? data[name] : data;
    }
    
    /**
     * Get retry configuration
     */
    getRetryConfig() {
        return this.retryConfig;
    }
    
    /**
     * Get performance thresholds
     */
    getPerformanceThresholds() {
        return this.performance.thresholds;
    }
    
    /**
     * Get assertion messages
     */
    getAssertions(category) {
        return this.assertions[category];
    }
    
    /**
     * Check if running in CI environment
     */
    isCI() {
        return process.env.CI === 'true' || process.env.CONTINUOUS_INTEGRATION === 'true';
    }
    
    /**
     * Check if debug mode is enabled
     */
    isDebugMode() {
        return process.env.DEBUG === 'true' || process.argv.includes('--debug');
    }
    
    /**
     * Get environment-specific configuration
     */
    getEnvironmentConfig() {
        return {
            environment: this.environment,
            baseUrl: this.getBaseUrl(),
            isCI: this.isCI(),
            isDebug: this.isDebugMode(),
            timeouts: this.timeouts,
            retries: this.retryConfig
        };
    }
}

module.exports = new TestConfig();