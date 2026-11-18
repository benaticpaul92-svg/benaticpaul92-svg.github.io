/* Small page behaviours for the landing pages. No network calls, tracking or storage. */
(() => {
  'use strict';
  const form = document.querySelector('[data-search-enquiry]');
  if (form) {
    // Keep optional notes useful to the existing receipt-based enquiry receiver.
    const sync = () => {
      form.elements.message.value = `${form.dataset.searchEnquiry} quote request.\nProject details: ${form.elements.project_notes.value.trim() || 'Please help me confirm the drawing scope.'}`;
    };
    form.addEventListener('input', sync, true);
    form.addEventListener('submit', sync, true);
    form.addEventListener('reset', () => queueMicrotask(sync));
    sync();
    // The shared form script writes its own button and status wording. Keep the US wording.
    const words = [['Send enquiry', 'Get my quote'], ['Enquiry submitted', 'Quote request sent'], ['enquiries', 'requests'], ['Enquiries', 'Requests'], ['enquiry', 'request'], ['Enquiry', 'Request']];
    const relabel = () => {
      form.querySelectorAll('button, [data-form-status]').forEach((el) => {
        let text = el.textContent;
        for (const [from, to] of words) text = text.split(from).join(to);
        if (text !== el.textContent) el.textContent = text;
      });
    };
    new MutationObserver(relabel).observe(form, { childList: true, subtree: true, characterData: true });
    document.addEventListener('DOMContentLoaded', relabel);
    relabel();
  }
  // State picker: go to the chosen state page.
  const jump = document.querySelector('[data-state-jump]');
  if (jump) jump.addEventListener('change', () => { if (jump.value) window.location.href = jump.value; });
  // Lists that are folded on phones are open on wide screens.
  if (window.matchMedia('(min-width: 761px)').matches) {
    document.querySelectorAll('details[data-open-wide]').forEach((d) => { d.open = true; });
    document.documentElement.classList.add('wide-open');
  }
  // A link to a folded block opens it first.
  const openTarget = (hash) => {
    if (!hash || hash.length < 2) return;
    let target = null;
    try { target = document.getElementById(decodeURIComponent(hash.slice(1))); } catch (e) { return; }
    const fold = target && target.closest('details');
    if (fold && !fold.open) fold.open = true;
  };
  document.addEventListener('click', (event) => {
    const link = event.target.closest && event.target.closest('a[href^="#"]');
    if (link) openTarget(link.getAttribute('href'));
  });
  window.addEventListener('hashchange', () => openTarget(window.location.hash));
  openTarget(window.location.hash);
  // Phone quote bar: show it only while the quote form is off screen.
  const bar = document.querySelector('[data-sticky-cta]');
  const panel = document.getElementById('contact');
  if (bar && panel && 'IntersectionObserver' in window) {
    new IntersectionObserver((entries) => {
      bar.hidden = entries[0].isIntersecting;
    }, { rootMargin: '0px 0px -10% 0px' }).observe(panel);
  }
})();
