import React from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Machines from './pages/Machines';
import Predict from './pages/Predict';
import BulkAnalysis from './pages/BulkAnalysis';
import Knowledge from './pages/Knowledge';
import SystemStatus from './pages/SystemStatus';
import './index.css';

function HeaderTitle() {
  const location = useLocation();
  const pathTitles = {
    '/': 'Factory Operational Dashboard',
    '/machines': 'Company DB Machine Catalog',
    '/predict': 'Single Batch Telemetry Analysis',
    '/bulk-analysis': 'Bulk Dataset Telemetry Analysis',
    '/knowledge': 'Knowledge & Technical Evidence Pipeline',
    '/status': 'System Health & Component Status',
  };

  const title = pathTitles[location.pathname] || 'Machine Telemetry Predictor';

  return (
    <div className="topbar">
      <h1 className="page-title">{title}</h1>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '0.8rem', color: '#64748b' }}>
        <span style={{ display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%', background: '#16a34a' }}></span>
        System Engine: <strong>Local Offline Mode</strong>
      </div>
    </div>
  );
}

function App() {
  return (
    <Router>
      <div className="app-layout">
        <Sidebar />
        <div className="main-wrapper">
          <HeaderTitle />
          <main className="page-content">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/machines" element={<Machines />} />
              <Route path="/predict" element={<Predict />} />
              <Route path="/machines/:machine_id/predict" element={<Predict />} />
              <Route path="/bulk-analysis" element={<BulkAnalysis />} />
              <Route path="/knowledge" element={<Knowledge />} />
              <Route path="/status" element={<SystemStatus />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;
