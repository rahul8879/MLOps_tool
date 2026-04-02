import React, { useState, useEffect, useCallback } from 'react';
import './App.css';

const BASE_URL = 'http://localhost:8000/api';

// ─── API ──────────────────────────────────────────────────────────────────────

async function apiFetch(path) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} — ${body}`);
  }
  return res.json();
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function fmtTime(ts) {
  if (!ts) return null;
  const ms = ts > 1e12 ? ts : ts * 1000;
  return new Date(ms).toLocaleString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

function duration(start, end) {
  if (!start || !end) return null;
  const s = (end > 1e12 ? end : end * 1000) - (start > 1e12 ? start : start * 1000);
  if (s < 0) return null;
  const sec = Math.floor(s / 1000);
  if (sec < 60) return `${sec}s`;
  if (sec < 3600) return `${Math.floor(sec / 60)}m ${sec % 60}s`;
  return `${Math.floor(sec / 3600)}h ${Math.floor((sec % 3600) / 60)}m`;
}

// ─── Atoms ────────────────────────────────────────────────────────────────────

function Spinner({ size = 20 }) {
  return (
    <span
      className="spinner"
      style={{ width: size, height: size, borderWidth: size > 24 ? 3 : 2 }}
    />
  );
}

function StatusPill({ status }) {
  const map = {
    FINISHED: 'pill-green', RUNNING: 'pill-blue', FAILED: 'pill-red',
    KILLED: 'pill-orange', active: 'pill-green', deleted: 'pill-red',
  };
  return (
    <span className={`pill ${map[status] || 'pill-gray'}`}>
      {status}
    </span>
  );
}

function EmptyState({ icon, title, sub }) {
  return (
    <div className="empty-state">
      <div className="empty-icon">{icon}</div>
      <div className="empty-title">{title}</div>
      {sub && <div className="empty-sub">{sub}</div>}
    </div>
  );
}

function ErrorBanner({ msg, onDismiss }) {
  if (!msg) return null;
  return (
    <div className="error-banner">
      <span className="error-icon">⚠</span>
      <span className="error-text">{msg}</span>
      {onDismiss && <button className="error-dismiss" onClick={onDismiss}>✕</button>}
    </div>
  );
}

// ─── Breadcrumb ───────────────────────────────────────────────────────────────

function Breadcrumb({ experiment, run, onGoExperiments, onGoRuns }) {
  return (
    <nav className="breadcrumb">
      <button
        className={`crumb ${!experiment ? 'crumb-active' : 'crumb-link'}`}
        onClick={onGoExperiments}
      >
        Experiments
      </button>

      {experiment && (
        <>
          <span className="crumb-sep">›</span>
          <button
            className={`crumb ${experiment && !run ? 'crumb-active' : 'crumb-link'}`}
            onClick={onGoRuns}
          >
            {experiment.name}
          </button>
        </>
      )}

      {run && (
        <>
          <span className="crumb-sep">›</span>
          <span className="crumb crumb-active">
            {run.run_name || run.run_id.slice(0, 12) + '…'}
          </span>
        </>
      )}
    </nav>
  );
}

// ─── Run Details ──────────────────────────────────────────────────────────────

function RunDetailsView({ experiment, run }) {
  const [data, setData]     = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    setData(null);
    apiFetch(`/experiments/${experiment.experiment_id}/runs/${run.run_id}`)
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [experiment.experiment_id, run.run_id]);

  const metrics = data?.metrics ? Object.entries(data.metrics) : [];
  const params  = data?.params  ? Object.entries(data.params)  : [];

  return (
    <div className="view-run-details">
      {/* Run header */}
      <div className="run-header-card">
        <div className="run-header-left">
          <div className="run-id-label">Run ID</div>
          <code className="run-id-val">{run.run_id}</code>
        </div>
        <div className="run-header-meta">
          <div className="run-meta-item">
            <span className="run-meta-label">Status</span>
            <StatusPill status={run.status} />
          </div>
          {run.start_time && (
            <div className="run-meta-item">
              <span className="run-meta-label">Started</span>
              <span className="run-meta-val">{fmtTime(run.start_time)}</span>
            </div>
          )}
          {duration(run.start_time, run.end_time) && (
            <div className="run-meta-item">
              <span className="run-meta-label">Duration</span>
              <span className="run-meta-val">{duration(run.start_time, run.end_time)}</span>
            </div>
          )}
        </div>
      </div>

      {loading && (
        <div className="loading-center">
          <Spinner size={28} />
          <span>Fetching run details…</span>
        </div>
      )}
      <ErrorBanner msg={error} />

      {data && (
        <div className="details-columns">
          {/* Metrics */}
          <div className="detail-panel">
            <div className="panel-header">
              <span className="panel-icon">📈</span>
              <span className="panel-title">Metrics</span>
              <span className="panel-count">{metrics.length}</span>
            </div>
            {metrics.length === 0
              ? <EmptyState icon="—" title="No metrics logged" />
              : (
                <div className="kv-list">
                  {metrics.map(([k, v]) => (
                    <div className="kv-row" key={k}>
                      <span className="kv-key">{k}</span>
                      <span className="kv-val metric-val">
                        {typeof v === 'number' ? v.toLocaleString('en', { maximumFractionDigits: 6 }) : String(v)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
          </div>

          {/* Params */}
          <div className="detail-panel">
            <div className="panel-header">
              <span className="panel-icon">⚙️</span>
              <span className="panel-title">Parameters</span>
              <span className="panel-count">{params.length}</span>
            </div>
            {params.length === 0
              ? <EmptyState icon="—" title="No params logged" />
              : (
                <div className="kv-list">
                  {params.map(([k, v]) => (
                    <div className="kv-row" key={k}>
                      <span className="kv-key">{k}</span>
                      <span className="kv-val">{String(v)}</span>
                    </div>
                  ))}
                </div>
              )}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Runs View ────────────────────────────────────────────────────────────────

function RunsView({ experiment, onSelectRun }) {
  const [runs, setRuns]         = useState(null);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);
  const [maxResults, setMaxResults] = useState(20);

  const fetchRuns = useCallback(() => {
    setLoading(true);
    setError(null);
    apiFetch(`/experiments/${experiment.experiment_id}/runs?max_results=${maxResults}`)
      .then(data => setRuns(Array.isArray(data) ? data : data.runs || []))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [experiment.experiment_id, maxResults]);

  useEffect(() => { fetchRuns(); }, [fetchRuns]);

  return (
    <div className="view-runs">
      <div className="view-toolbar">
        <div className="toolbar-left">
          <h2 className="view-title">Runs</h2>
          {runs && <span className="count-badge">{runs.length}</span>}
        </div>
        <div className="toolbar-right">
          <label className="toolbar-label">
            Show
            <select
              className="select-input"
              value={maxResults}
              onChange={e => setMaxResults(Number(e.target.value))}
            >
              {[10, 20, 50, 100].map(n => (
                <option key={n} value={n}>{n}</option>
              ))}
            </select>
            runs
          </label>
          <button className="btn btn-secondary" onClick={fetchRuns} disabled={loading}>
            {loading ? <Spinner size={14} /> : '↻'} Refresh
          </button>
        </div>
      </div>

      <ErrorBanner msg={error} onDismiss={() => setError(null)} />

      {loading && !runs && (
        <div className="loading-center">
          <Spinner size={28} />
          <span>Loading runs…</span>
        </div>
      )}

      {runs && runs.length === 0 && (
        <EmptyState icon="🏃" title="No runs found" sub="This experiment has no recorded runs yet." />
      )}

      {runs && runs.length > 0 && (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Run Name</th>
                <th>Run ID</th>
                <th>Status</th>
                <th>Started</th>
                <th>Duration</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {runs.map(run => (
                <tr key={run.run_id} className="table-row" onClick={() => onSelectRun(run)}>
                  <td className="td-name">{run.run_name || <span className="dim">—</span>}</td>
                  <td><code className="id-chip">{run.run_id.slice(0, 10)}…</code></td>
                  <td><StatusPill status={run.status} /></td>
                  <td className="td-time">{fmtTime(run.start_time) || <span className="dim">—</span>}</td>
                  <td className="td-dur">{duration(run.start_time, run.end_time) || <span className="dim">—</span>}</td>
                  <td className="td-action">
                    <span className="row-action-hint">View details →</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ─── Experiments View ─────────────────────────────────────────────────────────

function ExperimentsView({ onSelectExperiment }) {
  const [experiments, setExperiments] = useState(null);
  const [loading, setLoading]         = useState(false);
  const [error, setError]             = useState(null);
  const [query, setQuery]             = useState('');
  const [searchLoading, setSearchLoading] = useState(false);

  const loadAll = useCallback(() => {
    setLoading(true);
    setError(null);
    apiFetch('/experiments/')
      .then(data => setExperiments(Array.isArray(data) ? data : data.experiments || []))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { loadAll(); }, [loadAll]);

  const handleSearch = e => {
    e.preventDefault();
    if (!query.trim()) { loadAll(); return; }
    setSearchLoading(true);
    setError(null);
    apiFetch(`/experiments/search?name=${encodeURIComponent(query.trim())}`)
      .then(data => setExperiments(Array.isArray(data) ? data : data.experiments || []))
      .catch(e => setError(e.message))
      .finally(() => setSearchLoading(false));
  };

  const busy = loading || searchLoading;

  return (
    <div className="view-experiments">
      <div className="view-toolbar">
        <div className="toolbar-left">
          <h2 className="view-title">Experiments</h2>
          {experiments && <span className="count-badge">{experiments.length}</span>}
        </div>
        <div className="toolbar-right">
          <form className="search-form" onSubmit={handleSearch}>
            <div className="search-box">
              <span className="search-icon">⌕</span>
              <input
                className="search-input"
                type="text"
                placeholder="Search experiments…"
                value={query}
                onChange={e => setQuery(e.target.value)}
              />
              {query && (
                <button type="button" className="search-clear" onClick={() => { setQuery(''); loadAll(); }}>
                  ✕
                </button>
              )}
            </div>
            <button className="btn btn-secondary" type="submit" disabled={busy}>
              {searchLoading ? <Spinner size={14} /> : 'Search'}
            </button>
          </form>
          <button className="btn btn-secondary" onClick={loadAll} disabled={busy}>
            {loading ? <Spinner size={14} /> : '↻'} Refresh
          </button>
        </div>
      </div>

      <ErrorBanner msg={error} onDismiss={() => setError(null)} />

      {busy && !experiments && (
        <div className="loading-center">
          <Spinner size={28} />
          <span>Loading experiments…</span>
        </div>
      )}

      {experiments && experiments.length === 0 && (
        <EmptyState icon="🧪" title="No experiments found" sub="Try a different search query or check your MLflow connection." />
      )}

      {experiments && experiments.length > 0 && (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Experiment ID</th>
                <th>Owner</th>
                <th>Stage</th>
                <th>Created</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {experiments.map(exp => (
                <tr key={exp.experiment_id} className="table-row" onClick={() => onSelectExperiment(exp)}>
                  <td className="td-name">{exp.name}</td>
                  <td><code className="id-chip">{exp.experiment_id}</code></td>
                  <td className="td-owner">{exp.owner_email || <span className="dim">—</span>}</td>
                  <td><StatusPill status={exp.lifecycle_stage} /></td>
                  <td className="td-time">{fmtTime(exp.creation_time) || <span className="dim">—</span>}</td>
                  <td className="td-action">
                    <span className="row-action-hint">View runs →</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ─── App Root ─────────────────────────────────────────────────────────────────

export default function App() {
  const [experiment, setExperiment] = useState(null);
  const [run, setRun]               = useState(null);

  const goExperiments = () => { setExperiment(null); setRun(null); };
  const goRuns        = () => setRun(null);

  const selectExperiment = exp => { setExperiment(exp); setRun(null); };
  const selectRun        = r   => setRun(r);

  return (
    <div className="shell">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="logo-mark">AZ</div>
          <div className="logo-text">
            <div className="logo-product">MLOps MVP</div>
            <div className="logo-sub">Experiment Tracker</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section-label">Workspace</div>
          <button
            className={`nav-item ${!experiment ? 'nav-active' : ''}`}
            onClick={goExperiments}
          >
            <span className="nav-icon">🧪</span> Experiments
          </button>

          {experiment && (
            <button
              className={`nav-item nav-child ${experiment && !run ? 'nav-active' : ''}`}
              onClick={goRuns}
            >
              <span className="nav-icon">🏃</span> Runs
            </button>
          )}

          {run && (
            <button className="nav-item nav-grandchild nav-active">
              <span className="nav-icon">🔬</span> Run Details
            </button>
          )}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-endpoint">
            <div className="endpoint-label">API</div>
            <code className="endpoint-url">{BASE_URL}</code>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="main-wrap">
        <header className="topbar">
          <Breadcrumb
            experiment={experiment}
            run={run}
            onGoExperiments={goExperiments}
            onGoRuns={goRuns}
          />
        </header>

        <main className="content">
          {!experiment && (
            <ExperimentsView onSelectExperiment={selectExperiment} />
          )}
          {experiment && !run && (
            <RunsView experiment={experiment} onSelectRun={selectRun} />
          )}
          {experiment && run && (
            <RunDetailsView experiment={experiment} run={run} />
          )}
        </main>
      </div>
    </div>
  );
}
