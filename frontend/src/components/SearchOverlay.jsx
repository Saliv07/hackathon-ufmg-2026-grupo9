import { useState, useEffect, useRef } from 'react';
import { Search, X, FileText, ArrowRight, Database, Files, BookOpen } from 'lucide-react';
import './SearchOverlay.css';

function SearchOverlay({ cases, selectedCase, onClose, onSelectCase }) {
  const [query, setQuery] = useState('');
  const [scope, setScope] = useState('cases'); // cases, current_docs, all_docs, historical
  const [results, setResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const inputRef = useRef(null);

  useEffect(() => {
    inputRef.current?.focus();
    const handleEsc = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [onClose]);

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }

    const q = query.toLowerCase();
    setIsSearching(true);

    // Simulação de busca com pequeno delay para "feel" de processamento
    const timer = setTimeout(() => {
      let filtered = [];

      if (scope === 'cases') {
        filtered = cases.filter(c => 
          c.plaintiff.toLowerCase().includes(q) || 
          c.number.toLowerCase().includes(q) ||
          c.summary.toLowerCase().includes(q)
        ).map(c => ({ ...c, type: 'case' }));
      } 
      else if (scope === 'current_docs' && selectedCase) {
        filtered = (selectedCase.documents || []).filter(d => 
          d.name.toLowerCase().includes(q) || 
          (d.content && d.content.toLowerCase().includes(q))
        ).map(d => ({ ...d, type: 'doc', parentCase: selectedCase }));
      }
      else if (scope === 'all_docs') {
        cases.forEach(c => {
          (c.documents || []).forEach(d => {
            if (d.name.toLowerCase().includes(q) || (d.content && d.content.toLowerCase().includes(q))) {
              filtered.push({ ...d, type: 'doc', parentCase: c });
            }
          });
        });
      }
      else if (scope === 'historical') {
        // Busca na base histórica (via API ou mock local se disponível)
        // Aqui simulamos uma busca nos dados que temos, mas poderíamos chamar o backend
        filtered = cases.filter(c => 
          c.suggestion.toLowerCase().includes(q) || 
          c.summary.toLowerCase().includes(q)
        ).map(c => ({ ...c, type: 'history' }));
      }

      setResults(filtered.slice(0, 10));
      setIsSearching(false);
    }, 150);

    return () => clearTimeout(timer);
  }, [query, scope, cases, selectedCase]);

  const renderIcon = (type) => {
    switch(type) {
      case 'doc': return <Files size={18} />;
      case 'history': return <Database size={18} />;
      default: return <FileText size={18} />;
    }
  };

  return (
    <div className="search-overlay-backdrop" onClick={onClose}>
      <div className="search-modal" onClick={e => e.stopPropagation()}>
        <div className="search-header-area">
          <div className="search-input-wrapper">
            <Search size={20} className="search-icon-inside" />
            <input
              ref={inputRef}
              placeholder={
                scope === 'cases' ? "Pesquisar processos..." :
                scope === 'historical' ? "Pesquisar na base histórica..." :
                "Pesquisar conteúdo de documentos..."
              }
              value={query}
              onChange={e => setQuery(e.target.value)}
            />
            {isSearching && <div className="search-spinner-small" />}
            <button className="search-close-btn" onClick={onClose}><X size={18} /></button>
          </div>

          <div className="search-scopes">
            <button 
              className={`scope-pill ${scope === 'cases' ? 'active' : ''}`}
              onClick={() => setScope('cases')}
            >
              <FileText size={14} /> Processos
            </button>
            {selectedCase && (
              <button 
                className={`scope-pill ${scope === 'current_docs' ? 'active' : ''}`}
                onClick={() => setScope('current_docs')}
              >
                <BookOpen size={14} /> Este Processo
              </button>
            )}
            <button 
              className={`scope-pill ${scope === 'all_docs' ? 'active' : ''}`}
              onClick={() => setScope('all_docs')}
            >
              <Files size={14} /> Todos Documentos
            </button>
            <button 
              className={`scope-pill ${scope === 'historical' ? 'active' : ''}`}
              onClick={() => setScope('historical')}
            >
              <Database size={14} /> Base Histórica
            </button>
          </div>
        </div>

        <div className="search-results-area">
          {query && results.length === 0 && !isSearching ? (
            <div className="search-no-results">
              Nenhum resultado encontrado para "{query}" no escopo selecionado.
            </div>
          ) : (
            <div className="search-results-list">
              {results.map(res => (
                <div 
                  key={res.id + (res.type || '')} 
                  className="search-result-item" 
                  onClick={() => { 
                    if (res.type === 'doc' || res.type === 'case' || res.type === 'history') {
                      onSelectCase(res.parentCase || res);
                    }
                    onClose(); 
                  }}
                >
                  <div className={`res-icon ${res.type}`}>{renderIcon(res.type)}</div>
                  <div className="res-info">
                    <div className="res-title">{res.plaintiff || res.name}</div>
                    <div className="res-sub">
                      {res.type === 'doc' ? `Documento de ${res.parentCase.plaintiff}` : 
                       res.type === 'history' ? `Registro Histórico · ${res.number}` : 
                       res.number}
                    </div>
                  </div>
                  <ArrowRight size={14} className="res-arrow" />
                </div>
              ))}
              {!query && (
                <div className="search-hint">
                  Selecione o escopo e digite para pesquisar...
                </div>
              )}
            </div>
          )}
        </div>

        <div className="search-footer">
          <span><strong>↑↓</strong> navegar</span>
          <span><strong>TAB</strong> alternar escopo</span>
          <span><strong>ESC</strong> fechar</span>
        </div>
      </div>
    </div>
  );
}

export default SearchOverlay;
