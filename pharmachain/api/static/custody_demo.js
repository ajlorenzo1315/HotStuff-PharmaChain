/* Visualiza SOLO custodia confirmada y eventos reales de DistributedHotStuff. */
(() => {
 'use strict';
 const $ = id => document.getElementById(id);
 let busy = false;
 const esc = s => String(s ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 async function request(path, data) {
   const res = await fetch('/api/simulation'+path, {method:data===undefined?'GET':'POST',headers:{'Content-Type':'application/json'},body:data===undefined?undefined:JSON.stringify(data),cache:'no-store'});
   const json = await res.json();
   if(!res.ok) throw Error(typeof json.detail==='string'?json.detail:JSON.stringify(json.detail||json));
   return json.state||json;
 }
 function display(state) {
   const custody=state.custody_by_node||{};
   const nodeIds=Object.keys(custody).sort();
   const batches=[...new Set(nodeIds.flatMap(id=>Object.keys(custody[id]||{})))].sort();
   const pending=state.pending_transactions||[];
   $('custodyMode').textContent=state.pharmaceutical_transactions_enabled?'Transacciones distribuidas habilitadas':'Este backend todavía no habilita transacciones farmacéuticas';
   $('custodyPending').textContent=pending.length?pending.map(t=>`${t.type} · ${t.batch_id} · ${t.sender} → ${t.receiver||'registro'}`).join(' | '):'No hay transacciones pendientes';
   $('custodyTable').innerHTML=batches.length?`<table><thead><tr><th>Lote</th>${nodeIds.map(id=>`<th>${esc(id)}</th>`).join('')}</tr></thead><tbody>${batches.map(batch=>`<tr><td>${esc(batch)}</td>${nodeIds.map(id=>`<td>${esc(custody[id]?.[batch]??'No confirmado')}</td>`).join('')}</tr>`).join('')}</tbody></table>`:'No hay lotes confirmados. Registra un lote y ejecuta suficientes rondas hasta observar TX_COMMITTED.';
   const events=(state.events||[]).filter(e=>['TX_PENDING','TX_COMMITTED','COMMITTED','COMMIT_REJECTED','QC_FORMED','VOTE_REJECTED'].includes(e.event)).slice(-15);
   $('custodyEvents').innerHTML=events.length?events.map(e=>`<div><strong>${esc(e.event)}</strong> · ${esc(e.node||'red')} · ${esc(e.batch_id||e.block||'')} ${e.event==='TX_COMMITTED'?`· ${esc(e.previous_custodian||'sin custodio')} → ${esc(e.new_custodian||'sin custodio')}`:''}</div>`).join(''):'Todavía no hay eventos de transacciones, QC o commit en la ventana de eventos.';
   const inconsistent=batches.filter(batch=>new Set(nodeIds.map(id=>custody[id]?.[batch]??null)).size>1);
   $('custodyConsistency').textContent=inconsistent.length?`Custodia diferente entre nodos para: ${inconsistent.join(', ')}. Puede haber nodos atrasados; revisa sincronización y commits.`:'Sin diferencias de custodia entre los nodos mostrados (esto no constituye una prueba formal de safety).';
 }
 async function refresh() {try{display(await request(''));}catch(e){$('custodyMessage').textContent='No se pudo cargar: '+e.message;}}
 async function run(path,payload) {
   if(busy)return;busy=true;
   $('custodyMessage').textContent='Procesando…';
   try{await request(path,payload);await refresh();$('custodyMessage').textContent='Solicitud procesada. Comprueba los eventos y el estado confirmado.';}
   catch(e){$('custodyMessage').textContent='Error: '+e.message;}
   finally{busy=false;}
 }
 async function rounds() {
   if(busy)return;busy=true;
   const count=Number($('custodyRounds').value);
   if(!Number.isInteger(count)||count<1||count>20){busy=false;$('custodyMessage').textContent='Introduce entre 1 y 20 rondas.';return;}
   try{for(let i=0;i<count;i++){$('custodyMessage').textContent=`Ejecutando ronda ${i+1}/${count}…`;await request('/round',{});}await refresh();$('custodyMessage').textContent=`Ejecutadas ${count} rondas. Comprueba si existe TX_COMMITTED.`;}
   catch(e){$('custodyMessage').textContent='Error: '+e.message;}
   finally{busy=false;}
 }
 function init() {
   const section=$('custodyDemo');if(!section)return;
   $('custodyRegister').addEventListener('submit',e=>{e.preventDefault();run('/batches/register',{batch_id:$('custodyBatch').value.trim(),medicine_name:$('custodyMedicine').value.trim(),quantity:Number($('custodyQuantity').value)});});
   $('custodyTransfer').addEventListener('submit',e=>{e.preventDefault();run('/batches/transfer',{batch_id:$('custodyTransferBatch').value.trim(),sender_id:$('custodySender').value,receiver_id:$('custodyReceiver').value});});
   $('custodyRun').addEventListener('click',rounds);
   $('custodyRefresh').addEventListener('click',refresh);
   $('liveNormal')?.addEventListener('click',()=>setTimeout(refresh,800));
   $('liveReset')?.addEventListener('click',()=>setTimeout(refresh,800));
   refresh();
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
