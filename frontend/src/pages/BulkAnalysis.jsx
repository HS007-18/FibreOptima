import React, { useState } from 'react';
import axios from 'axios';
import { Upload, FileText, Activity, Layers, PieChart as PieIcon, BarChart2, TrendingUp, Cpu, Wrench, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, LineChart, Line } from 'recharts';
import InvestigationModal from '../components/InvestigationModal';

const API_URL = 'http://localhost:8000/api';

const COLORS = {
  Normal: '#16a34a',
  Warning: '#d97706',
  'High Risk': '#dc2626',
  'Data Issue': '#64748b'
};

export default function BulkAnalysis() {
  const [file, setFile] = useState(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedBatch, setSelectedBatch] = useState(null);
  const [activeTab, setActiveTab] = useState('Overview');

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_URL}/process`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setData(response.data);
    } catch (err) {
      console.error(err);
      setError("Failed to process dataset. Ensure backend service is active.");
    } finally {
      setLoading(false);
    }
  };

  const batches = data?.batches || [];
  const metrics = data?.metrics || {};
  const machineAnalytics = data?.machine_analytics || [];
  const fabricAnalytics = data?.fabric_analytics || [];
  const shiftAnalytics = data?.shift_analytics || [];
  const operatorAnalytics = data?.operator_analytics || [];

  // Charts processing
  const riskPieData = [
    { name: 'Normal', value: metrics.normal || 0 },
    { name: 'Warning', value: metrics.warnings || 0 },
    { name: 'High Risk', value: metrics.high_risk || 0 },
    { name: 'Data Issue', value: metrics.data_issues || 0 },
  ].filter(d => d.value > 0);

  const batchTrendData = batches.map((b, idx) => ({
    name: b.record_id || `B${idx+1}`,
    waste_pct: b.observed_waste_pct !== null ? parseFloat(b.observed_waste_pct.toFixed(2)) : 0,
    pred_pct: b.predicted_waste_pct !== null ? parseFloat(b.predicted_waste_pct.toFixed(2)) : 0,
    prod: b.production_quantity || 0,
    waste: b.waste_quantity || 0
  }));

  const tabs = [
    { id: 'Overview', label: '📊 Overview' },
    { id: 'Batches', label: '📦 Batch-wise Analysis' },
    { id: 'Machines', label: '⚙️ Machine-wise Waste' },
    { id: 'Fabrics', label: '🧵 Fabric-wise Waste' },
    { id: 'Shifts', label: '🕒 Shift-wise Waste' },
    { id: 'Operators', label: '👤 Operator-wise Waste' },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Multi-Dimensional Production Waste Analytics</h2>
          <p style={{ fontSize: '0.85rem', color: '#64748b' }}>Complete Batch-wise, Machine-wise, Fabric-wise, Shift-wise, and Operator-wise Waste Predictor</p>
        </div>
      </div>

      {/* CSV Upload Section */}
      <div className="card" style={{ marginBottom: '1.5rem', background: '#ffffff' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <FileText size={18} color="#2563eb" /> Upload Production Telemetry Dataset (CSV)
        </h3>
        <p style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '1rem' }}>
          Evaluates all 9 core requirements: Waste %, Machine-wise, Fabric-wise, Shift-wise, Operator-wise, Maintenance, Abnormal Batches, Risk Classification, & Reasons.
        </p>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <input type="file" accept=".csv" onChange={handleFileChange} style={{ fontSize: '0.875rem' }} />
          <button className="btn-primary" onClick={handleUpload} disabled={!file || loading}>
            <Upload size={16} /> {loading ? 'Processing Pipeline...' : 'Analyze Dataset'}
          </button>
        </div>
        {error && <div style={{ color: '#dc2626', fontSize: '0.85rem', marginTop: '0.5rem' }}>{error}</div>}
      </div>

      {data && (
        <>
          {/* Factory Level KPIs */}
          <div className="kpi-grid">
            <div className="kpi-card">
              <div className="kpi-title">Total Records</div>
              <div className="kpi-value">{metrics.total_records}</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-title">Total Production</div>
              <div className="kpi-value">{metrics.total_production} kg</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-title">Total Waste</div>
              <div className="kpi-value" style={{ color: '#d97706' }}>{metrics.total_waste} kg</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-title">Overall Waste %</div>
              <div className="kpi-value" style={{ color: '#2563eb' }}>{metrics.overall_waste_pct}%</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-title" style={{ color: '#16a34a' }}>Normal</div>
              <div className="kpi-value" style={{ color: '#16a34a' }}>{metrics.normal}</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-title" style={{ color: '#d97706' }}>Warnings</div>
              <div className="kpi-value" style={{ color: '#d97706' }}>{metrics.warnings}</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-title" style={{ color: '#dc2626' }}>High Risk</div>
              <div className="kpi-value" style={{ color: '#dc2626' }}>{metrics.high_risk}</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-title" style={{ color: '#64748b' }}>Data Issues</div>
              <div className="kpi-value" style={{ color: '#64748b' }}>{metrics.data_issues}</div>
            </div>
          </div>

          {/* Navigation Tabs corresponding to Problem Statement Requirements */}
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', borderBottom: '1px solid #e2e8f0', paddingBottom: '0.5rem', flexWrap: 'wrap' }}>
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  padding: '0.5rem 1rem',
                  border: 'none',
                  borderRadius: '6px',
                  fontWeight: 600,
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                  background: activeTab === tab.id ? '#2563eb' : '#f1f5f9',
                  color: activeTab === tab.id ? '#ffffff' : '#475569'
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* TAB 1: Overview */}
          {activeTab === 'Overview' && (
            <>
              <div className="grid-3" style={{ marginBottom: '1.5rem' }}>
                <div className="card">
                  <h3 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '0.75rem' }}>Risk Classification</h3>
                  <div style={{ height: 200 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie data={riskPieData} cx="50%" cy="50%" innerRadius={45} outerRadius={70} paddingAngle={4} dataKey="value">
                          {riskPieData.map((entry, idx) => <Cell key={idx} fill={COLORS[entry.name]} />)}
                        </Pie>
                        <Tooltip />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div className="card">
                  <h3 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '0.75rem' }}>Machine-wise Waste %</h3>
                  <div style={{ height: 200 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={machineAnalytics}>
                        <XAxis dataKey="name" />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="avg_waste_pct" fill="#2563eb" radius={[4, 4, 0, 0]} name="Waste %" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div className="card">
                  <h3 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '0.75rem' }}>Fabric-wise Waste %</h3>
                  <div style={{ height: 200 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={fabricAnalytics}>
                        <XAxis dataKey="name" />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="avg_waste_pct" fill="#059669" radius={[4, 4, 0, 0]} name="Waste %" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>

              <div className="grid-3" style={{ marginBottom: '1.5rem' }}>
                <div className="card">
                  <h3 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '0.75rem' }}>Shift-wise Waste %</h3>
                  <div style={{ height: 200 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={shiftAnalytics}>
                        <XAxis dataKey="name" />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="avg_waste_pct" fill="#d97706" radius={[4, 4, 0, 0]} name="Waste %" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div className="card">
                  <h3 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '0.75rem' }}>Operator-wise Waste %</h3>
                  <div style={{ height: 200 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={operatorAnalytics}>
                        <XAxis dataKey="name" />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="avg_waste_pct" fill="#6366f1" radius={[4, 4, 0, 0]} name="Waste %" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div className="card">
                  <h3 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '0.75rem' }}>Predicted vs Observed Waste %</h3>
                  <div style={{ height: 200 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={machineAnalytics}>
                        <XAxis dataKey="name" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="avg_waste_pct" fill="#3b82f6" name="Observed %" />
                        <Bar dataKey="avg_predicted_waste_pct" fill="#8b5cf6" name="Predicted %" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            </>
          )}

          {/* TAB 2: Batch-wise Analysis */}
          {activeTab === 'Batches' && (
            <div className="card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem' }}>Batch-wise Waste & Prediction Trend</h3>
              <div style={{ height: 260, marginBottom: '1.5rem' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={batchTrendData}>
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="waste_pct" stroke="#2563eb" strokeWidth={2} name="Observed Waste %" />
                    <Line type="monotone" dataKey="pred_pct" stroke="#d97706" strokeWidth={2} strokeDasharray="5 5" name="Predicted Waste %" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* TAB 3: Machine-wise Waste */}
          {activeTab === 'Machines' && (
            <div className="card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem' }}>Machine-wise Waste Analysis</h3>
              <div style={{ height: 240, marginBottom: '1.5rem' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={machineAnalytics}>
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="avg_waste_pct" fill="#2563eb" radius={[4, 4, 0, 0]} name="Avg Waste %" />
                    <Bar dataKey="avg_predicted_waste_pct" fill="#8b5cf6" radius={[4, 4, 0, 0]} name="Predicted Waste %" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Machine ID</th>
                      <th>Record Count</th>
                      <th>Total Production</th>
                      <th>Total Waste</th>
                      <th>Avg Waste %</th>
                      <th>Predicted %</th>
                      <th>Anomalies</th>
                      <th>High Risk</th>
                    </tr>
                  </thead>
                  <tbody>
                    {machineAnalytics.map(m => (
                      <tr key={m.name}>
                        <td style={{ fontWeight: 700 }}>{m.name}</td>
                        <td>{m.record_count}</td>
                        <td>{m.total_production} kg</td>
                        <td>{m.total_waste} kg</td>
                        <td style={{ fontWeight: 700, color: '#2563eb' }}>{m.avg_waste_pct}%</td>
                        <td>{m.avg_predicted_waste_pct}%</td>
                        <td>{m.anomaly_count}</td>
                        <td>{m.high_risk_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 4: Fabric-wise Waste */}
          {activeTab === 'Fabrics' && (
            <div className="card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem' }}>Fabric-wise Waste Analysis</h3>
              <div style={{ height: 240, marginBottom: '1.5rem' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={fabricAnalytics}>
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="avg_waste_pct" fill="#059669" radius={[4, 4, 0, 0]} name="Avg Waste %" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Fabric Type</th>
                      <th>Record Count</th>
                      <th>Total Production</th>
                      <th>Total Waste</th>
                      <th>Avg Waste %</th>
                      <th>Anomalies</th>
                    </tr>
                  </thead>
                  <tbody>
                    {fabricAnalytics.map(f => (
                      <tr key={f.name}>
                        <td style={{ fontWeight: 700 }}>{f.name}</td>
                        <td>{f.record_count}</td>
                        <td>{f.total_production} kg</td>
                        <td>{f.total_waste} kg</td>
                        <td style={{ fontWeight: 700, color: '#059669' }}>{f.avg_waste_pct}%</td>
                        <td>{f.anomaly_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 5: Shift-wise Waste */}
          {activeTab === 'Shifts' && (
            <div className="card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem' }}>Shift-wise Waste Analysis</h3>
              <div style={{ height: 240, marginBottom: '1.5rem' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={shiftAnalytics}>
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="avg_waste_pct" fill="#d97706" radius={[4, 4, 0, 0]} name="Avg Waste %" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Shift</th>
                      <th>Record Count</th>
                      <th>Total Production</th>
                      <th>Total Waste</th>
                      <th>Avg Waste %</th>
                      <th>Anomalies</th>
                      <th>High Risk</th>
                    </tr>
                  </thead>
                  <tbody>
                    {shiftAnalytics.map(s => (
                      <tr key={s.name}>
                        <td style={{ fontWeight: 700 }}>{s.name}</td>
                        <td>{s.record_count}</td>
                        <td>{s.total_production} kg</td>
                        <td>{s.total_waste} kg</td>
                        <td style={{ fontWeight: 700, color: '#d97706' }}>{s.avg_waste_pct}%</td>
                        <td>{s.anomaly_count}</td>
                        <td>{s.high_risk_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 6: Operator-wise Waste */}
          {activeTab === 'Operators' && (
            <div className="card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem' }}>Operator-wise Waste Analysis</h3>
              <div style={{ height: 240, marginBottom: '1.5rem' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={operatorAnalytics}>
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="avg_waste_pct" fill="#6366f1" radius={[4, 4, 0, 0]} name="Avg Waste %" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Operator ID</th>
                      <th>Record Count</th>
                      <th>Total Production</th>
                      <th>Total Waste</th>
                      <th>Avg Waste %</th>
                      <th>Anomalies</th>
                    </tr>
                  </thead>
                  <tbody>
                    {operatorAnalytics.map(o => (
                      <tr key={o.name}>
                        <td style={{ fontWeight: 700 }}>{o.name}</td>
                        <td>{o.record_count}</td>
                        <td>{o.total_production} kg</td>
                        <td>{o.total_waste} kg</td>
                        <td style={{ fontWeight: 700, color: '#6366f1' }}>{o.avg_waste_pct}%</td>
                        <td>{o.anomaly_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Processed Production Records Queue Table */}
          <div className="card">
            <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem' }}>Batch Records Queue & Reasons</h3>
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Batch ID</th>
                    <th>Machine</th>
                    <th>Fabric</th>
                    <th>Operator</th>
                    <th>Shift</th>
                    <th>Production</th>
                    <th>Waste</th>
                    <th>Waste %</th>
                    <th>Predicted %</th>
                    <th>ML / OOD</th>
                    <th>Risk Level</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {batches.map((b, idx) => (
                    <tr key={idx}>
                      <td style={{ fontWeight: 600 }}>{b.record_id}</td>
                      <td>{b.machine_id}</td>
                      <td>{b.fabric_type}</td>
                      <td>{b.operator}</td>
                      <td>{b.shift}</td>
                      <td>{b.production_quantity} kg</td>
                      <td>{b.waste_quantity} kg</td>
                      <td style={{ fontWeight: 600 }}>
                        {b.observed_waste_pct !== null ? `${b.observed_waste_pct.toFixed(2)}%` : 'N/A'}
                      </td>
                      <td>{b.predicted_waste_pct !== null ? `${b.predicted_waste_pct.toFixed(2)}%` : 'N/A'}</td>
                      <td>
                        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                          {b.ml_flag && <span className="badge badge-warning">Anomaly</span>}
                          {b.is_ood && <span className="badge badge-ood">OOD</span>}
                        </div>
                      </td>
                      <td>
                        <span className={`badge badge-${b.risk_level.toLowerCase().replace(' ', '-')}`}>
                          {b.risk_level}
                        </span>
                      </td>
                      <td>
                        <button
                          className={b.risk_level === 'DATA ISSUE' ? 'btn-secondary' : 'btn-primary'}
                          style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem' }}
                          onClick={() => setSelectedBatch(b)}
                        >
                          {b.risk_level === 'DATA ISSUE' ? 'Data Issue' : 'Investigate & Reasons'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {selectedBatch && (
        <InvestigationModal
          recordId={selectedBatch.record_id}
          batchData={selectedBatch}
          onClose={() => setSelectedBatch(null)}
        />
      )}
    </div>
  );
}
