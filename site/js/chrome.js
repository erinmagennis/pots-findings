/* chrome.js: the one phone-menu toggle for the site header, on every page (home included).
   It imports nothing, so it runs before any page data loads. ui.js mount() calls wireChrome() too; it only wires once. */
let wired = false;
export function wireChrome(){
  if(wired) return;
  const navToggle = document.getElementById('mobileNavToggle');
  const primaryNav = document.getElementById('primaryNav');
  if(!navToggle) return;
  wired = true;
  navToggle.addEventListener('click', () => {
    const open = navToggle.getAttribute('aria-expanded') === 'true';
    navToggle.setAttribute('aria-expanded', String(!open));
    primaryNav?.toggleAttribute('data-open', !open);
  });
}
wireChrome();
