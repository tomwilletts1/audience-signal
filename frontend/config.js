// API Configuration
const API_CONFIG = {
    BASE_URL: 'http://localhost:5000',
    ENDPOINTS: {
        ANALYZE: '/api/analyze',
        HISTORY: '/api/history',
        SUMMARY: '/api/summary',
        PRESETS: '/api/presets'
    }
};

// UI Configuration
const UI_CONFIG = {
    MAX_MESSAGE_LENGTH: 1000,
    MAX_IMAGE_SIZE: 5 * 1024 * 1024, // 5MB
    SUPPORTED_IMAGE_TYPES: ['image/jpeg', 'image/png', 'image/gif'],
    DEFAULT_TEMPERATURE: 0.7,
    MAX_PERSONAS_SELECTABLE: 5
};

// Feature Flags
const FEATURE_FLAGS = {
    ENABLE_IMAGE_UPLOAD: true,
    ENABLE_HISTORY: true,
    ENABLE_SUMMARY: true,
    ENABLE_KEYBOARD_SHORTCUTS: true
};

// Export configurations
export {
    API_CONFIG,
    UI_CONFIG,
    FEATURE_FLAGS
}; 