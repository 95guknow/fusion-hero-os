// ALTE_Frau Real-time Dashboard — Geisterjagd + Banach Live Viz
(function () {
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const WS_URL = `${proto}//${location.host}/ws`;
  let ws;
  const events = [];
  let maxEvents = 500;
  let latestViz = null;
  let settingsSchema = null;
  let settingsDraft = { env: {}, ui: {} };
  let settingsActiveTab = 'performance';
  const pollTimers = { metrics: null, bridge: null, phone: null, connectivity: null, viz: null };

  const LAYER_NAMES = ['L0 Seed', 'L1 Review', 'L2 α', 'L3 Audit', 'L4 PMS', 'L5 Quad', 'L6 ω'];

  function connect() {
    ws = new WebSocket(WS_URL);
    ws.onopen = () => {
      ws.send(JSON.stringify({ action: 'request_initial_state' }));
    };
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.type === 'welcome') {
        const el = document.getElementById('event-count');
        if (el) el.textContent = `${data.event_count} events`;
      } else if (data.type === 'geisterjagd_banach' && data.viz) {
        latestViz = data.viz;
        renderGeisterjagd(data.viz);
        renderBanach(data.viz);
        updateVizMetrics(data.viz);
      } else if (data.type === 'layer_update' && data.layers) {
        renderLayers(data.layers);
        renderHyperThreads(data.layers);
      } else {
        events.unshift(data);
        if (events.length > maxEvents) events.pop();
        renderEvents();
      }
    };
    ws.onclose = () => setTimeout(connect, 2500);
  }

  async function fetchMetrics() {
    try {
      const r = await fetch('/api/metrics');
      const m = await r.json();
      const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
      set('cpu', m.cpu);
      set('ram', m.ram);
      set('events', m.events);
      set('ops', m.ops_per_sec);
      if (m.hyperthreading && m.hyperthreading.layers) {
        renderHyperThreads(m.hyperthreading.layers);
        renderLayers(m.hyperthreading.layers);
      }
    } catch (_) { /* ignore */ }
  }

  async function pollViz() {
    try {
      const r = await fetch('/api/viz/geisterjagd-banach?tick=true');
      const snap = await r.json();
      latestViz = snap;
      renderGeisterjagd(snap);
      renderBanach(snap);
      updateVizMetrics(snap);
    } catch (_) { /* ignore */ }
  }

  function renderEvents() {
    const el = document.getElementById('event-stream');
    if (!el) return;
    el.innerHTML = events.slice(0, 24).map((ev) => {
      const t = ev.type || 'event';
      const color = t === 'geisterjagd_banach' ? 'text-[#c084fc]' : t === 'peer_review' ? 'text-teal-400' : 'text-amber-300';
      return `<div class="text-xs mb-1"><span class="${color}">[${t}]</span> <span class="text-slate-400">${ev.msg || ''}</span></div>`;
    }).join('');
  }

  function renderHyperThreads(layers) {
    const el = document.getElementById('hyper-threads');
    if (!el) return;
    el.innerHTML = Object.entries(layers).map(([k, v]) => {
      const util = v.util || 50;
      return `<div class="ht-bar" title="Layer ${k}"><div class="ht-fill" style="height:${util}%"></div><div class="ht-label">L${k} ${Math.round(util)}%</div></div>`;
    }).join('');
  }

  function renderLayers(layers) {
    const el = document.getElementById('layer-grid');
    if (!el) return;
    el.innerHTML = Object.entries(layers).map(([k, v]) => {
      const idx = parseInt(k, 10);
      const name = LAYER_NAMES[idx] || `L${k}`;
      const active = (v.util || 0) > 55 ? 'active' : '';
      return `<div class="layer-cell ${active}"><div class="font-bold text-[#00d4aa]">${name}</div><div class="text-[9px] text-slate-500">${v.status || 'STABLE'}</div></div>`;
    }).join('');
  }

  function updateVizMetrics(snap) {
    const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
    const latent = (snap.ghosts || []).filter((g) => !g.manifest).length;
    const manifest = (snap.ghosts || []).filter((g) => g.manifest).length;
    set('gj-ghosts', `${latent}L / ${manifest}M`);
    set('gj-emerged', snap.emergence_total ?? '--');
    set('gj-heuristic', snap.heuristic_score != null ? snap.heuristic_score.toFixed(2) : '--');
    set('bn-lambda', snap.lambda != null ? snap.lambda.toFixed(3) : '--');
    set('bn-distance', snap.distance != null ? snap.distance.toFixed(3) : '--');
    set('bn-fixpoint', (snap.s_star || [0, 0]).map((x) => x.toFixed(1)).join(', '));
  }

  function renderGeisterjagd(snap) {
    const canvas = document.getElementById('canvas-geisterjagd');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width;
    const H = canvas.height;
    ctx.fillStyle = '#08080c';
    ctx.fillRect(0, 0, W, H);

    // Heuristik-Feld (Heatmap)
    const grid = snap.heuristic_grid || [];
    const cellW = W / 8;
    const cellH = H / 8;
    for (let r = 0; r < grid.length; r++) {
      for (let c = 0; c < (grid[r] || []).length; c++) {
        const v = grid[r][c];
        const hue = 270 - v * 80;
        ctx.fillStyle = `hsla(${hue}, 70%, ${18 + v * 28}%, ${0.25 + v * 0.45})`;
        ctx.fillRect(c * cellW, r * cellH, cellW, cellH);
      }
    }

    // Zonen
    ctx.strokeStyle = 'rgba(124, 58, 237, 0.4)';
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(0, H * 0.48);
    ctx.lineTo(W, H * 0.48);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = 'rgba(148, 163, 184, 0.5)';
    ctx.font = '9px JetBrains Mono';
    ctx.fillText('LATENT (Geister)', 8, 14);
    ctx.fillText('MANIFEST (Emergenz)', 8, H * 0.48 + 14);

    const ghosts = snap.ghosts || [];
    ghosts.forEach((g) => {
      const ax = g.latent[0] * W;
      const ay = g.latent[1] * H * 0.45;
      const alpha = 0.25 + g.activation * 0.75;
      const r = 3 + g.activation * 6;

      // Latent ghost
      const grad = ctx.createRadialGradient(ax, ay, 0, ax, ay, r * 2);
      grad.addColorStop(0, `rgba(192, 132, 252, ${alpha})`);
      grad.addColorStop(1, 'rgba(124, 58, 237, 0)');
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(ax, ay, r * 2, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = `rgba(233, 213, 255, ${alpha})`;
      ctx.beginPath();
      ctx.arc(ax, ay, r, 0, Math.PI * 2);
      ctx.fill();

      if (g.manifest && g.manifest_pos) {
        const mx = g.manifest_pos[0] * W;
        const my = H * 0.52 + g.manifest_pos[1] * H * 0.45;
        // Emergenz-Linie
        ctx.strokeStyle = `rgba(0, 212, 170, ${0.3 + g.activation * 0.4})`;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(ax, ay);
        ctx.lineTo(mx, my);
        ctx.stroke();
        // Manifest spark
        const mg = ctx.createRadialGradient(mx, my, 0, mx, my, 10);
        mg.addColorStop(0, 'rgba(0, 212, 170, 0.9)');
        mg.addColorStop(1, 'rgba(0, 212, 170, 0)');
        ctx.fillStyle = mg;
        ctx.beginPath();
        ctx.arc(mx, my, 10, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#00d4aa';
        ctx.beginPath();
        ctx.arc(mx, my, 4, 0, Math.PI * 2);
        ctx.fill();
      }
    });
  }

  function renderBanach(snap) {
    const canvas = document.getElementById('canvas-banach');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width;
    const H = canvas.height;
    ctx.fillStyle = '#08080c';
    ctx.fillRect(0, 0, W, H);

    const cx = W * 0.38;
    const cy = H * 0.52;
    const scale = Math.min(W, H) * 0.14;

    function toScreen(x, y) {
      return [cx + x * scale, cy - y * scale];
    }

    // Achsen
    ctx.strokeStyle = 'rgba(51, 65, 85, 0.6)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, cy);
    ctx.lineTo(W, cy);
    ctx.moveTo(cx, 0);
    ctx.lineTo(cx, H);
    ctx.stroke();

    // Orbit trail
    const trail = snap.orbit_trail || [];
    if (trail.length > 1) {
      ctx.strokeStyle = 'rgba(124, 58, 237, 0.5)';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      trail.forEach((p, i) => {
        const [sx, sy] = toScreen(p[0], p[1]);
        if (i === 0) ctx.moveTo(sx, sy);
        else ctx.lineTo(sx, sy);
      });
      ctx.stroke();
    }

    // Fixpunkt s*
    const [fx, fy] = toScreen(snap.s_star[0], snap.s_star[1]);
    ctx.fillStyle = '#fbbf24';
    ctx.beginPath();
    ctx.arc(fx, fy, 6, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = 'rgba(251, 191, 36, 0.8)';
    ctx.font = '9px JetBrains Mono';
    ctx.fillText('s* (Z*)', fx + 8, fy - 4);

    // Aktueller Zustand s_n
    const sn = snap.s_n || [0, 0];
    const [nx, ny] = toScreen(sn[0], sn[1]);
    ctx.strokeStyle = 'rgba(0, 212, 170, 0.6)';
    ctx.setLineDash([3, 3]);
    ctx.beginPath();
    ctx.moveTo(fx, fy);
    ctx.lineTo(nx, ny);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = '#00d4aa';
    ctx.beginPath();
    ctx.arc(nx, ny, 7, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#e2e8f0';
    ctx.fillText('sₙ', nx + 9, ny + 3);

    // Distance chart (rechts)
    const dists = snap.distances || [];
    const chartX = W * 0.62;
    const chartW = W * 0.34;
    const chartH = H * 0.7;
    const chartY = H * 0.12;
    ctx.strokeStyle = 'rgba(51, 65, 85, 0.5)';
    ctx.strokeRect(chartX, chartY, chartW, chartH);
    if (dists.length > 1) {
      const maxD = Math.max(...dists, 0.01);
      ctx.strokeStyle = '#c084fc';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      dists.forEach((d, i) => {
        const x = chartX + (i / (dists.length - 1)) * chartW;
        const y = chartY + chartH - (d / maxD) * chartH;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();
    }
    ctx.fillStyle = 'rgba(148, 163, 184, 0.7)';
    ctx.font = '8px JetBrains Mono';
    ctx.fillText('d(sₙ,s*)', chartX, chartY - 4);
    ctx.fillText(`λ=${(snap.lambda || 0).toFixed(3)}`, chartX, chartY + chartH + 12);
  }

  const DEEP_MODULES = new Set([
    'TimespaceTokenCoreModule',
    'HeroicLLMEAOrchestrator',
    'HeroicImageOrchestrator',
  ]);

  const DISPATCH_PRESETS = {
    TimespaceTokenCoreModule: {
      tracks: [{
        name: 'layer0',
        coordinate: { time_index: 0, space_depth: 0, timescale: 'macro' },
        state: {
          stability: 0.85, latent_tension: 0.2, depth: 1,
          fluctuation_severity: 0.1, bottleneck_risk: 0.15,
        },
        transformation: 'meme_synthesis',
      }],
    },
    HeroicLLMEAOrchestrator: {
      action: 'propose',
      prompt: 'cyberpunk campfire synthesis',
      n_proposals: 2,
      theme: 'campfire',
    },
    HeroicImageOrchestrator: {
      action: 'submit',
      prompt: 'cyberpunk campfire ALTE_Frau_95g',
    },
  };

  async function fetchBridgeStatus() {
    const dot = document.getElementById('bridge-status-dot');
    const badge = document.getElementById('bridge-transport-badge');
    try {
      const r = await fetch('/api/bridge/ipc/status');
      const st = await r.json();
      const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
      const ok = st.ok !== false;
      if (dot) {
        dot.className = ok ? 'status-online' : 'status-warning';
      }
      const transport = st.transport || 'unknown';
      set('bridge-transport', transport);
      if (badge) badge.textContent = transport.toUpperCase();
      set('bridge-module-count', st.module_count ?? (st.modules || []).length ?? '--');
      const ping = st.ping || {};
      set('bridge-ping', ping.pong ? 'pong' : (ok ? 'ok' : 'fail'));

      const modulesEl = document.getElementById('bridge-modules');
      const modules = st.modules || [];
      if (modulesEl) {
        modulesEl.innerHTML = modules.map((m) => {
          const deep = DEEP_MODULES.has(m) ? ' deep' : '';
          return `<span class="bridge-module-chip${deep}">${m}</span>`;
        }).join('');
      }

      const select = document.getElementById('bridge-module-select');
      if (select && modules.length) {
        const current = select.value;
        select.innerHTML = modules.map((m) =>
          `<option value="${m}"${DEEP_MODULES.has(m) ? ' selected' : ''}>${m}</option>`
        ).join('');
        if (modules.includes(current)) select.value = current;
      }
      return st;
    } catch (err) {
      if (dot) dot.className = 'status-offline';
      const res = document.getElementById('bridge-dispatch-result');
      if (res) res.textContent = `Bridge offline: ${err.message}`;
      return null;
    }
  }

  async function runBridgeDispatch() {
    const select = document.getElementById('bridge-module-select');
    const resultEl = document.getElementById('bridge-dispatch-result');
    const btn = document.getElementById('bridge-dispatch-btn');
    if (!select || !resultEl) return;
    const module = select.value;
    const payload = DISPATCH_PRESETS[module] || {};
    if (btn) btn.disabled = true;
    resultEl.textContent = `Dispatching ${module}…`;
    try {
      const r = await fetch('/api/bridge/ipc/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ module, payload }),
      });
      const data = await r.json();
      resultEl.textContent = JSON.stringify(data, null, 2);
      events.unshift({ type: 'bridge_dispatch', msg: `${module} → ${data.ok !== false ? 'ok' : 'fail'}` });
      renderEvents();
    } catch (err) {
      resultEl.textContent = `Error: ${err.message}`;
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  function setPollTimer(name, fn, ms) {
    if (pollTimers[name]) clearInterval(pollTimers[name]);
    pollTimers[name] = setInterval(fn, ms);
  }

  function applyUiSettings(ui) {
    ui = ui || {};
    const bridgePanel = document.getElementById('bridge-panel');
    const phonePanel = document.getElementById('phone-panel');
    if (bridgePanel) bridgePanel.classList.toggle('panel-hidden', ui.bridge_panel === false);
    if (phonePanel) phonePanel.classList.toggle('panel-hidden', ui.phone_link_panel === false);
    if (ui.event_stream_max) maxEvents = parseInt(ui.event_stream_max, 10) || 500;
    const bridgeMs = parseInt(ui.poll_bridge_ms, 10) || 4000;
    const phoneMs = parseInt(ui.poll_phone_ms, 10) || 8000;
    const connMs = parseInt(ui.poll_connectivity_ms, 10) || 8000;
    const metricsMs = parseInt(ui.poll_metrics_ms, 10) || 1200;
    setPollTimer('bridge', fetchBridgeStatus, bridgeMs);
    setPollTimer('phone', fetchPhoneLinkStatus, phoneMs);
    setPollTimer('connectivity', fetchConnectivity, connMs);
    setPollTimer('metrics', fetchMetrics, metricsMs);
    fetchBridgeStatus();
    fetchPhoneLinkStatus();
    fetchConnectivity();
    fetchMetrics();
  }

  function initBridgeUI() {
    const dispatchBtn = document.getElementById('bridge-dispatch-btn');
    const refreshBtn = document.getElementById('bridge-refresh-btn');
    if (dispatchBtn) dispatchBtn.addEventListener('click', runBridgeDispatch);
    if (refreshBtn) refreshBtn.addEventListener('click', fetchBridgeStatus);
  }

  async function fetchPhoneLinkStatus() {
    const dot = document.getElementById('phone-status-dot');
    const badge = document.getElementById('phone-status-badge');
    const feed = document.getElementById('phone-feed');
    const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
    try {
      const r = await fetch('/api/phone-link/status');
      const st = await r.json();
      const ok = st.connected === true;
      if (dot) dot.className = ok ? 'status-online' : (st.host_running ? 'status-warning' : 'status-offline');
      if (badge) badge.textContent = ok ? 'VERBUNDEN' : (st.host_running ? 'HOST' : 'OFFLINE');
      set('phone-msg-count', st.message_count ?? '--');
      set('phone-conv-count', st.conversation_count ?? '--');
      set('phone-unread', st.unread_total ?? '--');
      if (feed) {
        const msgs = st.recent_messages || [];
        if (!msgs.length) {
          feed.innerHTML = '<div class="phone-feed-empty">Keine gespiegelten Nachrichten.</div>';
        } else {
          feed.innerHTML = msgs.map((m) => {
            const ts = m.timestamp ? new Date(m.timestamp).toLocaleString('de-DE') : '';
            const from = m.from_masked || m.from || '?';
            const body = (m.body_preview || '').replace(/</g, '&lt;');
            return `<div class="phone-feed-item"><span class="phone-feed-from">${from}</span><span class="phone-feed-ts">${ts}</span><div class="phone-feed-body">${body}</div></div>`;
          }).join('');
        }
      }
      return st;
    } catch (err) {
      if (dot) dot.className = 'status-offline';
      if (feed) feed.textContent = `Phone Link offline: ${err.message}`;
      return null;
    }
  }

  function initPhoneLinkUI() { /* polling via applyUiSettings */ }

  async function fetchConnectivity() {
    const dot = document.getElementById('connectivity-status-dot');
    const badge = document.getElementById('connectivity-status-badge');
    const grid = document.getElementById('conn-access-grid');
    const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
    try {
      const [disc, conn] = await Promise.all([
        fetch('/api/discovery').then((r) => r.json()),
        fetch('/api/connectivity').then((r) => r.json()),
      ]);
      set('conn-lan-ip', disc.lan_ip || '--');
      set('conn-device-id', (disc.device_id || '--').slice(0, 16));
      set('conn-port', disc.port ?? '--');
      const watchLink = document.getElementById('conn-watch-link');
      if (watchLink && disc.watch_url) watchLink.href = disc.watch_url;
      const allOk = conn.all_ok === true;
      if (dot) dot.className = allOk ? 'status-online' : 'status-warning';
      if (badge) badge.textContent = allOk ? 'VERBUNDEN' : 'TEILWEISE';
      if (grid && conn.access_points) {
        grid.innerHTML = Object.entries(conn.access_points).map(([name, st]) => {
          const ok = st && st.ok === true;
          const detail = st.transport || st.cloud_sync || st.message_count || st.rooms || st.queue_len;
          const detailTxt = detail !== undefined && detail !== null ? ` · ${detail}` : '';
          return `<div class="conn-ap-row ${ok ? 'ok' : 'warn'}"><span>${name}</span><span>${ok ? 'OK' : '—'}${detailTxt}</span></div>`;
        }).join('');
      }
      return { disc, conn };
    } catch (err) {
      if (dot) dot.className = 'status-offline';
      if (grid) grid.textContent = `Connectivity offline: ${err.message}`;
      return null;
    }
  }

  function initConnectivityUI() {
    const copyBtn = document.getElementById('conn-copy-lan-btn');
    if (copyBtn) {
      copyBtn.addEventListener('click', async () => {
        try {
          const disc = await fetch('/api/discovery').then((r) => r.json());
          const url = disc.lan_base || disc.watch_url || location.origin;
          await navigator.clipboard.writeText(url);
          copyBtn.textContent = 'Kopiert!';
          setTimeout(() => { copyBtn.textContent = 'LAN kopieren'; }, 1500);
        } catch (_) { /* ignore */ }
      });
    }
  }

  function getDraftValue(key, spec) {
    const scope = spec.scope === 'ui' ? 'ui' : 'env';
    const store = settingsDraft[scope] || {};
    const uiKey = key.startsWith('ui.') ? key.slice(3) : key;
    const lookup = scope === 'ui' ? (store[uiKey] !== undefined ? store[uiKey] : store[key]) : store[key];
    if (lookup !== undefined) return lookup;
    if (spec.type === 'bool') return false;
    if (spec.type === 'multi_enum') return [];
    return spec.default || '';
  }

  function renderSettingsGroup(groupId) {
    const body = document.getElementById('settings-body');
    if (!body || !settingsSchema) return;
    const specs = settingsSchema.settings.filter((s) => s.group === groupId);
    body.innerHTML = `<div class="settings-group active" data-group="${groupId}">` +
      specs.map((spec) => {
        const val = getDraftValue(spec.key, spec);
        let control = '';
        if (spec.type === 'bool') {
          const on = val === true || val === '1' || val === 1;
          control = `<label class="settings-toggle"><input type="checkbox" data-key="${spec.key}" ${on ? 'checked' : ''}><span class="settings-toggle-slider"></span></label>`;
        } else if (spec.type === 'enum') {
          const opts = (spec.options || []).map((o) =>
            `<option value="${o.value}"${String(val) === String(o.value) ? ' selected' : ''}>${o.label}</option>`
          ).join('');
          control = `<select class="settings-select" data-key="${spec.key}">${opts}</select>`;
        } else if (spec.type === 'multi_enum') {
          const selected = Array.isArray(val) ? val : String(val || '').split(',').filter(Boolean);
          control = `<div class="settings-multi">${(spec.options || []).map((o) => {
            const chk = selected.includes(o.value) ? ' checked' : '';
            return `<label><input type="checkbox" data-key="${spec.key}" data-multi value="${o.value}"${chk}> ${o.label}</label>`;
          }).join('')}</div>`;
        }
        return `<div class="settings-row"><div><div class="settings-label">${spec.label}</div><div class="settings-desc">${spec.description || ''}</div></div><div class="settings-control">${control}</div></div>`;
      }).join('') + '</div>';

    body.querySelectorAll('input[data-key]:not([data-multi])').forEach((el) => {
      el.addEventListener('change', () => {
        const spec = settingsSchema.settings.find((s) => s.key === el.dataset.key);
        const scope = spec.scope === 'ui' ? 'ui' : 'env';
        const uiKey = el.dataset.key.startsWith('ui.') ? el.dataset.key.slice(3) : el.dataset.key;
        settingsDraft[scope][uiKey] = el.checked;
      });
    });
    body.querySelectorAll('select[data-key]').forEach((el) => {
      el.addEventListener('change', () => {
        const spec = settingsSchema.settings.find((s) => s.key === el.dataset.key);
        const scope = spec.scope === 'ui' ? 'ui' : 'env';
        const uiKey = el.dataset.key.startsWith('ui.') ? el.dataset.key.slice(3) : el.dataset.key;
        settingsDraft[scope][uiKey] = el.value;
      });
    });
    body.querySelectorAll('input[data-multi]').forEach((el) => {
      el.addEventListener('change', () => {
        const key = el.dataset.key;
        const spec = settingsSchema.settings.find((s) => s.key === key);
        const scope = spec.scope === 'ui' ? 'ui' : 'env';
        const checked = [...body.querySelectorAll(`input[data-multi][data-key="${key}"]:checked`)].map((c) => c.value);
        settingsDraft[scope][key] = checked;
      });
    });
  }

  function renderSettingsTabs() {
    const tabs = document.getElementById('settings-tabs');
    if (!tabs || !settingsSchema) return;
    tabs.innerHTML = settingsSchema.groups.map((g) =>
      `<button type="button" class="settings-tab${g.id === settingsActiveTab ? ' active' : ''}" data-tab="${g.id}">${g.label}</button>`
    ).join('');
    tabs.querySelectorAll('[data-tab]').forEach((btn) => {
      btn.addEventListener('click', () => {
        settingsActiveTab = btn.dataset.tab;
        tabs.querySelectorAll('.settings-tab').forEach((t) => t.classList.toggle('active', t.dataset.tab === settingsActiveTab));
        renderSettingsGroup(settingsActiveTab);
      });
    });
    renderSettingsGroup(settingsActiveTab);
  }

  async function openSettings() {
    const overlay = document.getElementById('settings-overlay');
    const status = document.getElementById('settings-status');
    if (!overlay) return;
    if (status) status.textContent = 'Lade…';
    try {
      const [schema, values] = await Promise.all([
        fetch('/api/settings/schema').then((r) => r.json()),
        fetch('/api/settings').then((r) => r.json()),
      ]);
      settingsSchema = schema;
      settingsDraft = { env: { ...values.env }, ui: { ...values.ui } };
      renderSettingsTabs();
      overlay.hidden = false;
      if (status) status.textContent = '';
    } catch (err) {
      if (status) status.textContent = `Fehler: ${err.message}`;
    }
  }

  function closeSettings() {
    const overlay = document.getElementById('settings-overlay');
    if (overlay) overlay.hidden = true;
  }

  async function saveSettings() {
    const status = document.getElementById('settings-status');
    if (status) status.textContent = 'Speichern…';
    const payload = {};
    (settingsSchema.settings || []).forEach((spec) => {
      const scope = spec.scope === 'ui' ? 'ui' : 'env';
      const uiKey = spec.key.startsWith('ui.') ? spec.key.slice(3) : spec.key;
      const v = settingsDraft[scope][uiKey] !== undefined ? settingsDraft[scope][uiKey] : settingsDraft[scope][spec.key];
      if (v !== undefined) payload[spec.key] = v;
    });
    try {
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ settings: payload }),
      });
      const data = await res.json();
      if (data.values) {
        settingsDraft = { env: { ...data.values.env }, ui: { ...data.values.ui } };
        applyUiSettings(data.values.ui);
      }
      if (status) status.textContent = `Gespeichert (${(data.applied_env || []).length} env, ${(data.applied_ui || []).length} ui)`;
      events.unshift({ type: 'settings', msg: 'Einstellungen aktualisiert' });
      renderEvents();
      setTimeout(closeSettings, 600);
    } catch (err) {
      if (status) status.textContent = `Fehler: ${err.message}`;
    }
  }

  async function resetSettings() {
    const status = document.getElementById('settings-status');
    if (status) status.textContent = 'Setze Standard…';
    try {
      const data = await fetch('/api/settings/reset', { method: 'POST' }).then((r) => r.json());
      if (data.values) {
        settingsDraft = { env: { ...data.values.env }, ui: { ...data.values.ui } };
        applyUiSettings(data.values.ui);
        renderSettingsTabs();
      }
      if (status) status.textContent = 'Standard wiederhergestellt';
    } catch (err) {
      if (status) status.textContent = `Fehler: ${err.message}`;
    }
  }

  function initSettingsUI() {
    const openBtn = document.getElementById('settings-open-btn');
    const closeBtn = document.getElementById('settings-close-btn');
    const cancelBtn = document.getElementById('settings-cancel-btn');
    const saveBtn = document.getElementById('settings-save-btn');
    const resetBtn = document.getElementById('settings-reset-btn');
    const overlay = document.getElementById('settings-overlay');
    if (openBtn) openBtn.addEventListener('click', openSettings);
    if (closeBtn) closeBtn.addEventListener('click', closeSettings);
    if (cancelBtn) cancelBtn.addEventListener('click', closeSettings);
    if (saveBtn) saveBtn.addEventListener('click', saveSettings);
    if (resetBtn) resetBtn.addEventListener('click', resetSettings);
    if (overlay) overlay.addEventListener('click', (e) => { if (e.target === overlay) closeSettings(); });
  }

  async function bootSettings() {
    try {
      const values = await fetch('/api/settings').then((r) => r.json());
      applyUiSettings(values.ui);
    } catch (_) {
      applyUiSettings({ bridge_panel: true, phone_link_panel: true, poll_bridge_ms: '4000', poll_phone_ms: '8000', poll_metrics_ms: '1200' });
    }
  }

  connect();
  setPollTimer('viz', pollViz, 1800);
  pollViz();
  initBridgeUI();
  initPhoneLinkUI();
  initConnectivityUI();
  initSettingsUI();
  bootSettings();

  // Init layer placeholders
  const initLayers = {};
  for (let i = 0; i <= 6; i++) initLayers[i] = { util: 40 + i * 5, status: 'STABLE' };
  renderLayers(initLayers);
  renderHyperThreads(initLayers);
})();