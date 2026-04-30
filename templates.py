"""HTML for the home page. Kept as a single string to avoid a templating engine."""

INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Trading Agents — Multi-agent stock analysis</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=IBM+Plex+Sans:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0a0a0b;
    --surface: #111113;
    --surface-2: #16161a;
    --border: #26262c;
    --border-strong: #3a3a42;
    --text: #ebebed;
    --text-dim: #9c9ca6;
    --text-faint: #5e5e68;
    --accent: #22ff88;
    --accent-soft: rgba(34,255,136,0.12);
    --danger: #ff5d5d;
    --danger-soft: rgba(255,93,93,0.14);
    --warn: #ffb547;
    --warn-soft: rgba(255,181,71,0.14);
    --serif: 'Instrument Serif', 'Times New Roman', serif;
    --sans: 'IBM Plex Sans', -apple-system, system-ui, sans-serif;
    --mono: 'IBM Plex Mono', ui-monospace, 'SF Mono', monospace;
  }

  * { box-sizing: border-box; }

  html, body {
    margin: 0; padding: 0;
    background: var(--bg);
    color: var(--text);
    font-family: var(--sans);
    font-weight: 400;
    font-size: 14px;
    line-height: 1.55;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  body {
    background:
      radial-gradient(ellipse 80% 50% at 50% -20%, rgba(34,255,136,0.06), transparent 60%),
      var(--bg);
    min-height: 100vh;
    background-attachment: fixed;
  }

  .shell {
    max-width: 760px;
    margin: 0 auto;
    padding: 56px 28px 80px;
  }

  /* ── Header ───────────────────────────────────────── */
  header {
    display: flex; align-items: baseline; justify-content: space-between;
    gap: 16px; margin-bottom: 8px;
  }
  .brand {
    font-family: var(--serif);
    font-size: 38px; line-height: 1; letter-spacing: -0.01em;
    font-weight: 400;
  }
  .brand em {
    font-style: italic;
    color: var(--accent);
    font-weight: 400;
  }
  .status-dot {
    display: inline-flex; align-items: center; gap: 8px;
    font-family: var(--mono); font-size: 11px;
    color: var(--text-faint); text-transform: uppercase;
    letter-spacing: 0.08em;
  }
  .status-dot::before {
    content: ""; width: 6px; height: 6px; border-radius: 50%;
    background: var(--accent); box-shadow: 0 0 8px var(--accent);
    animation: pulse 2s ease-in-out infinite;
  }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

  .tagline {
    color: var(--text-dim);
    font-size: 14px;
    margin: 4px 0 36px;
    max-width: 520px;
  }

  /* ── Provider strip ───────────────────────────────── */
  .providers {
    display: flex; gap: 6px; flex-wrap: wrap;
    margin-bottom: 32px;
    font-family: var(--mono); font-size: 11px;
  }
  .provider {
    padding: 4px 10px;
    border: 1px solid var(--border);
    border-radius: 100px;
    color: var(--text-faint);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    transition: all 120ms ease;
  }
  .provider.on {
    color: var(--accent);
    border-color: var(--accent-soft);
    background: var(--accent-soft);
  }

  /* ── Form ─────────────────────────────────────────── */
  .panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 28px;
    margin-bottom: 20px;
  }

  .panel-label {
    font-family: var(--mono);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--text-faint);
    margin-bottom: 18px;
    display: flex; align-items: center; gap: 10px;
  }
  .panel-label::after {
    content: ""; flex: 1; height: 1px; background: var(--border);
  }

  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  .grid-3 { display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 16px; }
  @media (max-width: 540px) {
    .grid, .grid-3 { grid-template-columns: 1fr; }
  }

  .field { display: flex; flex-direction: column; gap: 6px; margin-bottom: 16px; }
  .field label {
    font-family: var(--mono);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-dim);
    font-weight: 500;
  }

  input[type="text"], input[type="date"], select {
    width: 100%;
    padding: 10px 12px;
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 3px;
    color: var(--text);
    font-family: var(--mono);
    font-size: 13px;
    font-weight: 500;
    transition: border-color 120ms ease, box-shadow 120ms ease;
  }
  input[type="text"]:focus, input[type="date"]:focus, select:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-soft);
  }
  input::placeholder { color: var(--text-faint); }

  /* Native date picker tweaks */
  input[type="date"] { color-scheme: dark; }
  input[type="date"]::-webkit-calendar-picker-indicator {
    filter: invert(1) opacity(0.5);
    cursor: pointer;
  }

  select {
    appearance: none;
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='6' viewBox='0 0 10 6' fill='none'><path d='M1 1L5 5L9 1' stroke='%239c9ca6' stroke-width='1.4' stroke-linecap='round'/></svg>");
    background-repeat: no-repeat;
    background-position: right 14px center;
    padding-right: 36px;
  }

  .actions {
    display: flex; align-items: center; gap: 16px; margin-top: 8px;
  }

  button {
    background: var(--accent);
    color: #001207;
    border: none;
    border-radius: 3px;
    padding: 11px 22px;
    font-family: var(--mono);
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    cursor: pointer;
    transition: all 120ms ease;
  }
  button:hover:not(:disabled) {
    background: #5fffa8;
    transform: translateY(-1px);
    box-shadow: 0 6px 20px -8px var(--accent);
  }
  button:disabled {
    background: var(--surface-2);
    color: var(--text-faint);
    cursor: not-allowed;
  }
  .hint {
    font-family: var(--mono); font-size: 11px; color: var(--text-faint);
    letter-spacing: 0.04em;
  }

  /* ── Result panel ─────────────────────────────────── */
  .result-head {
    display: flex; align-items: baseline; justify-content: space-between;
    gap: 12px; margin-bottom: 16px; flex-wrap: wrap;
  }
  .result-title {
    font-family: var(--serif);
    font-size: 22px;
    font-weight: 400;
  }
  .result-title em { font-style: italic; color: var(--accent); }
  .meta {
    font-family: var(--mono); font-size: 11px; color: var(--text-faint);
  }
  .meta code {
    color: var(--text-dim);
    background: var(--surface-2);
    padding: 2px 6px; border-radius: 2px;
  }

  .pill {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 3px 10px;
    border-radius: 100px;
    font-family: var(--mono);
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
  }
  .pill::before {
    content: ""; width: 6px; height: 6px; border-radius: 50%;
  }
  .pill.running { color: var(--warn); background: var(--warn-soft); }
  .pill.running::before { background: var(--warn); animation: pulse 1.4s ease-in-out infinite; }
  .pill.completed { color: var(--accent); background: var(--accent-soft); }
  .pill.completed::before { background: var(--accent); }
  .pill.failed { color: var(--danger); background: var(--danger-soft); }
  .pill.failed::before { background: var(--danger); }

  pre.output {
    background: var(--bg);
    border: 1px solid var(--border);
    border-left: 2px solid var(--accent);
    padding: 18px 20px;
    border-radius: 3px;
    color: var(--text);
    font-family: var(--mono);
    font-size: 13px;
    line-height: 1.65;
    white-space: pre-wrap;
    word-wrap: break-word;
    margin: 0;
    overflow-x: auto;
    max-height: 480px;
    overflow-y: auto;
  }
  pre.output.failed { border-left-color: var(--danger); }
  pre.output.running { border-left-color: var(--warn); color: var(--text-dim); }
  pre.output.running::after {
    content: "▊";
    color: var(--warn);
    animation: blink 1s steps(2,start) infinite;
  }
  @keyframes blink { to { visibility: hidden; } }

  /* ── Job list ─────────────────────────────────────── */
  .jobs-list { font-family: var(--mono); font-size: 12px; }
  .job-row {
    display: grid;
    grid-template-columns: auto 1fr auto auto;
    gap: 14px; align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid var(--border);
  }
  .job-row:last-child { border-bottom: none; }
  .job-row .ticker { font-weight: 600; color: var(--text); letter-spacing: 0.04em; }
  .job-row .date { color: var(--text-dim); }
  .job-row .when { color: var(--text-faint); font-size: 11px; }
  .empty { color: var(--text-faint); font-style: italic; padding: 8px 0; font-family: var(--sans); }

  /* ── Footer ───────────────────────────────────────── */
  footer {
    margin-top: 28px;
    font-family: var(--mono); font-size: 11px;
    color: var(--text-faint);
    letter-spacing: 0.04em;
    display: flex; gap: 18px; flex-wrap: wrap;
  }
  footer a {
    color: var(--text-dim);
    text-decoration: none;
    border-bottom: 1px dashed var(--border-strong);
    padding-bottom: 1px;
    transition: color 120ms ease, border-color 120ms ease;
  }
  footer a:hover { color: var(--accent); border-color: var(--accent); }
  footer .sep { color: var(--text-faint); }

  /* Stagger reveal on load */
  .shell > * { animation: rise 600ms cubic-bezier(0.2,0.8,0.2,1) backwards; }
  .shell > *:nth-child(1) { animation-delay: 0ms; }
  .shell > *:nth-child(2) { animation-delay: 60ms; }
  .shell > *:nth-child(3) { animation-delay: 120ms; }
  .shell > *:nth-child(4) { animation-delay: 180ms; }
  .shell > *:nth-child(5) { animation-delay: 240ms; }
  @keyframes rise {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
  }
