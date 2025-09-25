# Visual Demo - Contract Analysis Workflow

This directory contains a comprehensive visual demonstration of the Contract Analyzer's complete workflow, designed to run with a visible browser window.

## Quick Start

```bash
cd tests/e2e
npm run demo
```

## What the Demo Shows

The visual demo demonstrates a complete contract analysis workflow:

### 🔄 Complete Workflow Steps

1. **Dashboard Loading** - Loads the main Contract Analyzer dashboard
2. **File Upload** - Navigates to upload page and uploads a test contract
3. **Template Selection** - Selects appropriate template (SOW - Statement of Work)
4. **Analysis Initiation** - Starts the contract analysis process
5. **Progress Monitoring** - Watches analysis progress in real-time
6. **Report Generation** - Creates reports in multiple formats:
   - 📊 Excel workbook with detailed analysis
   - 📄 PDF report with summary
   - 📝 Word document with tracked changes
7. **File Downloads** - Downloads all generated reports
8. **Results Review** - Shows final dashboard with completed analysis

### 🎯 Demo Features

- **Visible Browser**: Non-headless mode for demonstration
- **Slow Motion**: 500ms delays between actions for visibility
- **Step-by-Step Logging**: Detailed console output for each step
- **Screenshot Capture**: Automatic screenshots at key moments
- **Report Opening**: Automatically opens generated reports (Windows)
- **Error Handling**: Demonstrates error handling for invalid files
- **Extended Timeouts**: 10-minute timeout for complete workflow

## Prerequisites

1. **Contract Analyzer Running**:
   ```bash
   python start_dashboard.py
   ```

2. **Node Dependencies** (auto-installed):
   ```bash
   npm install
   ```

## Running the Demo

### Standard Demo
```bash
npm run demo
```

### Alternative Command
```bash
node run-visual-demo.js
```

### Direct Test Execution
```bash
npx mocha scenarios/visual-demo/visual-analysis-demo.test.js --timeout 600000
```

## Demo Configuration

The demo is configured for optimal viewing:

```javascript
{
    headless: false,         // Visible browser window
    slowMo: 500,            // 500ms delay between actions
    timeout: 600000,        // 10-minute total timeout
    viewport: {
        width: 1280,
        height: 720
    },
    screenshots: true,       // Capture key moments
    reportDownloads: true   // Download all report formats
}
```

## Output Files

After the demo completes, check these directories:

### 📸 Screenshots (`temp/screenshots/`)
- `01_dashboard_loaded.png` - Initial dashboard
- `02_upload_page_loaded.png` - Upload interface
- `03_contract_uploaded.png` - Successful upload
- `04_back_to_dashboard.png` - Return to dashboard
- `05_analysis_started.png` - Analysis initiated
- `06_analysis_in_progress.png` - Progress monitoring
- `07_analysis_completed.png` - Completed analysis
- `08_final_dashboard.png` - Final state

### 📥 Downloads (`temp/downloads/`)
- `analysis-report-excel-[timestamp].xlsx` - Excel workbook
- `analysis-report-pdf-[timestamp].pdf` - PDF report
- `analysis-report-word-[timestamp].docx` - Word document

### 📊 Reports (`temp/reports/`)
- Test execution reports and metrics

## Demo Flow Details

### Phase 1: Setup & Navigation (1-2 minutes)
- Load Contract Analyzer dashboard
- Verify system health
- Navigate to upload interface

### Phase 2: Upload & Configuration (1 minute)
- Select contract template (SOW)
- Upload test contract document
- Verify upload success

### Phase 3: Analysis Execution (2-5 minutes)
- Initiate contract analysis
- Monitor progress in real-time
- Wait for completion

### Phase 4: Report Generation (2-3 minutes)
- Generate Excel analysis report
- Generate PDF summary report
- Generate Word document with changes
- Download all formats

### Phase 5: Review & Completion (1 minute)
- Review final dashboard state
- Verify statistics updated
- Display completion summary

## Troubleshooting

### Demo Won't Start
- Ensure Contract Analyzer is running: `python start_dashboard.py`
- Check port availability (default: http://localhost:5000)
- Install dependencies: `npm install`

### Browser Doesn't Open
- Verify Puppeteer installation: `npm list puppeteer`
- Check for conflicting browser processes
- Run with debug flag: `TEST_DEBUG=true npm run demo`

### Analysis Fails
- Check API connectivity
- Verify test contract file exists: `fixtures/test-contract.docx`
- Review console logs for API errors

### Reports Don't Generate
- Check LLM provider configuration (OpenAI/Ollama)
- Verify API keys in `.env` file
- Monitor console for generation errors

## Customization

### Run Specific Test Scenarios
```bash
# Run only the main workflow
npx mocha scenarios/visual-demo/visual-analysis-demo.test.js -g "Complete Workflow"

# Run error handling demo
npx mocha scenarios/visual-demo/visual-analysis-demo.test.js -g "Error Handling"
```

### Modify Demo Speed
Edit `run-visual-demo.js`:
```javascript
slowMo: 1000,  // Slower for presentation
slowMo: 100,   // Faster for testing
```

### Change Browser Settings
```javascript
headless: true,     // Hidden browser
devtools: true,     // Open DevTools
viewport: {         // Different window size
    width: 1920,
    height: 1080
}
```

## Integration with CI/CD

For automated testing without visual demo:
```bash
npm run test:ci
```

For specific scenario testing:
```bash
npm run test:scenario contract-workflow
```

## Demo Script Structure

```
tests/e2e/
├── scenarios/visual-demo/
│   └── visual-analysis-demo.test.js     # Main demo test
├── run-visual-demo.js                   # Demo runner
├── framework/                           # Test framework
│   ├── TestBase.js                      # Base test class
│   ├── ApiClient.js                     # API integration
│   └── PageObjects/                     # Page object models
├── fixtures/                            # Test files
├── temp/                                # Generated files
│   ├── screenshots/                     # Demo screenshots
│   ├── downloads/                       # Downloaded reports
│   └── reports/                         # Test reports
└── README-VISUAL-DEMO.md               # This file
```

## Support

For issues with the visual demo:
1. Check that Contract Analyzer is running
2. Review console output for errors
3. Verify all dependencies are installed
4. Check generated logs in `temp/` directories

The demo is designed to showcase the complete Contract Analyzer workflow in an interactive, visual format suitable for demonstrations, training, and development validation.