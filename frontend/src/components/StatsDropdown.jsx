import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { TrendingUp, Scale, ShieldAlert } from 'lucide-react';
import './StatsDropdown.css';

const historicalData = [
  { ano: '2021', acordos: 30, perdas: 70 },
  { ano: '2022', acordos: 45, perdas: 55 },
  { ano: '2023', acordos: 60, perdas: 40 },
  { ano: '2024', acordos: 85, perdas: 15 },
];

function StatsDropdown({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <>
      <div className="stats-overlay" onClick={onClose}></div>
      <div className="stats-dropdown-panel">
        <div className="stats-panel-header">
          <div className="stats-title-group">
            <TrendingUp size={20} color="var(--accent-color)" />
            <h3>Estatísticas do Processo</h3>
          </div>
          <p>Dados históricos de casos similares nesta comarca (MG)</p>
        </div>

        <div className="stats-cards">
          <div className="stats-card">
            <div className="stats-card-header">
              <Scale size={16} />
              <span>Valor Médio (Acordo)</span>
            </div>
            <div className="stats-card-value success">R$ 3.800</div>
          </div>
          <div className="stats-card">
            <div className="stats-card-header">
              <ShieldAlert size={16} />
              <span>Condenação Média</span>
            </div>
            <div className="stats-card-value danger">R$ 8.500</div>
          </div>
        </div>

        <div className="stats-chart-section">
          <h4>Taxa de Sucesso vs Perdas ao Longo do Tempo</h4>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={historicalData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorAcordos" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--success-color)" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="var(--success-color)" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorPerdas" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--danger-color)" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="var(--danger-color)" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="ano" stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'var(--bg-panel)', border: '1px solid var(--border-color)', borderRadius: '8px' }}
                  itemStyle={{ color: 'var(--text-main)' }}
                />
                <Area type="monotone" dataKey="acordos" name="Acordos (Êxito)" stroke="var(--success-color)" fillOpacity={1} fill="url(#colorAcordos)" />
                <Area type="monotone" dataKey="perdas" name="Perdas" stroke="var(--danger-color)" fillOpacity={1} fill="url(#colorPerdas)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </>
  );
}

export default StatsDropdown;
