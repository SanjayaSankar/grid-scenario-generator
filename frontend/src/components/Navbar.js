// In Navbar.js
// Update the imports at the top to include Form
import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Navbar as BootstrapNavbar, Nav, Container, Button } from 'react-bootstrap';
import { Zap, Grid, List, Database, Menu, X } from 'react-feather';
import { useMockDataContext } from '../components/MockDataProvider';
import '../styles/Navbar.css';

const Navbar = () => {
  const location = useLocation();
  const [expanded, setExpanded] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const { mockDataEnabled, setMockDataEnabled } = useMockDataContext();

  // Handle scroll effect
  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 20) {
        setScrolled(true);
      } else {
        setScrolled(false);
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  // Close mobile menu on location change
  useEffect(() => {
    setExpanded(false);
  }, [location]);

  return (
    <BootstrapNavbar 
      expand="lg" 
      expanded={expanded}
      className={`main-navbar ${scrolled ? 'scrolled' : ''}`}
      variant="dark"
    >
      <Container>
        <BootstrapNavbar.Brand as={Link} to="/" className="navbar-brand">
          <div className="brand-icon">
            <Zap size={24} />
          </div>
          <span className="brand-text">
            Grid<span className="text-gold">Scenario</span>
          </span>
        </BootstrapNavbar.Brand>

        
        
        <BootstrapNavbar.Toggle 
          aria-controls="basic-navbar-nav" 
          onClick={() => setExpanded(!expanded)}
          className="navbar-toggler"
        >
          {expanded ? <X size={24} /> : <Menu size={24} />}
        </BootstrapNavbar.Toggle>
        
        <BootstrapNavbar.Collapse id="basic-navbar-nav">
          <Nav className="me-auto">
            <Nav.Link 
              as={Link} 
              to="/" 
              className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
            >
              <Grid size={18} className="nav-icon" />
              <span>Home</span>
            </Nav.Link>
            
            <Nav.Link 
              as={Link} 
              to="/generate" 
              className={`nav-link ${location.pathname === '/generate' ? 'active' : ''}`}
            >
              <Zap size={18} className="nav-icon" />
              <span>Generate</span>
            </Nav.Link>
            
            <Nav.Link 
              as={Link} 
              to="/scenarios" 
              className={`nav-link ${location.pathname === '/scenarios' ? 'active' : ''}`}
            >
              <Database size={18} className="nav-icon" />
              <span>Scenarios</span>
            </Nav.Link>
            
            <Nav.Link 
              as={Link} 
              to="/validate" 
              className={`nav-link ${location.pathname === '/validate' ? 'active' : ''}`}
            >
              <List size={18} className="nav-icon" />
              <span>Validate</span>
            </Nav.Link>
          </Nav>
          
          <div className="d-flex">
            <Button 
              as={Link}
              to="/generate"
              variant="gold"
              className="nav-action-btn"
            >
              Create Scenario
            </Button>
          </div>
        </BootstrapNavbar.Collapse>
      </Container>
    </BootstrapNavbar>
  );
};

export default Navbar;