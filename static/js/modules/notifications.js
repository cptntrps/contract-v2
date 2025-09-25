/**
 * Notifications Module
 * 
 * Handles all user notifications including success messages, errors, warnings, and info messages.
 * Provides a centralized way to show feedback to users across the application.
 */

class NotificationsModule {
    constructor() {
        this.name = 'notifications';
        this.initialized = false;
        this.notifications = new Map();
        this.defaultDuration = 5000;
        this.maxNotifications = 5;
    }

    /**
     * Initialize the notifications module
     */
    async init() {
        console.log('Notifications: Initializing notification system...');
        
        // Create notification container if it doesn't exist
        this.createContainer();
        
        // Set up global error handlers
        this.setupGlobalErrorHandlers();
        
        this.initialized = true;
        console.log('Notifications: Notification system initialized successfully');
    }

    /**
     * Handle module events
     */
    handleEvent(eventName, data) {
        switch (eventName) {
            case 'escapePressed':
                this.closeAll();
                break;
        }
    }

    /**
     * Create notification container
     */
    createContainer() {
        let container = document.getElementById('notification-container');
        
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            container.className = 'notification-container';
            document.body.appendChild(container);
        }
        
        this.container = container;
    }

    /**
     * Set up global error handlers
     */
    setupGlobalErrorHandlers() {
        // Handle unhandled JavaScript errors
        window.addEventListener('error', (event) => {
            this.show('An unexpected error occurred', 'error');
            console.error('Unhandled error:', event.error);
        });

        // Handle unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.show('An unexpected error occurred', 'error');
            console.error('Unhandled promise rejection:', event.reason);
        });
    }

    /**
     * Show notification
     * @param {string} message - The message to display
     * @param {string} type - Type of notification (success, error, warning, info)
     * @param {number} duration - How long to show (0 = permanent)
     * @param {object} options - Additional options
     */
    show(message, type = 'info', duration = null, options = {}) {
        // Validate parameters
        if (!message) {
            console.warn('Notifications: Cannot show empty message');
            return null;
        }

        const validTypes = ['success', 'error', 'warning', 'info'];
        if (!validTypes.includes(type)) {
            console.warn(`Notifications: Invalid type '${type}', using 'info'`);
            type = 'info';
        }

        // Remove old notifications if we have too many
        this.enforceMaxNotifications();

        // Create notification
        const notification = this.createNotification(message, type, duration, options);
        
        // Add to container
        this.container.appendChild(notification);
        
        // Add to tracking map
        this.notifications.set(notification.id, {
            element: notification,
            type: type,
            message: message,
            timestamp: Date.now()
        });

        // Trigger animation
        requestAnimationFrame(() => {
            notification.classList.add('show');
        });

        // Auto-remove if duration is specified
        if (duration !== 0) {
            const actualDuration = duration || this.getDefaultDuration(type);
            setTimeout(() => {
                this.close(notification.id);
            }, actualDuration);
        }

        console.log(`Notifications: Showing ${type} notification: ${message}`);
        return notification.id;
    }

    /**
     * Create notification element
     */
    createNotification(message, type, duration, options) {
        const notification = document.createElement('div');
        const id = this.generateId();
        
        notification.id = id;
        notification.className = `notification notification-${type}`;
        notification.dataset.type = type;
        notification.dataset.timestamp = Date.now();

        // Create notification content
        const content = document.createElement('div');
        content.className = 'notification-content';

        // Add icon
        const icon = document.createElement('i');
        icon.className = `fas fa-${this.getIcon(type)} notification-icon`;
        content.appendChild(icon);

        // Add message
        const messageElement = document.createElement('span');
        messageElement.className = 'notification-message';
        messageElement.textContent = message;
        content.appendChild(messageElement);

        // Add close button (unless disabled)
        if (!options.noClose) {
            const closeButton = document.createElement('button');
            closeButton.className = 'notification-close';
            closeButton.innerHTML = '<i class="fas fa-times"></i>';
            closeButton.onclick = () => this.close(id);
            closeButton.setAttribute('aria-label', 'Close notification');
            content.appendChild(closeButton);
        }

        notification.appendChild(content);

        // Add action buttons if provided
        if (options.actions && options.actions.length > 0) {
            const actionsContainer = document.createElement('div');
            actionsContainer.className = 'notification-actions';

            options.actions.forEach(action => {
                const button = document.createElement('button');
                button.className = `notification-action ${action.style || 'default'}`;
                button.textContent = action.label;
                button.onclick = () => {
                    if (action.handler) {
                        action.handler();
                    }
                    if (action.close !== false) {
                        this.close(id);
                    }
                };
                actionsContainer.appendChild(button);
            });

            notification.appendChild(actionsContainer);
        }

        return notification;
    }

    /**
     * Get icon for notification type
     */
    getIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-triangle',
            warning: 'exclamation-circle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    /**
     * Get default duration for notification type
     */
    getDefaultDuration(type) {
        const durations = {
            success: 3000,
            error: 8000,
            warning: 6000,
            info: 5000
        };
        return durations[type] || this.defaultDuration;
    }

    /**
     * Close specific notification
     */
    close(notificationId) {
        const notificationData = this.notifications.get(notificationId);
        if (!notificationData) {
            return;
        }

        const element = notificationData.element;
        
        // Add closing animation
        element.classList.add('closing');
        
        // Remove after animation
        setTimeout(() => {
            if (element.parentNode) {
                element.parentNode.removeChild(element);
            }
            this.notifications.delete(notificationId);
        }, 300);

        console.log(`Notifications: Closed notification ${notificationId}`);
    }

    /**
     * Close all notifications
     */
    closeAll() {
        const notificationIds = Array.from(this.notifications.keys());
        notificationIds.forEach(id => this.close(id));
        console.log('Notifications: Closed all notifications');
    }

    /**
     * Close notifications of specific type
     */
    closeByType(type) {
        const notificationIds = [];
        
        this.notifications.forEach((data, id) => {
            if (data.type === type) {
                notificationIds.push(id);
            }
        });
        
        notificationIds.forEach(id => this.close(id));
        console.log(`Notifications: Closed all ${type} notifications`);
    }

    /**
     * Enforce maximum number of notifications
     */
    enforceMaxNotifications() {
        if (this.notifications.size >= this.maxNotifications) {
            // Remove oldest notification
            const oldestId = Array.from(this.notifications.keys())[0];
            this.close(oldestId);
        }
    }

    /**
     * Generate unique ID for notification
     */
    generateId() {
        return `notification_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Convenience methods for different notification types
     */
    success(message, duration = null, options = {}) {
        return this.show(message, 'success', duration, options);
    }

    error(message, duration = null, options = {}) {
        return this.show(message, 'error', duration, options);
    }

    warning(message, duration = null, options = {}) {
        return this.show(message, 'warning', duration, options);
    }

    info(message, duration = null, options = {}) {
        return this.show(message, 'info', duration, options);
    }

    /**
     * Show loading notification that persists until manually closed
     */
    showLoading(message = 'Loading...') {
        return this.show(`<i class="fas fa-spinner fa-spin"></i> ${message}`, 'info', 0, { noClose: true });
    }

    /**
     * Show confirmation dialog using notifications
     */
    confirm(message, onConfirm, onCancel = null) {
        const actions = [
            {
                label: 'Confirm',
                style: 'primary',
                handler: onConfirm
            },
            {
                label: 'Cancel',
                style: 'secondary',
                handler: onCancel
            }
        ];

        return this.show(message, 'warning', 0, { actions, noClose: true });
    }

    /**
     * Get all current notifications
     */
    getAll() {
        return Array.from(this.notifications.values());
    }

    /**
     * Get notifications by type
     */
    getByType(type) {
        return Array.from(this.notifications.values()).filter(notification => notification.type === type);
    }

    /**
     * Check if there are any error notifications
     */
    hasErrors() {
        return this.getByType('error').length > 0;
    }

    /**
     * Set maximum number of notifications
     */
    setMaxNotifications(max) {
        this.maxNotifications = Math.max(1, max);
    }

    /**
     * Set default duration for notifications
     */
    setDefaultDuration(duration) {
        this.defaultDuration = Math.max(1000, duration);
    }
}

// Export for global use
window.NotificationsModule = NotificationsModule;