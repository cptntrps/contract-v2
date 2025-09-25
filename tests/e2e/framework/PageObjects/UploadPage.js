/**
 * Upload Page Object Model
 * 
 * Represents the contract upload interface and provides methods
 * for file upload operations and related functionality.
 */

const path = require('path');
const fs = require('fs-extra');
const testConfig = require('../../config/test.config');

class UploadPage {
    constructor(page) {
        this.page = page;
        this.config = testConfig;
        
        // Upload page selectors
        this.selectors = {
            container: this.config.getSelector('uploadContainer'),
            fileInput: this.config.getSelector('fileInput'),
            uploadButton: this.config.getSelector('uploadButton'),
            templateSelect: this.config.getSelector('templateSelect'),
            uploadProgress: this.config.getSelector('uploadProgress'),
            uploadStatus: this.config.getSelector('uploadStatus'),
            
            // Upload area elements
            dropZone: '.drop-zone',
            dragOverlay: '.drag-overlay',
            filePreview: '.file-preview',
            fileName: '.file-name',
            fileSize: '.file-size',
            removeFileButton: '.remove-file-button',
            
            // Template selection
            templateOption: '.template-option',
            templatePreview: '.template-preview',
            templateDescription: '.template-description',
            
            // Upload controls
            startUploadButton: '.start-upload-button',
            cancelUploadButton: '.cancel-upload-button',
            clearAllButton: '.clear-all-button',
            
            // Progress indicators
            progressBar: '.progress-bar',
            progressPercent: '.progress-percent',
            progressText: '.progress-text',
            uploadingSpinner: '.uploading-spinner',
            
            // Status messages
            successMessage: '.upload-success-message',
            errorMessage: '.upload-error-message',
            warningMessage: '.upload-warning-message',
            
            // File validation
            validationErrors: '.validation-errors',
            errorList: '.error-list',
            errorItem: '.error-item'
        };
    }
    
    /**
     * Wait for upload page to load completely
     */
    async waitForLoad() {
        console.log('UploadPage: Waiting for upload page to load...');
        
        // Wait for main container
        await this.page.waitForSelector(this.selectors.container, {
            visible: true,
            timeout: this.config.getTimeout('pageLoad')
        });
        
        // Wait for key components
        await Promise.all([
            this.page.waitForSelector(this.selectors.fileInput, { visible: true }),
            this.page.waitForSelector(this.selectors.templateSelect, { visible: true }),
            this.page.waitForSelector(this.selectors.dropZone, { visible: true })
        ]);
        
        console.log('UploadPage: Upload page loaded successfully');
    }
    
    /**
     * Upload file using file input
     */
    async uploadFile(filePath, templateName = null) {
        console.log(`UploadPage: Uploading file: ${filePath}`);
        
        // Check if file exists
        if (!fs.existsSync(filePath)) {
            throw new Error(`Upload file not found: ${filePath}`);
        }
        
        // Select template if specified
        if (templateName) {
            await this.selectTemplate(templateName);
        }
        
        // Upload the file
        const fileInput = await this.page.$(this.selectors.fileInput);
        await fileInput.uploadFile(filePath);
        
        // Wait for file to be processed and preview to appear
        await this.waitForFilePreview();
        
        // Start the upload
        await this.startUpload();
        
        // Wait for upload to complete
        await this.waitForUploadComplete();
        
        console.log('UploadPage: File uploaded successfully');
    }
    
    /**
     * Upload file using drag and drop
     */
    async uploadFileByDragDrop(filePath, templateName = null) {
        console.log(`UploadPage: Uploading file by drag/drop: ${filePath}`);
        
        if (!fs.existsSync(filePath)) {
            throw new Error(`Upload file not found: ${filePath}`);
        }
        
        // Select template if specified
        if (templateName) {
            await this.selectTemplate(templateName);
        }
        
        // Read file as buffer
        const fileBuffer = fs.readFileSync(filePath);
        const fileName = path.basename(filePath);
        
        // Create file object for drag/drop simulation
        await this.page.evaluate((fileData, fileName) => {
            const dt = new DataTransfer();
            const file = new File([new Uint8Array(fileData)], fileName, {
                type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            });
            dt.items.add(file);
            
            const dropZone = document.querySelector('.drop-zone');
            const dropEvent = new DragEvent('drop', {
                dataTransfer: dt,
                bubbles: true,
                cancelable: true
            });
            
            dropZone.dispatchEvent(dropEvent);
        }, Array.from(fileBuffer), fileName);
        
        // Wait for file to be processed
        await this.waitForFilePreview();
        
        // Start the upload
        await this.startUpload();
        
        // Wait for upload to complete
        await this.waitForUploadComplete();
        
        console.log('UploadPage: File uploaded successfully via drag/drop');
    }
    
