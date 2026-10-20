(() => {
  "use strict";
  const dialog = document.getElementById("project-viewer");
  if (!dialog || typeof dialog.showModal !== "function") return;
  const picture = dialog.querySelector("img");
  const heading = dialog.querySelector("h2");
  const description = dialog.querySelector("[data-description]");
  const notice = dialog.querySelector("[data-image-status]");
  const fullImage = dialog.querySelector("[data-full-image]");
  let trigger;
  document.querySelectorAll("[data-project-preview]").forEach(link => {
    link.addEventListener("click", event => {
      event.preventDefault();
      trigger = link;
      const card = link.closest(".portfolio-card");
      heading.textContent = card.querySelector("h3").textContent;
      description.textContent = card.querySelector("p").textContent;
      picture.alt = card.querySelector("img").alt;
      picture.hidden = true;
      notice.hidden = false;
      notice.textContent = "Loading preview…";
      fullImage.href = link.href;
      picture.onload = () => { picture.hidden = false; notice.hidden = true; };
      picture.onerror = () => { notice.textContent = "This preview could not load. You can request sample drawings through the enquiry form."; };
      // Hidden lazy images may never start loading. A viewer request is explicit.
      picture.loading = "eager";
      picture.src = link.href;
      dialog.showModal();
      document.body.classList.add("viewer-open");
    });
  });
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
