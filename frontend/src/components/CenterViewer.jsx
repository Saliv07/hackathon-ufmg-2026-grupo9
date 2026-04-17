import './CenterViewer.css';

function CenterViewer({ document, onContentChange }) {
  if (!document) {
    return (
      <div className="center-viewer empty-state">
        <div className="empty-icon">📄</div>
        <p>Selecione um documento para visualizar</p>
      </div>
    );
  }

  // Nota editável
  if (document.type === 'Nota') {
    return (
      <div className="center-viewer note-viewer">
        <div className="note-header">
          <span className="note-icon">✏️</span>
          <span className="note-title">{document.name}</span>
          <span className="note-hint">As anotações ficam visíveis ao agente como contexto</span>
        </div>
        <textarea
          className="note-textarea"
          value={document.content}
          onChange={e => onContentChange?.(document.id, e.target.value)}
          placeholder="Digite suas anotações aqui...&#10;&#10;Este documento será incluído como contexto no chat do Agente Jurídico."
          spellCheck={false}
          autoFocus
        />
      </div>
    );
  }

  // PDF ou arquivo com URL — renderiza inline
  if (document.fileUrl) {
    const isPdf = document.name?.toLowerCase().endsWith('.pdf') || document.type !== 'Nota';
    const isImage = /\.(png|jpg|jpeg|gif|webp)$/i.test(document.name || '');

    if (isImage) {
      return (
        <div className="center-viewer image-viewer">
          <div className="viewer-toolbar">
            <span className="doc-type-badge">{document.type}</span>
            <span className="doc-name-label">{document.name}</span>
          </div>
          <div className="image-container">
            <img src={document.fileUrl} alt={document.name} className="doc-image" />
          </div>
        </div>
      );
    }

    if (isPdf) {
      return (
        <div className="center-viewer pdf-viewer">
          <div className="viewer-toolbar">
            <span className="doc-type-badge">{document.type}</span>
            <span className="doc-name-label">{document.name}</span>
            <a
              href={document.fileUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="toolbar-btn"
              title="Abrir em nova aba"
            >
              ↗ Abrir
            </a>
          </div>
          <iframe
            src={document.fileUrl}
            title={document.name}
            className="pdf-iframe"
            type="application/pdf"
          />
        </div>
      );
    }
  }

  // Fallback: exibe o conteúdo de texto
  return (
    <div className="center-viewer text-viewer">
      <div className="viewer-toolbar">
        <span className="doc-type-badge">{document.type}</span>
        <span className="doc-name-label">{document.name}</span>
      </div>
      <div className="text-content">
        <div className="text-body">
          {document.content
            ? document.content.split('\n').map((line, i) => (
                <p key={i}>{line || <br />}</p>
              ))
            : <p className="no-content">Conteúdo não disponível.</p>
          }
        </div>
      </div>
    </div>
  );
}

export default CenterViewer;
