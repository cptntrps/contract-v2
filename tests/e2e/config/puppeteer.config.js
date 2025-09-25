/**
 * Puppeteer Configuration for Contract Analyzer E2E Tests
 * 
 * Comprehensive browser configuration for different testing scenarios
 * including development, CI/CD, and performance testing.
 */

const path = require('path');

class PuppeteerConfig {
    constructor() {
        this.baseConfig = {
            // Browser launch options
            headless: process.env.CI ? 'new' : false, // Use new headless mode in CI
            defaultViewport: {
                width: 1920,
                height: 1080
            },
            
            // Performance and stability options
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage', // Overcome limited resource problems
                '--disable-gpu',
                '--disable-extensions',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--enable-features=NetworkService,NetworkServiceLogging',
                '--force-color-profile=srgb',
                '--metrics-recording-only',
                '--use-mock-keychain',
                '--no-first-run'
            ],
            
            // Timeout settings
            slowMo: process.env.DEBUG ? 100 : 0, // Slow down operations in debug mode
            
            // Download handling
            downloadPath: path.join(__dirname, '../temp/downloads'),
            
            // User agent
            userAgent: 'Contract-Analyzer-E2E-Tests/1.0'
        };
        
        this.environments = {
            development: {
                baseURL: 'http://localhost:5000',
                timeout: 30000,
                retries: 2,
                slowMo: 50
            },
            
            staging: {
                baseURL: process.env.STAGING_URL || 'http://staging.contractanalyzer.local',
                timeout: 60000,
                retries: 3,
                slowMo: 0
            },
            
            ci: {
                baseURL: 'http://localhost:5000',
                timeout: 120000, // Longer timeout for CI
                retries: 3,
                slowMo: 0,
                headless: 'new',
                args: [
                    ...this.baseConfig.args,
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            }
        };
        
        this.testTypes = {
            smoke: {
                timeout: 15000,
                retries: 1,
                parallel: false
            },
            
            integration: {
                timeout: 60000,
                retries: 2,
                parallel: true,
                maxConcurrency: 2
            },
            
            performance: {
                timeout: 180000, // 3 minutes for performance tests
                retries: 1,
                parallel: false,
                networkConditions: {
                    offline: false,
                    downloadThroughput: 1.5 * 1024 * 1024 / 8, // 1.5 Mbps
                    uploadThroughput: 750 * 1024 / 8, // 750 Kbps
                    latency: 40 // 40ms RTT
                }
            },
            
            visual: {
                timeout: 30000,
                retries: 1,
                parallel: false,
                fullPage: true,
                screenshotOptions: {
                    fullPage: true,
                    type: 'png'
                }
            }
        };
    }
    
    /**
     * Get configuration for specific environment and test type
     */
    getConfig(environment = 'development', testType = 'integration') {
        const envConfig = this.environments[environment] || this.environments.development;
        const typeConfig = this.testTypes[testType] || this.testTypes.integration;
        
        return {
            ...this.baseConfig,
            ...envConfig,
            ...typeConfig,
            
            // Merge args if both exist
            args: [
                ...this.baseConfig.args,
                ...(envConfig.args || []),
                ...(typeConfig.args || [])
            ]
        };
    }
    
    /**
     * Get browser launch options
     */
    getLaunchOptions(environment, testType) {
        const config = this.getConfig(environment, testType);
        
        return {
            headless: config.headless,
            defaultViewport: config.defaultViewport,
            args: config.args,
            slowMo: config.slowMo,
            timeout: config.timeout,
            userDataDir: process.env.DEBUG ? undefined : path.join(__dirname, '../temp/browser-data')
        };
    }
    
    /**
     * Get page configuration options
     */
    getPageOptions(environment, testType) {
        const config = this.getConfig(environment, testType);
        
        return {
            timeout: config.timeout,
            baseURL: config.baseURL,
            retries: config.retries,
            screenshotOptions: config.screenshotOptions || {},
            networkConditions: config.networkConditions
        };
    }
    
    /**
     * Get download configuration
     */
    getDownloadConfig() {
        return {
            downloadPath: this.baseConfig.downloadPath,
            acceptDownloads: true,
            downloadTimeout: 60000 // 1 minute for downloads
        };
    }
    
    /**
     * Get screenshot configuration
     */
    getScreenshotConfig(testType = 'integration') {
        const config = this.testTypes[testType];
        
        return {
            path: path.join(__dirname, '../temp/screenshots'),
            fullPage: config.fullPage || false,
            type: 'png'
            // Note: PNG doesn't support quality parameter
        };
    }
    
    /**
     * Get performance monitoring configuration
     */
    getPerformanceConfig() {
        return {
            collectMetrics: true,
            collectTrace: process.env.PERFORMANCE_TRACE === 'true',
            tracePath: path.join(__dirname, '../temp/traces'),
            metricsPath: path.join(__dirname, '../temp/metrics'),
            thresholds: {
                firstContentfulPaint: 2000, // 2 seconds
                largestContentfulPaint: 4000, // 4 seconds
                firstInputDelay: 100, // 100ms
                cumulativeLayoutShift: 0.1
            }
        };
    }
    
    /**
     * Create directories for test artifacts
     */
    createDirectories() {
        const dirs = [
            path.join(__dirname, '../temp'),
            path.join(__dirname, '../temp/downloads'),
            path.join(__dirname, '../temp/screenshots'),
            path.join(__dirname, '../temp/traces'),
            path.join(__dirname, '../temp/metrics'),
            path.join(__dirname, '../temp/browser-data'),
            path.join(__dirname, '../temp/reports')
        ];
        
        const fs = require('fs-extra');
        dirs.forEach(dir => {
            fs.ensureDirSync(dir);
        });
    }
    
    /**
     * Clean up temporary directories
     */
    cleanupDirectories() {
        const fs = require('fs-extra');
        const tempDir = path.join(__dirname, '../temp');
        
        if (fs.existsSync(tempDir)) {
            fs.removeSync(tempDir);
        }
    }
}

module.exports = new PuppeteerConfig();