import React, { useState, useEffect } from 'react';
import './Dashboard.css';

function Dashboard({ caseData }) {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetch('http://localhost:5000/api/stats')
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(err => console.error("Erro ao buscar estatísticas:", err));
  }, []);

  if (!caseData) return <div className="no-case">Selecione um caso para ver a análise estratégica.</div>;
  if (!stats) return <div className="loading-stats">Carregando estatísticas do servidor Python...</div>;

  const askedValue = caseData.askedValue || 0;
  const isDefesa = caseData.recommendation === 'DEFESA';
  
  const negotiationValue = isDefesa ? 0 : askedValue * 0.28; 
  const legalCosts = askedValue * 0.15 + 2000;
  const riskValue = askedValue + legalCosts;

  return (
    <div className="dashboard-container slide-in-right">
      <div className="dashboard-header">
        <h2>Dashboard Estratégico - Análise de Viabilidade</h2>
        <p>Processo: {caseData.number} | {caseData.plaintiff}</p>
      </div>

      <div className="dashboard-grid">
        {/* Painel de Valores */}
        <div className="dashboard-card">
          <div className="card-header">
            <h3>Comparativo de Cenários</h3>
          </div>
          <div className="card-body">
            <div className="kpi-group">
              <div className="kpi">
                <div className="kpi-value highlight-danger">
                  {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(askedValue)}
                </div>
                <div className="kpi-label">Valor do Pedido (Risco)</div>
              </div>
              <div className="kpi">
                <div className="kpi-value highlight-success">
                  {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(negotiationValue)}
                </div>
                <div className="kpi-label">{isDefesa ? 'Valor Sugerido para Acordo' : 'Teto de Negociação Sugerido'}</div>
              </div>
            </div>
            
            <div className="chart-placeholder">
              <div className="chart-bar" style={{width: '100%', background: 'var(--danger-color)'}}></div>
              <div className="chart-bar" style={{width: isDefesa ? '0%' : '30%', background: 'var(--success-color)'}}></div>
            </div>
            
            <div className="stats-list">
              <h4>{isDefesa ? 'Análise de Risco' : 'Por que fazer o acordo?'}</h4>
              <ul>
                <li>Custas processuais estimadas: {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(legalCosts)}</li>
                <li>Risco total em caso de perda: {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(riskValue)}</li>
                <li className="highlight-success">
                  <strong>
                    {isDefesa 
                      ? 'Economia projetada (Sucesso na Defesa): ' + new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(riskValue)
                      : 'Economia projetada (Acordo): ' + new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(riskValue - negotiationValue)}
                  </strong>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Painel de Recomendação da IA */}
        <div className="dashboard-card">
          <div className="card-header">
            <h3>Justificativa do Agente IA (Python API)</h3>
          </div>
          <div className="card-body">
            <div className="kpi-group">
              <div className="kpi">
                <div className="kpi-value highlight-info">{isDefesa ? 'Baixo' : 'Alto'}</div>
                <div className="kpi-label">Risco de Inversão do Ônus</div>
              </div>
              <div className="kpi">
                <div className="kpi-value highlight-info">{isDefesa ? 'Sólida' : 'Frágil'}</div>
                <div className="kpi-label">Prova Documental</div>
              </div>
            </div>

            <div className="stats-comparison">
              <div className="compare-item" style={{ flexDirection: 'column', alignItems: 'flex-start', marginTop: '1rem' }}>
                <span className="compare-label" style={{ marginBottom: '0.5rem' }}>Estratégia Recomendada:</span>
                <span className="compare-value highlight-success" style={{ fontSize: '1rem', textAlign: 'left', lineHeight: '1.5' }}>
                  {caseData.suggestion}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Painel de Inteligência de Mercado - Base Histórica */}
        <div className="dashboard-card full-width">
          <div className="card-header">
            <h3>Inteligência de Mercado - Base Histórica ({stats.total_cases.toLocaleString()} Processos)</h3>
          </div>
          <div className="card-body">
            <div className="macro-stats-grid">
              <div className="macro-kpi">
                <span className="label">Taxa de Êxito (Banco Ganha)</span>
                <span className="value highlight-success">{stats.success_rate}%</span>
                <span className="sub">41.733 casos</span>
              </div>
              <div className="macro-kpi">
                <span className="label">Taxa de Derrota (Banco Perde)</span>
                <span className="value highlight-danger">{stats.loss_rate}%</span>
                <span className="sub">18.267 casos</span>
              </div>
              <div className="macro-kpi">
                <span className="label">Adesão Atual a Acordos</span>
                <span className="value highlight-info">{stats.agreement_rate}%</span>
                <span className="sub">Apenas 280 acordos realizados</span>
              </div>
            </div>

            <div className="micro-stats-table">
              <h4>Detalhamento Granular (Resultados Micro)</h4>
              <div className="stats-row">
                {stats.detailed.map((item, idx) => (
                  <div key={idx} className="stats-bar-group">
                    <div className="stats-bar-label">{item.label} ({item.value}%)</div>
                    <div className="stats-bar-outer">
                      <div 
                        className={`stats-bar-inner ${item.macro === 'Exito' ? 'success' : item.label === 'Acordo' ? 'info' : 'danger'}`} 
                        style={{width: `${item.value}%`}}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="insight-box">
              <p><strong>Insight Estratégico:</strong> Atualmente, {stats.loss_rate}% dos casos resultam em perda para o banco. Com apenas {stats.agreement_rate}% de acordos, há uma oportunidade massiva de converter os 18 mil casos de "Não Êxito" em acordos controlados, reduzindo o ticket médio de condenação em até 60%.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
