// tabs.js
(function () {
  "use strict";

  const MAIN_TAB_IDS = ["tab-params", "tab-template", "tab-settings"];

  function activateTab(tabId) {
    if (!MAIN_TAB_IDS.includes(tabId)) tabId = "tab-params";

    // buttons
    window.$$(".tabbtn[data-tab]").forEach(b => b.classList.remove("active"));
    const btn = window.$(`.tabbtn[data-tab="${CSS.escape(tabId)}"]`);
    if (btn) btn.classList.add("active");

    // panels (TYLKO główne)
    MAIN_TAB_IDS.forEach(id => {
      const p = document.getElementById(id);
      if (p) p.classList.remove("active");
    });
    const panel = document.getElementById(tabId);
    if (panel) panel.classList.add("active");

    // URL state
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

    // start tab from URL
    const url = new URL(window.location.href);
    const q = (url.searchParams.get("tab") || "").toLowerCase();
    const map = { params: "tab-params", template: "tab-template", settings: "tab-settings" };
    activateTab(map[q] || "tab-params");
  };
})();
