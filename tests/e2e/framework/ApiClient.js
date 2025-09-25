/**
 * API Client for E2E Tests
 * 
 * Provides methods for direct API interaction during E2E tests
 * to set up test data, verify backend state, and perform API-level assertions.
 */

const axios = require('axios');
const fs = require('fs-extra');
const FormData = require('form-data');
const testConfig = require('../config/test.config');

class ApiClient {
    constructor(environment = 'development') {
        this.environment = environment;
        this.config = testConfig;
        this.baseUrl = this.config.getBaseUrl();
        
        // Configure axios instance
        this.client = axios.create({
            baseURL: this.baseUrl,
            timeout: this.config.getTimeout('apiResponse'),
            headers: {
                'Content-Type': 'application/json',
                'User-Agent': 'Contract-Analyzer-E2E-Tests/1.0'
            }
        });
        
        // Set up request/response interceptors for logging
        this.setupInterceptors();
    }
    
    /**
     * Set up axios interceptors for logging and error handling
     */
    setupInterceptors() {
        // Request interceptor
        this.client.interceptors.request.use(
            (config) => {
                if (this.config.isDebugMode()) {
                    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
                }
                return config;
            },
            (error) => {
                console.error('API Request Error:', error);
                return Promise.reject(error);
            }
        );
        
        // Response interceptor
        this.client.interceptors.response.use(
            (response) => {
                if (this.config.isDebugMode()) {
                    console.log(`API Response: ${response.status} ${response.config.method?.toUpperCase()} ${response.config.url}`);
                }
                return response;
            },
            (error) => {
                console.error('API Response Error:', {
                    status: error.response?.status,
                    statusText: error.response?.statusText,
                    url: error.config?.url,
                    method: error.config?.method
                });
                return Promise.reject(error);
            }
        );
    }
    
    /**
     * Check API health status
     */
    async checkHealth() {
        try {
            const response = await this.client.get('/api/health');
            return {
                healthy: response.status === 200,
                data: response.data,
                status: response.status
            };
        } catch (error) {
            return {
                healthy: false,
                error: error.message,
                status: error.response?.status || 0
            };
        }
    }
    
    /**
     * Get all contracts
     */
    async getContracts() {
        try {
            const response = await this.client.get('/api/contracts');
            return {
                success: true,
                contracts: response.data.contracts || [],
                total: response.data.total || 0
            };
        } catch (error) {
            return {
                success: false,
                error: error.message,
                contracts: []
            };
        }
    }
    
    /**
     * Get contract by ID
     */
    async getContract(contractId) {
        try {
            const response = await this.client.get(`/api/contracts/${contractId}`);
            return {
                success: true,
                contract: response.data
            };
        } catch (error) {
            return {
                success: false,
                error: error.message,
                contract: null
            };
        }
    }
    
    /**
     * Upload contract file
     */
    async uploadContract(filePath, templateName = null) {
        try {
            // Check if file exists
            if (!fs.existsSync(filePath)) {
                throw new Error(`File not found: ${filePath}`);
            }
            
            // Create form data
            const formData = new FormData();
            formData.append('contract', fs.createReadStream(filePath));
            
            if (templateName) {
                formData.append('template', templateName);
            }
            
            const response = await this.client.post('/api/contracts/upload', formData, {
                headers: {
                    ...formData.getHeaders(),
                    'Content-Type': 'multipart/form-data'
                },
                timeout: this.config.getTimeout('fileUpload')
            });
            
            return {
                success: true,
                contractId: response.data.contract_id,
                data: response.data
            };
            
        } catch (error) {
            return {
                success: false,
                error: error.message,
                contractId: null
            };
        }
    }
    
    /**
     * Get available templates
     */
    async getTemplates() {
        try {
            const response = await this.client.get('/api/templates');
            return {
                success: true,
                templates: response.data.templates || []
            };
        } catch (error) {
            return {
                success: false,
                error: error.message,
                templates: []
            };
        }
    }
    
    /**
     * Start contract analysis
     */
    async analyzeContract(contractId, options = {}) {
        try {
            const payload = {
                contract_id: contractId,
                ...options
            };
            
            const response = await this.client.post('/api/analyze-contract', payload, {
                timeout: this.config.getTimeout('analysis')
            });
            
            return {
                success: true,
                analysisId: response.data.analysis_id,
                data: response.data
            };
            
        } catch (error) {
            return {
                success: false,
                error: error.message,
                analysisId: null
            };
        }
    }
    
    /**
     * Get analysis results
     */
    async getAnalysisResults(analysisId = null) {
        try {
            const url = analysisId ? `/api/analysis-results/${analysisId}` : '/api/analysis-results';
            const response = await this.client.get(url);
            
            return {
                success: true,
                results: analysisId ? response.data : response.data.results || [],
                data: response.data
            };
            
        } catch (error) {
            return {
                success: false,
                error: error.message,
                results: analysisId ? null : []
            };
        }
    }
    
    /**
     * Wait for analysis to complete
     */
    async waitForAnalysisComplete(analysisId, timeout = null) {
        timeout = timeout || this.config.getTimeout('analysis');
        const startTime = Date.now();
        const checkInterval = 2000; // Check every 2 seconds
        
        console.log(`ApiClient: Waiting for analysis ${analysisId} to complete...`);
        
        while (Date.now() - startTime < timeout) {
            const result = await this.getAnalysisResults(analysisId);
            
            if (result.success && result.results) {
                const status = result.results.status?.toLowerCase();
                
                if (status === 'completed') {
                    console.log(`ApiClient: Analysis ${analysisId} completed successfully`);
                    return result.results;
                }
                
                if (status === 'failed' || status === 'error') {
                    throw new Error(`Analysis ${analysisId} failed: ${result.results.error || 'Unknown error'}`);
                }
                
                console.log(`ApiClient: Analysis ${analysisId} status: ${status}`);
            }
            
            // Wait before checking again
            await new Promise(resolve => setTimeout(resolve, checkInterval));
        }
        
        throw new Error(`Analysis ${analysisId} timeout after ${timeout}ms`);
    }
    
