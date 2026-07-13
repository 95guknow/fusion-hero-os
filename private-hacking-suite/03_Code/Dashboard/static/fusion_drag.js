
(function(){
  if(window.__fusionDrag_fusion_monitor_panel_positions) return;
  window.__fusionDrag_fusion_monitor_panel_positions = true;
  const STORAGE = 'fusion-monitor-panel-positions';
  function loadPos(){ try{return JSON.parse(localStorage.getItem(STORAGE)||'{}');}catch(e){return{};} }
  function savePos(id,x,y){ const p=loadPos(); p[id]={x,y}; localStorage.setItem(STORAGE,JSON.stringify(p)); }
  function applyPos(el,id){
    const p=loadPos()[id];
    if(p){ el.style.left=p.x+'px'; el.style.top=p.y+'px'; }
  }
  window.fusionInitDraggable = function(panelId, handleSel, defaultX, defaultY, storeKey){
    const key = storeKey || STORAGE;
    function load(){ try{return JSON.parse(localStorage.getItem(key)||'{}');}catch(e){return{};} }
    function save(id,x,y){ const p=load(); p[id]={x,y}; localStorage.setItem(key,JSON.stringify(p)); }
    const panel=document.getElementById(panelId);
    if(!panel) return;
    const handle=panel.querySelector(handleSel)||panel;
    if(!load()[panelId]){ panel.style.left=defaultX+'px'; panel.style.top=defaultY+'px'; }
    else { const p=load()[panelId]; if(p){ panel.style.left=p.x+'px'; panel.style.top=p.y+'px'; } }
    let drag=false,sx=0,sy=0,sl=0,st=0;
    handle.addEventListener('mousedown',function(e){
      if(e.target.closest('button,.fusion-btn')) return;
      drag=true; sx=e.clientX; sy=e.clientY;
      const r=panel.getBoundingClientRect();
      const pr=panel.offsetParent?panel.offsetParent.getBoundingClientRect():{left:0,top:0};
      sl=r.left-pr.left; st=r.top-pr.top;
      panel.classList.add('fusion-task-panel--dragging');
      e.preventDefault();
    });
    document.addEventListener('mousemove',function(e){
      if(!drag) return;
      panel.style.left=Math.max(0,sl+(e.clientX-sx))+'px';
      panel.style.top=Math.max(0,st+(e.clientY-sy))+'px';
    });
    document.addEventListener('mouseup',function(){
      if(!drag) return;
      drag=false;
      panel.classList.remove('fusion-task-panel--dragging');
      const pr=panel.offsetParent?panel.offsetParent.getBoundingClientRect():{left:0,top:0};
      const r=panel.getBoundingClientRect();
      save(panelId, r.left-pr.left, r.top-pr.top);
    });
  };
  window.fusionResetPanels = function(storeKey){
    const key = storeKey || STORAGE;
    localStorage.removeItem(key);
    document.querySelectorAll('.fusion-task-panel').forEach(function(p){
      p.style.left=''; p.style.top='';
    });
  };
})();
