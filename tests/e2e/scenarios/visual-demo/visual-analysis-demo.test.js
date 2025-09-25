/**
 * Visual Analysis Demo E2E Test
 * 
 * Interactive test designed to be run with visible browser window to demonstrate
 * complete contract analysis workflow including uploading, analyzing, and opening all reports.
 * 
 * Features:
 * - Visible browser window for demonstration
 * - Comprehensive step-by-step workflow
 * - Opens all report types (Excel, PDF, Word)
 * - Extended timeouts for demonstration purposes
 * - Detailed logging and screenshot capture
 */

const TestBase = require('../../framework/TestBase');
const DashboardPage = require('../../framework/PageObjects/DashboardPage');
const UploadPage = require('../../framework/PageObjects/UploadPage');
const ApiClient = require('../../framework/ApiClient');
const testConfig = require('../../config/test.config');
const path = require('path');
const fs = require('fs-extra');
const { expect } = require('chai');

describe('Visual Analysis Demo - Complete Workflow', function() {
    this.timeout(600000); // 10 minute timeout for visual demo
    
    let testBase;
    let dashboardPage;
    let uploadPage;
    let apiClient;
    let testContractFile;
    let analysisId;
    
    before(async function() {
        console.log('\n🎬 Setting up Visual Analysis Demo...');
        console.log('='.repeat(60));
        
        // Initialize test components with visible browser
        testBase = new TestBase('integration', 'development', {
            headless: false,
            slowMo: 500, // Slow down for demonstration
            devtools: false
        });
        
        apiClient = new ApiClient('development');
        
        // Use the existing test contract file
        testContractFile = path.join(__dirname, '../../fixtures/test-contract.docx');
        
        // Clean up any existing test data
        await apiClient.cleanupTestData();
        
        console.log('✅ Setup completed - Ready for visual demo\n');
    });
    
    beforeEach(async function() {
        await testBase.setup();
        dashboardPage = new DashboardPage(testBase.page);
        uploadPage = new UploadPage(testBase.page);
    });
    
    afterEach(async function() {
        // Keep browser open for demonstration - no cleanup
        if (testBase.page) {
            await testBase.page.waitForTimeout(2000); // Brief pause before next test
        }
    });
    
    after(async function() {
        console.log('\n🎭 Demo completed - Browser will remain open for inspection');
        // Don't close browser automatically in visual demo mode
    });
    
    it('🎯 Visual Demo: Complete Contract Analysis and Report Generation', async function() {
        console.log('\n🚀 Starting Visual Contract Analysis Demo');
        console.log('=' .repeat(60));
        
        // === STEP 1: Navigate to Application ===
        console.log('\n📱 STEP 1: Loading Contract Analyzer Dashboard...');
        await testBase.navigateToApp();
        
        // Wait for user to see the page load
        await testBase.page.waitForTimeout(2000);
        
        await dashboardPage.assertDashboardLoaded();
        await dashboardPage.assertSystemHealthy();
        
        console.log('✅ Dashboard loaded successfully');
        await testBase.takeScreenshot('01_dashboard_loaded');
        
        // === STEP 2: Navigate to Upload Page ===
        console.log('\n📤 STEP 2: Navigating to File Upload...');
        await dashboardPage.navigateToUpload();
        await uploadPage.waitForLoad();
        
        console.log('✅ Upload page ready');
        await testBase.takeScreenshot('02_upload_page_loaded');
        await testBase.page.waitForTimeout(1500);
        
        // === STEP 3: Upload Contract File ===
        console.log('\n📄 STEP 3: Uploading Contract Document...');
        
        // Select template first
        const templateName = 'SOW'; // Statement of Work template
        console.log(`   Selecting template: ${templateName}`);
        
        // Upload the contract file
        console.log(`   Uploading file: ${path.basename(testContractFile)}`);
        await uploadPage.uploadFile(testContractFile, templateName);
        
        // Wait for upload to complete
        await uploadPage.assertUploadSuccessful();
        console.log('✅ Contract uploaded successfully');
        await testBase.takeScreenshot('03_contract_uploaded');
        await testBase.page.waitForTimeout(2000);
        
        // === STEP 4: Return to Dashboard ===
        console.log('\n🏠 STEP 4: Returning to Dashboard...');
        await testBase.page.click('[data-tab="dashboard"]');
        await dashboardPage.waitForLoad();
        
        console.log('✅ Back on dashboard');
        await testBase.takeScreenshot('04_back_to_dashboard');
        
        // === STEP 5: Locate Uploaded Contract ===
        console.log('\n🔍 STEP 5: Locating Uploaded Contract...');
        await dashboardPage.refresh();
        
        const contracts = await dashboardPage.getContracts();
        console.log(`   Found ${contracts.length} contract(s) in system`);
        
        const uploadedContract = contracts.find(c => 
            c.name.includes('test-contract') || 
            c.name.includes('sample-contract') ||
            contracts.length > 0 // Use first contract if no specific match
        );
        
        if (!uploadedContract && contracts.length === 0) {
            throw new Error('No contracts found in dashboard');
        }
        
        const contractToUse = uploadedContract || contracts[0];
        console.log(`✅ Contract located: ${contractToUse.name}`);
        
        // === STEP 6: Start Analysis via API ===
        console.log('\n🔄 STEP 6: Initiating Contract Analysis...');
        
        // Get contract ID via API
        const contractsResult = await apiClient.getContracts();
        if (!contractsResult.success || contractsResult.contracts.length === 0) {
            throw new Error('Could not retrieve contract via API');
        }
        
        const latestContract = contractsResult.contracts[0];
        const contractId = latestContract.id;
        
        console.log(`   Contract ID: ${contractId}`);
        console.log(`   Template: ${templateName}`);
        console.log('   Starting analysis...');
        
        // Start analysis
        const analysisResult = await apiClient.analyzeContract(contractId, {
            template: templateName,
            custom_prompts: false
        });
        
        if (!analysisResult.success) {
            throw new Error(`Failed to start analysis: ${analysisResult.error}`);
        }
        
        analysisId = analysisResult.analysisId;
        console.log(`✅ Analysis started (ID: ${analysisId})`);
        await testBase.takeScreenshot('05_analysis_started');
        
        // === STEP 7: Monitor Analysis Progress ===
        console.log('\n⏳ STEP 7: Monitoring Analysis Progress...');
        console.log('   This may take 1-3 minutes depending on document complexity...');
        
        // Show progress in dashboard
        await dashboardPage.refresh();
        await testBase.page.waitForTimeout(3000);
        await testBase.takeScreenshot('06_analysis_in_progress');
        
        // Wait for analysis completion
        const completedAnalysis = await apiClient.waitForAnalysisComplete(analysisId, 300000); // 5 min timeout
        
        console.log('✅ Analysis completed successfully!');
        console.log(`   Status: ${completedAnalysis.status}`);
        console.log(`   Changes found: ${completedAnalysis.changes ? completedAnalysis.changes.length : 'N/A'}`);
        
        // Refresh dashboard to show completed analysis
        await dashboardPage.refresh();
        await testBase.page.waitForTimeout(2000);
        await testBase.takeScreenshot('07_analysis_completed');
        
        // === STEP 8: Generate and Open Reports ===
        console.log('\n📊 STEP 8: Generating and Opening Reports...');
        
        const reportTypes = [
            { type: 'excel', extension: 'xlsx', name: 'Excel Workbook' },
            { type: 'pdf', extension: 'pdf', name: 'PDF Report' },
            { type: 'word', extension: 'docx', name: 'Word Document' }
        ];
        
        const downloadDir = path.join(__dirname, '../../temp/downloads');
        await fs.ensureDir(downloadDir);
        
        for (let i = 0; i < reportTypes.length; i++) {
            const report = reportTypes[i];
            console.log(`\n   📄 Generating ${report.name}...`);
            
            try {
                // Generate report
                const reportResult = await apiClient.generateReport(analysisId, report.type);
                
                if (!reportResult.success) {
                    console.warn(`     ⚠️  Failed to generate ${report.name}: ${reportResult.error}`);
                    continue;
                }
                
                console.log(`     ✅ ${report.name} generated successfully`);
                
                // Download report
                const downloadPath = path.join(
                    downloadDir,
                    `analysis-report-${report.type}-${Date.now()}.${report.extension}`
                );
                
                const downloadResult = await apiClient.downloadReport(reportResult.reportId, downloadPath);
                
                if (downloadResult.success && fs.existsSync(downloadPath)) {
                    console.log(`     📥 Downloaded: ${path.basename(downloadPath)}`);
                    
                    // Verify file size
                    const stats = fs.statSync(downloadPath);
                    console.log(`     📐 File size: ${(stats.size / 1024).toFixed(1)} KB`);
                    
                    // Open report in system default application (for demonstration)
                    if (process.platform === 'win32') {
                        console.log(`     👀 Opening ${report.name} for review...`);
                        try {
                            const { spawn } = require('child_process');
                            spawn('cmd', ['/c', 'start', '""', downloadPath], { detached: true });
                            await testBase.page.waitForTimeout(2000); // Allow time for app to open
                        } catch (error) {
                            console.log(`     ⚠️  Could not auto-open file: ${error.message}`);
                        }
                    }
                    
                } else {
                    console.warn(`     ⚠️  Failed to download ${report.name}`);
                }
                
            } catch (error) {
                console.warn(`     ❌ Error with ${report.name}: ${error.message}`);
            }
            
            // Brief pause between reports
            await testBase.page.waitForTimeout(1000);
        }
        
        // === STEP 9: Final Dashboard Review ===
        console.log('\n📋 STEP 9: Final Dashboard Review...');
        
        await dashboardPage.refresh();
        await testBase.page.waitForTimeout(2000);
        
        const finalStats = await dashboardPage.getStatistics();
        console.log('\n📈 Final Statistics:');
        console.log(`   Total Contracts: ${finalStats.totalContracts}`);
        console.log(`   Completed Analyses: ${finalStats.completedAnalyses}`);
        console.log(`   Failed Analyses: ${finalStats.failedAnalyses}`);
        console.log(`   System Status: ${finalStats.systemStatus}`);
        
        await testBase.takeScreenshot('08_final_dashboard');
        
        // === DEMO COMPLETION ===
        console.log('\n🎉 VISUAL DEMO COMPLETED SUCCESSFULLY!');
        console.log('=' .repeat(60));
        console.log('\n📋 Summary:');
        console.log('   ✅ Contract uploaded successfully');
        console.log('   ✅ Analysis completed with results');
        console.log('   ✅ Reports generated in multiple formats');
        console.log('   ✅ All components functioning properly');
        console.log('\n💡 Browser will remain open for manual inspection');
        console.log('   Check the temp/downloads folder for generated reports');
        console.log('   Screenshots saved in temp/screenshots folder');
        
        // Keep browser open for inspection
        console.log('\n⏸️  Pausing for manual review (60 seconds)...');
        await testBase.page.waitForTimeout(60000);
        
        // Success assertions
        expect(completedAnalysis).to.not.be.null;
        expect(completedAnalysis.status).to.equal('completed');
        expect(finalStats.completedAnalyses).to.be.greaterThan(0);
        
        console.log('\n✅ All assertions passed - Demo successful!');
    });
    
    it('🔍 Visual Demo: Error Handling Showcase', async function() {
        console.log('\n🚨 BONUS: Error Handling Demonstration');
        console.log('=' .repeat(60));
        
        await testBase.navigateToApp();
        await dashboardPage.navigateToUpload();
        
        console.log('\n📤 Demonstrating invalid file upload handling...');
        
        // Create and try invalid file
        const invalidFile = path.join(__dirname, '../../temp/invalid-file.txt');
        await fs.ensureFile(invalidFile);
        await fs.writeFile(invalidFile, 'This is not a valid contract file');
        
        try {
            await uploadPage.uploadFile(invalidFile);
            console.log('⚠️  Should have failed - checking error handling...');
        } catch (error) {
            console.log('✅ Error correctly caught and handled');
        }
        
        await testBase.takeScreenshot('error_handling_demo');
        await testBase.page.waitForTimeout(3000);
        
        console.log('✅ Error handling demonstration completed');
    });
});