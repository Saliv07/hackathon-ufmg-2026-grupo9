import { useState, useRef, useEffect } from 'react';
import { Bot, FileText } from 'lucide-react';
import './SidebarRight.css';

function SidebarRight({ caseData, openDocuments, aiModel, temperature, messages, onUpdateMessages, onAgentReply }) {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg = input;
    const newMessages = [...messages, { role: 'user', content: userMsg, type: 'text' }];
    onUpdateMessages(newMessages);
    setInput('');
    setIsLoading(true);

    try {
      const hostname = window.location.hostname;
      const response = await fetch(`http://${hostname}:5000/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMsg,
          case_context: JSON.stringify(caseData),
          open_documents: openDocuments.map(doc => ({
            title: doc.name || doc.title,
            type: doc.type,
            content: doc.content,
          })),
          model: aiModel || 'gpt-4o',
          temperature: temperature ?? 0.3,
        }),
      });

      const data = await response.json();

      if (data.status === 'success') {
        onUpdateMessages([...newMessages, {
          role: 'agent',
          content: data.analysis,
          type: 'text',
        }]);
        onAgentReply?.();
      } else {
        throw new Error(data.message || 'Falha na análise');
      }
    } catch (error) {
      onUpdateMessages([...newMessages, {
        role: 'agent',
        content: `Erro ao contatar o servidor: ${error.message}`,
        type: 'error',
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const renderContent = (content, type) => {
    return content.split('\n').map((line, i) => {
      if (line.startsWith('### ')) {
        return <h3 key={i}>{line.replace('### ', '')}</h3>;
      }
      if (type === 'case-summary' && i === 1 && line.match(/[0-9.-]+/)) {
        return <span key={i} className="case-number-text">{line}</span>;
      }
      if (line.includes('**')) {
        const parts = line.split('**');
        return (
          <div key={i}>
            {parts.map((part, idx) => idx % 2 === 1 ? <strong key={idx}>{part}</strong> : part)}
          </div>
        );
      }
      if (line.startsWith('Recomendação:')) {
        return <strong key={i}>{line}</strong>;
      }
      return <div key={i}>{line || <br />}</div>;
    });
  };

  return (
    <div className="sidebar-right">
      <div className="agent-header">
        <div className="agent-title">
          <Bot size={16} style={{ color: 'var(--accent-color)' }} />
          Agente Jurídico IA
        </div>
        <span className="agent-model-badge">{aiModel || 'gpt-4o'}</span>
      </div>

      <div className="chat-container">
        {messages.map((msg, index) => (
          <div key={index} className={`message-wrapper ${msg.role}`}>
            <div className={`message-bubble ${msg.type}`}>
              {renderContent(msg.content, msg.type)}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message-wrapper agent">
            <div className="message-bubble info processing">
              <Bot size={16} className="thinking-bot" />
              <span className="loading-dots">O Agente está analisando os documentos</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {openDocuments.length > 0 && (
        <div className="context-strip">
          <span className="context-strip-label">
            <FileText size={11} />
            Contexto ativo:
          </span>
          <div className="context-chips">
            {openDocuments.map(doc => (
              <span key={doc.id} className="context-chip" title={doc.name || doc.title}>
                {doc.name || doc.title}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="chat-input-area">
        <textarea
          placeholder="Pergunte ao agente sobre os documentos abertos..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
        />
        <button className="send-btn" onClick={handleSend} disabled={isLoading}>➤</button>
      </div>
    </div>
  );
}

export default SidebarRight;
