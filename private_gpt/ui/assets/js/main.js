/**
 * Main Application Entry Point
 */

import { setTheme, getStoredTheme, toggleTheme } from './utils.js';
import { initializeUI, loadFileList, loadModelInfo } from './ui.js';

/**
 * Initialize the application
 */
async function initializeApp() {
    try {
        // Load theme first
        loadTheme();
        
        // Initialize UI components
        initializeUI();
        
        // Set focus to message input
        const messageInput = document.getElementById('message-input');
        if (messageInput) {
            messageInput.focus();
        }
        
        // Load initial data
        await Promise.all([
            loadFileList(),
            loadModelInfo()
        ]);
        
        console.log('PrivateGPT application initialized successfully');
    } catch (error) {
        console.error('Failed to initialize application:', error);
    }
}

/**
 * Theme management
 */
function loadTheme() {
    const savedTheme = getStoredTheme();
    setTheme(savedTheme);
}

/**
 * Theme toggle event handler
 */
function initializeThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
}

/**
 * DOM Content Loaded event handler
 */
document.addEventListener('DOMContentLoaded', async function() {
    initializeThemeToggle();
    await initializeApp();
});

// Make theme toggle available globally
window.toggleTheme = toggleTheme;
