import React from 'react';
import { ArrowRight, FileText, Search, Database, Layers, CheckCircle2 } from 'lucide-react';

export default function RAGExplanation() {
  const steps = [
    { title: 'Machine Signal', desc: 'Anomaly / Waste outlier detected', icon: FileText },
    { title: 'Investigation Query', desc: 'Constructed search query', icon: Search },
    { title: 'Local Embeddings', desc: 'HuggingFace all-MiniLM-L6-v2', icon: Layers },
    { title: 'Chroma Vector DB', desc: 'Top-K semantic similarity search', icon: Database },
    { title: 'Technical Evidence', desc: 'Extracted domain knowledge & fixes', icon: CheckCircle2 },
  ];

  return (
    <div className="card" style={{ background: '#ffffff' }}>
      <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1.25rem', color: '#0f172a' }}>
        Retrieval-Augmented Generation (RAG) Architecture
      </h3>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem', overflowX: 'auto', padding: '0.5rem 0' }}>
        {steps.map((step, idx) => {
          const Icon = step.icon;
          return (
            <React.Fragment key={idx}>
              <div style={{ flex: 1, minWidth: '130px', background: '#f8fafc', padding: '0.85rem', borderRadius: '8px', border: '1px solid #e2e8f0', textAlign: 'center' }}>
                <Icon size={20} color="#2563eb" style={{ margin: '0 auto 0.35rem auto' }} />
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#0f172a' }}>{step.title}</div>
                <div style={{ fontSize: '0.65rem', color: '#64748b', marginTop: '0.2rem' }}>{step.desc}</div>
              </div>
              {idx < steps.length - 1 && <ArrowRight size={16} color="#94a3b8" style={{ flexShrink: 0 }} />}
            </React.Fragment>
          );
        })}
      </div>

      <div style={{ marginTop: '1rem', padding: '0.75rem 1rem', background: '#eff6ff', borderRadius: '6px', fontSize: '0.8rem', color: '#1e40af', border: '1px solid #bfdbfe' }}>
        <strong>Scope Notice:</strong> RAG retrieves domain knowledge from indexed textile manufacturing manuals. Machine profiles and historical performance baselines originate strictly from <strong>CompanyDB</strong>.
      </div>
    </div>
  );
}
