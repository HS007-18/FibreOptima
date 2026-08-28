import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { Play, Cpu, AlertTriangle, ShieldCheck, HelpCircle, Activity } from 'lucide-react';
import OODExplainer from '../components/OODExplainer';
import IntelligenceStack from '../components/IntelligenceStack';

const API_URL = 'http://localhost:8000/api';

export default function Predict() {
  const { machine_id } = useParams();
  const targetMachine = machine_id || 'M01';

  const [machineProfile, setMachineProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState(null);

  const [telemetry, setTelemetry] = useState({
    "Batch ID": "B-SINGLE-001",
    "Machine ID": targetMachine,
    "Fabric type": "Cotton",
    "Operator": "OP01",
    "Shift": "Morning",
    "Production quantity": 1200.0,
    "Production speed": 850.0,
    "Waste quantity": 25.0,
    "Machine age": 5.0,
    "Humidity": 55.0,
    "Temperature": 25.0,
    "Last maintenance date": "2026-01-15"
  });

  useEffect(() => {
    fetchMachineProfile();
  }, [targetMachine]);

  const fetchMachineProfile = async () => {
    try {
      const res = await axios.get(`${API_URL}/machines/${targetMachine}`);
      setMachineProfile(res.data);
      setTelemetry(prev => ({
        ...prev,
        "Machine ID": targetMachine,
        "Machine age": res.data.installation_date ? 5.0 : 5.0
      }));
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const val = e.target.type === 'number' ? parseFloat(e.target.value) || 0 : e.target.value;
    setTelemetry({ ...telemetry, [e.target.name]: val });
  };

  const handleAnalyze = async (e) => {
    e.preventDefault();
    setAnalyzing(true);
    setResult(null);

    try {
      const res = await axios.post(`${API_URL}/predict`, telemetry);
      setResult(res.data);
    } catch (err) {
      console.error(err);
      alert(err.response?.data?.detail || "Failed to execute prediction pipeline.");
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Single Machine Telemetry Predictor</h2>
        <p style={{ fontSize: '0.85rem', color: '#64748b' }}>Analyze current operating parameters against CompanyDB facts and ML models</p>
      </div>

      <div className="grid-2" style={{ gridTemplateColumns: '1fr 1.2fr' }}>
        {/* Left: Pre-populated Machine Profile + Operational Inputs Form */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          
          {/* Known CompanyDB Context Header */}
          <div className="card" style={{ background: '#f8fafc', borderLeft: '4px solid #2563eb' }}>
            <h3 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Cpu size={18} color="#2563eb" /> CompanyDB Context: {targetMachine}
            </h3>
            {loading ? (
              <div style={{ fontSize: '0.8rem', color: '#64748b' }}>Fetching profile...</div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.8rem', color: '#334155' }}>
                <div><strong>Rated Capacity:</strong> {machineProfile?.rated_capacity} units</div>
                <div><strong>Rated Speed:</strong> {machineProfile?.rated_speed} RPM</div>
                <div><strong>Baseline Waste:</strong> {machineProfile?.baseline?.historical_waste_pct?.toFixed(1)}%</div>
                <div><strong>Status:</strong> {machineProfile?.status}</div>
              </div>
            )}
          </div>

          {/* Form */}
          <form className="card" onSubmit={handleAnalyze}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem' }}>Operational Telemetry Input</h3>
            
            <div className="form-group">
              <label>Machine ID (Fixed from DB)</label>
              <input value={telemetry["Machine ID"]} disabled style={{ background: '#f1f5f9', cursor: 'not-allowed' }} />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label>Production Quantity</label>
                <input type="number" name="Production quantity" value={telemetry["Production quantity"]} onChange={handleChange} required />
              </div>

              <div className="form-group">
                <label>Production Speed (RPM)</label>
                <input type="number" name="Production speed" value={telemetry["Production speed"]} onChange={handleChange} required />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label>Waste Quantity</label>
                <input type="number" name="Waste quantity" value={telemetry["Waste quantity"]} onChange={handleChange} required />
              </div>

              <div className="form-group">
                <label>Fabric Type</label>
                <select name="Fabric type" value={telemetry["Fabric type"]} onChange={handleChange}>
                  <option value="Cotton">Cotton</option>
                  <option value="Polyester">Polyester</option>
                  <option value="Nylon">Nylon</option>
                  <option value="Silk">Silk</option>
                  <option value="Wool">Wool</option>
                </select>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label>Humidity (%)</label>
                <input type="number" name="Humidity" value={telemetry["Humidity"]} onChange={handleChange} required />
              </div>

              <div className="form-group">
                <label>Temperature (°C)</label>
                <input type="number" name="Temperature" value={telemetry["Temperature"]} onChange={handleChange} required />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label>Operator</label>
                <input name="Operator" value={telemetry["Operator"]} onChange={handleChange} />
              </div>

              <div className="form-group">
                <label>Shift</label>
                <select name="Shift" value={telemetry["Shift"]} onChange={handleChange}>
                  <option value="Morning">Morning</option>
                  <option value="Evening">Evening</option>
                  <option value="Night">Night</option>
                </select>
              </div>
            </div>

            <button type="submit" className="btn-primary" style={{ width: '100%', justifyContent: 'center', marginTop: '0.5rem' }} disabled={analyzing}>
              <Play size={16} /> {analyzing ? 'Analyzing Telemetry...' : 'Analyze Batch'}
            </button>
          </form>
        </div>

        {/* Right: Results Page */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {result ? (
            <>
              {/* Main Analysis Result Card */}
              <div className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>{result.machine_id} — Batch Analysis Result</h3>
                  <span className={`badge badge-${result.risk_level.toLowerCase().replace(' ', '-')}`}>
                    {result.risk_level}
                  </span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1.25rem', textAlignment: 'center' }}>
                  <div style={{ background: '#eff6ff', padding: '1rem', borderRadius: '8px', border: '1px solid #bfdbfe' }}>
                    <div style={{ fontSize: '0.75rem', color: '#1e40af', fontWeight: 600 }}>PREDICTED WASTE</div>
                    <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#1d4ed8' }}>
                      {result.predicted_waste_pct !== null ? `${result.predicted_waste_pct.toFixed(2)}%` : 'N/A'}
                    </div>
                  </div>

                  <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                    <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>ML ANOMALY</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 700, color: result.ml_flag ? '#dc2626' : '#16a34a', marginTop: '0.25rem' }}>
                      {result.ml_flag ? 'ANOMALY' : 'NORMAL'}
                    </div>
                  </div>

                  <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                    <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>CAPACITY UTIL.</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a', marginTop: '0.25rem' }}>
                      {result.utilization_percentage ? `${result.utilization_percentage.toFixed(1)}%` : 'N/A'}
                    </div>
                  </div>
                </div>

                {/* OOD Safety Explainer Component */}
                <OODExplainer
                  isOod={result.is_ood}
                  reasons={result.ood_reasons}
                  confidence={result.prediction_confidence}
                />

                {/* Why? Section */}
                <div style={{ marginTop: '1.25rem', paddingTop: '1rem', borderTop: '1px solid #e2e8f0' }}>
                  <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <HelpCircle size={18} color="#2563eb" /> Why was this signal generated?
                  </h4>
                  <ul style={{ fontSize: '0.85rem', color: '#334155', lineHeight: 1.6, paddingLeft: '1.25rem' }}>
                    <li>
                      <strong>Speed Telemetry:</strong> Operating at {telemetry["Production speed"]} RPM vs machine baseline of {machineProfile?.baseline?.historical_avg_speed?.toFixed(0) || 1000} RPM.
                    </li>
                    <li>
                      <strong>Capacity Utilization:</strong> Operating at {result.utilization_percentage?.toFixed(1)}% of rated capacity ({result.rated_capacity} units).
                    </li>
                    <li>
                      <strong>Baseline Deviation:</strong> Predicted waste of {result.predicted_waste_pct?.toFixed(2)}% vs machine baseline of {result.historical_waste_pct?.toFixed(1)}%.
                    </li>
                  </ul>
                </div>
              </div>

              {/* Offline Investigation Output */}
              <div className="card">
                <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <ShieldCheck size={18} color="#16a34a" /> Offline Investigation Engine Report
                </h4>
                <div style={{ background: '#0f172a', color: '#f8fafc', padding: '1rem', borderRadius: '8px', fontFamily: 'monospace', fontSize: '0.8rem', lineHeight: '1.5', whitespace: 'pre-wrap' }}>
                  {result.investigation}
                </div>
              </div>
            </>
          ) : (
            <div className="card" style={{ textAlign: 'center', padding: '4rem 2rem', color: '#94a3b8' }}>
              <Activity size={48} style={{ opacity: 0.2, marginBottom: '1rem' }} />
              <h3>Ready for Batch Telemetry Analysis</h3>
              <p style={{ fontSize: '0.85rem' }}>Adjust operating parameters on the left and click "Analyze Batch" to run the pipeline.</p>
            </div>
          )}

          <IntelligenceStack />
        </div>
      </div>
    </div>
  );
}
