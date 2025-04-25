import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Badge, Button, Form, Pagination, Spinner, Alert } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { Search, Filter, Grid, Download, Eye, Clock, ChevronRight } from 'react-feather';
import ApiService from '../services/ApiService';
import '../styles/ScenarioListPage.css';
import { useMockDataContext } from '../components/MockDataProvider';


const ScenarioListPage = () => {
  const [scenarios, setScenarios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [sortOrder, setSortOrder] = useState('newest');
  const { mockDataEnabled } = useMockDataContext();
  
  const scenariosPerPage = 10;
  
  useEffect(() => {
    fetchScenarios();
  }, [currentPage, filterType, sortOrder]);
  
  const fetchScenarios = async () => {
    setLoading(true);
    try {
      // Calculate offset based on current page
      const offset = (currentPage - 1) * scenariosPerPage;
      
      // Fetch scenarios from API
      const result = await ApiService.getScenarios({
        limit: scenariosPerPage,
        offset: offset,
        filter: filterType !== 'all' ? filterType : undefined,
        sort: sortOrder
      });
      
      let scenariosData = result.scenarios || [];
      
      // Process scenarios to check validity 
      // (actual validation logic based on physical constraints)
      scenariosData = scenariosData.map(scenario => {
        // Return scenario with the original validity status from the backend
        return {
          ...scenario,
          summary: {
            ...scenario.summary
            // Keep the original is_valid value from the backend
          }
        };
      });
      
      // If using mock data, add some mock scenarios to the list
      if (mockDataEnabled) {
        const mockScenarios = [
          {
            id: `mock-scenario-valid-${Date.now()}`,
            timestamp: new Date().toISOString(),
            summary: {
              num_buses: 3,
              num_lines: 2,
              num_devices: 3,
              is_valid: true  // Valid scenario
            }
          },
          {
            id: `mock-scenario-invalid-${Date.now() - 100000}`,
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            summary: {
              num_buses: 5,
              num_lines: 4,
              num_devices: 6,
              is_valid: false  // Invalid scenario
            }
          }
        ];
        
        // Add mock scenarios to the beginning of the list
        scenariosData = [...mockScenarios, ...scenariosData];
      }
      
      setScenarios(scenariosData);
      setTotalPages(Math.ceil(result.total / scenariosPerPage));
      
    } catch (err) {
      setError('Failed to fetch scenarios. Please try again later.');
      console.error('Error fetching scenarios:', err);
      
      // For demo/development: mock some data if API fails
      mockScenarios();
    } finally {
      setLoading(false);
    }
  };
  
  // Function to generate mock data for development/demo
  const mockScenarios = () => {
    const mockData = [];
    for (let i = 1; i <= 10; i++) {
      // Create a mix of valid and invalid scenarios
      const isValid = i % 2 !== 0; // Alternating valid and invalid
      
      mockData.push({
        id: isValid ? `scenario_valid_${i}` : `scenario_invalid_${i}`,
        timestamp: new Date(Date.now() - i * 86400000).toISOString(),
        summary: {
          num_buses: Math.floor(Math.random() * 10) + 3,
          num_lines: Math.floor(Math.random() * 15) + 5,
          num_devices: Math.floor(Math.random() * 8) + 2,
          is_valid: isValid // Properly mark validity status
        }
      });
    }
    setScenarios(mockData);
    setTotalPages(5); // Mock 5 pages total
  };
  
  const handleSearch = (e) => {
    e.preventDefault();
    // Reset to first page when searching
    setCurrentPage(1);
    fetchScenarios();
  };
  
  const handleFilterChange = (e) => {
    setFilterType(e.target.value);
    setCurrentPage(1); // Reset to first page when filter changes
  };
  
  const handleSortChange = (e) => {
    setSortOrder(e.target.value);
    setCurrentPage(1); // Reset to first page when sort changes
  };
  
  const handlePageChange = (pageNumber) => {
    setCurrentPage(pageNumber);
    window.scrollTo(0, 0);
  };
  
  // Format date for display
  const formatDate = (dateString) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (e) {
      return 'Invalid date';
    }
  };
  
  // Filtered scenarios based on search term
  const filteredScenarios = scenarios.filter(scenario => {
    // First apply search term filter
    const matchesSearch = scenario.id.toLowerCase().includes(searchTerm.toLowerCase());
    
    // Then apply validity filter if needed
    if (filterType === 'valid') {
      return matchesSearch && scenario.summary.is_valid === true;
    } else if (filterType === 'invalid') {
      return matchesSearch && scenario.summary.is_valid === false;
    }
    
    // Default case - just apply search filter
    return matchesSearch;
  });
  
  // Create pagination items
  const paginationItems = [];
  for (let number = 1; number <= totalPages; number++) {
    paginationItems.push(
      <Pagination.Item 
        key={number} 
        active={number === currentPage}
        onClick={() => handlePageChange(number)}
      >
        {number}
      </Pagination.Item>
    );
  }

  return (
    <Container className="scenario-list-page">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1>Grid Scenarios</h1>
        <Button 
          as={Link} 
          to="/generate" 
          variant="primary" 
          className="btn-gold"
        >
          <Grid size={18} className="me-2" />
          Generate New Scenario
        </Button>
      </div>
      
      <Card className="filter-card mb-4">
        <Card.Body>
          <Row>
            <Col md={6} lg={4} className="mb-3 mb-md-0">
              <Form onSubmit={handleSearch}>
                <div className="search-wrapper">
                  <Form.Control
                    type="text"
                    placeholder="Search scenarios..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                  <Button variant="outline-primary" type="submit" className="search-btn">
                    <Search size={18} />
                  </Button>
                </div>
              </Form>
            </Col>
            
            <Col md={3} lg={4} className="mb-3 mb-md-0">
              <div className="d-flex align-items-center filter-select-wrapper">
                <Filter size={18} className="me-2 text-gold" />
                <Form.Select 
                  value={filterType}
                  onChange={handleFilterChange}
                  aria-label="Filter scenarios"
                >
                  <option value="all">All Scenarios</option>
                  <option value="valid">Valid Only</option>
                  <option value="invalid">Invalid Only</option>
                  <option value="recent">Recently Created</option>
                </Form.Select>
              </div>
            </Col>
            
            <Col md={3} lg={4}>
              <div className="d-flex align-items-center filter-select-wrapper">
                <Clock size={18} className="me-2 text-gold" />
                <Form.Select 
                  value={sortOrder}
                  onChange={handleSortChange}
                  aria-label="Sort scenarios"
                >
                  <option value="newest">Newest First</option>
                  <option value="oldest">Oldest First</option>
                  <option value="buses">Most Buses</option>
                  <option value="complexity">Most Complex</option>
                </Form.Select>
              </div>
            </Col>
          </Row>
        </Card.Body>
      </Card>
      
      {loading ? (
        <div className="text-center my-5">
          <Spinner animation="border" variant="primary" className="spinner-gold" />
          <p className="mt-3">Loading scenarios...</p>
        </div>
      ) : error ? (
        <Alert variant="danger">
          <Alert.Heading>Error</Alert.Heading>
          <p>{error}</p>
        </Alert>
      ) : filteredScenarios.length === 0 ? (
        <div className="text-center my-5">
          <div className="empty-state-icon mb-3">
            <Grid size={48} />
          </div>
          <h4 className="mb-3">No Scenarios Found</h4>
          <p className="text-muted mb-4">
            No scenarios match your current filters or search criteria.
          </p>
          <Button 
            variant="primary" 
            onClick={() => {
              setSearchTerm('');
              setFilterType('all');
              setCurrentPage(1);
            }}
          >
            Clear Filters
          </Button>
        </div>
      ) : (
        <div className="scenarios-container">
          {filteredScenarios.map((scenario) => (
            <Card key={scenario.id} className="scenario-card mb-3 hover-card">
              <Card.Body>
                <Row>
                  <Col md={7}>
                    <h5 className="scenario-title">
                      <Link to={`/scenarios/${scenario.id}`} className="text-gold">
                        {scenario.id}
                      </Link>
                      {scenario.summary.is_valid ? (
                        <Badge bg="success" className="ms-2">Valid</Badge>
                      ) : (
                        <Badge bg="danger" className="ms-2">Invalid</Badge>
                      )}
                    </h5>
                    <div className="scenario-date">
                      <Clock size={14} className="me-1" />
                      <span>Created: {formatDate(scenario.timestamp)}</span>
                    </div>
                    <div className="scenario-metrics mt-2">
                      <Badge className="badge-metric me-2">
                        Buses: {scenario.summary.num_buses}
                      </Badge>
                      <Badge className="badge-metric me-2">
                        Lines: {scenario.summary.num_lines}
                      </Badge>
                      <Badge className="badge-metric">
                        Devices: {scenario.summary.num_devices}
                      </Badge>
                    </div>
                  </Col>
                  <Col md={5} className="d-flex align-items-center justify-content-end">
                    <div className="scenario-actions">
                      <Button 
                        as={Link}
                        to={`/scenarios/${scenario.id}`}
                        variant="primary" 
                        size="sm" 
                        className="me-2"
                      >
                        <Eye size={16} className="me-1" />
                        View
                      </Button>
                      <Button 
                        variant="outline-primary" 
                        size="sm"
                      >
                        <Download size={16} className="me-1" />
                        Download
                      </Button>
                    </div>
                  </Col>
                </Row>
              </Card.Body>
            </Card>
          ))}
          
          {totalPages > 1 && (
            <div className="pagination-container mt-4 d-flex justify-content-center">
              <Pagination>
                <Pagination.First 
                  onClick={() => handlePageChange(1)} 
                  disabled={currentPage === 1}
                />
                <Pagination.Prev 
                  onClick={() => handlePageChange(currentPage - 1)} 
                  disabled={currentPage === 1}
                />
                
                {currentPage > 2 && <Pagination.Ellipsis />}
                
                {paginationItems.filter(item => {
                  const pageNum = parseInt(item.props.children);
                  return pageNum === 1 || 
                         pageNum === totalPages || 
                         (pageNum >= currentPage - 1 && pageNum <= currentPage + 1);
                })}
                
                {currentPage < totalPages - 1 && <Pagination.Ellipsis />}
                
                <Pagination.Next 
                  onClick={() => handlePageChange(currentPage + 1)} 
                  disabled={currentPage === totalPages}
                />
                <Pagination.Last 
                  onClick={() => handlePageChange(totalPages)} 
                  disabled={currentPage === totalPages}
                />
              </Pagination>
            </div>
          )}
        </div>
      )}
    </Container>
  );
};

export default ScenarioListPage;