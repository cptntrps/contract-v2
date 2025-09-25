/**
 * Utilities Module
 * 
 * Shared utility functions used across the application.
 * This module provides common functionality like date formatting, file size formatting,
 * API helpers, and other utility functions.
 */

class UtilsModule {
    constructor() {
        this.name = 'utils';
        this.initialized = false;
    }

    /**
     * Initialize the utils module
     */
    async init() {
        console.log('Utils: Initializing utilities...');
        this.initialized = true;
        console.log('Utils: Utilities initialized successfully');
    }

    /**
     * Handle module events
     */
    handleEvent(eventName, data) {
        // Utils module doesn't need to handle events currently
    }

    /**
     * Format file size from bytes to human readable format
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Format date to readable format
     */
    formatDate(dateString) {
        if (!dateString) return 'N/A';
        
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (error) {
            console.error('Utils: Error formatting date:', error);
            return 'Invalid Date';
        }
    }

    /**
     * Format date to short format (date only)
     */
    formatDateShort(dateString) {
        if (!dateString) return 'N/A';
        
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US');
        } catch (error) {
            console.error('Utils: Error formatting date:', error);
            return 'Invalid Date';
        }
    }

    /**
     * Debounce function execution
     */
    debounce(func, delay) {
        let timeoutId;
        return function (...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    }

    /**
     * Throttle function execution
     */
    throttle(func, limit) {
        let inThrottle;
        return function (...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    /**
     * Make API request with error handling
     */
    async apiRequest(endpoint, options = {}) {
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        };

        const requestOptions = { ...defaultOptions, ...options };

        try {
            console.log(`Utils: Making ${requestOptions.method} request to ${endpoint}`);
            
            const response = await fetch(endpoint, requestOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log(`Utils: Request to ${endpoint} successful`);
            return data;
            
        } catch (error) {
            console.error(`Utils: API request failed for ${endpoint}:`, error);
            throw error;
        }
    }

    /**
     * Download file from URL
     */
    downloadFile(url, filename = null) {
        try {
            const link = document.createElement('a');
            link.href = url;
            
            if (filename) {
                link.download = filename;
            }
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            console.log(`Utils: File download initiated: ${filename || url}`);
            
        } catch (error) {
            console.error('Utils: Error downloading file:', error);
            throw error;
        }
    }

    /**
     * Validate file type
     */
    validateFileType(file, allowedTypes = ['.docx']) {
        const fileName = file.name.toLowerCase();
        const isValid = allowedTypes.some(type => fileName.endsWith(type.toLowerCase()));
        
        if (!isValid) {
            console.warn(`Utils: Invalid file type: ${fileName}. Allowed: ${allowedTypes.join(', ')}`);
        }
        
        return isValid;
    }

    /**
     * Validate file size
     */
    validateFileSize(file, maxSizeMB = 16) {
        const maxSizeBytes = maxSizeMB * 1024 * 1024;
        const isValid = file.size <= maxSizeBytes;
        
        if (!isValid) {
            console.warn(`Utils: File too large: ${this.formatFileSize(file.size)}. Max: ${maxSizeMB}MB`);
        }
        
        return isValid;
    }

    /**
     * Generate unique ID
     */
    generateId(prefix = 'id') {
        return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Sanitize HTML to prevent XSS
     */
    sanitizeHTML(str) {
        const temp = document.createElement('div');
        temp.textContent = str;
        return temp.innerHTML;
    }

    /**
     * Copy text to clipboard
     */
    async copyToClipboard(text) {
        try {
            if (navigator.clipboard) {
                await navigator.clipboard.writeText(text);
                console.log('Utils: Text copied to clipboard');
                return true;
            } else {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = text;
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                
                const successful = document.execCommand('copy');
                document.body.removeChild(textArea);
                
                if (successful) {
                    console.log('Utils: Text copied to clipboard (fallback)');
                    return true;
                } else {
                    throw new Error('Copy command failed');
                }
            }
        } catch (error) {
            console.error('Utils: Failed to copy to clipboard:', error);
            throw error;
        }
    }

    /**
     * Format number with commas
     */
    formatNumber(num) {
        if (num === null || num === undefined) return '0';
        return num.toLocaleString();
    }

    /**
     * Get confidence CSS class based on percentage
     */
    getConfidenceClass(confidence) {
        if (confidence >= 90) return 'high';
        if (confidence >= 70) return 'medium';
        return 'low';
    }

    /**
     * Get status CSS class based on status text
     */
    getStatusClass(status) {
        if (!status) return 'unknown';
        
        const statusLower = status.toLowerCase();
        if (statusLower === 'no changes' || statusLower.includes('success')) return 'success';
        if (statusLower.includes('minor')) return 'info';
        if (statusLower.includes('moderate')) return 'warning';
        if (statusLower.includes('critical') || statusLower.includes('error')) return 'danger';
        return 'default';
    }

    /**
     * Get next step suggestion based on status
     */
    getNextStepSuggestion(status) {
        if (!status) return 'Review Required';
        
        const statusLower = status.toLowerCase();
        if (statusLower === 'no changes') return 'Proceed without Legal';
        if (statusLower.includes('minor')) return 'Quick Review';
        if (statusLower.includes('moderate')) return 'Legal Review';
        return 'Requires Legal Review';
    }

    /**
     * Check if device is mobile
     */
    isMobile() {
        return window.innerWidth <= 768;
    }

    /**
     * Check if device is tablet
     */
    isTablet() {
        return window.innerWidth > 768 && window.innerWidth <= 1024;
    }

    /**
     * Check if device is desktop
     */
    isDesktop() {
        return window.innerWidth > 1024;
    }

    /**
     * Animate numeric value change
     */
    animateValue(element, startValue, endValue, duration = 1000) {
        if (!element) return;
        
        const startTime = performance.now();
        const startNum = parseInt(startValue) || 0;
        const endNum = parseInt(endValue) || 0;
        
        const animate = (currentTime) => {
            const elapsedTime = currentTime - startTime;
            const progress = Math.min(elapsedTime / duration, 1);
            
            const currentValue = Math.floor(startNum + (endNum - startNum) * progress);
            element.textContent = this.formatNumber(currentValue);
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }

    /**
     * Create loading spinner element
     */
    createLoadingSpinner(size = 'medium') {
        const spinner = document.createElement('div');
        spinner.className = `loading-spinner ${size}`;
        spinner.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        return spinner;
    }

    /**
     * Show/hide loading state on element
     */
    setLoadingState(element, isLoading, text = 'Loading...') {
        if (!element) return;
        
        if (isLoading) {
            element.classList.add('loading');
            element.dataset.originalText = element.textContent;
            element.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${text}`;
        } else {
            element.classList.remove('loading');
            if (element.dataset.originalText) {
                element.textContent = element.dataset.originalText;
                delete element.dataset.originalText;
            }
        }
    }

    /**
     * Wait for specified time
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Retry function with exponential backoff
     */
    async retry(fn, maxAttempts = 3, baseDelay = 1000) {
        for (let attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                return await fn();
            } catch (error) {
                if (attempt === maxAttempts) {
                    throw error;
                }
                
                const delay = baseDelay * Math.pow(2, attempt - 1);
                console.warn(`Utils: Retry attempt ${attempt} failed, waiting ${delay}ms...`);
                await this.sleep(delay);
            }
        }
    }
}

// Export for global use
window.UtilsModule = UtilsModule;