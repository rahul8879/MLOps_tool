import React, { useState, useCallback } from 'react';
import './App.css';

const BASE_URL = 'http://localhost:8000/api';

// ─── Utilities ───────────────────────────────────────────────────────────────

function formatTimestamp(ts) {
  if (!ts) return '—';
  // Handle both seconds and milliseconds
  const ms = ts > 1e12 ? ts : ts * 1000;
  return new Date(ms).toLocaleString();
}

function apiFetch(path, token) {
  return fetch(`${BASE_URL}${path}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  }).then(async (res) => {
    if (!res.ok) {
      const body = await res.text();
      throw new Error(`HTTP ${res.status}: ${body}`);
    }
    return res.json();
  });
}

// ─── Sub-components ──────────────────────────────────────────────────────────

function Spinner() {
  return <div className="spinner" aria-label="Loading" />;
}

function ErrorMsg({ message }) {
  if (!message) return null;
  return <div className="error-msg">{message}</div>;
}

function KeyValueCard({ title, data }) {
  const entries = data ? Object.entries(data) : [];
  return (
    <div className="card kv-card">
      <h3 className="card-title">{title}</h3>
      {entries.length === 0 ? (
        <p className="empty-note">No data available.</p>
      ) : (
        <table className="kv-table">
          <thead>
            <tr>
              <th>Key</th>
              <th>Value</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(([key, val]) => (
              <tr key={key}>
                <td className="kv-key">{key}</td>
                <td className="kv-val">{String(val)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

// ─── Section: Token Input ─────────────────────────────────────────────────────

function TokenSection({ token, onSave }) {
  const [draft, setDraft] = useState(token || '');
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    onSave(draft.trim());
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <section className="card token-section">
      <h2 className="section-title">🔑 Databricks PAT Token</h2>
      <p className="section-desc">Paste your Databricks Personal Access Token. It will be sent as a Bearer token on every request.</p>
      <div className="token-row">
        <input
          className="token-input"
          type="password"
          placeholder="dapi••••••••••••••••••••••••••••••••"
          value={draft}
          onChange={(e) => { setDraft(e.target.value); setSaved(false); }}
          onKeyDown={(e) => e.key === 'Enter' && handleSave()}
          spellCheck={false}
        />
        <button className="btn btn-primary" onClick={handleSave}>
          Save Token
        </button>
      </div>
      {saved && <div className="token-saved">✔ Token saved</div>}
    </section>
  );
}

// ─── Section: Run Details ─────────────────────────────────────────────────────

function RunDetailsSection({ experimentId, run, token }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [details, setDetails] = useState(null);

  // Auto-fetch when run changes
  React.useEffect(() => {
    if (!run || !token) return;
    setLoading(true);
    setError(null);
    setDetails(null);
    apiFetch(`/experiments/${experimentId}/runs/${run.run_id}`, token)
      .then((data) => setDetails(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [experimentId, run, token]);

  if (!run) return null;

  return (
    <section className="card details-section">
      <h2 className="section-title">🔬 Run Details</h2>
      <p className="section-desc">
        Run: <strong>{run.run_name || run.run_id}</strong>
        <span className="badge badge-status">{run.status}</span>
      </p>

      {loading && <Spinner />}
      <ErrorMsg message={error} />

      {details && (
        <div className="details-grid">
          <KeyValueCard title="📊 Metrics" data={details.metrics} />
          <KeyValueCard title="⚙️ Params" data={details.params} />
        </div>
      )}
    </section>
  );
}

// ─── Section: Runs ────────────────────────────────────────────────────────────

function RunsSection({ experiment, token, onViewDetails }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [runs, setRuns] = useState(null);
  const [maxResults, setMaxResults] = useState(20);
  const [selectedRun, setSelectedRun] = useState(null);

  const fetchRuns = useCallback(() => {
    if (!token) { setError('Please save a token first.'); return; }
    setLoading(true);
    setError(null);
    setSelectedRun(null);
    apiFetch(`/experiments/${experiment.experiment_id}/runs?max_results=${maxResults}`, token)
      .then((data) => {
        // Normalize: accept array or { runs: [...] }
        setRuns(Array.isArray(data) ? data : data.runs || []);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [experiment, token, maxResults]);

  // Auto-fetch when experiment changes
  React.useEffect(() => {
    if (experiment) fetchRuns();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [experiment]);

  if (!experiment) return null;

  const handleViewDetails = (run) => {
    setSelectedRun(run);
    onViewDetails(run);
  };

  return (
    <>
      <section className="card runs-section">
        <h2 className="section-title">🏃 Runs</h2>
        <p className="section-desc">
          Experiment: <strong>{experiment.name}</strong>
          <span className="experiment-id"> ({experiment.experiment_id})</span>
        </p>

        <div className="runs-controls">
          <label className="input-label">
            Max results
            <input
              className="small-input"
              type="number"
              min={1}
              max={1000}
              value={maxResults}
              onChange={(e) => setMaxResults(Number(e.target.value))}
            />
          </label>
          <button className="btn btn-primary" onClick={fetchRuns} disabled={loading}>
            {loading ? 'Loading…' : 'Reload Runs'}
          </button>
        </div>

        {loading && <Spinner />}
        <ErrorMsg message={error} />

        {runs && runs.length === 0 && (
          <p className="empty-note">No runs found for this experiment.</p>
        )}

        {runs && runs.length > 0 && (
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Run ID</th>
                  <th>Run Name</th>
                  <th>Status</th>
                  <th>Start Time</th>
                  <th>End Time</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {runs.map((run) => (
                  <tr key={run.run_id} className={selectedRun?.run_id === run.run_id ? 'row-selected' : ''}>
                    <td className="mono truncate" title={run.run_id}>{run.run_id}</td>
                    <td>{run.run_name || '—'}</td>
                    <td>
                      <span className={`badge badge-run-status badge-${(run.status || '').toLowerCase()}`}>
                        {run.status || '—'}
                      </span>
                    </td>
                    <td className="nowrap">{formatTimestamp(run.start_time)}</td>
                    <td className="nowrap">{formatTimestamp(run.end_time)}</td>
                    <td>
                      <button
                        className="btn btn-sm btn-outline"
                        onClick={() => handleViewDetails(run)}
                      >
                        View Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {selectedRun && (
        <RunDetailsSection
          experimentId={experiment.experiment_id}
          run={selectedRun}
          token={token}
        />
      )}
    </>
  );
}

// ─── Section: Experiments ─────────────────────────────────────────────────────

function ExperimentsSection({ token }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [experiments, setExperiments] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [selectedExperiment, setSelectedExperiment] = useState(null);

  const loadExperiments = () => {
    if (!token) { setError('Please save a token first.'); return; }
    setLoading(true);
    setError(null);
    setSelectedExperiment(null);
    apiFetch('/experiments/', token)
      .then((data) => {
        setExperiments(Array.isArray(data) ? data : data.experiments || []);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (!token) { setError('Please save a token first.'); return; }
    if (!searchQuery.trim()) { loadExperiments(); return; }
    setSearching(true);
    setError(null);
    setSelectedExperiment(null);
    apiFetch(`/experiments/search?name=${encodeURIComponent(searchQuery.trim())}`, token)
      .then((data) => {
        setExperiments(Array.isArray(data) ? data : data.experiments || []);
      })
      .catch((err) => setError(err.message))
      .finally(() => setSearching(false));
  };

  return (
    <>
      <section className="card experiments-section">
        <div className="section-header">
          <h2 className="section-title">🧪 Experiments</h2>
          <button className="btn btn-primary" onClick={loadExperiments} disabled={loading || searching}>
            {loading ? 'Loading…' : 'Load Experiments'}
          </button>
        </div>

        {/* Search bar */}
        <form className="search-row" onSubmit={handleSearch}>
          <input
            className="search-input"
            type="text"
            placeholder="Search experiments by name…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <button className="btn btn-outline" type="submit" disabled={searching || loading}>
            {searching ? 'Searching…' : 'Search'}
          </button>
          {searchQuery && (
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => { setSearchQuery(''); loadExperiments(); }}
            >
              Clear
            </button>
          )}
        </form>

        {(loading || searching) && <Spinner />}
        <ErrorMsg message={error} />

        {experiments && experiments.length === 0 && (
          <p className="empty-note">No experiments found.</p>
        )}

        {experiments && experiments.length > 0 && (
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Experiment ID</th>
                  <th>Name</th>
                  <th>Owner Email</th>
                  <th>Lifecycle Stage</th>
                  <th>Creation Time</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {experiments.map((exp) => (
                  <tr
                    key={exp.experiment_id}
                    className={selectedExperiment?.experiment_id === exp.experiment_id ? 'row-selected' : ''}
                  >
                    <td className="mono">{exp.experiment_id}</td>
                    <td><strong>{exp.name}</strong></td>
                    <td>{exp.owner_email || '—'}</td>
                    <td>
                      <span className={`badge badge-lifecycle badge-${(exp.lifecycle_stage || '').toLowerCase()}`}>
                        {exp.lifecycle_stage || '—'}
                      </span>
                    </td>
                    <td className="nowrap">{formatTimestamp(exp.creation_time)}</td>
                    <td>
                      <button
                        className="btn btn-sm btn-outline"
                        onClick={() => setSelectedExperiment(exp)}
                      >
                        View Runs
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {selectedExperiment && (
        <RunsSection
          experiment={selectedExperiment}
          token={token}
          onViewDetails={() => {}}
        />
      )}
    </>
  );
}

// ─── App Root ─────────────────────────────────────────────────────────────────

export default function App() {
  const [token, setToken] = useState('');

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-inner">
          <div className="header-logo">
            <span className="logo-az">AZ</span>
            <div>
              <div className="header-title">MLOps MVP</div>
              <div className="header-sub">API Testing Interface</div>
            </div>
          </div>
          <div className="header-meta">
            <span className="meta-label">Base URL</span>
            <code className="meta-url">http://localhost:8000/api</code>
          </div>
        </div>
      </header>

      <main className="app-main">
        <TokenSection token={token} onSave={setToken} />
        <ExperimentsSection token={token} />
      </main>

      <footer className="app-footer">
        AstraZeneca MLOps MVP · Internal Tool · {new Date().getFullYear()}
      </footer>
    </div>
  );
}
