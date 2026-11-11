/* Keep optional notes useful to the existing receipt-based enquiry receiver.
   No new network calls, tracking, storage or submission handlers. */
(() => {
  'use strict';
  const form = document.querySelector('[data-search-enquiry]');
  if (!form) return;
  const sync = () => {
    form.elements.message.value = `${form.dataset.searchEnquiry} quote request.\nProject details: ${form.elements.project_notes.value.trim() || 'Please help me confirm the drawing scope.'}`;
  };
  form.addEventListener('input', sync, true);
  form.addEventListener('submit', sync, true);
  form.addEventListener('reset', () => queueMicrotask(sync));
  sync();
})();
