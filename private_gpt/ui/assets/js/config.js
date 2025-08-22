/**
 * Application Configuration
 */

// API Configuration
export const API_CONFIG = {
    BASE_URL: '/api/html-ui',
    ENDPOINTS: {
        UPLOAD: '/upload',
        FILES: '/files',
        CHAT: '/chat',
        MODEL_INFO: '/model-info'
    },
    TIMEOUT: 900000 // 15 minutes
};

// Application Constants
export const APP_CONFIG = {
    MODES: {
        RAG: 'rag',
        SEARCH: 'search', 
        CHAT: 'chat',
        SUMMARIZE: 'summarize'
    },
    MODE_DESCRIPTIONS: {
        rag: 'Get contextualized answers from selected files.',
        search: 'Find relevant chunks of text in selected files.',
        chat: 'Chat with the LLM using its training data. Files are ignored.',
        summarize: 'Generate a summary of the selected files. Prompt to customize the result.'
    },
    THEME: {
        LIGHT: 'light',
        DARK: 'dark'
    }
};

// File Type Configuration
export const FILE_CONFIG = {
    SUPPORTED_TYPES: ['.pdf', '.txt', '.md', '.csv', '.doc', '.docx'],
    MAX_FILE_SIZE: 50 * 1024 * 1024, // 50MB
    UPLOAD_PHASES: {
        UPLOAD: { progress: 20, icon: '📤', text: 'Uploading files...' },
        PROCESSING: { progress: 60, icon: '⚙️', text: 'Processing and analyzing files...' },
        EMBEDDING: { progress: 80, icon: '🧠', text: 'Generating embeddings for intelligent search...' },
        COMPLETE: { progress: 100, icon: '✅', text: 'Files processed successfully!' }
    }
};

// Notification Configuration
export const NOTIFICATION_CONFIG = {
    TYPES: {
        SUCCESS: 'success',
        ERROR: 'error',
        INFO: 'info'
    },
    ICONS: {
        success: '✅',
        error: '❌',
        info: 'ℹ️'
    },
    AUTO_DISMISS_TIME: 5000
};
