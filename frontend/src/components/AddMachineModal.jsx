import React, { useState } from 'react';
import axios from 'axios';
import { X, PlusCircle } from 'lucide-react';

const API_URL = 'http://localhost:8000/api';

export default function AddMachineModal({ onClose, onAdded }) {
  const [formData, setFormData] = useState({
    machine_id: '',
    machine_type: 'Cotton Loom',
    rated_capacity: '1500',
    rated_speed: '1000',
    installation_date: '2026-01-01',
    status: 'Active'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.machine_id.trim()) {
      setError('Machine ID is required.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await axios.post(`${API_URL}/machines`, {
        machine_id: formData.machine_id.trim(),
        machine_type: formData.machine_type,
        rated_capacity: parseFloat(formData.rated_capacity),
        rated_speed: parseFloat(formData.rated_speed),
        installation_date: formData.installation_date,
        status: formData.status
      });
      onAdded();
      onClose();
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to add machine.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <PlusCircle color="#2563eb" size={20} /> Add New Machine
          </h2>
          <button style={{ background: 'none', border: 'none', cursor: 'pointer' }} onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {error && (
          <div style={{ background: '#fef2f2', border: '1px solid #fecaca', color: '#991b1b', padding: '0.5rem 0.75rem', borderRadius: '6px', fontSize: '0.85rem', marginBottom: '1rem' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Machine ID (e.g. M11)</label>
            <input name="machine_id" value={formData.machine_id} onChange={handleChange} placeholder="M11" required />
          </div>

          <div className="form-group">
            <label>Machine Type / Name</label>
            <input name="machine_type" value={formData.machine_type} onChange={handleChange} placeholder="Cotton Loom" />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label>Rated Capacity (Units)</label>
              <input type="number" name="rated_capacity" value={formData.rated_capacity} onChange={handleChange} required />
            </div>

            <div className="form-group">
              <label>Rated Speed (RPM)</label>
              <input type="number" name="rated_speed" value={formData.rated_speed} onChange={handleChange} required />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label>Installation Date</label>
              <input type="date" name="installation_date" value={formData.installation_date} onChange={handleChange} />
            </div>

            <div className="form-group">
              <label>Status</label>
              <select name="status" value={formData.status} onChange={handleChange}>
                <option value="Active">Active</option>
                <option value="Maintenance">Maintenance</option>
                <option value="Inactive">Inactive</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
            <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Adding...' : 'Save Machine to DB'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
