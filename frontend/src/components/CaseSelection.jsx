import React, { useState } from 'react';
import { ArrowRight, Filter, TrendingUp } from 'lucide-react';
import './CaseSelection.css';

function CaseSelection({ onSelectCase, cases }) {
  const [filter, setFilter] = useState('todos');

  if (!cases || cases.length === 0) {
    return (
      <div className="home-view">
        <div className="home-header">
          <div className="home-header-text">
            <h1>Nenhum processo encontrado</h1>
            <p>Verifique se o backend Python está rodando na porta 5001.</p>
          </div>
        </div>
      </div>
    );
  }

  const filtered = filter === 'todos'
    ? cases
    : cases.filter(c => c.recommendation.toLowerCase() === filter);

  return (
    <div className="home-view fade-in">
      <div className="home-header">
        <div className="home-header-text">
          <div className="breadcrumb">
            <span>enterOS</span><span>workspace</span><span>home</span>
          </div>
          <h1>Boa tarde, Silva.</h1>
          <p>{cases.length} processos aguardando triagem · política v2.1 ativa · modelo gpt-4o</p>
        </div>
        <div className="home-header-actions">
          <button className="filter-pill"><Filter size={12} /> filtros</button>
          <button className="filter-pill active"><TrendingUp size={12} /> esta semana</button>
        </div>
      </div>

      {/* Macro strip */}
      <div className="macro-strip">
        <div className="macro-cell">
          <span className="label">Novos processos (mês)</span>
          <span className="value">{cases.length}</span>
          <span className="sub"><span className="trend up">▲</span> ativos na fila</span>
        </div>
        <div className="macro-cell">
          <span className="label">Taxa de êxito</span>
          <span className="value">69.6%</span>
          <span className="sub"><span className="trend up">▲</span> 41.733 / 60.000</span>
        </div>
        <div className="macro-cell">
          <span className="label">Adesão à política</span>
          <span className="value accent">87%</span>
          <span className="sub"><span className="trend up">▲</span> +3.2pp</span>
        </div>
        <div className="macro-cell">
          <span className="label">Ticket médio condenação</span>
          <span className="value">R$ 9.340</span>
          <span className="sub"><span className="trend down">▼</span> −18% vs baseline</span>
        </div>
      </div>

      {/* Filter + Table */}
      <div className="section-head">
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 14 }}>
          <h2>Fila de processos</h2>
          <span className="count">{filtered.length} casos · ordenado por risco</span>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className={`filter-pill ${filter === 'todos' ? 'active' : ''}`} onClick={() => setFilter('todos')}>todos</button>
          <button className={`filter-pill ${filter === 'defesa' ? 'active' : ''}`} onClick={() => setFilter('defesa')}>defesa</button>
          <button className={`filter-pill ${filter === 'acordo' ? 'active' : ''}`} onClick={() => setFilter('acordo')}>acordo</button>
        </div>
      </div>

      <div className="case-table">
        <div className="case-row header">
          <span>Parte autora / nº processo</span>
          <span>Valor</span>
          <span>Risco</span>
          <span>Recomendação</span>
          <span></span>
        </div>
        {filtered.map(c => (
          <div className="case-row" key={c.id} onClick={() => onSelectCase(c)}>
            <div className="case-primary">
              <span className="case-plaintiff">{c.plaintiff}</span>
              <span className="case-number">{c.number}</span>
            </div>
            <span className="case-value">{c.value}</span>
            <span className={`risk-badge ${c.risk?.toLowerCase() === 'médio' ? 'medio' : c.risk?.toLowerCase()}`}>
              {c.risk}
            </span>
            <span className={`reco-pill ${c.recommendation?.toLowerCase()}`}>
              {c.recommendation}
            </span>
            <button className="open-case-btn">
              Abrir <ArrowRight size={11} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default CaseSelection;
