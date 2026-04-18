import React, { useState, useEffect } from 'react';
import { Shield, TrendingUp } from 'lucide-react';
import './Dashboard.css';

const fmt = (v) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v);
const fmtCompact = (v) => new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
  notation: 'compact',
  maximumFractionDigits: 1,
}).format(v);
const fmtPct = (v) => `${Number(v || 0).toLocaleString('pt-BR', {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
})}%`;

function Dashboard() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    const hostname = window.location.hostname;
    fetch(`http://${hostname}:5000/api/stats`)
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(err => console.error("Erro ao buscar estatísticas:", err));
  }, []);

  if (!stats) return <div className="loading-stats">Carregando estatísticas do servidor Python...</div>;

  const policyProjection = stats.policy_projection;
  const projectionModeLabel = policyProjection?.projection_type === 'hybrid_policy_engine_v2_1'
    ? 'Híbrido · regras + XGBoost'
    : 'Regras fixas';

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
          <span className="label">Gasto com política</span>
          <span className="value">
            {policyProjection ? fmtCompact(policyProjection.projected_total_cost) : '—'}
          </span>
          <span className="sub">
            {policyProjection
              ? <><span className="trend up">▲</span> Economia potencial {fmtCompact(policyProjection.estimated_savings)}</>
              : 'Simulação indisponível'}
          </span>
        </div>
      </div>

      <div className="dash-grid">
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

        <div className="rail-card">
          <div className="rail-card-header">
            <Shield size={16} />
            <h3>Cenário com política · v2.1</h3>
            {policyProjection && <span className="mono-dim">{projectionModeLabel}</span>}
          </div>
          <div className="rail-card-body">
            {policyProjection ? (
              <>
                <div className="policy-metric">
                  <span className="pm-label">Gasto histórico total</span>
                  <span className="pm-value">{fmtCompact(policyProjection.actual_total_cost)}</span>
                </div>
                <div className="policy-metric">
                  <span className="pm-label">Gasto com a política</span>
                  <span className="pm-value">{fmtCompact(policyProjection.projected_total_cost)}</span>
                </div>
                <div className="policy-metric">
                  <span className="pm-label">Economia estimada</span>
                  <span className="pm-value good">{fmtCompact(policyProjection.estimated_savings)}</span>
                </div>
                <div className="policy-metric">
                  <span className="pm-label">Redução projetada</span>
                  <span className="pm-value good">{fmtPct(policyProjection.estimated_savings_rate)}</span>
                </div>
                <div className="policy-metric">
                  <span className="pm-label">Acordos atuais</span>
                  <span className="pm-value">
                    {policyProjection.current_agreement_cases.toLocaleString('pt-BR')}
                  </span>
                </div>
                <div className="policy-metric">
                  <span className="pm-label">Acordos com política</span>
                  <span className="pm-value">
                    {policyProjection.projected_agreement_cases.toLocaleString('pt-BR')}
                  </span>
                </div>
                <div className="policy-metric">
                  <span className="pm-label">Valor médio do acordo projetado</span>
                  <span className="pm-value">{fmt(policyProjection.projected_agreement_average)}</span>
                </div>
              </>
            ) : (
              <div style={{ color: 'var(--text-muted)', fontSize: '13px', lineHeight: 1.6 }}>
                A simulação da política não está disponível no backend.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Insight box */}
      <div className="dash-insight-box">
        {policyProjection ? (
          <p>
            <strong>Insight Estratégico:</strong> Na base histórica, o banco desembolsou {fmt(policyProjection.actual_total_cost)}.
            Se a política v2.1 tivesse sido aplicada de forma consistente, o gasto estimado cairia para {fmt(policyProjection.projected_total_cost)},
            com economia potencial de {fmt(policyProjection.estimated_savings)} ({fmtPct(policyProjection.estimated_savings_rate)}).
          </p>
        ) : (
          <p>
            <strong>Insight Estratégico:</strong> Atualmente, {stats.loss_rate}% dos casos resultam em perda para o banco.
            Com apenas {stats.agreement_rate}% de acordos, há uma oportunidade massiva de converter os 18 mil casos
            de "Não Êxito" em acordos controlados, reduzindo o ticket médio de condenação em até 60%.
          </p>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
