#!/usr/bin/env node

/**
 * E2E Test Runner for Contract Analyzer
 * 
 * Comprehensive test runner that executes E2E tests with proper setup,
 * reporting, and cleanup. Supports multiple execution modes and environments.
 */

const path = require('path');
const fs = require('fs-extra');
const { spawn } = require('child_process');
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');
const chalk = require('chalk');
const moment = require('moment');

// Import configuration
const testConfig = require('./config/test.config');
const puppeteerConfig = require('./config/puppeteer.config');
const ApiClient = require('./framework/ApiClient');

class E2ETestRunner {
    constructor(options = {}) {
        this.options = {
            headless: options.headless !== false, // Default to headless
            debug: options.debug || false,
            environment: options.environment || 'development',
            testType: options.testType || 'integration',
            scenario: options.scenario || null, // Run specific scenario
            parallel: options.parallel || false,
            maxConcurrency: options.maxConcurrency || 2,
            timeout: options.timeout || 300000, // 5 minutes default
            retries: options.retries || 1,
            cleanup: options.cleanup !== false, // Default to cleanup
            setupData: options.setupData !== false, // Default to setup test data
            generateReport: options.generateReport !== false,
            ...options
        };
        
        this.results = {
            total: 0,
            passed: 0,
            failed: 0,
            skipped: 0,
            duration: 0,
            tests: []
        };
        
        this.startTime = Date.now();
        this.apiClient = new ApiClient(this.options.environment);
    }
    
    /**
     * Main test execution entry point
     */
    async run() {
        console.log(chalk.blue.bold('\n🧪 Contract Analyzer E2E Test Suite\n'));
        
        try {
            // Pre-test setup
            await this.preTestSetup();
            
            // Execute tests
            await this.executeTests();
            
            // Post-test cleanup
            await this.postTestCleanup();
            
            // Generate report
            if (this.options.generateReport) {
                await this.generateTestReport();
            }
            
            // Print summary
            this.printTestSummary();
            
            // Exit with appropriate code
            process.exit(this.results.failed > 0 ? 1 : 0);
            
        } catch (error) {
            console.error(chalk.red.bold('\n❌ Test runner failed:'), error.message);
            console.error(error.stack);
            process.exit(1);
        }
    }
    
    /**
     * Pre-test setup and validation
     */
    async preTestSetup() {
        console.log(chalk.yellow('📋 Setting up test environment...'));
        
        // Create necessary directories
        puppeteerConfig.createDirectories();
        
        // Verify API is available
        await this.verifyApiAvailability();
        
        // Set up test data if requested
        if (this.options.setupData) {
            await this.setupTestData();
        }
        
        // Install dependencies if needed
        await this.ensureDependencies();
        
        console.log(chalk.green('✅ Pre-test setup completed\n'));
    }
    
    /**
     * Verify API availability before running tests
     */
    async verifyApiAvailability() {
        console.log(chalk.blue('🔍 Checking API availability...'));
        
        const healthCheck = await this.apiClient.checkHealth();
        
        if (!healthCheck.healthy) {
            const message = `API not available at ${testConfig.getBaseUrl()}`;
            console.error(chalk.red(`❌ ${message}`));
            
            if (healthCheck.status === 0) {
                console.error(chalk.red('   Could not connect to server. Is it running?'));
            } else {
                console.error(chalk.red(`   Server responded with status ${healthCheck.status}`));
            }
            
            throw new Error(message);
        }
        
        console.log(chalk.green('✅ API is healthy and available'));
    }
    
    /**
     * Set up test data
     */
    async setupTestData() {
        console.log(chalk.blue('📁 Setting up test data...'));
        
        const setupResult = await this.apiClient.setupTestData();
        
        if (!setupResult.success) {
            console.warn(chalk.yellow(`⚠️ Test data setup failed: ${setupResult.error}`));
        } else {
            console.log(chalk.green(`✅ Test data setup completed`));
        }
    }
    
