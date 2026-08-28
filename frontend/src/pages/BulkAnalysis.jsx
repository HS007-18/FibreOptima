import React, { useState } from 'react';
import axios from 'axios';
import { Upload, AlertTriangle, Layers, FileText, CheckCircle2, TrendingUp, BarChart2 } from 'lucide-react';
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

  // Visual Analytics Processing
  const normalCount = batches.filter(b => b.risk_level === 'NORMAL').length;
  const warningCount = batches.filter(b => b.risk_level === 'WARNING').length;
  const highRiskCount = batches.filter(b => b.risk_level === 'HIGH RISK').length;
  const dataIssueCount = batches.filter(b => b.risk_level === 'DATA ISSUE').length;
  const oodCount = batches.filter(b => b.is_ood).length;
  const anomalyCount = batches.filter(b => b.ml_flag).length;

  const validBatches = batches.filter(b => b.predicted_waste_pct !== null && b.predicted_waste_pct !== undefined);
  const avgWaste = validBatches.length ? (validBatches.reduce((acc, b) => acc + b.predicted_waste_pct, 0) / validBatches.length).toFixed(1) : '0';
  const avgUtil = batches.length ? (batches.reduce((acc, b) => acc + (b.utilization_percentage || 0), 0) / batches.length).toFixed(1) : '0';

  const riskPieData = [
    { name: 'Normal', value: normalCount },
    { name: 'Warning', value: warningCount },
    { name: 'High Risk', value: highRiskCount },
    { name: 'Data Issue', value: dataIssueCount },
  ].filter(d => d.value > 0);

  // Waste by Machine (Bar)
  const machineGroups = {};
  batches.forEach(b => {
    if (!machineGroups[b.machine_id]) {
      machineGroups[b.machine_id] = { machine: b.machine_id, totalWaste: 0, count: 0, totalUtil: 0, anomalies: 0, ood: 0 };
    }
    if (b.predicted_waste_pct !== null) {
      machineGroups[b.machine_id].totalWaste += b.predicted_waste_pct;
      machineGroups[b.machine_id].count += 1;
    }
    if (b.utilization_percentage) machineGroups[b.machine_id].totalUtil += b.utilization_percentage;
    if (b.ml_flag) machineGroups[b.machine_id].anomalies += 1;
    if (b.is_ood) machineGroups[b.machine_id].ood += 1;
  });

  const wasteByMachineData = Object.values(machineGroups).map(g => ({
    machine: g.machine,
    avgWaste: g.count ? parseFloat((g.totalWaste / g.count).toFixed(1)) : 0,
    avgUtil: g.count ? parseFloat((g.totalUtil / g.count).toFixed(1)) : 0,
    anomalies: g.anomalies,
    ood: g.ood
  }));

  // Waste Across Batches (Line)
  const wasteTrendData = batches.map((b, idx) => ({
    batch: b.record_id || `B${idx+1}`,
    waste: b.predicted_waste_pct ? parseFloat(b.predicted_waste_pct.toFixed(2)) : null
  }));

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Bulk Factory Telemetry Analysis</h2>
          <p style={{ fontSize: '0.85rem', color: '#64748b' }}>Process entire CSV batches through complete ML, OOD, CompanyDB, and RAG pipeline</p>
        </div>
      </div>

      {/* CSV Upload Section */}
      <div className="card" style={{ marginBottom: '1.5rem', background: '#ffffff' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <FileText size={18} color="#2563eb" /> Upload Telemetry Dataset (CSV)
        </h3>
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
          {/* KPI Summary */}
          <div className="kpi-grid">
            <div className="kpi-card">
              <div className="kpi-title">Total Batches</div>
              <div className="kpi-value">{batches.length}</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-title" style={{ color: '#16a34a' }}>Normal</div>
              <div className="kpi-value" style={{ color: '#16a34a' }}>{normalCount}</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-title" style={{ color: '#d97706' }}>Warnings</div>
              <div className="kpi-value" style={{ color: '#d97706' }}>{warningCount}</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-title" style={{ color: '#dc2626' }}>High Risk</div>
              <div className="kpi-value" style={{ color: '#dc2626' }}>{highRiskCount}</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-title" style={{ color: '#64748b' }}>Data Issues</div>
              <div className="kpi-value" style={{ color: '#64748b' }}>{dataIssueCount}</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-title" style={{ color: '#991b1b' }}>OOD Batches</div>
              <div className="kpi-value" style={{ color: '#991b1b' }}>{oodCount}</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-title">Avg Waste %</div>
              <div className="kpi-value">{avgWaste}%</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-title">Avg Utilization</div>
              <div className="kpi-value">{avgUtil}%</div>
            </div>
          </div>

          {/* 5 Distinct Charts Section */}
          <div className="grid-2">
            {/* Chart 1: Risk Distribution */}
            <div className="card">
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '1rem' }}>Chart 1 — Risk Level Distribution</h3>
              <div style={{ height: 240 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={riskPieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={4} dataKey="value">
                      {riskPieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[entry.name]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Chart 2: Waste by Machine */}
            <div className="card">
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '1rem' }}>Chart 2 — Average Waste % by Machine</h3>
              <div style={{ height: 240 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={wasteByMachineData}>
                    <XAxis dataKey="machine" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="avgWaste" fill="#2563eb" radius={[4, 4, 0, 0]} name="Avg Waste %" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          <div className="grid-3">
            {/* Chart 3: Waste Across Batches */}
            <div className="card">
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '1rem' }}>Chart 3 — Waste Across Batches</h3>
              <div style={{ height: 220 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={wasteTrendData}>
                    <XAxis dataKey="batch" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="waste" stroke="#2563eb" strokeWidth={2} name="Waste %" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Chart 4: Capacity Utilization */}
            <div className="card">
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '1rem' }}>Chart 4 — Capacity Utilization % by Machine</h3>
              <div style={{ height: 220 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={wasteByMachineData}>
                    <XAxis dataKey="machine" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="avgUtil" fill="#059669" radius={[4, 4, 0, 0]} name="Capacity Util %" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Chart 5: ML Anomaly & OOD Distribution */}
            <div className="card">
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '1rem' }}>Chart 5 — ML Anomalies vs OOD Count</h3>
              <div style={{ height: 220 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={wasteByMachineData}>
                    <XAxis dataKey="machine" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="anomalies" fill="#d97706" name="ML Anomalies" />
                    <Bar dataKey="ood" fill="#dc2626" name="OOD Events" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Machine Comparison Table */}
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem' }}>Machine Performance Comparison</h3>
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Machine</th>
                    <th>Avg Waste %</th>
                    <th>Avg Utilization</th>
                    <th>ML Anomalies</th>
                    <th>OOD Events</th>
                  </tr>
                </thead>
                <tbody>
                  {wasteByMachineData.map((m) => (
                    <tr key={m.machine}>
                      <td style={{ fontWeight: 700 }}>{m.machine}</td>
                      <td>{m.avgWaste}%</td>
                      <td>{m.avgUtil}%</td>
                      <td>{m.anomalies}</td>
                      <td>{m.ood}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Processed Batches Results Table */}
          <div className="card">
            <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem' }}>Processed Batch Queue</h3>
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Batch ID</th>
                    <th>Machine</th>
                    <th>Predicted Waste</th>
                    <th>Capacity Util.</th>
                    <th>ML / OOD Status</th>
                    <th>Risk Level</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {batches.map((b, idx) => (
                    <tr key={idx}>
                      <td style={{ fontWeight: 600 }}>{b.record_id}</td>
                      <td>{b.machine_id}</td>
                      <td>{b.predicted_waste_pct !== null ? `${b.predicted_waste_pct.toFixed(2)}%` : 'N/A'}</td>
                      <td>{b.utilization_percentage ? `${b.utilization_percentage.toFixed(1)}%` : 'N/A'}</td>
                      <td>
                        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                          {b.ml_flag && <span className="badge badge-warning">ML Anomaly</span>}
                          {b.is_ood && <span className="badge badge-ood">OOD</span>}
                          {!b.ml_flag && !b.is_ood && <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Normal</span>}
                        </div>
                      </td>
                      <td>
                        <span className={`badge badge-${b.risk_level.toLowerCase().replace(' ', '-')}`}>
                          {b.risk_level}
                        </span>
                      </td>
                      <td>
                        {b.risk_level === 'DATA ISSUE' ? (
                          <button
                            className="btn-secondary"
                            style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem' }}
                            onClick={() => setSelectedBatch(b)}
                          >
                            Data Issue
                          </button>
                        ) : (
                          <button
                            className="btn-primary"
                            style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem' }}
                            onClick={() => setSelectedBatch(b)}
                          >
                            Investigate
                          </button>
                        )}
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
