import React, { useState } from 'react';
import { Bot, Shield, Handshake, Download, ArrowLeft, Star, Send } from 'lucide-react';
import './CaseConclusion.css';

function CaseConclusion({ caseData, onBack, onComplete }) {
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedbackType, setFeedbackType] = useState(null); // 'defesa' or 'acordo'
  const [rating, setRating] = useState(0);
  const [reason, setReason] = useState('');

  if (!caseData) return null;

  const aiRecommendation = caseData.recommendation || 'DEFESA'; // 'DEFESA' or 'ACORDO'

  const handleDefesaClick = () => {
    if (aiRecommendation === 'DEFESA') {
      onComplete({ action: 'DEFESA', alignedWithAI: true });
    } else {
      setFeedbackType('DEFESA');
      setShowFeedback(true);
    }
  };

  const handleAcordoClick = () => {
    if (aiRecommendation === 'ACORDO') {
      onComplete({ action: 'ACORDO', alignedWithAI: true });
    } else {
      setFeedbackType('ACORDO');
      setShowFeedback(true);
    }
  };

  const handleDownload = () => {
    alert('Iniciando download do pacote .zip com todos os autos e laudos...');
  };

  const handleSubmitFeedback = () => {
    if (rating === 0) {
      alert('Por favor, avalie as sugestões da IA com 1 a 5 estrelas.');
      return;
    }
    if (!reason.trim()) {
      alert('Por favor, deixe uma breve descrição do porquê.');
      return;
    }
    onComplete({ action: feedbackType, alignedWithAI: false, rating, reason });
  };

  return (
    <div className="case-conclusion-container slide-in">
      <div className="conclusion-header">
        <button className="back-btn" onClick={onBack}>
          <ArrowLeft size={20} /> Voltar
        </button>
        <h2>Conclusão de Análise</h2>
        <span className="case-num">{caseData.number} • {caseData.plaintiff}</span>
      </div>

      <div className="conclusion-content">
        {/* IA Recap */}
        <div className="ai-recap-box">
          <div className="ai-recap-header">
            <Bot size={24} />
            <h3>Recapitulação da IA</h3>
          </div>
          <p className="recap-suggestion">
            A Inteligência Artificial indicou que a melhor estratégia é: <strong>{aiRecommendation}</strong>
          </p>
          <p className="recap-detail">{caseData.suggestion}</p>
        </div>

        {!showFeedback ? (
          <div className="action-buttons-grid">
            <button 
              className={`decision-btn ${aiRecommendation === 'DEFESA' ? 'btn-green' : 'btn-red'}`}
              onClick={handleDefesaClick}
            >
              <Shield size={28} />
              <div className="btn-texts">
                <span className="btn-title">Tentar Defesa</span>
                <span className="btn-sub">Contestar o pedido inicial</span>
              </div>
            </button>

            <button 
              className={`decision-btn ${aiRecommendation === 'ACORDO' ? 'btn-green' : 'btn-red'}`}
              onClick={handleAcordoClick}
            >
              <Handshake size={28} />
              <div className="btn-texts">
                <span className="btn-title">Negociação de Acordo</span>
                <span className="btn-sub">Propor valor para acordo</span>
              </div>
            </button>

            <button className="decision-btn btn-neutral" onClick={handleDownload}>
              <Download size={28} />
              <div className="btn-texts">
                <span className="btn-title">Baixar Autos (.zip)</span>
                <span className="btn-sub">Fazer backup local do caso</span>
              </div>
            </button>
          </div>
        ) : (
          <div className="feedback-form-container slide-in-bottom">
            <div className="feedback-header">
              <h3>Divergência da Sugestão da IA</h3>
              <p>Você escolheu <strong>{feedbackType === 'DEFESA' ? 'Tentar Defesa' : 'Negociação de Acordo'}</strong>, mas a IA sugeriu <strong>{aiRecommendation}</strong>.</p>
            </div>
            
            <div className="rating-section">
              <label>Como você avalia a sugestão da plataforma para este caso?</label>
              <div className="stars-container">
                {[1, 2, 3, 4, 5].map(num => (
                  <button 
                    key={num} 
                    className={`star-btn ${rating >= num ? 'active' : ''}`}
                    onClick={() => setRating(num)}
                  >
                    <Star size={32} fill={rating >= num ? 'currentColor' : 'none'} />
                  </button>
                ))}
              </div>
            </div>

            <div className="reason-section">
              <label>Por que você decidiu seguir um caminho diferente?</label>
              <textarea 
                placeholder="Ex: Encontrei jurisprudência recente que favorece nossa tese, apesar do risco operacional..."
                value={reason}
                onChange={e => setReason(e.target.value)}
                rows={4}
              />
            </div>

            <div className="feedback-actions">
              <button className="cancel-feedback-btn" onClick={() => setShowFeedback(false)}>Cancelar</button>
              <button className="submit-feedback-btn" onClick={handleSubmitFeedback}>
                <Send size={18} /> Enviar e Concluir
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default CaseConclusion;
