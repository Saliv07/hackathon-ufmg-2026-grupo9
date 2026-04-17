import './CenterViewer.css';

function CenterViewer({ document }) {
  if (!document) {
    return (
      <div className="center-viewer empty-state">
        <div className="empty-icon">📄</div>
        <p>Selecione um documento para visualizar</p>
      </div>
    );
  }

  return (
    <div className="center-viewer">
      <div className="viewer-header">
        <div className="tabs">
          <div className="tab active">{document.name}</div>
        </div>
        <div className="viewer-actions">
          <button className="action-btn" title="Download">⬇️</button>
          <button className="action-btn" title="Expandir">⛶</button>
        </div>
      </div>
      <div className="viewer-content">
        <div className="document-page">
          <h2>{document.name}</h2>
          <div className="document-text">
            {document.content}
            <br/><br/>
            <div className="document-body">
              {/* Conteúdo real do documento simulado */}
              <p>Considerando o teor do processo nº {document.caseNumber || '0801234-56.2024.8.10.0001'}, este documento de {document.type} apresenta os fatos narrados e as evidências colhidas.</p>
              <p>A análise técnica do Agente Jurídico IA identificou pontos de convergência com a base histórica do banco, permitindo uma decisão fundamentada em dados.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default CenterViewer;
