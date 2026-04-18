import { useEffect, useMemo, useState } from 'react';
import { AlertCircle, ExternalLink, RefreshCw, X } from 'lucide-react';
import './MonitoramentoBanco.css';

// Em produção o próprio Flask serve /monitoramento/ (Dash montado no mesmo
// processo via create_dash_app). Em dev Vite (porta 5173), aponta para o
// backend em :5000 onde o Dash está montado.
const MONITOR_BASE = window.location.port === '5173'
  ? `http://${window.location.hostname}:5000/monitoramento/`
  : '/monitoramento/';

const API_BASE = window.location.port === '5173'
  ? `http://${window.location.hostname}:5000/api`
  : '/api';

const TABS = [
  { id: 'aderencia', label: 'Aderência' },
  { id: 'efetividade', label: 'Efetividade' },
];

const SUB_OPTIONS = [
  { id: 'Todos', label: 'Todos' },
  { id: 'Golpe', label: 'Golpe' },
  { id: 'Genérico', label: 'Genérico' },
];

function buildQueryString({ tab, ufs, escs, sub, dataFrom, dataTo, prob }) {
  const params = new URLSearchParams();
  if (tab) params.set('tab', tab);
  if (ufs && ufs.length) params.set('uf', ufs.join(','));
  if (escs && escs.length) params.set('esc', escs.join(','));
  if (sub && sub !== 'Todos') params.set('sub', sub);
  if (dataFrom) params.set('from', dataFrom);
  if (dataTo) params.set('to', dataTo);
  if (typeof prob === 'number' && !Number.isNaN(prob)) {
    params.set('prob', prob.toFixed(2));
  }
  const str = params.toString();
  return str ? `?${str}` : '';
}

