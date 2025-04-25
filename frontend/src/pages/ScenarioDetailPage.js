import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  Container, Row, Col, Card, Button, Tabs, Tab, 
  Alert, Spinner, Badge, ListGroup, Table 
} from 'react-bootstrap';
import { 
  FileText, CheckCircle, XCircle, Download, 
  BarChart2, Grid, Terminal, Info 
} from 'react-feather';
import ApiService from '../services/ApiService';
import ScenarioVisualization from '../components/ScenarioVisualization';
import '../styles/ScenarioDetailPage.css';
import { useMockDataContext } from '../components/MockDataProvider';

// Conditionally import ReactJson
let ReactJson = null;
try {
  ReactJson = require('react-json-view').default;
} catch (error) {
  console.warn('react-json-view not available, using fallback');
}

const ScenarioDetailPage = () => {
  const { id } = useParams();
  const { mockDataEnabled, generateMockScenario } = useMockDataContext();
  const [scenario, setScenario] = useState(null);
  const [validationResult, setValidationResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  
  useEffect(() => {
    const fetchScenario = async () => {
      try {
        setLoading(true);

        // Check if this is a mock scenario ID (they start with "mock-scenario-")
        if (id.startsWith('mock-scenario-')) {
          if (mockDataEnabled) {
            // Generate a consistent mock scenario based on the ID
            const mockScenario = generateMockScenario({
              num_buses: 3,
              num_generators: 2,
              num_loads: 1
            });
            
            setScenario(mockScenario.scenario);
            
            // Also set a mock validation result
            setValidationResult({
              is_valid: true,
              physics_validation: {
                is_valid: true,
                voltage_violations: [],
                line_violations: []
              },
              opendss_validation: {
                success: true,
                voltage_violations: [],
                thermal_violations: []
              },
              opendss_success: true
            });
            
            setLoading(false);
            return;
          }
        }
        
        // Fetch scenario data
        const scenarioData = await ApiService.getScenarioById(id);
        setScenario(scenarioData);
        
        // Fetch validation results if available
        if (scenarioData) {
          const validationData = await ApiService.getValidationResults(id);
          setValidationResult(validationData);
        }
      } catch (err) {
        setError(err.message || 'Failed to fetch scenario');
      } finally {
        setLoading(false);
      }
    };
    
    fetchScenario();
  }, [id]);
  
  const handleValidate = async () => {
    setLoading(true);
    
    try {
      const result = await ApiService.validateScenario(id);
      setValidationResult(result);
    } catch (err) {
      setError(err.message || 'Validation failed');
    } finally {
      setLoading(false);
    }
  };
  
  const handleDownloadJson = () => {
    if (!scenario) return;
    
    const dataStr = JSON.stringify(scenario, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const downloadLink = document.createElement('a');
    downloadLink.setAttribute('href', dataUri);
    downloadLink.setAttribute('download', `scenario_${id}.json`);
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
  };
  
  if (loading) {
    return (
      <Container className="text-center my-5">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading...</span>
        </Spinner>
        <p className="mt-3">Loading scenario data...</p>
      </Container>
    );
  }
  
  if (error) {
    return (
      <Container className="my-5">
        <Alert variant="danger">
          <Alert.Heading>Error</Alert.Heading>
          <p>{error}</p>
          <div className="d-flex justify-content-end">
            <Link to="/scenarios">
              <Button variant="outline-danger">Back to Scenarios</Button>
            </Link>
          </div>
        </Alert>
      </Container>
    );
  }
  
  if (!scenario) {
    return (
      <Container className="my-5">
        <Alert variant="warning">
          <Alert.Heading>Scenario Not Found</Alert.Heading>
          <p>The scenario with ID {id} could not be found.</p>
          <div className="d-flex justify-content-end">
            <Link to="/scenarios">
              <Button variant="outline-primary">View All Scenarios</Button>
            </Link>
          </div>
        </Alert>
      </Container>
    );
  }
  
  // Extract scenario details
  const network = scenario.network || {};
  const numBuses = network.bus?.length || 0;
  const numLines = network.ac_line?.length || 0;
  const numTransformers = network.two_winding_transformer?.length || 0;
  const devices = network.simple_dispatchable_device || [];
  const generators = devices.filter(d => d.device_type === 'producer');
  const loads = devices.filter(d => d.device_type === 'consumer');
  
  const renderOverviewTab = () => (
    <div className="overview-tab">
      <Row>
        <Col md={6}>
          <Card className="mb-4">
            <Card.Header className="d-flex align-items-center">
              <Info className="me-2" size={20} />
              <span>Scenario Information</span>
            </Card.Header>
            <Card.Body>
              <p><strong>ID:</strong> {id}</p>
              <p><strong>Base MVA:</strong> {network.general?.base_norm_mva || 100} MVA</p>
              <p>
                <strong>Status:</strong>{' '}
                {validationResult?.is_valid ? (
                  <Badge bg="success">Valid</Badge>
                ) : validationResult ? (
                  <Badge bg="danger">Invalid</Badge>
                ) : (
                  <Badge bg="secondary">Not Validated</Badge>
                )}
              </p>
            </Card.Body>
          </Card>
          
          <Card className="mb-4">
            <Card.Header className="d-flex align-items-center">
              <Grid className="me-2" size={20} />
              <span>Network Components</span>
            </Card.Header>
            <ListGroup variant="flush">
              <ListGroup.Item className="d-flex justify-content-between align-items-center">
                Buses
                <Badge bg="primary" pill>{numBuses}</Badge>
              </ListGroup.Item>
              <ListGroup.Item className="d-flex justify-content-between align-items-center">
                AC Lines
                <Badge bg="primary" pill>{numLines}</Badge>
              </ListGroup.Item>
              <ListGroup.Item className="d-flex justify-content-between align-items-center">
                Transformers
                <Badge bg="primary" pill>{numTransformers}</Badge>
              </ListGroup.Item>
              <ListGroup.Item className="d-flex justify-content-between align-items-center">
                Generators
                <Badge bg="primary" pill>{generators.length}</Badge>
              </ListGroup.Item>
              <ListGroup.Item className="d-flex justify-content-between align-items-center">
                Loads
                <Badge bg="primary" pill>{loads.length}</Badge>
              </ListGroup.Item>
            </ListGroup>
          </Card>
        </Col>
        
        <Col md={6}>
          {validationResult ? (
            <Card className="mb-4">
              <Card.Header className="d-flex align-items-center">
                {validationResult.is_valid ? (
                  <CheckCircle className="me-2 text-success" size={20} />
                ) : (
                  <XCircle className="me-2 text-danger" size={20} />
                )}
                <span>Validation Results</span>
              </Card.Header>
              <Card.Body>
                <p>
                  <strong>Physics Validation:</strong>{' '}
                  {validationResult.physics_validation?.is_valid ? (
                    <Badge bg="success">Passed</Badge>
                  ) : (
                    <Badge bg="danger">Failed</Badge>
                  )}
                </p>
                
                <p>
                  <strong>OpenDSS Validation:</strong>{' '}
                  {validationResult.opendss_success ? (
                    validationResult.opendss_validation?.voltage_violations?.length === 0 && 
                    validationResult.opendss_validation?.thermal_violations?.length === 0 ? (
                      <Badge bg="success">Passed</Badge>
                    ) : (
                      <Badge bg="danger">Failed</Badge>
                    )
                  ) : (
                    <Badge bg="secondary">Not Run</Badge>
                  )}
                </p>
                
                {validationResult.physics_validation?.voltage_violations?.length > 0 && (
                  <div className="mt-3">
                    <h6>Voltage Violations</h6>
                    <ul className="small">
                      {validationResult.physics_validation.voltage_violations.map((v, i) => (
                        <li key={i} className="text-danger">
                          {v.bus_id}: {v.value.toFixed(3)} p.u. (Limit: {v.limit.toFixed(3)} p.u.)
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {validationResult.physics_validation?.line_violations?.length > 0 && (
                  <div className="mt-3">
                    <h6>Line Violations</h6>
                    <ul className="small">
                      {validationResult.physics_validation.line_violations.map((v, i) => (
                        <li key={i} className="text-danger">
                          {v.line_id}: {v.value.toFixed(2)} MVA (Limit: {v.limit.toFixed(2)} MVA)
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </Card.Body>
              <Card.Footer>
                <Button 
                  variant="outline-primary"
                  size="sm"
                  onClick={() => setActiveTab('validation')}
                >
                  View Full Validation Results
                </Button>
              </Card.Footer>
            </Card>
          ) : (
            <Card className="mb-4">
              <Card.Header>Validation</Card.Header>
              <Card.Body className="text-center p-4">
                <p className="mb-4">
                  This scenario has not been validated yet. Run validation to check 
                  if it meets physics constraints and operational requirements.
                </p>
                <Button 
                  variant="primary" 
                  onClick={handleValidate}
                  disabled={loading}
                >
                  {loading ? 'Validating...' : 'Validate Scenario'}
                </Button>
              </Card.Body>
            </Card>
          )}
          
          <Card>
            <Card.Header className="d-flex align-items-center">
              <BarChart2 className="me-2" size={20} />
              <span>Power Summary</span>
            </Card.Header>
            <Card.Body>
              {generators.length > 0 && (
                <div className="mb-3">
                  <h6>Generation</h6>
                  <Table size="sm">
                    <thead>
                      <tr>
                        <th>Generator</th>
                        <th>Bus</th>
                        <th>P (MW)</th>
                        <th>Q (MVAr)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {generators.slice(0, 5).map((gen, i) => (
                        <tr key={i}>
                          <td>{gen.uid}</td>
                          <td>{gen.bus}</td>
                          <td>{(gen.initial_status?.p || 0) * (network.general?.base_norm_mva || 100)}</td>
                          <td>{(gen.initial_status?.q || 0) * (network.general?.base_norm_mva || 100)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                  {generators.length > 5 && (
                    <p className="text-muted small mt-1">+ {generators.length - 5} more generators</p>
                  )}
                </div>
              )}
              
              {loads.length > 0 && (
                <div>
                  <h6>Load</h6>
                  <Table size="sm">
                    <thead>
                      <tr>
                        <th>Load</th>
                        <th>Bus</th>
                        <th>P (MW)</th>
                        <th>Q (MVAr)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {loads.slice(0, 5).map((load, i) => (
                        <tr key={i}>
                          <td>{load.uid}</td>
                          <td>{load.bus}</td>
                          <td>{(load.initial_status?.p || 0) * (network.general?.base_norm_mva || 100)}</td>
                          <td>{(load.initial_status?.q || 0) * (network.general?.base_norm_mva || 100)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                  {loads.length > 5 && (
                    <p className="text-muted small mt-1">+ {loads.length - 5} more loads</p>
                  )}
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </div>
  );
  
  const renderVisualizationTab = () => (
    <div className="visualization-tab">
      <Card>
        <Card.Header>Network Visualization</Card.Header>
        <Card.Body>
          <ScenarioVisualization scenario={scenario} />
        </Card.Body>
      </Card>
    </div>
  );
  
  const renderRawDataTab = () => (
    <div className="raw-data-tab">
      <Card>
        <Card.Header className="d-flex align-items-center justify-content-between">
          <div className="d-flex align-items-center">
            <FileText className="me-2" size={20} />
            <span>Raw Scenario Data</span>
          </div>
          <Button 
            variant="outline-secondary" 
            size="sm"
            onClick={handleDownloadJson}
          >
            <Download size={16} className="me-1" />
            Download JSON
          </Button>
        </Card.Header>
        <Card.Body>
          <div className="json-viewer">
            {ReactJson ? (
              <ReactJson 
                src={scenario} 
                name={null}
                collapsed={1}
                displayDataTypes={false}
                enableClipboard={false}
                theme="monokai"
              />
            ) : (
              <pre>{JSON.stringify(scenario, null, 2)}</pre>
            )}
          </div>
        </Card.Body>
      </Card>
    </div>
  );
  
  const renderValidationTab = () => (
    <div className="validation-tab">
      {validationResult ? (
        <>
          <Card className="mb-4">
            <Card.Header className="d-flex align-items-center">
              {validationResult.is_valid ? (
                <CheckCircle className="me-2 text-success" size={20} />
              ) : (
                <XCircle className="me-2 text-danger" size={20} />
              )}
              <span>Validation Summary</span>
            </Card.Header>
            <Card.Body>
              <Row>
                <Col md={6}>
                  <div className="mb-3">
                    <h6>Physics Validation</h6>
                    <p>
                      {validationResult.physics_validation?.is_valid ? (
                        <span className="text-success">Passed all physics checks</span>
                      ) : (
                        <span className="text-danger">Failed physics validation</span>
                      )}
                    </p>
                  </div>
                </Col>
                <Col md={6}>
                  <div className="mb-3">
                    <h6>OpenDSS Validation</h6>
                    <p>
                      {validationResult.opendss_success ? (
                        validationResult.opendss_validation?.voltage_violations?.length === 0 && 
                        validationResult.opendss_validation?.thermal_violations?.length === 0 ? (
                          <span className="text-success">Passed OpenDSS simulation</span>
                        ) : (
                          <span className="text-danger">Failed OpenDSS simulation</span>
                        )
                      ) : (
                        <span className="text-secondary">OpenDSS validation not run</span>
                      )}
                    </p>
                  </div>
                </Col>
              </Row>
              
              <div className="mt-3">
                <Button 
                  variant="primary" 
                  onClick={handleValidate}
                  disabled={loading}
                  className="me-2"
                >
                  {loading ? 'Validating...' : 'Re-run Validation'}
                </Button>
              </div>
            </Card.Body>
          </Card>
          
          <Row>
            <Col md={6}>
              <Card className="mb-4">
                <Card.Header>Voltage Checks</Card.Header>
                <Card.Body>
                  {validationResult.physics_validation?.voltage_violations?.length > 0 ? (
                    <>
                      <Alert variant="danger">
                        <strong>
                          {validationResult.physics_validation.voltage_violations.length} voltage violations found
                        </strong>
                      </Alert>
                      <Table size="sm">
                        <thead>
                          <tr>
                            <th>Bus</th>
                            <th>Type</th>
                            <th>Value (p.u.)</th>
                            <th>Limit (p.u.)</th>
                          </tr>
                        </thead>
                        <tbody>
                          {validationResult.physics_validation.voltage_violations.map((v, i) => (
                            <tr key={i}>
                              <td>{v.bus_id}</td>
                              <td>{v.type}</td>
                              <td className="text-danger">{v.value.toFixed(3)}</td>
                              <td>{v.limit.toFixed(3)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </Table>
                    </>
                  ) : (
                    <Alert variant="success">
                      All bus voltages are within acceptable limits
                    </Alert>
                  )}
                </Card.Body>
              </Card>
            </Col>
            
            <Col md={6}>
              <Card className="mb-4">
                <Card.Header>Line Flow Checks</Card.Header>
                <Card.Body>
                  {validationResult.physics_validation?.line_violations?.length > 0 ? (
                    <>
                      <Alert variant="danger">
                        <strong>
                          {validationResult.physics_validation.line_violations.length} line flow violations found
                        </strong>
                      </Alert>
                      <Table size="sm">
                        <thead>
                          <tr>
                            <th>Line</th>
                            <th>Type</th>
                            <th>Flow (MVA)</th>
                            <th>Limit (MVA)</th>
                          </tr>
                        </thead>
                        <tbody>
                          {validationResult.physics_validation.line_violations.map((v, i) => (
                            <tr key={i}>
                              <td>{v.line_id}</td>
                              <td>{v.type}</td>
                              <td className="text-danger">{v.value.toFixed(2)}</td>
                              <td>{v.limit.toFixed(2)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </Table>
                    </>
                  ) : (
                    <Alert variant="success">
                      All line flows are within thermal limits
                    </Alert>
                  )}
                </Card.Body>
              </Card>
            </Col>
          </Row>
          
          {validationResult.opendss_success && (
            <Card className="mb-4">
              <Card.Header className="d-flex align-items-center">
                <Terminal className="me-2" size={20} />
                <span>OpenDSS Validation</span>
              </Card.Header>
              <Card.Body>
                {validationResult.opendss_validation?.voltage_violations?.length === 0 && 
                 validationResult.opendss_validation?.thermal_violations?.length === 0 ? (
                  <Alert variant="success">
                    <div className="d-flex align-items-center">
                      <CheckCircle size={18} className="me-2" />
                      <span>OpenDSS simulation completed successfully with no violations</span>
                    </div>
                  </Alert>
                ) : (
                  <Alert variant="danger">
                    <div className="d-flex align-items-center mb-2">
                      <XCircle size={18} className="me-2" />
                      <span>OpenDSS simulation detected violations</span>
                    </div>
                    
                    {validationResult.opendss_validation?.voltage_violations?.length > 0 && (
                      <div className="mt-3">
                        <h6>OpenDSS Voltage Violations</h6>
                        <ul className="small">
                          {validationResult.opendss_validation.voltage_violations.map((v, i) => (
                            <li key={i} className="text-danger">{v}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    {validationResult.opendss_validation?.thermal_violations?.length > 0 && (
                      <div className="mt-3">
                        <h6>OpenDSS Thermal Violations</h6>
                        <ul className="small">
                          {validationResult.opendss_validation.thermal_violations.map((v, i) => (
                            <li key={i} className="text-danger">{v}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </Alert>
                )}
              </Card.Body>
            </Card>
          )}
        </>
      ) : (
        <Card>
          <Card.Body className="text-center p-5">
            <h5 className="mb-3">No Validation Results</h5>
            <p className="mb-4">
              This scenario has not been validated yet. Run validation to check 
              if it meets physics constraints and operational requirements.
            </p>
            <Button 
              variant="primary" 
              onClick={handleValidate}
              disabled={loading}
              size="lg"
            >
              {loading ? 'Validating...' : 'Validate Scenario'}
            </Button>
          </Card.Body>
        </Card>
      )}
    </div>
  );
  
  return (
    <Container className="scenario-detail-page">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1>Scenario Details</h1>
        
        <div>
          <Link to="/scenarios">
            <Button variant="outline-secondary" className="me-2">
              Back to List
            </Button>
          </Link>
          
          <Button variant="outline-primary" onClick={handleDownloadJson}>
            <Download size={16} className="me-1" />
            Download
          </Button>
        </div>
      </div>
      
      <Tabs
        activeKey={activeTab}
        onSelect={(key) => setActiveTab(key)}
        className="mb-4"
      >
        <Tab eventKey="overview" title="Overview">
          {renderOverviewTab()}
        </Tab>
        <Tab eventKey="visualization" title="Visualization">
          {renderVisualizationTab()}
        </Tab>
        <Tab eventKey="raw" title="Raw Data">
          {renderRawDataTab()}
        </Tab>
        <Tab eventKey="validation" title="Validation">
          {renderValidationTab()}
        </Tab>
      </Tabs>
    </Container>
  );
};

export default ScenarioDetailPage;