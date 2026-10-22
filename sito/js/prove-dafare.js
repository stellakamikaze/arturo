// Lo script della pagina /prove/dafare/: un voto e un commento per variante, poi un solo invio
// al modulo di feedback (/api/feedback), con le risposte messe in un testo. Fuori dall'HTML per la CSP.
(function(){
  var d=document, modulo=d.getElementById('prove'), domande=d.getElementById('domande');
  var invia=d.getElementById('invia'), contate=d.getElementById('contate');
  var CHIAVE='arturo-prove-dafare-1', MASSIMO=4000;
  var VOTI=[['mi serve','Mi serve'],['forse','Forse'],['non mi serve','Non mi serve']];
  var varianti=[].slice.call(d.querySelectorAll('[data-variante]'));

  // voto e commento sotto ogni variante
  varianti.forEach(function(v){
    var s=v.getAttribute('data-variante'), box=v.querySelector('.variante__voto');
    var titolo=v.querySelector('h3').firstChild.textContent.trim();
    var f=d.createElement('fieldset'), l=d.createElement('legend'), riga=d.createElement('div');
    l.className='nome-campo'; l.textContent='Cosa ne pensi della '+s+'?'; f.appendChild(l);
    riga.className='scelte';
    VOTI.forEach(function(x,i){
      var id='v-'+s+'-'+i, inp=d.createElement('input'), lab=d.createElement('label');
      inp.type='radio'; inp.name='voto-'+s; inp.id=id; inp.value=x[0];
      lab.htmlFor=id; lab.textContent=x[1];
      riga.appendChild(inp); riga.appendChild(lab);
    });
    f.appendChild(riga); box.appendChild(f);
    var c=d.createElement('div'), cl=d.createElement('label'), t=d.createElement('textarea');
    c.className='campo'; cl.className='nome-campo'; cl.htmlFor='n-'+s;
    cl.innerHTML='Un commento <small>(facoltativo)</small>';
    t.id='n-'+s; t.name='nota-'+s; t.maxLength=400; t.placeholder='Cosa cambi, cosa manca, cosa ti piace.';
    c.appendChild(cl); c.appendChild(t); box.appendChild(c);
    v.setAttribute('data-titolo',titolo);
  });

  // le risposte restano in questo browser fino all'invio
  function leggi(){try{return JSON.parse(localStorage.getItem(CHIAVE)||'{}')}catch(e){return {}}}
  function salva(){
    var dati={};
    [].forEach.call(modulo.elements,function(el){
      if(!el.name||el.name==='sito') return;
      if(el.type==='radio'){if(el.checked) dati[el.name]=el.value}
      else dati[el.name]=el.value;
    });
    try{localStorage.setItem(CHIAVE,JSON.stringify(dati))}catch(e){}
  }
  var prima=leggi();
  [].forEach.call(modulo.elements,function(el){
    if(!el.name||!(el.name in prima)) return;
    if(el.type==='radio') el.checked=(prima[el.name]===el.value);
    else el.value=prima[el.name];
  });
  var nome=d.getElementById('d-nome'), da=new URLSearchParams(location.search).get('da');
  if(da&&!nome.value) nome.value=da.charAt(0).toUpperCase()+da.slice(1);

  function voto(s){var x=modulo.querySelector('input[name="voto-'+s+'"]:checked'); return x?x.value:''}
  function conta(){contate.textContent=varianti.filter(function(v){return voto(v.getAttribute('data-variante'))}).length}
  modulo.addEventListener('change',function(){conta();salva()});
  modulo.addEventListener('input',salva);
  conta();

  function testo(){
    var righe=['Prove di /dafare (/prove/dafare/)','Da: '+(nome.value.trim()||'senza nome'),''];
    varianti.forEach(function(v){
      var s=v.getAttribute('data-variante'), n=modulo.elements['nota-'+s].value.trim();
      righe.push(s+' '+v.getAttribute('data-titolo')+': '+(voto(s)||'nessun voto'));
      if(n) righe.push('  '+n.replace(/\s*\n\s*/g,' / '));
    });
    var q=modulo.querySelector('input[name="quanti"]:checked');
    righe.push('','Progetti in una settimana: '+(q?q.value:'non risposto'));
    [['prima','Prima cosa da sapere'],['pm','Cosa manca']].forEach(function(x){
      var t=modulo.elements[x[0]].value.trim(); if(t) righe.push(x[1]+': '+t);
    });
    return righe.join('\n');
  }

  function mostra(id,motivo){
    [].forEach.call(domande.querySelectorAll('.esito'),function(e){e.classList.remove('visibile')});
    var e=d.getElementById(id);
    if(motivo){var m=e.querySelector('[data-motivo]'); if(m) m.textContent=motivo}
    e.classList.add('visibile'); domande.classList.toggle('spedito',id==='inviato');
    e.focus({preventScroll:true}); e.scrollIntoView({block:'center',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});
  }

  modulo.addEventListener('submit',function(ev){
    ev.preventDefault();
    var t=testo();
    if(t.length>MASSIMO){mostra('errore','Le risposte sono troppo lunghe: accorcia un commento e riprova.');return}
    var dati=new FormData();
    dati.append('tipo','idea'); dati.append('testo',t); dati.append('sito',modulo.elements.sito.value);
    invia.disabled=true;
    fetch(modulo.action,{method:'POST',body:dati,headers:{'Accept':'application/json'}}).then(function(r){
      return r.json().catch(function(){return {}}).then(function(j){return {stato:r.status,j:j}});
    }).then(function(x){
      invia.disabled=false;
      if(x.stato===201||x.stato===202){try{localStorage.removeItem(CHIAVE)}catch(e){} mostra('inviato'); return}
      mostra('errore',x.stato===429?'Per oggi il modulo ha ricevuto troppi messaggi. Riprova domani: le risposte restano qui.'
        :'Il server ha risposto: '+(x.j.errore||x.stato)+'. Riprova tra un momento.');
    }).catch(function(){
      invia.disabled=false;
      mostra('errore','La connessione non ha risposto. Riprova tra un momento: le risposte restano qui.');
    });
  });
})();
