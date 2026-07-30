import { useRouter } from 'next/router';
import Head from 'next/head';
import dynamic from 'next/dynamic';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { HologramCard } from '../../components/HologramCard';
import { useSoundFX } from '../../hooks/useSoundFX';

const Scene3D = dynamic(
  () => import('../../components/Scene3D').then((m) => m.Scene3D),
  { ssr: false }
);

type StatusData = {
  status: string;
  overall_confidence?: number;
  issue_id?: string;
};

type ClarificationQuestion = {
  question_id: string;
  target_field: string;
  question: string;
  options: string[];
};

// Fields that are long-form — use a textarea instead of single-line input
const TEXTAREA_FIELDS = ['stack_trace', 'raw_logs', 'logs', 'body', 'error_log', 'traceback'];

function isTextareaField(target_field: string): boolean {
  return TEXTAREA_FIELDS.some((f) => target_field.toLowerCase().includes(f));
}

function fieldToLabel(target_field: string): string {
  const map: Record<string, string> = {
    error_message:       'What exact error message did you see?',
    stack_trace:         'Paste the full stack trace (if available)',
    runtime_environment: 'What is the runtime environment? (OS, language version, etc.)',
    app_version:         'What version of the app were you running?',
    affected_version:    'Which version first showed this issue?',
    repository_url:      'What is the repository URL?',
    operating_system:    'What operating system are you using?',
    reproduction_steps:  'Can you describe the steps to reproduce this?',
    raw_logs:            'Paste any relevant log output',
  };
  return map[target_field] ?? `Please provide: ${target_field.replace(/_/g, ' ')}`;
}

function statusClass(s: string) {
  return { completed: 'completed', failed: 'failed', running: 'running', needs_input: 'needs_input', pending: 'pending', queued: 'queued' }[s] ?? 'pending';
}

/* ── Confidence Arc ─────────────────────────────────── */
function ConfidenceArc({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const r = 44;
  const circ = 2 * Math.PI * r;
  const fill = (value * circ).toFixed(2);
  const gap  = (circ - parseFloat(fill)).toFixed(2);
  const color = pct >= 70 ? '#00ff41' : pct >= 40 ? '#ffa600' : '#ff0080';
  const glow  = pct >= 70 ? 'var(--glow-green)' : pct >= 40 ? '0 0 8px #ffa600' : 'var(--glow-pink)';

  return (
    <div className="confidence-panel">
      {/* Arc SVG */}
      <div className="arc-wrap">
        <svg width="110" height="110" viewBox="0 0 110 110">
          <circle cx="55" cy="55" r={r} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
          <circle
            cx="55" cy="55" r={r}
            fill="none"
            stroke={color}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={`${fill} ${gap}`}
            style={{ filter: `drop-shadow(0 0 6px ${color})`, transition: 'stroke-dasharray 1s cubic-bezier(0.16,1,0.3,1)' }}
          />
        </svg>
        <div className="arc-center">
          <span className="arc-pct" style={{ color, textShadow: glow }}>{pct}</span>
          <span className="arc-unit">%</span>
        </div>
      </div>

      {/* Detail */}
      <div className="confidence-detail">
        <div className="confidence-bar-label">REPRODUCTION CONFIDENCE INDEX</div>
        <div className="confidence-track">
          <div
            className="confidence-fill"
            style={{ width: `${pct}%`, background: color, color, boxShadow: glow }}
          />
        </div>
        <div className="confidence-verdict" style={{ color }}>
          {pct >= 70 ? '◆ HIGH CONFIDENCE — BUG SUCCESSFULLY REPRODUCED'
           : pct >= 40 ? '◈ MEDIUM CONFIDENCE — PARTIAL REPRODUCTION'
           :             '◇ LOW CONFIDENCE — UNABLE TO RELIABLY REPRODUCE'}
        </div>
      </div>
    </div>
  );
}

/* ── Clarification Panel ────────────────────────────── */
interface ClarificationPanelProps {
  runId: string;
  questions: ClarificationQuestion[];
  onSubmitted: () => void;
  soundFX: ReturnType<typeof useSoundFX>;
}

function ClarificationPanel({ runId, questions, onSubmitted, soundFX }: ClarificationPanelProps) {
  const { playClick, playHover } = soundFX;
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');

  const handleChange = (questionId: string, value: string) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
  };

  const handleSubmit = async () => {
    // Require all questions to have an answer
    const unanswered = questions.filter((q) => !answers[q.question_id]?.trim());
    if (unanswered.length > 0) {
      setSubmitError(`Please answer all ${unanswered.length} question(s) before submitting.`);
      return;
    }

    setSubmitting(true);
    setSubmitError('');
    playClick();

    // Build the payload matching ClarificationSubmitRequest exactly:
    // { answers: [{ question_id, target_field, answer }] }
    const payload = {
      answers: questions.map((q) => ({
        question_id: q.question_id,
        target_field: q.target_field,
        answer: answers[q.question_id] ?? '',
      })),
    };

    try {
      const res = await fetch(`http://localhost:8000/analysis/${runId}/clarifications`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setSubmitError(err.detail ?? `Server error (${res.status})`);
        setSubmitting(false);
        return;
      }
      // Success — parent polling loop will pick up the new status
      setAnswers({});
      onSubmitted();
    } catch (e) {
      setSubmitError('Network error — please try again.');
      setSubmitting(false);
    }
  };

  return (
    <div className="clarification-panel">
      {/* Header */}
      <div className="clarification-header">
        <div className="clarification-icon">◈</div>
        <div>
          <div className="clarification-title">Awaiting Your Input</div>
          <div className="clarification-subtitle">
            The confidence score is too low to generate a reliable report.
            Answer the questions below so the pipeline can re-analyse with fuller context.
          </div>
        </div>
      </div>

      <div className="clarification-divider" />

      {/* Questions */}
      {questions.map((q, idx) => {
        const label = fieldToLabel(q.target_field);
        const useTextarea = isTextareaField(q.target_field);
        return (
          <div key={q.question_id} className="clarification-question-row">
            <div className="clarification-q-label">
              <span className="clarification-q-counter">{idx + 1}</span>
              {label}
            </div>
            {useTextarea ? (
              <textarea
                className="cyber-textarea cyber-textarea--violet"
                placeholder={`e.g. Traceback (most recent call last):\n  File "services/token.py", line 88 …`}
                rows={5}
                value={answers[q.question_id] ?? ''}
                onChange={(e) => handleChange(q.question_id, e.target.value)}
              />
            ) : (
              <input
                type="text"
                className="cyber-input cyber-input--violet"
                placeholder={`Enter ${q.target_field.replace(/_/g, ' ')}…`}
                value={answers[q.question_id] ?? ''}
                onChange={(e) => handleChange(q.question_id, e.target.value)}
              />
            )}
          </div>
        );
      })}

      {/* Submit */}
      <div className="clarification-submit-row">
        <button
          className="btn-cyber btn-cyber-violet"
          style={{ width: 'auto', padding: '12px 32px' }}
          disabled={submitting}
          onMouseEnter={playHover}
          onClick={handleSubmit}
        >
          {submitting ? (
            <>
              <div className="spinner" style={{ borderTopColor: 'var(--violet)', borderColor: 'rgba(191,95,255,0.2)' }} />
              SUBMITTING…
            </>
          ) : (
            '◈ SUBMIT ANSWERS'
          )}
        </button>
        <span className="clarification-submit-hint">
          // pipeline will re-run automatically after submission
        </span>
      </div>

      {submitError && (
        <div className="clarification-error">⚠ {submitError}</div>
      )}
    </div>
  );
}

