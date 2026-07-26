/* Public-safe UI stub visuals.
   connect-src 'none' — no fetch, no websocket, no backend.
   Canvas only: illustrative graph loops (heroic + formal). */

const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;

/** Fixed synthetic graph — not live data */
const NODES = [
  { id: "hub", label: "GraphAPI", kind: "hub", g: "core" },
  { id: "mf", label: "Mainframe", kind: "surface", g: "core" },
  { id: "c1", label: "connector·dry", kind: "connector", g: "graph", dry: true },
  { id: "c2", label: "connector·dry", kind: "connector", g: "graph", dry: true },
  { id: "fw", label: "framework", kind: "framework", g: "intel" },
  { id: "q0", label: "Q0", kind: "quantum", g: "q" },
  { id: "q2", label: "Q2", kind: "quantum", g: "q" },
  { id: "q10", label: "Q10·asm", kind: "inject", g: "kernel" },
];
const EDGES = [
  ["mf", "hub"],
  ["hub", "c1"],
  ["hub", "c2"],
  ["hub", "fw"],
  ["mf", "q0"],
  ["mf", "q2"],
  ["mf", "q10"],
];

function layout() {
  const groups = {};
  for (const n of NODES) {
    (groups[n.g] ||= []).push(n.id);
  }
  const radii = { core: 0.12, graph: 0.4, intel: 0.52, q: 0.65, kernel: 0.78 };
  const pos = {};
  for (const [g, ids] of Object.entries(groups)) {
    const r = radii[g] ?? 0.7;
    ids.forEach((id, i) => {
      const ang = (Math.PI * 2 * i) / ids.length - Math.PI / 2;
      if (g === "core") {
        pos[id] = { x: 0.42 + i * 0.16, y: 0.5 };
      } else {
        pos[id] = {
          x: 0.5 + r * 0.42 * Math.cos(ang),
          y: 0.5 + r * 0.42 * Math.sin(ang),
        };
      }
    });
  }
  return pos;
}

const POS = layout();

function paint(canvas, mode, t) {
  if (!canvas) return;
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const rect = canvas.getBoundingClientRect();
  const w = Math.max(2, Math.floor(rect.width * dpr));
  const h = Math.max(2, Math.floor(rect.height * dpr));
  if (canvas.width !== w || canvas.height !== h) {
    canvas.width = w;
    canvas.height = h;
  }
  const ctx = canvas.getContext("2d");
  const heroic = mode === "heroic";

  if (heroic) {
    ctx.fillStyle = "#05050a";
    ctx.fillRect(0, 0, w, h);
    const g = ctx.createRadialGradient(w / 2, h / 2, 8, w / 2, h / 2, w * 0.38);
    g.addColorStop(0, "rgba(245,158,11,0.14)");
    g.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);
  } else {
    ctx.fillStyle = "#f8fafc";
    ctx.fillRect(0, 0, w, h);
    ctx.strokeStyle = "rgba(226,232,240,0.9)";
    ctx.lineWidth = 1;
    for (let x = 0; x < w; x += 36 * dpr) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
      ctx.stroke();
    }
    for (let y = 0; y < h; y += 36 * dpr) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }
  }

  const amp = heroic ? 0.015 : 0.008;
  const xy = (id) => {
    const b = POS[id] || { x: 0.5, y: 0.5 };
    const ph = (id.charCodeAt(0) % 7) * 0.7;
    return {
      x: (b.x + amp * Math.cos(t * 1.4 + ph)) * w,
      y: (b.y + amp * Math.sin(t * 1.4 + ph)) * h,
    };
  };

  for (const [a, b] of EDGES) {
    const p = xy(a);
    const q = xy(b);
    ctx.beginPath();
    ctx.moveTo(p.x, p.y);
    ctx.lineTo(q.x, q.y);
    ctx.strokeStyle = heroic ? "rgba(0,212,170,0.35)" : "rgba(14,165,233,0.4)";
    ctx.lineWidth = 1.5 * dpr;
    ctx.stroke();
    const u = (Math.sin(t * 2.2 + a.charCodeAt(0)) + 1) / 2;
    const mx = p.x + (q.x - p.x) * u;
    const my = p.y + (q.y - p.y) * u;
    ctx.beginPath();
    ctx.arc(mx, my, 2.5 * dpr, 0, Math.PI * 2);
    ctx.fillStyle = heroic ? "#f59e0b" : "#0f172a";
    ctx.fill();
  }

  for (const n of NODES) {
    const p = xy(n.id);
    let r = 7 * dpr;
    let fill = "#64748b";
    if (n.kind === "hub") {
      r = 13 * dpr;
      fill = heroic ? "#f59e0b" : "#0f172a";
    } else if (n.kind === "connector") fill = n.dry ? "#64748b" : "#00d4aa";
    else if (n.kind === "framework") fill = heroic ? "#7c3aed" : "#0284c7";
    else if (n.kind === "quantum") fill = heroic ? "#ef4444" : "#1e293b";
    else if (n.kind === "inject") fill = heroic ? "#22d3ee" : "#475569";
    else if (n.kind === "surface") fill = heroic ? "#00d4aa" : "#0ea5e9";
    ctx.beginPath();
    ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
    ctx.fillStyle = fill;
    ctx.fill();
    if (!heroic) {
      ctx.strokeStyle = "#0f172a";
      ctx.lineWidth = 1;
      ctx.stroke();
    }
    if (n.kind === "hub" || n.kind === "surface") {
      ctx.fillStyle = heroic ? "#e2e8f0" : "#0f172a";
      ctx.font = `${11 * dpr}px ui-monospace, monospace`;
      ctx.fillText(n.label, p.x + r + 3 * dpr, p.y + 3 * dpr);
    }
  }

  ctx.fillStyle = heroic ? "rgba(245,158,11,0.95)" : "#0f172a";
  ctx.font = `${12 * dpr}px ui-monospace, monospace`;
  if (heroic) {
    ctx.fillText("STUB · heroisch · keine Live-API", 12 * dpr, 18 * dpr);
  } else {
    const step = Math.floor((t * 1.5) % 10);
    const dn = Math.pow(0.74, step).toFixed(3);
    ctx.fillText(`STUB · G=(V,E) n=${NODES.length} · dₙ≈${dn} · Modell`, 12 * dpr, 18 * dpr);
  }
}

function loop() {
  const cH = document.getElementById("stub-canvas-heroic");
  const cF = document.getElementById("stub-canvas-formal");
  if (!cH && !cF) return;

  if (reduceMotion) {
    paint(cH, "heroic", 0);
    paint(cF, "formal", 0);
    return;
  }

  const t0 = performance.now();
  function frame(now) {
    const t = (now - t0) / 1000;
    paint(cH, "heroic", t);
    paint(cF, "formal", t);
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", loop);
} else {
  loop();
}
