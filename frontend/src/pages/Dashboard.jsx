import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import { AlertTriangle, Cpu, Layers, Activity, TrendingUp, Wrench, ShieldAlert } from 'lucide-react';
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

  const totalMachines = machines.length;
  const overdueMachines = machines.filter(m => (m.maintenance?.days_ago || 0) > 150);

  // Real calculations from CompanyDB baselines — no hardcoded values
  const validWasteBaselines = machines.map(m => m.baseline?.historical_waste_pct).filter(v => v != null);
  const avgWaste = validWasteBaselines.length
    ? (validWasteBaselines.reduce((a, b) => a + b, 0) / validWasteBaselines.length).toFixed(1)
    : '—';

  // Real rated capacity utilization: avg(historical_avg_qty / rated_capacity)
  const utilValues = machines
    .filter(m => m.baseline?.historical_avg_qty && m.rated_capacity)
    .map(m => (m.baseline.historical_avg_qty / m.rated_capacity) * 100);
  const avgUtil = utilValues.length
    ? (utilValues.reduce((a, b) => a + b, 0) / utilValues.length).toFixed(1)
    : '—';

  // Real overdue machine IDs for subtext
  const overdueIds = overdueMachines.map(m => m.machine_id).join(', ') || 'None';

  // Risk pie uses real baseline distribution: machines > 1 std dev above mean = Warning
  const meanWaste = validWasteBaselines.length ? validWasteBaselines.reduce((a, b) => a + b, 0) / validWasteBaselines.length : 0;
  const stdDev = validWasteBaselines.length ? Math.sqrt(validWasteBaselines.map(v => Math.pow(v - meanWaste, 2)).reduce((a, b) => a + b, 0) / validWasteBaselines.length) : 0;
  const normalCount = validWasteBaselines.filter(v => v <= meanWaste + stdDev).length;
  const warnCount = validWasteBaselines.filter(v => v > meanWaste + stdDev && v <= meanWaste + 2 * stdDev).length;
  const highCount = validWasteBaselines.filter(v => v > meanWaste + 2 * stdDev).length;

  const riskPieData = [
    { name: 'Normal', value: normalCount || 0 },
    { name: 'Warning', value: warnCount || 0 },
    { name: 'High Risk', value: highCount || 0 },
  ].filter(d => d.value > 0);

  const machinePerformanceData = machines.map(m => ({
    name: m.machine_id,
    waste: m.baseline?.historical_waste_pct != null ? parseFloat(m.baseline.historical_waste_pct.toFixed(2)) : null,
    batches: m.baseline?.total_batches || 0
  })).filter(m => m.waste !== null);

  return (
    <div>
      {/* Top Level Real CompanyDB KPIs */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-title">Total Registered Machines</div>
          <div className="kpi-value">{totalMachines}</div>
          <div className="kpi-subtext">Active in CompanyDB</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-title" style={{ color: '#dc2626' }}>Overdue Maintenance</div>
          <div className="kpi-value" style={{ color: '#dc2626' }}>{overdueMachines.length}</div>
          <div className="kpi-subtext">&gt; 150 Days — {overdueIds}</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-title" style={{ color: '#d97706' }}>Above-Baseline Machines</div>
          <div className="kpi-value" style={{ color: '#d97706' }}>{warnCount + highCount}</div>
          <div className="kpi-subtext">Waste above historical mean</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-title" style={{ color: '#dc2626' }}>High Waste Outliers</div>
          <div className="kpi-value" style={{ color: '#dc2626' }}>{highCount}</div>
          <div className="kpi-subtext">&gt; 2 std dev above mean</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-title">Avg Historical Waste %</div>
          <div className="kpi-value" style={{ color: '#2563eb' }}>{avgWaste}%</div>
          <div className="kpi-subtext">CompanyDB Mill Baseline</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-title">Avg Capacity Utilization</div>
          <div className="kpi-value" style={{ color: '#059669' }}>{avgUtil}%</div>
          <div className="kpi-subtext">Hist. avg qty / rated capacity</div>
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
                <YAxis unit="%" />
                <Tooltip formatter={(val) => [`${val}%`, 'Baseline Waste']} />
                <Bar dataKey="waste" fill="#2563eb" radius={[4, 4, 0, 0]} name="Baseline Waste %" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Real Machine Performance Table from CompanyDB */}
      <div className="card">
        <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Cpu size={18} color="#2563eb" /> Registered Factory Machines & Maintenance Status
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
                <th>Last Maintenance</th>
                <th>Maintenance Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {machines.map((m) => {
                const daysAgo = m.maintenance?.days_ago || 0;
                const isOverdue = daysAgo > 150;
                return (
                  <tr key={m.machine_id}>
                    <td style={{ fontWeight: 700 }}>{m.machine_id}</td>
                    <td>{m.machine_type || 'Spinning Frame'}</td>
                    <td>{m.rated_capacity ? `${m.rated_capacity} units` : 'N/A'}</td>
                    <td>{m.rated_speed ? `${m.rated_speed} RPM` : 'N/A'}</td>
                    <td>{m.baseline?.historical_waste_pct ? `${m.baseline.historical_waste_pct.toFixed(2)}%` : 'N/A'}</td>
                    <td>{m.maintenance?.maintenance_date || 'N/A'}</td>
                    <td>
                      {isOverdue ? (
                        <span className="badge badge-high-risk" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                          <AlertTriangle size={12} /> {daysAgo} days ago (OVERDUE &gt; 150d)
                        </span>
                      ) : (
                        <span className="badge badge-normal">
                          {daysAgo ? `${daysAgo} days ago` : 'Normal'}
                        </span>
                      )}
                    </td>
                    <td>
                      <Link to={`/machines/${m.machine_id}/predict`} className="btn-secondary" style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem', textDecoration: 'none' }}>
                        Analyze Batch →
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