/* ── Main Page ──────────────────────────────────────── */
export default function AnalysisView() {
  const router = useRouter();
  const { id } = router.query;

  const [statusData,      setStatusData]      = useState<StatusData | null>(null);
  const [reportMd,        setReportMd]        = useState('');
  const [reportJson,      setReportJson]      = useState<any>(null);
  const [clarifications,  setClarifications]  = useState<ClarificationQuestion[]>([]);
  const [activeTab,       setActiveTab]       = useState<'md' | 'json'>('md');
  const [lastTick,        setLastTick]        = useState<Date | null>(null);
  const soundFX = useSoundFX();
  const { playClick, playTab, playHover, playCopy, playDownload } = soundFX;
  const [copied, setCopied] = React.useState<'md' | 'json' | null>(null);
  // Track whether the user just submitted answers — suppresses the "no report" placeholder briefly
  const justSubmittedRef = useRef(false);

  const handleCopy = async (tab: 'md' | 'json') => {
    const text = tab === 'md' ? reportMd : JSON.stringify(reportJson, null, 2);
    try {
      await navigator.clipboard.writeText(text);
      playCopy();
      setCopied(tab);
      setTimeout(() => setCopied(null), 2000);
    } catch { /* clipboard denied */ }
  };

  const handleDownload = (tab: 'md' | 'json') => {
    const text = tab === 'md' ? reportMd : JSON.stringify(reportJson, null, 2);
    const filename = tab === 'md' ? `report-${id}.md` : `report-${id}.json`;
    const mime     = tab === 'md' ? 'text/markdown' : 'application/json';
    const blob = new Blob([text], { type: mime });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url; a.download = filename; a.click();
    URL.revokeObjectURL(url);
    playDownload();
  };

  const fetchData = useCallback(async () => {
    if (!id) return;
    try {
      const res  = await fetch(`http://localhost:8000/analysis/${id}`);
      const data: StatusData = await res.json();
      setStatusData(data);
      setLastTick(new Date());

      if (data.status === 'completed') {
        // Only fetch the report when the run has actually completed
        const [mdRes, jsonRes] = await Promise.all([
          fetch(`http://localhost:8000/analysis/${id}/report.md`),
          fetch(`http://localhost:8000/analysis/${id}/report.json`),
        ]);
        if (mdRes.ok)   setReportMd(await mdRes.text());
        if (jsonRes.ok) setReportJson(await jsonRes.json());
        setClarifications([]); // clear any stale questions
      } else if (data.status === 'needs_input') {
        // Fetch the pending clarification questions
        const clariRes = await fetch(`http://localhost:8000/analysis/${id}/clarifications`);
        if (clariRes.ok) {
          const clariData = await clariRes.json();
          setClarifications(clariData.questions ?? []);
        }
        // Clear any stale report state from a previous completed run
        setReportMd('');
        setReportJson(null);
      } else {
        // running / queued / failed — clear clarifications
        setClarifications([]);
      }
    } catch (e) { console.error(e); }
  }, [id]);

  useEffect(() => {
    fetchData();
    const iv = setInterval(fetchData, 3000);
    return () => clearInterval(iv);
  }, [fetchData]);

  const handleClarificationSubmitted = () => {
    justSubmittedRef.current = true;
    // Immediate re-fetch to reflect status = running quickly
    fetchData();
  };

  const isActive = statusData ? ['running', 'pending', 'queued'].includes(statusData.status) : false;

  /* ── Loading ── */
  if (!statusData) {
    return (
      <>
        <Scene3D />
        <div className="loading-screen">
          <div className="loading-hex">◎</div>
          <span className="loading-text">// LOADING RUN DATA...</span>
        </div>
      </>
    );
  }

  const sc = statusClass(statusData.status);

  return (
    <>
      <Head>
        <title>ANALYSIS // {id ? String(id).slice(0, 8).toUpperCase() : '---'}</title>
      </Head>

      <Scene3D />

      <div className="page-wrapper">
        {/* ── Navbar ── */}
        <nav className="navbar">
          <div className="navbar-logo">
            <div className="navbar-hex">🐛</div>
            <span className="navbar-title">Analysis Dashboard</span>
          </div>
          <div className="navbar-right">
            {isActive && (
              <div className="live-badge">
                <div className="live-ring" />
                LIVE FEED
              </div>
            )}
            <a
              href="/"
              style={{ fontFamily: 'var(--font-mono)', fontSize: 11, letterSpacing: '0.1em', color: 'rgba(0,255,255,0.45)' }}
              onMouseEnter={playHover}
              onClick={playClick}
            >
              ← NEW ISSUE
            </a>
          </div>
        </nav>

        <main className="page-content">
          {/* Page header */}
          <div style={{ paddingTop: 44, marginBottom: 24 }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, letterSpacing: '0.2em', color: 'rgba(0,255,255,0.4)', marginBottom: 8 }}>
              // ANALYSIS RUN DASHBOARD
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
              <h1 className="section-heading" style={{ margin: 0, fontSize: 22 }}>
                RUN MONITOR
              </h1>
              <span className={`status-badge ${sc}`}>
                <span className="status-dot" />
                {statusData.status.replace(/_/g, ' ').toUpperCase()}
              </span>
            </div>
          </div>

          {/* Meta grid */}
          <div className="meta-grid">
            <div className="meta-cell">
              <div className="meta-key">RUN_ID</div>
              <div className="meta-val" style={{ fontSize: 11, wordBreak: 'break-all' }}>{id}</div>
            </div>
            {statusData.issue_id && (
              <div className="meta-cell">
                <div className="meta-key">ISSUE_ID</div>
                <div className="meta-val">{statusData.issue_id}</div>
              </div>
            )}
            <div className="meta-cell">
              <div className="meta-key">STATUS</div>
              <div className="meta-val" style={{ color: sc === 'completed' ? 'var(--green)' : sc === 'failed' ? 'var(--pink)' : sc === 'needs_input' ? 'var(--violet)' : 'var(--cyan)' }}>
                {statusData.status.toUpperCase()}
              </div>
            </div>
            {lastTick && (
              <div className="meta-cell">
                <div className="meta-key">LAST_TICK</div>
                <div className="meta-val" style={{ fontSize: 11, color: 'rgba(0,255,255,0.4)' }}>
                  {lastTick.toLocaleTimeString()}
                </div>
              </div>
            )}
          </div>

          {/* Confidence arc */}
          {statusData.overall_confidence != null && (
            <ConfidenceArc value={statusData.overall_confidence} />
          )}

          {/* Running alert */}
          {isActive && (
            <div className="cyber-alert info">
              <div className="spinner" style={{ borderTopColor: 'var(--cyan)', borderColor: 'rgba(0,255,255,0.2)' }} />
              <span>
                SANDBOX AGENT ACTIVE — REPRODUCING BUG — AUTO-REFRESHING EVERY 3s
              </span>
            </div>
          )}

          {/* ── Clarification form (needs_input) ── */}
          {statusData.status === 'needs_input' && clarifications.length > 0 && (
            <ClarificationPanel
              runId={String(id)}
              questions={clarifications}
              onSubmitted={handleClarificationSubmitted}
              soundFX={soundFX}
            />
          )}

          {/* needs_input but questions haven't loaded yet */}
          {statusData.status === 'needs_input' && clarifications.length === 0 && (
            <div className="clarification-panel" style={{ textAlign: 'center', padding: '32px' }}>
              <div style={{ color: 'var(--violet)', fontFamily: 'var(--font-mono)', fontSize: 12, letterSpacing: '0.1em' }}>
                <div className="spinner" style={{ borderTopColor: 'var(--violet)', borderColor: 'rgba(191,95,255,0.2)', margin: '0 auto 12px' }} />
                // LOADING CLARIFICATION QUESTIONS…
              </div>
            </div>
          )}

          {/* Report viewer */}
          {reportMd && (
            <HologramCard tilt={6}>
              {/* Tab bar + live indicator */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12, marginBottom: 20 }}>
                <div className="tab-bar">
                  <button
                    className={`tab-btn ${activeTab === 'md' ? 'active' : ''}`}
                    onMouseEnter={playHover}
                    onClick={() => { playTab(); setActiveTab('md'); }}
                  >
                    ▶ MARKDOWN
                  </button>
                  <button
                    className={`tab-btn ${activeTab === 'json' ? 'active' : ''}`}
                    onMouseEnter={playHover}
                    onClick={() => { playTab(); setActiveTab('json'); }}
                  >
                    ⬡ JSON PAYLOAD
                  </button>
                </div>
                {isActive && (
                  <div className="live-badge">
                    <div className="live-ring" />
                    UPDATING LIVE
                  </div>
                )}
              </div>

              {/* Terminal viewer */}
              <div className="terminal-wrap">
                <div className="terminal-bar">
                  <span className="terminal-title">
                    {activeTab === 'md' ? 'report.md' : 'report.json'}
                  </span>
                  <div className="terminal-actions">
                    <span className="terminal-lines">
                      {activeTab === 'md'
                        ? `${reportMd.split('\n').length} LINES`
                        : `${JSON.stringify(reportJson, null, 2).split('\n').length} LINES`}
                    </span>
                    <button
                      className={`btn-terminal-action ${copied === activeTab ? 'btn-terminal-action--copied' : ''}`}
                      onMouseEnter={playHover}
                      onClick={() => handleCopy(activeTab)}
                      title="Copy to clipboard"
                    >
                      {copied === activeTab ? '✓ COPIED' : '⎘ COPY'}
                    </button>
                    <button
                      className="btn-terminal-action btn-terminal-action--dl"
                      onMouseEnter={playHover}
                      onClick={() => { handleDownload(activeTab); }}
                      title={`Download ${activeTab === 'md' ? 'report.md' : 'report.json'}`}
                    >
                      ↓ DOWNLOAD
                    </button>
                  </div>
                </div>
                {activeTab === 'md' ? (
                  <pre className="terminal-body">{reportMd}</pre>
                ) : (
                  <pre className="terminal-body terminal-body-json">
                    {JSON.stringify(reportJson, null, 2)}
                  </pre>
                )}
              </div>
            </HologramCard>
          )}

          {/* No report — only show when genuinely terminal and not needs_input */}
          {!reportMd && !isActive && statusData.status !== 'needs_input' && (
            <HologramCard>
              <div style={{ textAlign: 'center', padding: '40px 0' }}>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: 32, marginBottom: 12, opacity: 0.3 }}>◇</div>
                <div className="section-heading" style={{ fontSize: 14 }}>NO REPORT DATA</div>
                <p style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'rgba(0,255,255,0.3)', marginTop: 6 }}>
                  // Analysis completed without generating a report file
                </p>
              </div>
            </HologramCard>
          )}

          {/* Footer */}
          <div style={{ textAlign: 'center', marginTop: 48 }}>
            <a
              href="/"
              style={{ fontFamily: 'var(--font-mono)', fontSize: 11, letterSpacing: '0.1em', color: 'rgba(0,255,255,0.3)' }}
              onMouseEnter={playHover}
              onClick={playClick}
            >
              // ← SUBMIT NEW ISSUE
            </a>
          </div>
        </main>
      </div>
    </>
  );
}
