#!/usr/bin/env node

/**
 * Visual Demo Test Runner
 * 
 * Dedicated script to run the visual analysis demo with optimized settings
 * for demonstration purposes. This script ensures the browser window is visible
 * and provides the best viewing experience for the complete workflow.
 */

const path = require('path');
const fs = require('fs-extra');
const { spawn } = require('child_process');
const chalk = require('chalk');

class VisualDemoRunner {
    constructor() {
        this.testDir = __dirname;
        this.demoTestFile = path.join(__dirname, 'scenarios/visual-demo/visual-analysis-demo.test.js');
        
        // Demo configuration
        this.config = {
            headless: false,
            slowMo: 500,
            devtools: false,
            timeout: 600000, // 10 minutes
            viewport: {
                width: 1280,
                height: 720
            }
        };
    }
    
    /**
     * Main execution entry point
     */
    async run() {
        console.log(chalk.blue.bold('\n🎬 Contract Analyzer Visual Demo'));
        console.log(chalk.blue.bold('=' .repeat(50)));
        console.log(chalk.yellow('\n📋 Demo Configuration:'));
        console.log(chalk.gray('   • Browser: Visible (non-headless)'));
        console.log(chalk.gray('   • Speed: Slow motion for visibility'));
        console.log(chalk.gray('   • Timeout: 10 minutes'));
        console.log(chalk.gray('   • Screenshots: Enabled'));
        console.log(chalk.gray('   • Report Downloads: Enabled'));
        
        try {
            // Pre-demo setup
            await this.setup();
            
            // Run the visual demo
            await this.runDemo();
            
            // Post-demo information
            this.showResults();
            
        } catch (error) {
            console.error(chalk.red.bold('\n❌ Demo failed:'), error.message);
            console.error(chalk.gray(error.stack));
            process.exit(1);
        }
    }
    
    /**
     * Setup demo environment
     */
    async setup() {
        console.log(chalk.yellow('\n🔧 Setting up demo environment...'));
        
        // Ensure test file exists
        if (!fs.existsSync(this.demoTestFile)) {
            throw new Error(`Demo test file not found: ${this.demoTestFile}`);
        }
        
        // Create necessary directories
        const dirs = [
            path.join(this.testDir, 'temp/downloads'),
            path.join(this.testDir, 'temp/screenshots'),
            path.join(this.testDir, 'temp/reports')
        ];
        
        for (const dir of dirs) {
            await fs.ensureDir(dir);
            console.log(chalk.green(`   ✓ Created directory: ${path.relative(this.testDir, dir)}`));
        }
        
        // Check if contract analyzer is running
        console.log(chalk.blue('\n🔍 Checking Contract Analyzer availability...'));
        
        try {
            const ApiClient = require('./framework/ApiClient');
            const apiClient = new ApiClient('development');
            const healthCheck = await apiClient.checkHealth();
            
            if (healthCheck.healthy) {
                console.log(chalk.green('   ✓ Contract Analyzer is running and healthy'));
            } else {
                console.log(chalk.yellow('   ⚠️  Contract Analyzer may not be running'));
                console.log(chalk.yellow('   Please ensure the application is started before running the demo'));
                console.log(chalk.gray('   Run: python start_dashboard.py'));
            }
        } catch (error) {
            console.log(chalk.yellow('   ⚠️  Could not verify Contract Analyzer status'));
            console.log(chalk.gray('   Make sure the application is running: python start_dashboard.py'));
        }
        
        // Ensure dependencies are installed
        await this.ensureDependencies();
        
        console.log(chalk.green('\n✅ Demo setup completed'));
    }
    
    /**
     * Ensure test dependencies are installed
     */
    async ensureDependencies() {
        const nodeModulesPath = path.join(this.testDir, 'node_modules');
        
        if (!fs.existsSync(nodeModulesPath)) {
            console.log(chalk.blue('📦 Installing test dependencies...'));
            
            await this.runCommand('npm', ['install'], { cwd: this.testDir });
            
            console.log(chalk.green('   ✓ Dependencies installed'));
        } else {
            console.log(chalk.green('   ✓ Dependencies already installed'));
        }
    }
    
