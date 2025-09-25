/**
 * Prompts Module
 * 
 * Handles LLM prompt management including editing, validation, preview, backup,
 * and restoration of prompt templates for different analysis types.
 */

class PromptsModule {
    constructor() {
        this.name = 'prompts';
        this.initialized = false;
        this.currentPromptType = 'individual_analysis';
        this.originalPromptContent = '';
        this.promptBackups = [];
        this.validationInProgress = false;
        this.previewInProgress = false;
    }

    /**
     * Initialize the prompts module
     */
    async init() {
        console.log('Prompts: Initializing prompt management system...');
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Load initial prompt data
        await this.loadPrompts();
        
        // Load backup list
        await this.loadBackupList();
        
        // Load prompt statistics
        await this.loadPromptStats();
        
        this.initialized = true;
        console.log('Prompts: Prompt management system initialized successfully');
    }

    /**
     * Handle module events
     */
    handleEvent(eventName, data) {
        switch (eventName) {
            case 'tabChanged':
                if (data.currentTab === 'prompts') {
                    this.onTabActivated();
                }
                break;
            case 'escapePressed':
                this.closeModals();
                break;
        }
    }

    /**
     * Called when prompts tab is activated
     */
    onTabActivated() {
        console.log('Prompts: Tab activated, refreshing prompts...');
        this.loadPrompts();
        this.loadBackupList();
        this.loadPromptStats();
    }

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Prompt type selector
        const promptTypeSelect = document.getElementById('promptTypeSelect');
        if (promptTypeSelect) {
            promptTypeSelect.addEventListener('change', () => {
                this.onPromptTypeChange();
            });
        }

        // Action buttons
        this.setupActionButtons();
        
        // Variable tags
        this.setupVariableTags();
        
        // Backup management
        this.setupBackupManagement();
        
