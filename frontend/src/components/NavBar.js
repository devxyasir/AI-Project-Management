import React from 'react';
import { Navbar, Container, Nav, Badge } from 'react-bootstrap';
import { Link, useLocation } from 'react-router-dom';

const NavBar = () => {
  const location = useLocation();
  
  const isActive = (path) => {
    return location.pathname === path;
  };
  
  return (
    <Navbar bg="primary" variant="dark" expand="lg" className="shadow-sm">
      <Container>
        <Navbar.Brand as={Link} to="/" className="d-flex align-items-center">
          <i className="bi bi-bar-chart-line me-2 fs-4"></i>
          <span className="fw-bold">AI Project Management Assistant</span>
        </Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="ms-auto">
            <Nav.Link 
              as={Link} 
              to="/" 
              className={isActive('/') ? 'active fw-bold' : ''}
            >
              <i className="bi bi-speedometer2 me-1"></i> Dashboard
            </Nav.Link>
            <Nav.Link 
              as={Link} 
              to="/gantt" 
              className={isActive('/gantt') ? 'active fw-bold' : ''}
            >
              <i className="bi bi-calendar3 me-1"></i> Gantt Chart
            </Nav.Link>
            <Nav.Link 
              as={Link} 
              to="/critical-path" 
              className={isActive('/critical-path') ? 'active fw-bold' : ''}
            >
              <i className="bi bi-diagram-3 me-1"></i> Critical Path
            </Nav.Link>
            <Nav.Link 
              as={Link} 
              to="/risks" 
              className={isActive('/risks') ? 'active fw-bold' : ''}
            >
              <i className="bi bi-exclamation-triangle me-1"></i> Risk Analysis
            </Nav.Link>
            <Nav.Link 
              as={Link} 
              to="/assistant" 
              className={isActive('/assistant') ? 'active fw-bold' : ''}
            >
              <i className="bi bi-robot me-1"></i> AI Assistant <Badge bg="info" pill className="ms-1">AI</Badge>
            </Nav.Link>
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
};

export default NavBar;
