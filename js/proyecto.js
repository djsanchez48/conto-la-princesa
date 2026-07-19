/* Visor (lightbox) de la galería en la página de cada mural. */
(function () {
  var items = Array.prototype.slice.call(document.querySelectorAll(".gallery .gal-item"));
  var lb = document.getElementById("lightbox");
  if (!items.length || !lb) return;

  var img = lb.querySelector(".lightbox__img");
  var counter = lb.querySelector(".lightbox__counter");
  var fulls = items.map(function (it) { return it.dataset.full; });
  var i = 0;

  function pintar() {
    img.src = fulls[i];
    img.alt = "Foto " + (i + 1) + " de " + fulls.length;
    counter.textContent = (i + 1) + " / " + fulls.length;
    var multi = fulls.length > 1;
    counter.style.display = multi ? "block" : "none";
    lb.querySelector(".lightbox__prev").style.display = multi ? "flex" : "none";
    lb.querySelector(".lightbox__next").style.display = multi ? "flex" : "none";
  }
  function abrir(n) { i = n; pintar(); lb.setAttribute("data-open", "true"); document.body.style.overflow = "hidden"; }
  function cerrar() { lb.setAttribute("data-open", "false"); document.body.style.overflow = ""; }
  function mover(d) { i = (i + d + fulls.length) % fulls.length; pintar(); }

  items.forEach(function (it, n) { it.addEventListener("click", function () { abrir(n); }); });
  lb.querySelector(".lightbox__close").addEventListener("click", cerrar);
  lb.querySelector(".lightbox__prev").addEventListener("click", function () { mover(-1); });
  lb.querySelector(".lightbox__next").addEventListener("click", function () { mover(1); });
  lb.addEventListener("click", function (e) { if (e.target === lb) cerrar(); });
  document.addEventListener("keydown", function (e) {
    if (lb.getAttribute("data-open") !== "true") return;
    if (e.key === "Escape") cerrar();
    if (e.key === "ArrowLeft") mover(-1);
    if (e.key === "ArrowRight") mover(1);
  });
})();