        console.log('Prompts: Event listeners setup complete');
    }

    /**
     * Set up action buttons
     */
    setupActionButtons() {
        const buttons = {
            'savePrompt': () => this.savePrompt(),
            'validatePrompt': () => this.validatePrompt(),
            'previewPrompt': () => this.previewPrompt(),
            'resetPrompt': () => this.resetPrompt(),
            'createBackup': () => this.createBackup(),
            'restoreBackup': () => this.restoreBackup()
        };

        Object.entries(buttons).forEach(([id, handler]) => {
            const button = document.getElementById(id);
            if (button) {
                button.addEventListener('click', handler);
            }
        });
    }

    /**
     * Set up variable tag insertion
     */
    setupVariableTags() {
        const variableTags = document.querySelectorAll('.variable-tag');
        
        variableTags.forEach(tag => {
            tag.addEventListener('click', (event) => {
                this.insertVariableAtCursor(event);
            });
        });
        
        console.log(`Prompts: Setup ${variableTags.length} variable tag listeners`);
    }

    /**
     * Set up backup management
     */
    setupBackupManagement() {
        const backupList = document.getElementById('backupList');
        if (backupList) {
            backupList.addEventListener('change', () => {
                this.onBackupSelectionChange();
            });
        }
    }

    /**
     * Handle prompt type change
     */
    onPromptTypeChange() {
        const promptTypeSelect = document.getElementById('promptTypeSelect');
        this.currentPromptType = promptTypeSelect.value;
        
        console.log(`Prompts: Prompt type changed to: ${this.currentPromptType}`);
        
        // Load the selected prompt type
        this.loadPrompts();
        
        // Load backups for this type
        this.loadBackupList();
        
        // Clear validation and preview
        this.clearValidationAndPreview();
    }

    /**
     * Load prompts for current type
     */
    async loadPrompts() {
        const notifications = window.ContractApp?.modules?.notifications;
        const utils = window.ContractApp?.modules?.utils;
        
        console.log(`Prompts: Loading prompt for type: ${this.currentPromptType}`);
        
        try {
            const data = await utils?.apiRequest(`/api/prompts/${this.currentPromptType}`);
            
            if (data?.error) {
                throw new Error(data.error);
            }
            
            const promptEditor = document.getElementById('promptEditor');
            if (promptEditor) {
                promptEditor.value = data.template || '';
                this.originalPromptContent = data.template || '';
            } else {
                console.warn('Prompts: Prompt editor not found');
            }
            
            // Update prompt info
            this.updatePromptInfo(data);
            
            console.log('Prompts: Prompt loaded successfully');
            
        } catch (error) {
            console.error('Prompts: Error loading prompt:', error);
            notifications?.error(`Failed to load prompt template: ${error.message}`);
        }
    }

    /**
     * Update prompt information display
     */
    updatePromptInfo(data) {
        const versionElement = document.getElementById('prompt-version');
        const statusElement = document.getElementById('prompt-status');
        
        if (versionElement) {
            versionElement.textContent = `Version: ${data.version || '1.0'}`;
        }
        
        if (statusElement) {
            statusElement.textContent = `Status: ${data.status || 'Active'}`;
        }
    }

    /**
     * Save current prompt
     */
    async savePrompt() {
        if (this.validationInProgress) return;
        
        const notifications = window.ContractApp?.modules?.notifications;
        const utils = window.ContractApp?.modules?.utils;
        
        const promptEditor = document.getElementById('promptEditor');
        if (!promptEditor) {
            notifications?.error('Prompt editor not found');
            return;
        }
        
        const newContent = promptEditor.value.trim();
        if (!newContent) {
            notifications?.error('Prompt cannot be empty');
            return;
        }
        
        console.log('Prompts: Saving prompt...');
        notifications?.info('Saving prompt...');
        
        try {
            const response = await utils?.apiRequest(`/api/prompts/${this.currentPromptType}`, {
                method: 'POST',
                body: JSON.stringify({ template: newContent })
            });
            
            if (response?.error) {
                throw new Error(response.error);
            }
            
            notifications?.success('Prompt saved successfully!');
            this.originalPromptContent = newContent;
            
            // Update prompt info
            this.updatePromptInfo(response);
            
            // Refresh statistics
            this.loadPromptStats();
            
            console.log('Prompts: Prompt saved successfully');
            
        } catch (error) {
            console.error('Prompts: Error saving prompt:', error);
            notifications?.error(`Failed to save prompt: ${error.message}`);
        }
    }

    /**
     * Validate current prompt
     */
    async validatePrompt() {
        if (this.validationInProgress) return;
        
        const notifications = window.ContractApp?.modules?.notifications;
        const utils = window.ContractApp?.modules?.utils;
        
        const promptEditor = document.getElementById('promptEditor');
        if (!promptEditor) {
            notifications?.error('Prompt editor not found');
            return;
        }
        
        const content = promptEditor.value.trim();
        if (!content) {
            this.showValidationResult('Prompt cannot be empty', false);
            return;
        }
        
        console.log('Prompts: Validating prompt...');
        this.validationInProgress = true;
        notifications?.info('Validating prompt...');
        
        try {
            const response = await utils?.apiRequest('/api/prompts/validate', {
                method: 'POST',
                body: JSON.stringify({
                    template: content,
                    prompt_type: this.currentPromptType
                })
            });
            
            if (response?.error) {
                this.showValidationResult(response.error, false);
                return;
            }
            
            this.showValidationResult(response.message || 'Prompt is valid!', response.valid);
            
            if (response.suggestions && response.suggestions.length > 0) {
                this.showValidationSuggestions(response.suggestions);
            }
            
            console.log('Prompts: Validation completed');
            
        } catch (error) {
            console.error('Prompts: Error validating prompt:', error);
            this.showValidationResult(`Validation failed: ${error.message}`, false);
        } finally {
            this.validationInProgress = false;
        }
    }

    /**
     * Show validation result
     */
    showValidationResult(message, isValid) {
        const validationResults = document.getElementById('validationResults');
        if (!validationResults) return;
        
        const icon = isValid ? 
            '<i class="fas fa-check-circle" style="color: green;"></i>' : 
            '<i class="fas fa-times-circle" style="color: red;"></i>';
        
        validationResults.innerHTML = `
            <div class="validation-message ${isValid ? 'valid' : 'invalid'}">
                ${icon} ${message}
            </div>
        `;
    }

    /**
     * Show validation suggestions
     */
    showValidationSuggestions(suggestions) {
        const validationResults = document.getElementById('validationResults');
        if (!validationResults) return;
        
        const suggestionsList = suggestions.map(s => `<li>${s}</li>`).join('');
        validationResults.innerHTML += `
            <div class="validation-suggestions">
                <h4>Suggestions:</h4>
                <ul>${suggestionsList}</ul>
            </div>
        `;
    }

    /**
     * Preview current prompt
     */
    async previewPrompt() {
        if (this.previewInProgress) return;
        
        const notifications = window.ContractApp?.modules?.notifications;
        const utils = window.ContractApp?.modules?.utils;
        
        const promptEditor = document.getElementById('promptEditor');
        if (!promptEditor) {
            notifications?.error('Prompt editor not found');
            return;
        }
        
        const content = promptEditor.value.trim();
        if (!content) {
            notifications?.error('Prompt cannot be empty');
            return;
        }
        
        console.log('Prompts: Generating preview...');
        this.previewInProgress = true;
        
        // Show preview loading
        const previewPanel = document.getElementById('promptPreview');
        if (previewPanel) {
            previewPanel.innerHTML = '<p class="preview-message">Generating preview...</p>';
        }
        
        try {
            const response = await utils?.apiRequest('/api/prompts/preview', {
                method: 'POST',
                body: JSON.stringify({
                    template: content,
                    prompt_type: this.currentPromptType
                })
            });
            
            if (response?.error) {
                this.showPreviewResult(`Preview failed: ${response.error}`, false);
                return;
            }
            
            this.showPreviewResult(response.preview_text, true);
            
            console.log('Prompts: Preview generated successfully');
            
        } catch (error) {
            console.error('Prompts: Error generating preview:', error);
            this.showPreviewResult(`Preview failed: ${error.message}`, false);
        } finally {
            this.previewInProgress = false;
        }
    }

    /**
     * Show preview result
     */
    showPreviewResult(content, isSuccess) {
        const previewPanel = document.getElementById('promptPreview');
        if (!previewPanel) return;
        
        if (isSuccess) {
            previewPanel.innerHTML = `
                <div class="preview-content-success">
                    <pre>${content}</pre>
                </div>
            `;
        } else {
            previewPanel.innerHTML = `
                <div class="preview-content-error">
                    <p style="color: red;">${content}</p>
                </div>
            `;
        }
    }

    /**
     * Reset prompt to original state
     */
    resetPrompt() {
        const promptEditor = document.getElementById('promptEditor');
        if (!promptEditor) {
            const notifications = window.ContractApp?.modules?.notifications;
            notifications?.error('Prompt editor not found');
            return;
        }
        
        const confirmed = confirm('Are you sure you want to reset the prompt to its original state? Any unsaved changes will be lost.');
        if (!confirmed) return;
        
        promptEditor.value = this.originalPromptContent;
        
        const notifications = window.ContractApp?.modules?.notifications;
        notifications?.info('Prompt reset to original state');
        
        // Clear validation and preview
        this.clearValidationAndPreview();
        
        console.log('Prompts: Prompt reset to original state');
    }

    /**
     * Clear validation and preview results
     */
    clearValidationAndPreview() {
        const validationResults = document.getElementById('validationResults');
        const previewPanel = document.getElementById('promptPreview');
        
        if (validationResults) {
            validationResults.innerHTML = '<p class="validation-message">Click "Validate" to check your prompt</p>';
        }
        
        if (previewPanel) {
            previewPanel.innerHTML = '<p class="preview-message">Click "Preview" to see prompt with sample data</p>';
        }
    }

    /**
     * Insert variable at cursor position
     */
    insertVariableAtCursor(event) {
        const notifications = window.ContractApp?.modules?.notifications;
        const promptEditor = document.getElementById('promptEditor');
        const variable = event.target.textContent;
        
        if (!promptEditor) return;
        
        const cursorPos = promptEditor.selectionStart;
        const textBefore = promptEditor.value.substring(0, cursorPos);
        const textAfter = promptEditor.value.substring(promptEditor.selectionEnd);
        
        promptEditor.value = textBefore + variable + textAfter;
        promptEditor.selectionStart = promptEditor.selectionEnd = cursorPos + variable.length;
        promptEditor.focus();
        
        notifications?.info(`Inserted variable: ${variable}`);
        
        console.log(`Prompts: Inserted variable: ${variable}`);
    }

    /**
     * Create backup of current prompt
     */
    async createBackup() {
        const notifications = window.ContractApp?.modules?.notifications;
        const utils = window.ContractApp?.modules?.utils;
        
        const promptEditor = document.getElementById('promptEditor');
        const backupNameInput = document.getElementById('backupName');
        
        if (!promptEditor) {
            notifications?.error('Prompt editor not found');
            return;
        }
        
        const content = promptEditor.value.trim();
        if (!content) {
            notifications?.error('Cannot backup empty prompt');
            return;
        }
        
        const backupName = backupNameInput ? backupNameInput.value.trim() : '';
        
        console.log('Prompts: Creating backup...');
        notifications?.info('Creating backup...');
        
        try {
            const response = await utils?.apiRequest('/api/prompts/backup', {
                method: 'POST',
                body: JSON.stringify({
                    prompt_type: this.currentPromptType,
                    template: content,
                    backup_name: backupName
                })
            });
            
            if (response?.error) {
                throw new Error(response.error);
            }
            
            notifications?.success('Backup created successfully!');
            
            // Clear backup name input
            if (backupNameInput) {
                backupNameInput.value = '';
            }
            
            // Refresh backup list and statistics
            this.loadBackupList();
            this.loadPromptStats();
            
            console.log('Prompts: Backup created successfully');
            
        } catch (error) {
            console.error('Prompts: Error creating backup:', error);
            notifications?.error(`Failed to create backup: ${error.message}`);
        }
    }

    /**
     * Load backup list
     */
    async loadBackupList() {
        const utils = window.ContractApp?.modules?.utils;
        
        try {
            const data = await utils?.apiRequest(`/api/prompts/backups/${this.currentPromptType}`);
            
            if (data?.error) {
                console.error('Prompts: Error loading backups:', data.error);
                return;
            }
            
            this.updateBackupList(data.backups || []);
            
        } catch (error) {
            console.error('Prompts: Error loading backup list:', error);
        }
    }

    /**
     * Update backup list display
     */
    updateBackupList(backups) {
        const backupSelector = document.getElementById('backupList');
        const backupContainer = document.getElementById('backupListContainer');
        
        if (backupSelector) {
            backupSelector.innerHTML = '<option value="">Select backup to restore...</option>';
            
            backups.forEach(backup => {
                const option = document.createElement('option');
                option.value = backup.id;
                option.textContent = `${backup.name} (${this.formatDate(backup.created_at)})`;
                backupSelector.appendChild(option);
            });
        }
        
        if (backupContainer) {
            if (backups.length === 0) {
                backupContainer.innerHTML = '<p class="backup-message">No backups available</p>';
            } else {
                const backupItems = backups.map(backup => `
                    <div class="backup-item">
                        <span class="backup-name">${backup.name}</span>
                        <span class="backup-date">${this.formatDate(backup.created_at)}</span>
                        <button class="action-btn small" onclick="window.ContractApp.modules.prompts.restoreSpecificBackup('${backup.id}')">
                            <i class="fas fa-download"></i> Restore
                        </button>
                    </div>
                `).join('');
                
                backupContainer.innerHTML = backupItems;
            }
        }
        
        console.log(`Prompts: Updated backup list with ${backups.length} items`);
    }

    /**
     * Handle backup selection change
     */
    onBackupSelectionChange() {
        // Could show backup preview or details here
        console.log('Prompts: Backup selection changed');
    }

    /**
     * Restore backup from dropdown
     */
    restoreBackup() {
        const backupSelector = document.getElementById('backupList');
        if (!backupSelector || !backupSelector.value) {
            const notifications = window.ContractApp?.modules?.notifications;
            notifications?.warning('Please select a backup to restore');
            return;
        }
        
        this.restoreSpecificBackup(backupSelector.value);
    }

    /**
     * Restore specific backup by ID
     */
    async restoreSpecificBackup(backupId) {
        const notifications = window.ContractApp?.modules?.notifications;
        const utils = window.ContractApp?.modules?.utils;
        
        const confirmed = confirm('Are you sure you want to restore this backup? Current prompt will be overwritten.');
        if (!confirmed) return;
        
        console.log(`Prompts: Restoring backup ${backupId}...`);
        notifications?.info('Restoring backup...');
        
        try {
            const response = await utils?.apiRequest(`/api/prompts/restore/${backupId}`, {
                method: 'POST'
            });
            
            if (response?.error) {
                throw new Error(response.error);
            }
            
            notifications?.success('Backup restored successfully!');
            
            // Reload the current prompt
            this.loadPrompts();
            
            // Clear validation and preview
            this.clearValidationAndPreview();
            
            console.log('Prompts: Backup restored successfully');
            
        } catch (error) {
            console.error('Prompts: Error restoring backup:', error);
            notifications?.error(`Failed to restore backup: ${error.message}`);
        }
    }

    /**
     * Load prompt statistics
     */
    async loadPromptStats() {
        const utils = window.ContractApp?.modules?.utils;
        
        try {
            const data = await utils?.apiRequest('/api/prompts/stats');
            
            if (data?.error) {
                console.error('Prompts: Error loading prompt stats:', data.error);
                return;
            }
            
            this.updatePromptStats(data);
            
        } catch (error) {
            console.error('Prompts: Error loading prompt stats:', error);
        }
    }

    /**
     * Update prompt statistics display
     */
    updatePromptStats(stats) {
        const elements = {
            'totalPrompts': stats.total_prompts || 0,
            'activePrompts': stats.active_prompts || 0,
            'totalBackups': stats.total_backups || 0,
            'lastModified': stats.last_modified ? this.formatDate(stats.last_modified) : 'Never'
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
        
        console.log('Prompts: Statistics updated:', stats);
    }

    /**
     * Close modals
     */
    closeModals() {
        // Close any prompt-related modals if they exist
        console.log('Prompts: Closing modals');
    }

    /**
     * Format date for display
     */
    formatDate(dateString) {
        const utils = window.ContractApp?.modules?.utils;
        return utils ? utils.formatDate(dateString) : dateString;
    }

    /**
     * Get current prompt content
     */
    getCurrentPromptContent() {
        const promptEditor = document.getElementById('promptEditor');
        return promptEditor ? promptEditor.value : '';
    }

    /**
     * Set prompt content
     */
    setPromptContent(content) {
        const promptEditor = document.getElementById('promptEditor');
        if (promptEditor) {
            promptEditor.value = content;
        }
    }

    /**
     * Check if prompt has unsaved changes
     */
    hasUnsavedChanges() {
        const current = this.getCurrentPromptContent();
        return current !== this.originalPromptContent;
    }

    /**
     * Get available prompt types
     */
    getAvailablePromptTypes() {
        const promptTypeSelect = document.getElementById('promptTypeSelect');
        if (!promptTypeSelect) return [];
        
        return Array.from(promptTypeSelect.options).map(option => ({
            value: option.value,
            text: option.textContent
        }));
    }

    /**
     * Get current prompt type
     */
    getCurrentPromptType() {
        return this.currentPromptType;
    }

    /**
     * Export current prompt
     */
    exportPrompt() {
        const notifications = window.ContractApp?.modules?.notifications;
        const utils = window.ContractApp?.modules?.utils;
        
        const content = this.getCurrentPromptContent();
        if (!content) {
            notifications?.warning('No prompt content to export');
            return;
        }
        
        const exportData = {
            type: this.currentPromptType,
            content: content,
            exported_at: new Date().toISOString(),
            version: '1.0'
        };
        
        const dataStr = JSON.stringify(exportData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        
        if (utils) {
            utils.downloadFile(url, `prompt-${this.currentPromptType}-${Date.now()}.json`);
        }
        
        URL.revokeObjectURL(url);
        
        notifications?.success('Prompt exported successfully');
        console.log('Prompts: Prompt exported');
    }
}

// Export for global use
window.PromptsModule = PromptsModule;