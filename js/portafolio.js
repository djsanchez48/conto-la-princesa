/* Filtrado del portafolio sobre tarjetas estáticas (pre-renderizadas).
   Lee ?cat=XXX de la URL para entrar ya filtrado. */
(function () {
  var filtros = document.querySelectorAll("#filters .filter-btn");
  var tarjetas = document.querySelectorAll("#grid .project-card");
  var grid = document.getElementById("grid");
  if (!filtros.length || !tarjetas.length) return;

  var cats = {};
  tarjetas.forEach(function (t) { cats[t.dataset.cat] = true; });

  var urlCat = new URLSearchParams(window.location.search).get("cat");
  var activo = urlCat && cats[urlCat] ? urlCat : "all";

  function aplicar() {
    tarjetas.forEach(function (t) {
      t.style.display = (activo === "all" || t.dataset.cat === activo) ? "" : "none";
    });
    filtros.forEach(function (b) {
      b.setAttribute("aria-pressed", b.dataset.cat === activo ? "true" : "false");
    });
  }

  filtros.forEach(function (b) {
    b.addEventListener("click", function () {
      activo = b.dataset.cat;
      aplicar();
      var url = activo === "all" ? location.pathname : location.pathname + "?cat=" + activo;
      history.replaceState(null, "", url);
    });
  });

  aplicar();
})();
