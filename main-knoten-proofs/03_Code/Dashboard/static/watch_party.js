(function () {
  'use strict';

  const roomId = window.WATCH_ROOM_ID || '';
  const initialVideoId = window.WATCH_VIDEO_ID || '';
  const serverSync = window.WATCH_SERVER_SYNC === true;
  const pollMs = Number(window.WATCH_POLL_MS) || 2000;
  const pollActiveMs = 2000;
  const realtimeStaleMs = 6000;
  const rtConfig = window.WATCH_REALTIME_CONFIG || {};
  const DRIFT_SEEK = 0.35;
  const SUPPRESS_MS = 100;
  const EXTRAPOLATE_MS = 200;
  const VIDEO_RETRY_MS = 2500;

  let ws = null;
  let player = null;
  let playerReady = false;
  let pendingState = null;
  let pendingPlayAfterLoad = false;
  let suppressEvents = false;
  let suppressTimer = null;
  let reconnectTimer = null;
  let pollTimer = null;
  let extrapolateTimer = null;
  let lastServerRevision = 0;
  let lastServerRev = 0;
  let lastAppliedKey = '';
  let cmdInFlight = false;
  let realtimeConnected = false;
  let lastRealtimeAt = 0;
  let realtimeChannel = null;
  let lastPlaybackState = null;
  let videoRetryTimer = null;
  let lastLoadedVideoId = '';
  const deviceId = (() => {
    const key = 'fusion-watch-device-id';
    let id = localStorage.getItem(key);
    if (!id) {
      id = `dev-${Math.random().toString(36).slice(2, 10)}`;
      localStorage.setItem(key, id);
    }
    return id;
  })();
  const urlParams = new URLSearchParams(location.search);
  const forcedFollower = urlParams.get('follower') === '1' || window.WATCH_ROLE === 'follower';
  let isController = !forcedFollower && (window.WATCH_ROLE === 'controller' || !urlParams.has('follower'));

  const $ = (id) => document.getElementById(id);

  const YT_PATTERNS = [
    /(?:youtube\.com\/watch\?.*v=|youtu\.be\/|youtube\.com\/embed\/)([A-Za-z0-9_-]{11})/,
    /^([A-Za-z0-9_-]{11})$/,
  ];

  function normalizeVideoId(raw) {
    const text = (raw || '').trim();
    if (!text) return '';
    for (const pat of YT_PATTERNS) {
      const m = text.match(pat);
      if (m) return m[1];
    }
    return '';
  }

  function setStatus(text) {
    const el = $('watch-status');
    if (el) el.textContent = text;
  }

  function lanBase() {
    return (window.WATCH_LAN_BASE || location.origin).replace(/\/$/, '');
  }

  function joinUrl(forFollower) {
    const base = `${lanBase()}/watch/${roomId}`;
    return forFollower ? `${base}?follower=1` : base;
  }

  function localUrl() {
    return `${location.origin}/watch/${roomId}`;
  }

  function setSuppress(ms) {
    suppressEvents = true;
    clearTimeout(suppressTimer);
    suppressTimer = setTimeout(() => { suppressEvents = false; }, ms);
  }

  function expectedPosition(st) {
    if (!st) return 0;
    const now = Date.now() / 1000;
    const base = Number(st.position) || 0;
    if (!st.playing) return base;
    const updatedAt = Number(st.updated_at) || now;
    return base + Math.max(0, now - updatedAt);
  }

  function updateRoleUi() {
    const badge = $('role-badge');
    const controls = document.querySelector('.watch-controls');
    if (badge) {
      badge.textContent = isController ? '● STEUERUNG' : '○ FOLLOWER (nur Ansehen)';
      badge.classList.toggle('follower', !isController);
    }
    if (controls) controls.classList.toggle('follower-mode', !isController);
    const loadBtn = $('load-video-btn');
    const videoInput = $('video-url');
    if (loadBtn) loadBtn.disabled = !isController;
    if (videoInput) videoInput.disabled = !isController;
  }

  function applyControllerFromState(st) {
    const cid = st.controller_id || '';
    if (!cid) return;
    if (forcedFollower) {
      isController = false;
    } else if (cid === deviceId) {
      isController = true;
    } else {
      isController = false;
    }
    updateRoleUi();
  }

  function updateJoinDisplay() {
    const joinEl = $('join-url');
    if (joinEl) joinEl.textContent = joinUrl(true);
    const localEl = $('local-url');
    if (localEl) localEl.textContent = localUrl();
    const roomInput = $('room-id');
    if (roomInput) roomInput.value = roomId;
    updateRoleUi();
    renderRoomQr();
    if (isController) {
      setStatus('Steuerungsseite — Play/Pause/Laden nur hier');
    } else {
      setStatus('Follower — folgt der Steuerungsseite, sendet keine Befehle');
    }
  }

  function rowToWatchState(row) {
    const now = Date.now() / 1000;
    const updatedAt = Number(row.updated_at) || now;
    const playing = !!row.playing;
    let position = Number(row.position) || 0;
    if (playing) position += Math.max(0, now - updatedAt);
    const payload = row.payload || {};
    return {
      type: 'watch_state',
      room_id: row.room_id,
      video_id: row.video_id || '',
      position: Math.round(position * 100) / 100,
      playing,
      server_time: now,
      updated_at: updatedAt,
      revision: Number(payload.revision || row.revision || 0),
      controller_id: String(payload.controller_id || ''),
      sync_authority: 'server',
      sync_source: 'realtime',
    };
  }

  function stateFingerprint(st) {
    return [
      st.video_id || '',
      st.playing ? 1 : 0,
      Math.round((Number(st.position) || 0) * 10),
      Number(st.updated_at) || 0,
      Number(st.revision) || 0,
    ].join('|');
  }

  function shouldApplyState(st) {
    const ts = Number(st.updated_at) || 0;
    const rev = Number(st.revision) || 0;
    const fp = stateFingerprint(st);
    if (fp === lastAppliedKey) return false;
    if (rev > 0 && rev < lastServerRev) return false;
    if (rev <= lastServerRev && ts < lastServerRevision - 0.001) return false;
    if (ts < lastServerRevision - 0.001) return false;
    if (cmdInFlight && st.sync_source === 'local_fast' && ts <= lastServerRevision && rev <= lastServerRev) {
      return false;
    }
    return true;
  }

  function rememberPlaybackState(st) {
    lastPlaybackState = {
      playing: !!st.playing,
      position: Number(st.position) || 0,
      updated_at: Number(st.updated_at) || Date.now() / 1000,
      video_id: st.video_id || '',
    };
  }

  function isPlayerApiReady() {
    return playerReady && player && typeof player.loadVideoById === 'function';
  }

  function getCurrentVideoId() {
    if (!isPlayerApiReady() || !player.getVideoData) return '';
    try {
      const data = player.getVideoData();
      return normalizeVideoId((data && data.video_id) || '');
    } catch (_) {
      return '';
    }
  }

  function playerNeedsLoad(targetVid) {
    if (!targetVid) return false;
    const current = getCurrentVideoId();
    if (!current || current !== targetVid) return true;
    try {
      const state = player.getPlayerState();
      if (state === YT.PlayerState.UNSTARTED || state === YT.PlayerState.ENDED) return true;
      const dur = player.getDuration();
      if (!dur || !Number.isFinite(dur) || dur <= 0) return true;
    } catch (_) {
      return true;
    }
    return false;
  }

  function scheduleVideoRetry(videoId, startSeconds, shouldPlay) {
    clearTimeout(videoRetryTimer);
    videoRetryTimer = setTimeout(() => {
      if (!isPlayerApiReady() || !videoId) return;
      if (playerNeedsLoad(videoId)) {
        loadVideo(videoId, startSeconds, shouldPlay, true);
      }
    }, VIDEO_RETRY_MS);
  }

  function resizePlayer() {
    if (!isPlayerApiReady() || !player.setSize) return;
    const dim = playerDimensions();
    try {
      player.setSize(dim.width, dim.height);
    } catch (_) { /* ignore */ }
  }

  function loadVideo(videoId, startSeconds, shouldPlay, isRetry) {
    const vid = normalizeVideoId(videoId);
    if (!isPlayerApiReady() || !vid) return;
    if (!isRetry && !playerNeedsLoad(vid) && lastLoadedVideoId === vid) return;
    pendingPlayAfterLoad = !!shouldPlay;
    lastLoadedVideoId = vid;
    setSuppress(SUPPRESS_MS);
    resizePlayer();
    try {
      player.loadVideoById({
        videoId: vid,
        startSeconds: Math.max(0, Number(startSeconds) || 0),
      });
      setStatus(`Video geladen: ${vid}`);
      scheduleVideoRetry(vid, startSeconds, shouldPlay);
    } catch (err) {
      setStatus(`Video-Ladefehler: ${err.message}`);
    }
  }

  function syncFromServer(st, opts) {
    if (!st) return;
    if (!shouldApplyState(st)) return;

    if (!isPlayerApiReady()) {
      pendingState = st;
      return;
    }

    const rev = Number(st.updated_at) || 0;
    const revision = Number(st.revision) || 0;
    if (rev > lastServerRevision) lastServerRevision = rev;
    if (revision > lastServerRev) lastServerRev = revision;
    lastAppliedKey = stateFingerprint(st);
    rememberPlaybackState(st);
    applyControllerFromState(st);

    const targetPos = expectedPosition(st);
    const vid = normalizeVideoId(st.video_id);
    const suppressMs = opts && opts.localEcho ? 60 : (isController ? SUPPRESS_MS : 320);
    setSuppress(suppressMs);

    try {
      if (vid && playerNeedsLoad(vid)) {
        loadVideo(vid, targetPos, st.playing);
        return;
      }
      if (!vid) {
        setStatus('Kein Video im Raum — URL oben einfügen und Laden klicken');
        return;
      }

      const state = player.getPlayerState();
      if (st.playing && state !== YT.PlayerState.PLAYING) {
        player.playVideo();
      } else if (!st.playing && state === YT.PlayerState.PLAYING) {
        player.pauseVideo();
      }
      const local = player.getCurrentTime() || 0;
      if (Math.abs(local - targetPos) > DRIFT_SEEK) {
        player.seekTo(targetPos, true);
      }
    } catch (err) {
      setStatus(`Sync-Fehler: ${err.message}`);
    }
  }

  async function fetchAndApplyServerState() {
    if (!roomId) return;
    try {
      const r = await fetch(`/api/watch/room/${roomId}/state`);
      const data = await r.json();
      if (data.ok && data.state) {
        syncFromServer({ ...data.state, sync_source: data.sync_source || 'poll' });
      }
    } catch (_) { /* retry later */ }
  }

  async function initRealtime() {
    if (!serverSync || !rtConfig.enabled || !rtConfig.url || !rtConfig.anon_key) return false;
    const lib = window.supabase;
    if (!lib || typeof lib.createClient !== 'function') return false;
    try {
      const sb = lib.createClient(rtConfig.url, rtConfig.anon_key);
      realtimeChannel = sb.channel(`watch-room-${roomId}`);
      realtimeChannel.on(
        'postgres_changes',
        {
          event: '*',
          schema: rtConfig.schema || 'public',
          table: rtConfig.table || 'watch_rooms',
          filter: `room_id=eq.${roomId}`,
        },
        (payload) => {
          if (!payload.new) return;
          lastRealtimeAt = Date.now();
          syncFromServer(rowToWatchState(payload.new));
        }
      );
      realtimeChannel.subscribe((status) => {
        if (status === 'SUBSCRIBED') {
          realtimeConnected = true;
          lastRealtimeAt = Date.now();
          setStatus('Realtime + WS — Sync aktiv');
          fetchAndApplyServerState();
        } else if (status === 'CHANNEL_ERROR' || status === 'TIMED_OUT' || status === 'CLOSED') {
          realtimeConnected = false;
          setStatus('Realtime offline — WS/Poll aktiv');
        }
      });
      return true;
    } catch (err) {
      setStatus(`Realtime Fehler: ${err.message}`);
      return false;
    }
  }

  async function renderRoomQr() {
    const canvas = $('room-qr');
    const fallback = $('room-qr-fallback');
    const url = joinUrl(true);
    if (!canvas && !fallback) return;
    try {
      if (window.QRCode && canvas) {
        await QRCode.toCanvas(canvas, url, {
          width: 220,
          margin: 1,
          color: { dark: '#0a0a0f', light: '#ffffff' },
        });
        if (fallback) fallback.hidden = true;
        return;
      }
    } catch (_) { /* fallback */ }
    if (fallback) {
      fallback.src = `/api/watch/room/${roomId}/qr?size=220`;
      fallback.hidden = false;
      if (canvas) canvas.style.display = 'none';
    }
  }

  async function sendCmd(cmd, extra) {
    if (!isController) return;
    const body = { cmd, device_id: deviceId, ...extra };
    if (serverSync) {
      if (cmdInFlight) return;
      cmdInFlight = true;
      try {
        const r = await fetch(`/api/watch/room/${roomId}/cmd`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });
        const data = await r.json();
        if (data.ok && data.state) {
          const st = { ...data.state, sync_source: data.sync_source || 'local_fast' };
          syncFromServer(st, { localEcho: true });
        } else if (data.error === 'not_controller') {
          isController = false;
          updateRoleUi();
          setStatus('Nur die Steuerungsseite darf Befehle senden');
        }
      } catch (err) {
        setStatus(`Server-Cmd Fehler: ${err.message}`);
      } finally {
        cmdInFlight = false;
      }
      return;
    }
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    ws.send(JSON.stringify({ action: 'watch_cmd', cmd, device_id: deviceId, ...extra }));
  }

  function startExtrapolation() {
    clearInterval(extrapolateTimer);
    extrapolateTimer = setInterval(() => {
      if (!isPlayerApiReady() || suppressEvents || cmdInFlight || !lastPlaybackState?.playing) return;
      const expected = expectedPosition(lastPlaybackState);
      const local = player.getCurrentTime() || 0;
      if (Math.abs(local - expected) > DRIFT_SEEK) {
        setSuppress(60);
        player.seekTo(expected, true);
      }
    }, EXTRAPOLATE_MS);
  }

  function onPlayerReady() {
    playerReady = true;
    resizePlayer();
    setStatus('Player bereit — Video wird geladen…');

    if (pendingState) {
      syncFromServer(pendingState);
      pendingState = null;
    } else if (normalizeVideoId(initialVideoId)) {
      loadVideo(initialVideoId, 0, false);
    }
    fetchAndApplyServerState();

    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'watch_join' }));
    }
    startExtrapolation();
  }

  function onPlayerStateChange(event) {
    if (pendingPlayAfterLoad) {
      if (event.data === YT.PlayerState.CUED || event.data === YT.PlayerState.BUFFERING) {
        pendingPlayAfterLoad = false;
        setSuppress(80);
        player.playVideo();
      }
    }
    if (!isController || suppressEvents || !isPlayerApiReady() || cmdInFlight) return;
    const pos = player.getCurrentTime() || 0;
    if (event.data === YT.PlayerState.PLAYING) {
      sendCmd('play', { position: pos });
    } else if (event.data === YT.PlayerState.PAUSED) {
      sendCmd('pause', { position: pos });
    }
  }

  function onPlayerError(event) {
    setStatus(`YouTube-Fehler ${event.data} — anderes Video probieren`);
  }

  function loadYouTubeApi() {
    return new Promise((resolve) => {
      if (window.YT && window.YT.Player) {
        resolve();
        return;
      }
      const prev = window.onYouTubeIframeAPIReady;
      window.onYouTubeIframeAPIReady = () => {
        if (prev) prev();
        resolve();
      };
      const tag = document.createElement('script');
      tag.src = 'https://www.youtube.com/iframe_api';
      document.head.appendChild(tag);
    });
  }

  function playerDimensions() {
    const el = $('player');
    const w = el ? Math.max(el.clientWidth || 0, 320) : 640;
    return { width: w, height: Math.round(w * 9 / 16) };
  }

  function initPlayer() {
    const dim = playerDimensions();
    const bootVid = normalizeVideoId(initialVideoId);
    player = new YT.Player('player', {
      width: dim.width,
      height: dim.height,
      videoId: bootVid || undefined,
      playerVars: {
        autoplay: 0,
        rel: 0,
        modestbranding: 1,
        playsinline: 1,
        enablejsapi: 1,
        origin: location.origin,
      },
      events: {
        onReady: onPlayerReady,
        onStateChange: onPlayerStateChange,
        onError: onPlayerError,
      },
    });
  }

  async function pollServerState() {
    if (!serverSync || !roomId) return;
    await fetchAndApplyServerState();
  }

  function startServerPoll() {
    if (!serverSync) return;
    clearInterval(pollTimer);
    pollTimer = setInterval(() => {
      const staleRealtime = realtimeConnected && (Date.now() - lastRealtimeAt > realtimeStaleMs);
      if (!realtimeConnected || staleRealtime) {
        pollServerState();
        return;
      }
      if (pollMs >= pollActiveMs) pollServerState();
    }, pollActiveMs);
  }

  function connectWs() {
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${proto}//${location.host}/ws/watch/${roomId}`);
    ws.onopen = () => {
      ws.send(JSON.stringify({ action: 'watch_join' }));
    };
    ws.onclose = () => {
      clearTimeout(reconnectTimer);
      reconnectTimer = setTimeout(connectWs, 1500);
    };
    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        if (msg.type === 'watch_state') {
          syncFromServer({ ...msg, sync_source: msg.sync_source || 'websocket' });
        } else if (msg.type === 'watch_meta') {
          const badge = $('viewer-count');
          if (badge) badge.textContent = `${msg.viewers || 0} Zuschauer`;
        }
      } catch (_) { /* ignore */ }
    };
  }

  function bindUi() {
    $('copy-link-btn')?.addEventListener('click', async () => {
      const url = joinUrl(true);
      try {
        await navigator.clipboard.writeText(url);
        setStatus('WLAN-Link kopiert');
      } catch (_) {
        setStatus(url);
      }
    });
    $('load-video-btn')?.addEventListener('click', () => {
      const url = ($('video-url')?.value || '').trim();
      if (!url) return;
      sendCmd('load', { video_id: url });
      setStatus('Video wird geladen…');
    });
  }

  function bindResize() {
    window.addEventListener('resize', () => {
      resizePlayer();
    });
  }

  async function boot() {
    if (!roomId) {
      setStatus('Kein Raum — bitte vom Dashboard erstellen');
      return;
    }
    updateJoinDisplay();
    bindUi();
    bindResize();
    await loadYouTubeApi();
    initPlayer();
    connectWs();
    await initRealtime();
    startServerPoll();
    if (isController && serverSync) {
      sendCmd('claim_controller', {});
    }
  }

  boot();
})();