    /**
     * Generate report
     */
    async generateReport(analysisId, reportType = 'excel', options = {}) {
        try {
            const payload = {
                analysis_id: analysisId,
                report_type: reportType,
                ...options
            };
            
            const response = await this.client.post('/api/reports/generate', payload, {
                timeout: this.config.getTimeout('reportGeneration')
            });
            
            return {
                success: true,
                reportId: response.data.report_id,
                downloadUrl: response.data.download_url,
                data: response.data
            };
            
        } catch (error) {
            return {
                success: false,
                error: error.message,
                reportId: null
            };
        }
    }
    
    /**
     * Download report
     */
    async downloadReport(reportId, downloadPath) {
        try {
            const response = await this.client.get(`/api/reports/${reportId}/download`, {
                responseType: 'stream',
                timeout: this.config.getTimeout('download')
            });
            
            // Ensure download directory exists
            await fs.ensureDir(require('path').dirname(downloadPath));
            
            // Write file
            const writer = fs.createWriteStream(downloadPath);
            response.data.pipe(writer);
            
            return new Promise((resolve, reject) => {
                writer.on('finish', () => {
                    resolve({
                        success: true,
                        filePath: downloadPath
                    });
                });
                
                writer.on('error', (error) => {
                    reject({
                        success: false,
                        error: error.message
                    });
                });
            });
            
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    /**
     * Get prompts
     */
    async getPrompts() {
        try {
            const response = await this.client.get('/api/prompts');
            return {
                success: true,
                prompts: response.data.prompts || []
            };
        } catch (error) {
            return {
                success: false,
                error: error.message,
                prompts: []
            };
        }
    }
    
    /**
     * Create or update prompt
     */
    async savePrompt(promptData) {
        try {
            const response = await this.client.post('/api/prompts', promptData);
            return {
                success: true,
                promptId: response.data.prompt_id,
                data: response.data
            };
        } catch (error) {
            return {
                success: false,
                error: error.message,
                promptId: null
            };
        }
    }
    
    /**
     * Delete prompt
     */
    async deletePrompt(promptId) {
        try {
            await this.client.delete(`/api/prompts/${promptId}`);
            return {
                success: true
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    /**
     * Get application settings
     */
    async getSettings() {
        try {
            const response = await this.client.get('/api/settings');
            return {
                success: true,
                settings: response.data
            };
        } catch (error) {
            return {
                success: false,
                error: error.message,
                settings: {}
            };
        }
    }
    
    /**
     * Update application settings
     */
    async updateSettings(settings) {
        try {
            const response = await this.client.post('/api/settings', settings);
            return {
                success: true,
                data: response.data
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    /**
     * Clean up test data
     */
    async cleanupTestData() {
        console.log('ApiClient: Cleaning up test data...');
        
        try {
            // Get all contracts
            const contractsResult = await this.getContracts();
            if (contractsResult.success) {
                // Delete test contracts (those with "test" in the name)
                const testContracts = contractsResult.contracts.filter(c => 
                    c.name?.toLowerCase().includes('test') || 
                    c.filename?.toLowerCase().includes('test')
                );
                
                for (const contract of testContracts) {
                    await this.client.delete(`/api/contracts/${contract.id}`);
                    console.log(`ApiClient: Deleted test contract: ${contract.name}`);
                }
            }
            
            // Get all analysis results
            const resultsResult = await this.getAnalysisResults();
            if (resultsResult.success) {
                // Delete test analysis results
                const testResults = resultsResult.results.filter(r => 
                    r.contract_name?.toLowerCase().includes('test')
                );
                
                for (const result of testResults) {
                    await this.client.delete(`/api/analysis-results/${result.id}`);
                    console.log(`ApiClient: Deleted test analysis: ${result.id}`);
                }
            }
            
            console.log('ApiClient: Test data cleanup completed');
            
        } catch (error) {
            console.error('ApiClient: Error during test data cleanup:', error.message);
        }
    }
    
    /**
     * Set up test data
     */
    async setupTestData() {
        console.log('ApiClient: Setting up test data...');
        
        try {
            // Clean up any existing test data first
            await this.cleanupTestData();
            
            // Upload test contracts
            const testFiles = this.config.getTestData('files');
            const uploadResults = [];
            
            for (const [fileName, filePath] of Object.entries(testFiles)) {
                if (fs.existsSync(filePath)) {
                    const result = await this.uploadContract(filePath);
                    uploadResults.push({
                        fileName,
                        filePath,
                        result
                    });
                    
                    if (result.success) {
                        console.log(`ApiClient: Uploaded test contract: ${fileName}`);
                    } else {
                        console.error(`ApiClient: Failed to upload test contract ${fileName}:`, result.error);
                    }
                }
            }
            
            return {
                success: true,
                uploadResults
            };
            
        } catch (error) {
            console.error('ApiClient: Error setting up test data:', error.message);
            return {
                success: false,
                error: error.message
            };
        }
    }
}

module.exports = ApiClient;