    /**
     * Select template for comparison
     */
    async selectTemplate(templateName) {
        console.log(`UploadPage: Selecting template: ${templateName}`);
        
        // Click template select dropdown
        await this.page.click(this.selectors.templateSelect);
        
        // Wait for options to appear
        await this.page.waitForSelector(this.selectors.templateOption, {
            visible: true,
            timeout: this.config.getTimeout('elementVisible')
        });
        
        // Find and click the specific template option
        const templateOptions = await this.page.$$(this.selectors.templateOption);
        
        for (const option of templateOptions) {
            const text = await option.evaluate(el => el.textContent.trim());
            if (text.includes(templateName)) {
                await option.click();
                console.log(`UploadPage: Selected template: ${templateName}`);
                return;
            }
        }
        
        throw new Error(`Template not found: ${templateName}`);
    }
    
    /**
     * Wait for file preview to appear
     */
    async waitForFilePreview() {
        console.log('UploadPage: Waiting for file preview...');
        
        await this.page.waitForSelector(this.selectors.filePreview, {
            visible: true,
            timeout: this.config.getTimeout('fileUpload')
        });
        
        // Wait for file details to load
        await this.page.waitForSelector(this.selectors.fileName, { visible: true });
        await this.page.waitForSelector(this.selectors.fileSize, { visible: true });
        
        console.log('UploadPage: File preview loaded');
    }
    
    /**
     * Start the upload process
     */
    async startUpload() {
        console.log('UploadPage: Starting upload...');
        
        // Click start upload button
        await this.page.click(this.selectors.startUploadButton);
        
        // Wait for upload progress to begin
        await this.page.waitForSelector(this.selectors.uploadProgress, {
            visible: true,
            timeout: this.config.getTimeout('elementVisible')
        });
    }
    
    /**
     * Wait for upload to complete
     */
    async waitForUploadComplete() {
        console.log('UploadPage: Waiting for upload to complete...');
        
        const timeout = this.config.getTimeout('fileUpload');
        const startTime = Date.now();
        
        while (Date.now() - startTime < timeout) {
            // Check for success message
            const successMessage = await this.page.$(this.selectors.successMessage);
            if (successMessage) {
                const isVisible = await successMessage.isIntersectingViewport();
                if (isVisible) {
                    console.log('UploadPage: Upload completed successfully');
                    return true;
                }
            }
            
            // Check for error message
            const errorMessage = await this.page.$(this.selectors.errorMessage);
            if (errorMessage) {
                const isVisible = await errorMessage.isIntersectingViewport();
                if (isVisible) {
                    const errorText = await errorMessage.evaluate(el => el.textContent.trim());
                    throw new Error(`Upload failed: ${errorText}`);
                }
            }
            
            // Check progress
            const progressElement = await this.page.$(this.selectors.progressPercent);
            if (progressElement) {
                const progressText = await progressElement.evaluate(el => el.textContent.trim());
                console.log(`UploadPage: Upload progress: ${progressText}`);
            }
            
            // Wait before checking again
            await this.page.waitForTimeout(1000);
        }
        
        throw new Error('Upload timeout - upload did not complete in expected time');
    }
    
    /**
     * Cancel current upload
     */
    async cancelUpload() {
        console.log('UploadPage: Canceling upload...');
        
        const cancelButton = await this.page.$(this.selectors.cancelUploadButton);
        if (cancelButton) {
            await cancelButton.click();
            
            // Wait for cancellation to be processed
            await this.page.waitForFunction(
                () => !document.querySelector('.uploading-spinner'),
                { timeout: this.config.getTimeout('elementVisible') }
            );
            
            console.log('UploadPage: Upload canceled');
        }
    }
    
    /**
     * Remove uploaded file
     */
    async removeFile() {
        console.log('UploadPage: Removing uploaded file...');
        
        const removeButton = await this.page.$(this.selectors.removeFileButton);
        if (removeButton) {
            await removeButton.click();
            
            // Wait for file preview to disappear
            await this.page.waitForFunction(
                () => !document.querySelector('.file-preview'),
                { timeout: this.config.getTimeout('elementVisible') }
            );
            
            console.log('UploadPage: File removed');
        }
    }
    
    /**
     * Clear all uploaded files
     */
    async clearAll() {
        console.log('UploadPage: Clearing all files...');
        
        const clearButton = await this.page.$(this.selectors.clearAllButton);
        if (clearButton) {
            await clearButton.click();
            
            // Wait for all previews to disappear
            await this.page.waitForFunction(
                () => !document.querySelector('.file-preview'),
                { timeout: this.config.getTimeout('elementVisible') }
            );
            
            console.log('UploadPage: All files cleared');
        }
    }
    
