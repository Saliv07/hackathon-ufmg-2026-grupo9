import { Bell, User, Search } from 'lucide-react';
import './TopBar.css';

function TopBar({ successChance, currentView, onNavigate, onOpenSearch, hasNewNotification, onClearNotification }) {
  const getSubtitle = () => {
    switch (currentView) {
      case 'case-selection': return 'seleção de processos';
      case 'case-summary': return 'resumo estratégico';
      case 'dashboard': return 'painel de inteligência';
      case 'workspace': return 'área de trabalho';
      default: return 'plataforma jurídica';
    }
  };

  return (
    <div className="top-bar">
      <div className="top-bar-left">
        <div className="brand-fixed" onClick={() => onNavigate('case-selection')}>
          <img src="/enter-logo.svg" alt="Enter" className="brand-icon" />
          <div className="brand-logo">ENTER<span className="caret" /></div>
          <div className="brand-logo-sub">OS</div>
        </div>
        <span className="view-title"><strong>Home</strong> · {getSubtitle()}</span>
      </div>

      <div className="top-bar-center">
        {currentView === 'workspace' && (
          <div className="success-meter">
            <span className="meter-label">Probabilidade de Êxito:</span>
            <div className="meter-bg">
              <div
                className={`meter-fill ${successChance > 70 ? 'high' : successChance > 40 ? 'medium' : 'low'}`}
                style={{ width: `${successChance}%` }}
              />
            </div>
            <span className="meter-value">{successChance}%</span>
          </div>
        )}
      </div>

      <div className="top-bar-right">
        <button className="nav-icon-btn" title="Buscar" onClick={onOpenSearch}><Search size={16} /></button>
        <button
          className="nav-icon-btn notification-btn"
          title="Notificações"
          onClick={onClearNotification}
        >
          <Bell size={16} />
          {hasNewNotification && <span className="notification-dot" />}
        </button>
        <button className="nav-icon-btn" title="Perfil"><User size={16} /></button>
      </div>
    </div>
  );
}

export default TopBar;
