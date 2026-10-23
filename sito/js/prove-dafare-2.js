// Lo script della pagina /prove/dafare-2/: il pannello di prova da cliccare (linguette e catena,
// con le regole del prototipo in Claude Code) e le risposte, mandate in un solo invio al modulo
// di feedback (/api/feedback). Fuori dall'HTML per la CSP.
(function(){
  var d=document, box=d.getElementById('demo');
  if(!box) return;

  function v(id,progetto,titolo,chi,c){
    c=c||{};
    return {id:id,progetto:progetto,titolo:titolo,chi:chi,stato:c.stato||'da fare',giorni:'giorni' in c?c.giorni:null,motivo:c.motivo||null,dopo:c.dopo||[]};
  }
  var ESEMPIO=[
    v(4,'Sito nuovo',"Scegliere l'hosting",'decidi'),
    v(7,'Sito nuovo','Configurare il dominio','io',{dopo:[4]}),
    v(9,'Sito nuovo','Pubblicare la beta','io',{dopo:[7]}),
    v(8,'Sito nuovo','Attivare le email','io',{dopo:[4]}),
    v(5,'Sito nuovo','Mandare il logo in vettoriale','tu',{giorni:-1}),
    v(11,'Sito nuovo','Stampare i biglietti','io',{dopo:[5]}),
    v(6,'Sito nuovo','Approvare i testi della home','decidi'),
    v(12,'Sito nuovo','Impaginare la home','io',{dopo:[6]}),
    v(2,'Sito nuovo','Rileggere la pagina privacy','tu',{giorni:3}),
    v(13,'Sito nuovo','Preparare le immagini per i social','io'),
    v(15,'Sito nuovo','Scrivere la pagina contatti','io'),
    v(14,'Sito nuovo','Rinnovare il certificato','io',{stato:'fermo',motivo:'aspetta la risposta di Aruba'}),
    v(1,'Sito nuovo','Comprare il dominio','tu',{stato:'fatto'}),
    v(3,'Sito nuovo','Scegliere i colori','decidi',{stato:'fatto'}),
    v(10,'Sito nuovo','Scrivere la home','io',{stato:'fatto'}),
    v(16,'Sito nuovo','Raccogliere le foto','tu',{stato:'fatto'}),
    v(17,'Sito nuovo','Fare la mappa del sito','io',{stato:'fatto'}),
    v(20,'Podcast','Registrare la puntata 3','tu',{giorni:2}),
    v(21,'Podcast','Montare la puntata 3','io',{dopo:[20]}),
    v(22,'Podcast','Scrivere le note della puntata 3','io',{dopo:[21]}),
    v(24,'Podcast','Caricare la puntata 3 su Spotify','io',{dopo:[21]}),
    v(23,'Podcast','Scegliere la copertina della stagione','decidi'),
    v(25,'Podcast',"Invitare l'ospite della puntata 4",'tu'),
    v(26,'Podcast',"Preparare le domande per l'ospite",'io',{dopo:[25]}),
    v(18,'Podcast','Registrare la puntata 2','tu',{stato:'fatto'}),
    v(19,'Podcast','Montare la puntata 2','io',{stato:'fatto'}),
    v(31,'Fatture','Mandare la fattura a Rossi','tu',{giorni:-3}),
    v(32,'Fatture','Controllare i pagamenti di settembre','io'),
    v(34,'Fatture','Archiviare le ricevute','io',{dopo:[32]}),
    v(33,'Fatture','Chiedere il rimborso spese','tu',{stato:'fermo',motivo:'aspetta il commercialista'}),
    v(30,'Fatture','Mandare la fattura di agosto','tu',{stato:'fatto'}),
    v(40,'Trasloco','Chiamare la ditta','tu'),
    v(41,'Trasloco','Scegliere il giorno del trasloco','decidi',{dopo:[40]})
  ];
  function copia(){return ESEMPIO.map(function(t){var c={};for(var k in t)c[k]=t[k];return c})}
  var voci=copia(), filtro='tutti', catena=false, scelto=null, esito='';

  function aperta(t){return t.stato!=='fatto'}
  function progetti(){var vis=[];voci.forEach(function(t){if(aperta(t)&&vis.indexOf(t.progetto)<0)vis.push(t.progetto)});return vis}
  function trova(id){for(var i=0;i<voci.length;i++)if(voci[i].id===id)return voci[i]}
  function attende(t){return t.dopo.filter(function(id){var x=trova(id);return x&&aperta(x)})}
  function sblocca(t){return voci.filter(function(x){return aperta(x)&&x.dopo.indexOf(t.id)>=0}).map(function(x){return x.id})}
  function gruppo(t){return t.stato==='fermo'?'fermo':t.chi}
  function chiTesto(t){return t.stato==='fermo'?'fermo':t.chi==='tu'?'tocca a te':t.chi==='decidi'?'decidi tu':'faccio io'}
  function scaduta(t){return t.giorni!==null&&t.giorni<0}
  function scadenza(g){if(g===null)return '';if(g<0)return g===-1?'scaduto ieri':'scaduto da '+(-g)+' g';return g===0?'scade oggi':g===1?'scade domani':'scade tra '+g+' g'}
  // La regola di Arturo per "da dove partire": prima chi chiede una persona, poi chi sblocca, poi le scadute.
  function chiave(t){return [t.stato==='fermo'?1:0,t.chi==='io'?1:0,sblocca(t).length?0:1,scaduta(t)?0:1,t.giorni===null?1e6:t.giorni,t.id]}
  function prima(a,b){var x=chiave(a),y=chiave(b);for(var i=0;i<x.length;i++)if(x[i]!==y[i])return x[i]-y[i];return 0}
  function daQui(p){
    var c=voci.filter(function(t){return t.progetto===p&&t.stato==='da fare'&&!attende(t).length}).sort(prima)[0];
    if(!c) return null;
    var s=sblocca(c);
    return {t:c,motivo:s.length?'sblocca '+s.map(function(n){return '#'+n}).join(', '):scaduta(c)?scadenza(c.giorni):chiTesto(c)};
  }
  function conta(n,uno,tanti){return n===1?'1 '+uno:n+' '+tanti}
  function stato(p,soloAperte){
    var qui=voci.filter(function(t){return p===null||t.progetto===p});
    var ap=qui.filter(aperta), f=qui.length-ap.length;
    var sc=ap.filter(scaduta).length, fe=ap.filter(function(t){return t.stato==='fermo'}).length;
    return [conta(ap.length,'aperta','aperte'),!soloAperte&&f?conta(f,'fatta','fatte'):'',sc?conta(sc,'scaduta','scadute'):'',fe?conta(fe,'ferma','ferme'):''].filter(Boolean).join(' · ');
  }
  function lista(p){
    var ord=['tu','decidi','io','fermo'];
    return voci.filter(function(t){return t.progetto===p&&aperta(t)})
      .sort(function(a,b){return ord.indexOf(gruppo(a))-ord.indexOf(gruppo(b))||prima(a,b)})
      .map(function(t){return {t:t,ramo:''}});
  }
  // La catena: ogni cosa sotto la prima cosa aperta che aspetta.
  function albero(p){
    var qui=voci.filter(function(t){return t.progetto===p&&aperta(t)}), fuori=[];
    function padre(t){return attende(t).filter(function(id){return qui.some(function(x){return x.id===id})})[0]}
    function figli(id){return qui.filter(function(t){return padre(t)===id}).sort(function(a,b){return a.id-b.id})}
    function giu(t,rientro,ultimo,radice){
      fuori.push({t:t,ramo:radice?'':rientro+(ultimo?'└─ ':'├─ ')});
      var s=figli(t.id), dentro=radice?'':rientro+(ultimo?'   ':'│  ');
      s.forEach(function(f,i){giu(f,dentro,i===s.length-1,false)});
    }
    qui.filter(function(t){return padre(t)===undefined}).sort(prima).forEach(function(r){giu(r,'',true,true)});
    return fuori;
  }
  function righe(){return filtro==='tutti'?[]:catena?albero(filtro):lista(filtro)}

  function el(tag,cls,testo){var e=d.createElement(tag);if(cls)e.className=cls;if(testo!=null)e.textContent=testo;return e}
  function bottone(cls,testo,fai,etichetta){var b=el('button',cls,testo);b.type='button';if(etichetta)b.setAttribute('aria-label',etichetta);b.addEventListener('click',fai);return b}

  function disegna(fuoco){
    var elenco=progetti();
    if(filtro!=='tutti'&&elenco.indexOf(filtro)<0) filtro='tutti';
    box.textContent='';
    var testa=el('div','pan__comandi');
    testa.appendChild(el('span',null,'Le tue cose da fare'));
    if(filtro!=='tutti'){
      var bc=bottone('tasto',catena?'lista':'catena',function(){catena=!catena;esito='';disegna('tasto')});
      bc.setAttribute('aria-pressed',catena?'true':'false');
      testa.appendChild(bc);
    }
    box.appendChild(testa);

    var lin=el('div','linguette'); lin.setAttribute('role','group'); lin.setAttribute('aria-label','Progetti');
    ['tutti'].concat(elenco).forEach(function(p){
      var n=p==='tutti'?voci.filter(aperta).length:voci.filter(function(t){return t.progetto===p&&aperta(t)}).length;
      var b=bottone('',(p==='tutti'?'Tutti':p)+' '+n,function(){filtro=p;scelto=null;esito='';disegna('linguetta-'+p)});
      b.setAttribute('aria-pressed',filtro===p?'true':'false'); b.setAttribute('data-fuoco','linguetta-'+p);
      lin.appendChild(b);
    });
    box.appendChild(lin);

    if(filtro==='tutti'){
      box.appendChild(el('p','stato',conta(elenco.length,'progetto','progetti')+' · '+stato(null)));
      elenco.forEach(function(p){
        var dq=daQui(p), b=bottone('progetto','',function(){filtro=p;scelto=null;esito='';disegna('linguetta-'+p)});
        b.appendChild(el('b',null,p)); b.appendChild(d.createTextNode('  '+stato(p,true)));
        if(dq) b.appendChild(el('span',null,'da qui: #'+dq.t.id+' '+dq.t.titolo));
        box.appendChild(b);
      });
    } else {
      box.appendChild(el('p','stato',filtro+' · '+stato(filtro)));
      var dq=daQui(filtro);
      if(dq) box.appendChild(el('p','daqui','Da qui: #'+dq.t.id+' '+dq.t.titolo+', '+dq.motivo));
      var rr=righe(), attiva=(rr.filter(function(r){return r.t.id===scelto})[0]||rr[0]||{t:{}}).t.id, prec='';
      var TIT={tu:'TOCCA A TE',decidi:'DECIDI TU',io:'FACCIO IO',fermo:'FERMO'};
      rr.forEach(function(r){
        var g=gruppo(r.t);
        if(!catena&&g!==prec) box.appendChild(el('p','gruppo-h '+g,TIT[g]));
        prec=g;
        var att=attende(r.t), destra=catena?chiTesto(r.t)+(scaduta(r.t)?', '+scadenza(r.t.giorni):'')
          :r.t.stato==='fermo'?(r.t.motivo||''):att.length?'aspetta '+att.map(function(n){return '#'+n}).join(', '):scadenza(r.t.giorni);
        var b=bottone('r'+(r.t.id===attiva?' sel':''),'',function(){scelto=r.t.id;disegna('riga-'+r.t.id)});
        b.setAttribute('data-fuoco','riga-'+r.t.id); b.setAttribute('aria-pressed',r.t.id===attiva?'true':'false');
        b.appendChild(el('span','k','#'+r.t.id));
        var tit=el('span'); if(r.ramo) tit.appendChild(el('span','ramo',r.ramo)); tit.appendChild(d.createTextNode(r.t.titolo));
        b.appendChild(tit);
        b.appendChild(el('span','m'+(scaduta(r.t)&&!catena?' scade':''),destra));
        box.appendChild(b);
      });
      var az=el('div','azioni');
      function cambia(come,testo){return function(){var t=trova(attiva);if(!t)return;come(t);esito=testo(t);if(t.stato==='fatto')scelto=null;disegna()}}
      az.appendChild(bottone('','fatto',cambia(function(t){t.stato='fatto'},function(t){return 'Fatto: #'+t.id+' '+t.titolo+'.'})));
      az.appendChild(bottone('','ferma o riprendi',cambia(function(t){var f=t.stato==='fermo';t.stato=f?'da fare':'fermo';t.motivo=f?null:'fermato da te'},function(t){return '#'+t.id+': '+t.stato+'.'})));
      az.appendChild(bottone('','chi lo fa',cambia(function(t){t.chi=t.chi==='tu'?'decidi':t.chi==='decidi'?'io':'tu'},function(t){return '#'+t.id+': '+chiTesto(t)+'.'})));
      az.appendChild(bottone('','ripristina',function(){voci=copia();scelto=null;esito='Dati di esempio ripristinati.';disegna()}));
      box.appendChild(az);
    }
    var es=el('p','esito-riga',esito); es.setAttribute('role','status'); box.appendChild(es);
    if(fuoco){var f=fuoco==='tasto'?box.querySelector('.tasto'):box.querySelector('[data-fuoco="'+fuoco+'"]'); if(f) f.focus({preventScroll:true})}
  }
  disegna();
})();