    /**
     * Ensure dependencies are installed
     */
    async ensureDependencies() {
        const nodeModulesPath = path.join(__dirname, 'node_modules');
        
        if (!fs.existsSync(nodeModulesPath)) {
            console.log(chalk.blue('📦 Installing dependencies...'));
            
            await this.runCommand('npm', ['install'], { cwd: __dirname });
            
            console.log(chalk.green('✅ Dependencies installed'));
        }
    }
    
    /**
     * Execute the actual tests
     */
    async executeTests() {
        console.log(chalk.yellow('🚀 Executing E2E tests...'));
        
        // Determine which tests to run
        const testFiles = await this.getTestFiles();
        
        if (testFiles.length === 0) {
            console.warn(chalk.yellow('⚠️ No test files found to execute'));
            return;
        }
        
        console.log(chalk.blue(`📝 Found ${testFiles.length} test file(s) to execute:`));
        testFiles.forEach(file => {
            console.log(chalk.gray(`   - ${path.relative(__dirname, file)}`));
        });
        
        console.log('');
        
        // Set environment variables for tests
        this.setTestEnvironment();
        
        // Execute tests based on parallel vs sequential mode
        if (this.options.parallel && testFiles.length > 1) {
            await this.runTestsParallel(testFiles);
        } else {
            await this.runTestsSequential(testFiles);
        }
    }
    
    /**
     * Get list of test files to execute
     */
    async getTestFiles() {
        const scenariosDir = path.join(__dirname, 'scenarios');
        
        if (this.options.scenario) {
            // Run specific scenario
            const scenarioPath = path.join(scenariosDir, this.options.scenario);
            
            if (fs.existsSync(scenarioPath)) {
                const testFiles = await this.findTestFiles(scenarioPath);
                return testFiles;
            } else {
                throw new Error(`Scenario not found: ${this.options.scenario}`);
            }
        } else {
            // Run all scenarios
            const testFiles = await this.findTestFiles(scenariosDir);
            return testFiles;
        }
    }
    
    /**
     * Find test files recursively
     */
    async findTestFiles(directory) {
        const testFiles = [];
        
        if (!fs.existsSync(directory)) {
            return testFiles;
        }
        
        const files = await fs.readdir(directory);
        
        for (const file of files) {
            const filePath = path.join(directory, file);
            const stat = await fs.stat(filePath);
            
            if (stat.isDirectory()) {
                const subFiles = await this.findTestFiles(filePath);
                testFiles.push(...subFiles);
            } else if (file.endsWith('.test.js')) {
                testFiles.push(filePath);
            }
        }
        
        return testFiles;
    }
    
    /**
     * Set environment variables for test execution
     */
    setTestEnvironment() {
        // Set NODE_ENV
        process.env.NODE_ENV = this.options.environment;
        
        // Set test-specific environment variables
        process.env.E2E_TEST = 'true';
        process.env.TEST_HEADLESS = this.options.headless.toString();
        process.env.TEST_DEBUG = this.options.debug.toString();
        process.env.TEST_TIMEOUT = this.options.timeout.toString();
        process.env.TEST_RETRIES = this.options.retries.toString();
        
        // Set Puppeteer environment
        if (this.options.headless) {
            process.env.CI = 'true';
        }
    }
    
    /**
     * Run tests sequentially
     */
    async runTestsSequential(testFiles) {
        console.log(chalk.blue('🔄 Running tests sequentially...\n'));
        
        for (let i = 0; i < testFiles.length; i++) {
            const testFile = testFiles[i];
            const testName = path.relative(__dirname, testFile);
            
            console.log(chalk.blue(`\n[${i + 1}/${testFiles.length}] Running: ${testName}`));
            
            const result = await this.runSingleTest(testFile);
            this.recordTestResult(testName, result);
            
            // Brief pause between tests
            if (i < testFiles.length - 1) {
                await new Promise(resolve => setTimeout(resolve, 2000));
            }
        }
    }
    
