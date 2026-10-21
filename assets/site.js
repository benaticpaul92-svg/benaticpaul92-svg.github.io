(() => {
  "use strict";
  const config = window.JEBN_CONFIG || {};
  const email = "benatic@jebnengineering.com";
  const header = document.getElementById("siteHeader");
  const menu = document.getElementById("navMenu");
  const toggle = document.getElementById("menuToggle");
  const mobile = window.matchMedia("(max-width: 1000px)");
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  // A closed mobile menu must also be absent from keyboard navigation.
  if (header && menu && toggle) {
    function setMenu(open, restoreFocus = false) {
      const visible = !mobile.matches || open;
      menu.hidden = !visible;
      menu.classList.toggle("active", mobile.matches && open);
      header.classList.toggle("menu-open", mobile.matches && open);
      toggle.classList.toggle("active", mobile.matches && open);
      toggle.setAttribute("aria-expanded", String(mobile.matches && open));
      toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
      if (restoreFocus) toggle.focus();
    }
    toggle.hidden = false;
    toggle.addEventListener("click", () => setMenu(toggle.getAttribute("aria-expanded") !== "true"));
    menu.querySelectorAll("a").forEach(link => link.addEventListener("click", () => setMenu(false)));
    document.addEventListener("keydown", event => {
      if (event.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") setMenu(false, true);
    });
    document.addEventListener("click", event => {
      if (!header.contains(event.target)) setMenu(false);
    });
    header.addEventListener("focusout", () => {
      requestAnimationFrame(() => {
        if (!header.contains(document.activeElement)) setMenu(false);
      });
    });
    mobile.addEventListener("change", () => setMenu(false));
    setMenu(false);
  }

  // Use ordinary anchor URLs, including browser history and no-JS behavior.
  document.querySelectorAll('a[href="#contact"]').forEach(link => {
    link.addEventListener("click", () => {
      requestAnimationFrame(() => {
        document.getElementById("contact-heading")?.focus({ preventScroll: true });
      });
    });
  });
  const dock = document.querySelector(".enquiry-dock");
  const contact = document.getElementById("contact");
  if (dock && contact && "IntersectionObserver" in window) {
    new IntersectionObserver(entries => {
      dock.hidden = entries[0].isIntersecting;
    }, { threshold: 0.05 }).observe(contact);
  }

  function endpointIsReady(value) {
    return typeof value === "string" &&
      /^https:\/\/script\.google\.com\/macros\/s\/[a-z0-9_-]{20,200}\/exec$/i.test(value) &&
      !/YOUR|PLACEHOLDER|DEPLOYMENT_ID/i.test(value);
  }

  document.querySelectorAll("[data-enquiry-form]").forEach(form => {
    const submit = form.querySelector('[type="submit"]');
    const fields = form.querySelector("fieldset");
    const status = form.querySelector("[data-form-status]");
    const emailLink = form.querySelector("[data-email-draft]");
    const copyButton = form.querySelector("[data-copy-message]");
    const copyText = form.querySelector("[data-copy-text]");
    const restart = form.querySelector("[data-new-enquiry]");
    const ready = endpointIsReady(config.formEndpoint);
    let sending = false;
    let completed = false;
    let reference = "";
    let previousPayload = "";

    function setStatus(message, kind) {
      status.textContent = message;
      status.dataset.state = kind;
    }
    function draftBody() {
      // Read controls directly so the copy fallback still works after success,
      // when the fieldset has been disabled to prevent duplicate submissions.
      const value = name => form.elements.namedItem(name)?.value || "";
      return [
        "Project enquiry",
        `Name: ${value("name")}`,
        `Email: ${value("email")}`,
        `Project location: ${value("location")}`,
        `Company: ${value("company")}`,
        `Timeline: ${value("timeline")}`,
        `Page: ${location.origin}${location.pathname}`,
        "",
        value("message")
      ].join("\n");
    }
    function updateFallback() {
      // Plain mailto fallback uses only the public address. No BCC/hidden recipient.
      emailLink.href = `mailto:${email}?subject=${encodeURIComponent("JEBN project enquiry")}&body=${encodeURIComponent(draftBody())}`;
    }
    function focusStatus() {
      status.focus({ preventScroll: true });
      status.scrollIntoView({ behavior: reducedMotion.matches ? "auto" : "smooth", block: "nearest" });
    }
    function initialState() {
      setStatus(ready
        ? "Ready to send. Fields marked required are needed."
        : "Online enquiries are not connected yet. You can type your details below, then open an email draft or copy your message.", ready ? "ready" : "unavailable");
      submit.disabled = !ready;
      submit.textContent = ready ? "Send enquiry" : "Online sending unavailable";
      updateFallback();
    }
    if (ready) form.action = config.formEndpoint;
    form.addEventListener("input", updateFallback);
    copyButton.hidden = false;
    copyButton.addEventListener("click", async () => {
      const body = draftBody();
      try {
        await navigator.clipboard.writeText(body);
        setStatus(`Message copied. Paste it into an email to ${email} and send it from your email app.`, "info");
      } catch {
        copyText.hidden = false;
        copyText.value = body;
        copyText.focus();
        copyText.select();
        setStatus("Select and copy the message below, then paste it into your email app.", "info");
      }
    });
    restart.addEventListener("click", () => {
      fields.disabled = false;
      completed = false;
      reference = "";
      previousPayload = "";
      form.reset();
      restart.hidden = true;
      copyText.hidden = true;
      initialState();
      form.elements.name.focus();
    });

    form.addEventListener("submit", async event => {
      event.preventDefault();
      if (sending || completed) return;
      if (!ready) {
        initialState();
        focusStatus();
        return;
      }
      if (!form.reportValidity()) return;
      if (!form.elements.name.value.trim() || !form.elements.message.value.trim()) {
        setStatus("Please enter your name and a short description of your project.", "error");
        focusStatus();
        return;
      }
      // Honeypot submissions never trigger a request or a conversion.
      if (form.elements._gotcha.value) {
        setStatus("Unable to submit this form. Please use the email option below.", "error");
        focusStatus();
        return;
      }
      // URL-encoded POST is a simple CORS request; no preflight or no-cors mode.
      // A readable, matching receipt is required before showing success.
      const data = new URLSearchParams(new FormData(form));
      data.set("page", location.pathname); // Never forward a full URL/query to analytics.
      data.set("page_title", document.title);
      data.set("subject", "JEBN website project enquiry");
      const query = new URLSearchParams(location.search);
      // Current-page campaign labels only; no cookies, click IDs or cross-page storage.
      for (const key of ["utm_source", "utm_medium", "utm_campaign"]) {
        const value = query.get(key);
        if (value && /^[a-z0-9_. -]{1,100}$/i.test(value)) data.set(key, value);
      }
      const payload = data.toString();
      if (!reference || payload !== previousPayload) {
        reference = window.crypto?.randomUUID?.() || `enquiry-${Date.now()}-${Math.random().toString(36).slice(2)}`;
        previousPayload = payload;
      }
      data.set("enquiry_reference", reference);
      sending = true;
      fields.disabled = true;
      submit.disabled = true;
      submit.textContent = "Sending…";
      form.setAttribute("aria-busy", "true");
      setStatus("Submitting your enquiry…", "sending");
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), config.formTimeoutMs || 45000);
      try {
        const response = await fetch(config.formEndpoint, {
          method: "POST",
          body: data,
          headers: { Accept: "application/json" },
          redirect: "follow",
          signal: controller.signal,
          credentials: "omit"
        });
        const result = await response.json().catch(() => null);
        // Apps Script ContentService redirects to Google's response host.
        // Only an acknowledgement of this exact stored enquiry counts.
        const responseURL = new URL(response.url);
        const trustedResponse = responseURL.href === config.formEndpoint ||
          (responseURL.protocol === "https:" && responseURL.hostname === "script.googleusercontent.com");
        const accepted = result && typeof result === "object" && !Array.isArray(result) &&
          result.service === "jebn-enquiries" && result.version === 1 &&
          result.ok === true && result.stored === true && result.reference === reference &&
          !("error" in result) && !("errors" in result) && !("challenge" in result);
        if (!response.ok || !trustedResponse || !accepted) {
          const error = new Error("Form was not accepted");
          error.status = ["BUSY", "RATE_LIMITED"].includes(result?.code) ? 429 : response.status;
          throw error;
        }
        completed = true;
        // Capture fallback content before disabling the fieldset.
        updateFallback();
        fields.disabled = true;
        submit.textContent = "Enquiry submitted";
        restart.hidden = false;
        setStatus("Thank you. Your enquiry has been received. We’ll reply by email.", "success");
        // Only accepted submissions emit this event. The optional Google Ads
        // adapter also requires enabled settings, consent and a conversion label.
        // Field values and email addresses never enter dataLayer.
        try {
          window.dataLayer = window.dataLayer || [];
          window.dataLayer.push({
            event: "jebn_enquiry_accepted",
            form_name: "project_enquiry",
            page_path: location.pathname,
            enquiry_reference: reference
          });
          window.JEBN_GOOGLE_ADS?.recordEnquiry(reference);
        } catch { /* Measurement failure must never change submission success. */ }
      } catch (error) {
        let message = "We could not confirm your submission. Your details are still here. You can try again or use the email option below.";
        if (error.name === "AbortError") message = "The connection timed out, so we cannot confirm whether your enquiry arrived. Your details are still here. Please use the email option if you need to follow up.";
        if (error.status === 429) message = "Online enquiries are temporarily busy. Your details are still here. Please try later or use the email option below.";
        setStatus(message, "error");
      } finally {
        clearTimeout(timeout);
        sending = false;
        form.removeAttribute("aria-busy");
        if (!completed) {
          fields.disabled = false;
          submit.disabled = false;
          submit.textContent = "Send enquiry";
        }
        focusStatus();
      }
    });
    initialState();
  });
})();
