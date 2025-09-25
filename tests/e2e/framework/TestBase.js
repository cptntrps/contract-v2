/**
 * Base Test Class for Contract Analyzer E2E Tests
 * 
 * Provides common functionality for all E2E tests including browser management,
 * page interactions, assertions, and error handling.
 */

const puppeteer = require('puppeteer');
const puppeteerExtra = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs-extra');
const path = require('path');
const { expect } = require('chai');

// Configure puppeteer with stealth plugin
puppeteerExtra.use(StealthPlugin());

const puppeteerConfig = require('../config/puppeteer.config');
const testConfig = require('../config/test.config');

class TestBase {
    constructor(testType = 'integration', environment = 'development') {
        this.testType = testType;
        this.environment = environment;
        this.browser = null;
        this.page = null;
        this.context = null;
        
        this.config = testConfig;
        this.puppeteerConfig = puppeteerConfig;
        
        this.screenshots = [];
        this.logs = [];
        this.performanceMetrics = [];
        
        this.retryCount = 0;
        this.maxRetries = this.config.getRetryConfig().maxRetries;
    }
    
    /**
     * Initialize browser and page
     */
    async setup() {
        console.log(`TestBase: Setting up browser for ${this.testType} test in ${this.environment}...`);
        
        try {
            // Ensure temp directories exist
            this.puppeteerConfig.createDirectories();
            
            // Launch browser with appropriate configuration
            const launchOptions = this.puppeteerConfig.getLaunchOptions(this.environment, this.testType);
            this.browser = await puppeteerExtra.launch(launchOptions);
            
            // Create new page
            this.page = await this.browser.newPage();
            
            // Configure page
            await this.configurePage();
            
            // Set up event listeners
            this.setupPageEventListeners();
            
            console.log('TestBase: Browser setup completed successfully');
            
        } catch (error) {
            console.error('TestBase: Browser setup failed:', error);
            await this.cleanup();
            throw error;
        }
    }
    
    /**
     * Configure page settings and handlers
     */
    async configurePage() {
        const pageOptions = this.puppeteerConfig.getPageOptions(this.environment, this.testType);
        
        // Set viewport
        await this.page.setViewport(this.puppeteerConfig.baseConfig.defaultViewport);
        
        // Set user agent
        await this.page.setUserAgent(this.puppeteerConfig.baseConfig.userAgent);
        
        // Configure timeouts
        this.page.setDefaultTimeout(pageOptions.timeout);
        this.page.setDefaultNavigationTimeout(pageOptions.timeout);
        
        // Configure download handling
        const downloadConfig = this.puppeteerConfig.getDownloadConfig();
        try {
            const client = await this.page.target().createCDPSession();
            await client.send('Page.setDownloadBehavior', {
                behavior: 'allow',
                downloadPath: downloadConfig.downloadPath
            });
        } catch (error) {
            console.warn('TestBase: Download configuration skipped:', error.message);
        }
        
        // Set network conditions for performance tests
        if (pageOptions.networkConditions) {
            await this.page.emulateNetworkConditions(pageOptions.networkConditions);
        }
        
        // Enable JavaScript
        await this.page.setJavaScriptEnabled(true);
    }
    
    /**
     * Set up page event listeners for monitoring
     */
    setupPageEventListeners() {
        // Log console messages
        this.page.on('console', (msg) => {
            const logEntry = {
                timestamp: new Date().toISOString(),
                type: msg.type(),
                text: msg.text(),
                location: msg.location()
            };
            this.logs.push(logEntry);
            
            // Also log to console in debug mode
            if (this.config.isDebugMode()) {
                console.log(`Browser ${msg.type()}: ${msg.text()}`);
            }
        });
        
        // Log page errors
        this.page.on('pageerror', (error) => {
            const errorEntry = {
                timestamp: new Date().toISOString(),
                type: 'pageerror',
                message: error.message,
                stack: error.stack
            };
            this.logs.push(errorEntry);
            console.error('Page Error:', error);
        });
        
        // Log network failures
        this.page.on('requestfailed', (request) => {
            const failureEntry = {
                timestamp: new Date().toISOString(),
                type: 'requestfailed',
                url: request.url(),
                method: request.method(),
                failure: request.failure()?.errorText
            };
            this.logs.push(failureEntry);
            console.warn('Request Failed:', failureEntry);
        });
        
        // Monitor response times
        this.page.on('response', (response) => {
            if (response.url().includes('/api/')) {
                const responseEntry = {
                    timestamp: new Date().toISOString(),
                    url: response.url(),
                    status: response.status(),
                    responseTime: Date.now() - response.request().timestamp
                };
                this.performanceMetrics.push(responseEntry);
            }
        });
    }
    
