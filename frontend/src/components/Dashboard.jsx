import React, { useState, useEffect } from 'react';
import { Bot, Shield, TrendingUp, Bell, Scale } from 'lucide-react';
import './Dashboard.css';

const fmt = (v) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v);



function Dashboard({ caseData }) {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    const hostname = window.location.hostname;
    fetch(`http://${hostname}:5000/api/stats`)
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(err => console.error("Erro ao buscar estatísticas:", err));
  }, []);

  if (!stats) return <div className="loading-stats">Carregando estatísticas do servidor Python...</div>;

  const askedValue = caseData?.askedValue || 0;
  const isDefesa = caseData?.recommendation === 'DEFESA';
  const negotiationValue = isDefesa ? 0 : askedValue * 0.28;
  const legalCosts = askedValue * 0.15 + 2000;
  const riskValue = askedValue + legalCosts;

  return (
    <div className="dash-view fade-in">
      {/* Header */}
      <div className="dash-header">
        <div className="dash-header-text">
          <div className="dash-breadcrumb">
            <span>enterOS</span><span>analytics</span><span>dashboard macro</span>
          </div>
          <h1>Painel de Inteligência</h1>
          <p>
            Base histórica de {stats.total_cases?.toLocaleString()} processos
            {caseData ? ` · caso ativo: ${caseData.plaintiff}` : ''}
          </p>
        </div>
      </div>

      {/* Macro strip KPIs */}
      <div className="dash-macro-strip">
        <div className="dash-macro-cell">
          <span className="label">Taxa de êxito</span>
          <span className="value">{stats.success_rate}%</span>
          <span className="sub"><span className="trend up">▲</span> 41.733 / {stats.total_cases?.toLocaleString()}</span>
        </div>
        <div className="dash-macro-cell">
          <span className="label">Taxa de derrota</span>
          <span className="value danger">{stats.loss_rate}%</span>
          <span className="sub"><span className="trend down">▼</span> 18.267 casos</span>
        </div>
        <div className="dash-macro-cell">
          <span className="label">Adesão a acordos</span>
          <span className="value accent">{stats.agreement_rate}%</span>
          <span className="sub">Apenas 280 acordos realizados</span>
        </div>
        <div className="dash-macro-cell">
          <span className="label">Ticket médio condenação</span>
          <span className="value">R$ 9.340</span>
          <span className="sub"><span className="trend down">▼</span> −18% vs baseline</span>
        </div>
      </div>

      {/* Main grid: left = case analysis, right = rail cards */}
      <div className="dash-grid">
        {/* Left: caso ativo */}
        <div className="dash-main-col">
          {caseData && (
            <>
              {/* Comparativo de Cenários */}
              <div className="rail-card">
                <div className="rail-card-header">
                  <Scale size={16} />
                  <h3>Comparativo de cenários</h3>
                  <span className="mono-dim">{caseData.number}</span>
                </div>
                <div className="rail-card-body">
                  <div className="dash-kpi-row">
                    <div className="dash-kpi">
                      <span className="dash-kpi-value danger">{fmt(askedValue)}</span>
                      <span className="dash-kpi-label">Valor do pedido (risco)</span>
                    </div>
                    <div className="dash-kpi">
                      <span className="dash-kpi-value success">{fmt(negotiationValue)}</span>
                      <span className="dash-kpi-label">{isDefesa ? 'Valor sugerido acordo' : 'Teto de negociação'}</span>
                    </div>
                  </div>

                  <div className="dash-comparison-bars">
                    <div className="dash-bar-outer"><div className="dash-bar-inner danger" style={{ width: '100%' }} /></div>
                    <div className="dash-bar-outer"><div className="dash-bar-inner success" style={{ width: isDefesa ? '0%' : '30%' }} /></div>
                  </div>

                  <div className="dash-metrics-list">
                    <div className="dash-metric-row">
                      <span className="dash-metric-label">Custas processuais estimadas</span>
                      <span className="dash-metric-value">{fmt(legalCosts)}</span>
                    </div>
                    <div className="dash-metric-row">
                      <span className="dash-metric-label">Risco total em caso de perda</span>
                      <span className="dash-metric-value danger">{fmt(riskValue)}</span>
                    </div>
                    <div className="dash-metric-row highlight">
                      <span className="dash-metric-label">
                        {isDefesa ? 'Economia projetada (defesa)' : 'Economia projetada (acordo)'}
                      </span>
                      <span className="dash-metric-value success">
                        {fmt(isDefesa ? riskValue : riskValue - negotiationValue)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Justificativa IA */}
              <div className="rail-card">
                <div className="rail-card-header">
                  <Bot size={16} />
                  <h3>Justificativa do agente IA</h3>
                  <span className="pulse" />
                </div>
                <div className="rail-card-body">
                  <div className="dash-kpi-row">
                    <div className="dash-kpi">
                      <span className={`dash-kpi-value ${isDefesa ? 'success' : 'danger'}`}>{isDefesa ? 'Baixo' : 'Alto'}</span>
                      <span className="dash-kpi-label">Risco inversão do ônus</span>
                    </div>
                    <div className="dash-kpi">
                      <span className={`dash-kpi-value ${isDefesa ? 'success' : 'danger'}`}>{isDefesa ? 'Sólida' : 'Frágil'}</span>
                      <span className="dash-kpi-label">Prova documental</span>
                    </div>
                  </div>
                  <div className="dash-strategy-box">
                    <span className="dash-strategy-label">Estratégia recomendada:</span>
                    <p className="dash-strategy-text">{caseData.suggestion}</p>
                  </div>
                </div>
              </div>
            </>
          )}

          {!caseData && (
            <div className="rail-card">
              <div className="rail-card-body" style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
                Selecione um caso na sidebar para ver a análise individual.
              </div>
            </div>
          )}
        </div>

        {/* Right: rail cards */}
        <div className="dash-rail-col">
          {/* Distribuição */}
          <div className="rail-card">
            <div className="rail-card-header">
              <TrendingUp size={16} />
              <h3>Resultados · base histórica</h3>
              <span className="mono-dim">{stats.total_cases?.toLocaleString()} casos</span>
            </div>
            <div className="rail-card-body">
              {stats.detailed.map((s, i) => (
                <div key={i}>
                  <div className="dist-row">
                    <span className="lbl">{s.label}</span>
                    <span className="val">{s.value}%</span>
                  </div>
                  <div className="dist-bar-outer">
                    <div
                      className={`dist-bar-inner ${s.macro === 'Exito' ? 'success' : s.label === 'Acordo' ? 'accent' : 'danger'}`}
                      style={{ width: `${s.value}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Política */}
          <div className="rail-card">
            <div className="rail-card-header">
              <Shield size={16} />
              <h3>Política de acordos · v2.1</h3>
            </div>
            <div className="rail-card-body">
              <div className="policy-metric">
                <span className="pm-label">Aderência dos advogados</span>
                <span className="pm-value good">87%</span>
              </div>
              <div className="policy-metric">
                <span className="pm-label">Acordos fechados (mês)</span>
                <span className="pm-value">214</span>
              </div>
              <div className="policy-metric">
                <span className="pm-label">Valor médio proposto</span>
                <span className="pm-value">R$ 6.420</span>
              </div>
              <div className="policy-metric">
                <span className="pm-label">Desvio de política</span>
                <span className="pm-value bad">12 casos</span>
              </div>
              <div className="mini-chart">
                {[40, 55, 48, 62, 58, 70, 66, 74, 80, 78, 85, 87].map((h, i) => (
                  <div className="bar" key={i} style={{ height: `${h}%` }} />
                ))}
              </div>
            </div>
          </div>


        </div>
      </div>

      {/* Insight box */}
      <div className="dash-insight-box">
        <p>
          <strong>Insight Estratégico:</strong> Atualmente, {stats.loss_rate}% dos casos resultam em perda para o banco.
          Com apenas {stats.agreement_rate}% de acordos, há uma oportunidade massiva de converter os 18 mil casos
          de "Não Êxito" em acordos controlados, reduzindo o ticket médio de condenação em até 60%.
        </p>
      </div>
    </div>
  );
}

export default Dashboard;
