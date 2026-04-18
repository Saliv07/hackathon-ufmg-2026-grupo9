import { useRef, useState } from 'react';
import './SidebarLeft.css';

const DOC_ICONS = { 'Autos': '⚖️', 'Subsídio': '📋', 'Anexo': '📎', 'Nota': '✏️' };

function SidebarLeft({ documents, selectedDocument, onSelectDocument, onUploadDocument, onCreateNote }) {
  const fileInputRef = useRef(null);
  const [uploading, setUploading] = useState(false);

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await fetch(`http://${window.location.hostname}:5000/api/upload`, { method: 'POST', body: formData });
      const newDoc = await res.json();
      if (newDoc.id) onUploadDocument(newDoc);
    } catch (err) {
      console.error('Erro ao fazer upload:', err);
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  return (
    <div className="sidebar-left">
      <div className="sidebar-header">
        <h3>Documentos do Processo</h3>
        <div className="header-actions">
          <button className="btn-icon-action" onClick={onCreateNote} title="Nova Nota">✏️</button>
          <button className={`btn-add ${uploading ? 'uploading' : ''}`} onClick={() => fileInputRef.current?.click()} disabled={uploading}>
            {uploading ? '⏳' : '+ Anexar'}
          </button>
        </div>
        <input ref={fileInputRef} type="file" accept=".pdf,.docx,.txt,.png,.jpg,.jpeg,.mp3,.wav,.m4a,.ogg" style={{ display: 'none' }} onChange={handleFileChange} />
      </div>
      <div className="document-list">
        {documents.map((doc) => (
          <div key={doc.id} className={`document-item ${selectedDocument?.id === doc.id ? 'active' : ''}`} onClick={() => onSelectDocument(doc)} title={doc.name}>
            <div className="doc-icon">{DOC_ICONS[doc.type] || '📄'}</div>
            <div className="doc-info">
              <div className="doc-name">{doc.name}</div>
              <div className="doc-type">{doc.type}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default SidebarLeft;
