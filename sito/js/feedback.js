// Lo script della pagina /feedback/, fuori dall'HTML perché la CSP non ammette script inline (16/10/2026).
(function(){
  var d=document, modulo=d.getElementById('modulo'), testo=d.getElementById('f-testo'), conta=d.getElementById('conta');
  var invia=d.getElementById('invia');

  // il tipo può arrivare dal link: /feedback/?tipo=installazione
  var q=new URLSearchParams(location.search), tipo=q.get('tipo');
  if(tipo){var r=d.getElementById('t-'+tipo); if(r) r.checked=true}

  function contaCaratteri(){
    var n=testo.value.length; conta.textContent=n+' / 4000'; conta.classList.toggle('vicino',n>3600);
  }
  testo.addEventListener('input',contaCaratteri); contaCaratteri();

  function mostra(id,motivo){
    [].forEach.call(modulo.querySelectorAll('.esito'),function(e){e.classList.remove('visibile')});
    var e=d.getElementById(id); if(!e) return;
    if(motivo){var m=e.querySelector('[data-motivo]'); if(m) m.textContent=motivo}
    e.classList.add('visibile'); modulo.classList.toggle('spedito',id==='inviato');
    e.focus({preventScroll:true}); e.scrollIntoView({block:'center',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});
  }
  // l'esito del rimando senza script (/feedback/?inviato#inviato) vale anche con lo script
  if(location.hash==='#inviato') modulo.classList.add('spedito');

  /* ---------- invio ---------- */
  modulo.addEventListener('submit',function(ev){
    if(!window.fetch||!window.FormData) return; // senza fetch il modulo parte come form, e torna con l'ancora
    ev.preventDefault();
    var email=d.getElementById('f-email').value.trim();
    if(!testo.value.trim()){mostra('errore','Scrivi qualcosa, poi premi «Invia».');testo.focus();return}
    if(email&&!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)){mostra('errore','L\'email sembra incompleta: controllala, oppure lasciala vuota.');d.getElementById('f-email').focus();return}
    var dati=new FormData(modulo);
    invia.disabled=true; invia.firstChild.nodeValue='Invio in corso ';
    fetch(modulo.action,{method:'POST',body:dati,headers:{'Accept':'application/json'}}).then(function(r){
      return r.json().catch(function(){return {}}).then(function(j){return {stato:r.status,j:j}});
    }).then(function(x){
      if(x.stato===201||x.stato===202){
        mostra('inviato');
        if(window.plausible) plausible('Feedback inviato',{props:{tipo:(dati.get('tipo')||'altro')}});
      }else if(x.stato===429){mostra('troppi')}
      else if(x.stato===413){mostra('troppo-grande')}
      else{mostra('errore',x.j&&x.j.errore?('Il server dice: '+x.j.errore+'. Correggi e riprova.'):'Qualcosa non ha funzionato dalla parte del server. Riprova fra qualche minuto.')}
    }).catch(function(){
      mostra('errore','Non riesco a raggiungere il server: controlla la connessione e riprova. Quello che hai scritto è ancora qui.');
    }).then(function(){invia.disabled=false; invia.firstChild.nodeValue='Invia a Federico '});
  });
})();
