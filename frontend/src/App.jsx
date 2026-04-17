import { useState, useEffect } from 'react';
import './App.css';
import TopBar from './components/TopBar';
import SidebarLeft from './components/SidebarLeft';
import CenterViewer from './components/CenterViewer';
import SidebarRight from './components/SidebarRight';
import Dashboard from './components/Dashboard';
import CaseSelection from './components/CaseSelection';
import CaseSummary from './components/CaseSummary';
import GlobalSidebar from './components/GlobalSidebar';
import SettingsModal from './components/SettingsModal';

const BACKEND = `http://${window.location.hostname}:5000`;
const API_URL = `${BACKEND}/api`;

const TAB_ICONS = {
  'Autos': '⚖️',
  'Subsídio': '📋',
  'Anexo': '📎',
  'Nota': '✏️',
};

function App() {
  const [cases, setCases] = useState([]);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [successChance, setSuccessChance] = useState(85);
  const [currentView, setCurrentView] = useState('case-selection');
  const [selectedCase, setSelectedCase] = useState(null);
  const [caseDocuments, setCaseDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [docsWidth, setDocsWidth] = useState(260);
  const [viewerWidth, setViewerWidth] = useState(600);
  const [openDocuments, setOpenDocuments] = useState([]);
  const [activeDocumentId, setActiveDocumentId] = useState(null);
  const [chatHistories, setChatHistories] = useState({});
  const [showSettings, setShowSettings] = useState(false);
  const [hasNewNotification, setHasNewNotification] = useState(false);

  const [settings, setSettings] = useState(() => {
    try {
      const saved = localStorage.getItem('juridico-ai-settings');
      return saved ? JSON.parse(saved) : { aiModel: 'gpt-4o', darkMode: true };
    } catch {
      return { aiModel: 'gpt-4o', darkMode: true };
    }
  });

  useEffect(() => {
    localStorage.setItem('juridico-ai-settings', JSON.stringify(settings));
    document.documentElement.setAttribute('data-theme', settings.darkMode ? 'dark' : 'light');
  }, [settings]);

  useEffect(() => {
    fetch(`${API_URL}/cases`)
      .then(res => res.json())
      .then(data => { setCases(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  // Enriquece documentos do caso com fileUrl apontando para o backend
  const enrichDocs = (caseData) =>
    caseData.documents.map(doc => ({
      ...doc,
      fileUrl: `${BACKEND}/api/cases/${caseData.id}/documents/${doc.id}/file`,
    }));

  const handleSelectCase = (caseData) => {
    const docs = enrichDocs(caseData);
    setSelectedCase(caseData);
    setCaseDocuments(docs);
    const firstDoc = docs[0];
    setOpenDocuments([firstDoc]);
    setActiveDocumentId(firstDoc.id);
    setSelectedDocument(firstDoc);
    setSuccessChance(caseData.recommendation === 'DEFESA' ? 95 : 15);

    if (!chatHistories[caseData.id]) {
      const initialMessages = [
        {
          role: 'agent',
          content: `### Resumo do Caso: ${caseData.plaintiff}\n${caseData.number}\n\n${caseData.summary}`,
          type: 'case-summary',
        },
        {
          role: 'agent',
          content: `Recomendação: ${caseData.recommendation}\n\n${caseData.suggestion}`,
          type: 'recommendation',
        },
        {
          role: 'agent',
          content: `Olá! Sou o seu Agente Jurídico. O resumo acima foi gerado automaticamente com base nos autos. Como posso ajudar você a analisar este caso hoje?`,
          type: 'text',
        },
      ];
      setChatHistories(prev => ({ ...prev, [caseData.id]: initialMessages }));
    }

    setCurrentView('case-summary');
  };

  const handleSelectDocument = (doc) => {
    if (!openDocuments.find(d => d.id === doc.id)) {
      setOpenDocuments(prev => [...prev, doc]);
    }
    setActiveDocumentId(doc.id);
    setSelectedDocument(doc);
  };

  const handleCloseDocument = (docId) => {
    const newOpenDocs = openDocuments.filter(d => d.id !== docId);
    setOpenDocuments(newOpenDocs);
    if (activeDocumentId === docId) {
      const fallback = newOpenDocs[newOpenDocs.length - 1] ?? null;
      setActiveDocumentId(fallback?.id ?? null);
      setSelectedDocument(fallback);
    }
  };

  const handleUploadDocument = (newDoc) => {
    // Upload: fileUrl é relativa, constrói URL completa
    const enriched = newDoc.fileUrl?.startsWith('/api/')
      ? { ...newDoc, fileUrl: `${BACKEND}${newDoc.fileUrl}` }
      : newDoc;
    setCaseDocuments(prev => [...prev, enriched]);
    setOpenDocuments(prev => [...prev, enriched]);
    setActiveDocumentId(enriched.id);
    setSelectedDocument(enriched);
  };

  const handleCreateNote = () => {
    const noteId = Date.now();
    const now = new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    const note = {
      id: noteId,
      name: `Nota_${now}.txt`,
      type: 'Nota',
      content: '',
      caseNumber: selectedCase?.number || '',
    };
    setCaseDocuments(prev => [...prev, note]);
    setOpenDocuments(prev => [...prev, note]);
    setActiveDocumentId(noteId);
    setSelectedDocument(note);
  };

  const handleDocumentContentChange = (docId, newContent) => {
    const update = docs => docs.map(d => d.id === docId ? { ...d, content: newContent } : d);
    setCaseDocuments(update);
    setOpenDocuments(update);
    setSelectedDocument(prev => prev?.id === docId ? { ...prev, content: newContent } : prev);
  };

  const handleProceedToWorkspace = () => setCurrentView('workspace');

  const renderView = () => {
    if (loading) return <div className="loading-screen">Carregando dados do servidor Python...</div>;
    if (currentView === 'case-selection') return <CaseSelection onSelectCase={handleSelectCase} cases={cases} />;
    if (currentView === 'case-summary') return <CaseSummary caseData={selectedCase} onProceed={handleProceedToWorkspace} />;
    if (currentView === 'dashboard') return <Dashboard caseData={selectedCase || cases[0]} />;

    if (currentView === 'workspace') {
      return (
        <div className="main-content slide-in-right">
          {/* Coluna: lista de documentos */}
          <div className="resizable-docs" style={{ width: docsWidth, minWidth: 150, maxWidth: 500 }}>
            <SidebarLeft
              documents={caseDocuments}
              selectedDocument={selectedDocument}
              onSelectDocument={handleSelectDocument}
              onUploadDocument={handleUploadDocument}
              onCreateNote={handleCreateNote}
            />
          </div>

          <div className="resizer-bar" onMouseDown={(e) => {
            const start = { x: e.clientX, w: docsWidth };
            const move = ev => setDocsWidth(Math.max(150, Math.min(500, start.w + ev.clientX - start.x)));
            const up = () => { document.removeEventListener('mousemove', move); document.removeEventListener('mouseup', up); };
            document.addEventListener('mousemove', move);
            document.addEventListener('mouseup', up);
          }} />

          {/* Coluna: visualizador com abas */}
          <div className="resizable-viewer" style={{ width: viewerWidth, minWidth: 300, maxWidth: 'calc(100% - 550px)' }}>
            <div className="document-tabs">
              {openDocuments.map(doc => (
                <div
                  key={doc.id}
                  className={`doc-tab ${activeDocumentId === doc.id ? 'active' : ''}`}
                  onClick={() => handleSelectDocument(doc)}
                  title={doc.name}
                >
                  <span className="tab-icon">{TAB_ICONS[doc.type] || '📄'}</span>
                  <span className="tab-title">{doc.name}</span>
                  <button className="close-tab" onClick={(e) => { e.stopPropagation(); handleCloseDocument(doc.id); }}>×</button>
                </div>
              ))}
            </div>

            <CenterViewer
              document={selectedDocument}
              onContentChange={handleDocumentContentChange}
            />
          </div>

          <div className="resizer-bar" onMouseDown={(e) => {
            const start = { x: e.clientX, w: viewerWidth };
            const move = ev => setViewerWidth(Math.max(300, start.w + ev.clientX - start.x));
            const up = () => { document.removeEventListener('mousemove', move); document.removeEventListener('mouseup', up); };
            document.addEventListener('mousemove', move);
            document.addEventListener('mouseup', up);
          }} />

          {/* Coluna: chat */}
          <div className="resizable-chat" style={{ flex: 1, minWidth: 300 }}>
            <SidebarRight
              caseData={selectedCase}
              successChance={successChance}
              openDocuments={openDocuments}
              aiModel={settings.aiModel}
              messages={chatHistories[selectedCase?.id] || []}
              onUpdateMessages={(msgs) => setChatHistories(prev => ({ ...prev, [selectedCase.id]: msgs }))}
              onAgentReply={() => setHasNewNotification(true)}
            />
          </div>
        </div>
      );
    }
  };

  return (
    <div className="app-shell">
      <TopBar
        successChance={successChance}
        currentView={currentView}
        onNavigate={view => setCurrentView(view)}
        hasNewNotification={hasNewNotification}
        onClearNotification={() => setHasNewNotification(false)}
      />
      <div className="main-layout">
        <GlobalSidebar
          cases={cases}
          currentView={currentView}
          selectedCase={selectedCase}
          onNavigate={setCurrentView}
          onSelectCase={handleSelectCase}
          isCollapsed={isSidebarCollapsed}
          onToggle={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
          onOpenSettings={() => setShowSettings(true)}
        />
        <div className="view-container">{renderView()}</div>
      </div>

      {showSettings && (
        <SettingsModal
          settings={settings}
          onSave={newSettings => setSettings(newSettings)}
          onClose={() => setShowSettings(false)}
        />
      )}
    </div>
  );
}

export default App;
