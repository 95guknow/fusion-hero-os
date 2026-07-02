# -*- coding: utf-8 -*-
"""Geteilte Web-Skripte — Workspace (NiceGUI) + Monitor (static)."""
from __future__ import annotations

INTERACTION_VERSION = "1.1"
GUI_POSITIONS_KEY = "fusion-gui-positions"


def drag_script(storage_key: str = GUI_POSITIONS_KEY) -> str:
    """Drag-Logik — Panels & Layer plug-and-play (ein Storage-Key)."""
    sk = storage_key.replace("-", "_")
    return f"""
(function(){{
  if(window.__fusionDrag_{sk}) return;
  window.__fusionDrag_{sk} = true;
  const STORAGE = '{storage_key}';
  function loadPos(key){{ try{{return JSON.parse(localStorage.getItem(key||STORAGE)||'{{}}');}}catch(e){{return{{}};}} }}
  function savePos(id,x,y,key){{ const p=loadPos(key); p[id]={{x,y}}; localStorage.setItem(key||STORAGE,JSON.stringify(p)); }}
  function isFixed(el){{ return window.getComputedStyle(el).position==='fixed'; }}
  window.fusionInitDraggable = function(panelId, handleSel, defaultX, defaultY, storeKey){{
    const key = storeKey || STORAGE;
    const panel=document.getElementById(panelId);
    if(!panel) return;
    const handle=panel.querySelector(handleSel)||panel;
    const fixed=isFixed(panel);
    const saved=loadPos(key)[panelId];
    if(saved){{ panel.style.left=saved.x+'px'; panel.style.top=saved.y+'px'; if(fixed) panel.style.right='auto'; }}
    else if(defaultX!=null&&defaultY!=null){{
      panel.style.left=defaultX+'px'; panel.style.top=defaultY+'px'; if(fixed) panel.style.right='auto';
    }}
    let drag=false,sx=0,sy=0,sl=0,st=0;
    handle.addEventListener('mousedown',function(e){{
      if(e.target.closest('button,.fusion-btn,.q-btn')) return;
      drag=true; sx=e.clientX; sy=e.clientY;
      const r=panel.getBoundingClientRect();
      if(fixed){{ sl=r.left; st=r.top; panel.style.right='auto'; }}
      else {{
        const pr=panel.offsetParent?panel.offsetParent.getBoundingClientRect():{{left:0,top:0}};
        sl=r.left-pr.left; st=r.top-pr.top;
      }}
      panel.classList.add('fusion-drag-active');
      e.preventDefault();
    }});
    document.addEventListener('mousemove',function(e){{
      if(!drag) return;
      panel.style.left=Math.max(0,sl+(e.clientX-sx))+'px';
      panel.style.top=Math.max(0,st+(e.clientY-sy))+'px';
    }});
    document.addEventListener('mouseup',function(){{
      if(!drag) return;
      drag=false;
      panel.classList.remove('fusion-drag-active');
      const r=panel.getBoundingClientRect();
      if(fixed) savePos(panelId, r.left, r.top, key);
      else {{
        const pr=panel.offsetParent?panel.offsetParent.getBoundingClientRect():{{left:0,top:0}};
        savePos(panelId, r.left-pr.left, r.top-pr.top, key);
      }}
    }});
  }};
  window.fusionScanDragLayers = function(storeKey){{
    const key = storeKey || STORAGE;
    document.querySelectorAll('[data-fusion-drag]').forEach(function(el){{
      const id=el.id||el.getAttribute('data-fusion-drag');
      if(!id) return;
      const hx=parseInt(el.getAttribute('data-fusion-drag-x')||'12',10);
      const hy=parseInt(el.getAttribute('data-fusion-drag-y')||'12',10);
      const hsel=el.getAttribute('data-fusion-drag-handle')||'.fusion-layer-handle,.fusion-task-handle';
      fusionInitDraggable(id, hsel, hx, hy, key);
    }});
  }};
  window.fusionResetGuiLayout = function(storeKey){{
    const key = storeKey || STORAGE;
    localStorage.removeItem(key);
    document.querySelectorAll('.fusion-task-panel,.fusion-layer-panel,.fusion-drag-layer').forEach(function(p){{
      p.style.left=''; p.style.top=''; p.style.right='';
    }});
  }};
  window.fusionResetPanels = window.fusionResetGuiLayout;
}})();
"""