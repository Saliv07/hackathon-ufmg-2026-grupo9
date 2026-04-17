import { MessageSquare, Plus, LayoutDashboard, Database, Settings, LogOut, ChevronLeft, ChevronRight } from 'lucide-react';
import './GlobalSidebar.css';

function GlobalSidebar({ cases, currentView, selectedCase, onNavigate, onSelectCase, isCollapsed, onToggle, onOpenSettings }) {
  return (
    <div className={`global-sidebar ${isCollapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-control">
        <button className="toggle-sidebar-btn" onClick={onToggle}>
          {isCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>

      <button className="new-chat-btn" onClick={() => onNavigate('case-selection')}>
        <Plus size={16} />
        {!isCollapsed && <span>Novo Processo</span>}
      </button>

      <div className="sidebar-section">
        {!isCollapsed && <div className="section-title">Histórico Recente</div>}
        <div className="history-list">
          {cases.map((c) => (
            <div
              key={c.id}
              className={`history-item ${currentView === 'workspace' && selectedCase?.id === c.id ? 'active' : ''}`}
              onClick={() => onSelectCase(c)}
              title={isCollapsed ? c.plaintiff : ''}
            >
              <MessageSquare size={18} />
              {!isCollapsed && <span className="truncate">{c.plaintiff}</span>}
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
          <LayoutDashboard size={20} />
          {!isCollapsed && <span>Estatísticas Macro</span>}
        </div>
        <div className="footer-item" title="Base Histórica">
          <Database size={20} />
          {!isCollapsed && <span>Base Histórica</span>}
        </div>
        <div className="footer-item" title="Configurações" onClick={onOpenSettings}>
          <Settings size={20} />
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
