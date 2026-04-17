import React from 'react';
import './CaseSelection.css';

function CaseSelection({ onSelectCase, cases }) {
  if (!cases || cases.length === 0) {
    return (
      <div className="case-selection-container">
        <div className="selection-header">
          <h1>Nenhum processo encontrado</h1>
          <p>Verifique se o backend Python está rodando na porta 5000.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="case-selection-container">
      <div className="selection-header">
        <h1>Selecione um Processo para Adjudicação</h1>
        <p>A IA analisou os novos casos e classificou por nível de risco e probabilidade de êxito.</p>
      </div>
      
      <div className="cases-grid">
        {cases.map((caseItem) => (
          <div 
            key={caseItem.id} 
            className={`case-card ${caseItem.risk === 'Alto' ? 'high-risk' : 'low-risk'}`}
            onClick={() => onSelectCase(caseItem)}
          >
            <div className="card-top">
              <span className="case-number">{caseItem.number}</span>
              <span className={`risk-badge ${caseItem.risk.toLowerCase()}`}>
                Risco {caseItem.risk}
              </span>
            </div>
            <h2 className="plaintiff-name">{caseItem.plaintiff}</h2>
            <div className="case-info">
              <span className="info-label">Tipo:</span>
              <span className="info-value">{caseItem.type}</span>
            </div>
            <div className="case-info">
              <span className="info-label">Valor da Causa:</span>
              <span className="info-value">{caseItem.value}</span>
            </div>
            <div className="card-footer">
              <span className="recommendation">Sugestão: <strong>{caseItem.recommendation}</strong></span>
              <button className="analyze-btn">Abrir Caso</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default CaseSelection;
