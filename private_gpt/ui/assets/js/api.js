/**
 * API Communication Module
 */

import { API_CONFIG } from './config.js';

/**
 * Base API request function
 */
async function apiRequest(endpoint, options = {}) {
    const url = API_CONFIG.BASE_URL + endpoint;
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
        ...options
    };

    // Handle FormData (for file uploads)
    if (options.body instanceof FormData) {
        delete defaultOptions.headers['Content-Type'];
    }

    try {
        const response = await fetch(url, defaultOptions);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

/**
 * Upload files to the server
 */
export async function uploadFiles(files) {
    const formData = new FormData();
    files.forEach(file => {
        formData.append('files', file);
    });

    return apiRequest(API_CONFIG.ENDPOINTS.UPLOAD, {
        method: 'POST',
        body: formData
    });
}

/**
 * Get list of uploaded files
 */
export async function getFileList() {
    return apiRequest(API_CONFIG.ENDPOINTS.FILES);
}

/**
 * Delete a specific file
 */
export async function deleteFile(filename) {
    return apiRequest(`${API_CONFIG.ENDPOINTS.FILES}/${encodeURIComponent(filename)}`, {
        method: 'DELETE'
    });
}

/**
 * Send chat message
 */
export async function sendChatMessage(message, mode, selectedFiles, systemPrompt = null) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.TIMEOUT);
    
    try {
        const response = await fetch(API_CONFIG.BASE_URL + API_CONFIG.ENDPOINTS.CHAT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                mode: mode,
                selected_files: selectedFiles,
                system_prompt: systemPrompt
            }),
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        clearTimeout(timeoutId);
        throw error;
    }
}

/**
 * Get model information
 */
export async function getModelInfo() {
    return apiRequest(API_CONFIG.ENDPOINTS.MODEL_INFO);
}