</style>
</head>
<body>
<div class="shell">

<header>
  <h1 class="brand">Trading <em>Agents</em></h1>
  <span class="status-dot" id="status-dot">live</span>
</header>

<p class="tagline">A multi-agent LLM trading firm. Analysts, researchers, traders, and risk managers debate every ticker before returning a decision.</p>

<div class="providers" id="providers">
  <span class="provider" data-key="openai">OpenAI</span>
  <span class="provider" data-key="anthropic">Anthropic</span>
  <span class="provider" data-key="google">Gemini</span>
  <span class="provider" data-key="deepseek">DeepSeek</span>
  <span class="provider" data-key="xai">xAI</span>
  <span class="provider" data-key="openrouter">OpenRouter</span>
</div>

<div class="panel">
  <div class="panel-label">Run analysis</div>
  <form id="analyze-form">
    <div class="grid-3">
      <div class="field">
        <label for="ticker">Ticker</label>
        <input id="ticker" name="ticker" value="NVDA" required autocomplete="off" spellcheck="false">
      </div>
      <div class="field">
        <label for="date">Date</label>
        <input id="date" name="date" type="date" required>
      </div>
      <div class="field">
        <label for="max_debate_rounds">Rounds</label>
        <select id="max_debate_rounds" name="max_debate_rounds">
          <option value="1">1 — quick</option>
          <option value="2">2 — deep</option>
          <option value="3">3 — thorough</option>
        </select>
      </div>
    </div>
    <div class="grid">
      <div class="field">
        <label for="llm_provider">Provider</label>
        <select id="llm_provider" name="llm_provider">
          <option value="openai">OpenAI</option>
          <option value="anthropic">Anthropic</option>
          <option value="google">Google Gemini</option>
          <option value="deepseek">DeepSeek</option>
          <option value="xai">xAI</option>
          <option value="openrouter">OpenRouter</option>
        </select>
      </div>
      <div class="field">
        <label for="deep_think_llm">Deep model</label>
        <input id="deep_think_llm" name="deep_think_llm" value="gpt-4o" autocomplete="off" spellcheck="false">
      </div>
    </div>
    <div class="field" style="margin-bottom: 22px">
      <label for="quick_think_llm">Quick model</label>
      <input id="quick_think_llm" name="quick_think_llm" value="gpt-4o-mini" autocomplete="off" spellcheck="false">
    </div>
    <div class="actions">
      <button type="submit" id="submit-btn">Run analysis →</button>
      <span id="hint" class="hint"></span>
    </div>
  </form>
