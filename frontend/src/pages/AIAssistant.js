import React, { useState, useEffect, useRef } from 'react';
import { Container, Card, Form, Button, Spinner, Alert, Badge } from 'react-bootstrap';
import apiService from '../services/apiService';

const AIAssistant = ({ projectData }) => {
  const [question, setQuestion] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [conversationId, setConversationId] = useState(null);
  const [projectInfo, setProjectInfo] = useState({});
  const messagesEndRef = useRef(null);
  
  // Auto-scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [chatHistory]);
  
  // Extract project information when component mounts or projectData changes
  useEffect(() => {
    if (projectData) {
      // Extract key project information to display in the UI
      const info = {
        name: projectData.project_name || 'Unnamed Project',
        taskCount: projectData.task_count || 0,
        hasRisks: projectData.risks && Object.keys(projectData.risks).length > 0,
        hasCriticalPath: projectData.critical_path && projectData.critical_path.critical_path,
        sessionId: apiService.getSessionId()
      };
      
      setProjectInfo(info);
      
      // Add a welcome message to the chat history if it's empty
      if (chatHistory.length === 0) {
        setChatHistory([{
          role: 'assistant',
          content: `Welcome! I'm your AI Project Assistant. I have analyzed your project "${info.name}" with ${info.taskCount} tasks. How can I help you with your project management questions?`
        }]);
      }
    }
  }, [projectData, chatHistory.length]);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!question.trim()) {
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    // Add user message to chat
    const userMessage = {
      role: 'user',
      content: question,
    };
    
    setChatHistory(prev => [...prev, userMessage]);
    
    try {
      // Make sure we're using the current session ID
      const sessionId = apiService.getSessionId();
      
      // Send the question with conversation context
      const response = await apiService.askQuestion(question, conversationId);
      
      if (response.success) {
        // Add assistant response to chat
        const responseContent = response.response || response.answer; // Handle both response formats (new and old)
        
        // Process the response to ensure proper formatting
        let formattedContent = responseContent;
        
        // Ensure response is properly formatted HTML
        // If it doesn't start with HTML tags and just contains plain text
        if (!responseContent.trim().startsWith('<')) {
          formattedContent = `<p>${responseContent}</p>`;
        }
        
        const assistantMessage = {
          role: 'assistant',
          content: formattedContent,
          isHtml: true, // Flag to indicate HTML content
          isAI: !response.simulated // Flag to indicate if this is a real AI response or simulated
        };
        
        setChatHistory(prev => [...prev, assistantMessage]);
        
        // Save the conversation ID for context continuity
        if (response.conversation_id) {
          setConversationId(response.conversation_id);
        }
        
        // If this is a simulated response, show a warning
        if (response.simulated) {
          setError('Using simulated AI responses. For full functionality, please provide an OpenAI API key.');
        }
      } else {
        setError(response.error || response.message || 'Failed to get a response from the AI assistant');
      }
    } catch (err) {
      console.error('Error asking question:', err);
      setError('An error occurred while communicating with the AI assistant');
    } finally {
      setQuestion('');
      setIsLoading(false);
    }
  };
  
  return (
    <Container fluid>
      <h1 className="mb-4">AI Assistant</h1>
      <p className="lead">Ask questions about your project in natural language</p>
      
      <Card className="mb-4">
        <Card.Body>
          <div className="message-container mb-4">
            {chatHistory.length === 0 ? (
              <div className="text-center text-muted my-5">
                <p>No conversation history yet. Ask a question to begin.</p>
                <p>Example questions you can ask:</p>
                <ul className="list-unstyled">
                  <li>• What is the total duration of the project?</li>
                  <li>• What are the main risks in this project?</li>
                  <li>• Which tasks are on the critical path?</li>
                  <li>• Who is responsible for task 3?</li>
                  <li>• How many resources are overloaded?</li>
                </ul>
              </div>
            ) : (
              chatHistory.map((msg, index) => (
                <div
                  key={index}
                  className={`message ${msg.role === 'user' ? 'user-message' : 'assistant-message'}`}
                >
                  <strong>
                    {msg.role === 'user' ? 'You' : (
                      msg.isAI ? 'AI Assistant' : 'Assistant'
                    )}
                  </strong>
                  {msg.isHtml ? (
                    <div className="message-content" dangerouslySetInnerHTML={{ __html: msg.content }} />
                  ) : (
                    <div className="message-content">{msg.content}</div>
                  )}
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>
          
          {error && (
            <Alert variant="danger" className="mb-4">
              {error}
            </Alert>
          )}
          
          <Form onSubmit={handleSubmit}>
            <Form.Group className="mb-3">
              <Form.Control
                as="textarea"
                rows={3}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask a question about your project..."
                disabled={isLoading}
              />
            </Form.Group>
            
            <div className="d-flex justify-content-end">
              <Button 
                type="submit" 
                variant="primary"
                disabled={isLoading || !question.trim()}
              >
                {isLoading ? (
                  <>
                    <Spinner
                      as="span"
                      animation="border"
                      size="sm"
                      role="status"
                      aria-hidden="true"
                      className="me-2"
                    />
                    Processing...
                  </>
                ) : "Ask Question"}
              </Button>
            </div>
          </Form>
        </Card.Body>
      </Card>
      
      <Card>
        <Card.Header>
          <h5 className="mb-0">About the AI Assistant</h5>
        </Card.Header>
        <Card.Body>
          <p>
            The AI Assistant uses natural language processing to analyze your project data and answer questions.
            It has access to information about:
          </p>
          <ul>
            <li>Project overview and metadata</li>
            <li>Task details, dependencies and current status</li>
            <li>Critical path analysis</li>
            <li>Risk assessment</li>
            <li>Resource allocation</li>
          </ul>
          <p>
            <strong>Note:</strong> The AI Assistant requires an OpenAI API key to function. 
            If no API key is provided, it will use a simulated response mode.
          </p>
        </Card.Body>
      </Card>
    </Container>
  );
};

export default AIAssistant;
