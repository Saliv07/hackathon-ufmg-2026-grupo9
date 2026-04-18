import { useState, useRef, useEffect } from 'react';
import { Bot, FileText, X } from 'lucide-react';
import './SidebarRight.css';

function SidebarRight({
  caseData, openDocuments, aiModel, temperature,
  messages, onUpdateMessages, onAgentReply,
  pendingQuote, onQuoteClear,
}) {
  const [input, setInput] = useState('');
  const [quotedText, setQuotedText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Recebe seleção citada do viewer
  useEffect(() => {
    if (pendingQuote) {
      setQuotedText(pendingQuote);
      onQuoteClear?.();
      textareaRef.current?.focus();
    }
  }, [pendingQuote]);

  const buildMessage = () => {
    if (quotedText) return `> "${quotedText}"\n\n${input}`.trim();
    return input.trim();
  };

  const handleSend = async () => {
    const finalMsg = buildMessage();
    if (!finalMsg) return;

    const newMessages = [...messages, { role: 'user', content: finalMsg, type: 'text' }];
    onUpdateMessages(newMessages);
    setInput('');
    setQuotedText('');
    setIsLoading(true);

    try {
      const hostname = window.location.hostname;
      const response = await fetch(`http://${hostname}:5000/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: finalMsg,
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
        onUpdateMessages([...newMessages, { role: 'agent', content: data.analysis, type: 'text' }]);
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
    const processBold = (text) => {
      if (typeof text !== 'string') return text;
      const parts = text.split(/(\*\*.*?\*\*)/g);
      return parts.map((part, i) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return <strong key={i}>{part.slice(2, -2)}</strong>;
        }
        return part;
      });
    };

    return content.split('\n').map((line, i) => {
      const trimmed = line.trim();
      if (!trimmed && i > 0) return <br key={i} />;

      if (line.startsWith('> "')) {
        return <blockquote key={i} className="chat-blockquote">{processBold(line.slice(3, line.endsWith('"') ? -1 : undefined))}</blockquote>;
      }
      
      if (line.startsWith('### ')) {
        return <h3 key={i}>{processBold(line.replace('### ', ''))}</h3>;
      }

      if (type === 'case-summary' && i === 1 && line.match(/[0-9.-]+/)) {
        return <div key={i} className="case-number-text">{line}</div>;
      }

      if (line.startsWith('Recomendação:')) {
        return (
          <div key={i} className="recommendation-header">
            <strong>{processBold(line)}</strong>
          </div>
        );
      }

      return <div key={i} className="content-line">{processBold(line)}</div>;
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

      {/* Contexto ativo */}
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

      {/* Preview do trecho citado */}
      {quotedText && (
        <div className="quote-preview">
          <span className="quote-preview-text">"{quotedText}"</span>
          <button className="quote-dismiss" onClick={() => setQuotedText('')} title="Remover citação">
            <X size={13} />
          </button>
        </div>
      )}

      <div className="chat-input-area">
        <textarea
          ref={textareaRef}
          placeholder="Pergunte ao agente sobre os documentos abertos..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
        />
        <button className="send-btn" onClick={handleSend} disabled={isLoading || (!input.trim() && !quotedText)}>➤</button>
      </div>
    </div>
  );
}

export default SidebarRight;
