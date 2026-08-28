import React from 'react';
import { AlertCircle, HelpCircle } from 'lucide-react';

export default function OODExplainer({ isOod, reasons, confidence }) {
  return (
    <div style={{ background: isOod ? '#fff5f5' : '#f8fafc', border: `1px solid ${isOod ? '#feb2b2' : '#e2e8f0'}`, borderRadius: '8px', padding: '1rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600, fontSize: '0.875rem', color: isOod ? '#9b2c2c' : '#0f172a' }}>
          <AlertCircle size={18} color={isOod ? '#c53030' : '#2563eb'} />
          Out-of-Distribution (OOD) Safety Status: {isOod ? 'OOD DETECTED' : 'IN DISTRIBUTION'}
        </div>
        <span style={{ fontSize: '0.75rem', padding: '2px 8px', borderRadius: '4px', background: confidence === 'Low' ? '#fee2e2' : '#dcfce7', color: confidence === 'Low' ? '#991b1b' : '#166534', fontWeight: 600 }}>
          Confidence: {confidence}
        </span>
      </div>

      <p style={{ fontSize: '0.8rem', color: '#475569', lineHeight: 1.4, marginBottom: '0.5rem' }}>
        <strong>What is OOD?</strong> Out-of-Distribution (OOD) indicates that operating conditions (e.g., speed, temperature, humidity) fall outside the statistical bounds of the dataset used to train the ML model.
      </p>

      {isOod && reasons && reasons.length > 0 && (
        <div style={{ background: '#ffffff', padding: '0.5rem 0.75rem', borderRadius: '6px', border: '1px solid #fecaca', fontSize: '0.75rem', color: '#7f1d1d' }}>
          <strong>OOD Triggers:</strong>
          <ul style={{ paddingLeft: '1.25rem', marginTop: '0.25rem' }}>
            {reasons.map((r, i) => <li key={i}>{r}</li>)}
          </ul>
        </div>
      )}

      <div style={{ fontSize: '0.7rem', color: '#64748b', marginTop: '0.5rem', fontStyle: 'italic' }}>
        * Note: OOD detection lowers prediction confidence due to extrapolation risk, but does not modify the underlying mathematical prediction value.
      </div>
    </div>
  );
}
