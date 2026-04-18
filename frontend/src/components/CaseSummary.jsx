import React from 'react';
import { Bot, ArrowRight, ShieldCheck, AlertTriangle, FileCheck, Info, User, CheckCircle2, XCircle } from 'lucide-react';
import './CaseSummary.css';

function CaseSummary({ caseData, onProceed }) {
  if (!caseData) return null;

  // Extracts structured data from caseData provided by backend
  const score = caseData?.score || 0;
  const askedValue = caseData?.askedValue || 0;
  const claimDetails = caseData?.claimDetails || 'Valor do pedido não identificado.';
  const authorProfile = caseData?.profile || { 
    gender: '-',
    age: '-', 
    civilStatus: '-',
    benefitType: '-',
    profession: '-', 
    literacy: '-',
    priority: '-',
    income: '-',
    location: '-'
  };
  
  const evidence = caseData?.evidence || [];
  const redFlags = caseData?.redFlags || [];
  const thesis = caseData?.thesis || 'Análise de tese pendente...';

  return (
    <div className="case-summary-container slide-in">
      <div className="summary-content structured-summary">
        <div className="ai-header">
          <div className="ai-header-left">
            <Bot size={32} className="ai-icon" />
            <div className="header-titles">
              <h2>Análise Estratégica IA</h2>
              <span className="case-num">{caseData.number} • {caseData.plaintiff}</span>
            </div>
          </div>

        </div>
        
        <div className="dashboard-grid">
          {/* Score Card */}
          <div className="dashboard-card score-card">
            <div className="score-section">
              <div className="card-header">
                <ShieldCheck size={18} />
                <h3>Análise de Risco</h3>
              </div>
              <div className="score-display">
                <div className="score-circle">
                  <span className="score-value">{score}%</span>
                </div>
                <div className="score-details">
                  <p className="score-desc">Score de Defesa</p>
                  <div className="claim-box">
                    <span className="claim-label">Pedido Total</span>
                    <span className="claim-value">R$ {askedValue.toLocaleString('pt-BR')}</span>
                  </div>
                </div>
              </div>
              <div className="claim-breakdown">
                <small>{claimDetails}</small>
              </div>
            </div>
          </div>
            
          {/* Profile Card */}
          <div className="dashboard-card profile-card">
            <div className="profile-info">
              <div className="card-header">
                <User size={14} /> <h3>Perfil do Autor</h3>
              </div>
              <ul className="profile-list">
                <li><strong>Pessoa no Contrato:</strong> <span style={{ color: 'var(--primary-light)' }}>{caseData.plaintiff}</span></li>
                <li><strong>Gênero/Idade:</strong> <span>{authorProfile.gender}, {authorProfile.age} anos</span></li>
                <li><strong>Estado Civil:</strong> <span>{authorProfile.civilStatus}</span></li>
                <li><strong>Localização:</strong> <span>{authorProfile.location}</span></li>
                <li><strong>Renda Est.:</strong> <span>{authorProfile.income}</span></li>
                <li><strong>Tipo Benefício:</strong> <span>{authorProfile.benefitType}</span></li>
                <li><strong>Instrução:</strong> <span>{authorProfile.literacy}</span></li>
              </ul>
            </div>
          </div>

          {/* Evidence Checklist */}
          <div className="dashboard-card evidence-card">
            <div className="card-header">
              <FileCheck size={18} />
              <h3>Checklist Probatório</h3>
            </div>
            <div className="evidence-list">
              {evidence.length > 0 ? (
                evidence.map((item) => (
                  <div key={item.id} className={`evidence-item ${item.status}`}>
                    <div className="evidence-details">
                      <span className="evidence-label">{item.label}</span>
                      <span className="evidence-subtext">{item.detail}</span>
                    </div>
                  </div>
                ))
              ) : (
                <p className="empty-state">Nenhuma evidência estruturada disponível.</p>
              )}
            </div>
          </div>
        </div>

        {/* Bottom Grid: Alerts & Recommendation */}
        <div className="bottom-dashboard-grid">
          {/* Red Flags */}
          <div className="dashboard-card alerts-section">
            <div className="card-header">
              <AlertTriangle size={18} className="danger-icon" />
              <h3>Alertas e Red Flags</h3>
            </div>
            <div className="flags-list">
              {redFlags.length > 0 ? (
                redFlags.map(flag => (
                  <div key={flag.id} className={`flag-item ${flag.type}`}>
                    <Info size={16} />
                    <span>{flag.message}</span>
                  </div>
                ))
              ) : (
                <p className="empty-state">Nenhum alerta crítico detectado.</p>
              )}
            </div>
          </div>
          
          {/* Recommendation */}
          <div className="structured-suggestion">
            <div className="suggestion-header">
              <Bot size={20} />
              <h4>Indicação de Solução</h4>
            </div>
            <div className="recommendation-content">
              <div className="recommendation-text-area">
                <div className="thesis-box">
                  <strong>Tese Recomendada</strong>
                  <p>{thesis}</p>
                </div>
                <div className="suggestion-details">
                  <p><strong>Ação: {caseData.recommendation}</strong></p>
                  <p>{caseData.suggestion}</p>
                </div>
              </div>
              <div className="recommendation-action-area">
                <button className="proceed-button-massive" onClick={onProceed}>
                  <span>Área de Trabalho</span>
                  <ArrowRight size={24} />
                </button>
              </div>
            </div>
          </div>
        </div>


      </div>
    </div>
  );
}

export default CaseSummary;
