/**
 * Upload Module
 * 
 * Handles file upload functionality including drag-and-drop, validation,
 * progress tracking, and file management for both contracts and templates.
 */

class UploadModule {
    constructor() {
        this.name = 'upload';
        this.initialized = false;
        this.uploadsInProgress = new Map();
        this.maxFileSize = 16 * 1024 * 1024; // 16MB
        this.allowedTypes = ['.docx'];
        this.currentData = null;
    }

    /**
     * Initialize the upload module
     */
    async init() {
        console.log('Upload: Initializing upload system...');
        
        // Set up file upload areas
        this.setupUploadAreas();
        
        // Set up modal functionality
        this.setupModalEvents();
        
        // Set up file input events
        this.setupFileInputEvents();
        
        this.initialized = true;
        console.log('Upload: Upload system initialized successfully');
    }

    /**
     * Handle module events
     */
    handleEvent(eventName, data) {
        switch (eventName) {
            case 'dataUpdated':
                this.currentData = data;
                this.updateFileListings();
                break;
            case 'tabChanged':
                if (data.currentTab === 'upload') {
                    this.onTabActivated();
                }
                break;
            case 'escapePressed':
                this.closeModals();
                break;
        }
    }

    /**
     * Called when upload tab is activated
     */
    onTabActivated() {
        console.log('Upload: Tab activated, refreshing file listings...');
        this.updateFileListings();
    }

    /**
     * Set up upload areas with drag and drop functionality
     */
    setupUploadAreas() {
        const uploadAreas = [
            { id: 'contractUpload', type: 'contract', inputId: 'contractFileInput' },
            { id: 'templateUpload', type: 'template', inputId: 'templateFileInput' }
        ];

        uploadAreas.forEach(area => {
            const element = document.getElementById(area.id);
            const input = document.getElementById(area.inputId);
            
            if (element && input) {
                this.setupUploadArea(element, input, area.type);
                console.log(`Upload: Setup upload area for ${area.type}`);
            } else {
                console.warn(`Upload: Upload area elements not found for ${area.type}`);
            }
        });
    }

    /**
     * Set up individual upload area
     */
    setupUploadArea(element, input, type) {
        // Click to upload
        element.addEventListener('click', () => {
            input.click();
        });

        // Drag and drop events
        element.addEventListener('dragover', this.handleDragOver.bind(this));
        element.addEventListener('dragleave', this.handleDragLeave.bind(this));
        element.addEventListener('drop', (e) => this.handleDrop(e, type));

        // File input change
        input.addEventListener('change', (e) => {
            if (!window.isDragDropUpload) {
                this.handleFileSelect(e.target.files, type);
            }
        });

        // Add visual styling
        element.classList.add('upload-area');
    }

    /**
     * Set up modal events
     */
    setupModalEvents() {
        // Upload modal
        const uploadModal = document.getElementById('uploadModal');
        const modalInput = document.getElementById('modalFileInput');
        
        if (uploadModal && modalInput) {
            // Modal file input
            modalInput.addEventListener('change', (e) => {
                if (!window.isDragDropUpload) {
                    this.handleFileSelect(e.target.files, 'contract');
                }
            });
        }

        // Close modals on outside click
        window.addEventListener('click', (event) => {
            if (event.target.classList.contains('modal')) {
                this.closeModal(event.target);
            }
        });

        console.log('Upload: Modal events setup complete');
    }

    /**
     * Set up file input events
     */
    setupFileInputEvents() {
        // Prevent multiple event listeners on inputs
        const inputs = document.querySelectorAll('input[type="file"]');
        inputs.forEach(input => {
            // Clear any existing listeners by cloning
            const newInput = input.cloneNode(true);
            input.parentNode.replaceChild(newInput, input);
        });
    }

    /**
     * Handle drag over event
     */
    handleDragOver(event) {
        event.preventDefault();
        event.stopPropagation();
        event.currentTarget.classList.add('drag-over');
    }

    /**
     * Handle drag leave event
     */
    handleDragLeave(event) {
        event.preventDefault();
        event.stopPropagation();
        
        // Only remove the class if we're actually leaving the element
        if (!event.currentTarget.contains(event.relatedTarget)) {
            event.currentTarget.classList.remove('drag-over');
        }
    }

