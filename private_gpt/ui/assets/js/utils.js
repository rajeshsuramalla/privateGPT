/**
 * Utility Functions
 */

import { NOTIFICATION_CONFIG } from './config.js';

/**
 * Notification System
 */
export function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(n => n.remove());

    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <span class="notification-icon">${NOTIFICATION_CONFIG.ICONS[type]}</span>
        <span class="notification-message">${message}</span>
        <button class="notification-close" onclick="this.parentElement.remove()">×</button>
    `;
    
    document.body.appendChild(notification);

    // Auto remove after configured time
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, NOTIFICATION_CONFIG.AUTO_DISMISS_TIME);
}

/**
 * Format message content with markdown support
 */
export function formatMessageContent(content) {
    if (!content) return '';
    
    // Escape HTML first to prevent injection
    let formatted = content
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    
    // Basic markdown formatting
    formatted = formatted
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold
        .replace(/\*(.*?)\*/g, '<em>$1</em>') // Italic
        .replace(/`(.*?)`/g, '<code style="background: #f1f5f9; padding: 2px 4px; border-radius: 3px;">$1</code>') // Inline code
        .replace(/\n/g, '<br>'); // Line breaks
    
    // Format tables (basic support)
    if (formatted.includes('|')) {
        formatted = formatted.replace(/\|([^|]+)\|([^|]+)\|([^|]+)\|/g, 
            '<div style="display: table-row;"><div style="display: table-cell; padding: 5px; border: 1px solid #e2e8f0;">$1</div><div style="display: table-cell; padding: 5px; border: 1px solid #e2e8f0;">$2</div><div style="display: table-cell; padding: 5px; border: 1px solid #e2e8f0;">$3</div></div>');
    }
    
    // Format sources section
    if (formatted.includes('**Sources:**')) {
        formatted = formatted.replace('**Sources:**', '<div class="sources-section"><strong>Sources:</strong></div>');
    }
    
    // Format code blocks
    formatted = formatted.replace(/```([^`]+)```/g, '<pre style="background: #f1f5f9; padding: 10px; border-radius: 5px; overflow-x: auto; white-space: pre-wrap;"><code>$1</code></pre>');
    
    return formatted;
}

/**
 * Generate loading messages based on file selection
 */
export function getLoadingMessage(selectedFiles) {
    if (selectedFiles.length === 0) {
        return '🔍 Processing your request...';
    }

    const hasCSV = selectedFiles.some(file => file.toLowerCase().endsWith('.csv'));
    const hasPDF = selectedFiles.some(file => file.toLowerCase().endsWith('.pdf'));
    const hasLargeFiles = selectedFiles.length > 3;
    
    if (hasCSV) {
        return '🔍 Analyzing your CSV data... This may take several minutes for large datasets.';
    } else if (hasPDF) {
        return '📄 Processing your PDF documents... Please wait.';
    } else if (hasLargeFiles) {
        return '📁 Processing multiple documents... This may take a moment.';
    } else {
        return '📖 Analyzing your documents... Please wait.';
    }
}

/**
 * Theme Management
 */
export function setTheme(theme) {
    const body = document.body;
    const themeIcon = document.getElementById('theme-icon');
    
    body.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    
    if (theme === 'dark') {
        themeIcon.textContent = '🌙';
    } else {
        themeIcon.textContent = '☀️';
    }
}

export function getStoredTheme() {
    return localStorage.getItem('theme') || 'light';
}

export function toggleTheme() {
    const currentTheme = document.body.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
}

/**
 * File utilities
 */
export function validateFileType(fileName) {
    const validExtensions = ['.pdf', '.txt', '.md', '.csv', '.doc', '.docx'];
    const extension = fileName.toLowerCase().substring(fileName.lastIndexOf('.'));
    return validExtensions.includes(extension);
}

export function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Time formatting
 */
export function formatTimestamp() {
    return new Date().toLocaleTimeString();
}

export function formatDuration(seconds) {
    return seconds.toFixed(2) + 's';
}

/**
 * DOM utilities
 */
export function createElement(tag, className, innerHTML) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (innerHTML) element.innerHTML = innerHTML;
    return element;
}

export function scrollToBottom(element) {
    element.scrollTop = element.scrollHeight;
}

/**
 * Export functionality
 */
export function exportChatToFile(messages) {
    let exportText = 'PrivateGPT Chat Export\n';
    exportText += '========================\n\n';
    
    messages.forEach((message, index) => {
        const isUser = message.classList.contains('user');
        const content = message.querySelector('.message-content');
        const text = content.textContent || content.innerText;
        
        exportText += `${isUser ? 'User' : 'Assistant'}: ${text}\n\n`;
    });
    
    // Create download link
    const blob = new Blob([exportText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `privateGPT-chat-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * Custom Confirmation Dialog
 * Replaces browser confirm() with a styled modal
 */
export function showConfirmDialog(message, title = 'Confirm Action') {
    return new Promise((resolve) => {
        const modal = document.getElementById('confirmModal');
        const titleElement = document.getElementById('confirmTitle');
        const messageElement = document.getElementById('confirmMessage');
        const cancelBtn = document.getElementById('confirmCancel');
        const okBtn = document.getElementById('confirmOk');

        // Set content
        titleElement.textContent = title;
        messageElement.textContent = message;

        // Show modal with animation
        modal.style.display = 'flex';
        requestAnimationFrame(() => {
            modal.classList.add('show');
        });

        // Handle responses
        function closeModal(result) {
            modal.classList.remove('show');
            setTimeout(() => {
                modal.style.display = 'none';
            }, 300);
            resolve(result);
        }

        // Event handlers
        function onCancel() {
            cancelBtn.removeEventListener('click', onCancel);
            okBtn.removeEventListener('click', onOk);
            modal.removeEventListener('click', onOverlayClick);
            document.removeEventListener('keydown', onKeyDown);
            closeModal(false);
        }

        function onOk() {
            cancelBtn.removeEventListener('click', onCancel);
            okBtn.removeEventListener('click', onOk);
            modal.removeEventListener('click', onOverlayClick);
            document.removeEventListener('keydown', onKeyDown);
            closeModal(true);
        }

        function onOverlayClick(e) {
            if (e.target === modal) {
                onCancel();
            }
        }

        function onKeyDown(e) {
            if (e.key === 'Escape') {
                onCancel();
            } else if (e.key === 'Enter') {
                onOk();
            }
        }

        // Attach event listeners
        cancelBtn.addEventListener('click', onCancel);
        okBtn.addEventListener('click', onOk);
        modal.addEventListener('click', onOverlayClick);
        document.addEventListener('keydown', onKeyDown);

        // Focus the OK button for accessibility
        setTimeout(() => okBtn.focus(), 100);
    });
}
