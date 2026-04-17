import { Bell, User } from 'lucide-react';
import './TopBar.css';

function TopBar({ successChance, currentView, onNavigate, hasNewNotification, onClearNotification }) {
  const getTitle = () => {
    switch (currentView) {
      case 'case-selection': return 'Seleção de Processos';
      case 'case-summary': return 'Resumo Estratégico';
      case 'dashboard': return 'Painel de Inteligência';
      case 'workspace': return 'Área de Trabalho IA';
      default: return 'Plataforma Jurídica';
    }
  };

  return (
    <div className="top-bar">
      <div className="top-bar-left">
        <div className="brand-fixed" onClick={() => onNavigate('case-selection')}>
          <img
            src="https://cdn.prod.website-files.com/67b30e3c33bea6276dc0a7b6/68ffc135ff24aa4cfb5cd0a7_enter_black.svg"
            alt="Enter.ai Logo"
            className="fixed-logo"
          />
        </div>
        <div className="top-bar-divider" />
        <span className="view-title">{getTitle()}</span>
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
        <button
          className="nav-icon-btn notification-btn"
          title="Notificações"
          onClick={onClearNotification}
        >
          <Bell size={18} />
          {hasNewNotification && <span className="notification-dot" />}
        </button>
        <button className="nav-icon-btn" title="Perfil">
          <User size={18} />
        </button>
      </div>
    </div>
  );
}

export default TopBar;
