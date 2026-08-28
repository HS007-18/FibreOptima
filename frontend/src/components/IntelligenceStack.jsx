import React from 'react';
import { Cpu, Database, BookOpen, ArrowRight, ShieldCheck } from 'lucide-react';

export default function IntelligenceStack() {
  return (
    <div className="card" style={{ background: '#ffffff', borderColor: '#e2e8f0' }}>
      <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem', color: '#0f172a' }}>
        FibreOptima Intelligence Stack Architecture
      </h3>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
        <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', color: '#2563eb', fontWeight: 600 }}>
            <Cpu size={18} /> ML Intelligence
          </div>
          <div style={{ fontSize: '0.8rem', color: '#475569' }}>
            "What looks unusual?"
          </div>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.5rem' }}>
            Gradient Boosting Waste Predictor + Isolation Forest Anomaly Detection
          </div>
        </div>

        <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', color: '#059669', fontWeight: 600 }}>
            <Database size={18} /> Company Intelligence
          </div>
          <div style={{ fontSize: '0.8rem', color: '#475569' }}>
            "What is normal for this machine?"
          </div>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.5rem' }}>
            Rated limits, historical waste baseline, maintenance logs from CompanyDB
          </div>
        </div>

        <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', color: '#d97706', fontWeight: 600 }}>
            <BookOpen size={18} /> Technical Knowledge
          </div>
          <div style={{ fontSize: '0.8rem', color: '#475569' }}>
            "What does technical evidence suggest?"
          </div>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.5rem' }}>
            Vector RAG search over textile manufacturing handbooks (ChromaDB)
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifySelf: 'center', gap: '1rem', background: '#0f172a', color: '#ffffff', padding: '1rem 1.5rem', borderRadius: '10px' }}>
        <ShieldCheck size={24} color="#3b82f6" />
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>Offline Investigation & Reasoning Engine</div>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Combines all three sources to output deterministic Risk, Root Cause Explanation & Actionable Recommendation</div>
        </div>
      </div>
    </div>
  );
}
