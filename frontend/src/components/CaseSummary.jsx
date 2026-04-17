import React from 'react';
import { Bot, ArrowRight } from 'lucide-react';
import './CaseSummary.css';

function CaseSummary({ caseData, onProceed }) {
  if (!caseData) return null;

  return (
    <div className="case-summary-container slide-in">
      <div className="summary-content">
        <div className="ai-header">
          <Bot size={32} className="ai-icon" />
          <h2>Análise do Agente IA</h2>
        </div>
        
        <div className="summary-card">
          <h3>Resumo do Caso: {caseData.plaintiff}</h3>
          <span className="case-num">{caseData.number}</span>
          
          <div className="summary-section">
            <p>
              {caseData.summary}
            </p>
          </div>
          
          <div className="ai-suggestion">
            <div className="suggestion-header">
              <Bot size={20} />
              <h4>Indicação de Solução</h4>
            </div>
            <p className="recommendation">
              <strong>Recomendação: {caseData.recommendation}</strong>
            </p>
            <p>
              {caseData.suggestion}
            </p>
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