    /**
     * Navigate to application URL
     */
    async navigateToApp() {
        const baseUrl = this.config.getBaseUrl();
        console.log(`TestBase: Navigating to ${baseUrl}`);
        
        await this.page.goto(baseUrl, {
            waitUntil: 'networkidle2',
            timeout: this.config.getTimeout('pageLoad')
        });
        
        // Wait for application to initialize
        await this.waitForApplicationReady();
    }
    
    /**
     * Wait for application to be fully initialized
     */
    async waitForApplicationReady() {
        console.log('TestBase: Waiting for application to be ready...');
        
        try {
            // Wait for core application object to be available
            await this.page.waitForFunction(
                () => window.ContractApp && window.ContractApp.initialized === true,
                { timeout: this.config.getTimeout('pageLoad') }
            );
            
            // Wait for dashboard to be visible (default tab)
            await this.page.waitForSelector(
                this.config.getSelector('dashboardContainer'),
                { visible: true, timeout: this.config.getTimeout('elementVisible') }
            );
            
            console.log('TestBase: Application is ready');
            
        } catch (error) {
            console.error('TestBase: Application failed to become ready:', error);
            await this.takeScreenshot('application_not_ready');
            throw error;
        }
    }
    
    /**
     * Take screenshot with automatic naming
     */
    async takeScreenshot(name = null) {
        if (!name) {
            name = `screenshot_${Date.now()}`;
        }
        
        const screenshotConfig = this.puppeteerConfig.getScreenshotConfig(this.testType);
        const screenshotPath = path.join(screenshotConfig.path, `${name}.png`);
        
        try {
            await this.page.screenshot({
                path: screenshotPath,
                fullPage: screenshotConfig.fullPage,
                type: screenshotConfig.type,
                quality: screenshotConfig.quality
            });
            
            this.screenshots.push(screenshotPath);
            console.log(`TestBase: Screenshot saved: ${screenshotPath}`);
            
        } catch (error) {
            console.error('TestBase: Failed to take screenshot:', error);
        }
    }
    
    /**
     * Wait for element with retry logic
     */
    async waitForElement(selector, options = {}) {
        const defaultOptions = {
            visible: true,
            timeout: this.config.getTimeout('elementVisible')
        };
        const waitOptions = { ...defaultOptions, ...options };
        
        const retryConfig = this.config.getRetryConfig();
        let lastError;
        
        for (let attempt = 0; attempt <= retryConfig.maxRetries; attempt++) {
            try {
                await this.page.waitForSelector(selector, waitOptions);
                return;
                
            } catch (error) {
                lastError = error;
                
                if (attempt < retryConfig.maxRetries) {
                    console.log(`TestBase: Retry ${attempt + 1}/${retryConfig.maxRetries} for selector: ${selector}`);
                    
                    const delay = retryConfig.exponentialBackoff 
                        ? retryConfig.retryDelay * Math.pow(2, attempt)
                        : retryConfig.retryDelay;
                    
                    await this.sleep(delay);
                }
            }
        }
        
        throw lastError;
    }
    
    /**
     * Click element with retry logic
     */
    async clickElement(selector, options = {}) {
        await this.waitForElement(selector, { visible: true });
        
        const retryConfig = this.config.getRetryConfig();
        let lastError;
        
        for (let attempt = 0; attempt <= retryConfig.maxRetries; attempt++) {
            try {
                await this.page.click(selector, options);
                return;
                
            } catch (error) {
                lastError = error;
                
                if (attempt < retryConfig.maxRetries) {
                    console.log(`TestBase: Retry click ${attempt + 1}/${retryConfig.maxRetries} for: ${selector}`);
                    await this.sleep(retryConfig.retryDelay);
                }
            }
        }
        
        throw lastError;
    }
    
