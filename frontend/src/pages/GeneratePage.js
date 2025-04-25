import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Row,
  Col,
  Form,
  Button,
  Card,
  Alert,
  ProgressBar,
  Tabs,
  Tab,
} from 'react-bootstrap';
import { Sliders, Grid, Database, Check, MessageSquare } from 'react-feather';
import ApiService from '../services/ApiService';
import '../styles/GeneratePage.css';
import { useMockDataContext } from '../components/MockDataProvider';
import ErrorMessage from '../components/ErrorMessage';


const GeneratePage = () => {
  // Context ---------------------------------------------------------------
  const { mockDataEnabled, generateMockScenario } = useMockDataContext();
  const navigate = useNavigate();

  // State ----------------------------------------------------------------
  const [advancedMode, setAdvancedMode] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [activeTab, setActiveTab] = useState('parameters');
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [textInput, setTextInput] = useState('');
  const [isTextInputMode, setIsTextInputMode] = useState(true);
  const [isParsingText, setIsParsingText] = useState(false);
  const [parameters, setParameters] = useState({
    num_buses: 2,
    num_generators: 1,
    num_loads: 1,
    peak_load: 10,
    voltage_profile: 'flat',
    reliability_level: 'high',
    congestion_level: 'low',
    include_context: false,
    similarity_threshold: 0.5,
  });

  // Handlers -------------------------------------------------------------
  const handleChange = ({ target }) => {
    const { name, value, checked, type } = target;
    setParameters((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleTextInputChange = (e) => {
    setTextInput(e.target.value);
  };

  const parseTextInput = async () => {
    setIsParsingText(true);
    try {
      // Call API to parse text input using prompt tuning
      const parsedParams = mockDataEnabled
        ? mockParseTextInput(textInput)
        : await ApiService.parseScenarioText(textInput);

      // Update parameters with parsed values
      setParameters(prev => ({
        ...prev,
        ...parsedParams
      }));

      return parsedParams;
    } catch (err) {
      setError("Failed to parse text input: " + (err.message || "Unknown error"));
      return null;
    } finally {
      setIsParsingText(false);
    }
  };

  // Mock function for demo purposes
  const mockParseTextInput = (text) => {
    // Simulates parsing text into parameters
    console.log("Parsing text:", text);
    
    // Extract values using simple pattern matching (this is a mock)
    // In a real implementation, this would use more sophisticated NLP or prompt tuning
    const parsedParams = {
      num_buses: text.match(/(\d+)\s+bus(es)?/i) ? parseInt(text.match(/(\d+)\s+bus(es)?/i)[1]) : 2,
      num_generators: text.match(/(\d+)\s+generator/i) ? parseInt(text.match(/(\d+)\s+generator/i)[1]) : 1,
      num_loads: text.match(/(\d+)\s+load/i) ? parseInt(text.match(/(\d+)\s+load/i)[1]) : 1,
      peak_load: text.match(/(\d+)\s+MW/i) ? parseInt(text.match(/(\d+)\s+MW/i)[1]) : 10,
    };

    // Determine voltage profile
    if (text.match(/flat\s+voltage/i)) parsedParams.voltage_profile = 'flat';
    else if (text.match(/varied\s+voltage/i)) parsedParams.voltage_profile = 'varied';
    else if (text.match(/stressed\s+voltage/i)) parsedParams.voltage_profile = 'stressed';

    // Determine reliability level
    if (text.match(/high\s+reliability/i)) parsedParams.reliability_level = 'high';
    else if (text.match(/medium\s+reliability/i)) parsedParams.reliability_level = 'medium';
    else if (text.match(/low\s+reliability/i)) parsedParams.reliability_level = 'low';

    // Determine congestion level
    if (text.match(/high\s+congestion/i)) parsedParams.congestion_level = 'high';
    else if (text.match(/medium\s+congestion/i)) parsedParams.congestion_level = 'medium';
    else if (text.match(/low\s+congestion/i)) parsedParams.congestion_level = 'low';

    return parsedParams;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    setError(null);
    setIsGenerating(true);
    setProgress(10);
    setActiveTab('progress');

    try {
      // If using text input, parse it first
      let finalParams = { ...parameters };
      if (isTextInputMode && textInput.trim()) {
        const parsedParams = await parseTextInput();
        if (parsedParams) {
          finalParams = { ...finalParams, ...parsedParams };
        } else {
          // If parsing failed but we want to continue anyway, use current parameters
          console.log("Using fallback parameters");
        }
      }

      // Convert string values to numbers where needed
      const payload = {
        ...finalParams,
        num_buses: Number(finalParams.num_buses),
        num_generators: Number(finalParams.num_generators),
        num_loads: Number(finalParams.num_loads),
        peak_load: Number(finalParams.peak_load),
        similarity_threshold: Number(finalParams.similarity_threshold),
      };

      // Simulate progress -----------------------------------------------
      const progressInterval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 1000);

      // Generate scenario (mock or API) ---------------------------------
      const response = mockDataEnabled
        ? generateMockScenario(payload)
        : await ApiService.generateScenario(payload);

      clearInterval(progressInterval);
      setProgress(100);

      if (response.error) {
        setError(response.error);
      } else {
        setResult(response);
        setActiveTab('result');
      }

    } catch (err) {
      setError(err.message || 'Failed to generate scenario');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleViewDetails = () => {
    if (result?.id) navigate(`/scenarios/${result.id}`);
  };

  // Render helpers -------------------------------------------------------
  const renderParametersTab = () => (
    <Form onSubmit={handleSubmit}>
      {/* Input Mode Selector */}
      <div className="input-mode-selector mb-4">
        <div className="d-flex align-items-center mb-3">
          <Form.Check
            type="switch"
            id="input-mode-switch"
            label="Use Text Input"
            checked={isTextInputMode}
            onChange={() => setIsTextInputMode(!isTextInputMode)}
            className="me-3"
          />
        </div>
      </div>

      {/* Text Input Mode */}
      {isTextInputMode && (
        <Card className="mb-4">
          <Card.Header className="d-flex align-items-center">
            <MessageSquare className="me-2" size={20} />
            <span>Scenario Description</span>
          </Card.Header>
          <Card.Body>
            <Form.Group>
              <Form.Label>Describe the grid scenario you want to generate</Form.Label>
              <Form.Control
                as="textarea"
                rows={4}
                value={textInput}
                onChange={handleTextInputChange}
                placeholder="Example: Generate a power grid with 3 buses, 2 generators, and 2 loads with a peak load of 15 MW. Use a varied voltage profile with medium reliability and low congestion."
              />
              <Form.Text className="text-muted">
                Describe the scenario in natural language. Mention parameters like number of buses, generators, loads, peak load, voltage profile, reliability, and congestion levels.
              </Form.Text>
            </Form.Group>

            {isParsingText ? (
              <div className="text-center mt-3">
                <div className="spinner-border spinner-border-sm me-2" role="status">
                  <span className="visually-hidden">Parsing...</span>
                </div>
                <span>Parsing input...</span>
              </div>
            ) : null}
          </Card.Body>
        </Card>
      )}

      {/* Parameter Inputs (only shown when text input mode is off) */}
      {!isTextInputMode && (
        <div>
          {/* Network Parameters -------------------------------------------- */}
          <Card className="mb-4">
            <Card.Header className="d-flex align-items-center">
              <Grid className="me-2" size={20} />
              <span>Network Parameters</span>
            </Card.Header>
            <Card.Body>
              <Row>
                {/* Buses ----------------------------------------------------- */}
                <Col md={4}>
                  <Form.Group className="mb-3">
                    <Form.Label>Number of Buses</Form.Label>
                    <Form.Control
                      type="number"
                      name="num_buses"
                      min="2"
                      max="10"
                      value={parameters.num_buses}
                      onChange={handleChange}
                      required
                    />
                    <Form.Text className="text-muted">Between 2 and 10 buses</Form.Text>
                  </Form.Group>
                </Col>

                {/* Generators ---------------------------------------------- */}
                <Col md={4}>
                  <Form.Group className="mb-3">
                    <Form.Label>Number of Generators</Form.Label>
                    <Form.Control
                      type="number"
                      name="num_generators"
                      min="1"
                      max="5"
                      value={parameters.num_generators}
                      onChange={handleChange}
                      required
                    />
                    <Form.Text className="text-muted">Between 1 and 5 generators</Form.Text>
                  </Form.Group>
                </Col>

                {/* Loads ---------------------------------------------------- */}
                <Col md={4}>
                  <Form.Group className="mb-3">
                    <Form.Label>Number of Loads</Form.Label>
                    <Form.Control
                      type="number"
                      name="num_loads"
                      min="1"
                      max="5"
                      value={parameters.num_loads}
                      onChange={handleChange}
                      required
                    />
                    <Form.Text className="text-muted">Between 1 and 5 loads</Form.Text>
                  </Form.Group>
                </Col>
              </Row>
            </Card.Body>
          </Card>

          {/* Scenario Characteristics -------------------------------------- */}
          <Card className="mb-4">
            <Card.Header className="d-flex align-items-center">
              <Sliders className="me-2" size={20} />
              <span>Scenario Characteristics</span>
            </Card.Header>
            <Card.Body>
              <Row>
                <Col md={6}>
                  <Form.Group className="mb-3">
                    <Form.Label>Peak Load (MW)</Form.Label>
                    <Form.Control
                      type="number"
                      name="peak_load"
                      min="10"
                      max="1000"
                      value={parameters.peak_load}
                      onChange={handleChange}
                      required
                    />
                  </Form.Group>
                </Col>
                <Col md={6}>
                  <Form.Group className="mb-3">
                    <Form.Label>Voltage Profile</Form.Label>
                    <Form.Select
                      name="voltage_profile"
                      value={parameters.voltage_profile}
                      onChange={handleChange}
                    >
                      <option value="flat">Flat</option>
                      <option value="varied">Varied</option>
                      <option value="stressed">Stressed</option>
                    </Form.Select>
                  </Form.Group>
                </Col>
              </Row>
              <Row>
                <Col md={6}>
                  <Form.Group className="mb-3">
                    <Form.Label>Reliability Level</Form.Label>
                    <Form.Select
                      name="reliability_level"
                      value={parameters.reliability_level}
                      onChange={handleChange}
                    >
                      <option value="high">High</option>
                      <option value="medium">Medium</option>
                      <option value="low">Low</option>
                    </Form.Select>
                  </Form.Group>
                </Col>
                <Col md={6}>
                  <Form.Group className="mb-3">
                    <Form.Label>Congestion Level</Form.Label>
                    <Form.Select
                      name="congestion_level"
                      value={parameters.congestion_level}
                      onChange={handleChange}
                    >
                      <option value="high">High</option>
                      <option value="medium">Medium</option>
                      <option value="low">Low</option>
                    </Form.Select>
                  </Form.Group>
                </Col>
              </Row>
            </Card.Body>
          </Card>
        </div>
      )}

      {/* Advanced Options (RAG) - always shown ------------------------------------ */}
      {advancedMode && (
        <Card className="mb-4">
          <Card.Header className="d-flex align-items-center">
            <Database className="me-2" size={20} />
            <span>RAG Settings</span>
          </Card.Header>
          <Card.Body>
            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Check
                    type="checkbox"
                    label="Use RAG (Retrieval Augmented Generation)"
                    name="include_context"
                    checked={parameters.include_context}
                    onChange={handleChange}
                  />
                  <Form.Text className="text-muted">
                    Enhance generation with similar existing scenarios
                  </Form.Text>
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>Similarity Threshold</Form.Label>
                  <Form.Control
                    type="range"
                    name="similarity_threshold"
                    min="0.5"
                    max="0.9"
                    step="0.05"
                    value={parameters.similarity_threshold}
                    onChange={handleChange}
                    disabled={!parameters.include_context}
                  />
                  <div className="d-flex justify-content-between">
                    <span className="text-muted">0.5</span>
                    <span>{parameters.similarity_threshold}</span>
                    <span className="text-muted">0.9</span>
                  </div>
                </Form.Group>
              </Col>
            </Row>
          </Card.Body>
        </Card>
      )}

      {/* Action buttons ------------------------------------------------- */}
      <div className="d-flex justify-content-between mb-4">
        <Button variant="link" className="text-decoration-none" onClick={() => setAdvancedMode(!advancedMode)}>
          {advancedMode ? 'Hide Advanced Options' : 'Show Advanced Options'}
        </Button>
        <Button type="submit" variant="primary" size="lg" disabled={isGenerating}>
          {isGenerating ? 'Generating...' : 'Generate Scenario'}
        </Button>
      </div>
    </Form>
  );

  const renderProgressTab = () => (
    <div className="progress-container text-center">
      <h3 className="mb-4">Generating Grid Scenario</h3>

      <div className="progress-status mb-4">
        <ProgressBar animated now={progress} label={`${progress}%`} />
      </div>

      {/* Steps --------------------------------------------------------- */}
      <div className="generation-steps">
        {/* Step 1 */}
        <div className={`generation-step ${progress >= 10 ? 'completed' : ''}`}>
          <div className="step-indicator">
            {progress >= 10 ? <Check size={24} /> : <span>1</span>}
          </div>
          <div className="step-content">
            <h5>Initializing</h5>
            <p>Setting up generation parameters</p>
          </div>
        </div>

        {/* Step 2 */}
        <div className={`generation-step ${progress >= 30 ? 'completed' : ''}`}>
          <div className="step-indicator">
            {progress >= 30 ? <Check size={24} /> : <span>2</span>}
          </div>
          <div className="step-content">
            <h5>Retrieving Context</h5>
            <p>Finding similar scenarios in database</p>
          </div>
        </div>

        {/* Step 3 */}
        <div className={`generation-step ${progress >= 50 ? 'completed' : ''}`}>
          <div className="step-indicator">
            {progress >= 50 ? <Check size={24} /> : <span>3</span>}
          </div>
          <div className="step-content">
            <h5>Generating</h5>
            <p>Creating scenario using PINN model</p>
          </div>
        </div>

        {/* Step 4 */}
        <div className={`generation-step ${progress >= 70 ? 'completed' : ''}`}>
          <div className="step-indicator">
            {progress >= 70 ? <Check size={24} /> : <span>4</span>}
          </div>
          <div className="step-content">
            <h5>Validating</h5>
            <p>Ensuring physics consistency</p>
          </div>
        </div>

        {/* Step 5 */}
        <div className={`generation-step ${progress >= 90 ? 'completed' : ''}`}>
          <div className="step-indicator">
            {progress >= 90 ? <Check size={24} /> : <span>5</span>}
          </div>
          <div className="step-content">
            <h5>Finalizing</h5>
            <p>Preparing results</p>
          </div>
        </div>
      </div>

      {/* Show error message if any */}
      {error && (
        <ErrorMessage 
          error={error} 
          onRetry={() => setError(null)} 
          onBack={() => navigate('/scenarios')}
        />
      )}
    </div>
  );

  const renderResultTab = () => (
    <div className="result-container">
      {result ? (
        <>
          {/* Success --------------------------------------------------- */}
          <div className="text-center mb-4">
            <h3 className="mb-3">
              <Check size={28} className="text-success me-2" />
              Scenario Generated Successfully
            </h3>
            <p className="lead">Your grid scenario has been generated and is ready to use</p>
          </div>

          {/* Summary --------------------------------------------------- */}
          <Card className="mb-4">
            <Card.Header>Scenario Summary</Card.Header>
            <Card.Body>
              <Row>
                <Col md={6}>
                  <p><strong>ID:</strong> {result.id}</p>
                  <p><strong>Buses:</strong> {parameters.num_buses}</p>
                  <p><strong>Generators:</strong> {parameters.num_generators}</p>
                </Col>
                <Col md={6}>
                  <p><strong>Loads:</strong> {parameters.num_loads}</p>
                  <p><strong>Peak Load:</strong> {parameters.peak_load} MW</p>
                  <p><strong>Reliability Level:</strong> {parameters.reliability_level}</p>
                </Col>
              </Row>
            </Card.Body>
          </Card>

          {/* Actions --------------------------------------------------- */}
          <div className="d-flex justify-content-between">
            <Button variant="outline-primary" onClick={() => setActiveTab('parameters')}>Generate Another</Button>
            <div>
              <Button
                variant="success"
                className="me-2"
                onClick={handleViewDetails}
                disabled={mockDataEnabled}
              >
                View Details
              </Button>
              {mockDataEnabled && (
                <span className="text-muted ms-2">(Unavailable for mock data)</span>
              )}
              <Button variant="outline-secondary">Download JSON</Button>
            </div>
          </div>
        </>
      ) : (
        <Alert variant="warning">
          <Alert.Heading>No Result</Alert.Heading>
          <p>No scenario has been generated yet</p>
          <Button variant="primary" onClick={() => setActiveTab('parameters')}>Go to Generation Form</Button>
        </Alert>
      )}
    </div>
  );

  // --------------------------------------------------------------------
  return (
    <Container className="generate-page">
      <h1 className="mb-4">Generate Grid Scenario</h1>
      <Tabs activeKey={activeTab} onSelect={(key) => setActiveTab(key)} className="mb-4">
        <Tab eventKey="parameters" title="Parameters">
          {renderParametersTab()}
        </Tab>
        <Tab eventKey="progress" title="Progress" disabled={!isGenerating && progress === 0}>
          {renderProgressTab()}
        </Tab>
        <Tab eventKey="result" title="Result" disabled={!result}>
          {renderResultTab()}
        </Tab>
      </Tabs>
    </Container>
  );
};

export default GeneratePage;
