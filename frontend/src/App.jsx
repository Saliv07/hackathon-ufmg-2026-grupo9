import { useState, useEffect } from 'react';
import './App.css';
import TopBar from './components/TopBar';
import SidebarLeft from './components/SidebarLeft';
import CenterViewer from './components/CenterViewer';
import SidebarRight from './components/SidebarRight';
import Dashboard from './components/Dashboard';
import CaseSelection from './components/CaseSelection';
import CaseSummary from './components/CaseSummary';
import CaseConclusion from './components/CaseConclusion';
import GlobalSidebar from './components/GlobalSidebar';
import LoginScreen from './components/LoginScreen';
import DataExplorer from './components/DataExplorer';
import SettingsModal from './components/SettingsModal';
import SearchOverlay from './components/SearchOverlay';

const BACKEND = '';
const API_URL = '/api';

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
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [currentView, setCurrentView] = useState('case-selection');
  const [selectedCase, setSelectedCase] = useState(null);
  const [caseDocuments, setCaseDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [docsWidth, setDocsWidth] = useState(260);
  const [viewerWidth, setViewerWidth] = useState(600);
  const [openDocuments, setOpenDocuments] = useState([]);
  const [activeDocumentId, setActiveDocumentId] = useState(null);
  const [chatHistories, setChatHistories] = useState(() => {
    try {
      const saved = localStorage.getItem('juridico-chat-histories');
      return saved ? JSON.parse(saved) : {};
    } catch { return {}; }
  });

  const [customDocs, setCustomDocs] = useState(() => {
    try {
      const saved = localStorage.getItem('juridico-custom-docs');
      return saved ? JSON.parse(saved) : {};
    } catch { return {}; }
  });

  const [workspaceSessions, setWorkspaceSessions] = useState(() => {
    try {
      const saved = localStorage.getItem('juridico-workspace-sessions');
      return saved ? JSON.parse(saved) : {};
    } catch { return {}; }
  });

  const [showSettings, setShowSettings] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [hasNewNotification, setHasNewNotification] = useState(false);
  const [pendingQuote, setPendingQuote] = useState('');

  const [settings, setSettings] = useState(() => {
    try {
      const saved = localStorage.getItem('juridico-ai-settings');
      return saved ? JSON.parse(saved) : { aiModel: 'gpt-4.1-mini', darkMode: true, temperature: 0.3 };
    } catch {
      return { aiModel: 'gpt-4.1-mini', darkMode: true };
    }
  });

  useEffect(() => {
    localStorage.setItem('juridico-ai-settings', JSON.stringify(settings));
    document.documentElement.setAttribute('data-theme', settings.darkMode ? 'dark' : 'light');
  }, [settings]);

  useEffect(() => {
    localStorage.setItem('juridico-chat-histories', JSON.stringify(chatHistories));
  }, [chatHistories]);

  useEffect(() => {
    localStorage.setItem('juridico-custom-docs', JSON.stringify(customDocs));
  }, [customDocs]);

  useEffect(() => {
    localStorage.setItem('juridico-workspace-sessions', JSON.stringify(workspaceSessions));
  }, [workspaceSessions]);

  useEffect(() => {
    fetch(`${API_URL}/cases`)
      .then(res => res.json())
      .then(data => { setCases(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  // Atalho Ctrl+K para busca
  useEffect(() => {
    const handleK = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setIsSearchOpen(true);
      }
    };
    window.addEventListener('keydown', handleK);
    return () => window.removeEventListener('keydown', handleK);
  }, []);

  // Enriquece documentos do caso com fileUrl apontando para o backend
  const enrichDocs = (caseData) =>
    caseData.documents.map(doc => ({
      ...doc,
      fileUrl: `${BACKEND}/api/cases/${caseData.id}/documents/${doc.id}/file`,
    }));

  const handleSelectCase = (caseData) => {
    const baseDocs = enrichDocs(caseData);
    const caseCustomDocs = customDocs[caseData.id] || [];
    const allDocs = [...baseDocs, ...caseCustomDocs];
    
    setSelectedCase(caseData);
    setCaseDocuments(allDocs);

    const savedSession = workspaceSessions[caseData.id];
    if (savedSession) {
      // Filtra documentos salvos para garantir que ainda existem
      const validOpenIds = savedSession.openDocumentIds || [];
      const restoredOpen = allDocs.filter(d => validOpenIds.includes(d.id));
      
      if (restoredOpen.length > 0) {
        setOpenDocuments(restoredOpen);
        const activeDoc = allDocs.find(d => d.id === savedSession.activeDocumentId) || restoredOpen[0];
        setActiveDocumentId(activeDoc.id);
        setSelectedDocument(activeDoc);
      } else {
        const firstDoc = allDocs[0];
        setOpenDocuments([firstDoc]);
        setActiveDocumentId(firstDoc.id);
        setSelectedDocument(firstDoc);
      }
      // Sempre volta para o sumário ao selecionar um caso pelo menu lateral
      setCurrentView('case-summary');
    } else {
      const firstDoc = allDocs[0];
      setOpenDocuments([firstDoc]);
      setActiveDocumentId(firstDoc.id);
      setSelectedDocument(firstDoc);
      setCurrentView('case-summary');
    }

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
  };

  // Salva sessão do workspace sempre que mudar documentos abertos ou ativos
  useEffect(() => {
    if (selectedCase) {
      setWorkspaceSessions(prev => ({
        ...prev,
        [selectedCase.id]: {
          openDocumentIds: openDocuments.map(d => d.id),
          activeDocumentId: activeDocumentId,
          currentView: currentView
        }
      }));
    }
  }, [openDocuments, activeDocumentId, currentView, selectedCase]);

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

  const handleDeleteDocument = (docId) => {
    if (!selectedCase) return;
    
    // Remove from customDocs (localStorage)
    setCustomDocs(prev => {
      const caseDocs = prev[selectedCase.id] || [];
      return {
        ...prev,
        [selectedCase.id]: caseDocs.filter(d => d.id !== docId)
      };
    });

    // Remove from active state lists
    setCaseDocuments(prev => prev.filter(d => d.id !== docId));
    
    // Close the tab if it's open
    handleCloseDocument(docId);
  };

  const handleUploadDocument = (newDoc) => {
    const enriched = newDoc.fileUrl?.startsWith('/api/')
      ? { ...newDoc, fileUrl: `${BACKEND}${newDoc.fileUrl}` }
      : newDoc;
    
    if (selectedCase) {
      setCustomDocs(prev => ({
        ...prev,
        [selectedCase.id]: [...(prev[selectedCase.id] || []), enriched]
      }));
    }

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

    if (selectedCase) {
      setCustomDocs(prev => ({
        ...prev,
        [selectedCase.id]: [...(prev[selectedCase.id] || []), note]
      }));
    }

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

    // Persiste alteração em documentos customizados (notas)
    if (selectedCase) {
      setCustomDocs(prev => ({
        ...prev,
        [selectedCase.id]: (prev[selectedCase.id] || []).map(d => d.id === docId ? { ...d, content: newContent } : d)
      }));
    }
  };

  const handleProceedToWorkspace = () => setCurrentView('workspace');

  // Auto-hide the global sidebar when entering the workspace
  useEffect(() => {
    if (currentView === 'workspace') {
      setIsSidebarCollapsed(true);
    }
  }, [currentView]);

  const renderView = () => {
    if (loading) return <div className="loading-screen">Carregando dados do servidor Python...</div>;
    if (currentView === 'case-selection') return <CaseSelection onSelectCase={handleSelectCase} cases={cases} />;
    if (currentView === 'case-summary') return <CaseSummary caseData={selectedCase} onProceed={handleProceedToWorkspace} />;
    if (currentView === 'dashboard') return <Dashboard />;
    if (currentView === 'data-explorer') return <DataExplorer />;

    if (currentView === 'case-conclusion') {
      return (
        <CaseConclusion
          caseData={selectedCase}
          onBack={() => setCurrentView('case-summary')}
          onComplete={(feedback) => {
            console.log('Caso concluído!', selectedCase.id, feedback);
            // Poderia adicionar o caso aos completedCases aqui
            setCurrentView('case-selection');
          }}
        />
      );
    }

    if (currentView === 'workspace') {
      return (
        <div className="main-content slide-in-right">
          {/* Coluna: lista de documentos */}
          <div className="resizable-docs" style={{ width: `${docsWidth}px`, flexShrink: 0 }}>
            <SidebarLeft
              documents={caseDocuments}
              selectedDocument={selectedDocument}
              onSelectDocument={handleSelectDocument}
              onUploadDocument={handleUploadDocument}
              onCreateNote={handleCreateNote}
              onDeleteDocument={handleDeleteDocument}
            />
          </div>

          <div className="resizer-bar" onMouseDown={(e) => {
            e.preventDefault();
            const target = e.currentTarget;
            target.classList.add('active');
            document.body.classList.add('resizing-active');
            const startX = e.clientX;
            const startW = docsWidth;
            const onMouseMove = (ev) => {
              const newW = Math.max(160, Math.min(450, startW + ev.clientX - startX));
              setDocsWidth(newW);
            };
            const onMouseUp = () => {
              target.classList.remove('active');
              document.body.classList.remove('resizing-active');
              document.removeEventListener('mousemove', onMouseMove);
              document.removeEventListener('mouseup', onMouseUp);
            };
            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
          }} />

          {/* Coluna: visualizador com abas */}
          <div className="resizable-viewer" style={{ width: `${viewerWidth}px`, flexShrink: 0 }}>
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
              onQuoteText={(text) => setPendingQuote(text)}
            />
          </div>

          <div className="resizer-bar" onMouseDown={(e) => {
            e.preventDefault();
            const target = e.currentTarget;
            target.classList.add('active');
            document.body.classList.add('resizing-active');
            const startX = e.clientX;
            const startW = viewerWidth;
            const onMouseMove = (ev) => {
              const maxAvailable = window.innerWidth - docsWidth - 350; // min 350 for chat
              const newW = Math.max(300, Math.min(maxAvailable, startW + ev.clientX - startX));
              setViewerWidth(newW);
            };
            const onMouseUp = () => {
              target.classList.remove('active');
              document.body.classList.remove('resizing-active');
              document.removeEventListener('mousemove', onMouseMove);
              document.removeEventListener('mouseup', onMouseUp);
            };
            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
          }} />

          {/* Coluna: chat */}
          <div className="resizable-chat" style={{ flex: 1, minWidth: 320 }}>
            <SidebarRight
              caseData={selectedCase}
              successChance={successChance}
              openDocuments={openDocuments}
              aiModel={settings.aiModel}
              temperature={settings.temperature ?? 0.3}
              messages={chatHistories[selectedCase?.id] || []}
              onUpdateMessages={(msgs) => setChatHistories(prev => ({ ...prev, [selectedCase.id]: msgs }))}
              onAgentReply={() => setHasNewNotification(true)}
              pendingQuote={pendingQuote}
              onQuoteClear={() => setPendingQuote('')}
            />
          </div>
        </div>
      );
    }
  };

  const handleLogin = () => {
    setIsLoggedIn(true);
    try { localStorage.setItem('enter-logged-in', 'true'); } catch {}
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setCurrentView('case-selection');
    setSelectedCase(null);
    try { localStorage.removeItem('enter-logged-in'); } catch {}
  };

  if (!isLoggedIn) {
    return <LoginScreen onLogin={handleLogin} />;
  }

  return (
    <div className="app-shell">
      <TopBar
        successChance={successChance}
        currentView={currentView}
        onNavigate={view => setCurrentView(view)}
        onOpenSearch={() => setIsSearchOpen(true)}
        hasNewNotification={hasNewNotification}
        onClearNotification={() => setHasNewNotification(false)}
        onConcluir={() => setCurrentView('case-conclusion')}
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
          onLogout={handleLogout}
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

      {isSearchOpen && (
        <SearchOverlay
          cases={cases}
          selectedCase={selectedCase}
          onClose={() => setIsSearchOpen(false)}
          onSelectCase={handleSelectCase}
        />
      )}
    </div>
  );
}

export default App;
