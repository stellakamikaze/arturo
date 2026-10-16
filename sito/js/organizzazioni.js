// Lo script della pagina /organizzazioni/, fuori dall'HTML perché la CSP non ammette script inline (16/10/2026).
(function(){
  var d=document;
  /* gli strati */
  var tabs=[].slice.call(d.querySelectorAll('#schema [role="tab"]'));
  function scegli(t,fuoco){
    tabs.forEach(function(x){
      var on=x===t;
      x.setAttribute('aria-selected',on?'true':'false');
      x.tabIndex=on?0:-1;
      x.parentNode.classList.toggle('attivo',on);
      d.getElementById(x.getAttribute('aria-controls')).hidden=!on;
    });
    if(fuoco)t.focus();
  }
  tabs.forEach(function(t,i){
    t.addEventListener('click',function(){scegli(t)});
    t.addEventListener('keydown',function(e){
      var n=null;
      if(e.key==='ArrowDown'||e.key==='ArrowRight')n=tabs[(i+1)%tabs.length];
      if(e.key==='ArrowUp'||e.key==='ArrowLeft')n=tabs[(i-1+tabs.length)%tabs.length];
      if(e.key==='Home')n=tabs[0];
      if(e.key==='End')n=tabs[tabs.length-1];
      if(n){e.preventDefault();scegli(n,true)}
    });
  });
})();