(function(){
  var d=document, modulo=d.getElementById('prove'), domande=d.getElementById('domande');
  var invia=d.getElementById('invia'), contate=d.getElementById('contate'), totale=d.getElementById('totale');
  var CHIAVE='arturo-prove-dafare-2', MASSIMO=4000;
  var VOTI=[['mi serve','Mi serve'],['forse','Forse'],['non mi serve','Non mi serve']];
  var varianti=[].slice.call(d.querySelectorAll('[data-variante]'));
  totale.textContent=varianti.length;

  // voto e commento sotto ogni voce
  varianti.forEach(function(v){
    var s=v.getAttribute('data-variante'), box=v.querySelector('.variante__voto');
    var titolo=v.querySelector('h3').firstChild.textContent.trim();
    var f=d.createElement('fieldset'), l=d.createElement('legend'), riga=d.createElement('div');
    l.className='nome-campo'; l.textContent='Cosa ne pensi di '+s+'?'; f.appendChild(l);
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
    var righe=['Prove di /dafare, seconda parte (/prove/dafare-2/)','Da: '+(nome.value.trim()||'senza nome'),''];
    varianti.forEach(function(v){
      var s=v.getAttribute('data-variante'), n=modulo.elements['nota-'+s].value.trim();
      righe.push(s+' '+v.getAttribute('data-titolo')+': '+(voto(s)||'nessun voto'));
      if(n) righe.push('  '+n.replace(/\s*\n\s*/g,' / '));
    });
    righe.push('');
    [].forEach.call(d.querySelectorAll('[data-domanda]'),function(q){
      var etichetta=q.getAttribute('data-domanda'), r;
      if(q.tagName==='FIELDSET'){var x=q.querySelector('input:checked'); r=x?x.value:'non risposto'}
      else{r=q.value.trim(); if(!r) return; r=r.replace(/\s*\n\s*/g,' / ')}
      righe.push(etichetta+': '+r);
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
