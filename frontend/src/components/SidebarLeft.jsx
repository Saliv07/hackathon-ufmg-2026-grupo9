import './SidebarLeft.css';

function SidebarLeft({ documents, selectedDocument, onSelectDocument }) {
  return (
    <div className="sidebar-left">
      <div className="sidebar-header">
        <h3>Documentos do Processo</h3>
        <button className="btn-add">Anexar</button>
      </div>
      
      <div className="document-list">
        {documents.map((doc) => (
          <div 
            key={doc.id} 
            className={`document-item ${selectedDocument?.id === doc.id ? 'active' : ''}`}
            onClick={() => onSelectDocument(doc)}
          >
            <div className="doc-icon">📄</div>
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
