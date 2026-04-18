import { useState, useEffect } from 'react';
import './CenterViewer.css';

function CenterViewer({ document, onContentChange, onQuoteText }) {
  const [tooltip, setTooltip] = useState(null); // { text, x, y }

  // Fecha tooltip ao clicar fora dele
  useEffect(() => {
    const dismiss = (e) => {
      if (!e.target.closest?.('.selection-tooltip')) setTooltip(null);
    };
    window.addEventListener('mousedown', dismiss);
    return () => window.removeEventListener('mousedown', dismiss);
  }, []);

  const handleMouseUp = () => {
    setTimeout(() => {
      const sel = window.getSelection();
      if (!sel || sel.isCollapsed) { setTooltip(null); return; }
      const text = sel.toString().trim();
      if (!text) { setTooltip(null); return; }
      const rect = sel.getRangeAt(0).getBoundingClientRect();
      setTooltip({ text, x: rect.left + rect.width / 2, y: rect.top });
    }, 10);
  };

  const handleCite = () => {
    if (!tooltip) return;
    onQuoteText?.(tooltip.text);
    setTooltip(null);
    window.getSelection()?.removeAllRanges();
  };

  if (!document) {
    return (
      <div className="center-viewer empty-state">
        <div className="empty-icon">📄</div>
        <p>Selecione um documento para visualizar</p>
      </div>
    );
  }

  const ext = document.name?.split('.').pop().toLowerCase() ?? '';
  const isPdf   = ext === 'pdf';
  const isImage = ['png', 'jpg', 'jpeg', 'gif', 'webp'].includes(ext);
  const isAudio = ['mp3', 'wav', 'ogg', 'm4a'].includes(ext);
  const isText  = ['txt', 'md'].includes(ext);

  // ── Nota editável ──────────────────────────────────────────────────────────
  if (document.type === 'Nota') {
    return (
      <div className="center-viewer note-viewer">
        <div className="note-header">
          <span className="note-icon">✏️</span>
          <span className="note-title">{document.name}</span>
          <span className="note-hint">Anotações ficam visíveis ao agente como contexto</span>
        </div>
        <textarea
          className="note-textarea"
          value={document.content}
          onChange={e => onContentChange?.(document.id, e.target.value)}
          onMouseUp={handleMouseUp}
          placeholder={"Digite suas anotações aqui...\n\nEste documento será incluído como contexto no Agente Jurídico."}
          spellCheck={false}
          autoFocus
        />
        {tooltip && (
          <div className="selection-tooltip" style={{ left: tooltip.x, top: tooltip.y }}>
            <button onClick={handleCite}>💬 Citar no chat</button>
          </div>
        )}
      </div>
    );
  }

  // ── Imagem ─────────────────────────────────────────────────────────────────
  if (document.fileUrl && isImage) {
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

  // ── Áudio ──────────────────────────────────────────────────────────────────
  if (document.fileUrl && isAudio) {
    return (
      <div className="center-viewer audio-viewer">
        <div className="viewer-toolbar">
          <span className="doc-type-badge">{document.type}</span>
          <span className="doc-name-label">{document.name}</span>
          {document.content && <span className="toolbar-hint">Selecione o texto para citar</span>}
          <a href={document.fileUrl} target="_blank" rel="noopener noreferrer" className="toolbar-btn" style={{ marginLeft: document.content ? '10px' : 'auto' }}>
            ↗ Baixar
          </a>
        </div>
        <div className="audio-container" onMouseUp={handleMouseUp}>
          <div className="audio-player-section">
            <div className="audio-icon-wrapper">🎧</div>
            <audio controls src={document.fileUrl} className="doc-audio">
              Seu navegador não suporta a reprodução de áudio.
            </audio>
          </div>
          {document.content && (
            <div className="audio-transcription">
              <h4 className="transcription-title">Transcrição</h4>
              <div className="text-body">
                {document.content.split('\n').map((line, i) => <p key={i}>{line || <br />}</p>)}
              </div>
            </div>
          )}
        </div>
        {tooltip && (
          <div className="selection-tooltip" style={{ left: tooltip.x, top: tooltip.y }}>
            <button onClick={handleCite}>💬 Citar no chat</button>
          </div>
        )}
      </div>
    );
  }

  // ── PDF via iframe ─────────────────────────────────────────────────────────
  if (document.fileUrl && isPdf) {
    return (
      <div className="center-viewer pdf-viewer">
        <div className="viewer-toolbar">
          <span className="doc-type-badge">{document.type}</span>
          <span className="doc-name-label">{document.name}</span>
          <a href={document.fileUrl} target="_blank" rel="noopener noreferrer" className="toolbar-btn">
            ↗ Abrir
          </a>
        </div>
        <iframe src={document.fileUrl} title={document.name} className="pdf-iframe" />
      </div>
    );
  }

  // ── Texto (txt/md ou fallback sem fileUrl) ─────────────────────────────────
  const textContent = document.content || '';
  return (
    <div className="center-viewer text-viewer">
      <div className="viewer-toolbar">
        <span className="doc-type-badge">{document.type}</span>
        <span className="doc-name-label">{document.name}</span>
        <span className="toolbar-hint">Selecione texto para citar no chat</span>
      </div>
      <div className="text-content" onMouseUp={handleMouseUp}>
        <div className="text-body">
          {textContent
            ? textContent.split('\n').map((line, i) => <p key={i}>{line || <br />}</p>)
            : <p className="no-content">Conteúdo não disponível.</p>
          }
        </div>
      </div>
      {tooltip && (
        <div className="selection-tooltip" style={{ left: tooltip.x, top: tooltip.y }}>
          <button onClick={handleCite}>💬 Citar no chat</button>
        </div>
      )}
    </div>
  );
}

export default CenterViewer;
