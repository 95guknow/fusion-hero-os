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
        if (window.FusionVizDemo) window.FusionVizDemo.setLiveSnap(data.viz);
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
      if (window.FusionVizDemo) window.FusionVizDemo.setLiveSnap(snap);
    } catch (_) { /* Demo-Loop läuft unabhängig weiter */ }
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
    window.dispatchEvent(new CustomEvent('fusion-panels-visibility-change'));
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

  if (window.FusionResponsiveLayout) {
    window.FusionResponsiveLayout.init('#dashboard-grid');
    window.addEventListener('fusion-panels-visibility-change', () => {
      if (window.FusionResponsiveLayout?.relayout) window.FusionResponsiveLayout.relayout();
    });
  }

  if (window.FusionVizDemo) {
    requestAnimationFrame(() => requestAnimationFrame(() => window.FusionVizDemo.start()));
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