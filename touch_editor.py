from pathlib import Path
from tempfile import gettempdir

import streamlit.components.v1 as components


HTML = r"""<!doctype html>
<html><head><meta charset="utf-8"><style>
*{box-sizing:border-box}body{margin:0;background:#fffaf7;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#332e35}
#toolbar{height:48px;display:flex;align-items:center;gap:8px;padding:7px 10px;background:#3a343d;color:#fff}
#picker{min-width:0;flex:1;border:0;border-radius:9px;padding:8px 9px;font-weight:700;background:#fff;color:#3a343d}
button{border:0;border-radius:9px;padding:8px 12px;font-weight:700;background:#fff;color:#3a343d}button:disabled{opacity:.35}
#stage{height:292px;padding:8px;background:#c85f80;display:grid;place-items:center;overflow:hidden}
svg{width:100%;height:100%;touch-action:none;user-select:none;-webkit-user-select:none}
.obj{cursor:pointer}.selected-outline{fill:none;stroke:#242027;stroke-width:.5;stroke-dasharray:1.4 1;vector-effect:non-scaling-stroke;pointer-events:none}
.handle{fill:#fff;stroke:#242027;stroke-width:.55;vector-effect:non-scaling-stroke;cursor:nwse-resize}
#hint{height:30px;padding:6px 10px;text-align:center;font-size:12px;color:#746b74;background:#fffaf7}
</style></head><body>
<div id="toolbar"><select id="picker"><option value="">Tap or choose a part</option></select></div>
<div id="stage"></div><div id="hint">Tap to select • drag to move • drag the square handle to resize</div>
<script>
const send=(type,data={})=>window.parent.postMessage({isStreamlitMessage:true,type,...data},"*");
const setValue=value=>send("streamlit:setComponentValue",{value});
const setHeight=height=>send("streamlit:setFrameHeight",{height});
let args={}, selected=null, gesture=null;
const stage=document.getElementById("stage"), picker=document.getElementById("picker");

function svgPoint(event){
  const svg=document.getElementById("canvas"), point=svg.createSVGPoint();
  point.x=event.clientX; point.y=event.clientY;
  return point.matrixTransform(svg.getScreenCTM().inverse());
}
function activeLayer(){return (args.layers||[]).find(layer=>layer.id===selected)}
function selectObject(id){
  selected=id; document.getElementById("selection")?.remove();
  const object=document.querySelector('.obj[data-id="'+id+'"]');
  if(!object){selected=null; picker.value="";return}
  const box=object.getBBox(), svg=document.getElementById("canvas"), overlay=document.createElementNS("http://www.w3.org/2000/svg","g");
  overlay.id="selection";
  const rect=document.createElementNS("http://www.w3.org/2000/svg","rect");
  rect.setAttribute("x",box.x);rect.setAttribute("y",box.y);rect.setAttribute("width",box.width);rect.setAttribute("height",box.height);rect.setAttribute("rx",Math.max(.3,Math.min(box.width,box.height)*.025));rect.setAttribute("class","selected-outline");
  const handle=document.createElementNS("http://www.w3.org/2000/svg","rect"), hs=Math.max(1.8,Math.min(args.width,args.height)*.045);
  handle.setAttribute("x",box.x+box.width-hs/2);handle.setAttribute("y",box.y+box.height-hs/2);handle.setAttribute("width",hs);handle.setAttribute("height",hs);handle.setAttribute("rx",hs*.18);handle.setAttribute("class","handle");handle.id="resize-handle";
  overlay.append(rect,handle);svg.append(overlay);
  picker.value=id;
}
function render(next){
  args=next||{}; selected=null;
  picker.innerHTML='<option value="">Tap or choose a part</option>'+(args.layers||[]).map(layer=>'<option value="'+layer.id+'">'+layer.label+'</option>').join("");
  const groups=(args.layers||[]).map(layer=>'<g class="obj" data-id="'+layer.id+'" fill="'+layer.fill+'" fill-rule="evenodd">'+layer.markup+'</g>').join("");
  stage.innerHTML='<svg id="canvas" viewBox="0 0 '+args.width+' '+args.height+'" preserveAspectRatio="xMidYMid meet"><rect width="'+args.width+'" height="'+args.height+'" rx="2" fill="'+args.background+'"/>'+groups+'</svg>';
  const svg=document.getElementById("canvas");
  svg.addEventListener("pointerdown",event=>{
    const handle=event.target.closest("#resize-handle"), object=event.target.closest(".obj");
    if(handle && selected){
      event.preventDefault();const layer=activeLayer(), box=document.querySelector('.obj[data-id="'+selected+'"]').getBBox(), p=svgPoint(event);
      gesture={type:"resize",id:selected,start:p,box,initialSize:layer.size,scale:1};svg.setPointerCapture(event.pointerId);return;
    }
    if(!object)return;
    event.preventDefault();const id=object.dataset.id;selectObject(id);const p=svgPoint(event), layer=activeLayer();
    if(id!=="base")gesture={type:"move",id,start:p,dx:0,dy:0,initialX:layer.x||0,initialY:layer.y||0};
    svg.setPointerCapture(event.pointerId);
  });
  svg.addEventListener("pointermove",event=>{
    if(!gesture)return;event.preventDefault();const p=svgPoint(event), object=document.querySelector('.obj[data-id="'+gesture.id+'"]'), overlay=document.getElementById("selection");
    if(gesture.type==="move"){
      gesture.dx=p.x-gesture.start.x;gesture.dy=p.y-gesture.start.y;
      if(Math.hypot(gesture.dx,gesture.dy)<1.0)return;
      const transform='translate('+gesture.dx+' '+gesture.dy+')';object.setAttribute("transform",transform);if(overlay)overlay.setAttribute("transform",transform);
    }else{
      const cx=gesture.box.x+gesture.box.width/2,cy=gesture.box.y+gesture.box.height/2;
      const startDistance=Math.hypot(gesture.start.x-cx,gesture.start.y-cy)||1,currentDistance=Math.hypot(p.x-cx,p.y-cy);
      gesture.scale=Math.max(.4,Math.min(1.8,currentDistance/startDistance));
      const transform='translate('+cx+' '+cy+') scale('+gesture.scale+') translate('+(-cx)+' '+(-cy)+')';object.setAttribute("transform",transform);if(overlay)overlay.setAttribute("transform",transform);
    }
  });
  const finish=event=>{
    if(!gesture)return;const current=gesture;gesture=null;
    const layer=(args.layers||[]).find(item=>item.id===current.id)||{};
    if(current.type==="move"){
      if(Math.hypot(current.dx,current.dy)>=1.0)setValue({nonce:Date.now(),action:"update",component:current.id,x:Math.max(-25,Math.min(25,current.initialX+current.dx)),y:Math.max(-20,Math.min(20,current.initialY+current.dy))});
    }else setValue({nonce:Date.now(),action:"update",component:current.id,size:Math.max(layer.minSize||40,Math.min(layer.maxSize||180,current.initialSize*current.scale))});
  };
  svg.addEventListener("pointerup",finish);svg.addEventListener("pointercancel",finish);
}
picker.addEventListener("change",()=>{if(picker.value)selectObject(picker.value);else selectObject("")});
window.addEventListener("message",event=>{if(event.data?.type==="streamlit:render")render(event.data.args)});
send("streamlit:componentReady",{apiVersion:1});setHeight(377);
</script></body></html>"""


component_directory = Path(gettempdir()) / "teddie_lane_touch_editor"
component_directory.mkdir(parents=True, exist_ok=True)
index_file = component_directory / "index.html"
if not index_file.exists() or index_file.read_text(encoding="utf-8") != HTML:
    index_file.write_text(HTML, encoding="utf-8")

touch_badge_editor = components.declare_component("touch_badge_editor", path=str(component_directory))
