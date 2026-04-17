import { useState } from 'react';
import { X, Moon, Sun, Cpu, Thermometer } from 'lucide-react';
import './SettingsModal.css';

const AI_MODELS = [
  { id: 'gpt-4.1', label: 'GPT-4.1', desc: '1M tokens — mais capaz, ideal para casos complexos', badge: '1M' },
  { id: 'gpt-4.1-mini', label: 'GPT-4.1 Mini', desc: '1M tokens — rápido e inteligente', badge: '1M' },
  { id: 'gpt-4.1-nano', label: 'GPT-4.1 Nano', desc: '1M tokens — ultra-rápido e econômico', badge: '1M' },
  { id: 'gpt-4o', label: 'GPT-4o', desc: '128K tokens — multimodal robusto' },
  { id: 'gpt-4o-mini', label: 'GPT-4o Mini', desc: '128K tokens — rápido e econômico' },
];

function SettingsModal({ settings, onSave, onClose }) {
  const [local, setLocal] = useState({ ...settings });

  const handleSave = () => {
    onSave(local);
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-panel" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Configurações</h2>
          <button className="modal-close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="modal-section">
          <div className="modal-section-label">
            <Cpu size={14} />
            <span>Modelo de IA</span>
          </div>
          <div className="model-list">
            {AI_MODELS.map(m => (
              <div
                key={m.id}
                className={`model-option ${local.aiModel === m.id ? 'selected' : ''}`}
                onClick={() => setLocal(prev => ({ ...prev, aiModel: m.id }))}
              >
              <div className="model-name">
                  {m.label}
                  {m.badge && <span className="model-context-badge">{m.badge}</span>}
                </div>
                <div className="model-desc">{m.desc}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="modal-section">
          <div className="modal-section-label">
            <Thermometer size={14} />
            <span>Temperatura do Modelo</span>
          </div>
          <div className="temperature-control">
            <div className="temperature-labels">
              <span>Preciso</span>
              <span className="temperature-value">{local.temperature?.toFixed(1) ?? '0.3'}</span>
              <span>Criativo</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={local.temperature ?? 0.3}
              onChange={e => setLocal(prev => ({ ...prev, temperature: parseFloat(e.target.value) }))}
              className="temperature-slider"
            />
            <div className="temperature-desc">
              {(local.temperature ?? 0.3) <= 0.2 && 'Respostas muito precisas e determinísticas'}
              {(local.temperature ?? 0.3) > 0.2 && (local.temperature ?? 0.3) <= 0.5 && 'Equilibrado — recomendado para análise jurídica'}
              {(local.temperature ?? 0.3) > 0.5 && (local.temperature ?? 0.3) <= 0.8 && 'Mais variado — bom para rascunhos e sugestões'}
              {(local.temperature ?? 0.3) > 0.8 && 'Alta criatividade — menos previsível'}
            </div>
          </div>
        </div>

        <div className="modal-section">
          <div className="modal-section-label">
            {local.darkMode ? <Moon size={14} /> : <Sun size={14} />}
            <span>Aparência</span>
          </div>
          <div className="toggle-row">
            <span>Modo escuro</span>
            <button
              className={`toggle-switch ${local.darkMode ? 'on' : 'off'}`}
              onClick={() => setLocal(prev => ({ ...prev, darkMode: !prev.darkMode }))}
              aria-label="Alternar modo escuro"
            >
              <div className="toggle-knob" />
            </button>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn-modal-cancel" onClick={onClose}>Cancelar</button>
          <button className="btn-modal-save" onClick={handleSave}>Salvar</button>
        </div>
      </div>
    </div>
  );
}

export default SettingsModal;
