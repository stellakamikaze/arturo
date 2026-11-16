// Le scene della landing a passi (16/11/2026). Fuori dall'HTML perché la CSP non ammette script inline.
// Senza questo script ogni scena mostra già il suo stato finale.
(function(){
  var d=document;
  var riduci=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
  function tutti(sel,radice){return [].slice.call((radice||d).querySelectorAll(sel))}
  function euro(n){return n.toString().replace(/\B(?=(\d{3})+(?!\d))/g,'.')+' €'}

  /* l'indice dei passi segue la lettura */
  var voci=tutti('.indice-passi a');
  if(voci.length&&'IntersectionObserver' in window){
    var segna=function(id){voci.forEach(function(a){if(a.getAttribute('href')==='#'+id)a.setAttribute('aria-current','step');else a.removeAttribute('aria-current')})};
    var visto=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting)segna(e.target.id)})},{rootMargin:'-40% 0px -55% 0px'});
    tutti('.passo').forEach(function(p){visto.observe(p)});
  }

  /* passo 1: i mestieri */
  tutti('[data-scena="mestieri"]').forEach(function(s){
    var chi=s.querySelector('.mestiere__chi'), torna=s.querySelector('.mestiere__torna');
    var etichetta=torna.querySelector('span');
    tutti('.scelte button',s).forEach(function(b,i,tuttiB){
      b.addEventListener('click',function(){
        tuttiB.forEach(function(x){x.setAttribute('aria-pressed',x===b?'true':'false')});
        chi.textContent=b.getAttribute('data-chi');
        torna.textContent='';torna.appendChild(etichetta);torna.appendChild(d.createTextNode(b.getAttribute('data-torna')));
      });
    });
  });

  /* passo 2: in chat o nel terminale */
  tutti('[data-scena="recinto"]').forEach(function(s){
    var bottoni=tutti('.interruttore button',s), viste=tutti('[data-vista]',s);
    function mostra(nome){
      bottoni.forEach(function(b){b.setAttribute('aria-pressed',b.getAttribute('data-mostra')===nome?'true':'false')});
      viste.forEach(function(v){v.hidden=v.getAttribute('data-vista')!==nome});
    }
    bottoni.forEach(function(b){b.addEventListener('click',function(){mostra(b.getAttribute('data-mostra'))})});
    mostra('chat');
  });

  /* passo 3: la pila degli strati */
  tutti('[data-scena="strati"]').forEach(function(s){
    var det=s.querySelector('.pila__dettaglio'), strati=tutti('.pila__strato',s);
    strati.forEach(function(b){b.addEventListener('click',function(){
      strati.forEach(function(x){x.setAttribute('aria-pressed',x===b?'true':'false')});
      det.textContent=b.getAttribute('data-cosa');
    })});
  });

  /* passi 4 e 7: una risposta nel terminale */
  var ESITI={
    guardia:{si:['Bash  rm -r bozze-vecchie · cartella cancellata','Fatto. La cartella non è passata dal cestino.'],
             no:[null,'Va bene: la cartella resta dov\'è.']},
    orsa:{si:['Edit  CLAUDE.md, sezione Regole','Fatto. Da qui la regola vale in ogni sessione.'],
          no:[null,'Va bene: non te lo ripropongo.']}
  };
  tutti('[data-scena="guardia"],[data-scena="orsa"]').forEach(function(s){
    var nome=s.getAttribute('data-scena'), esito=s.querySelector('.esito'), gruppo=s.querySelector('.scena-bottoni');
    tutti('button',gruppo).forEach(function(b){b.addEventListener('click',function(){
      var r=ESITI[nome][b.getAttribute('data-risposta')], pre=esito.parentNode;
      if(r[0]){var st=d.createElement('span');st.className='t t-strumento aggiunta';st.textContent=r[0];pre.insertBefore(st,esito)}
      esito.textContent=r[1];esito.setAttribute('data-esito','fatto');
      gruppo.hidden=true;
      var ancora=d.createElement('button');ancora.type='button';ancora.textContent='Di nuovo';ancora.className='ancora';
      var riga=d.createElement('div');riga.className='scena-bottoni';riga.appendChild(ancora);
      gruppo.parentNode.appendChild(riga);ancora.focus();
      ancora.addEventListener('click',function(){
        tutti('.aggiunta',pre).forEach(function(x){x.remove()});
        esito.textContent=nome==='guardia'?'La cartella resta finché non dici sì.':'Aspetto la tua risposta.';
        riga.remove();gruppo.hidden=false;gruppo.querySelector('button').focus();
      });
    })});
  });

  /* passo 5: l'indice compare riga per riga */
  tutti('[data-scena="storico"]').forEach(function(s){
    var righe=tutti('tbody tr',s), leggi=s.querySelector('.leggi');
    if(!leggi)return;
    leggi.hidden=false;
    leggi.addEventListener('click',function(){
      s.classList.add('pronto');
      righe.forEach(function(r){r.classList.remove('visto')});
      leggi.disabled=true;
      righe.forEach(function(r,i){setTimeout(function(){r.classList.add('visto');if(i===righe.length-1){leggi.disabled=false;leggi.textContent='Leggi di nuovo'}},riduci?0:450*(i+1))});
    });
  });

  /* passo 6: le forme della proposta, a schede */
  tutti('[data-scena="proposte"]').forEach(function(s){
    var schede=tutti('[role="tab"]',s);
    function scegli(t,fuoco){
      schede.forEach(function(x){var su=x===t;x.setAttribute('aria-selected',su?'true':'false');x.tabIndex=su?0:-1;d.getElementById(x.getAttribute('aria-controls')).hidden=!su});
      if(fuoco)t.focus();
    }
    schede.forEach(function(t,i){
      t.addEventListener('click',function(){scegli(t,false)});
      t.addEventListener('keydown',function(e){
        var k=e.key==='ArrowRight'?1:e.key==='ArrowLeft'?-1:0;
        if(k){e.preventDefault();scegli(schede[(i+k+schede.length)%schede.length],true)}
      });
    });
    scegli(schede[0],false);
    var cursore=s.querySelector('#catering');
    if(cursore){
      var FISSE=4800+2600+1400, BUDGET=11000;
      var valore=s.querySelector('#catering-valore'), totale=s.querySelector('#totale'), riga=s.querySelector('#budget'), esito=s.querySelector('#budget-esito');
      var aggiorna=function(){
        var c=+cursore.value, t=FISSE+c, diff=t-BUDGET;
        valore.textContent=euro(c);totale.textContent=euro(t);
        cursore.setAttribute('aria-valuetext',euro(c));
        riga.classList.toggle('dentro-budget',diff<=0);
        esito.textContent=diff>0?'fuori di '+euro(diff):diff<0?'dentro di '+euro(-diff):'in pari';
      };
      cursore.addEventListener('input',aggiorna);aggiorna();
    }
  });
})();
