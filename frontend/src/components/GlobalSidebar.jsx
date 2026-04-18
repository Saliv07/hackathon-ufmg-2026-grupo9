import { useState } from 'react';
import { Plus, LayoutDashboard, Database, Settings, LogOut, ChevronLeft, ChevronRight, Shield, X } from 'lucide-react';
import './GlobalSidebar.css';

function PolicyModal({ onClose }) {
  return (
    <div className="policy-modal-overlay" onClick={onClose}>
      <div className="policy-modal" onClick={e => e.stopPropagation()}>
        <div className="policy-modal-header">
          <div className="policy-modal-title">
            <Shield size={18} />
            Política de Acordo · Enter AI · v2.1
          </div>
          <button className="policy-modal-close" onClick={onClose}><X size={18} /></button>
        </div>

        <div className="policy-modal-body">

          <section className="policy-section">
            <h2>1. Objetivo</h2>
            <p>
              Estabelecer critérios objetivos e auditáveis para decisão entre <strong>defesa judicial</strong> e{' '}
              <strong>proposta de acordo</strong> em ações declaratórias de inexistência de débito envolvendo
              empréstimos consignados, garantindo consistência entre escritórios e maximizando a eficiência
              financeira do contencioso.
            </p>
          </section>

          <section className="policy-section">
            <h2>2. Escopo</h2>
            <p>
              Aplica-se exclusivamente a ações cíveis em que a parte autora alega não reconhecer a contratação
              de empréstimo consignado junto ao Banco UFMG.
            </p>
          </section>

          <section className="policy-section">
            <h2>3. Critérios de Decisão</h2>

            <h3>3.1 Classificação dos Subsídios</h3>
            <div className="policy-subsidy-grid">
              <div className="policy-subsidy-card critical">
                <div className="subsidy-badge">CRÍTICOS</div>
                <div className="subsidy-desc">Alto poder probatório</div>
                <ul>
                  <li>Contrato (cédula de crédito bancário)</li>
                  <li>Extrato bancário comprovando o crédito</li>
                  <li>Comprovante de Crédito BACEN</li>
                </ul>
              </div>
              <div className="policy-subsidy-card complementary">
                <div className="subsidy-badge">COMPLEMENTARES</div>
                <div className="subsidy-desc">Reforço probatório</div>
                <ul>
                  <li>Dossiê grafotécnico/documental</li>
                  <li>Demonstrativo de Evolução da Dívida</li>
                  <li>Laudo Referenciado</li>
                </ul>
              </div>
            </div>

            <h3>3.2 Análise do Dossiê</h3>
            <div className="policy-dossie-grid">
              <div className="dossie-tag conforme">CONFORME — Reforça a defesa</div>
              <div className="dossie-tag nao-conforme">NÃO CONFORME — Acordo imediato (prioritário)</div>
              <div className="dossie-tag ausente">AUSENTE / INCOMPLETO — Tratado como neutro</div>
            </div>

            <h3>3.3 Matriz de Recomendação</h3>
            <table className="policy-table">
              <thead>
                <tr><th>Cenário</th><th>Recomendação</th></tr>
              </thead>
              <tbody>
                <tr>
                  <td>Dossiê NÃO CONFORME</td>
                  <td><span className="rec-badge acordo">ACORDO</span> (prioritário)</td>
                </tr>
                <tr>
                  <td>0–1 subsídios críticos presentes</td>
                  <td><span className="rec-badge acordo">ACORDO</span></td>
                </tr>
                <tr>
                  <td>2 subsídios críticos + Dossiê CONFORME ou ausente</td>
                  <td><span className="rec-badge avaliar">AVALIAR</span> (modelo ML)</td>
                </tr>
                <tr>
                  <td>3 subsídios críticos presentes</td>
                  <td><span className="rec-badge defesa">DEFESA</span></td>
                </tr>
                <tr>
                  <td>UF de alto risco (AM, AP) com ≤ 2 subsídios críticos</td>
                  <td><span className="rec-badge acordo">ACORDO</span></td>
                </tr>
              </tbody>
            </table>
          </section>

          <section className="policy-section">
            <h2>4. Cálculo do Valor do Acordo</h2>

            <h3>4.1 Fórmula Base</h3>
            <div className="policy-formula">
              <span className="formula-text">Valor alvo do acordo</span>
              <span className="formula-eq">=</span>
              <span className="formula-text">Valor da Causa</span>
              <span className="formula-op">×</span>
              <span className="formula-factor">30%</span>
            </div>
            <p className="policy-note">
              Prática consolidada dos acordos históricos do banco (R² = 0,67 contra base de 280 acordos),
              validada por correlação de 0,82 com o valor da causa.
            </p>

            <h3>4.2 Ajustes por Perfil</h3>
            <table className="policy-table">
              <thead>
                <tr><th>Cenário</th><th>Ajuste no fator</th></tr>
              </thead>
              <tbody>
                <tr>
                  <td>3 subsídios críticos (banco forte)</td>
                  <td><span className="adj-badge neg">–3 pp (27%)</span></td>
                </tr>
                <tr>
                  <td>0–1 subsídio crítico (banco fraco)</td>
                  <td><span className="adj-badge pos">+3 pp (33%)</span></td>
                </tr>
                <tr>
                  <td>Dossiê NÃO CONFORME</td>
                  <td><span className="adj-badge pos">+5 pp (35%)</span></td>
                </tr>
                <tr>
                  <td>UF de alto risco (AM, AP)</td>
                  <td><span className="adj-badge pos">+2 pp</span></td>
                </tr>
                <tr>
                  <td>UF de baixo risco (MA, PI, TO…)</td>
                  <td><span className="adj-badge neg">–2 pp</span></td>
                </tr>
              </tbody>
            </table>

            <h3>4.3 Faixa de Negociação</h3>
            <div className="policy-negotiation">
              <div className="neg-row p25">
                <span className="neg-label">Abertura (P25)</span>
                <div className="neg-bar" style={{ width: '55%' }} />
                <span className="neg-pct">24 – 26%</span>
              </div>
              <div className="neg-row p50">
                <span className="neg-label">Alvo (P50)</span>
                <div className="neg-bar" style={{ width: '70%' }} />
                <span className="neg-pct">28 – 30%</span>
              </div>
              <div className="neg-row p75">
                <span className="neg-label">Máximo (P75)</span>
                <div className="neg-bar" style={{ width: '85%' }} />
                <span className="neg-pct">35%</span>
              </div>
              <div className="neg-row p90">
                <span className="neg-label">Teto absoluto (P90)</span>
                <div className="neg-bar" style={{ width: '100%' }} />
                <span className="neg-pct">40%</span>
              </div>
            </div>
          </section>

        </div>
      </div>
    </div>
  );
}

