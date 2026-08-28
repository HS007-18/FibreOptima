import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Cpu, PlusCircle, ArrowRight, Activity, Wrench } from 'lucide-react';
import AddMachineModal from '../components/AddMachineModal';

const API_URL = 'http://localhost:8000/api';

export default function Machines() {
  const [machines, setMachines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);

  useEffect(() => {
    fetchMachines();
  }, []);

  const fetchMachines = async () => {
    try {
      const res = await axios.get(`${API_URL}/machines`);
      setMachines(res.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Company Machine Catalog</h2>
          <p style={{ fontSize: '0.85rem', color: '#64748b' }}>Fetched directly from Company Database (SQLite facts)</p>
        </div>
        <button className="btn-primary" onClick={() => setShowAddModal(true)}>
          <PlusCircle size={18} /> Add Machine
        </button>
      </div>

      {loading ? (
        <div style={{ padding: '3rem', textAlign: 'center', color: '#64748b' }}>Loading machines from database...</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1.5rem' }}>
          {machines.map((m) => (
            <div key={m.machine_id} className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                  <div>
                    <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a' }}>{m.machine_id}</h3>
                    <div style={{ fontSize: '0.85rem', color: '#475569', fontWeight: 500 }}>{m.machine_type || 'Standard Loom'}</div>
                  </div>
                  <span className={`badge ${m.status === 'Active' ? 'badge-normal' : 'badge-warning'}`}>
                    {m.status || 'Active'}
                  </span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', padding: '0.75rem 0', borderTop: '1px solid #e2e8f0', borderBottom: '1px solid #e2e8f0', marginBottom: '1rem', fontSize: '0.825rem' }}>
                  <div>
                    <div style={{ color: '#94a3b8', fontSize: '0.75rem' }}>Rated Capacity</div>
                    <div style={{ fontWeight: 600 }}>{m.rated_capacity} units</div>
                  </div>
                  <div>
                    <div style={{ color: '#94a3b8', fontSize: '0.75rem' }}>Rated Speed</div>
                    <div style={{ fontWeight: 600 }}>{m.rated_speed} RPM</div>
                  </div>
                  <div>
                    <div style={{ color: '#94a3b8', fontSize: '0.75rem' }}>Hist. Avg Waste</div>
                    <div style={{ fontWeight: 600, color: '#2563eb' }}>
                      {m.baseline?.historical_waste_pct ? `${m.baseline.historical_waste_pct.toFixed(1)}%` : 'N/A'}
                    </div>
                  </div>
                  <div>
                    <div style={{ color: '#94a3b8', fontSize: '0.75rem' }}>Maintenance</div>
                    <div style={{ fontWeight: 600 }}>
                      {m.maintenance ? `${m.maintenance.days_ago} days ago` : 'None'}
                    </div>
                  </div>
                </div>
              </div>

              <Link
                to={`/machines/${m.machine_id}/predict`}
                className="btn-secondary"
                style={{ width: '100%', justifyContent: 'center', textDecoration: 'none' }}
              >
                View Machine & Analyze Batch <ArrowRight size={16} />
              </Link>
            </div>
          ))}
        </div>
      )}

      {showAddModal && (
        <AddMachineModal
          onClose={() => setShowAddModal(false)}
          onAdded={fetchMachines}
        />
      )}
    </div>
  );
}
