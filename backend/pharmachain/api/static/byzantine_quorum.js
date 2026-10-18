/* Cuórum del laboratorio: separa votos posibles, votos rechazados y QC observados. */
(() => {
 'use strict';
 const $=id=>document.getElementById(id);
 const add=(p,tag,cls,text)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=String(text);p.append(e);return e;};
 const num=v=>Number.isFinite(Number(v))?Number(v):null;
 function show(data){
   const panel=$('byzQcInspector');if(!panel)return;
   panel.replaceChildren();
   add(panel,'strong','','Cuórum y validación del ataque');
   const mode=$('vlScenario')?.value;
   if(!['omit','invalid_signature'].includes(mode)){
     add(panel,'p','','Selecciona «Omitir votos» o «Firma inválida» para comparar el efecto sobre el cuórum.');return;
   }
   const scenarios=Array.isArray(data?.scenarios)?data.scenarios:[];
   if(!scenarios.length){add(panel,'p','','Ejecuta el experimento para consultar los certificados observados.');return;}
   const grid=add(panel,'div','qc-row');
   for(const s of scenarios){
     const bad=num(s.faulty_count),rounds=num(s.rounds),qc=num(s.qc_rounds),invalid=num(s.invalid_votes);
     const box=add(grid,'div','qc-cell');
     add(box,'span','',`${bad??'—'} adversario(s)`);
     add(box,'strong','',rounds!==null&&qc!==null?`${qc}/${rounds} QC`:'QC: sin datos');
     add(box,'small','',bad!==null?`${Math.max(0,4-bad)}/4 votos honestos posibles; mínimo 3`:'Votos honestos no determinados');
     if(mode==='invalid_signature'&&invalid!==null)add(box,'small','',` · ${invalid} votos inválidos registrados`);
   }
   const chosen=scenarios.find(s=>String(s.faulty_count)===$('vlScenarioCount')?.value)||scenarios[0];
   const bad=num(chosen.faulty_count),honest=bad===null?null:4-bad;
   const explanation=mode==='omit'?'Los adversarios omiten votos: no deben contabilizarse para formar el certificado.':'Los votos con firmas inválidas deben rechazarse y no contribuir al certificado.';
   add(panel,'p','',explanation);
   if(honest!==null)add(panel,'p','',honest>=3?`Con ${honest} validadores honestos, el cuórum sigue siendo posible. Los QC observados aparecen arriba.`:`Con ${honest} validadores honestos no se puede alcanzar un QC únicamente con sus votos. Dos adversarios exceden f=1.`);
   add(panel,'small','','El recuento de QC procede de la respuesta del experimento; el número de votos honestos posibles es una estimación teórica.');
 }
 async function load(){
   const mode=$('vlScenario')?.value;
   if(!['omit','invalid_signature'].includes(mode)){show(null);return;}
   const rounds=Number($('vlRounds')?.value),seed=Number($('vlSeed')?.value);
   if(!Number.isInteger(rounds)||rounds<1||rounds>100||!Number.isSafeInteger(seed))return;
   const params=new URLSearchParams({mode,rounds:String(rounds),seed:String(seed)});
   try{const response=await fetch('/api/visual/byzantine?'+params);if(!response.ok)throw Error(`HTTP ${response.status}`);show(await response.json());}
   catch(e){const panel=$('byzQcInspector');if(panel)panel.textContent='No se pudo consultar el cuórum del ataque: '+e.message;}
 }
 function init(){
   const anchor=$('vlLiveEvent');if(!anchor||$('byzQcInspector'))return;
   const panel=document.createElement('div');panel.id='byzQcInspector';anchor.parentElement.append(panel);
   $('vlLoad')?.addEventListener('click',()=>setTimeout(load,100));
   $('vlScenarioCount')?.addEventListener('change',load);
   $('vlScenario')?.addEventListener('change',()=>show(null));
   show(null);
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
