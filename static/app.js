document.addEventListener("click", function (event) {
  const dismiss = event.target.closest(".dismiss");
  if (dismiss) dismiss.parentElement.remove();
});
document.addEventListener("submit", function (event) {
  const form = event.target.closest("form[data-confirm]");
  if (form && !window.confirm(form.dataset.confirm)) event.preventDefault();
});
