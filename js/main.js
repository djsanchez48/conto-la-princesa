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