    /**
     * Run the visual demo
     */
    async runDemo() {
        console.log(chalk.blue.bold('\n🚀 Starting Visual Demo...'));
        console.log(chalk.blue.bold('=' .repeat(50)));
        
        // Set environment variables for the test
        process.env.NODE_ENV = 'development';
        process.env.E2E_TEST = 'true';
        process.env.TEST_HEADLESS = 'false';
        process.env.TEST_DEBUG = 'true';
        process.env.TEST_TIMEOUT = this.config.timeout.toString();
        process.env.VISUAL_DEMO = 'true';
        
        // Prepare demo instructions
        this.showDemoInstructions();
        
        // Run the test
        const mochaArgs = [
            'mocha',
            this.demoTestFile,
            '--timeout', this.config.timeout.toString(),
            '--reporter', 'spec',
            '--bail', // Stop on first failure
            '--slow', '10000' // Mark tests as slow after 10s
        ];
        
        console.log(chalk.blue('\n🎭 Launching demo test...'));
        console.log(chalk.gray(`Command: npx ${mochaArgs.join(' ')}\n`));
        
        await this.runCommand('npx', mochaArgs, {
            cwd: this.testDir,
            stdio: 'inherit'
        });
        
        console.log(chalk.green.bold('\n🎉 Visual demo completed successfully!'));
    }
    
    /**
     * Show demo instructions
     */
    showDemoInstructions() {
        console.log(chalk.cyan.bold('\n📖 Demo Instructions:'));
        console.log(chalk.cyan('=' .repeat(30)));
        console.log(chalk.white('1. A browser window will open automatically'));
        console.log(chalk.white('2. The test will navigate through the complete workflow:'));
        console.log(chalk.gray('   • Load dashboard'));
        console.log(chalk.gray('   • Upload contract document'));
        console.log(chalk.gray('   • Run analysis'));
        console.log(chalk.gray('   • Generate reports'));
        console.log(chalk.gray('   • Download all report formats'));
        console.log(chalk.white('3. Watch the console for step-by-step progress'));
        console.log(chalk.white('4. Screenshots will be saved automatically'));
        console.log(chalk.white('5. Reports will be downloaded to temp/downloads'));
        console.log(chalk.white('6. The browser will remain open for inspection'));
        
        console.log(chalk.yellow.bold('\n⚠️  Important Notes:'));
        console.log(chalk.yellow('• Make sure Contract Analyzer is running'));
        console.log(chalk.yellow('• Do not close the browser window manually'));
        console.log(chalk.yellow('• The demo may take 5-10 minutes to complete'));
        console.log(chalk.yellow('• Generated reports will open automatically (Windows only)'));
        
        console.log(chalk.green.bold('\n▶️  Demo starting in 3 seconds...\n'));
        
        // Brief countdown
        for (let i = 3; i > 0; i--) {
            process.stdout.write(chalk.blue.bold(`${i}... `));
            // Synchronous delay
            require('child_process').execSync('sleep 1', { stdio: 'ignore' });
        }
        console.log(chalk.green.bold('GO! 🚀\n'));
    }
    
    /**
     * Show demo results
     */
    showResults() {
        console.log(chalk.blue.bold('\n📊 Demo Results'));
        console.log(chalk.blue.bold('=' .repeat(30)));
        
        // Check for generated files
        const dirs = {
            screenshots: path.join(this.testDir, 'temp/screenshots'),
            downloads: path.join(this.testDir, 'temp/downloads'),
            reports: path.join(this.testDir, 'temp/reports')
        };
        
        for (const [type, dir] of Object.entries(dirs)) {
            if (fs.existsSync(dir)) {
                const files = fs.readdirSync(dir);
                console.log(chalk.green(`✓ ${type}: ${files.length} files generated`));
                
                if (files.length > 0) {
                    files.slice(0, 3).forEach(file => {
                        console.log(chalk.gray(`   • ${file}`));
                    });
                    if (files.length > 3) {
                        console.log(chalk.gray(`   • ... and ${files.length - 3} more`));
                    }
                }
            } else {
                console.log(chalk.yellow(`⚠️  ${type}: directory not found`));
            }
        }
        
        console.log(chalk.cyan.bold('\n💡 Next Steps:'));
        console.log(chalk.cyan('• Review generated reports in temp/downloads'));
        console.log(chalk.cyan('• Check screenshots in temp/screenshots'));
        console.log(chalk.cyan('• Browser window shows final dashboard state'));
        console.log(chalk.cyan('• Close browser window when finished reviewing'));
        
        console.log(chalk.green.bold('\n🎊 Visual Demo Complete!'));
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
            
            if (child.stdout && options.stdio !== 'inherit') {
                child.stdout.on('data', (data) => {
                    stdout += data.toString();
                });
            }
            
            if (child.stderr && options.stdio !== 'inherit') {
                child.stderr.on('data', (data) => {
                    stderr += data.toString();
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
}

// Command line execution
if (require.main === module) {
    const runner = new VisualDemoRunner();
    runner.run().catch(error => {
        console.error(chalk.red.bold('Fatal error:'), error.message);
        process.exit(1);
    });
}

module.exports = VisualDemoRunner;