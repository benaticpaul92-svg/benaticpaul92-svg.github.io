/* One editable brief feeds the review panel, download and existing enquiry receiver.
   Choices live only in the DOM; no contact or project information is stored remotely. */
(() => {
  'use strict';
  const start = document.querySelector('.project-start');
  const form = document.querySelector('[data-enquiry-form]');
  if (!start || !form) return;
  const state = document.getElementById('project-state');
  const notes = form.elements.namedItem('project_notes');
  const message = form.elements.namedItem('message');
  const city = form.elements.namedItem('location');
  let lastLocation = '';
  function selection() {
    return {
      need: start.querySelector('input[name="project_need"]:checked').value,
      state: state.value || 'To be confirmed',
      scopes: [...document.querySelectorAll('[data-scope-option]:checked')].map(input => input.value)
    };
  }
  function syncBrief() {
    const chosen = selection();
    message.value = `Project need: ${chosen.need}\nProject state: ${chosen.state}\nRequested scope: ${chosen.scopes.length ? chosen.scopes.join('; ') : 'Please help confirm the scope'}\n\nProject notes:\n${notes.value.trim() || 'No additional notes yet.'}`;
    document.querySelector('[data-review-need]').textContent = chosen.need;
    document.querySelector('[data-review-state]').textContent = city.value || chosen.state;
    const list = document.querySelector('[data-review-scope]');
    list.replaceChildren(...(chosen.scopes.length ? chosen.scopes : ['Help me confirm the scope']).map(text => {
      const item = document.createElement('li'); item.textContent = text; return item;
    }));
    const count = chosen.scopes.length;
    document.querySelector('[data-scope-count]').textContent = count ? `${count} ${count === 1 ? 'service' : 'services'} selected.` : 'Select any services you need.';
  }
  function notifyForm() {
    // Capture listener updates the payload before the existing draft fallback reads it.
    form.dispatchEvent(new Event('input', {bubbles:true}));
  }
  function updateState() {
    if (!city.value || city.value === lastLocation) {
      city.value = state.value;
      lastLocation = state.value;
    }
    notifyForm();
  }
  function continueBrief() {
    notifyForm();
    document.getElementById('contact').scrollIntoView({block:'start'});
    document.getElementById('contact-heading').focus({preventScroll:true});
  }
  form.addEventListener('input', syncBrief, true);
  form.addEventListener('submit', syncBrief, true);
  form.addEventListener('reset', () => queueMicrotask(syncBrief));
  start.querySelector('[data-start-project]').addEventListener('click', () => {
    notifyForm();
    document.getElementById('services').scrollIntoView({block:'start'});
    document.getElementById('services-heading').focus({preventScroll:true});
  });
  document.querySelector('[data-scope-continue]').addEventListener('click', continueBrief);
  state.addEventListener('change', updateState);
  start.querySelectorAll('[name="project_need"]').forEach(input => input.addEventListener('change', notifyForm));
  document.querySelectorAll('[data-scope-option]').forEach(input => input.addEventListener('change', notifyForm));
  const download = document.querySelector('[data-download-brief]');
  download.hidden = false;
  download.addEventListener('click', () => {
    syncBrief();
    const content = `JEBN ENGINEERING — RESIDENTIAL POOL PROJECT BRIEF\n\n${message.value}\n\nProject location: ${city.value || selection().state}\n\nDrawings: DWG + PDF. Residential drawing preparation: 2 business days after all project inputs. PE review and authority approval have separate timelines.\n\nThis is a project enquiry brief, not an engineering design or agreed quote.\nhttps://www.jebnengineering.com/\n`;
    const url = URL.createObjectURL(new Blob([content], {type:'text/plain;charset=utf-8'}));
    const link = document.createElement('a'); link.href=url; link.download='JEBN-residential-pool-brief.txt';
    document.body.append(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    document.querySelector('[data-download-status]').textContent='Your brief download is ready. Nothing has been submitted.';
  });
  updateState();
})();