    /**
     * Handle drop event
     */
    handleDrop(event, type) {
        event.preventDefault();
        event.stopPropagation();
        event.currentTarget.classList.remove('drag-over');

        const files = event.dataTransfer.files;
        if (files.length > 0) {
            // Set flag to indicate drag and drop
            window.isDragDropUpload = true;
            this.handleFileSelect(files, type);
            
            // Reset flag after a delay
            setTimeout(() => {
                window.isDragDropUpload = false;
            }, 100);
        } else {
            const notifications = window.ContractApp?.modules?.notifications;
            notifications?.warning('No files were dropped');
        }
    }

    /**
     * Handle file selection
     */
    handleFileSelect(files, type) {
        console.log(`Upload: Processing ${files.length} files for ${type}`);
        
        Array.from(files).forEach(file => {
            this.processFile(file, type);
        });
    }

    /**
     * Process individual file
     */
    async processFile(file, type) {
        const notifications = window.ContractApp?.modules?.notifications;
        
        console.log(`Upload: Processing file: ${file.name} (${type})`);

        try {
            // Validate file
            this.validateFile(file);
            
            // Upload file
            await this.uploadFile(file, type);
            
        } catch (error) {
            console.error(`Upload: Error processing file ${file.name}:`, error);
            notifications?.error(`Error uploading ${file.name}: ${error.message}`);
        }
    }

    /**
     * Validate file before upload
     */
    validateFile(file) {
        const utils = window.ContractApp?.modules?.utils;
        
        // Check file type
        if (!utils?.validateFileType(file, this.allowedTypes)) {
            throw new Error(`Invalid file type. Only ${this.allowedTypes.join(', ')} files are supported.`);
        }

        // Check file size
        if (!utils?.validateFileSize(file, this.maxFileSize / (1024 * 1024))) {
            throw new Error(`File too large. Maximum size is ${this.maxFileSize / (1024 * 1024)}MB.`);
        }

        console.log(`Upload: File validation passed for ${file.name}`);
    }

    /**
     * Upload file to server
     */
    async uploadFile(file, type) {
        const notifications = window.ContractApp?.modules?.notifications;
        const utils = window.ContractApp?.modules?.utils;
        
        const uploadId = utils?.generateId('upload');
        
        console.log(`Upload: Starting upload ${uploadId} for ${file.name}`);

        try {
            // Create form data
            const formData = new FormData();
            formData.append('file', file);

            // Determine endpoint
            const endpoint = type === 'contract' ? '/api/contracts/upload' : '/api/templates/upload';
            
            // Show progress
            this.showUploadProgress(uploadId, file.name);
            
            // Track upload
            this.uploadsInProgress.set(uploadId, {
                filename: file.name,
                type: type,
                startTime: Date.now()
            });

            // Make request
            const response = await fetch(endpoint, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            // Hide progress
            this.hideUploadProgress(uploadId);
            
            // Remove from tracking
            this.uploadsInProgress.delete(uploadId);

            if (result.error) {
                throw new Error(result.error);
            }

            // Success
            const typeLabel = type.charAt(0).toUpperCase() + type.slice(1);
            notifications?.success(`${typeLabel} ${file.name} uploaded successfully`);
            
            console.log(`Upload: Successfully uploaded ${file.name} as ${type}`);
            
            // Refresh data
            this.refreshData();

        } catch (error) {
            // Hide progress and remove tracking
            this.hideUploadProgress(uploadId);
            this.uploadsInProgress.delete(uploadId);
            
            throw error;
        }
    }

    /**
     * Show upload progress
     */
    showUploadProgress(uploadId, filename) {
        const progressContainer = this.getProgressContainer();
        
        const progressElement = document.createElement('div');
        progressElement.id = `progress-${uploadId}`;
        progressElement.className = 'upload-progress-item';
        progressElement.innerHTML = `
            <div class="progress-info">
                <i class="fas fa-upload"></i>
                <span class="filename">${filename}</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: 0%"></div>
            </div>
            <div class="progress-status">Uploading...</div>
        `;
        
        progressContainer.appendChild(progressElement);
        
        // Simulate progress (replace with actual progress tracking if available)
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 30;
            if (progress >= 100) {
                progress = 100;
                clearInterval(progressInterval);
            }
            
            const fill = progressElement.querySelector('.progress-fill');
            if (fill) {
                fill.style.width = `${progress}%`;
            }
        }, 200);
        
