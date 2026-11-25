(() => {
  "use strict";
  const dialog = document.getElementById("project-viewer");
  if (!dialog || typeof dialog.showModal !== "function") return;
  const picture = dialog.querySelector("img");
  const heading = dialog.querySelector("h2");
  const description = dialog.querySelector("[data-description]");
  const notice = dialog.querySelector("[data-image-status]");
  const fullImage = dialog.querySelector("[data-full-image]");
  // Only pages that show drawing sets have the step buttons.
  const steps = dialog.querySelector("[data-viewer-steps]");
  const position = dialog.querySelector("[data-viewer-position]");
  let trigger;
  let sheets = [];
  let current = 0;

  const show = (href, title, text, alt, preview) => {
    heading.textContent = title;
    description.textContent = text;
    picture.alt = alt;
    picture.hidden = true;
    notice.hidden = false;
    notice.textContent = "Loading preview…";
    fullImage.href = href;
    // A large sheet takes a moment to decode after it has loaded: keep the notice until it can be painted.
    const reveal = () => { if (picture.src === new URL(href, location.href).href) { picture.hidden = false; notice.hidden = true; } };
    picture.onload = () => { picture.decode ? picture.decode().then(reveal, reveal) : reveal(); };
    picture.onerror = () => { notice.textContent = "This preview could not load. You can request sample drawings through the quote form."; };
    // Phones, tablets and 1x screens get the 1600 px copy of a sheet; 2x desktops still get the full 3200 px file.
    if (preview) { picture.sizes = "(max-width: 1150px) calc(100vw - 4rem), 1072px"; picture.srcset = preview + " 1600w, " + href + " 3200w"; } else { picture.removeAttribute("srcset"); picture.removeAttribute("sizes"); }
    picture.src = href;
    // Hidden lazy images may never start loading. A viewer request is explicit.
    // Set after the new address: switching to eager first would also download the picture the viewer was built with.
    picture.loading = "eager";
  };

  // A drawing set is the ordered list of links in its sheet list: [data-sheet-list="<set>"] a
  const showSheet = index => {
    current = (index + sheets.length) % sheets.length;
    const sheet = sheets[current];
    const list = sheet.closest("[data-sheet-list]");
    show(sheet.href, sheet.dataset.title, list.dataset.setText || "", sheet.dataset.title, sheet.dataset.preview);
    if (position) position.textContent = "Sheet " + (current + 1) + " of " + sheets.length;
  };

  document.querySelectorAll("[data-project-preview]").forEach(link => {
    link.addEventListener("click", event => {
      const set = link.dataset.set;
      const list = set ? Array.from(document.querySelectorAll('[data-sheet-list="' + set + '"] a')) : [];
      const card = link.closest(".portfolio-card");
      // Without a sheet list or a card to describe the picture, the link opens the picture itself.
      if (!list.length && !card) return;
      event.preventDefault();
      trigger = link;
      sheets = steps ? list : [];
      if (steps) steps.hidden = sheets.length < 2;
      if (sheets.length) {
        showSheet(Math.max(0, sheets.findIndex(sheet => sheet.href === link.href)));
      } else if (list.length) {
        const sheet = list.find(item => item.href === link.href) || list[0];
        show(link.href, sheet.dataset.title, "", sheet.dataset.title, sheet.dataset.preview);
      } else {
        show(link.href, card.querySelector("h3").textContent, card.querySelector("p").textContent, card.querySelector("img").alt);
      }
      dialog.showModal();
      document.body.classList.add("viewer-open");
    });
  });
  if (steps) {
    steps.querySelector("[data-viewer-previous]").addEventListener("click", () => showSheet(current - 1));
    steps.querySelector("[data-viewer-next]").addEventListener("click", () => showSheet(current + 1));
    dialog.addEventListener("keydown", event => {
      // Alt, Ctrl, Cmd or Shift with an arrow is a browser or system shortcut, not a step through the set.
      if (sheets.length < 2 || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
      if (event.key === "ArrowLeft") showSheet(current - 1);
      if (event.key === "ArrowRight") showSheet(current + 1);
    });
  }
  dialog.querySelector("[data-close-viewer]").addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", event => {
    if (event.target === dialog) {
      const rect = dialog.getBoundingClientRect();
      if (event.clientX < rect.left || event.clientX > rect.right ||
          event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
    }
  });
  dialog.addEventListener("close", () => {
    document.body.classList.remove("viewer-open");
    trigger?.focus();
  });
})();
