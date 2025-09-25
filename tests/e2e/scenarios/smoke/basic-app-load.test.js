/**
 * Basic Application Load Smoke Test
 * 
 * Simple smoke test to verify the application loads and key elements are present.
 * This test validates the foundation before running more complex scenarios.
 */

const TestBase = require('../../framework/TestBase');
const DashboardPage = require('../../framework/PageObjects/DashboardPage');
const ApiClient = require('../../framework/ApiClient');
const { expect } = require('chai');

describe('Basic Application Load - Smoke Test', function() {
    this.timeout(60000); // 1 minute timeout for smoke test
    
    let testBase;
    let dashboardPage;
    let apiClient;
    
    beforeEach(async function() {
        testBase = new TestBase('smoke', 'development');
        await testBase.setup();
        dashboardPage = new DashboardPage(testBase.page);
        apiClient = new ApiClient('development');
    });
    
    afterEach(async function() {
        await testBase.cleanup();
    });
    
    it('should load the application and display dashboard', async function() {
        console.log('Testing basic application load...');
        
        // Step 1: Navigate to application
        await testBase.navigateToApp();
        
        // Step 2: Verify dashboard loads
        await testBase.page.waitForSelector('#dashboard', {
            visible: true,
            timeout: 15000
        });
        
        console.log('✓ Dashboard container visible');
        
        // Step 3: Verify sidebar navigation exists
        await testBase.page.waitForSelector('.sidebar', {
            visible: true,
            timeout: 5000
        });
        
        console.log('✓ Sidebar navigation visible');
        
        // Step 4: Verify main navigation tabs are present
        const dashboardTab = await testBase.page.$('[data-tab="dashboard"]');
        const uploadTab = await testBase.page.$('[data-tab="upload"]');
        const promptsTab = await testBase.page.$('[data-tab="prompts"]');
        const settingsTab = await testBase.page.$('[data-tab="settings"]');
        
        expect(dashboardTab).to.not.be.null;
        expect(uploadTab).to.not.be.null;
        expect(promptsTab).to.not.be.null;
        expect(settingsTab).to.not.be.null;
        
        console.log('✓ All navigation tabs present');
        
        // Step 5: Verify key dashboard elements exist
        const metricsGrid = await testBase.page.$('.metrics-grid');
        const analysisTable = await testBase.page.$('.analysis-table');
        const systemStatus = await testBase.page.$('#systemStatus');
        
        expect(metricsGrid).to.not.be.null;
        expect(analysisTable).to.not.be.null;
        
        console.log('✓ Key dashboard elements present');
        
        // Step 6: Verify metrics display some values (even if 0)
        const totalContracts = await testBase.page.$eval('#totalContracts', el => el.textContent);
        const totalTemplates = await testBase.page.$eval('#totalTemplates', el => el.textContent);
        const totalAnalyses = await testBase.page.$eval('#totalAnalyses', el => el.textContent);
        
        expect(totalContracts).to.match(/^\d+$/);
        expect(totalTemplates).to.match(/^\d+$/);
        expect(totalAnalyses).to.match(/^\d+$/);
        
        console.log(`✓ Metrics loaded: ${totalContracts} contracts, ${totalTemplates} templates, ${totalAnalyses} analyses`);
        
        // Step 7: Take a screenshot for verification
        await testBase.takeScreenshot('basic-app-load-success');
        
        console.log('✓ Basic application load test completed successfully');
    });
    
    it('should allow navigation between tabs', async function() {
        console.log('Testing tab navigation...');
        
        await testBase.navigateToApp();
        
        // Test navigation to upload tab
        await testBase.page.click('[data-tab="upload"]');
        await testBase.page.waitForSelector('#upload', {
            visible: true,
            timeout: 5000
        });
        
        console.log('✓ Upload tab navigation works');
        
        // Test navigation to prompts tab
        await testBase.page.click('[data-tab="prompts"]');
        await testBase.page.waitForSelector('#prompts', {
            visible: true,
            timeout: 5000
        });
        
        console.log('✓ Prompts tab navigation works');
        
        // Test navigation to settings tab
        await testBase.page.click('[data-tab="settings"]');
        await testBase.page.waitForSelector('#settings', {
            visible: true,
            timeout: 5000
        });
        
        console.log('✓ Settings tab navigation works');
        
        // Return to dashboard
        await testBase.page.click('[data-tab="dashboard"]');
        await testBase.page.waitForSelector('#dashboard', {
            visible: true,
            timeout: 5000
        });
        
        console.log('✓ Return to dashboard works');
        console.log('✓ Tab navigation test completed successfully');
    });
    
    it('should verify API connectivity', async function() {
        console.log('Testing API connectivity...');
        
        // Check API health
        const healthCheck = await apiClient.checkHealth();
        expect(healthCheck.healthy).to.be.true;
        
        console.log('✓ API health check passed');
        
        // Try to fetch basic data
        const contractsResult = await apiClient.getContracts();
        expect(contractsResult.success).to.be.true;
        expect(contractsResult.contracts).to.be.an('array');
        
        console.log(`✓ Contracts API working: ${contractsResult.contracts.length} contracts found`);
        
        const templatesResult = await apiClient.getTemplates();
        expect(templatesResult.success).to.be.true;
        expect(templatesResult.templates).to.be.an('array');
        
        console.log(`✓ Templates API working: ${templatesResult.templates.length} templates found`);
        
        console.log('✓ API connectivity test completed successfully');
    });
    
    it('should handle JavaScript errors gracefully', async function() {
        console.log('Testing JavaScript error handling...');
        
        const jsErrors = [];
        
        // Listen for JavaScript errors
        testBase.page.on('pageerror', (error) => {
            jsErrors.push(error.message);
        });
        
        await testBase.navigateToApp();
        
        // Wait a bit for any errors to occur
        await testBase.page.waitForTimeout(3000);
        
        // Allow some errors but not critical ones
        if (jsErrors.length > 0) {
            console.log('JavaScript errors found:', jsErrors);
            
            // Check if any critical errors occurred
            const criticalErrors = jsErrors.filter(error => 
                error.includes('ReferenceError') ||
                error.includes('TypeError: Cannot read') ||
                error.includes('modules is not defined')
            );
            
            if (criticalErrors.length > 0) {
                console.error('Critical JavaScript errors found:', criticalErrors);
                throw new Error(`Critical JavaScript errors: ${criticalErrors.join(', ')}`);
            }
            
            console.log('✓ Only non-critical JavaScript errors found - application still functional');
        } else {
            console.log('✓ No JavaScript errors found');
        }
        
        console.log('✓ JavaScript error handling test completed');
    });
});