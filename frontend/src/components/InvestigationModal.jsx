import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, X, AlertTriangle, ShieldCheck, FileText, CheckCircle2 } from 'lucide-react';

const API_URL = 'http://localhost:8000/api';

export default function InvestigationModal({ recordId, batchData, onClose }) {
  const [investigation, setInvestigation] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (batchData?.risk_level === 'DATA ISSUE') {
      setLoading(false);
      return;
    }

    axios.get(`${API_URL}/investigate/${recordId}`)
      .then(res => {
        setInvestigation(res.data.investigation);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setInvestigation("Offline investigation unavailable or skipped for invalid records.");
        setLoading(false);
      });
  }, [recordId, batchData]);

  const isDataIssue = batchData?.risk_level === 'DATA ISSUE';

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" style={{ maxWidth: '750px', maxHeight: '85vh', overflowY: 'auto' }} onClick={e => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', borderBottom: '1px solid #e2e8f0', pb: '0.75rem' }}>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#0f172a' }}>
            <Search size={20} color="#2563eb" />
            {isDataIssue ? 'Data Issue Summary' : `Offline Intelligence Report: ${recordId}`}
          </h2>
          <button style={{ background: 'none', border: 'none', cursor: 'pointer' }} onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {isDataIssue ? (
          <div style={{ background: '#f8fafc', padding: '1.5rem', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#64748b', fontWeight: 700, marginBottom: '0.75rem' }}>
              <AlertTriangle size={20} color="#dc2626" />
              STATUS: REJECTED AT DATA VALIDATION LAYER
            </div>
            <p style={{ fontSize: '0.9rem', color: '#334155', marginBottom: '1rem' }}>
              This record contained invalid telemetry data or an unrecognized machine ID and was safely stopped before reaching ML inference models or RAG indexers.
            </p>
            <div style={{ background: '#ffffff', padding: '1rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.85rem' }}>
              <div><strong>Record ID:</strong> {recordId}</div>
              <div><strong>Machine ID:</strong> {batchData?.machine_id || 'Unknown'}</div>
              <div><strong>Predicted Waste:</strong> N/A</div>
              <div><strong>Risk Classification:</strong> DATA ISSUE</div>
            </div>
          </div>
        ) : loading ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>
            Running offline investigation over CompanyDB & Chroma RAG...
          </div>
        ) : (
          <div>
            {batchData && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.75rem', marginBottom: '1.25rem', background: '#f8fafc', padding: '1rem', borderRadius: '8px' }}>
                <div>
                  <div style={{ fontSize: '0.7rem', color: '#64748b' }}>MACHINE</div>
                  <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>{batchData.machine_id}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.7rem', color: '#64748b' }}>PREDICTED WASTE</div>
                  <div style={{ fontWeight: 700, fontSize: '0.95rem', color: '#2563eb' }}>
                    {batchData.predicted_waste_pct ? `${batchData.predicted_waste_pct.toFixed(2)}%` : 'N/A'}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '0.7rem', color: '#64748b' }}>RISK LEVEL</div>
                  <div style={{ fontWeight: 700, fontSize: '0.95rem', color: batchData.risk_level === 'HIGH RISK' ? '#dc2626' : '#d97706' }}>
                    {batchData.risk_level}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '0.7rem', color: '#64748b' }}>OOD STATUS</div>
                  <div style={{ fontWeight: 700, fontSize: '0.95rem', color: batchData.is_ood ? '#dc2626' : '#16a34a' }}>
                    {batchData.is_ood ? 'OOD DETECTED' : 'IN DISTRIBUTION'}
                  </div>
                </div>
              </div>
            )}

            <div style={{ background: '#0f172a', color: '#f8fafc', padding: '1.25rem', borderRadius: '8px', fontFamily: 'monospace', fontSize: '0.825rem', lineHeight: '1.6', whitespace: 'pre-wrap', maxHeight: '400px', overflowY: 'auto' }}>
              {investigation}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
