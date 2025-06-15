import React from 'react';
import { Container, Card, Row, Col, Table, Badge, Alert } from 'react-bootstrap';

const RiskDetection = ({ risks }) => {
  if (!risks || Object.keys(risks).length === 0) {
    return (
      <Container>
        <h1 className="mb-4">Risk Detection</h1>
        <Alert variant="warning">
          No risk data available. Please upload a project file first.
        </Alert>
      </Container>
    );
  }
  
  const totalRisks = risks.total_risks || 0;
  const riskLevel = risks.risk_level || 'Unknown';
  const allRisks = risks.risks || {};
  const recommendations = risks.recommendations || [];
  
  // Get appropriate color based on risk level
  const getRiskLevelColor = (level) => {
    switch (level) {
      case 'Très faible':
      case 'Very low': 
        return 'success';
      case 'Faible':
      case 'Low':
        return 'info';
      case 'Moyen':
      case 'Medium':
        return 'warning';
      case 'Élevé':
      case 'High':
        return 'danger';
      default:
        return 'secondary';
    }
  };
  
  // Get color class based on risk level
  const getRiskClass = (level) => {
    switch (level) {
      case 'Élevé':
      case 'High':
        return 'risk-high';
      case 'Moyen':
      case 'Medium':
        return 'risk-medium';
      default:
        return 'risk-low';
    }
  };

  return (
    <Container fluid>
      <h1 className="mb-4">Risk Detection</h1>
      
      <Row className="mb-4">
        <Col md={6}>
          <Card className="mb-4">
            <Card.Body>
              <div className="d-flex justify-content-between align-items-center">
                <h4>Overall Risk Level:</h4>
                <h3 className={`${getRiskClass(riskLevel)} fw-bold`}>
                  {riskLevel}
                </h3>
              </div>
            </Card.Body>
          </Card>
        </Col>
        
        <Col md={6}>
          <Card className="mb-4 text-center">
            <Card.Body>
              <h4>Total Risks Detected</h4>
              <h2>{totalRisks}</h2>
            </Card.Body>
          </Card>
        </Col>
      </Row>
      
      {/* Tasks with no resources */}
      {allRisks.no_resources && allRisks.no_resources.length > 0 && (
        <Card className="mb-4">
          <Card.Header>
            <h5 className="mb-0">💼 Tasks Without Resources</h5>
          </Card.Header>
          <Card.Body>
            <Table striped bordered hover responsive>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Task</th>
                  <th>Risk Level</th>
                </tr>
              </thead>
              <tbody>
                {allRisks.no_resources.map(risk => (
                  <tr key={`no-resource-${risk.id}`}>
                    <td>{risk.id}</td>
                    <td>{risk.nom}</td>
                    <td>
                      <Badge bg={getRiskLevelColor(risk.risk_level)}>
                        {risk.risk_level}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </Card.Body>
        </Card>
      )}
      
      {/* Tasks with no dependencies */}
      {allRisks.no_dependencies && allRisks.no_dependencies.length > 0 && (
        <Card className="mb-4">
          <Card.Header>
            <h5 className="mb-0">🔗 Tasks Without Dependencies</h5>
          </Card.Header>
          <Card.Body>
            <Table striped bordered hover responsive>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Task</th>
                  <th>Risk Level</th>
                </tr>
              </thead>
              <tbody>
                {allRisks.no_dependencies.map(risk => (
                  <tr key={`no-dep-${risk.id}`}>
                    <td>{risk.id}</td>
                    <td>{risk.nom}</td>
                    <td>
                      <Badge bg={getRiskLevelColor(risk.risk_level)}>
                        {risk.risk_level}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </Card.Body>
        </Card>
      )}
      
      {/* Bottleneck tasks */}
      {allRisks.bottlenecks && allRisks.bottlenecks.length > 0 && (
        <Card className="mb-4">
          <Card.Header>
            <h5 className="mb-0">⏳ Bottleneck Tasks</h5>
          </Card.Header>
          <Card.Body>
            <Table striped bordered hover responsive>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Task</th>
                  <th>Duration</th>
                  <th>Risk Level</th>
                </tr>
              </thead>
              <tbody>
                {allRisks.bottlenecks.map(risk => (
                  <tr key={`bottleneck-${risk.id}`}>
                    <td>{risk.id}</td>
                    <td>{risk.nom}</td>
                    <td>{`${risk.duree_estimee} ${risk.unite_duree || 'days'}`}</td>
                    <td>
                      <Badge bg={getRiskLevelColor(risk.risk_level)}>
                        {risk.risk_level}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </Card.Body>
        </Card>
      )}
      
      {/* Overloaded resources */}
      {allRisks.overloaded_resources && allRisks.overloaded_resources.length > 0 && (
        <Card className="mb-4">
          <Card.Header>
            <h5 className="mb-0">💥 Overloaded Resources</h5>
          </Card.Header>
          <Card.Body>
            <Table striped bordered hover responsive>
              <thead>
                <tr>
                  <th>Resource</th>
                  <th>Task Count</th>
                  <th>Tasks</th>
                  <th>Risk Level</th>
                </tr>
              </thead>
              <tbody>
                {allRisks.overloaded_resources.map((risk, idx) => (
                  <tr key={`overload-${idx}`}>
                    <td><strong>{risk.resource}</strong></td>
                    <td>{risk.task_count}</td>
                    <td>
                      {risk.tasks && risk.tasks.map(task => task.nom).join(', ')}
                    </td>
                    <td>
                      <Badge bg={getRiskLevelColor(risk.risk_level)}>
                        {risk.risk_level}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </Card.Body>
        </Card>
      )}
      
      {/* Recommendations */}
      <Card className="mb-4">
        <Card.Header>
          <h5 className="mb-0">💡 Recommendations</h5>
        </Card.Header>
        <Card.Body>
          {recommendations && recommendations.length > 0 ? (
            <ul className="list-group">
              {recommendations.map((rec, idx) => (
                <li key={`rec-${idx}`} className="list-group-item">
                  {rec}
                </li>
              ))}
            </ul>
          ) : (
            <p>No specific recommendations available.</p>
          )}
        </Card.Body>
      </Card>
    </Container>
  );
};

export default RiskDetection;
