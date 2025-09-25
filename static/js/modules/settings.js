/**
 * Settings Module
 * 
 * Handles system configuration including LLM model settings, provider configuration,
 * cache management, and other system settings.
 */

class SettingsModule {
    constructor() {
        this.name = 'settings';
        this.initialized = false;
        this.currentProvider = 'openai';
        this.availableModels = [];
        this.currentModel = '';
        this.modelSwitchInProgress = false;
        this.settings = {};
    }

    /**
     * Initialize the settings module
     */
    async init() {
        console.log('Settings: Initializing settings system...');
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Load initial settings
        await this.loadSettings();
        
        this.initialized = true;
        console.log('Settings: Settings system initialized successfully');
    }

    /**
     * Handle module events
     */
    handleEvent(eventName, data) {
        switch (eventName) {
            case 'tabChanged':
                if (data.currentTab === 'settings') {
                    this.onTabActivated();
                }
                break;
        }
    }

    /**
     * Called when settings tab is activated
     */
    onTabActivated() {
        console.log('Settings: Tab activated, refreshing settings...');
        this.loadSettings();
    }

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Model selection
        this.setupModelListeners();
        
        // Provider settings
        this.setupProviderListeners();
        
        // Cache management
        this.setupCacheListeners();
        
        // System settings
        this.setupSystemListeners();
        
