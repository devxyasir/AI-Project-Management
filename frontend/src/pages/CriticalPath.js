import React from 'react';
import { Container, Card, Table, Badge, Alert } from 'react-bootstrap';

const CriticalPath = ({ criticalPath }) => {
  if (!criticalPath || !criticalPath.critical_path || criticalPath.critical_path.length === 0) {
    return (
      <Container>
        <h1 className="mb-4">Critical Path Analysis</h1>
        <Alert variant="warning">
          No critical path data available. Make sure your project has tasks with dependencies.
        </Alert>
      </Container>
    );
  }
  
  const totalDuration = criticalPath.total_duration || 0;
  const durationUnit = criticalPath.duration_unit || 'days';
  const tasks = criticalPath.critical_path || [];
  const pathIds = criticalPath.path_ids || [];
  
  return (
    <Container fluid>
      <h1 className="mb-4">Critical Path Analysis</h1>
      <p className="lead">
        Tasks that, if delayed, will delay the entire project
      </p>
      
      <Card className="mb-4 text-center">
        <Card.Body>
          <h4>Critical Path Duration</h4>
          <h2>
            {totalDuration} {durationUnit}
          </h2>
        </Card.Body>
      </Card>
      
      <Card className="mb-4">
        <Card.Header>
          <h5 className="mb-0">Critical Path Sequence</h5>
        </Card.Header>
        <Card.Body>
          <div className="d-flex flex-wrap">
            {pathIds.map((id, index) => (
              <React.Fragment key={index}>
                <Badge 
                  bg="primary" 
                  style={{ fontSize: '1rem', padding: '0.5rem' }}
                >
                  Task {id}
                </Badge>
                
                {index < pathIds.length - 1 && (
                  <div className="mx-2 d-flex align-items-center">
                    <i className="bi bi-arrow-right"></i>
                    →
                  </div>
                )}
              </React.Fragment>
            ))}
          </div>
        </Card.Body>
      </Card>
      
      <Card>
        <Card.Header>
          <h5 className="mb-0">Critical Tasks</h5>
        </Card.Header>
        <Card.Body>
          <Table striped bordered hover responsive>
            <thead>
              <tr>
                <th>ID</th>
                <th>Task</th>
                <th>Duration</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map(task => (
                <tr key={task.id}>
                  <td>{task.id}</td>
                  <td><strong>{task.nom}</strong></td>
                  <td>{task.duree_estimee} {task.unite_duree || durationUnit}</td>
                  <td>{task.description || 'No description'}</td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card.Body>
      </Card>
      
      <Card className="mt-4">
        <Card.Body>
          <h5>Why is the Critical Path Important?</h5>
          <p>
            The critical path is the sequence of tasks that determines the minimum time needed to complete the project. 
            Any delay in critical path tasks will directly delay your project completion date.
          </p>
          <h5>Recommendations:</h5>
          <ul>
            <li>Focus resources on critical path tasks first</li>
            <li>Monitor these tasks closely and address any delays immediately</li>
            <li>Consider adding buffers around these tasks</li>
            <li>Look for opportunities to fast-track these tasks when possible</li>
          </ul>
        </Card.Body>
      </Card>
    </Container>
  );
};

export default CriticalPath;
