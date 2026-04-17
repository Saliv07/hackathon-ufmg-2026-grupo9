import { useState, useEffect, useCallback } from 'react';
import { Search, ChevronLeft, ChevronRight, Database, ArrowUp, ArrowDown } from 'lucide-react';
import './DataExplorer.css';

const BACKEND = `http://${window.location.hostname}:5000`;

const COLS = [
  { key: 'Número do processo', label: 'Nº Processo', mono: true },
  { key: 'UF', label: 'UF' },
  { key: 'Assunto', label: 'Assunto' },
  { key: 'Sub-assunto', label: 'Sub-assunto' },
  { key: 'Resultado macro', label: 'Macro' },
  { key: 'Resultado micro', label: 'Micro' },
  { key: 'Valor da causa', label: 'Valor Causa', fmt: true },
  { key: 'Valor da condenação/indenização', label: 'Valor Condenação', fmt: true },
];

const fmt = (v) => {
  if (v === '' || v == null) return '—';
  const n = Number(v);
  if (isNaN(n)) return String(v);
  return n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
};

function DataExplorer() {
  const [data, setData] = useState(null);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [resultFilter, setResultFilter] = useState('');
  const [sortBy, setSortBy] = useState('');
  const [sortOrder, setSortOrder] = useState('asc');
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(() => {
    setLoading(true);
    const params = new URLSearchParams({ page, per_page: 50 });
    if (search) params.set('search', search);
    if (resultFilter) params.set('result', resultFilter);
    if (sortBy) {
      params.set('sort_by', sortBy);
      params.set('order', sortOrder);
    }

    fetch(`${BACKEND}/api/historical?${params}`)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [page, search, resultFilter, sortBy, sortOrder]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    fetchData();
  };

  const handleSort = (key) => {
    if (sortBy === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(key);
      setSortOrder('asc');
    }
    setPage(1);
  };

  const macroBadge = (val) => {
    if (!val) return val;
    const cls = val === 'Êxito' ? 'success' : val === 'Não Êxito' ? 'danger' : 'neutral';
    return <span className={`macro-badge ${cls}`}>{val}</span>;
  };

  return (
    <div className="explorer-view fade-in">
      <div className="explorer-header">
        <div>
          <div className="explorer-breadcrumb">
            <span>enterOS</span><span>analytics</span><span>base histórica</span>
          </div>
          <h1>Base Histórica</h1>
          <p>
            {data ? `${data.total.toLocaleString()} processos encontrados` : 'Carregando...'}
            {' · '}Hackaton_Enter_Base_Candidatos.xlsx
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="explorer-filters">
        <form onSubmit={handleSearch} className="search-box">
          <Search size={14} />
          <input
            placeholder="Buscar por nº processo, assunto ou UF..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </form>
        <div className="filter-pills">
          {[{ val: '', label: 'todos' }, { val: 'Êxito', label: 'Êxito' }, { val: 'Não Êxito', label: 'Não Êxito' }].map(f => (
            <button
              key={f.val}
              className={`filter-pill ${resultFilter === f.val ? 'active' : ''}`}
              onClick={() => { setResultFilter(f.val); setPage(1); }}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="explorer-table-wrap">
        {loading ? (
          <div className="explorer-loading">
            <Database size={24} className="spin" />
            <span>Carregando base histórica...</span>
          </div>
        ) : (
          <table className="explorer-table">
            <thead>
              <tr>
                {COLS.map(c => (
                  <th 
                    key={c.key} 
                    onClick={() => handleSort(c.key)}
                    className="sortable-header"
                  >
                    <div className="header-content">
                      {c.label}
                      {sortBy === c.key && (
                        sortOrder === 'asc' ? <ArrowUp size={12} /> : <ArrowDown size={12} />
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data?.rows?.map((row, i) => (
                <tr key={i}>
                  {COLS.map(c => (
                    <td key={c.key} className={c.mono ? 'mono' : ''}>
                      {c.key === 'Resultado macro'
                        ? macroBadge(row[c.key])
                        : c.fmt ? fmt(row[c.key]) : (row[c.key] || '—')}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {data && (
        <div className="explorer-pagination">
          <span className="page-info">
            Página {data.page} de {data.total_pages}
            {' · '}{data.total.toLocaleString()} registros
          </span>
          <div className="page-buttons">
            <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}>
              <ChevronLeft size={14} /> Anterior
            </button>
            <button disabled={page >= data.total_pages} onClick={() => setPage(p => p + 1)}>
              Próxima <ChevronRight size={14} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default DataExplorer;
