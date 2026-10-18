/* Classifies only observed test verdicts; does not invent results. */
(() => {
 const $=id=>document.getElementById(id);
 const names={offline_leader:'Líder desconectado',quorum_loss:'Pérdida de cuórum',forged_qc:'QC falsificado',duplicate_qc:'QC duplicado',unsolicited_sync:'Sync no solicitado',valid_sync:'Sincronización válida',equivocation:'Equivocación del líder',omit:'Omisión de votos',invalid_signature:'Firmas inválidas'};
 const cache=new Map();
 function draw(){const root=$('attackOutcomeRows');if(!root)return;root.replaceChildren();for(const [id,title] of Object.entries(names)){
  const row=document.createElement('div');row.className='attack-outcome-row';
  const name=document.createElement('strong');name.textContent=title;
  const badge=document.createElement('span');const result=cache.get(id);
  badge.textContent=result===true?'Criterio superado':result===false?'Criterio fallido':'Sin evaluar';
  badge.className=result===true?'outcome-ok':result===false?'outcome-fail':'outcome-unknown';
  row.append(name,badge);root.append(row);
 }}
 async function inspect(){const id=$('vlScenario')?.value;if(!id)return;
  // Use the existing experiment request. Read its result only after the original click handler finishes.
  try{
   const url=['omit','invalid_signature'].includes(id)?'/api/visual/byzantine?'+new URLSearchParams({mode:id,rounds:$('vlRounds').value,seed:$('vlSeed').value}):'/api/visual/attack/'+encodeURIComponent(id);
   const response=await fetch(url);if(!response.ok)return;const data=await response.json();
   if(typeof data.passed==='boolean')cache.set(id,data.passed);
   else if(Array.isArray(data.scenarios)){
    // QC rates are liveness measurements, not pass/fail security verdicts.
    cache.set(id,null);
   }
   draw();
  }catch(error){console.debug('Attack outcome unavailable',error);}
 }
 function init(){draw();$('vlLoad')?.addEventListener('click',()=>{setTimeout(inspect,150);});}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
