/**
 * UI Interactions and Components
 */

import { APP_CONFIG, FILE_CONFIG } from './config.js';
import { uploadFiles, getFileList, deleteFile, sendChatMessage, getModelInfo } from './api.js';
import { 
    showNotification, 
    formatMessageContent, 
    getLoadingMessage,
    showConfirmDialog,
    formatTimestamp, 
    formatDuration,
    scrollToBottom,
    exportChatToFile
} from './utils.js';

// Application state
export const appState = {
    currentMode: APP_CONFIG.MODES.RAG,
    selectedFiles: [],
    uploadedFiles: []
};

/**
 * Initialize UI components
 */
export function initializeUI() {
    initializeModeSelector();
    initializeFileUpload();
    initializeChatInput();
    initializeControlButtons();
}

/**
 * Mode Selector functionality
 */
function initializeModeSelector() {
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            appState.currentMode = this.dataset.mode;
            document.getElementById('mode-description').textContent = APP_CONFIG.MODE_DESCRIPTIONS[appState.currentMode];
        });
    });
}

/**
 * File Upload functionality
 */
function initializeFileUpload() {
    const fileInput = document.getElementById('file-input');
    fileInput.addEventListener('change', handleFileUpload);
}

async function handleFileUpload(e) {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    const uploadBtn = document.getElementById('upload-btn');
    const progressDiv = document.getElementById('upload-progress');
    const statusText = document.getElementById('status-text');
    const statusIcon = document.querySelector('.status-icon');
    const progressFill = document.getElementById('progress-fill');

    // Show progress and disable button
    uploadBtn.disabled = true;
    uploadBtn.textContent = '⏳ Uploading...';
    progressDiv.classList.add('show');
    progressFill.style.width = '0%';

    try {
        // Phase 1: File Upload
        updateUploadProgress(FILE_CONFIG.UPLOAD_PHASES.UPLOAD, files.length);

        const result = await uploadFiles(files);
        console.log('Upload successful:', result);

        // Phase 2: Processing/Ingestion
        updateUploadProgress(FILE_CONFIG.UPLOAD_PHASES.PROCESSING);
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Phase 3: Embedding Generation
        updateUploadProgress(FILE_CONFIG.UPLOAD_PHASES.EMBEDDING);
        await new Promise(resolve => setTimeout(resolve, 2000));

        // Phase 4: Complete
        updateUploadProgress(FILE_CONFIG.UPLOAD_PHASES.COMPLETE);

        // Refresh file list
        await loadFileList();

        // Show success notification
        showNotification(`Successfully processed ${files.length} file(s)`, 'success');

        // Hide progress after delay
        setTimeout(() => {
            progressDiv.classList.remove('show');
            uploadBtn.disabled = false;
            uploadBtn.textContent = '📁 Upload Files';
        }, 2000);

    } catch (error) {
        console.error('Upload error:', error);
        
        // Show error state
        statusIcon.textContent = '❌';
        statusText.textContent = 'Upload failed!';
        progressFill.style.width = '100%';
        progressFill.style.background = 'var(--error-color)';
        
        showNotification('Failed to upload files: ' + error.message, 'error');
        
        // Reset after delay
        setTimeout(() => {
            progressDiv.classList.remove('show');
            uploadBtn.disabled = false;
            uploadBtn.textContent = '📁 Upload Files';
            progressFill.style.background = 'var(--primary-gradient)';
        }, 3000);
    }

    // Clear the input
    e.target.value = '';
}

function updateUploadProgress(phase, fileCount = null) {
    const statusText = document.getElementById('status-text');
    const statusIcon = document.querySelector('.status-icon');
    const progressFill = document.getElementById('progress-fill');

    statusIcon.textContent = phase.icon;
    statusText.textContent = fileCount ? `${phase.text.replace('files', `${fileCount} file(s)`)}` : phase.text;
    progressFill.style.width = `${phase.progress}%`;
}

/**
 * File List Management
 */
export async function loadFileList() {
    try {
        const data = await getFileList();
        appState.uploadedFiles = data.files || [];
        updateFileList();
    } catch (error) {
        console.error('Error loading files:', error);
        showNotification('Failed to load file list', 'error');
    }
}

function updateFileList() {
    const fileList = document.getElementById('file-list');
    if (appState.uploadedFiles.length === 0) {
        fileList.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 20px;">No files uploaded yet</div>';
        return;
    }

    fileList.innerHTML = appState.uploadedFiles.map(file => 
        `<div class="file-item ${appState.selectedFiles.includes(file.name) ? 'selected' : ''}" data-filename="${file.name}">
            <div class="file-info" onclick="toggleFileSelection('${file.name}')">
                📄 ${file.name}
            </div>
            <div class="file-actions">
                <button class="delete-file-btn" onclick="handleDeleteFile('${file.name}')" title="Delete file">🗑️</button>
            </div>
        </div>`
    ).join('');
}

window.toggleFileSelection = function(filename) {
    const fileItem = document.querySelector(`[data-filename="${filename}"]`);
    if (appState.selectedFiles.includes(filename)) {
        appState.selectedFiles = appState.selectedFiles.filter(f => f !== filename);
        fileItem.classList.remove('selected');
    } else {
        appState.selectedFiles.push(filename);
        fileItem.classList.add('selected');
    }
};

