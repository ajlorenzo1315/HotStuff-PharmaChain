/* Trace-driven visualization. Never invent a message if the backend did not record one. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const NS = 'http://www.w3.org/2000/svg';
  const state = {data:null, events:[], index:0, timer:null, busy:false};
  const descriptions = {
    PROPOSE:'Un líder propone un bloque; los validadores deben verificarlo antes de votar.',
    VOTE:'Un validador emite o procesa un voto. No equivale todavía a un QC.',
    QC:'Un certificado acredita votos válidos suficientes; aún no implica COMMIT inmediato.',
    COMMIT:'Se confirma un bloque según las reglas de tres cadenas de Chained HotStuff.',
    VIEW_CHANGE:'Timeout, cambio de vista o ronda sin QC: el progreso puede necesitar otro líder.',
    REJECT:'Se ha detectado o rechazado evidencia inválida. Consulta el registro exacto.',
    SYNC:'Un nodo solicita o procesa bloques y certificados para ponerse al día.',
    OTHER:'Evento registrado por el simulador. Consulta sus campos para interpretarlo.'
  };
  const make = (tag, cls, txt) => {const e=document.createElement(tag);if(cls)e.className=cls;if(txt!==undefined)e.textContent=String(txt);return e;};
  const svg = (tag, attrs, text) => {const e=document.createElementNS(NS,tag);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,String(v)));if(text!==undefined)e.textContent=String(text);return e;};
  const faultIDs = () => {
    if (!state.data || !Array.isArray(state.data.scenarios)) return [];
    const n = Number($('vlScenarioCount').value || 0);
    return Array.from({length:n}, (_,i) => `validator-${4-n+i}`);
  };
  const intro = {
    offline_leader:'El líder deja de proponer. Observa los timeouts y la recuperación de progreso.',
    quorum_loss:'Dos nodos ausentes impiden reunir los tres votos necesarios.',
    forged_qc:'Un certificado manipulado debe rechazarse antes de incorporarse al estado.',
    duplicate_qc:'Se comprueba la validación de certificados duplicados durante la sincronización.',
    unsolicited_sync:'Una respuesta sin petición correspondiente no debe modificar el estado.',
    valid_sync:'Control positivo: una sincronización legítima sí debe poder completarse.',
    equivocation:'Un líder distribuye propuestas incompatibles. Una bifurcación no implica doble commit.',
    omit:'Los validadores señalados omiten votos. Compara cuántas rondas forman QC.',
    invalid_signature:'Los validadores señalados firman incorrectamente. Los votos inválidos no deben contar.'
  };
  const ensureExtras = () => {
    if ($('vlExtra')) return;
    const section=$('visualLab');
    const panel=make('div','vl-extra'); panel.id='vlExtra';
    panel.innerHTML=`<div class="vl-box"><h3>Métricas de ejecución</h3><div id="vlAnalytics" class="vl-analytics"></div><h4>Eventos por categoría</h4><div id="vlHistogram"></div></div><div class="vl-box"><h3>Interpretación técnica</h3><p id="vlStepExplanation" class="vl-info">Ejecuta una simulación.</p><h4>Modelo de cuórum</h4><div id="vlQuorum"></div><h4>Verificación criptográfica interactiva</h4><p class="vl-info">Genera claves temporales Ed25519 en tu navegador, firma un voto de ejemplo y comprueba si la firma sigue siendo válida después de modificarlo.</p><div class="vl-controls"><button type="button" id="vlGenerateKeys">Generar claves</button><button type="button" id="vlSignVote" disabled>Firmar voto</button><button type="button" id="vlVerifyVote" disabled>Verificar firma</button></div><label class="vl-control-label" for="vlVoteMessage">Mensaje firmado</label><input id="vlVoteMessage" type="text" value="view=1;block=abc123;validator=0" style="width:100%"><p id="vlCryptoResult" class="vl-info" role="status">No hay claves generadas.</p><p id="vlKeyFingerprint" class="vl-info"></p><p class="vl-fine">Claves efímeras de demostración: no corresponden a los validadores del simulador.</p></div>`;
    section.append(panel);
    const exportButton=make('button','','⬇ Descargar traza JSON');
    exportButton.type='button';exportButton.id='vlExport';
    exportButton.addEventListener('click',()=>{
      if(!state.data)return;
      const blob=new Blob([JSON.stringify(state.data,null,2)],{type:'application/json'});
      const url=URL.createObjectURL(blob);const a=document.createElement('a');
      a.href=url;a.download=`hotstuff_${$('vlScenario').value}_evidencia.json`;a.click();
      setTimeout(()=>URL.revokeObjectURL(url),1000);
    });
    $('vlLoad').after(exportButton);
  };
  const renderAnalysis = e => {
    ensureExtras();
    const id=$('vlScenario').value, d=state.data;

    const scenario=Array.isArray(d?.scenarios)?d.scenarios.find(x=>String(x.faulty_count)===$('vlScenarioCount').value):d;
    const analysis=scenario?.analysis||{};
    const analytics=$('vlAnalytics');analytics.replaceChildren();
    const values=[
      ['Eventos observados',analysis.recorded_events,'Entradas de la traza, no paquetes de red'],
      ['Vistas registradas',analysis.observed_views,'Vistas distintas con eventos registrados'],
      ['Origen y destino',analysis.recorded_transmissions,'Eventos con ambos extremos conocidos'],
      ['Cobertura de transmisión',analysis.transmission_coverage_pct==null?'N/D':analysis.transmission_coverage_pct+'%','Porcentaje de eventos con extremos conocidos; no es rendimiento'],
      ['Tiempo simulado',analysis.observed_time_span==null?'N/D':analysis.observed_time_span,'Intervalo de la traza, no latencia real'],
    ];
    for(const [label,value,note] of values){const el=make('div','vl-measure');const title=make('small','',label);const num=make('strong','',value??'N/D');const hint=make('span','',note);el.append(title,num,hint);analytics.append(el);}
    const histogram=$('vlHistogram');histogram.replaceChildren();
    const entries=Object.entries(analysis.types||{}).sort((a,b)=>b[1]-a[1]);
    const max=Math.max(1,...entries.map(x=>x[1]));
    for(const [kind,n] of entries){const r=make('div','vl-barrow');r.append(make('span','',kind));const track=make('div','vl-bartrack');const bar=make('div','vl-barfill');bar.style.width=(n/max*100)+'%';track.append(bar);r.append(track,make('b','',n));histogram.append(r);}
    if(!entries.length)histogram.append(make('p','vl-warning','No hay eventos registrados; no se pueden calcular frecuencias.'));
    $('vlStepExplanation').textContent=e?(e.explanation||descriptions[e.type]||descriptions.OTHER):'No hay eventos individuales registrados.';
    const faults=faultIDs().length;const active=4-faults;
    $('vlQuorum').textContent=Array.isArray(d?.scenarios)?
      `${active} validadores no marcados como maliciosos; umbral QC = 3/4. ${active>=3?'El cuórum es matemáticamente posible, no garantizado.':'Con votos exclusivamente honestos no se alcanza el cuórum.'} Con 2 maliciosos se excede f=1.`:
      'Configuración teórica de referencia: n=4, f=1, QC=3 votos. La conectividad efectiva depende del escenario.';
  };
  const stop = () => {if(state.timer!==null){clearInterval(state.timer);state.timer=null;}$('vlPlay').textContent='▶ Reproducir';};
  const message = txt => {$('vlStatus').textContent=txt;};
  async function load(){
    stop();state.busy=true;$('vlLoad').disabled=true;message('Ejecutando experimento aislado…');
    try{
      const id=$('vlScenario').value, params=new URLSearchParams();
      let url;
      if(['omit','invalid_signature'].includes(id)){
        const rounds=Number($('vlRounds').value), seed=Number($('vlSeed').value);
        if(!Number.isInteger(rounds)||rounds<1||rounds>100||!Number.isSafeInteger(seed))throw Error('Rondas (1–100) y semilla entera requeridas');
        params.set('mode',id);params.set('rounds',String(rounds));params.set('seed',String(seed));
        url='/api/visual/byzantine?'+params;
      }else{url='/api/visual/attack/'+encodeURIComponent(id);}
      const response=await fetch(url);const data=await response.json();
      if(!response.ok)throw Error(typeof data.detail==='string'?data.detail:`HTTP ${response.status}`);
      state.data=data;
      if(Array.isArray(data.scenarios)){
        $('vlScenarioCount').hidden=false;
        $('vlScenarioCount').replaceChildren();
        for(const s of data.scenarios){const option=make('option','',`${s.faulty_count} maliciosos · ${s.qc_rounds}/${s.rounds} QC`);option.value=String(s.faulty_count);$('vlScenarioCount').append(option);}
      }else{$('vlScenarioCount').hidden=true;}
      setScenario();message('Experimento terminado. Reproduce los pasos para inspeccionar la evidencia.');
       if(['omit','invalid_signature'].includes(id)){
         if(typeof window.runByzantineComparison==='function')window.runByzantineComparison(id,Number($('vlRounds').value),Number($('vlSeed').value));
       }else{$('byzantineLab').hidden=true;}
    }catch(error){message('Error: '+error.message);state.data=null;state.events=[];render();}
    finally{state.busy=false;$('vlLoad').disabled=false;}
  }
  function setScenario(){
    stop();if(!state.data)return;
    const d=state.data, s=Array.isArray(d.scenarios)?d.scenarios.find(x=>String(x.faulty_count)===$('vlScenarioCount').value):d;
    state.events=s?.events||[];state.index=0;
    $('vlTitle').textContent=d.title||'Experimento';$('vlMechanism').textContent=d.mechanism||'—';
    $('vlImpact').textContent=d.impact||'—';$('vlMitigation').textContent=d.mitigation||'—';
    $('vlConclusion').textContent=Array.isArray(d.scenarios)?
      `${s.faulty_count} maliciosos: ${s.qc_rounds}/${s.rounds} rondas con QC; altura confirmada ${s.max_committed_height}; ${s.safety_ok?'sin conflictos detectados':'se detectó conflicto'}. ${d.conclusion}`:
      `${d.passed===true?'Criterio del experimento cumplido.':d.passed===false?'Criterio NO cumplido.':'Resultado sin veredicto booleano.'} ${d.observation||''} ${d.conclusion||''}`;
    $('vlLimits').textContent=d.limitations||'';
    $('vlExpected').textContent=d.expected||'Consulta los resultados y la traza.';
    $('vlMetric1').textContent=Array.isArray(d.scenarios)?`${s.qc_rounds}/${s.rounds}`:'—';
    $('vlMetric2').textContent=Array.isArray(d.scenarios)?String(s.invalid_votes):'—';
    $('vlMetric3').textContent=Array.isArray(d.scenarios)?String(s.max_committed_height):'—';
    render();
  }
  function render(){
    const events=state.events, e=events[state.index];
    $('vlProgress').max=Math.max(1,events.length-1);$('vlProgress').value=state.index;
    $('vlCounter').textContent=events.length?`Paso ${state.index+1} de ${events.length}`:'Sin eventos registrados';
    $('vlPrev').disabled=!events.length||state.index===0;
    $('vlNext').disabled=!events.length||state.index>=events.length-1;
    $('vlPlay').disabled=events.length<2;
    $('vlEventName').textContent=e?e.name:'No hay eventos para animar';
    $('vlEventMeaning').textContent=e?descriptions[e.type]||descriptions.OTHER:'El experimento puede ofrecer métricas aunque no registre mensajes individuales.';
    $('vlEventData').textContent=e?JSON.stringify(e.evidence,null,2):'—';
    drawNetwork(e);
    renderLiveConsensus(e);
    renderAnalysis(e);
    const steps=$('vlSteps');steps.replaceChildren();
    events.forEach((ev,i)=>{const b=make('button','vl-step '+(ev.type==='REJECT'?'reject':ev.type==='QC'?'qc':'')+(i===state.index?' active':''),String(i+1));b.title=`${ev.name} · vista ${ev.view??'?'}`;b.type='button';b.setAttribute('aria-label',`Ir al paso ${i+1}: ${ev.name}`);b.setAttribute('aria-current',i===state.index?'step':'false');b.addEventListener('click',()=>{stop();state.index=i;render();});steps.append(b);});
    const selected=steps.children[state.index];if(selected)selected.scrollIntoView({block:'nearest',inline:'nearest'});
  }
  // Resume exclusivamente acciones atribuidas por los eventos del simulador.
  function nodeStatistics(){
    const counts=Array.from({length:4},()=>({sent:0,received:0,last:null}));
    for(const ev of state.events.slice(0,state.index+1)){
      const src=/^validator-[0-3]$/.test(ev.source||'')?Number(ev.source.slice(-1)):-1;
      const dst=/^validator-[0-3]$/.test(ev.target||'')?Number(ev.target.slice(-1)):-1;
      if(src>=0){counts[src].sent++;counts[src].last=ev;}
      if(dst>=0){counts[dst].received++;counts[dst].last=ev;}
    }
    return counts;
  }
  function drawNetwork(event){
    const root=$('vlNetwork');root.setAttribute('viewBox','0 0 680 410');root.setAttribute('preserveAspectRatio','xMidYMid meet');root.replaceChildren();
    const positions=[[165,93],[515,93],[165,317],[515,317]];
    const source=event?.source||'',target=event?.target||'';
    const isValidator=x=>/^validator-[0-3]$/.test(x);
    const ids=[0,1,2,3].map(i=>`validator-${i}`);
    const faulty=faultIDs(), counts=nodeStatistics();
    root.append(svg('rect',{x:1,y:1,width:678,height:408,rx:14,fill:'#081626',stroke:'#34506a'}));
    for(let i=0;i<4;i++)for(let k=i+1;k<4;k++){
      const a=positions[i],b=positions[k];
      root.append(svg('line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],stroke:'#274b63','stroke-width':2,'stroke-dasharray':'5 7'}));
    }
    if(isValidator(source)&&isValidator(target)&&source!==target){
      const a=positions[ids.indexOf(source)],b=positions[ids.indexOf(target)];
      root.append(svg('line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],stroke:'#ffc978','stroke-width':5,'stroke-linecap':'round'}));
      const dot=svg('circle',{r:7,fill:'#fff0b3'});
      dot.append(svg('animateMotion',{dur:'1.5s',repeatCount:'indefinite',path:`M${a[0]},${a[1]} L${b[0]},${b[1]}`}));
      root.append(dot);
    }
    ids.forEach((id,i)=>{
      const [x,y]=positions[i], active=id===source||id===target;
      const role=id===source?'ENVÍA':id===target?'RECIBE':faulty.includes(id)?'ADVERSARIO':'EN ESPERA';
      const last=counts[i].last;
      const activity=active?(event.name||event.type||'Evento'):(last?`Último: ${last.name||last.type}`:'Sin eventos atribuidos');
      const shorten=(value,max=30)=>String(value).length>max?String(value).slice(0,max-1)+'…':String(value);
      const rect=svg('rect',{x:x-135,y:y-54,width:270,height:108,rx:12,fill:faulty.includes(id)?'#57323e':active?'#245b61':'#163047',stroke:faulty.includes(id)?'#ff8195':active?'#6ff2d1':'#5b7997','stroke-width':active?3:1.5});
      root.append(rect);
      root.append(svg('text',{x:x-118,y:y-29,'font-size':18,'font-weight':700,fill:'#f2fcff'},`V${i}`));
      root.append(svg('text',{x:x+118,y:y-29,'text-anchor':'end','font-size':11,'font-weight':700,fill:active?'#92ffdf':'#c8d6e6'},role));
      root.append(svg('line',{x1:x-118,y1:y-18,x2:x+118,y2:y-18,stroke:'#5d7d91','stroke-width':1}));
      const activityText=svg('text',{x:x-118,y:y+4,'font-size':12,fill:'#f2fcff'},shorten(activity));
      activityText.append(svg('title',{},activity));root.append(activityText);
      root.append(svg('text',{x:x-118,y:y+27,'font-size':11,fill:'#bfd5e5'},`Enviados: ${counts[i].sent}   Recibidos: ${counts[i].received}`));
      root.append(svg('text',{x:x-118,y:y+43,'font-size':10,fill:'#a9c2d6'},faulty.includes(id)?'Marcado como adversario':'Actividad registrada hasta este paso'));
    });
    const label=event?`${event.name||event.type} · vista ${event.view??'—'}`:'Red de cuatro validadores';
    root.append(svg('rect',{x:233,y:186,width:214,height:36,rx:9,fill:'#122c40',stroke:'#3e647d'}));
    root.append(svg('text',{x:340,y:209,'text-anchor':'middle',fill:'#e2f5ff','font-size':12},label.length>31?label.slice(0,30)+'…':label));
    if(event&&!isValidator(source)){
      root.append(svg('text',{x:340,y:237,'text-anchor':'middle',fill:'#ffc978','font-size':10},'Emisor no identificado en la traza'));
    }
  }
  function renderLiveConsensus(event){
    const d=state.data;
    const scenario=Array.isArray(d?.scenarios)?d.scenarios.find(x=>String(x.faulty_count)===$('vlScenarioCount').value):d;
    const scenarioId=$('vlScenario').value;
    const bad=faultIDs();
    // Estos dos escenarios son fallos de conectividad. No se atribuye desconexión a otros ataques.
    const offline=scenarioId==='quorum_loss'?['validator-2','validator-3']:
      scenarioId==='offline_leader'?['validator-0']:[];
    const excluded=new Set([...bad,...offline]);
    const eligible=4-excluded.size;
    const possible=eligible>=3;
    const label=$('vlLiveQuorum');
    label.textContent=`${eligible}/4 votos potencialmente válidos · ${possible?'Cuórum posible':'Sin cuórum honesto'}`;
    label.dataset.status=possible?'possible':'blocked';
    $('vlLiveQuorumBar').style.width=(eligible/4*100)+'%';
    const voters=$('vlLiveVoters');voters.replaceChildren();
    for(let i=0;i<4;i++){
      const id=`validator-${i}`;
      const status=bad.includes(id)?'Malicioso':offline.includes(id)?'Desconectado':'Elegible';
      const item=make('div','vl-voter '+(status==='Elegible'?'eligible':'excluded'),`V${i} · ${status}`);
      voters.append(item);
    }
    $('vlLiveExplanation').textContent=possible?
      'El umbral de 3 votos es alcanzable si los validadores elegibles reciben una propuesta segura y votan correctamente. No equivale a un QC observado.':
      'Quedan menos de 3 votos honestos potenciales. No puede formarse un QC solo con esos votos.';
    if(!['omit','invalid_signature','quorum_loss','offline_leader'].includes(scenarioId)){
      $('vlLiveExplanation').textContent='El contador representa el umbral teórico. Este escenario no proporciona estados individuales de conectividad o votos; consulta los eventos para verificar lo ocurrido.';
      label.textContent='3/4 votos requeridos · estado real no determinado';
      $('vlLiveQuorumBar').style.width='75%';
    }
    const checks=$('vlLiveChecks');checks.replaceChildren();
    const observed=event?.evidence||{};
    const rows=[
      ['Identidad del votante','Requerida','Voto único por identidad'],
      ['Firma digital','Requerida','Verificar con la clave pública del emisor'],
      ['Bloque y vista','Requeridos','Voto vinculado al bloque y la vista'],
      ['Umbral de votos','3 de 4','Votos distintos y válidos'],
      ['Certificado observado',scenario?.qc_rounds!=null?`${scenario.qc_rounds}/${scenario.rounds} rondas con QC`:'No determinado','Solo resultados medidos, si existen'],
    ];
    for(const [name,value,description] of rows){
      const line=make('div','vl-check');line.append(make('span','',name),make('strong','',value));line.title=description;checks.append(line);
    }
    $('vlLiveEvent').textContent=event?`${event.name} · vista ${event.view??'—'} · ${event.source||'origen desconocido'} → ${event.target||'destino desconocido'}`:'Sin evento seleccionado';
  }
  function initCalculator(){
    const input=$('vlNodeCount');
    const update=()=>{
      const n=Number(input.value);
      if(!Number.isInteger(n)||n<4||n>100){$('vlFormula').textContent='Introduce entre 4 y 100 validadores.';return;}
      const f=Math.floor((n-1)/3);
      const q=n-f;
      $('vlFormula').textContent=`n=${n} · f=${f} · cuórum=${q} · intersección mínima=${2*q-n}. Con f nodos maliciosos, la intersección contiene al menos ${Math.max(0,2*q-n-f)} honestos.`;
    };
    input.addEventListener('input',update);update();
  }
  function initCrypto(){
    let keys=null,signature=null,signedText=null;
    const encode=text=>new TextEncoder().encode(text);
    const hex=bytes=>Array.from(new Uint8Array(bytes)).map(b=>b.toString(16).padStart(2,'0')).join('');
    $('vlGenerateKeys').addEventListener('click',async()=>{
      try{
        if(!crypto?.subtle)throw Error('Web Crypto no disponible. Usa localhost o HTTPS.');
        keys=await crypto.subtle.generateKey({name:'Ed25519'},true,['sign','verify']);
        const pub=await crypto.subtle.exportKey('raw',keys.publicKey);
        const digest=await crypto.subtle.digest('SHA-256',pub);
        $('vlKeyFingerprint').textContent=`Huella SHA-256 de la clave pública: ${hex(digest).slice(0,32)}…`;
        signature=null;signedText=null;$('vlSignVote').disabled=false;$('vlVerifyVote').disabled=true;
        $('vlCryptoResult').textContent='Par Ed25519 temporal generado. La clave privada permanece en este navegador.';
      }catch(err){$('vlCryptoResult').textContent=`No se pudo generar Ed25519: ${err.message}`;}
    });
    $('vlSignVote').addEventListener('click',async()=>{
      if(!keys)return;
      signedText=$('vlVoteMessage').value;
      signature=await crypto.subtle.sign('Ed25519',keys.privateKey,encode(signedText));
      $('vlVerifyVote').disabled=false;
      $('vlCryptoResult').textContent='Voto de ejemplo firmado. Ahora verifica o cambia el mensaje para comprobar su integridad.';
    });
    $('vlVerifyVote').addEventListener('click',async()=>{
      if(!keys||!signature)return;
      try{
        const ok=await crypto.subtle.verify('Ed25519',keys.publicKey,signature,encode($('vlVoteMessage').value));
        $('vlCryptoResult').textContent=ok?'Firma válida: el contenido coincide con el mensaje firmado.':'Firma inválida: el mensaje cambió o no corresponde a esta firma.';
      }catch(err){$('vlCryptoResult').textContent=`Error de verificación: ${err.message}`;}
    });
  }
  function next(){if(state.index<state.events.length-1){state.index++;render();}else stop();}
  $('vlLoad').addEventListener('click',load);
  $('vlScenarioCount').addEventListener('change',setScenario);
  $('vlPrev').addEventListener('click',()=>{stop();state.index=Math.max(0,state.index-1);render();});
  $('vlNext').addEventListener('click',()=>{stop();next();});
  $('vlProgress').addEventListener('input',e=>{stop();state.index=Number(e.target.value);render();});
  $('vlPlay').addEventListener('click',()=>{if(state.timer!==null){stop();return;}if(state.index===state.events.length-1)state.index=0;render();$('vlPlay').textContent='⏸ Pausar';const ms=Number($('vlSpeed').value);state.timer=setInterval(next,ms);});
  $('vlSpeed').addEventListener('change',()=>{if(state.timer!==null){stop();$('vlPlay').click();}});
  $('vlScenario').addEventListener('change',()=>{stop();state.data=null;state.events=[];$('vlScenarioCount').hidden=true;$('byzantineLab').hidden=true;message('Ejecuta el escenario seleccionado.');render();});
  ensureExtras();
  initCrypto();
  initCalculator();
  render();
})();
