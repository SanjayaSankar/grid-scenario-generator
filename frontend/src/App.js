// frontend/src/App.js
import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import { Container } from 'react-bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';
import './styles/App.css';

// Import components
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import { MockDataProvider } from './components/MockDataProvider';

// Import pages
import HomePage from './pages/HomePage';
import GeneratePage from './pages/GeneratePage';
import ScenarioListPage from './pages/ScenarioListPage';
import ScenarioDetailPage from './pages/ScenarioDetailPage';
import ValidatePage from './pages/ValidatePage';

const App = () => {
  return (
    <MockDataProvider>
      <Router>
        <div className="app">
          <Navbar />
          <main className="main-content">
            <Container>
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/generate" element={<GeneratePage />} />
                <Route path="/scenarios" element={<ScenarioListPage />} />
                <Route path="/scenarios/:id" element={<ScenarioDetailPage />} />
                <Route path="/validate" element={<ValidatePage />} />
              </Routes>
            </Container>
          </main>
          <Footer />
        </div>
      </Router>
    </MockDataProvider>
  );
};

export default App;