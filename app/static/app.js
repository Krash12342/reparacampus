// Mejoras de usabilidad (la validacion real ocurre en el servidor).
document.querySelectorAll("textarea[maxlength]").forEach(function (area) {
  var out = document.getElementById(area.id + "-count");
  if (!out) return;
  var update = function () { out.textContent = area.value.trim().length + " / " + area.maxLength; };
  area.addEventListener("input", update);
  update();
});
document.querySelectorAll("form[data-confirm]").forEach(function (form) {
  form.addEventListener("submit", function (e) {
    if (!window.confirm(form.dataset.confirm)) e.preventDefault();
  });
});
