import axios from 'axios';

// API configuration
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
let apiKey = '';

// Create axios instance with common configuration
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 30000, // 30 second timeout
  withCredentials: true // Enable cookies
});

/**
 * API Service for project management operations
 */
const apiService = {
  /**
   * Base API URL
   */
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000',
  
  /**
   * Store API key and session ID
   */
  apiKey: null,
  sessionId: null,

  /**
   * Initialize the API service
   */
  init() {
    // Set up axios instance
    this.api = axios.create({
      baseURL: this.baseURL,
      withCredentials: true, // Enable cookies
      headers: {
        'Content-Type': 'application/json'
      },
      timeout: 30000 // 30 second timeout
    });
    
    // Retrieve API key from localStorage if available
    const storedApiKey = localStorage.getItem('openai_api_key');
    if (storedApiKey) {
      this.apiKey = storedApiKey;
    }
    
    // Retrieve session ID from cookies if available
    this.sessionId = this.getCookie('project_session_id');
  },
  
  /**
   * Get cookie by name
   * @param {string} name - Cookie name
   * @returns {string|null} - Cookie value
   */
  getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
  },
  
  /**
   * Set session ID
   * @param {string} sessionId - Session ID
   */
  setSessionId(sessionId) {
    this.sessionId = sessionId;
  },
  
  /**
   * Get current session ID
   * @returns {string|null} - Current session ID
   */
  getSessionId() {
    return this.sessionId;
  },
  
  /**
   * Set API key for OpenAI requests
   * @param {string} key - The OpenAI API key
   */
  setApiKey(key) {
    apiKey = key;
    // Store in localStorage for persistence, but make sure to warn users about security implications
    if (key) {
      localStorage.setItem('temp_openai_key', key);
    } else {
      localStorage.removeItem('temp_openai_key');
    }
  },
  
  /**
   * Get stored API key
   * @returns {string} - The stored API key or empty string
   */
  getApiKey() {
    if (apiKey) return apiKey;
    const storedKey = localStorage.getItem('temp_openai_key');
    if (storedKey) {
      apiKey = storedKey;
    }
    return apiKey;
  },
  
  /**
   * Get headers for API requests
   * @returns {Object} - Headers with API key and session ID
   */
  getHeaders() {
    const headers = {};
    if (this.apiKey) {
      headers['X-API-Key'] = this.apiKey;
    }
    if (this.sessionId) {
      headers['X-Session-ID'] = this.sessionId;
    }
    return headers;
  },
  
  /**
   * Upload project data
   * @param {FormData|Object} data - Project data or FormData with file
   * @returns {Promise} - Response with processed project data
   */
  async uploadProject(data) {
    try {
      const isFormData = data instanceof FormData;
      
      const config = {
        headers: {
          ...this.getHeaders(),
          ...(isFormData ? { 'Content-Type': 'multipart/form-data' } : {})
        }
      };
      
      // Use the correct API endpoint path
      const response = await this.api.post('/api/upload', data, config);
      
      // Save session ID from response
      if (response.data.session_id) {
        this.setSessionId(response.data.session_id);
        
        // Add to localStorage project history
        this.addProjectToHistory(response.data.summary?.project_name || 'Unnamed Project', response.data.session_id);
      }
      
      return response.data;
    } catch (error) {
      console.error('Error uploading project:', error);
      throw new Error(error.response?.data?.error || 'Error uploading project');
    }
  },
  
  /**
   * Get project data from session
   * @returns {Promise} - Response with project data
   */
  async getSessionData() {
    try {
      if (!this.sessionId) {
        throw new Error('No active session');
      }
      
      // Use the correct API endpoint path
      const response = await this.api.get(`/api/session/${this.sessionId}`, {
        headers: this.getHeaders()
      });
      
      // If successful, update the project in history as recently used
      if (response.data.success) {
        this.markProjectAsRecentlyUsed(this.sessionId);
      }
      
      return response.data;
    } catch (error) {
      console.error('Error retrieving session data:', error);
      throw new Error(error.response?.data?.error || 'Error retrieving session data');
    }
  },
  
  /**
   * Ask a question to the AI assistant
   * @param {string} question - The question to ask
   * @param {string} conversationId - Optional conversation ID for context
   * @returns {Promise} - Response from AI assistant
   */
  async askQuestion(question, conversationId = null) {
    try {
      // Send API key if available
      const headers = this.getHeaders();
      
      const payload = { 
        question, 
        conversation_id: conversationId 
      };
      
      const response = await this.api.post('/api/ask', payload, { headers });
      return response.data;
    } catch (error) {
      console.error('Error asking question:', error);
      
      // If the error is related to API key, provide a helpful message
      if (error.response?.status === 401 || 
          error.response?.data?.error?.includes('API key')) {
        return {
          success: false,
          error: 'OpenAI API key required or invalid. Please provide a valid API key in the settings.'
        };
      }
      
      return {
        success: false,
        error: error.response?.data?.error || error.message || 'Error processing your question'
      };
    }
  },
  
  /**
   * Get sample project data
   * @returns {Promise} - Response with sample data
   */
  async getSampleProject() {
    try {
      // Send API key if available
      const headers = this.getHeaders();
      
      const response = await this.api.get('/api/sample', { headers });
      
      // Save session ID and add to project history
      if (response.data.success && response.data.session_id) {
        this.setSessionId(response.data.session_id);
        this.addProjectToHistory('Sample Project', response.data.session_id);
      }
      
      return response.data;
    } catch (error) {
      console.error('Error loading sample data:', error);
      return {
        success: false,
        error: error.response?.data?.error || error.message || 'Error loading sample data'
      };
    }
  },

  /**
   * Get project history
   * @returns {Array} - Array of project objects with name and session ID
   */
  getProjectHistory() {
    const history = localStorage.getItem('project_history');
    return history ? JSON.parse(history) : [];
  },
  
  /**
   * Add project to history
   * @param {string} name - Project name
   * @param {string} sessionId - Session ID
   */
  addProjectToHistory(name, sessionId) {
    if (!name || !sessionId) return;
    
    // Get current history
    let history = this.getProjectHistory();
    
    // Remove existing entry with same sessionId if exists
    history = history.filter(p => p.sessionId !== sessionId);
    
    // Add new entry at the beginning (most recent)
    history.unshift({
      name,
      sessionId,
      timestamp: new Date().toISOString(),
      lastAccessed: new Date().toISOString()
    });
    
    // Limit history to 10 items
    if (history.length > 10) {
      history = history.slice(0, 10);
    }
    
    // Save back to localStorage
    localStorage.setItem('project_history', JSON.stringify(history));
  },
  
  /**
   * Mark project as recently used
   * @param {string} sessionId - Session ID
   */
  markProjectAsRecentlyUsed(sessionId) {
    if (!sessionId) return;
    
    // Get current history
    let history = this.getProjectHistory();
    
    // Find project and update lastAccessed
    const index = history.findIndex(p => p.sessionId === sessionId);
    if (index !== -1) {
      history[index].lastAccessed = new Date().toISOString();
      
      // Move to top of list
      const item = history.splice(index, 1)[0];
      history.unshift(item);
      
      // Save back to localStorage
      localStorage.setItem('project_history', JSON.stringify(history));
    }
  },
  
  /**
   * Switch to a project from history
   * @param {string} sessionId - Session ID
   * @returns {Promise} - Response with project data
   */
  async switchToProject(sessionId) {
    this.setSessionId(sessionId);
    return await this.getSessionData();
  },
  
  /**
   * Remove a project from history
   * @param {string} sessionId - Session ID to remove
   */
  removeProjectFromHistory(sessionId) {
    if (!sessionId) return;
    
    // Get current history
    let history = this.getProjectHistory();
    
    // Remove the project
    history = history.filter(p => p.sessionId !== sessionId);
    
    // Save back to localStorage
    localStorage.setItem('project_history', JSON.stringify(history));
    
    // If the current session was removed, clear it
    if (this.sessionId === sessionId) {
      this.sessionId = null;
    }
  }
};

export default apiService;
