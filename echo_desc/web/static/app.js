// app.js (entrypoint + helpery)

(function () {
  "use strict";

  // mini-helpery
  window.$$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  window.$ = (sel, root = document) => root.querySelector(sel);

  document.addEventListener("DOMContentLoaded", () => {
    // te funkcje dostarczy każdy moduł
    if (window.initTabs) window.initTabs();
    if (window.initSettings) window.initSettings();
    if (window.initTemplateEditor) window.initTemplateEditor();
  });
})();
