// Menú móvil
(function () {
  const toggle = document.querySelector(".nav-toggle");
  const nav = document.querySelector("#nav");
  if (!toggle || !nav) return;

  toggle.addEventListener("click", function () {
    const open = nav.getAttribute("data-open") === "true";
    nav.setAttribute("data-open", String(!open));
    toggle.setAttribute("aria-expanded", String(!open));
  });

  // Cerrar al elegir un enlace
  nav.querySelectorAll("a").forEach((a) =>
    a.addEventListener("click", () => {
      nav.setAttribute("data-open", "false");
      toggle.setAttribute("aria-expanded", "false");
    })
  );
})();

// Selector de idioma: recuerda la elección manual para que el script
// de auto-detección no vuelva a redirigir en la siguiente página.
(function () {
  var link = document.querySelector(".lang-switch");
  if (!link) return;
  link.addEventListener("click", function () {
    var target = document.documentElement.lang === "en" ? "es" : "en";
    try { localStorage.setItem("lang", target); } catch (e) {}
  });
})();
