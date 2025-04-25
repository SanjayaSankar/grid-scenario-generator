import React from 'react';
import { Link } from 'react-router-dom';
import { Container, Row, Col, Card, Button } from 'react-bootstrap';
import { BarChart2, Zap, Database, Search } from 'react-feather';
import '../styles/HomePage.css';

const HomePage = () => {
  return (
    <Container className="home-page">
      <Row className="hero-section text-center mb-5">
        <Col>
          <h1 className="display-4 mb-4">Grid Scenario Generator</h1>
          <p className="lead mb-4">
            Generate realistic power grid scenarios using Physics-Informed Neural Networks
            and Retrieval Augmented Generation techniques
          </p>
          <div className="d-flex justify-content-center">
            <Link to="/generate">
              <Button variant="primary" size="lg" className="me-3">
                Generate Scenario
              </Button>
            </Link>
            <Link to="/about">
              <Button variant="outline-secondary" size="lg">
                Learn More
              </Button>
            </Link>
          </div>
        </Col>
      </Row>

      <Row className="features-section mb-5">
        <Col md={3}>
          <Card className="h-100 feature-card">
            <Card.Body className="text-center">
              <div className="icon-container mb-3">
                <Zap size={48} />
              </div>
              <Card.Title>Physics-Informed Generation</Card.Title>
              <Card.Text>
                Generate power grid scenarios that adhere to physical laws and constraints
              </Card.Text>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="h-100 feature-card">
            <Card.Body className="text-center">
              <div className="icon-container mb-3">
                <Search size={48} />
              </div>
              <Card.Title>RAG-Enhanced Creation</Card.Title>
              <Card.Text>
                Leverage existing scenarios to inform and enhance new generation
              </Card.Text>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="h-100 feature-card">
            <Card.Body className="text-center">
              <div className="icon-container mb-3">
                <BarChart2 size={48} />
              </div>
              <Card.Title>OpenDSS Validation</Card.Title>
              <Card.Text>
                Validate generated scenarios with industry-standard power flow tools
              </Card.Text>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="h-100 feature-card">
            <Card.Body className="text-center">
              <div className="icon-container mb-3">
                <Database size={48} />
              </div>
              <Card.Title>Scenario Management</Card.Title>
              <Card.Text>
                Store, retrieve, and analyze your generated grid scenarios
              </Card.Text>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Row className="workflow-section mb-5">
        <Col>
          <h2 className="text-center mb-4">How It Works</h2>
          <div className="workflow-steps">
            <div className="workflow-step">
              <div className="step-number">1</div>
              <div className="step-content">
                <h4>Specify Parameters</h4>
                <p>Define the characteristics of your desired grid scenario</p>
              </div>
            </div>
            <div className="workflow-step">
              <div className="step-number">2</div>
              <div className="step-content">
                <h4>Generate Scenario</h4>
                <p>Create a physics-consistent scenario using our PINN model</p>
              </div>
            </div>
            <div className="workflow-step">
              <div className="step-number">3</div>
              <div className="step-content">
                <h4>Validate Results</h4>
                <p>Ensure the scenario meets all physical and operational constraints</p>
              </div>
            </div>
            <div className="workflow-step">
              <div className="step-number">4</div>
              <div className="step-content">
                <h4>Export and Use</h4>
                <p>Download the scenario for use in your simulations and analyses</p>
              </div>
            </div>
          </div>
        </Col>
      </Row>

      <Row className="cta-section text-center">
        <Col>
          <h2 className="mb-4">Ready to Generate Your Scenario?</h2>
          <Link to="/generate">
            <Button variant="primary" size="lg">
              Get Started
            </Button>
          </Link>
        </Col>
      </Row>
    </Container>
  );
};

export default HomePage;