function GlobalSidebar({ cases, currentView, selectedCase, onNavigate, onSelectCase, isCollapsed, onToggle, onOpenSettings, onLogout }) {
  const [showPolicy, setShowPolicy] = useState(false);

  const getRiskClass = (risk) => {
    if (!risk) return '';
    const r = risk.toLowerCase();
    if (r === 'alto') return 'alto';
    if (r === 'baixo') return 'baixo';
    return 'alto';
  };

  return (
    <>
      <div className={`global-sidebar ${isCollapsed ? 'collapsed' : ''}`}>
        <div className="sidebar-control">
          <button className="toggle-sidebar-btn" onClick={onToggle}>
            {isCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
          </button>
        </div>

        <button className="new-case-btn" onClick={() => onNavigate('case-selection')}>
          <Plus size={14} />
          {!isCollapsed && <span>Novo processo</span>}
        </button>

        <div className="sidebar-section">
          {!isCollapsed && <div className="section-title">Histórico recente</div>}
          <div className="history-list">
            {cases.map((c) => (
              <div
                key={c.id}
                className={`history-item ${currentView === 'workspace' && selectedCase?.id === c.id ? 'active' : ''}`}
                onClick={() => onSelectCase(c)}
                title={isCollapsed ? c.plaintiff : ''}
              >
                <span className={`risk-dot ${getRiskClass(c.risk)}`} />
                {!isCollapsed && <span className="truncate">{c.plaintiff}</span>}
              </div>
            ))}
          </div>
        </div>

        <div className="sidebar-footer">
          <div
            className={`footer-item ${currentView === 'dashboard' ? 'active' : ''}`}
            onClick={() => onNavigate('dashboard')}
            title="Dashboard macro"
          >
            <LayoutDashboard size={16} />
            {!isCollapsed && <span>Dashboard macro</span>}
          </div>
          <div
            className={`footer-item ${currentView === 'data-explorer' ? 'active' : ''}`}
            title="Base histórica"
            onClick={() => onNavigate('data-explorer')}
          >
            <Database size={16} />
            {!isCollapsed && <span>Base histórica</span>}
          </div>
          <div
            className="footer-item policy-item"
            title="Política de acordos"
            onClick={() => setShowPolicy(true)}
          >
            <Shield size={16} />
            {!isCollapsed && <span>Política de acordos</span>}
          </div>
          <div className="footer-item" title="Configurações" onClick={onOpenSettings}>
            <Settings size={16} />
            {!isCollapsed && <span>Configurações</span>}
          </div>

          {!isCollapsed ? (
            <div className="user-info">
              <div className="user-avatar">AS</div>
              <div className="user-details">
                <div className="user-name">Advogado Silva</div>
                <div className="user-role">sócio · OAB 98.321</div>
              </div>
              <LogOut size={14} className="logout-icon" onClick={onLogout} title="Sair" />
            </div>
          ) : (
            <div className="user-info collapsed">
              <div className="user-avatar">AS</div>
            </div>
          )}
        </div>
      </div>

      {showPolicy && <PolicyModal onClose={() => setShowPolicy(false)} />}
    </>
  );
}

export default GlobalSidebar;
