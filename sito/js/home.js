// Lo script della pagina /, fuori dall'HTML perché la CSP non ammette script inline (16/10/2026).
// Dal 16/11/2026 la home è la landing a passi: le scene stanno in js/racconto.js, qui restano il sistema
// del visitatore (per la guida d'installazione) e i bottoni Copia.
(function(){
  var d=document, root=d.documentElement;

  /* lo stato della guida d'installazione: la stessa chiave di installa/ */
  var CHIAVE='arturo-setup-2', TOTALE=5;  // la guida ha cinque tappe, come installa/
  var guida={};
  try{var s=JSON.parse(localStorage.getItem(CHIAVE)||'null');if(s&&typeof s==='object')guida=s}catch(e){}
  var os=guida.os==='win'||guida.os==='mac'?guida.os:(/Windows|Win64|Win32/i.test(navigator.userAgent||'')?'win':'mac');
  root.setAttribute('data-os',os);

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
})();