window.handleDeleteFile = async function(filename) {
    const confirmed = await showConfirmDialog(
        `Are you sure you want to delete "${filename}"?`,
        'Delete File'
    );
    
    if (!confirmed) {
        return;
    }

    try {
        await deleteFile(filename);

        // Remove from local arrays
        appState.uploadedFiles = appState.uploadedFiles.filter(f => f.name !== filename);
        appState.selectedFiles = appState.selectedFiles.filter(f => f !== filename);

        // Update UI
        updateFileList();
        
        // Show success message
        showNotification(`File "${filename}" deleted successfully`, 'success');
    } catch (error) {
        console.error('Delete error:', error);
        showNotification(`Failed to delete file: ${error.message}`, 'error');
    }
};

/**
 * Chat functionality
 */
function initializeChatInput() {
    const messageInput = document.getElementById('message-input');
    messageInput.addEventListener('keypress', handleKeyPress);
    
    const sendBtn = document.getElementById('send-btn');
    sendBtn.addEventListener('click', sendMessage);
}

function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

async function sendMessage() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();
    if (!message) return;

    const sendBtn = document.getElementById('send-btn');
    const loading = document.getElementById('loading');
    
    // Disable input and show loading
    input.disabled = true;
    sendBtn.disabled = true;
    loading.style.display = 'block';

    // Add user message to chat
    addMessage(message, 'user');
    input.value = '';

    // Add placeholder for assistant response
    const assistantMessageId = 'msg-' + Date.now();
    const loadingMessage = getLoadingMessage(appState.selectedFiles);
    addMessage(loadingMessage, 'assistant', assistantMessageId);

    // Start time tracking
    const startTime = Date.now();

    try {
        // Get system prompt
        const systemPrompt = document.getElementById('system-prompt').value;
        
        // Send request to API
        const data = await sendChatMessage(
            message, 
            appState.currentMode, 
            appState.selectedFiles, 
            systemPrompt || null
        );

        console.log('Received response data:', data);
        let responseText = data.response;

        // Add sources if available
        if (data.sources && data.sources.length > 0) {
            responseText += '\n\n**Sources:**\n';
            data.sources.forEach((source, index) => {
                responseText += `${index + 1}. ${source.file} (page ${source.page})\n`;
            });
        }

        // Calculate time taken
        const endTime = Date.now();
        const timeTaken = formatDuration((endTime - startTime) / 1000);

        // Update the assistant message with the response and time
        updateMessage(assistantMessageId, responseText, timeTaken);
    } catch (error) {
        const endTime = Date.now();
        const timeTaken = formatDuration((endTime - startTime) / 1000);
        
        let errorMessage;
        if (error.name === 'AbortError') {
            errorMessage = 'Request timed out after 15 minutes. For large datasets, this may be normal - please check the console logs to see if processing completed.';
        } else {
            errorMessage = 'Sorry, I encountered an error processing your request: ' + error.message;
        }
        
        updateMessage(assistantMessageId, errorMessage, timeTaken);
        console.error('Error:', error);
    } finally {
        // Re-enable input and hide loading
        input.disabled = false;
        sendBtn.disabled = false;
        loading.style.display = 'none';
        input.focus();
    }
}

function addMessage(content, sender, messageId = null) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    if (messageId) {
        messageDiv.id = messageId;
    }
    
    const formattedContent = formatMessageContent(content);
    const timestamp = formatTimestamp();
    messageDiv.innerHTML = `
        <div class="message-content">${formattedContent}</div>
        <div class="message-time">${timestamp}</div>
    `;
    messagesContainer.appendChild(messageDiv);
    scrollToBottom(messagesContainer);
}

function updateMessage(messageId, content, timeTaken = null) {
    const messageElement = document.getElementById(messageId);
    if (messageElement) {
        const contentDiv = messageElement.querySelector('.message-content');
        const timeDiv = messageElement.querySelector('.message-time');
        
        if (contentDiv) {
            try {
                contentDiv.innerHTML = formatMessageContent(content);
            } catch (error) {
                console.error('Error formatting message content:', error);
                contentDiv.innerHTML = content; // Fallback to plain text
            }
        }
        
        if (timeDiv && timeTaken) {
            const timestamp = formatTimestamp();
            timeDiv.innerHTML = `${timestamp} (${timeTaken})`;
        }
    }
}

/**
 * Control buttons functionality
 */
function initializeControlButtons() {
    // Clear chat button
    const clearBtn = document.querySelector('[onclick="clearChat()"]');
    if (clearBtn) {
        clearBtn.onclick = clearChat;
    }

    // Export chat button
    const exportBtn = document.querySelector('[onclick="exportChat()"]');
    if (exportBtn) {
        exportBtn.onclick = exportChat;
    }
}

async function clearChat() {
    const confirmed = await showConfirmDialog(
        'Are you sure you want to clear the chat history?',
        'Clear Chat History'
    );
    
    if (!confirmed) {
        return;
    }
    
    const messagesContainer = document.getElementById('chat-messages');
    messagesContainer.innerHTML = '';
    showNotification('Chat cleared successfully', 'success');
}

function exportChat() {
    const messagesContainer = document.getElementById('chat-messages');
    const messages = messagesContainer.querySelectorAll('.message');
    
    if (messages.length === 0) {
        showNotification('No messages to export', 'info');
        return;
    }
    
    exportChatToFile(messages);
    showNotification('Chat exported successfully', 'success');
}

/**
 * Load model information
 */
export async function loadModelInfo() {
    try {
        const data = await getModelInfo();
        const modelInfoElement = document.getElementById('model-info');
        if (data.model_name) {
            modelInfoElement.textContent = `LLM: ${data.llm_mode} | Model: ${data.model_name}`;
        } else {
            modelInfoElement.textContent = `LLM: ${data.llm_mode}`;
        }
    } catch (error) {
        console.error('Error loading model info:', error);
    }
}

// Make functions available globally for onclick handlers
window.clearChat = clearChat;
window.exportChat = exportChat;
