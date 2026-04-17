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

  const handleSend = () => {
    if (!input.trim()) return;
    
    const newMessages = [...messages, { role: 'user', content: input, type: 'text' }];
    setMessages(newMessages);
    setInput('');
    
    // Simulate agent response
    setTimeout(() => {
      setMessages([...newMessages, { 
        role: 'agent', 
        content: `Entendido. Analisando sua ponderação com base na Súmula 479 do STJ e nos resultados da comarca de ${caseData.number.split('.')[4] === '10' ? 'São Luís' : 'Manaus'}, mantenho a recomendação técnica. Deseja que eu elabore uma minuta baseada nesta estratégia?`, 
        type: 'text' 
      }]);
    }, 1000);
  };

  return (
    <div className="sidebar-right">
      <div className="agent-header">
        <div className="agent-title">Agente Jurídico IA</div>
        <div className="agent-status">
          <span className="status-dot"></span> Online
        </div>
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
