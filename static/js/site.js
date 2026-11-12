'use strict';
const toggle = document.querySelector('.menu-toggle');
const nav = document.getElementById('navigation');
function closeMenu() { if (!toggle || !nav) return; toggle.setAttribute('aria-expanded', 'false'); nav.classList.remove('is-open'); }
toggle?.addEventListener('click', () => { const open = toggle.getAttribute('aria-expanded') !== 'true'; toggle.setAttribute('aria-expanded', String(open)); nav.classList.toggle('is-open', open); });
document.addEventListener('keydown', event => { if (event.key === 'Escape' && toggle?.getAttribute('aria-expanded') === 'true') { closeMenu(); toggle.focus(); } });
document.addEventListener('click', event => { if (!event.target.closest('.header')) closeMenu(); });
window.matchMedia('(min-width: 701px)').addEventListener('change', closeMenu);
const dialog = document.getElementById('lightbox');
let origin;
document.querySelectorAll('[data-lightbox]').forEach(link => link.addEventListener('click', event => {
  if (!dialog?.showModal) return;
  event.preventDefault(); origin = link;
  const image = dialog.querySelector('img');
  image.src = link.href; image.alt = link.querySelector('img').alt;
  dialog.querySelector('p').textContent = link.dataset.caption;
  dialog.showModal(); dialog.querySelector('button').focus();
}));
dialog?.querySelector('button').addEventListener('click', () => dialog.close());
dialog?.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });
dialog?.addEventListener('close', () => origin?.focus());
const files = document.getElementById('files');
files?.addEventListener('change', () => {
  const list = Array.from(files.files);
  const invalid = list.length > 3 || list.some(file => file.size > 5 * 1024 * 1024);
  files.setCustomValidity(invalid ? 'Joignez au maximum 3 fichiers de 5 Mo chacun.' : '');
  document.querySelector('.file-status').textContent = invalid ? 'Sélection trop volumineuse : 3 fichiers de 5 Mo maximum.' : list.map(file => file.name).join(' · ');
});
const error = document.querySelector('.error-summary');
if (error?.hasAttribute('tabindex')) error.focus();