    /**
     * Fill input field with retry logic
     */
    async fillInput(selector, value, options = {}) {
        await this.waitForElement(selector, { visible: true });
        
        const retryConfig = this.config.getRetryConfig();
        let lastError;
        
        for (let attempt = 0; attempt <= retryConfig.maxRetries; attempt++) {
            try {
                await this.page.focus(selector);
                await this.page.keyboard.down('Control');
                await this.page.keyboard.press('KeyA');
                await this.page.keyboard.up('Control');
                await this.page.type(selector, value, options);
                return;
                
            } catch (error) {
                lastError = error;
                
                if (attempt < retryConfig.maxRetries) {
                    console.log(`TestBase: Retry fill ${attempt + 1}/${retryConfig.maxRetries} for: ${selector}`);
                    await this.sleep(retryConfig.retryDelay);
                }
            }
        }
        
        throw lastError;
    }
    
    /**
     * Upload file to input element
     */
    async uploadFile(selector, filePath) {
        await this.waitForElement(selector);
        
        // Check if file exists
        if (!fs.existsSync(filePath)) {
            throw new Error(`Upload file not found: ${filePath}`);
        }
        
        const input = await this.page.$(selector);
        await input.uploadFile(filePath);
        
        console.log(`TestBase: File uploaded: ${filePath}`);
    }
    
    /**
     * Wait for download to complete
     */
    async waitForDownload(timeout = null) {
        timeout = timeout || this.puppeteerConfig.getDownloadConfig().downloadTimeout;
        
        return new Promise((resolve, reject) => {
            const downloadPath = this.puppeteerConfig.getDownloadConfig().downloadPath;
            const checkInterval = 1000; // Check every second
            const maxChecks = Math.floor(timeout / checkInterval);
            let checks = 0;
            
            const checkDownload = () => {
                checks++;
                
                if (checks > maxChecks) {
                    reject(new Error('Download timeout exceeded'));
                    return;
                }
                
                fs.readdir(downloadPath, (err, files) => {
                    if (err) {
                        reject(err);
                        return;
                    }
                    
                    // Look for completed downloads (not .crdownload or .tmp files)
                    const completedFiles = files.filter(file => 
                        !file.endsWith('.crdownload') && 
                        !file.endsWith('.tmp') &&
                        !file.startsWith('.')
                    );
                    
                    if (completedFiles.length > 0) {
                        resolve(completedFiles[completedFiles.length - 1]); // Return latest file
                    } else {
                        setTimeout(checkDownload, checkInterval);
                    }
                });
            };
            
            checkDownload();
        });
    }
    
    /**
     * Assert element text content
     */
    async assertElementText(selector, expectedText, options = {}) {
        await this.waitForElement(selector);
        
        const element = await this.page.$(selector);
        const actualText = await element.evaluate(el => el.textContent.trim());
        
        if (options.contains) {
            expect(actualText).to.include(expectedText);
        } else {
            expect(actualText).to.equal(expectedText);
        }
    }
    
    /**
     * Assert element is visible
     */
    async assertElementVisible(selector) {
        await this.waitForElement(selector, { visible: true });
        const isVisible = await this.page.$(selector) !== null;
        expect(isVisible).to.be.true;
    }
    
    /**
     * Assert element is hidden
     */
    async assertElementHidden(selector) {
        const element = await this.page.$(selector);
        if (element) {
            const isVisible = await element.isIntersectingViewport();
            expect(isVisible).to.be.false;
        }
        // Element not existing is also considered "hidden"
    }
    
    /**
     * Sleep for specified milliseconds
     */
    async sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    /**
     * Get performance metrics
     */
    getPerformanceMetrics() {
        return {
            screenshots: this.screenshots,
            logs: this.logs,
            performanceMetrics: this.performanceMetrics,
            testDuration: Date.now() - this.testStartTime
        };
    }
    
    /**
     * Clean up browser resources
     */
    async cleanup() {
        console.log('TestBase: Cleaning up browser resources...');
        
        try {
            if (this.page && !this.page.isClosed()) {
                await this.page.close();
            }
            
            if (this.browser) {
                await this.browser.close();
            }
            
            console.log('TestBase: Cleanup completed');
            
        } catch (error) {
            console.error('TestBase: Error during cleanup:', error);
        }
    }
    
    /**
     * Run test with automatic setup and cleanup
     */
    async runTest(testFunction) {
        this.testStartTime = Date.now();
        
        try {
            await this.setup();
            await this.navigateToApp();
            
            // Run the actual test
            await testFunction.call(this);
            
            console.log('TestBase: Test completed successfully');
            
        } catch (error) {
            console.error('TestBase: Test failed:', error);
            await this.takeScreenshot('test_failure');
            throw error;
            
        } finally {
            await this.cleanup();
        }
    }
}

module.exports = TestBase;