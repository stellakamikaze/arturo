// Lo script della pagina /, fuori dall'HTML perché la CSP non ammette script inline (16/10/2026).
(function(){
  var d=document, root=d.documentElement;
  var riduci=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* lo stato della guida d'installazione: la stessa chiave di installa/, così la guida riparte da qui */
  var CHIAVE='arturo-setup-1';
  function leggi(){try{var s=JSON.parse(localStorage.getItem(CHIAVE)||'null');return s&&typeof s==='object'?s:{}}catch(e){return {}}}
  function scrivi(s){try{localStorage.setItem(CHIAVE,JSON.stringify(s))}catch(e){}}
  var guida=leggi();
  var os=guida.os==='win'||guida.os==='mac'?guida.os:(/Windows|Win64|Win32/i.test(navigator.userAgent||'')?'win':'mac');
  root.setAttribute('data-os',os);

  /* le schede della finestra */
  var schede=[].slice.call(d.querySelectorAll('.scheda'));
  var nota=d.getElementById('palco-nota');
  var note={casi:nota?nota.textContent:'',installa:'I primi quattro passi. Gli altri sei sono nella guida.'};
  function scegli(b,fuoco){
    schede.forEach(function(x){
      var su=x===b;
      x.setAttribute('aria-selected',su?'true':'false');
      x.tabIndex=su?0:-1;
      d.getElementById(x.getAttribute('aria-controls')).hidden=!su;
    });
    if(fuoco)b.focus();
    var installa=b.id==='scheda-installa';
    if(nota)nota.textContent=installa?note.installa:note.casi;
    if(installa)ferma();else riparti();
  }
  schede.forEach(function(b,i){
    b.addEventListener('click',function(){scegli(b,false)});
    b.addEventListener('keydown',function(e){
      var j=e.key==='ArrowRight'?i+1:e.key==='ArrowLeft'?i-1:null;
      if(j===null)return;
      e.preventDefault(); scegli(schede[(j+schede.length)%schede.length],true);
    });
  });
  if(location.hash==='#installa'){var bi=d.getElementById('scheda-installa');if(bi)scegli(bi,false)}

  /* la galleria dei casi */
  var casi=[].slice.call(d.querySelectorAll('.caso'));
  var puntini=d.getElementById('puntini');
  var ora=0, timer=null, fermo=false;
  /* la pausa visibile: senza movimento la galleria non gira, e il pulsante resta nascosto */
  var pausa=d.getElementById('galleria-pausa');
  function segnaPausa(){if(!pausa)return;pausa.classList.toggle('ferma',fermo);pausa.setAttribute('aria-label',fermo?'Riprendi la galleria':'Ferma la galleria')}
  function blocca(){fermo=true;ferma();segnaPausa()}
  if(pausa&&!riduci){
    pausa.hidden=false;
    pausa.addEventListener('click',function(){if(fermo){fermo=false;segnaPausa();riparti()}else blocca()});
  }
  casi.forEach(function(c,i){
    var li=d.createElement('li'), b=d.createElement('button');
    b.type='button'; b.textContent=c.getAttribute('data-nome');
    b.addEventListener('click',function(){mostra(i);blocca()});
    li.appendChild(b); puntini.appendChild(li);
  });
  var bottoni=[].slice.call(puntini.querySelectorAll('button'));
  function mostra(i){
    ora=(i+casi.length)%casi.length;
    casi.forEach(function(c,k){c.hidden=k!==ora});
    bottoni.forEach(function(b,k){if(k===ora)b.setAttribute('aria-current','true');else b.removeAttribute('aria-current')});
    var b=bottoni[ora];if(b&&puntini.scrollWidth>puntini.clientWidth)puntini.scrollLeft=b.offsetLeft-puntini.offsetLeft-(puntini.clientWidth-b.offsetWidth)/2;
  }
  function ferma(){if(timer){clearInterval(timer);timer=null}}
  function riparti(){ferma();if(!riduci&&!fermo)timer=setInterval(function(){mostra(ora+1)},7000)}
  d.getElementById('caso-prima').addEventListener('click',function(){mostra(ora-1);blocca()});
  d.getElementById('caso-dopo').addEventListener('click',function(){mostra(ora+1);blocca()});
  var palco=d.getElementById('sessione');
  palco.addEventListener('mouseenter',ferma);
  palco.addEventListener('mouseleave',function(){if(!d.getElementById('vista-casi').hidden)riparti()});
  palco.addEventListener('focusin',ferma);
  d.addEventListener('visibilitychange',function(){if(d.hidden)ferma();else if(!d.getElementById('vista-casi').hidden)riparti()});
  mostra(0); riparti();

  /* le carte d'installazione */
  var carte=[].slice.call(d.querySelectorAll('.carta'));
  var passo=d.getElementById('carte-passo');
  var prima=d.getElementById('carta-prima'), dopo=d.getElementById('carta-dopo');
  var c=0;
  function carta(i){
    c=Math.max(0,Math.min(carte.length-1,i));
    carte.forEach(function(x,k){x.hidden=k!==c});
    passo.textContent='Passo '+(c+1)+' di '+carte.length;
    prima.disabled=c===0;
    dopo.hidden=c===carte.length-1;
  }
  function segna(n){
    var s=leggi(); s.os=os;
    var f=Array.isArray(s.fatte)?s.fatte:[];
    for(var k=1;k<=n;k++)if(f.indexOf(k)<0)f.push(k);
    s.fatte=f.sort(function(a,b){return a-b});
    if(!(s.ultima>=n))s.ultima=n;
    s.aperta=n+1;
    if(!s.campi)s.campi={};
    scrivi(s);
  }
  prima.addEventListener('click',function(){carta(c-1)});
  dopo.addEventListener('click',function(){segna(c+1);carta(c+1);if(dopo.hidden)carte[c].querySelector('a').focus();else dopo.focus()});
  [].forEach.call(d.querySelectorAll('.mini-sistema button'),function(b){
    b.setAttribute('aria-pressed',b.getAttribute('data-os')===os?'true':'false');
    b.addEventListener('click',function(){
      os=b.getAttribute('data-os'); root.setAttribute('data-os',os);
      [].forEach.call(d.querySelectorAll('.mini-sistema button'),function(x){x.setAttribute('aria-pressed',x===b?'true':'false')});
      var s=leggi(); s.os=os; scrivi(s);
    });
  });
  carta(0);



  /* la scena: la stessa richiesta in chat e in Claude Code */
  var scena=d.getElementById('scena');
  if(scena){
    var righe=[].slice.call(scena.querySelectorAll('.scena__pre .t'));
    var MAX=righe.reduce(function(m,r){return Math.max(m,+r.getAttribute('data-passo'))},0);
    var stato=d.getElementById('scena-stato'), salta=d.getElementById('scena-salta'), ancora=d.getElementById('scena-ancora');
    var testi=righe.map(function(r){return r.classList.contains('t-tu')?r.textContent:null});
    var giro=0;
    function effetti(n){
      [].forEach.call(scena.querySelectorAll('[data-tocca]'),function(f){var su=+f.getAttribute('data-tocca')<=n;f.classList.toggle(f.getAttribute('data-modo'),su)});
      [].forEach.call(scena.querySelectorAll('.da-incollare [data-passo],.da-incollare__poi'),function(li){li.classList.toggle('fatto',+li.getAttribute('data-passo')<=n)});
    }
    function fine(){
      giro++; scena.classList.remove('gira');
      righe.forEach(function(r,k){r.classList.add('detta');if(testi[k]!==null)r.textContent=testi[k]});
      effetti(MAX); stato.textContent='Sessione completa'; salta.hidden=true; ancora.hidden=false;
    }
    function parti(){
      var mio=++giro;
      scena.classList.add('gira'); salta.hidden=false; ancora.hidden=true;
      righe.forEach(function(r){r.classList.remove('detta')}); effetti(-1);
      var k=0;
      function passo(){
        if(mio!==giro)return;
        if(k>=righe.length){fine();return}
        var r=righe[k], n=+r.getAttribute('data-passo'), tu=testi[k]!==null;
        stato.textContent='Passo '+(n+1)+' di '+(MAX+1);
        r.classList.add('detta'); effetti(n);
        if(tu){
          var t=testi[k], c=0; r.textContent='';
          (function batti(){if(mio!==giro)return;r.textContent=t.slice(0,++c);if(c<t.length)setTimeout(batti,16);else{k++;setTimeout(passo,450)}})();
        }else{
          k++; setTimeout(passo,r.classList.contains('t-cc')||r.classList.contains('t-guardia')?1500:850);
        }
      }
      setTimeout(passo,300);
    }
    salta.addEventListener('click',function(){fine();ancora.focus()});
    ancora.addEventListener('click',function(){parti()});
    /* il markup porta già lo stato finito (class "fatto", "letto", "nuovo"): senza script la scena è completa.
       parti() lo azzera con effetti(-1) quando la sessione comincia. */
    effetti(MAX); salta.hidden=true; ancora.hidden=false;
    if(!riduci&&'IntersectionObserver' in window){
      var visto=new IntersectionObserver(function(e){if(e[0].isIntersecting){visto.disconnect();parti()}},{threshold:.35});
      visto.observe(scena.querySelector('.scena__term'));
    }
  }

  /* copia dei comandi */
  [].forEach.call(d.querySelectorAll('[data-copia]'),function(b){
    b.addEventListener('click',function(){
      var pre=d.getElementById(b.getAttribute('data-copia')), testo=pre.textContent;
      function esito(ok){
        b.classList.toggle('copiato',ok);
        b.textContent=ok?'Copiato':'Seleziona';
        setTimeout(function(){b.classList.remove('copiato');b.textContent='Copia'},2200);
      }
      if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(testo).then(function(){esito(true)},function(){esito(false)})}
      else{try{var r=d.createRange();r.selectNodeContents(pre);var sel=getSelection();sel.removeAllRanges();sel.addRange(r);esito(d.execCommand('copy'))}catch(err){esito(false)}}
    });
  });

  /* gli articoli: l'elenco nella pagina vale finché l'API di Ghost non risponde */
  var lista=d.getElementById('articoli');
  if(lista&&window.fetch){
    var MESI=['gennaio','febbraio','marzo','aprile','maggio','giugno','luglio','agosto','settembre','ottobre','novembre','dicembre'];
    var url='https://stellakamikaze.org/ghost/api/content/posts/?key=56e828183ad14d6cc5739cc75d&filter=tag:'+lista.getAttribute('data-tag')+'&limit=4&fields=title,url,published_at';
    var ctl=window.AbortController?new AbortController():null;
    if(ctl)setTimeout(function(){ctl.abort()},6000);
    fetch(url,ctl?{signal:ctl.signal}:{}).then(function(r){return r.ok?r.json():null}).then(function(j){
      if(!j||!j.posts||j.posts.length<4)return;
      var nuovi=d.createDocumentFragment();
      j.posts.forEach(function(p){
        if(!/^https:\/\/stellakamikaze\.org\//.test(p.url))return;
        var giorno=new Date(p.published_at);
        var li=d.createElement('li'), a=d.createElement('a'), t=d.createElement('time'), s=d.createElement('strong');
        a.href=p.url;
        t.dateTime=p.published_at.slice(0,10);
        t.textContent=giorno.getDate()+' '+MESI[giorno.getMonth()]+' '+giorno.getFullYear();
        s.textContent=p.title;
        a.appendChild(t);a.appendChild(s);li.appendChild(a);nuovi.appendChild(li);
      });
      if(nuovi.childNodes.length===4){lista.textContent='';lista.appendChild(nuovi)}
    }).catch(function(){});
  }
})();
