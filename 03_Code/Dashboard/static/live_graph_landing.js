/**
 * Landing-page Live GraphAPI dual viz (heroic + formal math).
 * Polls GET /api/visuals/live-graph and paints both canvases.
 */
(function () {
  const LAMBDA = 0.74;
  let snap = null;
  let raf = 0;
  let t0 = performance.now();
  let pulse = 0;

  const $ = (id) => document.getElementById(id);

  function setText(id, v) {
    const el = $(id);
    if (el) el.textContent = v;
  }

  async function fetchSnap() {
    try {
      const r = await fetch("/api/visuals/live-graph", { cache: "no-store" });
      if (!r.ok) throw new Error("HTTP " + r.status);
      snap = await r.json();
      setText("lg-status", snap.ok ? "LIVE" : "ERR");
      const ga = snap.graph_api || {};
      setText("lg-conn", ga.connector_count ?? "--");
      setText("lg-live", ga.live_ready ?? "--");
      setText("lg-token", ga.token_present ?? "--");
      setText("lg-fw", (snap.frameworks && snap.frameworks.count) ?? "--");
      setText("lg-inj", (snap.inject && snap.inject.active_count) ?? "--");
      setText("lg-q", snap.quanta_count ?? "--");
      setText("lg-v", (snap.nodes || []).length);
      setText("lg-e", (snap.edges || []).length);
      setText("lg-geltung", (snap.geltung || "").slice(0, 48));
      setText(
        "lg-heroic-caption",
        "Hub · " +
          (ga.connector_count || 0) +
          " connectors · " +
          ((snap.frameworks && snap.frameworks.count) || 0) +
          " frameworks · inject " +
          ((snap.inject && snap.inject.active_count) || 0)
      );
      setText(
        "lg-formal-caption",
        "G=(V,E) |V|=" +
          (snap.nodes || []).length +
          " |E|=" +
          (snap.edges || []).length +
          " · LIVE_READY=" +
          (ga.live_ready || 0)
      );
    } catch (e) {
      setText("lg-status", "offline");
      console.warn("[live-graph]", e);
    }
  }

  function xy(layout, id, t, mode) {
    const b = (layout && layout[id]) || { x: 0.5, y: 0.5 };
    const phase = (hash(id) % 1000) / 1000 * Math.PI * 2;
    const amp = mode === "formal" ? 0.01 : 0.018;
    return {
      x: b.x + amp * Math.cos(t * 2 + phase),
      y: b.y + amp * Math.sin(t * 2 + phase),
    };
  }

  function hash(s) {
    let h = 0;
    for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
    return Math.abs(h);
  }

  function paint(canvas, mode, t) {
    if (!canvas || !snap || !snap.nodes) return;
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    const w = Math.max(2, Math.floor(rect.width * dpr));
    const h = Math.max(2, Math.floor(rect.height * dpr));
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w;
      canvas.height = h;
    }
    const ctx = canvas.getContext("2d");
    const nodes = snap.nodes || [];
    const edges = snap.edges || [];
    const layout = snap.layout || {};

    if (mode === "heroic") {
      ctx.fillStyle = "rgba(5,5,10,0.35)";
      ctx.fillRect(0, 0, w, h);
      // soft center glow
      const g = ctx.createRadialGradient(w / 2, h / 2, 10, w / 2, h / 2, w * 0.4);
      g.addColorStop(0, "rgba(245,158,11,0.12)");
      g.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, w, h);
    } else {
      ctx.fillStyle = "rgba(248,250,252,0.45)";
      ctx.fillRect(0, 0, w, h);
      ctx.strokeStyle = "rgba(226,232,240,0.7)";
      ctx.lineWidth = 1;
      for (let x = 0; x < w; x += 40 * dpr) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
        ctx.stroke();
      }
      for (let y = 0; y < h; y += 40 * dpr) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
      }
    }

    // edges
    for (const e of edges) {
      const a = xy(layout, e.source, t, mode);
      const b = xy(layout, e.target, t, mode);
      const x1 = a.x * w,
        y1 = a.y * h,
        x2 = b.x * w,
        y2 = b.y * h;
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      if (mode === "heroic") {
        ctx.strokeStyle =
          e.mode === "LIVE_READY"
            ? "rgba(0,212,170,0.55)"
            : e.kind === "framework"
              ? "rgba(124,58,237,0.45)"
              : "rgba(0,212,170,0.25)";
      } else {
        ctx.strokeStyle = "rgba(14,165,233,0.45)";
      }
      ctx.lineWidth = 1.5 * dpr;
      ctx.stroke();

      const u = (Math.sin(t * 3 + hash(e.source) % 7) + 1) / 2;
      const mx = x1 + (x2 - x1) * u;
      const my = y1 + (y2 - y1) * u;
      ctx.beginPath();
      ctx.arc(mx, my, 3 * dpr, 0, Math.PI * 2);
      ctx.fillStyle = mode === "heroic" ? "#f59e0b" : "#0f172a";
      ctx.fill();
    }

    // nodes
    for (const n of nodes) {
      const p = xy(layout, n.id, t, mode);
      const px = p.x * w;
      const py = p.y * h;
      let rad = (7 + 6 * (n.weight || 0.5)) * dpr;
      let fill = "#64748b";
      if (n.kind === "hub") {
        rad = 14 * dpr;
        fill = mode === "heroic" ? "#f59e0b" : "#0f172a";
      } else if (n.kind === "connector") fill = n.live ? "#00d4aa" : "#64748b";
      else if (n.kind === "framework") fill = mode === "heroic" ? "#7c3aed" : "#0284c7";
      else if (n.kind === "quantum") fill = mode === "heroic" ? "#ef4444" : "#1e293b";
      else if (n.kind === "inject") fill = mode === "heroic" ? "#22d3ee" : "#64748b";
      else if (n.kind === "surface") fill = mode === "heroic" ? "#00d4aa" : "#0ea5e9";

      ctx.beginPath();
      ctx.arc(px, py, rad, 0, Math.PI * 2);
      ctx.fillStyle = fill;
      ctx.fill();
      if (mode === "formal") {
        ctx.strokeStyle = "#0f172a";
        ctx.lineWidth = 1;
        ctx.stroke();
      }

      if (n.kind === "hub" || n.kind === "surface" || (mode === "formal" && n.kind === "quantum")) {
        ctx.fillStyle = mode === "heroic" ? "#e2e8f0" : "#0f172a";
        ctx.font = `${11 * dpr}px JetBrains Mono, monospace`;
        ctx.fillText(String(n.label || "").slice(0, 16), px + rad + 3 * dpr, py + 3 * dpr);
      }
    }

    if (mode === "formal") {
      const step = Math.floor((t * 2) % 12);
      const dn = Math.pow(LAMBDA, step);
      setText("lg-dn", dn.toFixed(3));
      setText("lg-lambda", String(LAMBDA));
      ctx.fillStyle = "#0f172a";
      ctx.font = `${12 * dpr}px JetBrains Mono, monospace`;
      ctx.fillText(`A∈ℝ^{n×n}  n=${nodes.length}  dₙ=d₀·λⁿ ≈ ${dn.toFixed(3)}`, 12 * dpr, 20 * dpr);
    } else {
      setText("lg-heroic-pulse", pulse.toFixed(2));
    }
  }

  function frame(now) {
    const t = (now - t0) / 1000;
    pulse = (Math.sin(t * 2) + 1) / 2;
    paint($("canvas-live-heroic"), "heroic", t);
    paint($("canvas-live-formal"), "formal", t);
    raf = requestAnimationFrame(frame);
  }

  function boot() {
    if (!$("canvas-live-heroic")) return;
    fetchSnap();
    setInterval(fetchSnap, 4000);
    raf = requestAnimationFrame(frame);
    // kick video play (autoplay policies)
    ["video-live-heroic", "video-live-formal"].forEach((id) => {
      const v = $(id);
      if (v) v.play().catch(() => {});
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
