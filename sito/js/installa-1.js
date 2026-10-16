// Lo script della pagina /installa/, fuori dall'HTML perché la CSP non ammette script inline (16/10/2026).
(function(){
  var d=document, root=d.documentElement;
  root.classList.add('js');
  var CHIAVE='arturo-setup-1', TOTALE=10;
  var attesa=null;
  var BASE='~/Documents/ClaudeCode';
  var riduci=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- stato, solo in questo browser ---------- */
  var stato={os:null,fatte:[],aperta:1,ultima:0,campi:{}};
  try{
    var letto=JSON.parse(localStorage.getItem(CHIAVE)||'null');
    if(letto&&typeof letto==='object'){
      if(letto.os==='mac'||letto.os==='win')stato.os=letto.os;
      if(Array.isArray(letto.fatte))stato.fatte=letto.fatte.filter(function(n){return n>=1&&n<=TOTALE});
      if(letto.aperta>=0&&letto.aperta<=TOTALE)stato.aperta=letto.aperta;
      if(letto.ultima>=0&&letto.ultima<=TOTALE)stato.ultima=letto.ultima;
      if(letto.campi&&typeof letto.campi==='object')stato.campi=letto.campi;
    }
  }catch(e){}
  function salva(){try{localStorage.setItem(CHIAVE,JSON.stringify(stato))}catch(e){}}
  var riconosciuto=!stato.os;
  if(!stato.os)stato.os=/Windows|Win64|Win32/i.test(navigator.userAgent||'')?'win':'mac';

  /* ---------- sistema ---------- */
  var nota=d.getElementById('os-nota');
  function sistema(os,annuncia){
    stato.os=os; root.setAttribute('data-os',os);
    d.getElementById(os==='win'?'os-win':'os-mac').checked=true;
    componi();
    if(annuncia)annunci('Comandi per '+(os==='win'?'Windows':'macOS'));
  }
  if(!riconosciuto&&nota)nota.textContent='Scelto da te. Cambialo quando vuoi.';
  [].forEach.call(d.querySelectorAll('input[name="os"]'),function(r){
    r.addEventListener('change',function(){sistema(r.value,true);if(nota)nota.textContent='Scelto da te. Cambialo quando vuoi.';salva()});
  });

  /* ---------- annunci per chi usa un lettore di schermo ---------- */
  var annuncio=d.getElementById('annuncio');
  function annunci(t){annuncio.textContent='';setTimeout(function(){annuncio.textContent=t},60)}

  /* ---------- la rotta ---------- */
  var tappe=[].slice.call(d.querySelectorAll('.tappa'));
  function tappa(n){return tappe[n-1]}
  function nome(n){return tappa(n).querySelector('.tappa__nome').textContent}
  // la prima tappa da fare dopo k; se dopo non ce ne sono, la prima rimasta indietro
  function prossimaDopo(k){
    for(var i=k+1;i<=TOTALE;i++){if(stato.fatte.indexOf(i)<0)return i}
    for(var j=1;j<=k;j++){if(stato.fatte.indexOf(j)<0)return j}
    return 0;
  }
  function prossima(){return prossimaDopo(stato.ultima||0)}
  function disegna(){
    var cur=prossima();
    tappe.forEach(function(li,i){
      var n=i+1, aperta=n===stato.aperta;
      li.classList.toggle('fatta',stato.fatte.indexOf(n)>=0);
      li.classList.toggle('corrente',n===cur);
      li.classList.toggle('aperta',aperta);
      li.querySelector('.tappa__apri').setAttribute('aria-expanded',aperta?'true':'false');
    });
    var punto=d.getElementById('punto');
    var fatte=stato.fatte.length;
    punto.firstChild.nodeValue=cur?('Passo '+cur+' di '+TOTALE):'Tutti i passi fatti';
    punto.lastChild.textContent=fatte===0?'circa un\'ora in tutto':(fatte===1?'uno fatto':fatte+' fatti');
    var qualcosa=fatte>0||Object.keys(stato.campi).some(function(k){var v=stato.campi[k];return typeof v==='string'&&v.trim()!==''});
    if(!attesa)d.getElementById('ricomincia').hidden=!qualcosa;
  }
  function apri(n,fuoco){
    stato.aperta=n; disegna(); salva();
    var li=tappa(n);
    if(fuoco){
      var bt=li.querySelector('.tappa__apri');
      setTimeout(function(){
        bt.focus({preventScroll:true});
        li.scrollIntoView({behavior:riduci?'auto':'smooth',block:'start'});
      },riduci?0:320);
    }
  }
  tappe.forEach(function(li,i){
    var n=i+1;
    li.querySelector('.tappa__apri').addEventListener('click',function(){
      if(stato.aperta===n){stato.aperta=0;disegna();salva()}else{apri(n,false)}
    });
  });
  [].forEach.call(d.querySelectorAll('[data-fatta]'),function(b){
    b.addEventListener('click',function(){
      var n=+b.getAttribute('data-fatta');
      if(stato.fatte.indexOf(n)<0)stato.fatte.push(n);
      stato.ultima=n;
      var dopo=prossima();
      if(dopo){apri(dopo,true);annunci('Passo '+n+' fatto. Passo '+dopo+': '+nome(dopo))}
      else{
        stato.aperta=0;disegna();salva();annunci('Tutti i passi fatti. Arturo è acceso.');
        var t=d.getElementById('traguardo');
        setTimeout(function(){t.focus({preventScroll:true});t.scrollIntoView({behavior:riduci?'auto':'smooth',block:'center'})},riduci?0:320);
      }
    });
  });

  var ric=d.getElementById('ricomincia');
  ric.addEventListener('click',function(){
    if(!attesa){
      ric.textContent='Sicuro? Clicca di nuovo per cancellare tutto';
      attesa=setTimeout(function(){ric.textContent='Ricomincia da capo';attesa=null},4000);
      return;
    }
    clearTimeout(attesa);attesa=null;ric.textContent='Ricomincia da capo';
    var os=stato.os; stato={os:os,fatte:[],aperta:1,ultima:0,campi:{}};
    [].forEach.call(d.querySelectorAll('[data-campo]'),function(el){
      if(el.type==='checkbox')el.checked=el.defaultChecked;
      else if(el.type==='radio')el.checked=el.defaultChecked;
      else el.value='';
    });
    d.getElementById('f-lingua').value='italian';
    salva();componi();apri(1,true);annunci('Ricominciato dal passo 1');
  });

  /* ---------- i campi ---------- */
  var campi=[].slice.call(d.querySelectorAll('.foglio input:not([name="os"]), .foglio textarea, .foglio select'));
  campi.forEach(function(el){
    el.setAttribute('data-campo','');
    var v=stato.campi[el.name];
    if(el.type==='checkbox'){if(typeof v==='boolean')el.checked=v}
    else if(el.type==='radio'){if(typeof v==='string')el.checked=el.value===v}
    else if(typeof v==='string')el.value=v;
    el.addEventListener(el.tagName==='SELECT'||el.type==='checkbox'||el.type==='radio'?'change':'input',function(){
      if(el.type==='checkbox')stato.campi[el.name]=el.checked;
      else if(el.type==='radio'){if(el.checked)stato.campi[el.name]=el.value}
      else stato.campi[el.name]=el.value;
      if(el.name==='nome'){var chi=d.getElementById('f-chi');if(!stato.campi.chiToccato){chi.value=el.value;stato.campi.chi=el.value}}
      if(el.name==='chi')stato.campi.chiToccato=true;
      salva();componi();disegna();
    });
  });
  function val(nome){
    var el=d.querySelector('.foglio [name="'+nome+'"]'+(d.querySelector('.foglio input[type="radio"][name="'+nome+'"]')?':checked':''));
    if(!el)return '';
    if(el.type==='checkbox')return el.checked;
    return (el.value||'').trim();
  }

  /* ---------- comporre i comandi ---------- */
  // Tra apici singoli la shell non interpreta niente: un apice nel testo diventa '\''
  function q(s){return "'"+String(s).replace(/'/g,"'\\''")+"'"}
  function cartellaShell(p){
    if(p==='~')return '"$HOME"';
    if(p.indexOf('~/')===0)return '"$HOME"'+q(p.slice(1));
    return q(p);
  }
  function blocco(id,testo,pronto,motivo){
    var pre=d.getElementById(id), box=pre.parentNode, bt=box.querySelector('button');
    pre.textContent=testo;
    box.classList.toggle('vuoto',!pronto);
    bt.disabled=!pronto;
    bt.setAttribute('aria-label',pronto?'Copia':'Da completare: '+motivo);
  }

  function scelte(){
    var nome=val('nome'), email=val('email'), cartella=val('cartella')||BASE, lingua=val('lingua')||'italian', alias=val('alias');
    var manca=[];
    if(!nome)manca.push('il nome');
    if(!email)manca.push("l'email");
    var r=[];
    r.push('git -C "$HOME/.claude" config user.name '+q(nome||'Il tuo nome')+' && git -C "$HOME/.claude" config user.email '+q(email||'la-tua@email')+' && echo "Fatto: la firma di Git per Arturo"');
    r.push('chmod +x "$HOME/.claude/hooks/"*.sh "$HOME/.claude/hooks/"*.py 2>/dev/null; echo "Fatto: i permessi delle guardie"');
    r.push('mkdir -p '+cartellaShell(cartella)+' && echo "Fatto: la cartella dei progetti"');
    var cambi=[];
    if(cartella!==BASE)cambi.push('("\\"PROJECTS_BASE\\": \\"~/Documents/ClaudeCode\\"", "\\"PROJECTS_BASE\\": " + json.dumps('+JSON.stringify(cartella)+', ensure_ascii=False))');
    if(lingua!=='italian')cambi.push('("\\"language\\": \\"italian\\"", "\\"language\\": " + json.dumps('+JSON.stringify(lingua)+', ensure_ascii=False))');
    if(cambi.length){
      r.push(
        "python3 - <<'ARTURO'\n"+
        'import json, pathlib\n'+
        'p = pathlib.Path.home() / ".claude" / "settings.json"\n'+
        'testo = p.read_bytes().decode("utf-8")\n'+
        'for vecchio, nuovo in ['+cambi.join(', ')+']:\n'+
        '    if vecchio in testo:\n'+
        '        testo = testo.replace(vecchio, nuovo, 1)\n'+
        '    elif nuovo not in testo:\n'+
        '        print("Non trovo " + vecchio + " in settings.json: al passo 6 scrivi /setup in Claude Code e la sistemate insieme.")\n'+
        'json.loads(testo)\n'+
        'p.write_bytes(testo.encode("utf-8"))\n'+
        'print("Fatto: le impostazioni")\n'+
        'ARTURO'
      );
    }
    if(alias){
      var rc=stato.os==='win'?'.bashrc':'.zshrc';
      r.push('if [ -f "$HOME/.claude/bin/arturo" ]; then grep -qs "alias arturo=" "$HOME/'+rc+'" || printf \'%s\\n\' "alias arturo=\'python3 \\"\\$HOME/.claude/bin/arturo\\"\'" >> "$HOME/'+rc+'"; echo "Fatto: il comando arturo, da una finestra nuova del terminale"; else echo "Questa versione di Arturo non ha ancora il comando arturo"; fi');
    }
    r.push('echo "Scelte salvate."');
    blocco('cmd-scelte',r.join('\n'),manca.length===0,'manca '+manca.join(' e '));
    d.getElementById('scelte-manca').textContent=manca.length?('Per copiare il blocco manca '+manca.join(' e ')+'.'):'';
  }

  var CONSIGLI={
    'r-azioni':"Le azioni tecniche le esegui tu: comandi, script, riavvii, verifiche. Chiedimi solo ciò che solo una persona può fare: password che conosco solo io, codici 2FA, pagamenti, invii a terzi, decisioni. Se un permesso ti blocca, non passarmi il comando: cerca un'altra via o chiedimi di allargare il permesso.",
    'r-brief':"Prima di ogni richiesta di lavoro riscrivi la mia richiesta come la eseguirai (il prompt), poi mostra un brief di massimo 8 righe: obiettivo, output, vincoli, fatto quando, assunzioni, da chiarire. Poi procedi.",
    'r-forma':"Frasi corte: 22 parole per un'istruzione, 28 per una descrizione. Voce attiva, niente gerundio né condizionale, una parola per concetto.",
    'r-passo':"A lavoro finito l'ultima riga è «Prossimo passo:» con una sola azione e chi la fa, oppure «Niente da fare per te».",
    'r-visivo':"Un risultato visivo o in un'app esterna (documento, slide, grafica, pagina) è fatto solo quando l'hai aperto come lo vedrò io: dammi il link e lo screenshot che hai guardato."
  };
  function claudemd(){
    var chi=val('chi'), mestiere=val('mestiere'), programmi=val('programmi'), tono=val('tono'), regole=val('regole');
    var lingua={italian:'italiano',english:'inglese',spanish:'spagnolo',french:'francese',german:'tedesco'}[val('lingua')||'italian'];
    var p=[];
    p.push('Scrivi il mio CLAUDE.md personale in ~/.claude/CLAUDE.md con le informazioni qui sotto. Tienilo corto e pratico. Prima mostrami la bozza e aspetta il mio sì. Se il file esiste già, mostrami cosa cambieresti e non sovrascriverlo.');
    p.push('');
    p.push('Chi sono: '+(chi||'il mio nome')+(mestiere?', '+mestiere:'')+'. '+({no:'Non programmo.',poco:'Programmo un po\'.',si:'Programmo.'}[programmi]||''));
    p.push('Risposte: '+(tono==='spiegate'?'spiegate passo per passo':'corte e dirette')+', in '+lingua+', con gli accenti giusti.');
    p.push('Computer: '+(stato.os==='win'?'Windows, con Git Bash':'macOS')+'.');
    var mie=regole.split('\n').map(function(s){return s.trim()}).filter(Boolean);
    if(mie.length){p.push('');p.push('Regole mie:');mie.forEach(function(s){p.push('- '+s)})}
    var sc=Object.keys(CONSIGLI).filter(function(k){return val(k)});
    if(sc.length){p.push('');p.push('Regole consigliate da includere:');sc.forEach(function(k){p.push('- '+CONSIGLI[k])})}
    blocco('cmd-claudemd',p.join('\n'),!!chi,'manca il nome');
  }

  function facoltative(){
    var host=val('host');
    blocco('cmd-host',host?('Aggiungi '+host+' agli host interni fidati di Arturo, nel file ~/.claude/hooks/hosts-interni.local, una voce per riga. Mostrami il file prima di scriverlo.'):'Scrivi il nome del server qui sopra.',!!host,'manca il nome del server');
  }

  function componi(){scelte();claudemd();facoltative()}

  /* ---------- copia ---------- */
  [].forEach.call(d.querySelectorAll('[data-copia]'),function(b){
    b.addEventListener('click',function(){
      if(b.disabled)return;
      var pre=d.getElementById(b.getAttribute('data-copia')), testo=pre.textContent;
      function esito(ok){
        b.classList.remove('copiato','errore'); b.classList.add(ok?'copiato':'errore');
        b.textContent=ok?'Copiato':'Seleziona';
        annunci(ok?'Copiato':'Copia non riuscita: seleziona il testo a mano');
        setTimeout(function(){b.classList.remove('copiato','errore');b.textContent='Copia'},2200);
      }
      if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(testo).then(function(){esito(true)},function(){esito(false)})}
      else{try{var r=d.createRange();r.selectNodeContents(pre);var s=getSelection();s.removeAllRanges();s.addRange(r);esito(d.execCommand('copy'))}catch(err){esito(false)}}
    });
  });

  /* ---------- avvio ---------- */
  sistema(stato.os,false);
  var dal=/^#tappa-(\d+)$/.exec(location.hash);
  if(dal&&+dal[1]>=1&&+dal[1]<=TOTALE)stato.aperta=+dal[1];
  else if(stato.aperta&&stato.fatte.indexOf(stato.aperta)>=0&&prossima())stato.aperta=prossima();
  disegna();

  /* ---------- la bandierina: dove ti eri fermato ---------- */
  (function(){
    var cur=prossima();
    if(stato.fatte.length>0&&cur){
      var li=tappa(cur), b=d.createElement('p');
      b.className='bandierina';
      b.innerHTML='<svg viewBox="0 0 14 16" fill="none" aria-hidden="true"><path d="M2 15V1.5M2 2h9l-2.2 3L11 8H2" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round" stroke-linecap="round"/></svg>Ti eri fermato qui';
      li.querySelector('.tappa__corpo').insertBefore(b,li.querySelector('.tappa__testa'));
      var via=d.getElementById('riprendi');
      if(via){via.hidden=false;via.href='#tappa-'+cur;via.querySelector('span').textContent='Riprendi dal passo '+cur;
        via.addEventListener('click',function(){apri(cur,true)});}
    }
  })();

  /* ---------- la testina: il computer scelto e il passo ---------- */
  [].forEach.call(d.querySelectorAll('[data-scegli-os]'),function(b){
    b.addEventListener('click',function(){
      var r=d.getElementById(b.getAttribute('data-scegli-os')==='win'?'os-win':'os-mac');
      r.checked=true; r.dispatchEvent(new Event('change'));
    });
  });
  var punto=d.getElementById('punto'), eco=d.getElementById('testina-punto');
  function ripeti(){if(eco)eco.textContent=punto.firstChild.nodeValue}
  ripeti();
  if(window.MutationObserver)new MutationObserver(ripeti).observe(punto,{childList:true,characterData:true,subtree:true});
})();
