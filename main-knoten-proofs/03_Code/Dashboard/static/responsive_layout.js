/**
 * Fusion Hero OS — Responsives Dashboard-Layout
 * Ordnet Panels nach Fenstergröße neu und strukturiert Ausgabefenster.
 */
(function () {
  const BREAKPOINTS = [
    { name: 'xs', min: 0, cols: 1, label: 'Kompakt' },
    { name: 'sm', min: 520, cols: 1, label: 'Schmal' },
    { name: 'md', min: 768, cols: 2, label: 'Tablet' },
    { name: 'lg', min: 1024, cols: 2, label: 'Desktop' },
    { name: 'xl', min: 1400, cols: 3, label: 'Breit' },
  ];

  /** Niedrigere priority-Zahl = weiter oben im Grid */
  const PANEL_CONFIG = {
    'event-stream': {
      zone: 'output',
      priority: { xs: 1, sm: 1, md: 3, lg: 7, xl: 7 },
      span: { xs: 1, sm: 1, md: 2, lg: 1, xl: 2 },
      output: true,
    },
    'bridge': {
      zone: 'integration',
      priority: { xs: 2, sm: 2, md: 4, lg: 4, xl: 4 },
      span: { xs: 1, sm: 1, md: 1, lg: 1, xl: 1 },
      output: true,
    },
    'phone-link': {
      zone: 'integration',
      priority: { xs: 3, sm: 3, md: 6, lg: 6, xl: 6 },
      span: { xs: 1, sm: 1, md: 1, lg: 1, xl: 1 },
      output: true,
    },
    'connectivity': {
      zone: 'integration',
      priority: { xs: 4, sm: 4, md: 5, lg: 5, xl: 5 },
      span: { xs: 1, sm: 1, md: 1, lg: 1, xl: 1 },
      output: true,
    },
    'core-metrics': {
      zone: 'metrics',
      priority: { xs: 5, sm: 5, md: 1, lg: 1, xl: 1 },
      span: { xs: 1, sm: 1, md: 1, lg: 1, xl: 1 },
    },
    'hyper-threading': {
      zone: 'metrics',
      priority: { xs: 6, sm: 6, md: 2, lg: 2, xl: 2 },
      span: { xs: 1, sm: 1, md: 1, lg: 1, xl: 1 },
    },
    'layer-architecture': {
      zone: 'metrics',
      priority: { xs: 7, sm: 7, md: 7, lg: 3, xl: 3 },
      span: { xs: 1, sm: 1, md: 2, lg: 2, xl: 2 },
    },
    'viz-banach': {
      zone: 'viz',
      priority: { xs: 8, sm: 8, md: 8, lg: 8, xl: 8 },
      span: { xs: 1, sm: 1, md: 2, lg: 2, xl: 3 },
    },
  };

  const OUTPUT_SELECTORS = [
    '#event-stream',
    '#bridge-dispatch-result',
    '#phone-feed',
    '#conn-access-grid',
  ];

  function debounce(fn, ms) {
    let t;
    return function (...args) {
      clearTimeout(t);
      t = setTimeout(() => fn.apply(this, args), ms);
    };
  }

  function getBreakpoint(width) {
    let current = BREAKPOINTS[0];
    for (const bp of BREAKPOINTS) {
      if (width >= bp.min) current = bp;
    }
    return current;
  }

  class FusionResponsiveLayout {
    constructor(gridSelector) {
      this.grid = document.querySelector(gridSelector);
      this.indicator = document.getElementById('layout-mode-indicator');
      this._panels = [];
      this._lastBp = '';
    }

    collectPanels() {
      if (!this.grid) return;
      this._panels = Array.from(this.grid.querySelectorAll('[data-panel-id]'));
    }

    isVisible(panel) {
      return panel && !panel.classList.contains('panel-hidden');
    }

    applySpan(panel, span, cols) {
      panel.classList.remove('panel-span-1', 'panel-span-2', 'panel-span-full');
      const id = panel.dataset.panelId;
      if (id === 'viz-banach' || span >= cols) {
        panel.classList.add('panel-span-full');
      } else if (span >= 2 && cols >= 2) {
        panel.classList.add('panel-span-2');
      } else {
        panel.classList.add('panel-span-1');
      }
    }

    tuneOutputSurfaces(bp) {
      const stream = document.getElementById('event-stream');
      const bridgeResult = document.getElementById('bridge-dispatch-result');
      const phoneFeed = document.getElementById('phone-feed');

      const heights = {
        xs: { stream: 200, bridge: 100, phone: 120 },
        sm: { stream: 220, bridge: 110, phone: 130 },
        md: { stream: 260, bridge: 120, phone: 140 },
        lg: { stream: 300, bridge: 140, phone: 150 },
        xl: { stream: 340, bridge: 150, phone: 160 },
      };
      const h = heights[bp.name] || heights.lg;

      if (stream) stream.style.maxHeight = `${h.stream}px`;
      if (bridgeResult) bridgeResult.style.maxHeight = `${h.bridge}px`;
      if (phoneFeed) phoneFeed.style.maxHeight = `${h.phone}px`;

      OUTPUT_SELECTORS.forEach((sel) => {
        const el = document.querySelector(sel);
        if (!el) return;
        el.classList.toggle('output-compact', bp.cols === 1);
        el.classList.toggle('output-expanded', bp.cols >= 2);
      });
    }

    apply(force) {
      if (!this.grid) return;
      this.collectPanels();

      const width = window.innerWidth;
      const bp = getBreakpoint(width);
      const visible = this._panels.filter((p) => this.isVisible(p));
      const visKey = visible.map((p) => p.dataset.panelId).join(',');
      if (
        !force
        && bp.name === this._lastBp
        && this._appliedWidth === width
        && visKey === this._lastVisKey
      ) {
        return;
      }
      this._lastBp = bp.name;
      this._appliedWidth = width;
      this._lastVisKey = visKey;

      document.body.dataset.layout = bp.name;
      document.documentElement.style.setProperty('--dash-cols', String(bp.cols));

      const sorted = visible.slice().sort((a, b) => {
        const idA = a.dataset.panelId;
        const idB = b.dataset.panelId;
        const pa = PANEL_CONFIG[idA]?.priority[bp.name] ?? 99;
        const pb = PANEL_CONFIG[idB]?.priority[bp.name] ?? 99;
        if (pa !== pb) return pa - pb;
        return idA.localeCompare(idB);
      });

      let lastZone = null;
      sorted.forEach((panel) => {
        const id = panel.dataset.panelId;
        const cfg = PANEL_CONFIG[id] || {};
        const zone = cfg.zone || 'misc';
        panel.dataset.panelZone = zone;
        panel.classList.toggle('panel-zone-break', zone !== lastZone && lastZone !== null);
        lastZone = zone;

        const span = cfg.span?.[bp.name] ?? 1;
        this.applySpan(panel, span, bp.cols);
        panel.classList.toggle('panel-output', Boolean(cfg.output));
        this.grid.appendChild(panel);
      });

      this.tuneOutputSurfaces(bp);

      if (this.indicator) {
        this.indicator.textContent = `Layout: ${bp.label} · ${bp.cols} Spalte${bp.cols > 1 ? 'n' : ''}`;
        this.indicator.dataset.layout = bp.name;
      }

      window.dispatchEvent(
        new CustomEvent('fusion-layout-change', {
          detail: { breakpoint: bp.name, cols: bp.cols, width },
        }),
      );
    }

    bind() {
      if (this._bound) return;
      this._bound = true;
      const run = debounce(() => this.apply(false), 80);
      window.addEventListener('resize', run);
      if (typeof ResizeObserver !== 'undefined') {
        const ro = new ResizeObserver(run);
        ro.observe(document.documentElement);
      }
      const observer = new MutationObserver(run);
      observer.observe(this.grid, { attributes: true, subtree: true, attributeFilter: ['class'] });
    }

    init() {
      if (!this.grid) return;
      this.bind();
      this.apply(true);
    }
  }

  let _instance = null;

  window.FusionResponsiveLayout = {
    init(selector) {
      if (!_instance) {
        _instance = new FusionResponsiveLayout(selector || '#dashboard-grid');
      }
      _instance.init();
      return _instance;
    },
    relayout() {
      if (_instance) _instance.apply(true);
    },
    getBreakpoint,
    PANEL_CONFIG,
  };
})();