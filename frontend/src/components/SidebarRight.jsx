import { useState, useRef, useEffect } from 'react';
import './SidebarRight.css';

function SidebarRight({ caseData, successChance }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (caseData) {
      setMessages([
        { 
          role: 'agent', 
          content: `Olá, sou o Agente Jurídico. Analisei os autos e subsídios do caso ${caseData.plaintiff}. A recomendação do sistema é seguir com: ${caseData.recommendation}.`, 
          type: 'recommendation' 
        },
        { 
          role: 'agent', 
          content: `${caseData.suggestion}\n\nFatores de impacto: Probabilidade de êxito atualizada em ${successChance}%.`, 
          type: 'info' 
        }
      ]);
    }
  }, [caseData, successChance]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;
    
    const userMsg = input;
    const newMessages = [...messages, { role: 'user', content: userMsg, type: 'text' }];
    setMessages(newMessages);
    setInput('');
    
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';
      const response = await fetch(`${apiUrl}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMsg,
          case_context: JSON.stringify(caseData)
        })
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        setMessages([...newMessages, { 
          role: 'agent', 
          content: data.analysis, 
          type: 'text' 
        }]);
      } else {
        throw new Error(data.message || 'Falha na análise');
      }
    } catch (error) {
      setMessages([...newMessages, { 
        role: 'agent', 
        content: `Erro ao contatar o servidor: ${error.message}`, 
        type: 'error' 
      }]);
    }
  };

  return (
    <div className="sidebar-right">
      <div className="agent-header">
        <div className="agent-title">Agente Jurídico IA</div>
      </div>
      
      <div className="chat-container">
        {messages.map((msg, index) => (
          <div key={index} className={`message-wrapper ${msg.role}`}>
            <div className={`message-bubble ${msg.type}`}>
              {msg.content}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      
      <div className="chat-input-area">
        <div className="input-actions">
          <button className="icon-btn" title="Anexar arquivo">📎</button>
        </div>
        <textarea 
          placeholder="Pergunte ao agente..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
        />
        <button className="send-btn" onClick={handleSend}>➤</button>
      </div>
    </div>
  );
}

export default SidebarRight;
