import React, { useState, useRef, useEffect } from 'react';
import { Bell, User, Search } from 'lucide-react';
import './TopBar.css';

const ALERTS = [
  { level: 'red', title: '3 casos de alto risco aguardando decisão', sub: 'SLA em <4h' },
  { level: 'yellow', title: 'Advogado externo fora da política em 2 casos', sub: 'Esc. Almeida & Partners' },
  { level: 'green', title: '86 acordos fechados nesta semana', sub: 'R$ 1.2M economizados' },
];

function TopBar({ successChance, currentView, onNavigate, onOpenSearch, hasNewNotification, onClearNotification, onConcluir }) {
  const [showNotifications, setShowNotifications] = useState(false);
  const notifRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (notifRef.current && !notifRef.current.contains(event.target)) {
        setShowNotifications(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleNotificationClick = () => {
    setShowNotifications(!showNotifications);
    if (onClearNotification) onClearNotification();
  };

  const getSubtitle = () => {
    switch (currentView) {
      case 'case-selection': return 'seleção de processos';
      case 'case-summary': return 'resumo estratégico';
      case 'dashboard': return 'painel de inteligência';
      case 'workspace': return 'área de trabalho';
      case 'case-conclusion': return 'conclusão de caso';
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
          <div className="top-bar-center-actions">
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
            <button className="topbar-concluir-btn" onClick={onConcluir}>
              Concluir Processo
            </button>
          </div>
        )}
      </div>

      <div className="top-bar-right">
        <button className="nav-icon-btn" title="Buscar" onClick={onOpenSearch}><Search size={16} /></button>
        
        <div className="notification-wrapper" ref={notifRef}>
          <button
            className="nav-icon-btn notification-btn"
            title="Notificações"
            onClick={handleNotificationClick}
          >
            <Bell size={16} />
            {hasNewNotification && <span className="notification-dot" />}
          </button>

          {showNotifications && (
            <div className="notifications-dropdown">
              <div className="notifications-header">
                <Bell size={14} />
                <span>Alertas operacionais</span>
              </div>
              <div className="notifications-body">
                {ALERTS.map((a, i) => (
                  <div className="notif-item" key={i}>
                    <span className={`notif-dot ${a.level}`} />
                    <div className="notif-content">
                      <div className="notif-title">{a.title}</div>
                      <div className="notif-sub">{a.sub}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <button className="nav-icon-btn" title="Perfil"><User size={16} /></button>
      </div>
    </div>
  );
}

export default TopBar;