    /**
     * Get upload status
     */
    async getUploadStatus() {
        const statusElement = await this.page.$(this.selectors.uploadStatus);
        if (!statusElement) {
            return null;
        }
        
        return await statusElement.evaluate(el => el.textContent.trim());
    }
    
    /**
     * Get upload progress
     */
    async getUploadProgress() {
        const progressElement = await this.page.$(this.selectors.progressPercent);
        if (!progressElement) {
            return 0;
        }
        
        const progressText = await progressElement.evaluate(el => el.textContent.trim());
        return parseInt(progressText.replace('%', '')) || 0;
    }
    
    /**
     * Get file details
     */
    async getFileDetails() {
        const nameElement = await this.page.$(this.selectors.fileName);
        const sizeElement = await this.page.$(this.selectors.fileSize);
        
        return {
            name: nameElement ? await nameElement.evaluate(el => el.textContent.trim()) : null,
            size: sizeElement ? await sizeElement.evaluate(el => el.textContent.trim()) : null
        };
    }
    
    /**
     * Get validation errors
     */
    async getValidationErrors() {
        const errorsContainer = await this.page.$(this.selectors.validationErrors);
        if (!errorsContainer) {
            return [];
        }
        
        const errorItems = await this.page.$$(this.selectors.errorItem);
        const errors = [];
        
        for (const item of errorItems) {
            const errorText = await item.evaluate(el => el.textContent.trim());
            errors.push(errorText);
        }
        
        return errors;
    }
    
    /**
     * Get available templates
     */
    async getAvailableTemplates() {
        // Click template select to open dropdown
        await this.page.click(this.selectors.templateSelect);
        
        // Wait for options to appear
        await this.page.waitForSelector(this.selectors.templateOption, {
            visible: true,
            timeout: this.config.getTimeout('elementVisible')
        });
        
        const templateOptions = await this.page.$$(this.selectors.templateOption);
        const templates = [];
        
        for (const option of templateOptions) {
            const text = await option.evaluate(el => el.textContent.trim());
            const value = await option.evaluate(el => el.getAttribute('value') || el.textContent.trim());
            templates.push({ text, value });
        }
        
        // Close dropdown
        await this.page.keyboard.press('Escape');
        
        return templates;
    }
    
    /**
     * Upload multiple files sequentially
     */
    async uploadMultipleFiles(filePaths, templateName = null) {
        console.log(`UploadPage: Uploading ${filePaths.length} files sequentially...`);
        
        const results = [];
        
        for (let i = 0; i < filePaths.length; i++) {
            const filePath = filePaths[i];
            
            try {
                console.log(`UploadPage: Uploading file ${i + 1}/${filePaths.length}: ${path.basename(filePath)}`);
                
                await this.uploadFile(filePath, templateName);
                
                results.push({
                    file: filePath,
                    success: true,
                    error: null
                });
                
            } catch (error) {
                console.error(`UploadPage: Failed to upload ${filePath}:`, error.message);
                
                results.push({
                    file: filePath,
                    success: false,
                    error: error.message
                });
            }
        }
        
        return results;
    }
    
    /**
     * Assert upload page is loaded
     */
    async assertUploadPageLoaded() {
        await this.waitForLoad();
        
        // Verify key elements are present
        const container = await this.page.$(this.selectors.container);
        const fileInput = await this.page.$(this.selectors.fileInput);
        const dropZone = await this.page.$(this.selectors.dropZone);
        
        if (!container || !fileInput || !dropZone) {
            throw new Error('Upload page not fully loaded - missing key elements');
        }
        
        console.log('UploadPage: Upload page load assertion passed');
    }
    
    /**
     * Assert file upload successful
     */
    async assertUploadSuccessful(fileName = null) {
        const successMessage = await this.page.$(this.selectors.successMessage);
        
        if (!successMessage) {
            throw new Error('Upload success message not found');
        }
        
        const isVisible = await successMessage.isIntersectingViewport();
        if (!isVisible) {
            throw new Error('Upload success message not visible');
        }
        
        if (fileName) {
            const messageText = await successMessage.evaluate(el => el.textContent.trim());
            if (!messageText.includes(fileName)) {
                throw new Error(`Upload success message does not mention file: ${fileName}`);
            }
        }
        
        console.log('UploadPage: Upload success assertion passed');
    }
    
    /**
     * Assert upload failed
     */
    async assertUploadFailed() {
        const errorMessage = await this.page.$(this.selectors.errorMessage);
        
        if (!errorMessage) {
            throw new Error('Upload error message not found');
        }
        
        const isVisible = await errorMessage.isIntersectingViewport();
        if (!isVisible) {
            throw new Error('Upload error message not visible');
        }
        
        console.log('UploadPage: Upload failure assertion passed');
    }
}

module.exports = UploadPage;