</div>

<div id="result" style="display:none" class="panel">
  <div class="result-head">
    <div>
      <div class="result-title">Decision <em id="result-ticker"></em></div>
      <div class="meta">job <code id="job-id"></code> · started <span id="started-at"></span></div>
    </div>
    <span id="job-status" class="pill running">running</span>
  </div>
  <pre class="output running" id="output">Spinning up agents…</pre>
</div>

<div class="panel">
  <div class="panel-label">Recent jobs</div>
  <div id="jobs-list" class="jobs-list"><div class="empty">Loading…</div></div>
</div>

<footer>
  <a href="/docs" target="_blank">api docs</a>
  <span class="sep">/</span>
  <a href="/api/jobs" target="_blank">jobs json</a>
  <span class="sep">/</span>
  <a href="/api/config" target="_blank">config</a>
  <span class="sep">/</span>
  <a href="https://github.com/TauricResearch/TradingAgents" target="_blank" rel="noopener">upstream</a>
</footer>

</div>

<script>
const form = document.getElementById('analyze-form');
const submitBtn = document.getElementById('submit-btn');
const hint = document.getElementById('hint');
const resultPanel = document.getElementById('result');
const jobIdEl = document.getElementById('job-id');
const startedEl = document.getElementById('started-at');
const statusEl = document.getElementById('job-status');
const outputEl = document.getElementById('output');
const resultTickerEl = document.getElementById('result-ticker');
const jobsListEl = document.getElementById('jobs-list');
const providersEl = document.getElementById('providers');

