import React from 'react';
import { Container, Row, Col } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { GitHub, Send, Code, Coffee } from 'react-feather';
import '../styles/Footer.css';

const Footer = () => {
  const currentYear = new Date().getFullYear();
  
  return (
    <footer className="main-footer">
      <Container>
        <Row className="py-4">
          <Col lg={4} md={6} className="mb-4 mb-md-0">
            <div className="footer-brand">
              <h3 className="footer-title">
                Grid<span className="text-gold">Scenario</span>
              </h3>
              <p className="footer-description">
                A generative AI system for creating synthetic power grid scenarios using 
                Physics-Informed Neural Networks and RAG techniques.
              </p>
            </div>
            
            <div className="footer-social">
              <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="social-link">
                <GitHub size={20} />
              </a>
              <a href="mailto:info@example.com" className="social-link">
                <Send size={20} />
              </a>
              <a href="https://example.com/docs" target="_blank" rel="noopener noreferrer" className="social-link">
                <Code size={20} />
              </a>
              <a href="https://buymeacoffee.com" target="_blank" rel="noopener noreferrer" className="social-link">
                <Coffee size={20} />
              </a>
            </div>
          </Col>
          
          <Col lg={2} md={6} className="mb-4 mb-md-0">
            <h5 className="footer-heading">Quick Links</h5>
            <ul className="footer-links">
              <li>
                <Link to="/" className="footer-link">Home</Link>
              </li><li>
                <Link to="/generate" className="footer-link">Generate</Link>
              </li>
              <li>
                <Link to="/scenarios" className="footer-link">Scenarios</Link>
              </li>
              <li>
                <Link to="/validate" className="footer-link">Validate</Link>
              </li>
              <li>
                <Link to="/about" className="footer-link">About</Link>
              </li>
            </ul>
          </Col>
          
          <Col lg={3} md={6} className="mb-4 mb-md-0">
            <h5 className="footer-heading">Technologies</h5>
            <ul className="footer-links">
              <li>
                <a href="https://pytorch.org" target="_blank" rel="noopener noreferrer" className="footer-link">PyTorch</a>
              </li>
              <li>
                <a href="https://www.epri.com/pages/sa/opendss" target="_blank" rel="noopener noreferrer" className="footer-link">OpenDSS</a>
              </li>
              <li>
                <a href="https://reactjs.org" target="_blank" rel="noopener noreferrer" className="footer-link">React</a>
              </li>
              <li>
                <a href="https://fastapi.tiangolo.com" target="_blank" rel="noopener noreferrer" className="footer-link">FastAPI</a>
              </li>
              <li>
                <a href="https://d3js.org" target="_blank" rel="noopener noreferrer" className="footer-link">D3.js</a>
              </li>
            </ul>
          </Col>
          
          <Col lg={3} md={6}>
            <h5 className="footer-heading">Resources</h5>
            <ul className="footer-links">
              <li>
                <a href="#documentation" className="footer-link">Documentation</a>
              </li>
              <li>
                <a href="#api" className="footer-link">API Reference</a>
              </li>
              <li>
                <a href="#tutorials" className="footer-link">Tutorials</a>
              </li>
              <li>
                <a href="#examples" className="footer-link">Examples</a>
              </li>
              <li>
                <a href="#faq" className="footer-link">FAQ</a>
              </li>
            </ul>
          </Col>
        </Row>
        
        <div className="footer-divider"></div>
        
        <div className="footer-bottom">
          <p className="copyright">
            &copy; {currentYear} GridScenario Generator. All rights reserved.
          </p>
          <div className="footer-bottom-links">
            <a href="#privacy" className="bottom-link">Privacy Policy</a>
            <a href="#terms" className="bottom-link">Terms of Service</a>
            <a href="#contact" className="bottom-link">Contact Us</a>
          </div>
        </div>
      </Container>
    </footer>
  );
};

export default Footer;