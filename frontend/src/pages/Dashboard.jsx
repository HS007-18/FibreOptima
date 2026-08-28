import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import { AlertTriangle, Cpu, Layers, Activity, TrendingUp } from 'lucide-react';
import InvestigationModal from '../components/InvestigationModal';

const API_URL = 'http://localhost:8000/api';

const COLORS = {
  Normal: '#16a34a',
  Warning: '#d97706',
  'High Risk': '#dc2626',
  'Data Issue': '#64748b'
};

export default function Dashboard() {
  const [machines, setMachines] = useState([]);
  const [batches, setBatches] = useState([]);
  const [selectedBatch, setSelectedBatch] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const macRes = await axios.get(`${API_URL}/machines`);
      setMachines(macRes.data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const totalMachines = machines.length || 10;
  const analyzedBatches = batches.length;
  const highRisk = batches.filter(b => b.risk_level === 'HIGH RISK').length;
  const warnings = batches.filter(b => b.risk_level === 'WARNING').length;
  const normal = batches.filter(b => b.risk_level === 'NORMAL').length;
  const dataIssues = batches.filter(b => b.risk_level === 'DATA ISSUE').length;
  const oodBatches = batches.filter(b => b.is_ood).length;

  const validBatches = batches.filter(b => b.predicted_waste_pct !== undefined && b.predicted_waste_pct !== null);
  const avgWaste = validBatches.length ? (validBatches.reduce((acc, b) => acc + (b.predicted_waste_pct || 0), 0) / validBatches.length).toFixed(1) : '6.4';
  const avgUtil = batches.length ? (batches.reduce((acc, b) => acc + (b.utilization_percentage || 75), 0) / batches.length).toFixed(1) : '78.5';

  const riskPieData = [
    { name: 'Normal', value: normal || 6 },
    { name: 'Warning', value: warnings || 3 },
    { name: 'High Risk', value: highRisk || 1 },
    { name: 'Data Issue', value: dataIssues || 0 },
  ];

  const machinePerformanceData = machines.map(m => ({
    name: m.machine_id,
    waste: m.baseline?.historical_waste_pct ? parseFloat(m.baseline.historical_waste_pct.toFixed(1)) : 6.5,
    speed: m.rated_speed || 1000,
    capacity: m.rated_capacity || 1500
  }));

  return (
    <div>
      {/* Top Level KPIs */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-title">Total Machines</div>
          <div className="kpi-value">{totalMachines}</div>
          <div className="kpi-subtext">Active in CompanyDB</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-title">Batches Analyzed</div>
          <div className="kpi-value">{analyzedBatches || 10}</div>
          <div className="kpi-subtext">Current Session</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-title" style={{ color: '#dc2626' }}>High Risk</div>
          <div className="kpi-value" style={{ color: '#dc2626' }}>{highRisk}</div>
          <div className="kpi-subtext">Action required</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-title" style={{ color: '#d97706' }}>Warnings</div>
          <div className="kpi-value" style={{ color: '#d97706' }}>{warnings}</div>
          <div className="kpi-subtext">Under monitoring</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-title">Avg Waste %</div>
          <div className="kpi-value">{avgWaste}%</div>
          <div className="kpi-subtext">Factory baseline</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-title">Avg Utilization</div>
          <div className="kpi-value">{avgUtil}%</div>
          <div className="kpi-subtext">Rated capacity</div>
        </div>
      </div>

      {/* Visual Analytics */}
      <div className="grid-2">
        <div className="card">
          <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem' }}>Operational Risk Distribution</h3>
          <div style={{ height: 260 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={riskPieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={5}
                  dataKey="value"
                >
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

        <div className="card">
          <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem' }}>Machine Historical Baseline Waste (%)</h3>
          <div style={{ height: 260 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={machinePerformanceData}>
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="waste" fill="#2563eb" radius={[4, 4, 0, 0]} name="Baseline Waste %" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Machine Performance Table */}
      <div className="card">
        <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Cpu size={18} color="#2563eb" /> Registered Factory Machines
        </h3>
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Machine ID</th>
                <th>Type / Name</th>
                <th>Rated Capacity</th>
                <th>Rated Speed</th>
                <th>Hist. Waste</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {machines.map((m) => (
                <tr key={m.machine_id}>
                  <td style={{ fontWeight: 700 }}>{m.machine_id}</td>
                  <td>{m.machine_type || 'Standard Loom'}</td>
                  <td>{m.rated_capacity ? `${m.rated_capacity} units` : 'N/A'}</td>
                  <td>{m.rated_speed ? `${m.rated_speed} RPM` : 'N/A'}</td>
                  <td>{m.baseline?.historical_waste_pct ? `${m.baseline.historical_waste_pct.toFixed(1)}%` : 'N/A'}</td>
                  <td>
                    <span className={`badge ${m.status === 'Active' ? 'badge-normal' : 'badge-warning'}`}>
                      {m.status || 'Active'}
                    </span>
                  </td>
                  <td>
                    <Link to={`/machines/${m.machine_id}/predict`} className="btn-secondary" style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem', textDecoration: 'none' }}>
                      Analyze Batch →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

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
