"""HTML for the home page. Kept as a single string to avoid a templating engine."""

INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TradingAgents — Multi-Agent Stock Analysis</title>
<style>
  :root { color-scheme: light dark; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
    max-width: 880px; margin: 0 auto; padding: 32px 16px;
    background: #fafafa; color: #1a1a1a; line-height: 1.5;
  }
  @media (prefers-color-scheme: dark) {
    body { background: #0c0c0c; color: #eaeaea; }
    .card { background: #181818; border-color: #2a2a2a; }
    input, select, button { background: #1f1f1f; color: #eaeaea; border-color: #333; }
    pre { background: #111; border-color: #2a2a2a; }
  }
  h1 { font-size: 1.6rem; margin-bottom: 0.2rem; }
  .sub { color: #888; margin-bottom: 1.5rem; }
  .card {
    background: #fff; border: 1px solid #e1e1e1; border-radius: 8px;
    padding: 20px; margin-bottom: 20px;
  }
  label { display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 4px; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  input, select {
    width: 100%; padding: 8px 10px; border: 1px solid #ccc; border-radius: 6px;
    font-size: 0.95rem; box-sizing: border-box;
  }
  button {
    background: #2563eb; color: white; border: none; border-radius: 6px;
    padding: 10px 18px; font-size: 0.95rem; cursor: pointer; font-weight: 600;
  }
  button:hover { background: #1d4ed8; }
  button:disabled { background: #888; cursor: not-allowed; }
  .row { margin-bottom: 12px; }
  pre {
    background: #f5f5f5; border: 1px solid #e1e1e1; padding: 12px;
    border-radius: 6px; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word;
    font-size: 0.85rem;
  }
  .status { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }
  .status.running { background: #fef3c7; color: #92400e; }
  .status.completed { background: #dcfce7; color: #166534; }
  .status.failed { background: #fee2e2; color: #991b1b; }
  .small { font-size: 0.8rem; color: #888; }
  a { color: #2563eb; }
</style>
</head>
<body>
<h1>TradingAgents</h1>
<p class="sub">Multi-agent LLM trading framework. Self-hosted on Railway.</p>

<div class="card">
  <form id="analyze-form">
    <div class="grid">
      <div class="row">
        <label for="ticker">Ticker</label>
        <input id="ticker" name="ticker" value="NVDA" required>
      </div>
      <div class="row">
        <label for="date">Analysis Date (YYYY-MM-DD)</label>
        <input id="date" name="date" type="date" required>
      </div>
    </div>
    <div class="grid">
      <div class="row">
        <label for="llm_provider">LLM Provider</label>
        <select id="llm_provider" name="llm_provider">
          <option value="openai">OpenAI</option>
          <option value="anthropic">Anthropic</option>
          <option value="google">Google Gemini</option>
          <option value="deepseek">DeepSeek</option>
          <option value="openrouter">OpenRouter</option>
        </select>
      </div>
      <div class="row">
        <label for="max_debate_rounds">Debate Rounds</label>
        <select id="max_debate_rounds" name="max_debate_rounds">
          <option value="1">1 (fastest, cheapest)</option>
          <option value="2">2 (deeper)</option>
          <option value="3">3 (thorough)</option>
        </select>
      </div>
    </div>
    <div class="grid">
      <div class="row">
        <label for="deep_think_llm">Deep-think model</label>
        <input id="deep_think_llm" name="deep_think_llm" value="gpt-4o">
      </div>
      <div class="row">
        <label for="quick_think_llm">Quick-think model</label>
        <input id="quick_think_llm" name="quick_think_llm" value="gpt-4o-mini">
      </div>
    </div>
    <button type="submit" id="submit-btn">Run Analysis</button>
    <span id="hint" class="small" style="margin-left:10px"></span>
  </form>
</div>

<div id="result" style="display:none" class="card">
  <h3>Analysis <span id="job-status" class="status"></span></h3>
  <p class="small">Job: <code id="job-id"></code> · Started <span id="started-at"></span></p>
  <pre id="output">Running…</pre>
</div>

<div class="card">
  <h3>Recent Jobs</h3>
  <div id="jobs-list" class="small">Loading…</div>
</div>

<p class="small">
  <a href="/docs" target="_blank">API docs</a> · <a href="/api/config" target="_blank">config</a> · <a href="/api/jobs" target="_blank">jobs</a>
</p>

<script>
const form = document.getElementById('analyze-form');
const submitBtn = document.getElementById('submit-btn');
const hint = document.getElementById('hint');
const resultCard = document.getElementById('result');
const jobIdEl = document.getElementById('job-id');
const startedEl = document.getElementById('started-at');
const statusEl = document.getElementById('job-status');
const outputEl = document.getElementById('output');
const jobsListEl = document.getElementById('jobs-list');

document.getElementById('date').valueAsDate = new Date();

let pollInterval = null;

async function pollJob(jobId) {
  try {
    const res = await fetch(`/api/jobs/${jobId}`);
    if (!res.ok) throw new Error(`Failed: ${res.status}`);
    const job = await res.json();
    statusEl.textContent = job.status;
    statusEl.className = `status ${job.status}`;
    if (job.status === 'completed') {
      outputEl.textContent = job.decision || '(no decision returned)';
      clearInterval(pollInterval);
      submitBtn.disabled = false;
      hint.textContent = '';
      loadJobsList();
    } else if (job.status === 'failed') {
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
    hint.textContent = 'running… this can take 1–5 minutes depending on LLM and rounds.';
    resultCard.style.display = 'block';
    jobIdEl.textContent = job.job_id;
    startedEl.textContent = new Date(job.created_at).toLocaleTimeString();
    statusEl.textContent = 'running';
    statusEl.className = 'status running';
    outputEl.textContent = 'Running…';
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
      jobsListEl.innerHTML = '<em>No jobs yet.</em>';
      return;
    }
    jobsListEl.innerHTML = jobs.slice(0, 10).map(j => `
      <div style="padding:6px 0;border-bottom:1px solid #eee">
        <strong>${j.ticker}</strong> @ ${j.date}
        — <span class="status ${j.status}">${j.status}</span>
        — <span class="small">${new Date(j.created_at).toLocaleString()}</span>
      </div>`).join('');
  } catch (e) {
    jobsListEl.textContent = `Failed: ${e.message}`;
  }
}

loadJobsList();
setInterval(loadJobsList, 10000);
</script>
</body>
</html>"""