document.getElementById('date').valueAsDate = new Date();

let pollInterval = null;

function relTime(iso) {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return Math.floor(diff) + 's ago';
  if (diff < 3600) return Math.floor(diff/60) + 'm ago';
  if (diff < 86400) return Math.floor(diff/3600) + 'h ago';
  return Math.floor(diff/86400) + 'd ago';
}

async function loadProviders() {
  try {
    const res = await fetch('/api/config');
    const cfg = await res.json();
    for (const p of providersEl.querySelectorAll('.provider')) {
      const key = p.dataset.key;
      if (cfg.providers_available && cfg.providers_available[key]) {
        p.classList.add('on');
      }
    }
  } catch (e) { /* silent */ }
}

function setStatus(state, text) {
  statusEl.className = 'pill ' + state;
  statusEl.textContent = text || state;
  outputEl.classList.remove('running','failed');
  if (state === 'running') outputEl.classList.add('running');
  if (state === 'failed') outputEl.classList.add('failed');
}

async function pollJob(jobId) {
  try {
    const res = await fetch(`/api/jobs/${jobId}`);
    if (!res.ok) throw new Error(`Failed: ${res.status}`);
    const job = await res.json();
    if (job.status === 'completed') {
      setStatus('completed', 'completed');
      outputEl.textContent = job.decision || '(no decision returned)';
      clearInterval(pollInterval);
      submitBtn.disabled = false;
      hint.textContent = '';
      loadJobsList();
    } else if (job.status === 'failed') {
      setStatus('failed', 'failed');
      outputEl.textContent = `Error: ${job.error || 'unknown'}`;
      clearInterval(pollInterval);
      submitBtn.disabled = false;
      hint.textContent = '';
      loadJobsList();
    }
  } catch (e) {
    outputEl.textContent = `Polling error: ${e.message}`;
  }
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  submitBtn.disabled = true;
  hint.textContent = 'submitting…';

  const data = Object.fromEntries(new FormData(form));
  data.max_debate_rounds = parseInt(data.max_debate_rounds, 10);

  try {
    const res = await fetch('/api/analyze', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data),
    });
    const job = await res.json();
    if (!res.ok) {
      hint.textContent = '';
      submitBtn.disabled = false;
      alert(job.detail || 'Failed to submit');
      return;
    }
    hint.textContent = '60–300s · debate is running';
    resultPanel.style.display = 'block';
    resultTickerEl.textContent = job.ticker;
    jobIdEl.textContent = job.job_id.slice(0, 8);
    startedEl.textContent = new Date(job.created_at).toLocaleTimeString();
    setStatus('running', 'running');
    outputEl.textContent = 'Spinning up agents…';
    resultPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    pollInterval = setInterval(() => pollJob(job.job_id), 3000);
  } catch (err) {
    submitBtn.disabled = false;
    hint.textContent = '';
    alert(`Error: ${err.message}`);
  }
});

async function loadJobsList() {
  try {
    const res = await fetch('/api/jobs');
    const jobs = await res.json();
    if (!jobs.length) {
      jobsListEl.innerHTML = '<div class="empty">No jobs yet — submit one above.</div>';
      return;
    }
    jobsListEl.innerHTML = jobs.slice(0, 10).map(j => `
      <div class="job-row">
        <span class="pill ${j.status}">${j.status}</span>
        <span><span class="ticker">${j.ticker}</span> <span class="date">@ ${j.date}</span></span>
        <span class="when">${relTime(j.created_at)}</span>
      </div>`).join('');
  } catch (e) {
    jobsListEl.innerHTML = `<div class="empty">Failed to load: ${e.message}</div>`;
  }
}

loadProviders();
loadJobsList();
setInterval(loadJobsList, 10000);
</script>
</body>
</html>"""
