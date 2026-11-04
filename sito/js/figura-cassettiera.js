// Figura 1: il mobile a cassetti. Al passaggio del mouse, al tocco o al fuoco di un pulsante
// si apre un cassetto e la lettura dice cosa contiene. Un cassetto aperto alla volta.
(function () {
  var fig = document.querySelector('[data-figura="cassettiera"]');
  if (!fig) return;
  var passo = (fig.getAttribute("data-passo") || "0 0").split(" ").map(Number);
  var cassetti = fig.querySelectorAll(".fg-cassetto");
  var bottoni = fig.querySelectorAll(".fg-strati button");
  var lettura = fig.querySelector("[data-lettura]");
  var aperto = null;

  function trova(lista, id) {
    for (var i = 0; i < lista.length; i++) if (lista[i].getAttribute("data-strato") === id) return lista[i];
    return null;
  }
  function apri(id) {
    if (id === aperto) return;
    aperto = id;
    for (var i = 0; i < cassetti.length; i++) {
      var c = cassetti[i], si = c.getAttribute("data-strato") === id;
      c.removeAttribute("transform");
      c.style.transform = si ? "translate(" + passo[0] + "px," + passo[1] + "px)" : "translate(0px,0px)";
      if (si) c.setAttribute("data-aperto", ""); else c.removeAttribute("data-aperto");
    }
    for (var j = 0; j < bottoni.length; j++) {
      bottoni[j].setAttribute("aria-pressed", String(bottoni[j].getAttribute("data-strato") === id));
    }
    var b = trova(bottoni, id);
    if (b && lettura) {
      lettura.textContent = "";
      var s = document.createElement("strong");
      s.textContent = b.textContent + ".";
      lettura.appendChild(s);
      lettura.appendChild(document.createTextNode(" " + b.getAttribute("data-riga")));
    }
  }
  for (var i = 0; i < cassetti.length; i++) {
    cassetti[i].addEventListener("pointerenter", function (e) { apri(e.currentTarget.getAttribute("data-strato")); });
    cassetti[i].addEventListener("click", function (e) { apri(e.currentTarget.getAttribute("data-strato")); });
  }
  for (var j = 0; j < bottoni.length; j++) {
    ["click", "focus", "pointerenter"].forEach(function (tipo) {
      bottoni[j].addEventListener(tipo, function (e) { apri(e.currentTarget.getAttribute("data-strato")); });
    });
  }
  // lo stato del markup: il primo cassetto è già aperto
  var primo = fig.querySelector(".fg-cassetto[data-aperto]");
  if (primo) {
    aperto = primo.getAttribute("data-strato");
    primo.removeAttribute("transform");
    primo.style.transform = "translate(" + passo[0] + "px," + passo[1] + "px)";
  }
})();
