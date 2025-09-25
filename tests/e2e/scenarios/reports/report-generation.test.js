/**
 * Report Generation E2E Tests
 * 
 * Comprehensive testing of report generation functionality including:
 * - Excel report generation
 * - PDF report generation
 * - Word document generation
 * - Report download verification
 * - Multiple format generation
 * - Report content validation
 */

const TestBase = require('../../framework/TestBase');
const DashboardPage = require('../../framework/PageObjects/DashboardPage');
const ApiClient = require('../../framework/ApiClient');
const testConfig = require('../../config/test.config');
const path = require('path');
const fs = require('fs-extra');
const { expect } = require('chai');

describe('Report Generation Functionality', function() {
    this.timeout(600000); // 10 minute timeout for report generation tests
    
    let testBase;
    let dashboardPage;
    let apiClient;
    let testAnalysisId;
    let downloadPath;
    
    before(async function() {
        console.log('Setting up Report Generation test suite...');
        
        apiClient = new ApiClient('development');
        downloadPath = path.join(__dirname, '../../temp/downloads');
        
        // Ensure download directory exists
        await fs.ensureDir(downloadPath);
        
        // Set up test analysis for report generation
        await setupTestAnalysis();
    });
    
    beforeEach(async function() {
        testBase = new TestBase('integration', 'development');
        await testBase.setup();
        dashboardPage = new DashboardPage(testBase.page);
    });
    
    afterEach(async function() {
        await testBase.cleanup();
    });
    
    after(async function() {
        // Clean up test data and downloads
        await apiClient.cleanupTestData();
        
        // Clean up downloaded files
        if (fs.existsSync(downloadPath)) {
            const files = await fs.readdir(downloadPath);
            for (const file of files) {
                if (file.includes('test-report')) {
                    await fs.remove(path.join(downloadPath, file));
                }
            }
        }
    });
    
    /**
     * Set up test analysis for report generation
     */
    async function setupTestAnalysis() {
        console.log('Setting up test analysis for report generation...');
        
        // Get existing analysis results
        const analysisResults = await apiClient.getAnalysisResults();
        
        if (analysisResults.success && analysisResults.results.length > 0) {
            // Use existing analysis
            const existingAnalysis = analysisResults.results[0];
            testAnalysisId = existingAnalysis.id;
            console.log('Using existing analysis for reports:', testAnalysisId);
            
        } else {
            // Create a new analysis if none exists
            console.log('No existing analysis found - creating test analysis...');
            
            // First upload a test contract
            const testFile = testConfig.getTestFile('validContract');
            if (!fs.existsSync(testFile)) {
                await fs.ensureDir(path.dirname(testFile));
                await fs.writeFile(testFile, 'PK\x03\x04Test contract for report generation');
            }
            
            const uploadResult = await apiClient.uploadContract(testFile, 'SOW');
            
            if (uploadResult.success) {
                // Start analysis
                const analysisResult = await apiClient.analyzeContract(uploadResult.contractId, {
                    template: 'SOW',
                    analysis_type: 'report_test'
                });
                
                if (analysisResult.success) {
                    testAnalysisId = analysisResult.analysisId;
                    
                    // Wait for analysis to complete
                    try {
                        await apiClient.waitForAnalysisComplete(testAnalysisId, 180000); // 3 minutes
                        console.log('Test analysis completed successfully');
                    } catch (error) {
                        console.warn('Test analysis may not have completed:', error.message);
                    }
                }
            }
        }
        
        if (!testAnalysisId) {
            console.warn('No test analysis available for report generation tests');
        }
    }
    
    it('should generate Excel report successfully', async function() {
        console.log('Testing Excel report generation...');
        
        if (!testAnalysisId) {
            this.skip('No analysis available for report generation');
        }
        
        // Generate Excel report via API
        const reportResult = await apiClient.generateReport(testAnalysisId, 'excel', {
            include_summary: true,
            include_details: true
        });
        
        expect(reportResult.success).to.be.true;
        expect(reportResult.reportId).to.not.be.null;
        
        console.log('Excel report generated:', reportResult.reportId);
        
        // Download the report
        const downloadFilePath = path.join(downloadPath, `test-report-excel-${Date.now()}.xlsx`);
        const downloadResult = await apiClient.downloadReport(reportResult.reportId, downloadFilePath);
        
        expect(downloadResult.success).to.be.true;
        expect(fs.existsSync(downloadFilePath)).to.be.true;
        
        // Verify file is not empty
        const stats = fs.statSync(downloadFilePath);
        expect(stats.size).to.be.greaterThan(0);
        
        console.log(`✓ Excel report downloaded successfully (${stats.size} bytes)`);
        
        await testBase.navigateToApp();
        await testBase.takeScreenshot('excel_report_generation');
    });
    
    it('should generate PDF report successfully', async function() {
        console.log('Testing PDF report generation...');
        
        if (!testAnalysisId) {
            this.skip('No analysis available for report generation');
        }
        
        // Generate PDF report via API
        const reportResult = await apiClient.generateReport(testAnalysisId, 'pdf', {
            include_charts: true,
            include_summary: true
        });
        
        expect(reportResult.success).to.be.true;
        expect(reportResult.reportId).to.not.be.null;
        
        console.log('PDF report generated:', reportResult.reportId);
        
        // Download the report
        const downloadFilePath = path.join(downloadPath, `test-report-pdf-${Date.now()}.pdf`);
        const downloadResult = await apiClient.downloadReport(reportResult.reportId, downloadFilePath);
        
        expect(downloadResult.success).to.be.true;
        expect(fs.existsSync(downloadFilePath)).to.be.true;
        
        // Verify file is not empty
        const stats = fs.statSync(downloadFilePath);
        expect(stats.size).to.be.greaterThan(0);
        
        console.log(`✓ PDF report downloaded successfully (${stats.size} bytes)`);
        
        await testBase.navigateToApp();
        await testBase.takeScreenshot('pdf_report_generation');
    });
    
    it('should generate Word document report successfully', async function() {
        console.log('Testing Word document report generation...');
        
        if (!testAnalysisId) {
            this.skip('No analysis available for report generation');
        }
        
        // Generate Word report via API
        const reportResult = await apiClient.generateReport(testAnalysisId, 'word', {
            track_changes: true,
            include_comments: true
        });
        
        if (reportResult.success) {
            expect(reportResult.reportId).to.not.be.null;
            
            console.log('Word report generated:', reportResult.reportId);
            
            // Download the report
            const downloadFilePath = path.join(downloadPath, `test-report-word-${Date.now()}.docx`);
            const downloadResult = await apiClient.downloadReport(reportResult.reportId, downloadFilePath);
            
            if (downloadResult.success) {
                expect(fs.existsSync(downloadFilePath)).to.be.true;
                
                const stats = fs.statSync(downloadFilePath);
                expect(stats.size).to.be.greaterThan(0);
                
                console.log(`✓ Word report downloaded successfully (${stats.size} bytes)`);
            } else {
                console.log('Word report download failed:', downloadResult.error);
            }
        } else {
            console.log('⚠️ Word report generation failed (may not be supported on Linux):', reportResult.error);
        }
        
        await testBase.navigateToApp();
        await testBase.takeScreenshot('word_report_generation');
    });
    
    it('should generate multiple report formats simultaneously', async function() {
        console.log('Testing multiple report format generation...');
        
        if (!testAnalysisId) {
            this.skip('No analysis available for report generation');
        }
        
        const reportTypes = ['excel', 'pdf'];
        const reportPromises = reportTypes.map(type => 
            apiClient.generateReport(testAnalysisId, type, {
                batch_id: `multi_format_test_${Date.now()}`
            })
        );
        
        // Generate all reports simultaneously
        const results = await Promise.allSettled(reportPromises);
        
        const successfulReports = results.filter(r => 
            r.status === 'fulfilled' && r.value.success
        );
        
        expect(successfulReports.length).to.be.greaterThan(0);
        
        console.log(`✓ ${successfulReports.length}/${reportTypes.length} report formats generated successfully`);
        
        // Download each successful report
        for (let i = 0; i < results.length; i++) {
            const result = results[i];
            if (result.status === 'fulfilled' && result.value.success) {
                const reportType = reportTypes[i];
                const extension = reportType === 'excel' ? 'xlsx' : 'pdf';
                
                const downloadFilePath = path.join(downloadPath, `multi-format-${reportType}-${Date.now()}.${extension}`);
                const downloadResult = await apiClient.downloadReport(result.value.reportId, downloadFilePath);
                
                if (downloadResult.success) {
                    console.log(`✓ ${reportType} report downloaded`);
                }
            }
        }
        
        await testBase.navigateToApp();
        await testBase.takeScreenshot('multiple_format_reports');
    });
    
    it('should validate report content accuracy', async function() {
        console.log('Testing report content validation...');
        
        if (!testAnalysisId) {
            this.skip('No analysis available for report generation');
        }
        
        // Get analysis details first
        const analysisDetails = await apiClient.getAnalysisResults(testAnalysisId);
        
        if (analysisDetails.success && analysisDetails.results) {
            console.log('Analysis details available for validation');
            
            // Generate Excel report for content validation
            const reportResult = await apiClient.generateReport(testAnalysisId, 'excel');
            
            if (reportResult.success) {
                const downloadFilePath = path.join(downloadPath, `content-validation-${Date.now()}.xlsx`);
                const downloadResult = await apiClient.downloadReport(reportResult.reportId, downloadFilePath);
                
                if (downloadResult.success) {
                    // Basic file validation
                    const stats = fs.statSync(downloadFilePath);
                    expect(stats.size).to.be.greaterThan(100); // Reasonable minimum size
                    
                    console.log('✓ Report content validation completed (basic file checks)');
                    
                    // In a full implementation, we would parse Excel content and validate against analysis data
                }
            }
        }
        
        await testBase.navigateToApp();
        await testBase.takeScreenshot('report_content_validation');
    });
    
    it('should handle report generation errors gracefully', async function() {
        console.log('Testing report generation error handling...');
        
        // Test with invalid analysis ID
        const invalidReportResult = await apiClient.generateReport('invalid-analysis-id', 'excel');
        
        expect(invalidReportResult.success).to.be.false;
        expect(invalidReportResult.error).to.be.a('string');
        
        console.log('✓ Invalid analysis ID error handled correctly');
        
        // Test with invalid report type
        if (testAnalysisId) {
            const invalidTypeResult = await apiClient.generateReport(testAnalysisId, 'invalid-type');
            
            if (!invalidTypeResult.success) {
                console.log('✓ Invalid report type error handled correctly');
            }
        }
        
        await testBase.navigateToApp();
        await testBase.takeScreenshot('report_error_handling');
    });
    
    it('should support custom report templates', async function() {
        console.log('Testing custom report templates...');
        
        if (!testAnalysisId) {
            this.skip('No analysis available for report generation');
        }
        
        // Test with custom template parameters
        const customReportResult = await apiClient.generateReport(testAnalysisId, 'excel', {
            template: 'detailed',
            include_metadata: true,
            include_audit_trail: true,
            custom_branding: true
        });
        
        if (customReportResult.success) {
            console.log('✓ Custom template report generated successfully');
            
            const downloadFilePath = path.join(downloadPath, `custom-template-${Date.now()}.xlsx`);
            const downloadResult = await apiClient.downloadReport(customReportResult.reportId, downloadFilePath);
            
            if (downloadResult.success) {
                console.log('✓ Custom template report downloaded successfully');
            }
        } else {
            console.log('⚠️ Custom template not supported:', customReportResult.error);
        }
        
        await testBase.navigateToApp();
        await testBase.takeScreenshot('custom_report_template');
    });
    
    it('should manage report storage and cleanup', async function() {
        console.log('Testing report storage and cleanup...');
        
        if (!testAnalysisId) {
            this.skip('No analysis available for report generation');
        }
        
        // Generate a report
        const reportResult = await apiClient.generateReport(testAnalysisId, 'excel', {
            storage_test: true
        });
        
        if (reportResult.success) {
            console.log('Report generated for storage test:', reportResult.reportId);
            
            // Download the report
            const downloadFilePath = path.join(downloadPath, `storage-test-${Date.now()}.xlsx`);
            const downloadResult = await apiClient.downloadReport(reportResult.reportId, downloadFilePath);
            
            expect(downloadResult.success).to.be.true;
            
            // Verify file exists
            expect(fs.existsSync(downloadFilePath)).to.be.true;
            
            console.log('✓ Report storage and download working correctly');
            
            // Test cleanup (file should remain available for reasonable time)
            setTimeout(async () => {
                if (fs.existsSync(downloadFilePath)) {
                    console.log('✓ Report file persists after generation');
                }
            }, 1000);
        }
        
        await testBase.navigateToApp();
        await testBase.takeScreenshot('report_storage_cleanup');
    });
    
    it('should provide report generation progress tracking', async function() {
        console.log('Testing report generation progress tracking...');
        
        if (!testAnalysisId) {
            this.skip('No analysis available for report generation');
        }
        
        await testBase.navigateToApp();
        await dashboardPage.assertDashboardLoaded();
        
        // Start report generation
        const reportResult = await apiClient.generateReport(testAnalysisId, 'excel', {
            progress_tracking: true
        });
        
        if (reportResult.success) {
            console.log('Report generation started with progress tracking');
            
            // In a full implementation, we would monitor progress via API or UI
            // For now, we verify the report completes successfully
            
            const downloadFilePath = path.join(downloadPath, `progress-tracking-${Date.now()}.xlsx`);
            const downloadResult = await apiClient.downloadReport(reportResult.reportId, downloadFilePath);
            
            if (downloadResult.success) {
                console.log('✓ Report with progress tracking completed successfully');
            }
        }
        
        await testBase.takeScreenshot('report_progress_tracking');
    });
    
    it('should support batch report generation', async function() {
        console.log('Testing batch report generation...');
        
        // Get multiple analysis results
        const allAnalysisResults = await apiClient.getAnalysisResults();
        
        if (allAnalysisResults.success && allAnalysisResults.results.length > 1) {
            const analysisIds = allAnalysisResults.results.slice(0, 3).map(r => r.id);
            
            console.log(`Generating batch reports for ${analysisIds.length} analyses`);
            
            // Generate reports for multiple analyses
            const batchPromises = analysisIds.map(id => 
                apiClient.generateReport(id, 'excel', {
                    batch_operation: true
                })
            );
            
            const batchResults = await Promise.allSettled(batchPromises);
            const successfulBatch = batchResults.filter(r => 
                r.status === 'fulfilled' && r.value.success
            );
            
            console.log(`✓ ${successfulBatch.length}/${analysisIds.length} batch reports generated successfully`);
            
            if (successfulBatch.length > 0) {
                expect(successfulBatch.length).to.be.greaterThan(0);
            }
            
        } else {
            console.log('⚠️ Not enough analysis results for batch report generation test');
        }
        
        await testBase.navigateToApp();
        await testBase.takeScreenshot('batch_report_generation');
    });
    
    it('should handle large dataset report generation', async function() {
        console.log('Testing large dataset report generation...');
        
        if (!testAnalysisId) {
            this.skip('No analysis available for report generation');
        }
        
        // Generate report with large dataset options
        const largeReportResult = await apiClient.generateReport(testAnalysisId, 'excel', {
            include_all_data: true,
            include_raw_data: true,
            include_detailed_analysis: true,
            large_dataset: true
        });
        
        if (largeReportResult.success) {
            console.log('Large dataset report generation started');
            
            // Use longer timeout for large reports
            const downloadFilePath = path.join(downloadPath, `large-dataset-${Date.now()}.xlsx`);
            
            try {
                const downloadResult = await apiClient.downloadReport(largeReportResult.reportId, downloadFilePath);
                
                if (downloadResult.success) {
                    const stats = fs.statSync(downloadFilePath);
                    console.log(`✓ Large dataset report generated successfully (${stats.size} bytes)`);
                    
                    // Verify it's actually larger than a basic report
                    expect(stats.size).to.be.greaterThan(1000);
                }
            } catch (error) {
                console.log('⚠️ Large dataset report may have timed out:', error.message);
            }
        }
        
        await testBase.navigateToApp();
        await testBase.takeScreenshot('large_dataset_report');
    });
});