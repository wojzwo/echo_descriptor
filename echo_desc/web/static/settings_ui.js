// settings_ui.js
(function () {
  "use strict";

  window.initSettings = function initSettings() {
    const table = document.getElementById("settingsTable");
    const exportBox = document.getElementById("exportBox");

    const btnExport = document.getElementById("btnExport");
    const btnSelectAll = document.getElementById("btnSelectAll");
    const btnHideAll = document.getElementById("btnHideAll");
    const btnResetOrder = document.getElementById("btnResetOrder");

    if (!table) return;

    function rows() {
      return Array.from(document.querySelectorAll("#settingsBody tr[data-param]"));
    }

    function exportYamlFromTable() {
      const out = [];
      out.push("# config/web/parameters_ui.yaml");
      out.push("# UI-only settings (visibility + order)");
      out.push("params:");
      rows().forEach(tr => {
        const name = tr.dataset.param;
        const cb = tr.querySelector("input.uiEnabled");
        const ord = tr.querySelector("input.uiOrder");
        const enabled = !!cb?.checked;
        let order = 9999;
        const v = Number(ord?.value);
        if (Number.isFinite(v)) order = Math.trunc(v);

        out.push(`  - name: ${name}`);
        out.push(`    enabled: ${enabled ? "true" : "false"}`);
        out.push(`    order: ${order}`);
      });
      return out.join("\n") + "\n";
    }

    function refreshExportBox() {
      if (!exportBox) return;
      exportBox.value = exportYamlFromTable();
    }

    table.addEventListener("input", refreshExportBox);
    refreshExportBox();

    btnExport?.addEventListener("click", async () => {
      refreshExportBox();
      exportBox?.focus();
      exportBox?.select();
      try { await navigator.clipboard.writeText(exportBox.value); } catch (_) {}
    });

    btnSelectAll?.addEventListener("click", () => {
      rows().forEach(tr => {
        const cb = tr.querySelector("input.uiEnabled");
        if (cb) cb.checked = true;
      });
      refreshExportBox();
    });

    btnHideAll?.addEventListener("click", () => {
      rows().forEach(tr => {
        const cb = tr.querySelector("input.uiEnabled");
        if (cb) cb.checked = false;
      });
      refreshExportBox();
    });

    btnResetOrder?.addEventListener("click", () => {
      let i = 1;
      rows().forEach(tr => {
        const ord = tr.querySelector("input.uiOrder");
        if (ord) ord.value = String(i * 10);
        i += 1;
      });
      refreshExportBox();
    });
  };
})();
