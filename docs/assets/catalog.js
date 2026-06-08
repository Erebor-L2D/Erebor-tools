// Toggle the runs catalog between table and cards; remember the choice.
function gfSetView(v) {
  document.querySelectorAll('.gf-view').forEach(function (el) {
    el.classList.toggle('gf-hidden', el.id !== 'view-' + v);
  });
  var bt = document.getElementById('gf-btn-table');
  var bc = document.getElementById('gf-btn-cards');
  if (bt) bt.classList.toggle('active', v === 'table');
  if (bc) bc.classList.toggle('active', v === 'cards');
  try { localStorage.setItem('gf-view', v); } catch (e) {}
}
window.gfSetView = gfSetView;

document.addEventListener('DOMContentLoaded', function () {
  var saved = null;
  try { saved = localStorage.getItem('gf-view'); } catch (e) {}
  if (saved === 'cards' || saved === 'table') gfSetView(saved);
});
