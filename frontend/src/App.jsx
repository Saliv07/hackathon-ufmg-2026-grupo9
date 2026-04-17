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

const API_URL = 'http://localhost:5000/api';

function App() {
  const [cases, setCases] = useState([]);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [successChance, setSuccessChance] = useState(85);
  const [currentView, setCurrentView] = useState('case-selection');
  const [selectedCase, setSelectedCase] = useState(null);
  const [caseDocuments, setCaseDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [chatWidth, setChatWidth] = useState(400); // Largura inicial do chat
  const [viewerWidth, setViewerWidth] = useState(600); // Largura inicial do visualizador


  useEffect(() => {
    fetch(`${API_URL}/cases`)
      .then(res => res.json())
      .then(data => {
        setCases(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Erro ao buscar casos:", err);
        setLoading(false);
      });
  }, []);

  const handleSelectCase = (caseData) => {
    setSelectedCase(caseData);
    setCaseDocuments(caseData.documents);
    setSelectedDocument(caseData.documents[0]);
    setSuccessChance(caseData.recommendation === 'DEFESA' ? 95 : 15);
    setCurrentView('case-summary');
  };

  const handleProceedToWorkspace = () => {
    setCurrentView('workspace');
  };

  const renderView = () => {
    if (loading) return <div className="loading-screen">Carregando dados do servidor Python...</div>;

    if (currentView === 'case-selection') {
      return <CaseSelection onSelectCase={handleSelectCase} cases={cases} />;
    }
    if (currentView === 'case-summary') {
      return <CaseSummary caseData={selectedCase} onProceed={handleProceedToWorkspace} />;
    }
    if (currentView === 'dashboard') {
      return <Dashboard caseData={selectedCase || cases[0]} />;
    }
    if (currentView === 'workspace') {
      return (
        <div className="main-content slide-in-right">
          <SidebarLeft 
            documents={caseDocuments} 
            selectedDocument={selectedDocument}
            onSelectDocument={setSelectedDocument} 
          />
          <div 
            className="resizable-viewer" 
            style={{ width: viewerWidth, minWidth: '300px' }}
          >
            <CenterViewer document={selectedDocument} />
          </div>
          
          <div 
            className="resizer-bar" 
            onMouseDown={(e) => {
              const startX = e.clientX;
              const startWidth = viewerWidth;
              const onMouseMove = (moveEvent) => {
                const delta = moveEvent.clientX - startX;
                setViewerWidth(startWidth + delta);
              };
              const onMouseUp = () => {
                document.removeEventListener('mousemove', onMouseMove);
                document.removeEventListener('mouseup', onMouseUp);
              };
              document.addEventListener('mousemove', onMouseMove);
              document.addEventListener('mouseup', onMouseUp);
            }}
          />

          <div 
            className="resizable-chat" 
            style={{ flex: 1, minWidth: '300px' }}
          >
            <SidebarRight caseData={selectedCase} successChance={successChance} />
          </div>
        </div>
      );
    }
  };

  return (
    <div className="layout-container chatgpt-style">
      <GlobalSidebar 
        cases={cases} 
        currentView={currentView} 
        onNavigate={setCurrentView}
        onSelectCase={handleSelectCase}
        isCollapsed={isSidebarCollapsed}
        onToggle={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
      />
      <div className="view-wrapper">
        <TopBar 
          successChance={successChance} 
          currentView={currentView}
          onNavigate={(view) => setCurrentView(view)}
        />
        {renderView()}
      </div>
    </div>
  );
}

export default App;