        console.log('Settings: Event listeners setup complete');
    }

    /**
     * Set up model-related listeners
     */
    setupModelListeners() {
        // OpenAI model selection
        const openaiModelSelect = document.getElementById('openaiModel');
        if (openaiModelSelect) {
            openaiModelSelect.addEventListener('change', (e) => {
                this.changeOpenAIModel(e.target.value);
            });
        }

        // Refresh models button
        const refreshButton = document.getElementById('refreshModels');
        if (refreshButton) {
            refreshButton.addEventListener('click', () => {
                this.refreshOpenAIModels();
            });
        }

        // Temperature slider
        const temperatureSlider = document.getElementById('temperatureSlider');
        const temperatureValue = document.getElementById('temperatureValue');
        
        if (temperatureSlider && temperatureValue) {
            temperatureSlider.addEventListener('input', (e) => {
                temperatureValue.textContent = e.target.value;
            });
            
            temperatureSlider.addEventListener('change', (e) => {
                this.updateLLMSettings({ temperature: parseFloat(e.target.value) });
            });
        }

        // Max tokens input
        const maxTokensInput = document.getElementById('maxTokensInput');
        if (maxTokensInput) {
            maxTokensInput.addEventListener('change', (e) => {
                this.updateLLMSettings({ max_tokens: parseInt(e.target.value) });
            });
        }
    }

    /**
     * Set up provider-related listeners
     */
    setupProviderListeners() {
        const providerSelector = document.getElementById('providerSelector');
        if (providerSelector) {
            providerSelector.addEventListener('change', (e) => {
                this.switchProvider(e.target.value);
            });
        }
    }

    /**
     * Set up cache-related listeners
     */
    setupCacheListeners() {
        const cacheButtons = {
            'clearAnalysisCache': () => this.clearCache('analysis'),
            'clearReportsCache': () => this.clearCache('reports'),
            'clearMemoryCache': () => this.clearCache('memory'),
            'clearAllCache': () => this.clearCache('all')
        };

        Object.entries(cacheButtons).forEach(([id, handler]) => {
            const button = document.getElementById(id);
            if (button) {
                button.addEventListener('click', handler);
            }
        });
    }

    /**
     * Set up system-related listeners
     */
    setupSystemListeners() {
        // System refresh
        const systemRefreshButton = document.getElementById('systemRefresh');
        if (systemRefreshButton) {
            systemRefreshButton.addEventListener('click', () => {
                this.refreshSystemStatus();
            });
        }
    }

    /**
     * Load all settings
     */
    async loadSettings() {
        console.log('Settings: Loading settings...');
        
        await Promise.all([
            this.loadLLMProviderInfo(),
            this.loadOpenAIModels(),
            this.loadCurrentModelInfo(),
            this.loadCacheStats(),
            this.loadSystemSettings()
        ]);
        
        console.log('Settings: Settings loaded successfully');
    }

    /**
     * Load LLM provider information
     */
    async loadLLMProviderInfo() {
        const utils = window.ContractApp?.modules?.utils;
        
        try {
            const data = await utils?.apiRequest('/api/llm-provider');
            
            if (data?.success) {
                this.currentProvider = data.provider;
                this.currentModel = data.model;
                
                // Update provider display
                this.updateProviderDisplay(data);
                
                // Update model settings
                this.updateModelSettings(data.temperature, data.max_tokens);
                
                console.log('Settings: LLM provider info loaded:', data);
            }
            
        } catch (error) {
            console.error('Settings: Error loading LLM provider info:', error);
        }
    }

    /**
     * Load OpenAI models
     */
    async loadOpenAIModels() {
        const notifications = window.ContractApp?.modules?.notifications;
        const utils = window.ContractApp?.modules?.utils;
        
        const modelSelect = document.getElementById('openaiModel');
        if (!modelSelect) return;
        
        try {
            // Show loading state
            modelSelect.innerHTML = '<option value="">Loading OpenAI models...</option>';
            
            const data = await utils?.apiRequest('/api/openai-models');
            
            if (data?.success && data.models) {
                this.availableModels = data.models;
                this.updateOpenAIModelDropdown(data.models, data.current_model);
                console.log(`Settings: Loaded ${data.models.length} OpenAI models`);
            } else {
                throw new Error(data?.error || 'Failed to load models');
            }
            
        } catch (error) {
            console.error('Settings: Error loading OpenAI models:', error);
            modelSelect.innerHTML = '<option value="">Error loading models</option>';
            notifications?.error('Failed to load OpenAI models');
        }
    }

    /**
     * Update OpenAI model dropdown
     */
    updateOpenAIModelDropdown(models, currentModel) {
        const modelSelect = document.getElementById('openaiModel');
        if (!modelSelect) return;
        
        // Clear existing options
        modelSelect.innerHTML = '';
        
        // Add default option
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = 'Select an OpenAI model...';
        defaultOption.disabled = true;
        modelSelect.appendChild(defaultOption);
        
        // Add model options
        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model.name;
            option.textContent = `${model.name} - ${model.tier?.toUpperCase() || 'STANDARD'}`;
            
            if (model.recommended) {
                option.textContent += ' ⭐ RECOMMENDED';
            }
            
            if (model.name === currentModel) {
                option.selected = true;
                this.updateModelDescription(model);
            }
            
            modelSelect.appendChild(option);
        });
        
        console.log(`Settings: Updated model dropdown with ${models.length} models`);
    }

    /**
     * Load current model information
     */
    async loadCurrentModelInfo() {
        const utils = window.ContractApp?.modules?.utils;
        
        try {
            const data = await utils?.apiRequest('/api/model-info');
            
            if (data) {
                this.updateCurrentModelStatus(
                    data.model || data.name,
                    data.connection_healthy ? 'Connected' : 'Disconnected'
                );
            }
            
        } catch (error) {
            console.error('Settings: Error loading current model info:', error);
            this.updateCurrentModelStatus('Unknown', 'Error');
        }
    }

    /**
     * Load cache statistics
     */
    async loadCacheStats() {
        const utils = window.ContractApp?.modules?.utils;
        
        try {
            const data = await utils?.apiRequest('/api/cache-stats');
            
            if (data?.success) {
                this.displayCacheStats(data.stats);
            }
            
        } catch (error) {
            console.error('Settings: Error loading cache stats:', error);
        }
    }

    /**
     * Load system settings
     */
    async loadSystemSettings() {
        // Load other system settings if needed
        console.log('Settings: Loading system settings...');
        
        // Placeholder for additional system settings
        this.settings.fileUploadLimit = '16MB';
        this.settings.maxAnalysisResults = 1000;
        
        this.updateSystemSettingsDisplay();
    }

    /**
     * Update provider display
     */
    updateProviderDisplay(data) {
        const providerElement = document.getElementById('current-provider');
        const healthElement = document.getElementById('provider-health');
        const providerSelector = document.getElementById('providerSelector');
        
        if (providerElement) {
            providerElement.textContent = data.provider.toUpperCase();
        }
        
        if (healthElement) {
            healthElement.className = `health-indicator ${data.api_key_configured ? 'health-healthy' : 'health-unhealthy'}`;
        }
        
        if (providerSelector) {
            providerSelector.value = data.provider;
        }
        
        // Show/hide appropriate settings sections
        this.toggleProviderSections(data.provider);
    }

    /**
     * Toggle provider-specific sections
     */
    toggleProviderSections(provider) {
        const openaiSettings = document.getElementById('openai-settings');
        
        if (provider === 'openai') {
            if (openaiSettings) openaiSettings.style.display = 'block';
        } else {
            if (openaiSettings) openaiSettings.style.display = 'none';
        }
    }

    /**
     * Update model settings display
     */
    updateModelSettings(temperature, maxTokens) {
        const temperatureSlider = document.getElementById('temperatureSlider');
        const temperatureValue = document.getElementById('temperatureValue');
        const maxTokensInput = document.getElementById('maxTokensInput');
        
        if (temperatureSlider && temperatureValue && temperature !== undefined) {
            temperatureSlider.value = temperature;
            temperatureValue.textContent = temperature;
        }
        
        if (maxTokensInput && maxTokens !== undefined) {
            maxTokensInput.value = maxTokens;
        }
    }

    /**
     * Update current model status display
     */
    updateCurrentModelStatus(modelName, status) {
        const statusModel = document.getElementById('status-model');
        const statusConnection = document.getElementById('status-connection');
        
        if (statusModel) {
            statusModel.textContent = modelName || 'Unknown';
        }
        
        if (statusConnection) {
            statusConnection.textContent = status || 'Unknown';
            statusConnection.className = status === 'Connected' ? 'status-connected' : 'status-disconnected';
        }
    }

    /**
     * Update model description display
     */
    updateModelDescription(model) {
        const modelDescription = document.getElementById('model-description');
        if (!modelDescription) return;
        
        modelDescription.innerHTML = `
            <div class="model-info">
                <strong>${model.name}</strong>
                <span class="model-tier">${model.tier?.toUpperCase() || 'STANDARD'}</span>
                ${model.recommended ? '<span class="recommended">⭐ RECOMMENDED</span>' : ''}
            </div>
            <div class="model-description-text">
                ${model.description || 'No description available'}
            </div>
            <div class="model-specs">
                <span>Context: ${model.context_window?.toLocaleString() || 'N/A'} tokens</span>
            </div>
        `;
    }

    /**
     * Display cache statistics
     */
    displayCacheStats(stats) {
        const cacheStatsDiv = document.getElementById('cacheStats');
        if (!cacheStatsDiv) return;
        
        cacheStatsDiv.innerHTML = `
            <div class="cache-stats">
                <h3>Cache Statistics</h3>
                <div class="cache-section">
                    <h4>Memory Cache</h4>
                    <ul>
                        <li>Analysis Results: ${stats.memory?.analysis_results || 0}</li>
                        <li>Contracts: ${stats.memory?.contracts || 0}</li>
                        <li>Templates: ${stats.memory?.templates || 0}</li>
                    </ul>
                </div>
                <div class="cache-section">
                    <h4>File Cache</h4>
                    <ul>
                        <li>Analysis JSON: ${stats.files?.analysis_json_exists ? 'Yes' : 'No'} (${this.formatBytes(stats.files?.analysis_json_size || 0)})</li>
                        <li>Report Files: ${stats.files?.reports_count || 0} files (${stats.files?.reports_size_mb || 0} MB)</li>
                    </ul>
                </div>
            </div>
        `;
    }

    /**
     * Update system settings display
     */
    updateSystemSettingsDisplay() {
        // Update system settings display if needed
        console.log('Settings: System settings display updated');
    }

    /**
     * Change OpenAI model
     */
    async changeOpenAIModel(modelName) {
        if (this.modelSwitchInProgress) return;
        if (!modelName) return;
        
        const notifications = window.ContractApp?.modules?.notifications;
        const utils = window.ContractApp?.modules?.utils;
        
        console.log(`Settings: Changing OpenAI model to ${modelName}...`);
        this.modelSwitchInProgress = true;
        
        notifications?.info(`Switching to model: ${modelName}...`);
        
        try {
            const response = await utils?.apiRequest('/api/update-openai-model', {
                method: 'POST',
                body: JSON.stringify({ model: modelName })
            });
            
            if (response?.success) {
                notifications?.success(`Successfully switched to ${modelName}`);
                this.updateCurrentModelStatus(modelName, 'Connected');
                
                // Update model description
                const model = this.availableModels.find(m => m.name === modelName);
                if (model) {
                    this.updateModelDescription(model);
                }
                
            } else {
                throw new Error(response?.error || 'Failed to switch model');
            }
            
        } catch (error) {
            console.error('Settings: Error changing model:', error);
            notifications?.error(`Failed to change model: ${error.message}`);
            
            // Reset dropdown to previous selection
            this.loadOpenAIModels();
        } finally {
            this.modelSwitchInProgress = false;
        }
    }

    /**
     * Refresh OpenAI models
     */
    refreshOpenAIModels() {
        const notifications = window.ContractApp?.modules?.notifications;
        
        console.log('Settings: Refreshing OpenAI models...');
        notifications?.info('Refreshing model list...');
        
        this.loadOpenAIModels();
    }

    /**
     * Switch LLM provider
     */
    switchProvider(providerType) {
        const notifications = window.ContractApp?.modules?.notifications;
        
        console.log(`Settings: Switching to provider: ${providerType}`);
        notifications?.info('Switching LLM provider...');
        
        // Update display
        this.toggleProviderSections(providerType);
        
        // Update provider in backend
        this.updateLLMProvider(providerType);
        
        // Update provider display
        const providerElement = document.getElementById('current-provider');
        if (providerElement) {
            providerElement.textContent = providerType.toUpperCase();
        }
    }

    /**
     * Update LLM provider in backend
     */
    async updateLLMProvider(providerType) {
        const utils = window.ContractApp?.modules?.utils;
        
        try {
            const response = await utils?.apiRequest('/api/user-config', {
                method: 'POST',
                body: JSON.stringify({
                    llm_settings: {
                        provider: providerType
                    }
                })
            });
            
            if (response?.success) {
                console.log('Settings: Provider updated successfully');
                this.loadCurrentModelInfo();
            }
            
        } catch (error) {
            console.error('Settings: Error updating provider:', error);
        }
    }

    /**
     * Update LLM settings
     */
    async updateLLMSettings(settings) {
        const notifications = window.ContractApp?.modules?.notifications;
        const utils = window.ContractApp?.modules?.utils;
        
        console.log('Settings: Updating LLM settings:', settings);
        
        try {
            const response = await utils?.apiRequest('/api/llm-settings', {
                method: 'POST',
                body: JSON.stringify(settings)
            });
            
            if (response?.success) {
                notifications?.success('Settings updated successfully');
                console.log('Settings: LLM settings updated:', response.updated_settings);
            } else {
                throw new Error(response?.error || 'Settings update failed');
            }
            
        } catch (error) {
            console.error('Settings: Error updating LLM settings:', error);
            notifications?.error(`Settings update failed: ${error.message}`);
        }
    }

    /**
     * Clear cache
     */
    async clearCache(cacheType = 'all') {
        const notifications = window.ContractApp?.modules?.notifications;
        const utils = window.ContractApp?.modules?.utils;
        
        const confirmed = confirm(`Are you sure you want to clear ${cacheType} cache? This action cannot be undone.`);
        if (!confirmed) return;
        
        console.log(`Settings: Clearing ${cacheType} cache...`);
        notifications?.info('Clearing cache...');
        
        try {
            const response = await utils?.apiRequest('/api/clear-cache', {
                method: 'POST',
                body: JSON.stringify({ cache_type: cacheType })
            });
            
            if (response?.success) {
                notifications?.success(`Cache cleared successfully: ${response.cleared_items?.join(', ') || 'completed'}`);
                
                // Refresh cache stats and main data
                this.loadCacheStats();
                
                const core = window.ContractApp?.core;
                if (core) {
                    core.refresh();
                }
                
            } else {
                throw new Error(response?.message || 'Failed to clear cache');
            }
            
        } catch (error) {
            console.error('Settings: Error clearing cache:', error);
            notifications?.error(`Error clearing cache: ${error.message}`);
        }
    }

    /**
     * Refresh system status
     */
    async refreshSystemStatus() {
        const notifications = window.ContractApp?.modules?.notifications;
        
        console.log('Settings: Refreshing system status...');
        notifications?.info('Refreshing system status...');
        
        await this.loadSettings();
        
        notifications?.success('System status refreshed');
    }

    /**
     * Format bytes for display
     */
    formatBytes(bytes) {
        const utils = window.ContractApp?.modules?.utils;
        return utils ? utils.formatFileSize(bytes) : `${bytes} bytes`;
    }

    /**
     * Get current settings
     */
    getCurrentSettings() {
        return {
            provider: this.currentProvider,
            model: this.currentModel,
            availableModels: this.availableModels.length,
            settings: this.settings
        };
    }

    /**
     * Export settings
     */
    exportSettings() {
        const settings = this.getCurrentSettings();
        const dataStr = JSON.stringify(settings, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        
        const utils = window.ContractApp?.modules?.utils;
        const url = URL.createObjectURL(dataBlob);
        
        if (utils) {
            utils.downloadFile(url, 'contract-analyzer-settings.json');
        }
        
        URL.revokeObjectURL(url);
        
        const notifications = window.ContractApp?.modules?.notifications;
        notifications?.success('Settings exported successfully');
    }

    /**
     * Reset settings to defaults
     */
    resetSettings() {
        const confirmed = confirm('Are you sure you want to reset all settings to defaults?');
        if (!confirmed) return;
        
        const notifications = window.ContractApp?.modules?.notifications;
        notifications?.info('Resetting settings to defaults...');
        
        // Reset UI elements to defaults
        const temperatureSlider = document.getElementById('temperatureSlider');
        const maxTokensInput = document.getElementById('maxTokensInput');
        
        if (temperatureSlider) {
            temperatureSlider.value = 0.7;
            document.getElementById('temperatureValue').textContent = '0.7';
        }
        
        if (maxTokensInput) {
            maxTokensInput.value = 4000;
        }
        
        // Update backend settings
        this.updateLLMSettings({
            temperature: 0.7,
            max_tokens: 4000
        });
        
        notifications?.success('Settings reset to defaults');
    }
}

// Export for global use
window.SettingsModule = SettingsModule;