/**
 * Fusion Hero OS — Beispiel-Visualisierungen (Loop)
 * Erklärt Geisterjagd (latent → manifest) und Banach-Kontraktion (λ < 1)
 * unabhängig vom Backend; Live-Daten werden optional eingeblendet.
 */
(function () {
  const LAMBDA = 0.74;
  const GJ_PHASES = [
    '① Heuristik-Feld — latente Spuren sammeln sich',
    '② Akkumulation — Aktivierung steigt im Feld',
    '③ Emergenz — Schwelle überschritten → manifest',
  ];
  const BN_PHASES = [
    '① Start: s₀ weit entfernt vom Fixpunkt s* (Z*)',
    '② Banach-Schritt: sₙ₊₁ = s* + λ · (sₙ − s*)',
    '③ Kontraktion: Abstand d(sₙ,s*) → 0 bei λ < 1',
  ];

  let liveSnap = null;
  let rafId = null;
  let lastTs = 0;
  let gjPhase = 0;
  let gjPhaseT = 0;
  let bnPhase = 0;
  let bnPhaseT = 0;

  const gj = {
    ghosts: [],
    emerged: 0,
    heuristic: 0.5,
    cycle: 0,
  };

  const bn = {
    sStar: [0, 0],
    sN: [2.4, 1.7],
    trail: [],
    step: 0,
    distance: 0,
    holdT: 0,
    resetting: false,
  };

  function rand(a, b) {
    return a + Math.random() * (b - a);
  }

  function initGhosts() {
    gj.ghosts = [];
    for (let i = 0; i < 10; i++) {
      gj.ghosts.push({
        x: rand(0.1, 0.9),
        y: rand(0.08, 0.38),
        activation: rand(0.05, 0.25),
        manifest: false,
        mx: rand(0.2, 0.8),
        my: rand(0.1, 0.35),
        label: ['prompt', 'latent', 'trace', 'echo'][i % 4],
        pulse: rand(0, Math.PI * 2),
      });
    }
    gj.emerged = 0;
    gj.heuristic = 0.45;
    gj.cycle = 0;
    gjPhase = 0;
    gjPhaseT = 0;
  }

  function resetBanach() {
    bn.sN = [rand(1.8, 2.8), rand(1.2, 2.0)];
    bn.trail = [[bn.sN[0], bn.sN[1]]];
    bn.step = 0;
    bn.distance = dist(bn.sN, bn.sStar);
    bn.holdT = 0;
    bn.resetting = false;
    bnPhase = 0;
    bnPhaseT = 0;
  }

  function dist(a, b) {
    return Math.hypot(a[0] - b[0], a[1] - b[1]);
  }

  function fitCanvas(canvas) {
    const wrap = canvas.closest('.viz-canvas-wrap');
    const cssW = Math.max(280, wrap ? wrap.clientWidth : 480);
    const cssH = Math.max(175, Math.round(cssW * 10 / 16));
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.floor(cssW * dpr);
    canvas.height = Math.floor(cssH * dpr);
    canvas.style.width = `${cssW}px`;
    canvas.style.height = `${cssH}px`;
    const ctx = canvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { ctx, w: cssW, h: cssH };
  }

  function drawHeuristicGrid(ctx, t, W, zoneH) {
    const rows = 8;
    const cols = 8;
    const cellW = W / cols;
    const cellH = zoneH / rows;
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const wave = Math.sin(t * 1.2 + r * 0.65 + c * 0.45) * 0.5 + 0.5;
        const v = 0.25 + 0.55 * wave * gj.heuristic;
        const hue = 270 - v * 75;
        ctx.fillStyle = `hsla(${hue}, 72%, ${16 + v * 30}%, ${0.22 + v * 0.5})`;
        ctx.fillRect(c * cellW, r * cellH, cellW + 1, cellH + 1);
      }
    }
  }

  function tickGeisterjagd(dt) {
    gjPhaseT += dt;
    if (gjPhaseT > 4.5) {
      gjPhaseT = 0;
      gjPhase = (gjPhase + 1) % GJ_PHASES.length;
    }

    gj.heuristic = 0.42 + 0.28 * Math.sin(gj.cycle * 0.04);
    gj.cycle += dt * 60;

    let emergedNow = 0;
    gj.ghosts.forEach((g) => {
      g.pulse += dt * 3;
      const boost = gjPhase >= 1 ? 0.045 : 0.018;
      g.activation = Math.min(1, g.activation + boost * (0.6 + gj.heuristic));
      if (!g.manifest && g.activation >= 0.72 && gjPhase >= 2) {
        g.manifest = true;
        gj.emerged += 1;
        emergedNow += 1;
      }
    });

    if (gj.ghosts.every((g) => g.manifest) && gjPhaseT > 2) {
      initGhosts();
    }
  }

  function tickBanach(dt) {
    bnPhaseT += dt;
    if (bnPhaseT > 5) {
      bnPhaseT = 0;
      bnPhase = (bnPhase + 1) % BN_PHASES.length;
    }

    if (bn.resetting) {
      bn.holdT += dt;
      if (bn.holdT > 2.2) resetBanach();
      return;
    }

    bn.step += dt;
    if (bn.step < 0.38) return;
    bn.step = 0;

    const sx = bn.sStar[0];
    const sy = bn.sStar[1];
    const nx = sx + LAMBDA * (bn.sN[0] - sx);
    const ny = sy + LAMBDA * (bn.sN[1] - sy);
    bn.sN = [nx, ny];
    bn.trail.push([nx, ny]);
    if (bn.trail.length > 64) bn.trail.shift();
    bn.distance = dist(bn.sN, bn.sStar);

    if (bn.distance < 0.07) {
      bn.resetting = true;
      bn.holdT = 0;
      bnPhase = 2;
    }
  }

  function drawGeisterjagd(canvas) {
    const { ctx, w: W, h: H } = fitCanvas(canvas);
    ctx.fillStyle = '#08080c';
    ctx.fillRect(0, 0, W, H);

    const latentH = H * 0.44;
    drawHeuristicGrid(ctx, gj.cycle * 0.02, W, latentH);

    ctx.strokeStyle = 'rgba(124, 58, 237, 0.55)';
    ctx.setLineDash([5, 4]);
    ctx.beginPath();
    ctx.moveTo(0, latentH);
    ctx.lineTo(W, latentH);
    ctx.stroke();
    ctx.setLineDash([]);

    ctx.fillStyle = 'rgba(148, 163, 184, 0.85)';
    ctx.font = 'bold 10px JetBrains Mono, monospace';
    ctx.fillText('LATENT (Geister)', 10, 16);
    ctx.fillText('MANIFEST (Emergenz)', 10, latentH + 16);

    gj.ghosts.forEach((g) => {
      const ax = g.x * W;
      const ay = g.y * latentH;
      const pulse = 1 + Math.sin(g.pulse) * 0.15;
      const r = (4 + g.activation * 8) * pulse;
      const alpha = 0.3 + g.activation * 0.65;

      const grad = ctx.createRadialGradient(ax, ay, 0, ax, ay, r * 2.2);
      grad.addColorStop(0, `rgba(192, 132, 252, ${alpha})`);
      grad.addColorStop(1, 'rgba(124, 58, 237, 0)');
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(ax, ay, r * 2.2, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = `rgba(233, 213, 255, ${alpha})`;
      ctx.beginPath();
      ctx.arc(ax, ay, r, 0, Math.PI * 2);
      ctx.fill();

      if (g.manifest) {
        const mx = g.mx * W;
        const my = latentH + 12 + g.my * (H - latentH - 24);
        ctx.strokeStyle = `rgba(0, 212, 170, ${0.35 + g.activation * 0.45})`;
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(ax, ay);
        ctx.lineTo(mx, my);
        ctx.stroke();

        const mg = ctx.createRadialGradient(mx, my, 0, mx, my, 14);
        mg.addColorStop(0, 'rgba(0, 212, 170, 0.95)');
        mg.addColorStop(1, 'rgba(0, 212, 170, 0)');
        ctx.fillStyle = mg;
        ctx.beginPath();
        ctx.arc(mx, my, 14, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#00d4aa';
        ctx.beginPath();
        ctx.arc(mx, my, 5, 0, Math.PI * 2);
        ctx.fill();
      }
    });

    ctx.fillStyle = 'rgba(15, 23, 42, 0.88)';
    ctx.fillRect(8, H - 34, W - 16, 26);
    ctx.strokeStyle = 'rgba(124, 58, 237, 0.4)';
    ctx.strokeRect(8, H - 34, W - 16, 26);
    ctx.fillStyle = '#e9d5ff';
    ctx.font = '10px JetBrains Mono, monospace';
    ctx.fillText(GJ_PHASES[gjPhase], 14, H - 16);

    const cap = document.getElementById('gj-caption');
    if (cap) cap.textContent = GJ_PHASES[gjPhase];
  }

  function drawBanach(canvas) {
    const { ctx, w: W, h: H } = fitCanvas(canvas);
    ctx.fillStyle = '#08080c';
    ctx.fillRect(0, 0, W, H);

    const plotW = W * 0.62;
    const plotH = H * 0.82;
    const ox = plotW * 0.42;
    const oy = plotH * 0.55 + H * 0.06;
    const scale = Math.min(plotW, plotH) * 0.19;

    function toScreen(x, y) {
      return [ox + x * scale, oy - y * scale];
    }

    ctx.strokeStyle = 'rgba(51, 65, 85, 0.65)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, oy);
    ctx.lineTo(plotW, oy);
    ctx.moveTo(ox, H * 0.04);
    ctx.lineTo(ox, plotH + H * 0.04);
    ctx.stroke();

    if (bn.trail.length > 1) {
      ctx.strokeStyle = 'rgba(124, 58, 237, 0.55)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      bn.trail.forEach((p, i) => {
        const [sx, sy] = toScreen(p[0], p[1]);
        if (i === 0) ctx.moveTo(sx, sy);
        else ctx.lineTo(sx, sy);
      });
      ctx.stroke();
    }

    const [fx, fy] = toScreen(bn.sStar[0], bn.sStar[1]);
    ctx.fillStyle = '#fbbf24';
    ctx.beginPath();
    ctx.arc(fx, fy, 7, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#fde68a';
    ctx.font = 'bold 10px JetBrains Mono, monospace';
    ctx.fillText('s* (Z*)', fx + 10, fy - 6);

    const [nx, ny] = toScreen(bn.sN[0], bn.sN[1]);
    ctx.strokeStyle = 'rgba(0, 212, 170, 0.65)';
    ctx.setLineDash([4, 3]);
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(fx, fy);
    ctx.lineTo(nx, ny);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = '#00d4aa';
    ctx.beginPath();
    ctx.arc(nx, ny, 8, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#e2e8f0';
    ctx.fillText(`sₙ (Schritt ${bn.trail.length})`, nx + 10, ny + 4);

    const chartX = plotW + 14;
    const chartW = W - chartX - 10;
    const chartH = H * 0.72;
    const chartY = H * 0.1;
    ctx.strokeStyle = 'rgba(51, 65, 85, 0.55)';
    ctx.strokeRect(chartX, chartY, chartW, chartH);
    ctx.fillStyle = 'rgba(148, 163, 184, 0.8)';
    ctx.font = '9px JetBrains Mono, monospace';
    ctx.fillText('d → 0', chartX, chartY - 4);

    const maxD = Math.max(2.8, ...bn.trail.map((p) => dist(p, bn.sStar)));
    const dNow = bn.distance;
    const barH = (dNow / maxD) * chartH;
    ctx.fillStyle = 'rgba(192, 132, 252, 0.25)';
    ctx.fillRect(chartX + 2, chartY + 2, chartW - 4, chartH - 4);
    ctx.fillStyle = '#c084fc';
    ctx.fillRect(chartX + 4, chartY + chartH - barH, chartW - 8, barH);

    ctx.fillStyle = 'rgba(15, 23, 42, 0.9)';
    ctx.fillRect(8, 8, plotW - 16, 36);
    ctx.strokeStyle = 'rgba(0, 212, 170, 0.35)';
    ctx.strokeRect(8, 8, plotW - 16, 36);
    ctx.fillStyle = '#00d4aa';
    ctx.font = '11px JetBrains Mono, monospace';
    ctx.fillText(`sₙ₊₁ = s* + λ(sₙ − s*)   λ=${LAMBDA}`, 14, 22);
    ctx.fillStyle = '#94a3b8';
    ctx.font = '9px JetBrains Mono, monospace';
    ctx.fillText(`d(sₙ,s*) = ${dNow.toFixed(3)}`, 14, 36);

    if (bn.resetting) {
      ctx.fillStyle = 'rgba(0, 212, 170, 0.15)';
      ctx.fillRect(plotW * 0.15, H * 0.38, plotW * 0.7, 28);
      ctx.fillStyle = '#00d4aa';
      ctx.font = 'bold 11px JetBrains Mono, monospace';
      ctx.fillText('✓ Fixpunkt erreicht — Neustart…', plotW * 0.18, H * 0.38 + 18);
    }

    ctx.fillStyle = 'rgba(15, 23, 42, 0.88)';
    ctx.fillRect(8, H - 34, W - 16, 26);
    ctx.strokeStyle = 'rgba(0, 212, 170, 0.35)';
    ctx.strokeRect(8, H - 34, W - 16, 26);
    ctx.fillStyle = '#a7f3d0';
    ctx.font = '10px JetBrains Mono, monospace';
    ctx.fillText(BN_PHASES[bnPhase], 14, H - 16);

    const cap = document.getElementById('bn-caption');
    if (cap) cap.textContent = BN_PHASES[bnPhase];
  }

  function updateMetrics() {
    const set = (id, v) => {
      const el = document.getElementById(id);
      if (el) el.textContent = v;
    };
    const latent = gj.ghosts.filter((g) => !g.manifest).length;
    const manifest = gj.ghosts.filter((g) => g.manifest).length;
    set('gj-ghosts', `${latent}L / ${manifest}M`);
    set('gj-emerged', String(gj.emerged));
    set('gj-heuristic', gj.heuristic.toFixed(2));

    set('bn-lambda', LAMBDA.toFixed(3));
    set('bn-distance', bn.distance.toFixed(3));
    set('bn-fixpoint', '0, 0');

    if (liveSnap) {
      if (liveSnap.lambda != null) set('bn-lambda', Number(liveSnap.lambda).toFixed(3));
      if (liveSnap.distance != null) set('bn-distance', Number(liveSnap.distance).toFixed(3));
      if (liveSnap.heuristic_score != null) set('gj-heuristic', Number(liveSnap.heuristic_score).toFixed(2));
      if (liveSnap.emergence_total != null) set('gj-emerged', String(liveSnap.emergence_total));
      const lg = (liveSnap.ghosts || []).filter((g) => !g.manifest).length;
      const mg = (liveSnap.ghosts || []).filter((g) => g.manifest).length;
      if (liveSnap.ghosts?.length) set('gj-ghosts', `${lg}L / ${mg}M`);
    }
  }

  function frame(ts) {
    if (!lastTs) lastTs = ts;
    const dt = Math.min(0.05, (ts - lastTs) / 1000);
    lastTs = ts;

    tickGeisterjagd(dt);
    tickBanach(dt);

    const cGj = document.getElementById('canvas-geisterjagd');
    const cBn = document.getElementById('canvas-banach');
    if (cGj) drawGeisterjagd(cGj);
    if (cBn) drawBanach(cBn);
    updateMetrics();

    rafId = requestAnimationFrame(frame);
  }

  function bindResize() {
    const wraps = document.querySelectorAll('.viz-canvas-wrap');
    if (!wraps.length || typeof ResizeObserver === 'undefined') return;
    const ro = new ResizeObserver(() => {
      const cGj = document.getElementById('canvas-geisterjagd');
      const cBn = document.getElementById('canvas-banach');
      if (cGj) drawGeisterjagd(cGj);
      if (cBn) drawBanach(cBn);
    });
    wraps.forEach((w) => ro.observe(w));
  }

  window.FusionVizDemo = {
    start() {
      if (rafId) return;
      initGhosts();
      resetBanach();
      bindResize();
      window.addEventListener('fusion-layout-change', () => {
        const cGj = document.getElementById('canvas-geisterjagd');
        const cBn = document.getElementById('canvas-banach');
        if (cGj) drawGeisterjagd(cGj);
        if (cBn) drawBanach(cBn);
      });
      lastTs = 0;
      rafId = requestAnimationFrame(frame);
    },
    stop() {
      if (rafId) cancelAnimationFrame(rafId);
      rafId = null;
    },
    setLiveSnap(snap) {
      liveSnap = snap;
    },
  };
})();