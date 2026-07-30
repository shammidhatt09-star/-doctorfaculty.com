const menu = document.querySelector('.menu-toggle');
const links = document.querySelector('.nav-links');

function closeMenu() {
  links?.classList.remove('open');
  menu?.setAttribute('aria-expanded', 'false');
  menu?.setAttribute('aria-label', 'Open menu');
  if (menu) menu.innerHTML = 'Menu <b>+</b>';
}

menu?.addEventListener('click', () => {
  const isOpen = links?.classList.toggle('open') ?? false;
  menu.setAttribute('aria-expanded', String(isOpen));
  menu.setAttribute('aria-label', isOpen ? 'Close menu' : 'Open menu');
  menu.innerHTML = isOpen ? 'Close <b>×</b>' : 'Menu <b>+</b>';
});

links?.querySelectorAll('a').forEach((link) => {
  link.addEventListener('click', closeMenu);
});

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') closeMenu();
});

window.addEventListener('resize', () => {
  if (window.innerWidth > 800) closeMenu();
});
