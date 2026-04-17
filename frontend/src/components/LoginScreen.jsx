import { useState, useEffect, useRef } from 'react';
import './LoginScreen.css';

const BOOT_LINES = [
  { t: 0,    text: 'auth: credenciais validadas',     dim: 'silva@enter.ai' },
  { t: 200,  text: 'session: token emitido',          dim: 'jwt · expires 8h' },
  { t: 450,  text: 'enteros: conectando workspace',   dim: '2 escritórios · 6 casos ativos' },
  { t: 700,  text: 'agents: carregando modelo',       dim: 'gpt-4o · temp 0.3' },
  { t: 950,  text: 'policy: política de acordos v2.1', dim: 'Banco UFMG' },
  { t: 1200, text: 'ready. bem-vindo, Silva.',         dim: '' },
];

function LoginScreen({ onLogin }) {
  const [pressed, setPressed] = useState(false);
  const [booting, setBooting] = useState(false);
  const [email, setEmail] = useState('silva@enter.ai');
  const [password, setPassword] = useState('••••••••••');
  const timerRef = useRef(null);
  const bootingRef = useRef(false);

  const trigger = () => {
    if (bootingRef.current) return;
    bootingRef.current = true;
    setPressed(true);
    setTimeout(() => setBooting(true), 180);
    timerRef.current = setTimeout(() => onLogin(), 2200);
  };

  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'Enter') { e.preventDefault(); trigger(); }
    };
    window.addEventListener('keydown', handler);
    return () => {
      window.removeEventListener('keydown', handler);
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  return (
    <div className="login-screen fade-in">
      <div className="login-corner tl">enterOS · v2.1.0</div>
      <div className="login-corner tr">hackathon-ufmg-2026</div>
      <div className="login-corner bl">© enter.ai — enterprise ai</div>
      <div className="login-corner br">
        <span className="login-status-dot" />
        <span>systems · operational</span>
      </div>

      {!booting && (
        <div className="login-card">
          <div className="login-wordmark">
            ENTER<span className="caret" />
          </div>
          <div className="login-tagline">
            ENTERPRISE&nbsp;AI<span className="sep">·</span>JURIDICAL&nbsp;OS
          </div>

          <div className="login-form">
            <div className="login-field">
              <label>email</label>
              <input value={email} onChange={e => setEmail(e.target.value)} />
            </div>
            <div className="login-field">
              <label>senha</label>
              <input type="password" value={password} onChange={e => setPassword(e.target.value)} />
            </div>
          </div>

          <div className="enter-key-wrap">
            <button
              className={`enter-key ${pressed ? 'pressed' : ''}`}
              onClick={trigger}
              onMouseDown={() => setPressed(true)}
              onMouseUp={() => !booting && setTimeout(() => setPressed(false), 200)}
              onMouseLeave={() => !booting && setPressed(false)}
              aria-label="Entrar"
            >
              <div className="enter-key-shadow" />
              <div className="enter-key-cap">
                <img src="/enter-logo.svg" alt="" className="login-btn-logo" />
                <span>ENTER</span>
              </div>
            </button>
            <div className="enter-key-hint">
              <span>aperte</span>
              <span className="kbd">↵ ENTER</span>
              <span>para iniciar</span>
            </div>
          </div>
        </div>
      )}

      <div className={`boot-overlay ${booting ? 'visible' : ''}`}>
        <div className="boot-lines">
          {booting && BOOT_LINES.map((l, i) => (
            <div key={i} className="boot-line" style={{ animationDelay: `${l.t}ms` }}>
              <span className="ok">✓</span>
              <span>{l.text}</span>
              {l.dim && <span className="dim">— {l.dim}</span>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default LoginScreen;