        console.log(`Upload: Showing progress for ${uploadId}`);
    }

    /**
     * Hide upload progress
     */
    hideUploadProgress(uploadId) {
        const progressElement = document.getElementById(`progress-${uploadId}`);
        if (progressElement) {
            progressElement.remove();
            console.log(`Upload: Removed progress for ${uploadId}`);
        }
    }

    /**
     * Get or create progress container
     */
    getProgressContainer() {
        let container = document.getElementById('upload-progress-container');
        
        if (!container) {
            container = document.createElement('div');
            container.id = 'upload-progress-container';
            container.className = 'upload-progress-container';
            document.body.appendChild(container);
        }
        
        return container;
    }

    /**
     * Update file listings in the UI
     */
    updateFileListings() {
        console.log('Upload: Updating file listings...');
        this.updateContractsList();
        this.updateTemplatesList();
    }

    /**
     * Update contracts list
     */
    updateContractsList() {
        const contractsList = document.getElementById('contractsList');
        if (!contractsList) {
            console.warn('Upload: Contracts list element not found');
            return;
        }

        const contracts = this.currentData?.contracts || [];
        contractsList.innerHTML = '';

        if (contracts.length === 0) {
            contractsList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-file-contract fa-2x text-muted mb-2"></i>
                    <p>No contracts uploaded yet</p>
                    <small class="text-muted">Upload DOCX files to get started</small>
                </div>
            `;
            return;
        }

        contracts.forEach(contract => {
            const contractDiv = this.createFileItem(contract, 'contract');
            contractsList.appendChild(contractDiv);
        });

        console.log(`Upload: Updated contracts list with ${contracts.length} items`);
    }

    /**
     * Update templates list
     */
    updateTemplatesList() {
        const templatesList = document.getElementById('templatesList');
        if (!templatesList) {
            console.warn('Upload: Templates list element not found');
            return;
        }

        const templates = this.currentData?.templates || [];
        templatesList.innerHTML = '';

        if (templates.length === 0) {
            templatesList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-file-alt fa-2x text-muted mb-2"></i>
                    <p>No templates uploaded yet</p>
                    <small class="text-muted">Upload DOCX template files</small>
                </div>
            `;
            return;
        }

        templates.forEach(template => {
            const templateDiv = this.createFileItem(template, 'template');
            templatesList.appendChild(templateDiv);
        });

        console.log(`Upload: Updated templates list with ${templates.length} items`);
    }

    /**
     * Create file item element
     */
    createFileItem(fileData, type) {
        const utils = window.ContractApp?.modules?.utils;
        
        const div = document.createElement('div');
        div.className = 'file-item';
        div.dataset.id = fileData.id || fileData.filename;

        const fileSize = fileData.file_size || fileData.size;
        const displayName = fileData.filename || fileData.display_name;
        const formattedSize = utils ? utils.formatFileSize(fileSize || 0) : 'Unknown size';

        div.innerHTML = `
            <div class="file-icon">
                <i class="fas fa-${type === 'contract' ? 'file-contract' : 'file-alt'}"></i>
            </div>
            <div class="file-info">
                <div class="file-name" title="${displayName}">${displayName}</div>
                <div class="file-details">${type.charAt(0).toUpperCase() + type.slice(1)} • ${formattedSize}</div>
                ${fileData.upload_date ? `<div class="file-date">Uploaded: ${utils ? utils.formatDateShort(fileData.upload_date) : fileData.upload_date}</div>` : ''}
            </div>
            <div class="file-actions">
                ${type === 'contract' ? 
                    `<button class="action-btn small" onclick="window.ContractApp.modules.upload.analyzeContract('${fileData.id}')" title="Analyze Contract">
                        <i class="fas fa-search"></i>
                    </button>` 
                    : 
                    `<button class="action-btn small" onclick="window.ContractApp.modules.upload.editTemplate('${fileData.id || fileData.filename}')" title="Edit Template">
                        <i class="fas fa-edit"></i>
                    </button>`
                }
                <button class="action-btn small danger" onclick="window.ContractApp.modules.upload.deleteFile('${fileData.id || fileData.filename}', '${type}')" title="Delete ${type}">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;

        return div;
    }

    /**
     * Analyze contract
     */
    async analyzeContract(contractId) {
        const notifications = window.ContractApp?.modules?.notifications;
        const utils = window.ContractApp?.modules?.utils;
        
        console.log(`Upload: Analyzing contract ${contractId}...`);
        notifications?.info('Analyzing contract...');

        try {
            const response = await utils?.apiRequest('/api/analyze-contract', {
                method: 'POST',
                body: JSON.stringify({ contract_id: contractId })
            });

            if (response?.success) {
                notifications?.success('Contract analyzed successfully');
                this.refreshData();
            } else {
                throw new Error(response?.error || 'Analysis failed');
            }

        } catch (error) {
            console.error('Upload: Error analyzing contract:', error);
            notifications?.error(`Contract analysis failed: ${error.message}`);
        }
    }

    /**
     * Edit template
     */
    editTemplate(templateId) {
        const notifications = window.ContractApp?.modules?.notifications;
        
        console.log(`Upload: Editing template ${templateId}...`);
        notifications?.info('Template editing not implemented yet');
    }

    /**
     * Delete file
     */
    async deleteFile(fileId, type) {
        const notifications = window.ContractApp?.modules?.notifications;
        const utils = window.ContractApp?.modules?.utils;
        
        const confirmed = confirm(`Are you sure you want to delete this ${type}?`);
        if (!confirmed) return;

        console.log(`Upload: Deleting ${type} ${fileId}...`);

        try {
            const endpoint = type === 'contract' ? `/api/contracts/${fileId}` : `/api/templates/${fileId}`;
            
            const response = await utils?.apiRequest(endpoint, {
                method: 'DELETE'
            });

            if (response?.success) {
                notifications?.success(`${type.charAt(0).toUpperCase() + type.slice(1)} deleted successfully`);
                this.refreshData();
            } else {
                throw new Error(response?.error || 'Delete failed');
            }

        } catch (error) {
            console.error(`Upload: Error deleting ${type}:`, error);
            notifications?.error(`Failed to delete ${type}: ${error.message}`);
        }
    }

    /**
     * Modal management
     */
    openUploadModal() {
        const modal = document.getElementById('uploadModal');
        if (modal) {
            modal.style.display = 'block';
            console.log('Upload: Upload modal opened');
        }
    }

    closeUploadModal() {
        const modal = document.getElementById('uploadModal');
        if (modal) {
            modal.style.display = 'none';
            console.log('Upload: Upload modal closed');
        }
    }

    closeModals() {
        this.closeUploadModal();
    }

    closeModal(modal) {
        if (modal) {
            modal.style.display = 'none';
        }
    }

    /**
     * Refresh data
     */
    refreshData() {
        const core = window.ContractApp?.core;
        if (core) {
            core.refresh();
        }
    }

    /**
     * Get upload statistics
     */
    getUploadStats() {
        return {
            contractsCount: this.currentData?.contracts?.length || 0,
            templatesCount: this.currentData?.templates?.length || 0,
            uploadsInProgress: this.uploadsInProgress.size
        };
    }

    /**
     * Cancel upload
     */
    cancelUpload(uploadId) {
        if (this.uploadsInProgress.has(uploadId)) {
            this.uploadsInProgress.delete(uploadId);
            this.hideUploadProgress(uploadId);
            
            const notifications = window.ContractApp?.modules?.notifications;
            notifications?.info('Upload cancelled');
            
            console.log(`Upload: Cancelled upload ${uploadId}`);
        }
    }

    /**
     * Get active uploads
     */
    getActiveUploads() {
        return Array.from(this.uploadsInProgress.entries()).map(([id, data]) => ({
            id,
            ...data
        }));
    }
}

// Export for global use
window.UploadModule = UploadModule;