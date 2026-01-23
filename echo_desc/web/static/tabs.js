// tabs.js
(function () {
  "use strict";

  function activateTab(tabId) {
    // buttons
    window.$$(".tabbtn[data-tab]").forEach(b => b.classList.remove("active"));
    const btn = window.$(`.tabbtn[data-tab="${CSS.escape(tabId)}"]`);
    if (btn) btn.classList.add("active");

    // panels
    window.$$("section.panel").forEach(p => p.classList.remove("active"));
    const panel = document.getElementById(tabId);
    if (panel) panel.classList.add("active");

    // (opcjonalnie) utrzymuj stan w URL
    const map = {
      "tab-params": "params",
      "tab-template": "template",
      "tab-settings": "settings",
    };
    const qtab = map[tabId] || "params";
    const url = new URL(window.location.href);
    url.searchParams.set("tab", qtab);
    window.history.replaceState({}, "", url);
  }

  window.initTabs = function initTabs() {
    const btns = window.$$(".tabbtn[data-tab]");
    if (!btns.length) return;

    btns.forEach(b => {
      b.addEventListener("click", () => {
        activateTab(b.dataset.tab);
      });
    });

    // start tab from URL (jeśli backend już wspiera active_tab, to to i tak zgra)
    const url = new URL(window.location.href);
    const q = (url.searchParams.get("tab") || "").toLowerCase();
    const map = { params: "tab-params", template: "tab-template", settings: "tab-settings" };
    const start = map[q] || "tab-params";
    activateTab(start);
  };
})();
