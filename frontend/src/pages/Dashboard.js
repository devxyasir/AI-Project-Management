import React from 'react';
import { Container, Row, Col, Card, Table, Badge, Alert } from 'react-bootstrap';

const Dashboard = ({ projectData, summary, error }) => {
  if (error) {
    return (
      <Container>
        <Alert variant="danger">
          Error: {error}
        </Alert>
      </Container>
    );
  }
  
  if (!summary) {
    return (
      <Container className="mt-4">
        <Card>
          <Card.Body className="text-center">
            <Card.Title>Welcome to the AI Project Management Assistant</Card.Title>
            <Card.Text>
              Please upload a project file or use the sample data to begin.
            </Card.Text>
            
            <Card.Text className="mt-4">
              <strong>Expected JSON Structure:</strong>
            </Card.Text>
            
            <pre className="bg-light p-3 text-start">
{`{
  "nom_projet": "Example Project",
  "date_debut": "2023-01-01",
  "responsable": "John Smith",
  "taches": [
    {
      "id": 1,
      "nom": "Requirements Analysis",
      "description": "Task description",
      "duree_estimee": 5,
      "unite_duree": "days",
      "predecesseurs": [],
      "ressources_requises": ["Analyst"],
      "statut": "non_commencee"
    },
    ...
  ]
}`}
            </pre>
          </Card.Body>
        </Card>
      </Container>
    );
  }
  
  // Get status badge class based on status
  const getStatusBadge = (status) => {
    switch(status) {
      case 'terminee':
        return <Badge bg="success">Completed</Badge>;
      case 'en_cours':
        return <Badge bg="primary">In Progress</Badge>;
      case 'non_commencee':
        return <Badge bg="secondary">Not Started</Badge>;
      case 'en_retard':
        return <Badge bg="danger">Delayed</Badge>;
      default:
        return <Badge bg="light" text="dark">{status}</Badge>;
    }
  };
  
  return (
    <Container fluid>
      <h1 className="mb-4">Project Summary</h1>
      
      <Row className="mb-4">
        <Col md={6}>
          <Card>
            <Card.Body>
              <Card.Title>
                {summary.project_name || "Unnamed Project"}
              </Card.Title>
              {summary.project_manager && (
                <Card.Subtitle className="mb-2 text-muted">
                  Manager: {summary.project_manager}
                </Card.Subtitle>
              )}
            </Card.Body>
          </Card>
        </Col>
        
        <Col md={3}>
          <Card className="text-center h-100">
            <Card.Body>
              <Card.Title>{summary.task_count}</Card.Title>
              <Card.Text>Tasks</Card.Text>
            </Card.Body>
          </Card>
        </Col>
        
        <Col md={3}>
          <Card className="text-center h-100">
            <Card.Body>
              <Card.Title>
                {summary.total_duration} {summary.duration_unit}
              </Card.Title>
              <Card.Text>Total Duration</Card.Text>
            </Card.Body>
          </Card>
        </Col>
      </Row>
      
      <Card>
        <Card.Header>
          <h5 className="mb-0">Task List</h5>
        </Card.Header>
        <Card.Body>
          <Table striped hover responsive>
            <thead>
              <tr>
                <th>ID</th>
                <th>Task</th>
                <th>Duration</th>
                <th>Resources</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {summary.tasks && summary.tasks.map(task => (
                <tr key={task.id}>
                  <td>{task.id}</td>
                  <td>{task.nom}</td>
                  <td>
                    {task.duree_estimee} {task.unite_duree || summary.duration_unit}
                  </td>
                  <td>
                    {task.ressources_requises && task.ressources_requises.length > 0 ? (
                      task.ressources_requises.join(', ')
                    ) : (
                      <Badge bg="warning" text="dark">No Resources</Badge>
                    )}
                  </td>
                  <td>{getStatusBadge(task.statut)}</td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card.Body>
      </Card>
    </Container>
  );
};

export default Dashboard;