export default function MonitoramentoBanco() {
  const [loadError, setLoadError] = useState(false);
  const [tab, setTab] = useState('aderencia');
  const [ufs, setUfs] = useState([]);
  const [escs, setEscs] = useState([]);
  const [sub, setSub] = useState('Todos');
  const [dataFrom, setDataFrom] = useState('');
  const [dataTo, setDataTo] = useState('');
  const [prob, setProb] = useState(0.40);

  // Opções dinâmicas vindas do backend
  const [options, setOptions] = useState({
    ufs: [],
    escritorios: [],
    escritoriosNomes: {},
    periodo: null,
  });
  const [optionsError, setOptionsError] = useState(false);

  // Chave que força o remount do iframe quando qualquer filtro muda
  const [iframeKey, setIframeKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_BASE}/monitoring/filtros`)
      .then((r) => r.ok ? r.json() : Promise.reject(new Error(`${r.status}`)))
      .then((data) => {
        if (cancelled) return;
        setOptions({
          ufs: data.ufs || [],
          escritorios: data.escritorios || [],
          escritoriosNomes: data.escritorios_nomes || {},
          periodo: data.periodo || null,
        });
        // Default do período: range completo
        if (data.periodo && !dataFrom && !dataTo) {
          setDataFrom(data.periodo.min);
          setDataTo(data.periodo.max);
        }
      })
      .catch(() => { if (!cancelled) setOptionsError(true); });
    return () => { cancelled = true; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const iframeUrl = useMemo(() => {
    const qs = buildQueryString({ tab, ufs, escs, sub, dataFrom, dataTo, prob });
    return `${MONITOR_BASE}${qs}`;
  }, [tab, ufs, escs, sub, dataFrom, dataTo, prob]);

  const toggleInList = (value, list, setter) => {
    if (list.includes(value)) {
      setter(list.filter((v) => v !== value));
    } else {
      setter([...list, value]);
    }
  };

  const resetFilters = () => {
    setUfs([]);
    setEscs([]);
    setSub('Todos');
    if (options.periodo) {
      setDataFrom(options.periodo.min);
      setDataTo(options.periodo.max);
    } else {
      setDataFrom('');
      setDataTo('');
    }
    setProb(0.40);
  };

  const reloadIframe = () => setIframeKey((k) => k + 1);

  const hasActiveFilter =
    ufs.length > 0 || escs.length > 0 || sub !== 'Todos' ||
    (options.periodo && (dataFrom !== options.periodo.min || dataTo !== options.periodo.max));

  return (
    <div className="monitoramento-view fade-in">
      <div className="monitoramento-header">
        <div className="monitoramento-titulo">
          <span className="monitoramento-eyebrow">ÁREA DO BANCO</span>
          <h2>Monitoramento da política de acordos</h2>
        </div>
        <div className="monitoramento-header-actions">
          <button
            type="button"
            onClick={reloadIframe}
            className="monitoramento-btn-ghost"
            title="Recarregar dashboard"
          >
            <RefreshCw size={14} />
            <span>Recarregar</span>
          </button>
          <a
            href={iframeUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="monitoramento-open-external"
            title="Abrir em uma nova aba"
          >
            <ExternalLink size={14} />
            <span>Abrir isolado</span>
          </a>
        </div>
      </div>

      <div className="monitoramento-controls">
        <div className="monitoramento-tabs">
          {TABS.map((t) => (
            <button
              type="button"
              key={t.id}
              className={`monitoramento-tab ${tab === t.id ? 'active' : ''}`}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div className="monitoramento-filters">
          {/* UF multi */}
          <div className="filter-group">
            <label className="filter-label">UF</label>
            <div className="filter-chips">
              {options.ufs.length === 0 && (
                <span className="filter-hint">
                  {optionsError ? 'Indisponível' : 'Carregando...'}
                </span>
              )}
              {options.ufs.map((u) => (
                <button
                  key={u}
                  type="button"
                  className={`chip ${ufs.includes(u) ? 'chip-active' : ''}`}
                  onClick={() => toggleInList(u, ufs, setUfs)}
                >
                  {u}
                </button>
              ))}
            </div>
          </div>

          {/* Sub-assunto segmented */}
          <div className="filter-group">
            <label className="filter-label">Sub-assunto</label>
            <div className="segmented">
              {SUB_OPTIONS.map((opt) => (
                <button
                  key={opt.id}
                  type="button"
                  className={`seg-btn ${sub === opt.id ? 'active' : ''}`}
                  onClick={() => setSub(opt.id)}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Período */}
          <div className="filter-group">
            <label className="filter-label">Período</label>
            <div className="filter-range">
              <input
                type="date"
                value={dataFrom}
                min={options.periodo?.min}
                max={options.periodo?.max}
                onChange={(e) => setDataFrom(e.target.value)}
                className="date-input"
              />
              <span className="range-sep">→</span>
              <input
                type="date"
                value={dataTo}
                min={options.periodo?.min}
                max={options.periodo?.max}
                onChange={(e) => setDataTo(e.target.value)}
                className="date-input"
              />
            </div>
          </div>

          {/* Escritório multi (dropdown-like) */}
          {options.escritorios.length > 0 && (
            <div className="filter-group filter-group-wide">
              <label className="filter-label">
                Escritório {escs.length > 0 && <span className="filter-count">({escs.length})</span>}
              </label>
              <details className="multi-details">
                <summary className="multi-summary">
                  {escs.length === 0
                    ? 'Todos'
                    : `${escs.length} selecionado(s)`}
                </summary>
                <div className="multi-list">
                  {options.escritorios.map((e) => (
                    <label key={e} className="multi-item">
                      <input
                        type="checkbox"
                        checked={escs.includes(e)}
                        onChange={() => toggleInList(e, escs, setEscs)}
                      />
                      <span>{options.escritoriosNomes[e] || e}</span>
                    </label>
                  ))}
                </div>
              </details>
            </div>
          )}

          {/* Slider de prob_aceita (apenas na aba Efetividade) */}
          {tab === 'efetividade' && (
            <div className="filter-group">
              <label className="filter-label">
                Prob. aceitação <span className="filter-count">({Math.round(prob*100)}%)</span>
              </label>
              <input
                type="range"
                min={0.10} max={0.95} step={0.05}
                value={prob}
                onChange={(e) => setProb(parseFloat(e.target.value))}
                className="prob-range"
              />
            </div>
          )}

          {hasActiveFilter && (
            <button
              type="button"
              onClick={resetFilters}
              className="monitoramento-btn-reset"
              title="Limpar filtros"
            >
              <X size={13} />
              <span>Limpar</span>
            </button>
          )}
        </div>
      </div>

      {loadError ? (
        <div className="monitoramento-error">
          <AlertCircle size={24} />
          <div>
            <strong>Dashboard offline</strong>
            <p>
              Não foi possível carregar o monitoramento em <code>{iframeUrl}</code>.
              Verifique se o backend Flask está rodando (<code>python backend/main.py</code>).
            </p>
          </div>
        </div>
      ) : (
        <iframe
          key={iframeKey}
          src={iframeUrl}
          title="Monitoramento Banco UFMG"
          className="monitoramento-frame"
          onError={() => setLoadError(true)}
        />
      )}
    </div>
  );
}
