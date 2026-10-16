// Lo script della pagina /installa/, fuori dall'HTML perché la CSP non ammette script inline (16/10/2026).
/* l'indice a sinistra: segue la rotta e ci porta */
(function(){
  var d=document, ol=d.getElementById('indice-passi');
  var tappe=[].slice.call(d.querySelectorAll('.tappa'));
  var voci=tappe.map(function(li,i){
    var n=i+1, item=d.createElement('li'), b=d.createElement('button');
    b.type='button';
    b.innerHTML='<b>'+n+'</b><span></span><i></i>';
    b.querySelector('span').textContent=li.querySelector('.tappa__nome').textContent;
    b.addEventListener('click',function(){
      if(!li.classList.contains('aperta'))li.querySelector('.tappa__apri').click();
      li.scrollIntoView({block:'start'});
      li.querySelector('.tappa__apri').focus({preventScroll:true});
    });
    item.appendChild(b); ol.appendChild(item); return b;
  });
  function segui(){
    d.documentElement.classList.toggle('finito',tappe.every(function(li){return li.classList.contains('fatta')}));
    tappe.forEach(function(li,i){
      var b=voci[i], f=li.classList.contains('fatta'), c=li.classList.contains('corrente');
      b.className=(f?'fatta ':'')+(c?'corrente ':'')+(li.classList.contains('aperta')?'aperta':'');
      b.querySelector('i').textContent=f?'fatto':(c?'tocca a te':'');
      if(c)b.setAttribute('aria-current','step');else b.removeAttribute('aria-current');
    });
  }
  segui();
  if(window.MutationObserver)tappe.forEach(function(li){new MutationObserver(segui).observe(li,{attributes:true,attributeFilter:['class']})});
})();
