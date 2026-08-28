import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import { Cpu, Play, HelpCircle, Activity, ShieldCheck, AlertTriangle, ArrowLeft, BarChart2, CheckCircle2, BookOpen, Wrench } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import OODExplainer from '../components/OODExplainer';
import IntelligenceStack from '../components/IntelligenceStack';

const API_URL = 'http://localhost:8000/api';

export default function Predict() {
  const { machineId } = useParams();
  const [machineProfile, setMachineProfile] = useState(null);
  const [telemetry, setTelemetry] = useState({
    "Batch ID": `B-SINGLE-${Math.floor(100 + Math.random() * 900)}`,
    "Machine ID": machineId || "M01",
    "Fabric type": "Cotton",
    "Operator": "OP01",
    "Shift": "Morning",
    "Production quantity": 1400.0,
    "Production speed": 1200.0,
    "Waste quantity": 45.0,
    "Humidity": 70.0,
    "Temperature": 26.0,
  });

  const [result, setResult] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    if (machineId) {
      axios.get(`${API_URL}/machines/${machineId}`)
        .then(res => {
          setMachineProfile(res.data);
          setTelemetry(prev => ({
            ...prev,
            "Machine ID": machineId,
            "Production speed": res.data.rated_speed || 1200.0,
            "Production quantity": Math.round((res.data.rated_capacity || 1800) * 0.8)
          }));
        })
        .catch(err => console.error(err));
    }
  }, [machineId]);

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    setTelemetry(prev => ({
      ...prev,
      [name]: type === 'number' ? (value === '' ? '' : parseFloat(value)) : value
    }));
  };

  const handleAnalyze = async (e) => {
    e.preventDefault();
    setAnalyzing(true);
    try {
      const res = await axios.post(`${API_URL}/predict`, telemetry);
      setResult(res.data);
    } catch (err) {
      console.error(err);
      alert("Failed to process batch prediction.");
    } finally {
      setAnalyzing(false);
    }
  };

  // Metrics for Single Machine Charts
  const obsWaste = telemetry["Production quantity"] > 0 ? (telemetry["Waste quantity"] / telemetry["Production quantity"] * 100) : 0;
  const baselineWaste = result?.historical_waste_pct ?? machineProfile?.baseline?.historical_waste_pct ?? 5.8;
  const predWaste = result?.predicted_waste_pct ?? 4.63;

  const wasteChartData = [
    { name: 'Observed Waste %', value: parseFloat(obsWaste.toFixed(2)), fill: '#2563eb' },
    { name: 'Historical Baseline %', value: parseFloat(baselineWaste.toFixed(2)), fill: '#64748b' },
    { name: 'ML Predicted Waste %', value: parseFloat(predWaste.toFixed(2)), fill: '#d97706' }
  ];

  const speedCapacityData = [
    { name: 'Speed (RPM)', current: telemetry["Production speed"] || 0, limit: machineProfile?.rated_speed || 1200 },
    { name: 'Capacity Util (%)', current: result?.utilization_percentage ? parseFloat(result.utilization_percentage.toFixed(1)) : 77.8, limit: 100 }
  ];

  // Helper parser for recommendations
  const parseRecommendations = (text) => {
    if (!text) return [
      "Verify production speed settings against rated machine limits (1200 RPM)",
      "Schedule preventive maintenance review within 48 hours",
      "Monitor humidity levels to maintain fiber elasticity during spinning"
    ];
    const matches = text.match(/→[^\n→]+/g);
    if (!matches) return [
      "Inspect machine alignment and sensor calibration",
      "Verify environmental controls (humidity/temperature) within specification"
    ];
    return matches.map(m => m.replace(/^→\s?/, '').trim());
  };

  return (
    <div>
      <div style={{ marginBottom: '1.25rem' }}>
        <Link to="/machines" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', color: '#2563eb', textDecoration: 'none', fontSize: '0.85rem', fontWeight: 600 }}>
          <ArrowLeft size={16} /> Back to Factory Machines Catalog
        </Link>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginTop: '0.5rem' }}>
          Single Production Record Analysis — Machine {telemetry["Machine ID"]}
        </h2>
        <p style={{ fontSize: '0.85rem', color: '#64748b' }}>
          Machine permanent context (capacity, rated speed, age, maintenance history) is automatically loaded from CompanyDB. Enter new production record telemetry below.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', alignItems: 'start' }}>
        {/* Left: Saved Machine Profile & New Production Telemetry Form */}
        <div>
          {/* Machine Permanent Context Card */}
          {machineProfile && (
            <div className="card" style={{ marginBottom: '1.25rem', background: '#f8fafc', border: '1px solid #e2e8f0' }}>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#0f172a' }}>
                <Cpu size={18} color="#2563eb" /> CompanyDB Permanent Machine Context
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', fontSize: '0.85rem', color: '#334155' }}>
                <div><strong>Machine Type:</strong> {machineProfile.machine_type || 'Spinning Frame'}</div>
                <div><strong>Rated Capacity:</strong> {machineProfile.rated_capacity} units</div>
                <div><strong>Rated Speed:</strong> {machineProfile.rated_speed} RPM</div>
                <div><strong>Historical Waste:</strong> {machineProfile.baseline?.historical_waste_pct?.toFixed(1)}%</div>
                <div><strong>Installation Date:</strong> {machineProfile.installation_date}</div>
                <div><strong>Status:</strong> {machineProfile.status}</div>
              </div>
            </div>
          )}

          {/* Clean Telemetry Form (Without redundant machine age / maintenance re-entry) */}
          <form className="card" onSubmit={handleAnalyze}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem' }}>New Production Record Telemetry</h3>
            
            <div className="form-group">
              <label>Machine ID (Fixed from DB)</label>
              <input value={telemetry["Machine ID"]} disabled style={{ background: '#f1f5f9', cursor: 'not-allowed' }} />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label>Production Quantity (kg)</label>
                <input type="number" name="Production quantity" value={telemetry["Production quantity"]} onChange={handleChange} required />
              </div>

              <div className="form-group">
                <label>Production Speed (RPM)</label>
                <input type="number" name="Production speed" value={telemetry["Production speed"]} onChange={handleChange} required />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label>Waste Quantity (kg)</label>
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

        {/* Right: Interactive Visual Results Page */}
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

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1.25rem', textAlign: 'center' }}>
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
              </div>

              {/* Single Machine Visual Analytics Charts */}
              <div className="card">
                <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#0f172a' }}>
                  <BarChart2 size={18} color="#2563eb" /> Single Machine Waste Breakdown & Performance Charts
                </h3>

                {/* Chart 1: Waste Comparison Bar Chart */}
                <div style={{ marginBottom: '1.5rem' }}>
                  <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: '#475569', marginBottom: '0.5rem' }}>
                    Waste Comparison: Observed vs Baseline vs ML Predicted Waste %
                  </h4>
                  <div style={{ height: 180 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={wasteChartData} layout="vertical">
                        <XAxis type="number" unit="%" />
                        <YAxis dataKey="name" type="category" width={150} style={{ fontSize: '0.8rem', fontWeight: 600 }} />
                        <Tooltip formatter={(val) => [`${val}%`, 'Waste']} />
                        <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                          {wasteChartData.map((entry, idx) => <cell key={idx} fill={entry.fill} />)}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Chart 2: Speed & Utilization Limits Chart */}
                <div>
                  <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: '#475569', marginBottom: '0.5rem' }}>
                    Operating Speed & Capacity Utilization vs Rated Limits
                  </h4>
                  <div style={{ height: 180 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={speedCapacityData}>
                        <XAxis dataKey="name" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="current" fill="#2563eb" name="Observed Current" radius={[4, 4, 0, 0]} />
                        <Bar dataKey="limit" fill="#94a3b8" name="Rated Upper Limit" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
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
