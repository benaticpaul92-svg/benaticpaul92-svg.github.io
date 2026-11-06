/* Progressive enhancements for redesigned pages. Native HTML remains usable. */
(() => {
  'use strict';
  const localPreview = ['localhost', '127.0.0.1'].includes(location.hostname);
  document.querySelectorAll('[data-enquiry-form]').forEach(form => {
    const required = [...form.querySelectorAll('[required]')];
    required.forEach(field => {
      const error = document.createElement('span');
      error.id = `${field.id}-error`;
      error.className = 'field-error';
      error.hidden = true;
      field.insertAdjacentElement('afterend', error);
      field.setAttribute('aria-describedby', error.id);
      function validate() {
        field.setCustomValidity('');
        if (!field.value.trim()) field.setCustomValidity('Please complete this field.');
        const message = field.validity.typeMismatch
          ? 'Enter an email address such as name@example.com.'
          : field.validationMessage;
        error.textContent = message;
        error.hidden = !message;
        field.setAttribute('aria-invalid', String(Boolean(message)));
        return !message;
      }
      field.addEventListener('blur', () => { field.dataset.touched = 'true'; validate(); });
      field.addEventListener('input', () => {
        field.setCustomValidity('');
        if (field.dataset.touched || field.getAttribute('aria-invalid') === 'true') validate();
      });
      field.addEventListener('invalid', validate);
    });
    if (localPreview) {
      const note = document.createElement('p');
      note.className = 'small';
      note.textContent = 'Local preview: enquiries are not sent from this version.';
      form.prepend(note);
      queueMicrotask(() => {
        form.querySelector('[data-form-status]').textContent = 'Complete the required fields to check the form.';
        form.querySelector('[type="submit"]').textContent = 'Check form (preview)';
      });
      // Prevent any live notification in a developer preview, including Enter submits.
      form.addEventListener('submit', event => {
        event.preventDefault();
        event.stopImmediatePropagation();
        const status = form.querySelector('[data-form-status]');
        status.textContent = 'Preview only. Your form is valid; no enquiry or email was sent.';
        status.dataset.state = 'info';
        status.focus();
      }, true);
    }
  });
})();
