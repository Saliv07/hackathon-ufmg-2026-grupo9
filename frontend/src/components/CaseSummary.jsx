import React from 'react';
import { Bot, ArrowRight, ShieldCheck, AlertTriangle, FileCheck, Info, User, CheckCircle2, XCircle } from 'lucide-react';
import './CaseSummary.css';

function CaseSummary({ caseData, onProceed }) {
  if (!caseData) return null;

  // Mocked data for the new structured overview if not provided by backend
  const score = caseData?.score || 85;
  const authorProfile = caseData?.profile || { 
    age: 65, 
    profession: 'Aposentado', 
    literacy: 'Lê e Escreve',
    priority: 'Idoso',
    income: 'R$ 1.412,00',
    location: 'Belo Horizonte - MG'
  };
  
  const evidence = caseData?.evidence || [
    { id: 'contract', label: 'Contrato Assinado', status: 'valid', detail: 'Biometria Facial' },
    { id: 'id', label: 'Documento de Identidade', status: 'valid', detail: 'Compatível' },
    { id: 'ted', label: 'Comprovante TED', status: 'valid', detail: 'Mesma Titularidade' },
    { id: 'usage', label: 'Utilização do Crédito', status: 'invalid', detail: 'Valor não movimentado' }
  ];

  const redFlags = caseData?.redFlags || [
    { id: 1, type: 'warning', message: 'Autor Idoso (>60 anos) - Atenção à vulnerabilidade' },
    { id: 2, type: 'danger', message: 'Alto volume de ações idênticas deste advogado (Litigância Predatória)' }
  ];

  const thesis = caseData?.thesis || 'Exercício regular de direito - Contratação validada por biometria';

  return (
    <div className="case-summary-container slide-in">
      <div className="summary-content structured-summary">
        <div className="ai-header">
          <Bot size={32} className="ai-icon" />
          <div className="header-titles">
            <h2>Análise Estratégica IA</h2>
            <span className="case-num">{caseData.number} • {caseData.plaintiff}</span>
          </div>
        </div>
        
        <div className="dashboard-grid">
          {/* KPI Card */}
          <div className="dashboard-card kpi-card">
            <div className="score-section">
              <div className="card-header">
                <ShieldCheck size={18} />
                <h3>Score de Defesa</h3>
              </div>
              <div className="score-display">
                <div className="score-circle">
                  <span className="score-value">{score}%</span>
                </div>
                <p className="score-desc">Alta Probabilidade</p>
              </div>
            </div>
            
            <div className="profile-info">
              <div className="card-header">
                <User size={14} /> <h3>Perfil do Autor</h3>
              </div>
              <ul className="profile-list">
                <li><strong>Idade:</strong> <span>{authorProfile.age} anos ({authorProfile.priority})</span></li>
                <li><strong>Localização:</strong> <span>{authorProfile.location}</span></li>
                <li><strong>Renda Est.:</strong> <span>{authorProfile.income}</span></li>
                <li><strong>Ocupação:</strong> <span>{authorProfile.profession}</span></li>
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
              {evidence.map(item => (
                <div key={item.id} className={`evidence-item ${item.status}`}>
                  <div className="evidence-details">
                    <span className="evidence-label">{item.label}</span>
                    <span className="evidence-subtext">{item.detail}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Bottom Grid: Alerts & Recommendation */}
        <div className="bottom-dashboard-grid">
          {/* Red Flags */}
          <div className="alerts-section">
            <div className="card-header">
              <AlertTriangle size={18} className="danger-icon" />
              <h3>Alertas e Red Flags</h3>
            </div>
            <div className="flags-list">
              {redFlags.map(flag => (
                <div key={flag.id} className={`flag-item ${flag.type}`}>
                  <Info size={16} />
                  <span>{flag.message}</span>
                </div>
              ))}
            </div>
          </div>
          
          {/* Recommendation */}
          <div className="ai-suggestion structured-suggestion">
            <div className="suggestion-header">
              <Bot size={20} />
              <h4>Indicação de Solução</h4>
            </div>
            <div className="recommendation-content">
              <div className="thesis-box">
                <strong>Tese Recomendada</strong>
                <p>{thesis}</p>
              </div>
              <div className="suggestion-details">
                <p><strong>Ação: {caseData.recommendation}</strong></p>
                <p>{caseData.suggestion}</p>
              </div>
            </div>
          </div>
        </div>

        <button className="proceed-button" onClick={onProceed}>
          Abrir Área de Trabalho <ArrowRight size={20} />
        </button>
      </div>
    </div>
  );
}

export default CaseSummary;
