// Lo script della pagina /feedback/, fuori dall'HTML perché la CSP non ammette script inline (16/10/2026).
(function(){
  var d=document, modulo=d.getElementById('modulo'), testo=d.getElementById('f-testo'), conta=d.getElementById('conta');
  var invia=d.getElementById('invia');
  var MASSIMO=120, vocale=null;

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

  /* ---------- il registratore ---------- */
  var box=d.getElementById('voce'), dice=d.getElementById('voce-dice');
  var puo=!!(navigator.mediaDevices&&navigator.mediaDevices.getUserMedia&&window.MediaRecorder);
  if(puo){
    box.hidden=false;
    var registratore=null, flusso=null, pezzi=[], inizio=0, timer=0, contesto=null, analisi=null, giro=0;
    var tempo=d.getElementById('tempo'), metro=d.getElementById('metro'), ascolto=d.getElementById('ascolto');
    var ctx=metro.getContext('2d');
    var tipi=['audio/webm;codecs=opus','audio/ogg;codecs=opus','audio/mp4','audio/webm'];
    var formato=tipi.filter(function(t){return MediaRecorder.isTypeSupported&&MediaRecorder.isTypeSupported(t)})[0]||'';

    function stato(s){box.setAttribute('data-ora',s); box.classList.toggle('voce--registra',s==='registra')}
    function scrivi(t,errore){dice.textContent=t; dice.classList.toggle('errore',!!errore)}
    function mmss(s){s=Math.floor(s);return Math.floor(s/60)+':'+String(s%60).padStart(2,'0')}

    function disegna(){
      if(!analisi) return;
      var w=metro.width, h=metro.height, dati=new Uint8Array(analisi.fftSize);
      analisi.getByteTimeDomainData(dati);
      ctx.clearRect(0,0,w,h);
      var barre=Math.floor(w/6), passo=Math.floor(dati.length/barre);
      ctx.fillStyle='#0b0d10';
      for(var i=0;i<barre;i++){
        var picco=0;
        for(var j=0;j<passo;j++){var v=Math.abs(dati[i*passo+j]-128);if(v>picco)picco=v}
        var a=Math.max(2,Math.min(h,(picco/128)*h*1.6));
        ctx.fillRect(i*6,(h-a)/2,3,a);
      }
      giro=requestAnimationFrame(disegna);
    }
    function chiudiFlusso(){
      cancelAnimationFrame(giro); clearInterval(timer);
      if(flusso){flusso.getTracks().forEach(function(t){t.stop()}); flusso=null}
      if(contesto){contesto.close(); contesto=null; analisi=null}
    }
    function avvia(){
      scrivi('Il browser ti chiede il permesso di usare il microfono.');
      navigator.mediaDevices.getUserMedia({audio:true}).then(function(s){
        flusso=s; pezzi=[];
        try{registratore=new MediaRecorder(s,formato?{mimeType:formato,audioBitsPerSecond:64000}:{audioBitsPerSecond:64000})}
        catch(e){registratore=new MediaRecorder(s)}
        registratore.ondataavailable=function(e){if(e.data&&e.data.size)pezzi.push(e.data)};
        registratore.onstop=function(){
          chiudiFlusso();
          var t=(registratore.mimeType||formato||'audio/webm');
          vocale=new Blob(pezzi,{type:t});
          if(!vocale.size){vocale=null;stato('pronto');scrivi('Non ho registrato niente: riprova.',true);return}
          ascolto.src=URL.createObjectURL(vocale);
          stato('fatto');
          scrivi('Vocale pronto, '+mmss((Date.now()-inizio)/1000)+'. Riascoltalo se vuoi: parte con «Invia».');
          d.getElementById('rifai').focus();
        };
        try{
          var AC=window.AudioContext||window.webkitAudioContext;
          if(AC){contesto=new AC(); analisi=contesto.createAnalyser(); analisi.fftSize=1024; contesto.createMediaStreamSource(s).connect(analisi)}
        }catch(e){analisi=null}
        registratore.start(1000); inizio=Date.now(); stato('registra'); disegna();
        scrivi('Sto registrando. Premi «Ferma» quando hai finito.');
        d.getElementById('ferma').focus();
        timer=setInterval(function(){
          var s=(Date.now()-inizio)/1000; tempo.firstChild.nodeValue=mmss(s)+' ';
          if(s>=MASSIMO&&registratore.state==='recording') registratore.stop();
        },250);
      }).catch(function(e){
        stato('pronto');
        var negato=e&&(e.name==='NotAllowedError'||e.name==='SecurityError');
        scrivi(negato?'Il browser non ha dato il microfono. Scrivi qui sopra: il messaggio arriva lo stesso.':'Non trovo un microfono su questo computer. Scrivi qui sopra: il messaggio arriva lo stesso.',true);
      });
    }
    d.getElementById('registra').addEventListener('click',avvia);
    d.getElementById('ferma').addEventListener('click',function(){if(registratore&&registratore.state==='recording')registratore.stop()});
    d.getElementById('rifai').addEventListener('click',function(){vocale=null;ascolto.removeAttribute('src');avvia()});
    d.getElementById('cancella').addEventListener('click',function(){
      vocale=null; ascolto.removeAttribute('src'); stato('pronto');
      scrivi('Vocale tolto. Il testo resta com\'è.'); d.getElementById('registra').focus();
    });
  }

  /* ---------- invio ---------- */
  modulo.addEventListener('submit',function(ev){
    if(!window.fetch||!window.FormData) return; // senza fetch il modulo parte come form, e torna con l'ancora
    ev.preventDefault();
    var email=d.getElementById('f-email').value.trim();
    if(!testo.value.trim()&&!vocale){mostra('errore','Scrivi qualcosa o registra un vocale, poi premi «Invia».');testo.focus();return}
    if(email&&!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)){mostra('errore','L\'email sembra incompleta: controllala, oppure lasciala vuota.');d.getElementById('f-email').focus();return}
    var dati=new FormData(modulo); dati.delete('voce');
    if(vocale){
      var est=/ogg/.test(vocale.type)?'ogg':/mp4/.test(vocale.type)?'m4a':'webm';
      dati.append('voce',vocale,'vocale.'+est);
    }
    invia.disabled=true; invia.firstChild.nodeValue='Invio in corso ';
    fetch(modulo.action,{method:'POST',body:dati,headers:{'Accept':'application/json'}}).then(function(r){
      return r.json().catch(function(){return {}}).then(function(j){return {stato:r.status,j:j}});
    }).then(function(x){
      if(x.stato===201||x.stato===202){
        mostra('inviato');
        if(window.plausible) plausible('Feedback inviato',{props:{tipo:(dati.get('tipo')||'altro'),vocale:vocale?'sì':'no'}});
      }else if(x.stato===429){mostra('troppi')}
      else if(x.stato===413){mostra('troppo-grande')}
      else{mostra('errore',x.j&&x.j.errore?('Il server dice: '+x.j.errore+'. Correggi e riprova.'):'Qualcosa non ha funzionato dalla parte del server. Riprova fra qualche minuto.')}
    }).catch(function(){
      mostra('errore','Non riesco a raggiungere il server: controlla la connessione e riprova. Quello che hai scritto è ancora qui.');
    }).then(function(){invia.disabled=false; invia.firstChild.nodeValue='Invia a Federico '});
  });
})();
