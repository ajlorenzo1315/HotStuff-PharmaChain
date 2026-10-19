/* Independent live network renderer. Does not depend on the older dashboard renderer. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const ns = 'http://www.w3.org/2000/svg';
  const point = [[180,110],[520,110],[180,350],[520,350]];
  let snapshot = null, selected = 0, current = 0, auto = null, lastEventIndex = -1;
  const E = (tag,attrs={},label) => {const el=document.createElementNS(ns,tag);for(const [k,v] of Object.entries(attrs))el.setAttribute(k,String(v));if(label!==undefined)el.textContent=String(label);return el;};
  const text = (root,x,y,label,size=13,color='#eaf7ff')=>root.append(E('text',{x,y,fill:color,'font-size':size},label));
  const parseNode = value => {const match=String(value??'').match(/(?:validator-|^V)([0-3])$/i);return match?Number(match[1]):-1;};
  function draw(data){
    const root=$('topologySvg');if(!root)return;
    root.setAttribute('viewBox','0 0 700 470');root.setAttribute('preserveAspectRatio','xMidYMid meet');root.replaceChildren();
    root.append(E('rect',{x:0,y:0,width:700,height:470,rx:14,fill:'#081626'}));
    const nodes=Array.isArray(data?.nodes)?data.nodes:[];
    const nodeById=new Map(nodes.map(n=>[n.id,n]));
    const list=Array.from({length:4},(_,i)=>nodeById.get(`validator-${i}`)||{id:`validator-${i}`,online:null});
    const events=Array.isArray(data?.events)?data.events:[];
    const event=events[current]||events.at(-1);
    const src=parseNode(event?.source??event?.sender??event?.validator??event?.node_id);
    const dst=parseNode(event?.target??event?.receiver??event?.destination);
    for(let i=0;i<4;i++)for(let j=i+1;j<4;j++){
      const [x1,y1]=point[i], [x2,y2]=point[j];root.append(E('line',{x1,y1,x2,y2,stroke:'#345b75','stroke-width':2,'stroke-dasharray':'6 8'}));
    }
    if(src>=0&&dst>=0&&src!==dst){
      const [x1,y1]=point[src], [x2,y2]=point[dst];
      root.append(E('line',{x1,y1,x2,y2,stroke:'#ffd08a','stroke-width':5}));
      const dot=E('circle',{r:7,fill:'#fff1bc'});dot.append(E('animateMotion',{dur:'1.5s',repeatCount:'indefinite',path:`M${x1},${y1} L${x2},${y2}`}));root.append(dot);
    }
    list.forEach((node,i)=>{
      const [x,y]=point[i], online=node.online, leader=node.id===data?.leader;
      const group=E('g',{tabindex:0,role:'button',style:'cursor:pointer','aria-label':`Seleccionar V${i}`});
      group.append(E('rect',{x:x-139,y:y-68,width:278,height:136,rx:13,fill:online===false?'#552c3a':online===true?'#153f44':'#20334c',stroke:i===selected?'#ffd08a':online===false?'#ff8b9c':'#68dfcb','stroke-width':i===selected?3:2}));
      text(group,x-122,y-41,`V${i} · ${['Laboratorio','Distribuidor','Farmacia','Regulador'][i]}`,16,'#fff');
      text(group,x-122,y-19,`${leader?'★ Líder · ':''}${online===true?'Conectado':online===false?'Desconectado':'Esperando estado'}`,12,leader?'#ffd08a':'#d5e8f5');
      text(group,x-122,y+4,`Vista ${node.view??'—'} · Altura ${node.height??'—'} · QC ${node.certificates??'—'}`,12);
      const action=i===src?'Emite: '+(event?.event??event?.name??'evento'):i===dst?'Recibe: '+(event?.event??event?.name??'evento'):'Sin mensaje atribuido';
      text(group,x-122,y+27,action.slice(0,39),12,i===src||i===dst?'#ffe3a3':'#b5cadb');
      text(group,x-122,y+49,`Clave pública: ${node.public_key?String(node.public_key).slice(0,15)+'…':'no publicada'}`,11,'#a8d9dd');
      group.addEventListener('click',()=>{selected=i;draw(data);});
      group.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){selected=i;draw(data);}});
      root.append(group);
    });
    const online=list.filter(n=>n.online===true).length, known=list.every(n=>typeof n.online==='boolean');
    if($('onlineCount'))$('onlineCount').textContent=known?`${online}/4`:'—';
    if($('onlineBar'))$('onlineBar').style.width=known?`${online*25}%`:'0%';
    const quorum=Number(data?.quorum)||3;
    if($('votePotential'))$('votePotential').textContent=known?`${online}/${quorum}`:'—';
    if($('quorumExplanation'))$('quorumExplanation').textContent=known?(online>=quorum?'Cuórum posible; un QC requiere votos distintos y firmas válidas.':'Sin suficientes nodos conectados para alcanzar el cuórum.'):'Topología lista. Esperando datos del servidor.';
    const n=list[selected];
    if($('inspectorTitle'))$('inspectorTitle').textContent=`V${selected} · ${n.id}`;
    if($('inspectorDetails'))$('inspectorDetails').textContent=`${n.online===true?'Conectado':n.online===false?'Desconectado':'Estado pendiente'} · Vista ${n.view??'—'} · Altura ${n.height??'—'} · QC ${n.certificates??'—'}`;
    if($('inspectorKey'))$('inspectorKey').textContent=n.public_key?`Clave pública: ${n.public_key}`:'Clave pública no publicada por la API; los votos se verifican con la clave pública del emisor.';
    if($('inspectorToggle')){$('inspectorToggle').disabled=typeof n.online!=='boolean';$('inspectorToggle').textContent=n.online===false?'Reconectar':'Desconectar';}
    if($('inspectorSync'))$('inspectorSync').disabled=n.online!==true;
    if($('networkActivity'))$('networkActivity').textContent=event?`Evento ${current+1}/${events.length}: ${event.event||event.name||'sin tipo'} · ${src>=0?'V'+src:'origen no identificado'} → ${dst>=0?'V'+dst:'destino no identificado'}`:'Sin eventos. Pulsa «Ejecutar ronda» para iniciar el consenso normal.';
    const scrub=$('liveScrub');if(scrub){scrub.max=Math.max(0,events.length-1);scrub.value=Math.min(current,events.length-1);scrub.disabled=!events.length;}
  }
  async function refresh(){
    try{
      const response=await fetch('/api/simulation',{cache:'no-store'});
      if(!response.ok)throw Error(`HTTP ${response.status}`);
      const body=await response.json();snapshot=body.state||body;
      if(!Array.isArray(snapshot.nodes))throw Error('Respuesta sin nodes[]');
      const count=Array.isArray(snapshot.events)?snapshot.events.length:0;
      if(count!==lastEventIndex){current=Math.max(0,count-1);lastEventIndex=count;}
      draw(snapshot);
      if($('liveError'))$('liveError').textContent='';
    }catch(error){draw(snapshot);if($('liveError'))$('liveError').textContent='No se pudo actualizar la red: '+error.message;}
  }
  async function action(path,payload={}){
    try{const response=await fetch('/api/simulation'+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});if(!response.ok)throw Error(`HTTP ${response.status}`);await refresh();}
    catch(error){if($('liveError'))$('liveError').textContent='Operación fallida: '+error.message;}
  }
  function init(){
    draw(null);refresh();
    $('liveNormal')?.addEventListener('click',()=>action('/round'));
    $('liveReset')?.addEventListener('click',()=>action('/reset'));
    $('liveRefresh')?.addEventListener('click',refresh);
    $('livePrev')?.addEventListener('click',()=>{current=Math.max(0,current-1);draw(snapshot);});
    $('liveNext')?.addEventListener('click',()=>{current=Math.min((snapshot?.events?.length||1)-1,current+1);draw(snapshot);});
    $('liveScrub')?.addEventListener('input',e=>{current=Number(e.target.value);draw(snapshot);});
    $('liveAuto')?.addEventListener('click',e=>{if(auto){clearInterval(auto);auto=null;e.target.textContent='▶ Animar';return;}current=0;auto=setInterval(()=>{if(current>=(snapshot?.events?.length||1)-1){clearInterval(auto);auto=null;e.target.textContent='▶ Animar';return;}current++;draw(snapshot);},950);e.target.textContent='⏸ Pausar';});
    setInterval(refresh,5000);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
