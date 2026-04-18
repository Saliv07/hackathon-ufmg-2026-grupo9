import { useState } from 'react';
import { AlertCircle, ExternalLink } from 'lucide-react';
import './MonitoramentoBanco.css';

const STREAMLIT_URL = `http://${window.location.hostname}:8501`;

export default function MonitoramentoBanco() {
  const [loadError, setLoadError] = useState(false);

  return (
    <div className="monitoramento-view fade-in">
      <div className="monitoramento-header">
        <div className="monitoramento-titulo">
          <span className="monitoramento-eyebrow">ÁREA DO BANCO</span>
          <h2>Monitoramento da política de acordos</h2>
        </div>
        <a
          href={STREAMLIT_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="monitoramento-open-external"
          title="Abrir em uma nova aba"
        >
          <ExternalLink size={14} />
          <span>Abrir em nova aba</span>
        </a>
      </div>

      {loadError ? (
        <div className="monitoramento-error">
          <AlertCircle size={24} />
          <div>
            <strong>Dashboard offline</strong>
            <p>
              Não foi possível carregar o monitoramento em <code>{STREAMLIT_URL}</code>.
              Verifique se o Streamlit está rodando (<code>streamlit run src/monitor/dashboards/app.py</code>).
            </p>
          </div>
        </div>
      ) : (
        <iframe
          src={STREAMLIT_URL}
          title="Monitoramento Banco UFMG"
          className="monitoramento-frame"
          onError={() => setLoadError(true)}
        />
      )}
    </div>
  );
}
