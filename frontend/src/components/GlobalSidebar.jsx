import { MessageSquare, Plus, LayoutDashboard, Database, Settings, LogOut, ChevronLeft, ChevronRight } from 'lucide-react';
import './GlobalSidebar.css';

function GlobalSidebar({ cases, currentView, onNavigate, onSelectCase, isCollapsed, onToggle }) {
  return (
    <div className={`global-sidebar ${isCollapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <div className="sidebar-brand" onClick={() => onNavigate('case-selection')}>
          <img 
            src="https://cdn.prod.website-files.com/67b30e3c33bea6276dc0a7b6/68ffc135ff24aa4cfb5cd0a7_enter_black.svg" 
            alt="Enter.ai Logo" 
            className="sidebar-logo"
            style={{ filter: 'invert(1)' }}
          />
        </div>
        <button className="toggle-sidebar-btn" onClick={onToggle}>
          {isCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      <button className="new-chat-btn" onClick={() => onNavigate('case-selection')}>
        <Plus size={16} />
        {!isCollapsed && <span>Novo Processo</span>}
      </button>

      <div className="sidebar-section">
        <div className="section-title">Histórico Recente</div>
        <div className="history-list">
          {cases.map((c) => (
            <div 
              key={c.id} 
              className={`history-item ${currentView === 'workspace' && c.id === cases.find(curr => curr.id === c.id)?.id ? 'active' : ''}`}
              onClick={() => {
                onSelectCase(c);
              }}
            >
              <MessageSquare size={14} />
              <span className="truncate">{c.plaintiff}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="sidebar-footer">
        <div 
          className={`footer-item ${currentView === 'dashboard' ? 'active' : ''}`}
          onClick={() => onNavigate('dashboard')}
          title="Estatísticas Macro"
        >
          <LayoutDashboard size={18} />
          {!isCollapsed && <span>Estatísticas Macro</span>}
        </div>
        <div className="footer-item" title="Base Histórica">
          <Database size={18} />
          {!isCollapsed && <span>Base Histórica</span>}
        </div>
        <div className="footer-item" title="Configurações">
          <Settings size={18} />
          {!isCollapsed && <span>Configurações</span>}
        </div>
        {!isCollapsed ? (
          <div className="user-info">
            <div className="avatar">AD</div>
            <div className="user-details">
              <div className="user-name">Advogado Silva</div>
              <div className="user-role">Sócio Senior</div>
            </div>
            <LogOut size={16} className="logout-icon" />
          </div>
        ) : (
          <div className="user-info collapsed">
            <div className="avatar">AD</div>
          </div>
        )}
      </div>
    </div>
  );
}

export default GlobalSidebar;
