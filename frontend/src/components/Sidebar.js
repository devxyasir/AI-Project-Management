import React, { useState, useEffect } from 'react';
import { Form, Button, Alert, ListGroup, Badge } from 'react-bootstrap';
import apiService from '../services/apiService';

const Sidebar = ({ onDataLoaded, onLoadStart, onError, apiKey, onApiKeyChange }) => {
  const [file, setFile] = useState(null);
  const [localApiKey, setLocalApiKey] = useState(apiKey || '');
  const [fileName, setFileName] = useState('');
  const [showSuccess, setShowSuccess] = useState(false);
  const [projectHistory, setProjectHistory] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [showHistory, setShowHistory] = useState(false);

  // Update local API key when prop changes and load project history
  useEffect(() => {
    setLocalApiKey(apiKey);
    
    // Load project history
    const history = apiService.getProjectHistory();
    setProjectHistory(history);
    
    // Get current session ID
    const currentSessionId = apiService.getSessionId();
    setActiveSessionId(currentSessionId);
  }, [apiKey]);

  // Handler for file selection
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
    if (selectedFile) {
      setFileName(selectedFile.name);
    } else {
      setFileName('');
    }
  };

  // Submit handler for file upload
  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      onError('Please select a file to upload');
      return;
    }
    
    try {
      onLoadStart();
      const formData = new FormData();
      formData.append('file', file);
      
      // Send API key if available
      if (localApiKey) {
        apiService.setApiKey(localApiKey);
      }
      
      const response = await apiService.uploadProject(formData);
      onDataLoaded(response);
      
      // Show success message
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);
    } catch (error) {
      console.error('Error uploading file:', error);
      onError(error.message || 'Failed to upload and process project file');
    }
  };
  
  // Handler for loading sample data
  const handleLoadSample = async () => {
    try {
      onLoadStart();
      
      // Send API key if available
      if (localApiKey) {
        apiService.setApiKey(localApiKey);
      }
      
      const response = await apiService.getSampleProject();
      onDataLoaded(response);
      
      // Show success message
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);
    } catch (error) {
      console.error('Error loading sample data:', error);
      onError(error.message || 'Failed to load sample project data');
    }
  };
  
  // Handler for API key changes
  const handleApiKeyChange = (e) => {
    const newKey = e.target.value;
    setLocalApiKey(newKey);
    
    // Call parent handler
    if (onApiKeyChange) {
      onApiKeyChange(newKey);
    }
    
    // Set API key in service
    apiService.setApiKey(newKey);
  };
  
  // Handler for switching to a project from history
  const handleSwitchProject = async (sessionId) => {
    try {
      onLoadStart();
      
      // Switch to the selected project
      const response = await apiService.switchToProject(sessionId);
      onDataLoaded(response);
      
      // Update active session
      setActiveSessionId(sessionId);
      
      // Reload project history
      const history = apiService.getProjectHistory();
      setProjectHistory(history);
      
      // Show success message
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);
    } catch (error) {
      console.error('Error switching project:', error);
      onError(error.message || 'Failed to switch to selected project');
    }
  };
  
  // Handler for removing a project from history
  const handleRemoveProject = (e, sessionId) => {
    e.stopPropagation(); // Prevent triggering the parent click handler
    
    apiService.removeProjectFromHistory(sessionId);
    
    // Reload project history
    const history = apiService.getProjectHistory();
    setProjectHistory(history);
    
    // If we removed the active project, clear it
    if (activeSessionId === sessionId) {
      setActiveSessionId(null);
    }
  };

  return (
    <div className="sidebar p-3">
      <h4 className="mb-3">Project Management</h4>
      
      {showSuccess && (
        <Alert variant="success" className="mb-3" onClose={() => setShowSuccess(false)} dismissible>
          Project loaded successfully!
        </Alert>
      )}
      
      <Form className="mb-4" onSubmit={handleFileUpload}>
        <Form.Group className="mb-3">
          <Form.Label>Upload Project File</Form.Label>
          <div className="custom-file-upload">
            <Form.Control 
              type="file" 
              onChange={handleFileChange} 
              accept=".json"
              className="mb-2"
            />
            {fileName && (
              <div className="selected-file">
                <i className="bi bi-file-earmark-text me-2"></i>
                {fileName}
              </div>
            )}
          </div>
          <Form.Text className="text-muted">
            Upload a JSON project file with tasks and dependencies.
          </Form.Text>
        </Form.Group>
        
        <Button 
          type="submit" 
          variant="primary" 
          className="w-100 mb-2"
          disabled={!file}
        >
          <i className="bi bi-cloud-upload me-2"></i>
          Upload & Analyze
        </Button>
      </Form>
      
      <div className="mb-4 text-center">
        <p className="text-muted mb-2">- or -</p>
        <Button 
          variant="outline-secondary" 
          onClick={handleLoadSample} 
          className="w-100 mb-2"
        >
          <i className="bi bi-file-earmark-code me-2"></i>
          Load Sample Project
        </Button>
        
        {projectHistory.length > 0 && (
          <Button 
            variant="outline-info" 
            onClick={() => setShowHistory(!showHistory)} 
            className="w-100"
          >
            <i className="bi bi-clock-history me-2"></i>
            {showHistory ? 'Hide Project History' : 'Show Project History'}
          </Button>
        )}
      </div>
      
      {showHistory && projectHistory.length > 0 && (
        <div className="mb-4">
          <h5 className="mb-2">Recent Projects</h5>
          <ListGroup>
            {projectHistory.map((project) => (
              <ListGroup.Item 
                key={project.sessionId}
                action
                active={activeSessionId === project.sessionId}
                onClick={() => handleSwitchProject(project.sessionId)}
                className="d-flex justify-content-between align-items-center"
              >
                <div className="text-truncate" style={{ maxWidth: '80%' }}>
                  <i className="bi bi-file-earmark-text me-2"></i>
                  {project.name || 'Unnamed Project'}
                </div>
                <div>
                  <Badge bg="secondary" className="me-2" title="Date added">
                    {new Date(project.timestamp).toLocaleDateString()}
                  </Badge>
                  <Button 
                    variant="danger" 
                    size="sm" 
                    onClick={(e) => handleRemoveProject(e, project.sessionId)}
                    title="Remove from history"
                  >
                    <i className="bi bi-x"></i>
                  </Button>
                </div>
              </ListGroup.Item>
            ))}
          </ListGroup>
        </div>
      )}
      
      <hr className="my-4" />
      
      <h4 className="mb-3">Settings</h4>
      
      <Form.Group className="mb-3">
        <Form.Label>
          <i className="bi bi-key me-2"></i>
          OpenAI API Key
        </Form.Label>
        <Form.Control 
          type="password" 
          placeholder="Enter your API key"
          value={localApiKey}
          onChange={handleApiKeyChange}
        />
        <Form.Text className="text-muted">
          Required for AI assistant questions. Your key is never stored on our servers.
        </Form.Text>
      </Form.Group>
      
      <div className="sidebar-footer text-center mt-5 pt-3 border-top">
        <p className="text-muted small">
          AI Project Management Assistant<br />
          <span className="fw-bold">v1.0.0</span>
        </p>
      </div>
    </div>
  );
};

export default Sidebar;
