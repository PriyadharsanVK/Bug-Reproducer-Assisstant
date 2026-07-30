import Head from 'next/head';
import dynamic from 'next/dynamic';
import React, { useState } from 'react';
import { useSoundFX } from '../hooks/useSoundFX';
import { HologramCard } from '../components/HologramCard';

// Load Three.js canvas client-side only (no SSR)
const Scene3D = dynamic(
  () => import('../components/Scene3D').then((m) => m.Scene3D),
  { ssr: false }
);

export default function Home() {
  const [title,   setTitle]   = useState('');
  const [body,    setBody]    = useState('');
  const [logs,    setLogs]    = useState('');
  const [runId,   setRunId]   = useState('');
  const [loading, setLoading] = useState(false);
  const { playClick, playSubmit, playSuccess, playHover } = useSoundFX();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    playSubmit();
    setLoading(true);
    setRunId('');
    try {
      const ingestRes = await fetch('http://localhost:8000/issues/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source: 'manual', title, body, raw_logs: logs }),
      });
      const issueData = await ingestRes.json();

      const runRes = await fetch('http://localhost:8000/analysis/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ issue_id: issueData.issue_id, auto_execute_sandbox: true }),
      });
      const runData = await runRes.json();
      setRunId(runData.run_id);
      playSuccess();
    } catch (err) {
      alert('Error: ' + err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>BUG REPRODUCER // AI CORE</title>
        <meta name="description" content="AI-powered automated bug reproduction and root-cause analysis" />
        <meta name="theme-color" content="#010408" />
      </Head>

      {/* ── 3D Canvas Background ── */}
      <Scene3D />

      <div className="page-wrapper">
        {/* ── Navbar ── */}
        <nav className="navbar">
          <div className="navbar-logo">
            <div className="navbar-hex">🐛</div>
            <span className="navbar-title">Bug Reproducer</span>
          </div>
          <div className="navbar-right">
            <span className="navbar-status">
              <span className="navbar-status-dot" />
              SYS ONLINE
            </span>
            <span className="navbar-version">v1.0.0</span>
          </div>
        </nav>

        {/* ── Main ── */}
        <main className="page-content">
          {/* Hero */}
          <section className="hero">
            <div className="hero-sys-label">
              <span className="sys-label-dot" />
              NEURAL CORE ACTIVE // AUTONOMOUS BUG ANALYSIS ENGINE
            </div>

            <h1 className="hero-title">
              REPRODUCE BUGS WITH{' '}
              <span className="neon-text" data-text="AI PRECISION">
                AI PRECISION
              </span>
            </h1>

            <p className="hero-subtitle">
              Submit a GitHub issue or raw stack trace. The agent ingests, sandboxes,
              reproduces and delivers a root-cause report — autonomously.
            </p>

            <div className="feature-row">
              {['⚡ AUTO SANDBOX', '🔍 ROOT CAUSE AI', '📊 CONFIDENCE SCORE', '🤖 SWE-AGENT CORE', '🔒 ISOLATED ENV'].map((f) => (
                <span key={f} className="feature-chip">{f}</span>
              ))}
            </div>
          </section>

          {/* Form card */}
          <HologramCard>
            <div className="section-label">// ISSUE INGEST INTERFACE</div>
            <h2 className="section-heading">Submit Issue</h2>
            <p className="section-sub">
              Provide issue details. The agent will isolate, reproduce and analyse in a secure sandbox environment.
            </p>

            <form onSubmit={handleSubmit}>
              {/* Title */}
              <div className="form-group">
                <label className="form-label">
                  ▸ ISSUE TITLE
                </label>
                <input
                  className="cyber-input"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="KeyError in auth token creation when scope=[]"
                  required
                />
              </div>

              {/* Body */}
              <div className="form-group">
                <label className="form-label">▸ ISSUE DESCRIPTION</label>
                <textarea
                  className="cyber-textarea"
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                  placeholder={`Sending scope=[] to POST /auth/token crashes the server.\n\n1. Call POST /auth/token with {"scope":[]}\n2. Server returns 500`}
                  required
                />
              </div>

              {/* Logs */}
              <div className="form-group">
                <label className="form-label">
                  ▸ RAW STACK TRACE
                  <span className="form-optional">— OPTIONAL</span>
                </label>
                <textarea
                  className="cyber-textarea"
                  value={logs}
                  onChange={(e) => setLogs(e.target.value)}
                  placeholder={`Traceback (most recent call last):\n  File "app.py", line 42, in create_token\n    scope = scopes[0]\nKeyError: 0`}
                />
                <p className="form-hint">// PASTE TRACEBACKS, LOG LINES OR ERROR MESSAGES</p>
              </div>

              <div className="cyber-divider" />

              <button
                type="submit"
                disabled={loading}
                className="btn-cyber"
                onMouseEnter={playHover}
              >
                {loading ? (
                  <>
                    <div className="spinner" />
                    INGESTING &amp; ANALYSING...
                  </>
                ) : (
                  <>
                    <span>⬡</span>
                    EXECUTE ANALYSIS
                  </>
                )}
              </button>
            </form>

            {/* Success result */}
            {runId && (
              <div className="success-panel">
                <div className="success-panel-header">
                  <div className="success-icon-box">✓</div>
                  <span className="success-label">ANALYSIS DISPATCHED</span>
                </div>
                <div className="run-id-row">
                  <span className="run-id-key">RUN_ID</span>
                  <span className="run-id-val">{runId}</span>
                </div>
                <a
                  href={`/analysis/${runId}`}
                  className="btn-view"
                  onMouseEnter={playHover}
                  onClick={playClick}
                >
                  ▶ VIEW LIVE ANALYSIS REPORT
                </a>
              </div>
            )}
          </HologramCard>

          {/* Footer */}
          <div style={{ textAlign: 'center', marginTop: 48 }}>
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, letterSpacing: '0.1em', color: 'rgba(0,255,255,0.25)' }}>
              // POWERED BY{' '}
              <a href="https://swe-agent.com" target="_blank" rel="noreferrer" style={{ color: 'rgba(0,255,255,0.5)' }}>
                SWE-AGENT
              </a>
              {' '} // PRINCETON &amp; STANFORD RESEARCH
            </p>
          </div>
        </main>
      </div>
    </>
  );
}
