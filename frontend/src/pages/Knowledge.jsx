import React from 'react';
import IntelligenceStack from '../components/IntelligenceStack';
import RAGExplanation from '../components/RAGExplanation';
import { BookOpen, Layers, ShieldCheck } from 'lucide-react';

export default function Knowledge() {
  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Knowledge & Technical Evidence Pipeline</h2>
        <p style={{ fontSize: '0.85rem', color: '#64748b' }}>Technical documentation explaining how statistical ML, SQL company facts, and Vector RAG combine</p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        <IntelligenceStack />
        <RAGExplanation />

        <div className="card">
          <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.75rem', color: '#0f172a' }}>
            Domain Knowledge Base Indexing Details
          </h3>
          <p style={{ fontSize: '0.85rem', color: '#475569', lineHeight: 1.6 }}>
            FibreOptima uses a localized <strong>ChromaDB</strong> vector database loaded with textile manufacturing trouble-shooting manuals, fabric defect catalogs, and machine maintenance guidelines. 
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginTop: '1rem' }}>
            <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
              <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>Embedding Engine</div>
              <div style={{ fontSize: '0.8rem', color: '#64748b' }}>HuggingFace `all-MiniLM-L6-v2` (Local inference)</div>
            </div>
            <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
              <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>Vector Database</div>
              <div style={{ fontSize: '0.8rem', color: '#64748b' }}>ChromaDB Persistent Store</div>
            </div>
            <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
              <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>Query Matching</div>
              <div style={{ fontSize: '0.8rem', color: '#64748b' }}>Cosine Similarity (Top K=3 documents)</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