    /**
     * Run tests in parallel
     */
    async runTestsParallel(testFiles) {
        console.log(chalk.blue(`🔄 Running tests in parallel (max ${this.options.maxConcurrency})...\n`));
        
        const chunks = this.chunkArray(testFiles, this.options.maxConcurrency);
        
        for (let chunkIndex = 0; chunkIndex < chunks.length; chunkIndex++) {
            const chunk = chunks[chunkIndex];
            
            console.log(chalk.blue(`\nBatch ${chunkIndex + 1}/${chunks.length}: Running ${chunk.length} tests in parallel`));
            
            const promises = chunk.map(async (testFile) => {
                const testName = path.relative(__dirname, testFile);
                const result = await this.runSingleTest(testFile);
                return { testName, result };
            });
            
            const results = await Promise.all(promises);
            
            results.forEach(({ testName, result }) => {
                this.recordTestResult(testName, result);
            });
            
            // Brief pause between batches
            if (chunkIndex < chunks.length - 1) {
                await new Promise(resolve => setTimeout(resolve, 3000));
            }
        }
    }
    
    /**
     * Run a single test file
     */
    async runSingleTest(testFile) {
        const testName = path.basename(testFile);
        const startTime = Date.now();
        
        try {
            await this.runCommand('npx', [
                'mocha',
                testFile,
                '--timeout', this.options.timeout.toString(),
                '--retries', this.options.retries.toString(),
                '--reporter', 'spec'
            ], {
                cwd: __dirname,
                stdio: this.options.debug ? 'inherit' : 'pipe'
            });
            
            const duration = Date.now() - startTime;
            console.log(chalk.green(`✅ ${testName} passed (${duration}ms)`));
            
            return {
                success: true,
                duration,
                error: null
            };
            
        } catch (error) {
            const duration = Date.now() - startTime;
            console.log(chalk.red(`❌ ${testName} failed (${duration}ms)`));
            
            if (this.options.debug) {
                console.error(chalk.red(error.message));
            }
            
            return {
                success: false,
                duration,
                error: error.message
            };
        }
    }
    
    /**
     * Record test result
     */
    recordTestResult(testName, result) {
        this.results.total++;
        this.results.duration += result.duration;
        
        if (result.success) {
            this.results.passed++;
        } else {
            this.results.failed++;
        }
        
        this.results.tests.push({
            name: testName,
            success: result.success,
            duration: result.duration,
            error: result.error
        });
    }
    
    /**
     * Post-test cleanup
     */
    async postTestCleanup() {
        if (!this.options.cleanup) {
            console.log(chalk.yellow('⚠️ Skipping cleanup as requested'));
            return;
        }
        
        console.log(chalk.yellow('\n🧹 Performing post-test cleanup...'));
        
        // Clean up test data
        await this.apiClient.cleanupTestData();
        
        // Clean up temporary files (but keep reports and screenshots for analysis)
        const tempDirs = [
            path.join(__dirname, 'temp/browser-data')
        ];
        
        for (const dir of tempDirs) {
            if (fs.existsSync(dir)) {
                await fs.remove(dir);
            }
        }
        
        console.log(chalk.green('✅ Post-test cleanup completed'));
    }
    
    /**
     * Generate test report
     */
    async generateTestReport() {
        console.log(chalk.yellow('📊 Generating test report...'));
        
        const reportPath = path.join(__dirname, 'temp/reports', `e2e-test-report-${Date.now()}.json`);
        
        const report = {
            timestamp: moment().toISOString(),
            environment: this.options.environment,
            configuration: this.options,
            results: this.results,
            duration: Date.now() - this.startTime
        };
        
        await fs.ensureDir(path.dirname(reportPath));
        await fs.writeJson(reportPath, report, { spaces: 2 });
        
        console.log(chalk.green(`✅ Test report generated: ${reportPath}`));
    }
    
    /**
     * Print test summary
     */
    printTestSummary() {
        const duration = Date.now() - this.startTime;
        
        console.log(chalk.blue.bold('\n📋 Test Summary'));
        console.log(chalk.gray('='.repeat(50)));
        
        console.log(chalk.blue(`Total Tests: ${this.results.total}`));
        console.log(chalk.green(`Passed: ${this.results.passed}`));
        console.log(chalk.red(`Failed: ${this.results.failed}`));
        console.log(chalk.yellow(`Skipped: ${this.results.skipped}`));
        console.log(chalk.blue(`Total Duration: ${duration}ms`));
        
        if (this.results.failed > 0) {
            console.log(chalk.red.bold('\n❌ Failed Tests:'));
            this.results.tests.forEach(test => {
                if (!test.success) {
                    console.log(chalk.red(`  - ${test.name}: ${test.error}`));
                }
            });
        }
        
        console.log(chalk.gray('='.repeat(50)));
        
        if (this.results.failed === 0) {
            console.log(chalk.green.bold('🎉 All tests passed!'));
        } else {
            console.log(chalk.red.bold('💥 Some tests failed!'));
        }
    }
    
