import { useState } from 'react';
import { X, Moon, Sun, Cpu } from 'lucide-react';
import './SettingsModal.css';

const AI_MODELS = [
  { id: 'gpt-4o', label: 'GPT-4o', desc: 'Mais capaz — recomendado' },
  { id: 'gpt-4o-mini', label: 'GPT-4o Mini', desc: 'Mais rápido e econômico' },
  { id: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo', desc: 'Legado — resposta básica' },
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
                <div className="model-name">{m.label}</div>
                <div className="model-desc">{m.desc}</div>
              </div>
            ))}
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
