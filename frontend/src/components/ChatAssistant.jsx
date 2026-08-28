import React, { useState } from 'react';
import axios from 'axios';
import { MessageSquare, X, Send, Bot, User, Sparkles, AlertCircle } from 'lucide-react';

const API_URL = 'http://localhost:8000/api';

export default function ChatAssistant({ activeBatch }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      sender: 'bot',
      text: "Hello! I am your FibreOptima AI Assistant. Ask me about pipeline mechanics (ML, OOD, RAG) or request machine recommendations!",
      source: 'Local System'
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const defaultPrompts = [
    "How does FibreOptima work?",
    "Explain OOD safety bounds",
    "Recommendations for Machine M01",
  ];

  const batchPrompts = activeBatch ? [
    `Recommendations for ${activeBatch.machine_id || 'M01'}`,
    `Why is this batch ${activeBatch.risk_level || 'classified'}?`,
    "How does FibreOptima work?"
  ] : defaultPrompts;

  const handleSend = async (promptText) => {
    const textToSend = promptText || input;
    if (!textToSend.trim() || loading) return;

    const userMsg = { sender: 'user', text: textToSend };
    setMessages(prev => [...prev, userMsg]);
    if (!promptText) setInput('');
    setLoading(true);

    try {
      const res = await axios.post(`${API_URL}/chat`, {
        message: textToSend,
        context: activeBatch || null
      });
      const botMsg = {
        sender: 'bot',
        text: res.data.reply,
        source: res.data.source
      };
      setMessages(prev => [...prev, botMsg]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [
        ...prev,
        { sender: 'bot', text: "Failed to connect to local AI assistant service.", source: "Error" }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const renderCleanText = (text) => {
    if (!text) return null;
    // Replace markdown bolding and headers with clean text presentation
    const lines = text.split('\n');
    return lines.map((line, idx) => {
      let cleanLine = line.replace(/\*\*/g, '').replace(/###\s?/g, '').replace(/#\s?/g, '');
      if (line.startsWith('###') || line.startsWith('#')) {
        return <div key={idx} style={{ fontWeight: 700, fontSize: '0.85rem', color: '#0f172a', marginTop: '0.4rem', marginBottom: '0.2rem' }}>{cleanLine}</div>;
      }
      if (line.startsWith('- ') || line.startsWith('1. ') || line.startsWith('2. ') || line.startsWith('3. ')) {
        return <div key={idx} style={{ paddingLeft: '0.5rem', marginBottom: '0.2rem' }}>• {cleanLine.replace(/^-\s?/, '').replace(/^[0-9]+\.\s?/, '')}</div>;
      }
      return <div key={idx} style={{ marginBottom: line.trim() ? '0.25rem' : '0.4rem' }}>{cleanLine}</div>;
    });
  };

  return (
    <>
      {/* Floating Assistant Trigger Button */}
      {!isOpen && (
        <button
          className="chat-toggle-btn"
          onClick={() => setIsOpen(true)}
        >
          <Bot size={20} color="#ffffff" />
          <span>Ask FibreOptima AI</span>
          {activeBatch && <span style={{ background: '#2563eb', padding: '2px 6px', borderRadius: '4px', fontSize: '0.65rem' }}>Active Context</span>}
        </button>
      )}

      {/* Slide-out Drawer / Chat Modal Panel */}
      {isOpen && (
        <div className="chat-drawer">
          <div className="chat-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <div style={{ background: '#2563eb', padding: '6px', borderRadius: '8px', display: 'flex' }}>
                <Bot size={18} color="#ffffff" />
              </div>
              <div>
                <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#ffffff' }}>FibreOptima Assistant</h3>
                <div style={{ fontSize: '0.7rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                  <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#16a34a' }}></span>
                  {activeBatch ? `Active Batch: ${activeBatch.record_id || activeBatch.machine_id}` : 'Local RAG • Offline Mode'}
                </div>
              </div>
            </div>
            <button className="chat-close-btn" onClick={() => setIsOpen(false)}>
              <X size={18} color="#94a3b8" />
            </button>
          </div>

          {/* Quick Action Chips */}
          <div className="chat-chips-container">
            {batchPrompts.map((qp, idx) => (
              <button
                key={idx}
                className="chat-chip"
                onClick={() => handleSend(qp)}
              >
                <Sparkles size={12} color="#2563eb" /> {qp}
              </button>
            ))}
          </div>

          {/* Message Log */}
          <div className="chat-messages">
            {messages.map((m, idx) => (
              <div key={idx} className={`chat-bubble-wrapper ${m.sender}`}>
                <div className="chat-avatar">
                  {m.sender === 'bot' ? <Bot size={14} color="#ffffff" /> : <User size={14} color="#0f172a" />}
                </div>
                <div className="chat-bubble">
                  {m.source && <div className="chat-source">{m.source}</div>}
                  <div className="chat-text">
                    {renderCleanText(m.text)}
                  </div>
                </div>
              </div>
            ))}
            {loading && (
              <div className="chat-bubble-wrapper bot">
                <div className="chat-avatar"><Bot size={14} color="#ffffff" /></div>
                <div className="chat-bubble" style={{ color: '#64748b', fontSize: '0.8rem' }}>
                  Synthesizing pipeline facts & RAG evidence...
                </div>
              </div>
            )}
          </div>

          {/* Input Bar */}
          <form
            className="chat-input-area"
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
          >
            <input
              type="text"
              placeholder="Ask about pipeline, OOD, or machine M01..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
            />
            <button type="submit" disabled={!input.trim() || loading}>
              <Send size={16} />
            </button>
          </form>
        </div>
      )}
    </>
  );
}
