import React, { useState, useEffect } from 'react';
import apiService from './services/apiService';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Container, Row, Col } from 'react-bootstrap';
import NavBar from './components/NavBar';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import GanttChart from './pages/GanttChart';
import CriticalPath from './pages/CriticalPath';
import RiskDetection from './pages/RiskDetection';
import AIAssistant from './pages/AIAssistant';
import './App.css';

function App() {
  const [projectData, setProjectData] = useState(null);
  const [summary, setSummary] = useState(null);
  const [criticalPath, setCriticalPath] = useState(null);
  const [risks, setRisks] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [apiKey, setApiKey] = useState('');
  const [sessionId, setSessionId] = useState(null);
  
  // Initialize API service and restore session if available
  useEffect(() => {
    // Initialize API service
    apiService.init();
    
    // Get API key from localStorage
    const storedApiKey = localStorage.getItem('temp_openai_key');
    if (storedApiKey) {
      setApiKey(storedApiKey);
      apiService.setApiKey(storedApiKey);
    }
    
    // Check for existing session
    const storedSessionId = apiService.getSessionId();
    if (storedSessionId) {
      setSessionId(storedSessionId);
      restoreSession(storedSessionId);
    }
  }, []);
  
  // Function to restore session data
  const restoreSession = async (sessionId) => {
    try {
      setIsLoading(true);
      const data = await apiService.getSessionData();
      if (data.success) {
        handleDataLoaded(data);
        console.log('Session restored successfully:', sessionId);
      } else {
        // Session might be expired or invalid
        console.warn('Failed to restore session:', data.error);
        // Remove from project history if expired
        apiService.removeProjectFromHistory(sessionId);
      }
    } catch (err) {
      console.error('Error restoring session:', err);
      // Handle network errors by showing more helpful error message
      if (err.message?.includes('Network Error')) {
        setError('Network connection error. Please check your internet connection and try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleDataLoaded = (data) => {
    if (data.success) {
      setProjectData(data.project || data.summary?.raw_project);
      setSummary(data.summary);
      setCriticalPath(data.critical_path);
      setRisks(data.risks);
      setError(null);
      
      // Save session ID if provided
      if (data.session_id) {
        setSessionId(data.session_id);
      }
    } else {
      setError(data.error || 'Failed to load project data');
    }
    setIsLoading(false);
  };
  
  const handleLoadStart = () => {
    setIsLoading(true);
    setError(null);
  };
  
  const handleError = (err) => {
    setError(err);
    setIsLoading(false);
  };
  
  const handleApiKeyChange = (key) => {
    setApiKey(key);
  };
  
  return (
    <Router>
      <div className="app">
        <NavBar />
        <Container fluid>
          <Row>
            <Col md={3} lg={2} className="sidebar-column">
              <Sidebar 
                onDataLoaded={handleDataLoaded} 
                onLoadStart={handleLoadStart}
                onError={handleError}
                apiKey={apiKey}
                onApiKeyChange={handleApiKeyChange}
              />
            </Col>
            <Col md={9} lg={10} className="content-column">
              {error && (
                <div className="alert alert-danger" role="alert">
                  {error}
                </div>
              )}
              
              {isLoading ? (
                <div className="loading-container">
                  <div className="spinner-border text-primary" role="status">
                    <span className="visually-hidden">Loading...</span>
                  </div>
                  <p>Processing project data...</p>
                </div>
              ) : (
                <Routes>
                  <Route path="/" element={<Dashboard summary={summary} />} />
                  <Route path="/gantt" element={
                    summary ? (
                      <GanttChart projectData={projectData} summary={summary} />
                    ) : (
                      <Navigate to="/" replace />
                    )
                  } />
                  <Route path="/critical-path" element={
                    criticalPath ? (
                      <CriticalPath criticalPath={criticalPath} />
                    ) : (
                      <Navigate to="/" replace />
                    )
                  } />
                  <Route path="/risks" element={
                    risks ? (
                      <RiskDetection risks={risks} />
                    ) : (
                      <Navigate to="/" replace />
                    )
                  } />
                  <Route path="/assistant" element={
                    summary ? (
                      <AIAssistant projectData={{ ...summary, critical_path: criticalPath, risks: risks }} />
                    ) : (
                      <Navigate to="/" replace />
                    )
                  } />
                </Routes>
              )}
            </Col>
          </Row>
        </Container>
      </div>
    </Router>
  );
}

export default App;
