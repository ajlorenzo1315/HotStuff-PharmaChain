/* Grafo autónomo: no depende de renderTopology, visual_lab.js ni de claves privadas. */
(() => {
 'use strict';
 const $ = id => document.getElementById(id);
 const NS='http://www.w3.org/2000/svg';
 const coords=[[180,120],[540,120],[180,385],[540,385]];
 const names=['Laboratorio','Distribuidor','Farmacia','Regulador'];
 let state=null, selected=0, cursor=0, playing=null, busy=false, lastLength=-1;
 const element=(tag,attrs={},value)=>{const e=document.createElementNS(NS,tag);for(const [k,v] of Object.entries(attrs))e.setAttribute(k,String(v));if(value!==undefined)e.textContent=String(value);return e;};
 const put=(parent,tag,attrs={},value)=>{const e=element(tag,attrs,value);parent.append(e);return e;};
 const idx=value=>{if(typeof value==='number'&&value>=0&&value<4)return value;const m=String(value??'').match(/(?:validator[-_]|^v)([0-3])$/i);return m?+m[1]:-1;};
 const events=()=>Array.isArray(state?.events)?state.events:[];
 const nodes=()=>Array.from({length:4},(_,i)=>state?.nodes?.find(n=>idx(n.id)===i)||state?.nodes?.[i]||{id:`validator-${i}`});
 const eventAt=()=>events()[cursor]||null;
 function draw(){
   const root=$('liveGraphV2');if(!root)return;
   root.setAttribute('viewBox','0 0 720 505');root.setAttribute('preserveAspectRatio','xMidYMid meet');root.replaceChildren();
   put(root,'rect',{x:1,y:1,width:718,height:503,rx:14,fill:'#09192b',stroke:'#35536e'});
   const ev=eventAt(),src=idx(ev?.source??ev?.sender??ev?.validator??ev?.node_id),dst=idx(ev?.target??ev?.receiver??ev?.destination);
   for(let i=0;i<4;i++)for(let j=i+1;j<4;j++){
     const a=coords[i],b=coords[j];put(root,'line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],stroke:'#3a5873','stroke-width':2,'stroke-dasharray':'5 9'});
   }
   if(src>=0&&dst>=0&&src!==dst){
     const a=coords[src],b=coords[dst];put(root,'line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],stroke:'#ffd18a','stroke-width':5});
     const dot=put(root,'circle',{r:8,fill:'#fff0bd'});
     put(dot,'animateMotion',{dur:'1.35s',repeatCount:'indefinite',path:`M${a[0]},${a[1]} L${b[0]},${b[1]}`});
   }
   const list=nodes();
   list.forEach((n,i)=>{
     const [x,y]=coords[i],lead=n.id===state?.leader,active=i===src||i===dst;
     const group=put(root,'g',{role:'button',tabindex:0,style:'cursor:pointer','aria-label':`Seleccionar validador V${i}`});
     put(group,'rect',{x:x-146,y:y-78,width:292,height:156,rx:13,fill:n.online===false?'#522b39':n.online===true?'#123f45':'#21374d',stroke:i===selected?'#ffd18a':n.online===false?'#ff8497':active?'#ffe1a0':'#66dcca','stroke-width':i===selected?4:2});
     put(group,'text',{x:x-127,y:y-49,fill:'#fff','font-size':19,'font-weight':700},`V${i} · ${names[i]}`);
     put(group,'text',{x:x-127,y:y-23,fill:lead?'#ffd18a':'#cfe5f0','font-size':13},`${lead?'★ Líder · ':''}${n.online===true?'Conectado':n.online===false?'Desconectado':'Estado no recibido'}`);
     put(group,'text',{x:x-127,y:y+3,fill:'#d7e9f5','font-size':12},`Vista ${n.view??'—'}   Altura ${n.height??'—'}   QC ${n.certificates??'—'}`);
     const action=i===src?`Envía ${ev?.event||ev?.name||'evento'}`:i===dst?`Recibe ${ev?.event||ev?.name||'evento'}`:'Sin mensaje dirigido registrado';
     put(group,'text',{x:x-127,y:y+28,fill:active?'#ffe2a5':'#b8cfe0','font-size':12},action.slice(0,41));
     const key=n.public_key||n.publicKey;
     put(group,'text',{x:x-127,y:y+52,fill:'#a9d9e1','font-size':11},key?`Clave pública: ${String(key).slice(0,23)}…`:'Clave pública no expuesta');
     const choose=()=>{selected=i;draw();};group.addEventListener('click',choose);group.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose();}});
   });
   const known=list.every(n=>typeof n.online==='boolean'),online=list.filter(n=>n.online===true).length,q=Number(state?.quorum)||3;
   if($('onlineCount'))$('onlineCount').textContent=known?`${online}/4`:'—';
   if($('onlineBar'))$('onlineBar').style.width=known?`${online*25}%`:'0%';
   if($('votePotential'))$('votePotential').textContent=known?`${online}/${q}`:'—';
   if($('quorumExplanation'))$('quorumExplanation').textContent=known?(online>=q?'Cuórum alcanzable si se reciben votos distintos y válidos.':'Sin suficientes nodos conectados para el cuórum.'):'Topología disponible; esperando respuesta de la API.';
   const n=list[selected];
   if($('inspectorTitle'))$('inspectorTitle').textContent=`V${selected} · ${names[selected]}`;
   if($('inspectorDetails'))$('inspectorDetails').textContent=`${n.online===true?'Conectado':n.online===false?'Desconectado':'Sin datos'} · Vista ${n.view??'—'} · Altura ${n.height??'—'} · QC ${n.certificates??'—'}`;
   if($('inspectorKey'))$('inspectorKey').textContent=n.public_key?`Clave pública: ${n.public_key}`:'Clave pública no expuesta por la API. Nunca se muestra la clave privada.';
   if($('inspectorToggle')){$('inspectorToggle').disabled=typeof n.online!=='boolean';$('inspectorToggle').textContent=n.online===false?'Reconectar':'Desconectar';}
   if($('inspectorSync'))$('inspectorSync').disabled=n.online!==true;
   if($('networkActivity'))$('networkActivity').textContent=ev?`Evento ${cursor+1}/${events().length}: ${ev.event||ev.name||'evento'} · ${src<0?'origen desconocido':'V'+src} → ${dst<0?'destino desconocido':'V'+dst}`:'Sin eventos de comunicación seleccionados. Ejecuta una ronda para generar actividad.';
   const scrub=$('liveScrub');if(scrub){scrub.max=Math.max(0,events().length-1);scrub.value=Math.min(cursor,events().length-1);scrub.disabled=events().length<2;}
 }
 async function refresh(){
   try{const r=await fetch('/api/simulation',{cache:'no-store'});if(!r.ok)throw Error(`HTTP ${r.status}`);const body=await r.json();const data=body.state||body;if(!Array.isArray(data.nodes))throw Error('Falta nodes[] en la respuesta');state=data;if(events().length!==lastLength){cursor=Math.max(0,events().length-1);lastLength=events().length;}if($('liveError'))$('liveError').textContent='';draw();}
   catch(e){if($('liveError'))$('liveError').textContent=`Error de actualización: ${e.message}`;draw();}
 }
 async function act(path,body={}){
   if(busy)return;busy=true;
   try{const r=await fetch('/api/simulation'+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});if(!r.ok){const data=await r.json().catch(()=>({}));throw Error(data.detail||`HTTP ${r.status}`);}await refresh();}
   catch(e){if($('liveError'))$('liveError').textContent=`Error en operación: ${e.message}`;}finally{busy=false;}
 }
 function init(){
   if(!$('liveGraphV2'))return;draw();refresh();
   $('liveNormal')?.addEventListener('click',()=>act('/round'));
   $('liveReset')?.addEventListener('click',()=>act('/reset'));
   $('liveRefresh')?.addEventListener('click',refresh);
   $('livePrev')?.addEventListener('click',()=>{cursor=Math.max(0,cursor-1);draw();});
   $('liveNext')?.addEventListener('click',()=>{cursor=Math.min(events().length-1,cursor+1);draw();});
   $('liveScrub')?.addEventListener('input',e=>{cursor=Number(e.target.value);draw();});
   $('inspectorToggle')?.addEventListener('click',()=>{const n=nodes()[selected];if(typeof n.online==='boolean')act(n.online?'/disconnect':'/reconnect',{node_id:n.id});});
   $('inspectorSync')?.addEventListener('click',()=>act('/recover',{node_id:nodes()[selected].id}));
   $('inspectorStep')?.addEventListener('click',()=>act('/round'));
   $('liveAuto')?.addEventListener('click',e=>{if(playing){clearInterval(playing);playing=null;e.target.textContent='▶ Animar';return;}cursor=0;draw();e.target.textContent='⏸ Pausar';playing=setInterval(()=>{if(cursor>=events().length-1){clearInterval(playing);playing=null;e.target.textContent='▶ Animar';return;}cursor++;draw();},1000);});
   // El refresco no debe saltar el reproductor si no hay eventos nuevos.
   setInterval(()=>{if(!playing)refresh();},5000);
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
