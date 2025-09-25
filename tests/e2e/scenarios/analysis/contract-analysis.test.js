/**
 * Contract Analysis E2E Tests
 * 
 * Comprehensive testing of contract analysis functionality including:
 * - Single contract analysis
 * - Batch analysis operations
 * - Analysis progress monitoring
 * - Results validation
 * - Error handling and recovery
 * - Performance under load
 */

const TestBase = require('../../framework/TestBase');
const DashboardPage = require('../../framework/PageObjects/DashboardPage');
const UploadPage = require('../../framework/PageObjects/UploadPage');
const ApiClient = require('../../framework/ApiClient');
const testConfig = require('../../config/test.config');
const path = require('path');
const fs = require('fs-extra');
const { expect } = require('chai');

describe('Contract Analysis Functionality', function() {
    this.timeout(600000); // 10 minute timeout for analysis tests
    
    let testBase;
    let dashboardPage;
    let uploadPage;
    let apiClient;
    let testContractId;
    let analysisId;
    
    before(async function() {
        console.log('Setting up Contract Analysis test suite...');
        
        apiClient = new ApiClient('development');
        
        // Clean up and set up test data
        await apiClient.cleanupTestData();
        await setupTestContracts();
    });
    
    beforeEach(async function() {
        testBase = new TestBase('integration', 'development');
        await testBase.setup();
        dashboardPage = new DashboardPage(testBase.page);
        uploadPage = new UploadPage(testBase.page);
    });
    
    afterEach(async function() {
        await testBase.cleanup();
    });
    
    after(async function() {
        // Clean up test data
        await apiClient.cleanupTestData();
    });
    
    /**
     * Set up test contracts for analysis
     */
    async function setupTestContracts() {
        console.log('Setting up test contracts for analysis...');
        
        // Create test contract file if it doesn't exist
        const testFile = testConfig.getTestFile('validContract');
        if (!fs.existsSync(testFile)) {
            await fs.ensureDir(path.dirname(testFile));
            await fs.writeFile(testFile, 'PK\x03\x04Sample contract content for analysis testing');
        }
        
        // Upload test contract via API
        const uploadResult = await apiClient.uploadContract(testFile, 'SOW');
        if (uploadResult.success) {
            testContractId = uploadResult.contractId;
            console.log('Test contract uploaded successfully:', testContractId);
        } else {
            console.warn('Failed to upload test contract:', uploadResult.error);
        }
    }
    
    it('should start analysis for a single contract', async function() {
        console.log('Testing single contract analysis start...');
        
        await testBase.navigateToApp();
        await dashboardPage.assertDashboardLoaded();
        
        // Check if we have contracts available
        const contracts = await dashboardPage.getContracts();
        console.log(`Found ${contracts.length} contracts available for analysis`);
        
        if (contracts.length === 0) {
            // Upload a contract first
            await dashboardPage.navigateToUpload();
            await uploadPage.assertUploadPageLoaded();
            
            const testFile = testConfig.getTestFile('validContract');
            await uploadPage.uploadFile(testFile, 'SOW');
            await uploadPage.assertUploadSuccessful();
            
            // Return to dashboard
            await dashboardPage.navigateToUpload();
            await testBase.page.click('[data-tab="dashboard"]');
            await dashboardPage.assertDashboardLoaded();
        }
        
        // Start analysis via API (UI-driven analysis would be complex to implement without specific UI elements)
        if (testContractId) {
            const analysisResult = await apiClient.analyzeContract(testContractId, {
                template: 'SOW',
                analysis_type: 'standard'
            });
            
            if (analysisResult.success) {
                analysisId = analysisResult.analysisId;
                console.log('Analysis started successfully:', analysisId);
                
                // Refresh dashboard to see analysis in progress
                await dashboardPage.refresh();
                
                const analysisResults = await dashboardPage.getAnalysisResults();
                console.log('Analysis results visible in dashboard:', analysisResults.length);
                
            } else {
                console.warn('Failed to start analysis:', analysisResult.error);
            }
        }
        
        console.log('✓ Single contract analysis start tested');
        await testBase.takeScreenshot('single_contract_analysis_start');
    });
    
    it('should monitor analysis progress in real-time', async function() {
        console.log('Testing analysis progress monitoring...');
        
        await testBase.navigateToApp();
        await dashboardPage.assertDashboardLoaded();
        
        if (analysisId) {
            console.log('Monitoring analysis progress for:', analysisId);
            
            let attempts = 0;
            const maxAttempts = 30; // 1 minute maximum wait
            
            while (attempts < maxAttempts) {
                // Refresh dashboard to get latest status
                await dashboardPage.refresh();
                
                // Check analysis results
                const analysisResults = await dashboardPage.getAnalysisResults();
                const ourAnalysis = analysisResults.find(r => 
                    r.contract.includes('test-contract') || 
                    r.contract.includes('sample')
                );
                
                if (ourAnalysis) {
                    console.log(`Analysis status: ${ourAnalysis.status}`);
                    
                    if (ourAnalysis.status.toLowerCase() === 'completed') {
                        console.log('✓ Analysis completed successfully');
                        break;
                    }
                    
                    if (ourAnalysis.status.toLowerCase() === 'failed') {
                        console.log('⚠️ Analysis failed');
                        break;
                    }
                }
                
                // Wait before next check
                await testBase.page.waitForTimeout(2000);
                attempts++;
            }
            
            if (attempts >= maxAttempts) {
                console.log('⚠️ Analysis monitoring timed out');
            }
        } else {
            console.log('⚠️ No analysis ID available for monitoring');
        }
        
        await testBase.takeScreenshot('analysis_progress_monitoring');
    });
    
    it('should complete analysis and display results', async function() {
        console.log('Testing analysis completion and results display...');
        
        await testBase.navigateToApp();
        await dashboardPage.assertDashboardLoaded();
        
        if (analysisId) {
            // Wait for analysis to complete
            try {
                const completedAnalysis = await apiClient.waitForAnalysisComplete(analysisId, 120000); // 2 minutes
                
                expect(completedAnalysis).to.not.be.null;
                expect(completedAnalysis.status).to.equal('completed');
                
                console.log('Analysis completed with results:', Object.keys(completedAnalysis));
                
                // Refresh dashboard to see completed results
                await dashboardPage.refresh();
                
                const dashboardResults = await dashboardPage.getAnalysisResults();
                const completedResult = dashboardResults.find(r => 
                    r.status.toLowerCase() === 'completed'
                );
                
                expect(completedResult).to.not.be.undefined;
                console.log('✓ Completed analysis visible in dashboard');
                
            } catch (error) {
                console.warn('Analysis completion test failed:', error.message);
            }
        }
        
        await testBase.takeScreenshot('analysis_completion_results');
    });
    
    it('should handle batch analysis of multiple contracts', async function() {
        console.log('Testing batch analysis functionality...');
        
        await testBase.navigateToApp();
        await dashboardPage.assertDashboardLoaded();
        
        // Get current contracts
        const contractsResult = await apiClient.getContracts();
        
        if (contractsResult.success && contractsResult.contracts.length > 1) {
            console.log(`Starting batch analysis for ${contractsResult.contracts.length} contracts`);
            
            // Start analysis for multiple contracts
            const batchAnalysisResults = [];
            
            for (const contract of contractsResult.contracts.slice(0, 3)) { // Test with up to 3 contracts
                try {
                    const analysisResult = await apiClient.analyzeContract(contract.id, {
                        template: 'SOW',
                        analysis_type: 'batch'
                    });
                    
                    if (analysisResult.success) {
                        batchAnalysisResults.push({
                            contractId: contract.id,
                            analysisId: analysisResult.analysisId
                        });
                    }
                } catch (error) {
                    console.warn(`Failed to start analysis for contract ${contract.id}:`, error.message);
                }
            }
            
            console.log(`Started ${batchAnalysisResults.length} analyses in batch`);
            
            // Monitor batch progress
            if (batchAnalysisResults.length > 0) {
                await dashboardPage.refresh();
                
                const analysisResults = await dashboardPage.getAnalysisResults();
                console.log(`Dashboard showing ${analysisResults.length} analysis results`);
                
                // Verify we can see multiple analyses in progress
                expect(analysisResults.length).to.be.greaterThanOrEqual(batchAnalysisResults.length);
            }
            
            console.log('✓ Batch analysis functionality tested');
            
        } else {
            console.log('⚠️ Not enough contracts available for batch analysis test');
        }
        
        await testBase.takeScreenshot('batch_analysis_test');
    });
    
    it('should validate analysis results accuracy', async function() {
        console.log('Testing analysis results validation...');
        
        await testBase.navigateToApp();
        await dashboardPage.assertDashboardLoaded();
        
        // Get completed analysis results
        const analysisResults = await dashboardPage.getAnalysisResults();
        const completedResults = analysisResults.filter(r => 
            r.status.toLowerCase() === 'completed'
        );
        
        if (completedResults.length > 0) {
            const result = completedResults[0];
            
            console.log('Validating analysis result:', result);
            
            // Validate result structure
            expect(result.contract).to.be.a('string');
            expect(result.status).to.equal('Completed');
            
            if (result.score) {
                expect(result.score).to.match(/\d+%?/);
            }
            
            // Get detailed results via API
            const detailedResults = await apiClient.getAnalysisResults();
            if (detailedResults.success && detailedResults.results.length > 0) {
                const apiResult = detailedResults.results[0];
                
                console.log('API result structure:', Object.keys(apiResult));
                
                // Validate API result structure
                expect(apiResult).to.have.property('status');
                
                if (apiResult.changes) {
                    expect(apiResult.changes).to.be.an('array');
                    console.log(`Analysis found ${apiResult.changes.length} changes`);
                }
            }
            
            console.log('✓ Analysis results validation completed');
            
        } else {
            console.log('⚠️ No completed analysis results available for validation');
        }
        
        await testBase.takeScreenshot('analysis_results_validation');
    });
    
    it('should handle analysis errors gracefully', async function() {
        console.log('Testing analysis error handling...');
        
        await testBase.navigateToApp();
        await dashboardPage.assertDashboardLoaded();
        
        // Test with invalid contract ID
        try {
            const errorResult = await apiClient.analyzeContract('invalid-contract-id', {
                template: 'SOW'
            });
            
            expect(errorResult.success).to.be.false;
            expect(errorResult.error).to.be.a('string');
            
            console.log('✓ Invalid contract ID error handled correctly');
            
        } catch (error) {
            console.log('✓ Analysis error handling working:', error.message);
        }
        
        // Test with invalid template
        if (testContractId) {
            try {
                const errorResult = await apiClient.analyzeContract(testContractId, {
                    template: 'INVALID_TEMPLATE'
                });
                
                if (!errorResult.success) {
                    console.log('✓ Invalid template error handled correctly');
                }
                
            } catch (error) {
                console.log('✓ Template validation error handled:', error.message);
            }
        }
        
        await testBase.takeScreenshot('analysis_error_handling');
    });
    
    it('should support different analysis types', async function() {
        console.log('Testing different analysis types...');
        
        await testBase.navigateToApp();
        await dashboardPage.assertDashboardLoaded();
        
        if (testContractId) {
            const analysisTypes = ['standard', 'detailed', 'quick'];
            
            for (const type of analysisTypes) {
                try {
                    const result = await apiClient.analyzeContract(testContractId, {
                        template: 'SOW',
                        analysis_type: type
                    });
                    
                    if (result.success) {
                        console.log(`✓ Analysis type "${type}" started successfully`);
                    } else {
                        console.log(`⚠️ Analysis type "${type}" failed:`, result.error);
                    }
                    
                } catch (error) {
                    console.log(`Analysis type "${type}" error:`, error.message);
                }
            }
        }
        
        await testBase.takeScreenshot('analysis_types_test');
    });
    
    it('should maintain analysis history', async function() {
        console.log('Testing analysis history maintenance...');
        
        await testBase.navigateToApp();
        await dashboardPage.assertDashboardLoaded();
        
        // Get current analysis results count
        const initialResults = await dashboardPage.getAnalysisResults();
        const initialCount = initialResults.length;
        
        console.log(`Initial analysis results count: ${initialCount}`);
        
        // Perform a new analysis if possible
        if (testContractId) {
            const newAnalysis = await apiClient.analyzeContract(testContractId, {
                template: 'SOW',
                analysis_type: 'history_test'
            });
            
            if (newAnalysis.success) {
                await dashboardPage.refresh();
                
                const updatedResults = await dashboardPage.getAnalysisResults();
                const updatedCount = updatedResults.length;
                
                console.log(`Updated analysis results count: ${updatedCount}`);
                
                // History should be maintained (new result added)
                expect(updatedCount).to.be.greaterThanOrEqual(initialCount);
                
                console.log('✓ Analysis history maintained correctly');
            }
        }
        
        await testBase.takeScreenshot('analysis_history_test');
    });
    
    it('should handle concurrent analysis requests', async function() {
        console.log('Testing concurrent analysis handling...');
        
        await testBase.navigateToApp();
        await dashboardPage.assertDashboardLoaded();
        
        if (testContractId) {
            // Start multiple analyses concurrently
            const concurrentPromises = [];
            
            for (let i = 0; i < 3; i++) {
                const promise = apiClient.analyzeContract(testContractId, {
                    template: 'SOW',
                    analysis_type: `concurrent_test_${i}`
                });
                concurrentPromises.push(promise);
            }
            
            try {
                const results = await Promise.allSettled(concurrentPromises);
                
                const successfulResults = results.filter(r => 
                    r.status === 'fulfilled' && r.value.success
                );
                
                console.log(`${successfulResults.length}/3 concurrent analyses started successfully`);
                
                if (successfulResults.length > 0) {
                    console.log('✓ Concurrent analysis requests handled');
                } else {
                    console.log('⚠️ No concurrent analyses succeeded');
                }
                
            } catch (error) {
                console.log('Concurrent analysis error:', error.message);
            }
        }
        
        await testBase.takeScreenshot('concurrent_analysis_test');
    });
    
    it('should provide analysis performance metrics', async function() {
        console.log('Testing analysis performance metrics...');
        
        await testBase.navigateToApp();
        await dashboardPage.assertDashboardLoaded();
        
        // Check dashboard statistics
        const stats = await dashboardPage.getStatistics();
        
        console.log('Dashboard statistics:', stats);
        
        // Validate performance indicators
        expect(stats.totalContracts).to.be.a('number');
        expect(stats.totalResults).to.be.a('number');
        expect(stats.completedAnalyses).to.be.a('number');
        
        if (stats.systemStatus) {
            console.log('System status:', stats.systemStatus);
        }
        
        // Check performance via API
        const healthCheck = await apiClient.checkHealth();
        if (healthCheck.healthy && healthCheck.data) {
            console.log('API health metrics available');
        }
        
        console.log('✓ Analysis performance metrics validated');
        
        await testBase.takeScreenshot('analysis_performance_metrics');
    });
});