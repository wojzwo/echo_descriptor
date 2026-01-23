// echo_desc/web/static/settings_ui.js
(function () {
  "use strict";

  window.initSettings = function initSettings() {
    const table = document.getElementById("settingsTable");
    const tbody = document.getElementById("settingsBody");
    const form = document.getElementById("settingsForm");
    const exportBox = document.getElementById("exportBox");

    const btnExport = document.getElementById("btnExport");
    const btnSelectAll = document.getElementById("btnSelectAll");
    const btnHideAll = document.getElementById("btnHideAll");
    const btnResetOrder = document.getElementById("btnResetOrder");

    if (!table || !tbody) return;

    function rows() {
      return Array.from(tbody.querySelectorAll('tr[data-param]'));
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

    function recomputeOrder(step = 10) {
      // DOM order => order numbers
      rows().forEach((tr, idx) => {
        const name = tr.dataset.param || "";
        const inp = tr.querySelector(`input.uiOrder[name="order__${CSS.escape(name)}"]`);
        if (inp) inp.value = String((idx + 1) * step);
      });
    }

    // ----------------------------
    // Live refresh (inputs + checks)
    // ----------------------------
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
      // reset order by current DOM sequence (registry order = initial render order)
      recomputeOrder(10);
      refreshExportBox();
    });

    // ----------------------------
    // Drag & drop reorder
    // ----------------------------
    let draggingRow = null;

    function rowFromEvent(e) {
      return e.target?.closest?.('tr[data-param]') || null;
    }

    // Optional: allow drag only by handle
    function isHandle(e) {
      return !!e.target?.closest?.(".dragHandle");
    }

    tbody.addEventListener("dragstart", (e) => {
      const tr = rowFromEvent(e);
      if (!tr) return;

      // uncomment if you want handle-only dragging:
      // if (!isHandle(e)) { e.preventDefault(); return; }

      draggingRow = tr;
      tr.classList.add("dragging");

      try {
        e.dataTransfer.effectAllowed = "move";
        e.dataTransfer.setData("text/plain", tr.dataset.param || "");
      } catch (_) {}
    });

    tbody.addEventListener("dragend", () => {
      if (draggingRow) draggingRow.classList.remove("dragging");
      draggingRow = null;
      rows().forEach(r => r.classList.remove("dropTarget"));
    });

    tbody.addEventListener("dragover", (e) => {
      const over = rowFromEvent(e);
      if (!draggingRow || !over || over === draggingRow) return;

      e.preventDefault(); // allow drop

      rows().forEach(r => r.classList.remove("dropTarget"));
      over.classList.add("dropTarget");

      const rect = over.getBoundingClientRect();
      const before = e.clientY < rect.top + rect.height / 2;

      if (before) {
        if (over.previousSibling !== draggingRow) tbody.insertBefore(draggingRow, over);
      } else {
        if (over.nextSibling !== draggingRow) tbody.insertBefore(draggingRow, over.nextSibling);
      }
    });

    tbody.addEventListener("drop", (e) => {
      if (!draggingRow) return;
      e.preventDefault();

      // after drop: recompute order + refresh export
      recomputeOrder(10);
      refreshExportBox();
    });

    // Always recompute right before saving (so backend gets correct order)
    form?.addEventListener("submit", () => {
      recomputeOrder(10);
      refreshExportBox();
    });
  };
})();
