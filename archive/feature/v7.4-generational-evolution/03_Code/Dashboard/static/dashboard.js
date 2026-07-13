// ALTE_Frau Real-time Dashboard
(function() {
  const WS_URL = ws:///ws;
  const ws = new WebSocket(WS_URL);
  
  // Event Stream
  const events = [];
  const maxEvents = 500;
  
  ws.onmessage = (e) => {
    const data = JSON.parse(e.data);
    if (data.type === 'welcome') {
      document.getElementById('event-count').textContent = data.event_count;
    } else {
      events.unshift(data);
      if (events.length > maxEvents) events.pop();
      renderEvents();
    }
  };
  
  // Metrics polling
  async function fetchMetrics() {
    try {
      const r = await fetch('/api/metrics');
      const m = await r.json();
      document.getElementById('cpu').textContent = m.cpu;
      document.getElementById('ram').textContent = m.ram;
      document.getElementById('events').textContent = m.events;
      document.getElementById('ops').textContent = m.ops_per_sec;
    } catch (e) {}
  }
  
  setInterval(fetchMetrics, 1000);
  fetchMetrics();
  
  function renderEvents() {
    const el = document.getElementById('event-stream');
    if (!el) return;
    el.innerHTML = events.slice(0, 20).map(ev => 
      <div class="text-xs mb-1"><span class="text-teal">[]</span> <span class="text-amber">:</span> </div>
    ).join('');
  }
})();
