/* Fusion GUI — 2026 Look · 1996-core (~4KB logic, kein Chart.js) */
(function () {
  'use strict';

  const STORAGE_KEY = 'fusion-monitor-panel-positions';
  const events = [];
  const maxEvents = 60;
  const cpuHist = [];
  const ramHist = [];
  const maxHist = 32;
  let ws = null;
  let busy = false;
  let hidden = false;
  let tickN = 0;
  let lastJobsKey = '';
  let config = { workspace_url: 'http://127.0.0.1:8080', era: { poll: { pulse_sec: 6, jobs_sec: 5, metrics_sec: 4 } } };

  function $(id) { return document.getElementById(id); }
  function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }

  function toast(msg, type) {
    var el = $('fusion-toast');
    if (!el) return;
    el.textContent = msg;
    el.className = 'fusion-toast fusion-toast--show fusion-toast--' + (type || 'ok');
    clearTimeout(toast._t);
    toast._t = setTimeout(function () { el.classList.remove('fusion-toast--show'); }, 2200);
  }

  function setBusy(on, msg) {
    busy = on;
    var bar = $('busy-bar');
    var st = $('status-bar');
    if (bar) bar.style.display = on ? 'block' : 'none';
    if (st) st.textContent = on ? (msg || 'Arbeitet…') : 'Bereit · Pulse-Modus';
  }

  async function api(path, opts) {
    var r = await fetch(path, opts);
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.json();
  }

  async function submitInput(kind, message, payload) {
    var ack = await api('/api/input', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ kind: kind, message: message, payload: payload || {}, history: [] }),
    });
    if (ack.sync || ack.response) return ack;
    if (!ack.job_id) return ack;
    toast('Worker ' + ack.job_id.slice(0, 8), 'warn');
    for (var i = 0; i < 240; i++) {
      await sleep(500);
      var job = await api('/api/jobs/' + ack.job_id);
      if (job.status === 'done') return job.result || job;
      if (job.status === 'error') throw new Error(job.error || 'Worker-Fehler');
    }
    throw new Error('Worker-Timeout');
  }

  function setOutput(text) {
    var out = $('panel-output-text');
    if (out) out.value = typeof text === 'string' ? text : JSON.stringify(text, null, 2);
  }

  function updateStat(name, val) {
    var v = Math.round(val || 0);
    var el = $(name);
    var bar = $(name + '-bar');
    var stat = $('stat-' + name);
    if (el) el.textContent = v;
    if (bar) bar.style.width = v + '%';
    if (stat) stat.textContent = v + '%';
  }

  function pushHist(cpu, ram) {
    cpuHist.push(cpu);
    ramHist.push(ram);
    if (cpuHist.length > maxHist) { cpuHist.shift(); ramHist.shift(); }
    drawSparkline();
  }

  function drawSparkline() {
    var c = $('sparkline');
    if (!c) return;
    var ctx = c.getContext('2d');
    var w = c.clientWidth || 400;
    var h = 140;
    if (c.width !== w) c.width = w;
    c.height = h;
    ctx.fillStyle = '#05050c';
    ctx.fillRect(0, 0, w, h);
    ctx.strokeStyle = 'rgba(0,255,213,.08)';
    ctx.lineWidth = 1;
    for (var g = 0; g <= 4; g++) {
      var gy = (h / 4) * g;
      ctx.beginPath(); ctx.moveTo(0, gy); ctx.lineTo(w, gy); ctx.stroke();
    }
    function line(data, color) {
      if (data.length < 2) return;
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      for (var i = 0; i < data.length; i++) {
        var x = (i / (maxHist - 1)) * (w - 8) + 4;
        var y = h - 8 - (data[i] / 100) * (h - 16);
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }
      ctx.stroke();
    }
    line(cpuHist, '#00ffd5');
    line(ramHist, '#a855f7');
    ctx.fillStyle = '#5c6b82';
    ctx.font = '10px system-ui';
    ctx.fillText('CPU', 6, 12);
    ctx.fillStyle = '#a855f7';
    ctx.fillText('RAM', 36, 12);
  }

  function renderCyberLayer(data) {
    var layer = $('fusion-cyber-layer');
    var badge = $('cyber-badge');
    var score = $('cyber-score');
    var signals = $('cyber-signals');
    var body = document.body;
    if (!layer || !data) return;
    var active = !!data.active;
    layer.className = 'fusion-cyber-layer ' + (active ? 'fusion-cyber-layer--active' : 'fusion-cyber-layer--standby');
    layer.setAttribute('aria-hidden', active ? 'false' : 'true');
    if (body) body.classList.toggle('fusion-cyber-active', active);
    if (badge) badge.textContent = (data.visual && data.visual.badge) || (active ? 'OPTIMIZATION ACTIVE' : 'CYBER STANDBY');
    if (score) score.textContent = active ? ('SCORE ' + (data.optimization_score || 0)) : '';
    if (signals && data.signals) {
      signals.innerHTML = data.signals.map(function (s) {
        var cls = 'fusion-cyber-signal' + (s.active ? '' : ' fusion-cyber-signal--off');
        return '<span class="' + cls + '" title="' + (s.detail || '') + '">' + s.label + '</span>';
      }).join('');
    }
    if ($('conn-status') && active) {
      $('conn-status').textContent = 'Cyber Layer · Substrat OK';
    }
  }

  async function fetchCyberLayer() {
    try {
      var data = await api('/api/windows/cyber-layer/status');
      renderCyberLayer(data);
      return data;
    } catch (e) { return null; }
  }

  async function fetchPulse() {
    try {
      var sig = await api('/api/signal/health?layer=pulse&client=fusion-monitor');
      if (sig.payload && sig.payload.unchanged) return false;
      var p = (sig.payload) || {};
      if (p.cpu != null) updateStat('cpu', p.cpu);
      if (p.ram != null) updateStat('ram', p.ram);
      if (p.cpu != null && p.ram != null) pushHist(Math.round(p.cpu), Math.round(p.ram));
      if ($('stat-modules') && p.modules_loaded != null) {
        $('stat-modules').textContent = p.modules_loaded + '/' + (p.modules_total || p.modules_loaded);
      }
      if ($('stat-agents') && p.agents != null) $('stat-agents').textContent = String(p.agents);
      if ($('stat-profile') && p.profile) $('stat-profile').textContent = String(p.profile).toUpperCase();
      var savings = sig.savings_pct;
      if (savings != null && $('eff-hint')) {
        $('eff-hint').textContent = 'Pulse -' + Math.round(savings) + '% Traffic';
      }
      return true;
    } catch (e) { return false; }
  }

  async function fetchMetrics() {
    try {
      var m = await api('/api/metrics');
      var cpu = Math.round(m.cpu || 0);
      var ram = Math.round(m.ram || 0);
      updateStat('cpu', cpu);
      updateStat('ram', ram);
      pushHist(cpu, ram);
      if ($('event-count')) $('event-count').textContent = m.events ?? 0;
      if ($('ops')) $('ops').textContent = (m.ops_per_sec ?? 0).toFixed(1);
      if ($('subs')) $('subs').textContent = m.subs ?? 0;
      if ($('cpu-peak')) $('cpu-peak').textContent = Math.round(m.cpu_max || cpu);
      if ($('cores')) $('cores').textContent = (m.active_cores || 0) + '/' + (m.cpu_cores || '?');
    } catch (e) { /* offline */ }
  }

  function jobClass(st) {
    return { done: 'fusion-job--done', running: 'fusion-job--run', queued: 'fusion-job--queue', error: 'fusion-job--err' }[st] || 'fusion-job--queue';
  }

  async function refreshJobs() {
    try {
      var data = await api('/api/jobs?limit=10');
      var jobs = data.jobs || [];
      var key = jobs.map(function (j) { return j.job_id + j.status; }).join('|');
      if (key === lastJobsKey) return;
      lastJobsKey = key;
      var list = $('job-list');
      var badge = $('job-badge');
      if (!list) return;
      var active = jobs.filter(function (j) { return j.status === 'queued' || j.status === 'running'; }).length;
      if (badge) badge.textContent = active || jobs.length;
      if (!jobs.length) {
        list.innerHTML = '<div class="fusion-status-text">Keine Jobs</div>';
        return;
      }
      list.innerHTML = jobs.map(function (j) {
        return '<div class="fusion-job-row ' + jobClass(j.status) + '" data-job="' + j.job_id + '">' +
          '<span class="fusion-job-id">' + (j.job_id || '').slice(0, 8) + '</span>' +
          '<span class="fusion-job-kind">' + (j.kind || '?') + '</span>' +
          '<span class="fusion-job-st">' + (j.status || 'queued').toUpperCase() + '</span></div>';
      }).join('');
      list.querySelectorAll('[data-job]').forEach(function (row) {
        row.onclick = function () { showJob(row.dataset.job); };
      });
    } catch (e) { /* skip */ }
  }

  async function showJob(jobId) {
    try {
      setOutput(await api('/api/jobs/' + jobId));
      toast('Job ' + jobId.slice(0, 8), 'ok');
    } catch (e) { toast(String(e.message || e), 'err'); }
  }

  function renderEvents() {
    var el = $('event-stream');
    if (!el) return;
    el.innerHTML = events.slice(0, 20).map(function (ev) {
      var type = ev.type || 'info';
      var msg = (ev.msg || '').slice(0, 100);
      var color = type === 'error' ? '#f87171' : type === 'system' ? '#fbbf24' : '#00ffd5';
      return '<div class="fusion-event-row" style="border-left-color:' + color + '" data-ev="' + encodeURIComponent(JSON.stringify(ev)) + '">' +
        '<span style="color:' + color + '">' + type + '</span> · ' + msg + '</div>';
    }).join('') || '<div class="fusion-status-text">Warte auf Events…</div>';
    el.querySelectorAll('[data-ev]').forEach(function (row) {
      row.onclick = function () {
        try { setOutput(JSON.parse(decodeURIComponent(row.dataset.ev))); } catch (_) {}
      };
    });
  }

  function initWebSocket() {
    ws = new WebSocket('ws://' + location.host + '/ws');
    ws.onopen = function () { if ($('conn-status')) $('conn-status').textContent = 'WS ok'; };
    ws.onclose = function () { if ($('conn-status')) $('conn-status').textContent = 'WS off'; };
    ws.onmessage = function (e) {
      var data = JSON.parse(e.data);
      if (data.type === 'welcome') {
        if ($('event-count')) $('event-count').textContent = data.event_count ?? 0;
        return;
      }
      events.unshift(data);
      if (events.length > maxEvents) events.pop();
      renderEvents();
    };
  }

  async function runAction(fn, msg) {
    if (busy) { toast('Warten…', 'warn'); return; }
    setBusy(true, msg);
    try {
      var result = await fn();
      if (result) setOutput(result);
      toast('OK', 'ok');
      await refreshJobs();
    } catch (e) {
      toast(String(e.message || e).slice(0, 80), 'err');
      setOutput('Fehler: ' + (e.message || e));
    } finally {
      setBusy(false);
    }
  }

  function actionLoad() { runAction(function () { return submitInput('command', 'alle laden'); }, 'Laden…'); }
  function actionBench() { runAction(function () { return submitInput('command', 'cpu benchmark'); }, 'Bench…'); }
  function actionStatus() { runAction(function () { return api('/api/health?full=true'); }, 'Status…'); }
  function actionRefresh() {
    runAction(async function () {
      await fetchPulse();
      await fetchMetrics();
      await refreshJobs();
      return { ok: true };
    }, 'Refresh…');
  }
  function actionGrok() { window.open(config.workspace_url, '_blank'); toast('Workspace', 'ok'); }
  function actionCopyOutput() {
    var out = $('panel-output-text');
    if (out && out.value) { navigator.clipboard.writeText(out.value); toast('Kopiert', 'ok'); }
  }
  function actionClearOutput() { setOutput('Bereit.'); toast('Leer', 'ok'); }
  function resetPanels() {
    if (window.fusionResetPanels) window.fusionResetPanels(STORAGE_KEY);
    toast('Layout reset', 'ok');
  }

  function initPanels() {
    if (!window.fusionInitDraggable) return;
    fusionInitDraggable('fusion-panel-jobs', '.fusion-task-handle', 10, 10, STORAGE_KEY);
    fusionInitDraggable('fusion-panel-quick', '.fusion-task-handle', 10, 180, STORAGE_KEY);
    fusionInitDraggable('fusion-panel-hints', '.fusion-task-handle', 10, 340, STORAGE_KEY);
    fusionInitDraggable('fusion-panel-output', '.fusion-task-handle', 300, 10, STORAGE_KEY);
  }

  function initKeyboard() {
    document.addEventListener('keydown', function (e) {
      if (e.target.matches('textarea,input')) return;
      if (e.ctrlKey && e.key.toLowerCase() === 'r') { e.preventDefault(); actionRefresh(); }
      else if (e.ctrlKey && e.key === 'Enter') { e.preventDefault(); actionStatus(); }
    });
  }

  function bindUI() {
    var map = {
      'btn-refresh': actionRefresh, 'btn-load': actionLoad, 'btn-bench': actionBench,
      'btn-status': actionStatus, 'btn-grok': actionGrok, 'btn-reset-layout': resetPanels,
      'btn-copy-out': actionCopyOutput, 'btn-clear-out': actionClearOutput,
    };
    Object.keys(map).forEach(function (id) {
      var el = $(id);
      if (el) el.addEventListener('click', map[id]);
    });
    if ($('card-modules')) $('card-modules').onclick = actionLoad;
    if ($('card-agents')) $('card-agents').onclick = actionGrok;
    if ($('card-profile')) $('card-profile').onclick = function () {
      api('/api/resources/plan').then(setOutput).catch(function (e) { toast(e.message, 'err'); });
    };
    if ($('card-cpu')) $('card-cpu').onclick = function () { $('sparkline').scrollIntoView({ behavior: 'smooth' }); };
    if ($('card-ram')) $('card-ram').onclick = function () { $('sparkline').scrollIntoView({ behavior: 'smooth' }); };
  }

  async function reloadThemeCss() {
    var links = document.querySelectorAll('link[href*="theme.css"],link[href*="/api/windows/skin/css"]');
    links.forEach(function (l) {
      var base = l.getAttribute('href').split('?')[0];
      l.setAttribute('href', base + '?' + Date.now());
    });
  }

  async function loadConfig() {
    try {
      config = await api('/api/gui/status');
      var link = $('workspace-link');
      if (link && config.workspace_url) link.href = config.workspace_url;
      try {
        var skin = await api('/api/windows/skin/status');
        if (skin.active && $('eff-hint')) {
          $('eff-hint').textContent = 'Skin: ' + (skin.active.label || skin.active.id);
        }
      } catch (e2) {}
    } catch (e) {}
  }

  async function tick() {
    if (hidden || busy) return;
    tickN++;
    var pulseSec = (config.era && config.era.poll && config.era.poll.pulse_sec) || 6;
    var metricsSec = (config.era && config.era.poll && config.era.poll.metrics_sec) || 4;
    var jobsSec = (config.era && config.era.poll && config.era.poll.jobs_sec) || 5;
    await fetchPulse();
    if (tickN % 2 === 0) await fetchCyberLayer();
    if (tickN % Math.max(1, Math.round(metricsSec / pulseSec)) === 0) await fetchMetrics();
    if (tickN % Math.max(1, Math.round(jobsSec / pulseSec)) === 0) await refreshJobs();
  }

  function startLoop() {
    var sec = ((config.era && config.era.poll && config.era.poll.pulse_sec) || 6) * 1000;
    setInterval(tick, hidden ? sec * 2 : sec);
    document.addEventListener('visibilitychange', function () {
      hidden = document.hidden;
      if ($('eff-hint')) $('eff-hint').textContent = hidden ? 'Pausiert (Tab hidden)' : 'Pulse-Modus aktiv';
    });
    window.addEventListener('resize', drawSparkline);
  }

  async function init() {
    await loadConfig();
    drawSparkline();
    initWebSocket();
    initPanels();
    initKeyboard();
    bindUI();
    await fetchCyberLayer();
    await tick();
    startLoop();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();