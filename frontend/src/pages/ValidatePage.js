import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Container, Row, Col, Card, Form, Button, Alert, Spinner, Tab, Tabs } from 'react-bootstrap';
import { Upload, CheckCircle, XCircle, AlertTriangle, File, FileText } from 'react-feather';
import ApiService from '../services/ApiService';
import '../styles/ValidatePage.css';
import ErrorMessage from '../components/ErrorMessage';

const ValidatePage = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [validating, setValidating] = useState(false);
  const [error, setError] = useState(null);
  const [validationResult, setValidationResult] = useState(null);
  const [activeTab, setActiveTab] = useState('upload');
  const [scenarioText, setScenarioText] = useState('');
  
  // Handle file input change
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.type === 'application/json') {
      setFile(selectedFile);
      setError(null);
    } else {
      setFile(null);
      setError('Please select a valid JSON file.');
    }
  };
  
  // Handle drag events
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };
  
  // Handle drop event
  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.type === 'application/json') {
        setFile(droppedFile);
        setError(null);
      } else {
        setError('Please drop a valid JSON file.');
      }
    }
  };
  
  // Handle text input change
  const handleTextChange = (e) => {
    setScenarioText(e.target.value);
    setError(null);
  };
  
  // Handle form submission for file upload
  const handleFileSubmit = async (e) => {
    e.preventDefault();
    
    if (!file) {
      setError('Please select a file to validate.');
      return;
    }
    
    setUploading(true);
    setError(null);
    
    try {
      // Upload the file
      const uploadResult = await ApiService.uploadScenarioFile(file);
      
      if (uploadResult.error) {
        throw new Error(uploadResult.error);
      }
      
      // Once uploaded, validate the scenario
      await validateScenario(uploadResult.scenario_id);
      
    } catch (err) {
      setError(err.message || 'Failed to upload and validate the file.');
      setValidationResult(null);
    } finally {
      setUploading(false);
    }
  };
  
  // Handle form submission for text input
  const handleTextSubmit = async (e) => {
    e.preventDefault();
    
    if (!scenarioText.trim()) {
      setError('Please enter a scenario to validate.');
      return;
    }
    
    setValidating(true);
    setError(null);
    
    try {
      // Parse the JSON text
      let scenarioData;
      try {
        scenarioData = JSON.parse(scenarioText);
      } catch (parseErr) {
        throw new Error('Invalid JSON format. Please check your input.');
      }
      
      // Validate the parsed scenario directly
      await validateScenarioData(scenarioData);
      
    } catch (err) {
      setError(err.message || 'Failed to validate the scenario.');
      setValidationResult(null);
    } finally {
      setValidating(false);
    }
  };
  
  // Function to validate a scenario by ID
  const validateScenario = async (scenarioId) => {
    setValidating(true);
    
    try {
      const result = await ApiService.validateScenario(scenarioId);
      setValidationResult(result);
    } catch (err) {
      throw new Error('Failed to validate the scenario: ' + err.message);
    } finally {
      setValidating(false);
    }
  };
  
  // Function to validate scenario data directly
  const validateScenarioData = async (scenarioData) => {
    try {
      // For direct validation, we simulate a scenario ID
      const mockScenarioId = 'direct_validation_' + Date.now();
      
      // Call validation API with the data
      const result = await ApiService.validateScenario(mockScenarioId, scenarioData);
      setValidationResult(result);
    } catch (err) {
      throw new Error('Failed to validate the scenario: ' + err.message);
    }
  };

  return (
    <Container className="validate-page">
      <h1 className="mb-4">Validate Grid Scenario</h1>
      <p className="lead mb-4">
        Upload a JSON file or paste your scenario JSON to validate it against physical 
        constraints and run power flow analysis.
      </p>
      
      <Tabs
        activeKey={activeTab}
        onSelect={(k) => setActiveTab(k)}
        className="mb-4"
      >
        <Tab eventKey="upload" title="Upload File">
          <Card className="mb-4">
            <Card.Body>
              <Form onSubmit={handleFileSubmit}>
                <div 
                  className={`file-drop-area ${dragActive ? 'drag-active' : ''} ${file ? 'has-file' : ''}`}
                  onDragEnter={handleDrag}
                  onDragOver={handleDrag}
                  onDragLeave={handleDrag}
                  onDrop={handleDrop}
                >
                  <input 
                    type="file" 
                    id="file-upload" 
                    className="file-input" 
                    accept=".json" 
                    onChange={handleFileChange}
                  />
                  <label htmlFor="file-upload" className="file-label">
                    {file ? (
                      <div className="selected-file">
                        <FileText size={36} className="mb-3 text-gold" />
                        <p className="file-name">{file.name}</p>
                        <p className="file-size">{(file.size / 1024).toFixed(2)} KB</p>
                      </div>
                    ) : (
                      <>
                        <Upload size={36} className="mb-3" />
                        <p className="mb-2">Drag & drop a scenario JSON file here</p>
                        <p className="text-muted small mb-3">or</p>
                        <Button variant="outline-primary" size="sm">Browse Files</Button>
                      </>
                    )}
                  </label>
                </div>
                
                <div className="d-flex justify-content-center mt-4">
                  <Button 
                    type="submit" 
                    variant="primary" 
                    size="lg"
                    disabled={!file || uploading || validating}
                    className="px-4"
                  >
                    {uploading ? (
                      <>
                        <Spinner
                          as="span"
                          animation="border"
                          size="sm"
                          role="status"
                          aria-hidden="true"
                          className="me-2"
                        />
                        Uploading...
                      </>
                    ) : validating ? (
                      <>
                        <Spinner
                          as="span"
                          animation="border"
                          size="sm"
                          role="status"
                          aria-hidden="true"
                          className="me-2"
                        />
                        Validating...
                      </>
                    ) : (
                      'Validate Scenario'
                    )}
                  </Button>
                </div>
              </Form>
            </Card.Body>
          </Card>
        </Tab>
        
        <Tab eventKey="paste" title="Paste JSON">
          <Card className="mb-4">
            <Card.Body>
              <Form onSubmit={handleTextSubmit}>
                <Form.Group className="mb-3">
                  <Form.Label>Enter Scenario JSON</Form.Label>
                  <Form.Control
                    as="textarea"
                    rows={10}
                    value={scenarioText}
                    onChange={handleTextChange}
                    placeholder='{"network": {"bus": [...], "ac_line": [...]}}'
                    className="json-textarea"
                  />
                </Form.Group>
                
                <div className="d-flex justify-content-center">
                  <Button 
                    type="submit" 
                    variant="primary" 
                    size="lg"
                    disabled={!scenarioText.trim() || validating}
                    className="px-4"
                  >
                    {validating ? (
                      <>
                        <Spinner
                          as="span"
                          animation="border"
                          size="sm"
                          role="status"
                          aria-hidden="true"
                          className="me-2"
                        />
                        Validating...
                      </>
                    ) : (
                      'Validate Scenario'
                    )}
                  </Button>
                </div>
              </Form>
            </Card.Body>
          </Card>
        </Tab>
      </Tabs>
      
      {/* Show error message if any */}
      {error && (
        <ErrorMessage 
          error={error} 
          onRetry={() => setError(null)} 
          onBack={() => navigate('/scenarios')}
        />
      )}
      
      {validationResult && (
        <Card className="validation-result-card">
          <Card.Header className="d-flex align-items-center">
            {validationResult.is_valid ? (
              <>
                <CheckCircle size={24} className="text-success me-2" />
                <span className="text-success fw-bold">Scenario Valid</span>
              </>
            ) : (
              <>
                <XCircle size={24} className="text-danger me-2" />
                <span className="text-danger fw-bold">Scenario Invalid</span>
              </>
            )}
          </Card.Header>
          <Card.Body>
            <Row>
              <Col md={6}>
                <h5 className="validation-section-title">Physics Validation</h5>
                {validationResult.physics_validation?.is_valid ? (
                  <Alert variant="success">
                    <div className="d-flex align-items-center">
                      <CheckCircle size={18} className="me-2" />
                      <span>All physics constraints satisfied</span>
                    </div>
                  </Alert>
                ) : (
                  <Alert variant="danger">
                    <div className="d-flex align-items-center mb-2">
                      <XCircle size={18} className="me-2" />
                      <span>Physics validation failed</span>
                    </div>
                    
                    {validationResult.physics_validation?.voltage_violations?.length > 0 && (
                      <div className="validation-issue mt-3">
                        <h6>Voltage Violations:</h6>
                        <ul className="issue-list">
                          {validationResult.physics_validation.voltage_violations.map((violation, index) => (
                            <li key={index}>
                              {violation.bus_id}: {violation.value.toFixed(3)} p.u. (Limit: {violation.limit.toFixed(3)} p.u.)
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    {validationResult.physics_validation?.line_violations?.length > 0 && (
                      <div className="validation-issue mt-3">
                        <h6>Line Flow Violations:</h6>
                        <ul className="issue-list">
                          {validationResult.physics_validation.line_violations.map((violation, index) => (
                            <li key={index}>
                              {violation.line_id}: {violation.value.toFixed(2)} MVA (Limit: {violation.limit.toFixed(2)} MVA)
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </Alert>
                )}
              </Col>
              
              <Col md={6}>
                <h5 className="validation-section-title">OpenDSS Validation</h5>
                {validationResult.opendss_success ? (
                  validationResult.opendss_validation?.voltage_violations?.length === 0 && 
                  validationResult.opendss_validation?.thermal_violations?.length === 0 ? (
                    <Alert variant="success">
                      <div className="d-flex align-items-center">
                        <CheckCircle size={18} className="me-2" />
                        <span>OpenDSS simulation successful with no violations</span>
                      </div>
                    </Alert>
                  ) : (
                    <Alert variant="danger">
                      <div className="d-flex align-items-center mb-2">
                        <XCircle size={18} className="me-2" />
                        <span>OpenDSS simulation found violations</span>
                      </div>
                      
                      {validationResult.opendss_validation?.voltage_violations?.length > 0 && (
                        <div className="validation-issue mt-3">
                          <h6>OpenDSS Voltage Violations:</h6>
                          <ul className="issue-list">
                            {validationResult.opendss_validation.voltage_violations.map((violation, index) => (
                              <li key={index}>{violation}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      
                      {validationResult.opendss_validation?.thermal_violations?.length > 0 && (
                        <div className="validation-issue mt-3">
                          <h6>OpenDSS Thermal Violations:</h6>
                          <ul className="issue-list">
                            {validationResult.opendss_validation.thermal_violations.map((violation, index) => (
                              <li key={index}>{violation}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </Alert>
                  )
                ) : (
                  <Alert variant="warning">
                    <div className="d-flex align-items-center">
                      <AlertTriangle size={18} className="me-2" />
                      <span>OpenDSS validation was skipped or failed to run</span>
                    </div>
                  </Alert>
                )}
              </Col>
            </Row>
            
            <div className="validation-actions mt-4 text-center">
              <Button variant="outline-primary" className="me-3">
                <FileText size={16} className="me-1" />
                Download Validation Report
              </Button>
              <Button variant="primary">
                <File size={16} className="me-1" />
                Save Validated Scenario
              </Button>
            </div>
          </Card.Body>
        </Card>
      )}
    </Container>
  );
};

export default ValidatePage;