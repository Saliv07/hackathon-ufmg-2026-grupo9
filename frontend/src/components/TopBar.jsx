import { Bell, User } from 'lucide-react';
import './TopBar.css';

function TopBar({ successChance, currentView, onNavigate }) {
  const getTitle = () => {
    switch(currentView) {
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
              ></div>
            </div>
            <span className="meter-value">{successChance}%</span>
          </div>
        )}
      </div>

      <div className="top-bar-right">
        <button className="nav-icon-btn" title="Notificações">
          <Bell size={18} />
        </button>
        <button className="nav-icon-btn" title="Perfil">
          <User size={18} />
        </button>
      </div>
    </div>
  );
}

export default TopBar;