    /**
     * Run command with promise
     */
    runCommand(command, args = [], options = {}) {
        return new Promise((resolve, reject) => {
            const child = spawn(command, args, {
                stdio: 'pipe',
                shell: process.platform === 'win32',
                ...options
            });
            
            let stdout = '';
            let stderr = '';
            
            if (child.stdout) {
                child.stdout.on('data', (data) => {
                    stdout += data.toString();
                    if (options.stdio === 'inherit') {
                        process.stdout.write(data);
                    }
                });
            }
            
            if (child.stderr) {
                child.stderr.on('data', (data) => {
                    stderr += data.toString();
                    if (options.stdio === 'inherit') {
                        process.stderr.write(data);
                    }
                });
            }
            
            child.on('close', (code) => {
                if (code === 0) {
                    resolve({ stdout, stderr, code });
                } else {
                    const error = new Error(`Command failed with exit code ${code}`);
                    error.stdout = stdout;
                    error.stderr = stderr;
                    error.code = code;
                    reject(error);
                }
            });
            
            child.on('error', (error) => {
                reject(error);
            });
        });
    }
    
    /**
     * Split array into chunks
     */
    chunkArray(array, chunkSize) {
        const chunks = [];
        for (let i = 0; i < array.length; i += chunkSize) {
            chunks.push(array.slice(i, i + chunkSize));
        }
        return chunks;
    }
}

// Command line interface
const argv = yargs(hideBin(process.argv))
    .command('$0', 'Run E2E tests for Contract Analyzer')
    .option('headless', {
        type: 'boolean',
        default: true,
        describe: 'Run tests in headless mode'
    })
    .option('debug', {
        type: 'boolean',
        default: false,
        describe: 'Enable debug mode'
    })
    .option('environment', {
        type: 'string',
        default: 'development',
        choices: ['development', 'staging', 'ci'],
        describe: 'Test environment'
    })
    .option('scenario', {
        type: 'string',
        describe: 'Run specific scenario (e.g., "contract-workflow")'
    })
    .option('parallel', {
        type: 'boolean',
        default: false,
        describe: 'Run tests in parallel'
    })
    .option('max-concurrency', {
        type: 'number',
        default: 2,
        describe: 'Maximum concurrent tests when running in parallel'
    })
    .option('timeout', {
        type: 'number',
        default: 300000,
        describe: 'Test timeout in milliseconds'
    })
    .option('retries', {
        type: 'number',
        default: 1,
        describe: 'Number of retries for failed tests'
    })
    .option('no-cleanup', {
        type: 'boolean',
        default: false,
        describe: 'Skip post-test cleanup'
    })
    .option('no-setup-data', {
        type: 'boolean',
        default: false,
        describe: 'Skip test data setup'
    })
    .option('no-report', {
        type: 'boolean',
        default: false,
        describe: 'Skip test report generation'
    })
    .help()
    .argv;

// Convert CLI args to options
const options = {
    headless: argv.headless && !argv.debug, // Force headed mode in debug
    debug: argv.debug,
    environment: argv.environment,
    scenario: argv.scenario,
    parallel: argv.parallel,
    maxConcurrency: argv['max-concurrency'],
    timeout: argv.timeout,
    retries: argv.retries,
    cleanup: !argv['no-cleanup'],
    setupData: !argv['no-setup-data'],
    generateReport: !argv['no-report']
};

// Run the tests
const runner = new E2ETestRunner(options);
runner.run().catch(error => {
    console.error(chalk.red.bold('Fatal error:'), error);
    process.exit(1);
});

module.exports = E2ETestRunner;