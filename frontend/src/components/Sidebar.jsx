import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Cpu, PlayCircle, Layers, BookOpen, Activity } from 'lucide-react';

export default function Sidebar() {
  const navItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/machines', label: 'Machines', icon: Cpu },
    { path: '/bulk-analysis', label: 'Bulk Analysis', icon: Layers },
    { path: '/knowledge', label: 'Knowledge & Evidence', icon: BookOpen },
    { path: '/status', label: 'System Status', icon: Activity },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <Activity color="#3b82f6" size={24} />
        <div>
          <h1>FibreOptima</h1>
          <span>Enterprise V3</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
              end={item.path === '/'}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      <div style={{ marginTop: 'auto', padding: '0.75rem', background: 'rgba(255,255,255,0.05)', borderRadius: '6px', fontSize: '0.75rem', color: '#94a3b8' }}>
        <div style={{ fontWeight: 600, color: '#fff', marginBottom: '2px' }}>FibreOptima Pipeline</div>
        <div>Offline ML + CompanyDB + RAG</div>
      </div>
    </aside>
  );
}
