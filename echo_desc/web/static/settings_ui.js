(function () {
  "use strict";

  window.initSettings = function initSettings() {
    const form = document.getElementById("settingsForm");
    const exportBox = document.getElementById("exportBox");

    const btnSaveSettings = document.getElementById("btnSaveSettings");
    const btnReloadSettings = document.getElementById("btnReloadSettings");

    const btnExport = document.getElementById("btnExport");
    const btnSelectAll = document.getElementById("btnSelectAll");
    const btnHideAll = document.getElementById("btnHideAll");
    const btnResetOrder = document.getElementById("btnResetOrder");

    const tbodyVis = document.getElementById("settingsBodyVisible");
    const tbodyHid = document.getElementById("settingsBodyHidden");

    if (!tbodyVis || !tbodyHid) return;

    // ---------- LOAD INPUT DATA (from server-rendered JSON) ----------
    let paramItems = [];
    let paramUi = {};
    try { paramItems = JSON.parse(document.getElementById("paramItemsData")?.textContent || "[]"); } catch (_) {}
    try { paramUi = JSON.parse(document.getElementById("paramUiData")?.textContent || "{}"); } catch (_) {}

    // Model: [{name, desc, enabled, order, _idx}]
    const model = (paramItems || [])
      .map((it, idx) => {
        const name = String(it?.name || "").trim();
        const desc = String(it?.description || "").trim();
        const st = (paramUi && typeof paramUi === "object") ? (paramUi[name] || {}) : {};
        const enabled = st.enabled !== undefined ? !!st.enabled : true;
        const order = Number.isFinite(Number(st.order)) ? Math.trunc(Number(st.order)) : (idx + 1) * 10;
        return { name, desc, enabled, order, _idx: idx };
      })
      .filter(x => x.name);

    // ---------- HELPERS ----------
    function esc(s) {
      return String(s || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;");
    }

    function rowHtml(x) {
      const checked = x.enabled ? "checked" : "";
      return `
        <tr data-param="${esc(x.name)}">
          <td class="dragCell">
            <span class="dragHandle" draggable="true" title="Przeciągnij">☰</span>
          </td>
          <td>
            <input type="checkbox" class="uiEnabled" name="enabled__${esc(x.name)}" ${checked}/>
          </td>
          <td>
            <input class="orderInput uiOrder" type="number" name="order__${esc(x.name)}" value="${esc(x.order)}"/>
          </td>
          <td>
            <strong>${esc(x.name)}</strong>
            ${x.desc ? `<div class="muted">${esc(x.desc)}</div>` : ``}
          </td>
        </tr>
      `;
    }

    function rowsIn(tbody) {
      return Array.from(tbody.querySelectorAll('tr[data-param]'));
    }

    function allRowsDom() {
      return rowsIn(tbodyVis).concat(rowsIn(tbodyHid));
    }

    function recomputeOrders(tbody, step = 10) {
      rowsIn(tbody).forEach((tr, idx) => {
        const name = tr.dataset.param || "";
        const inp = tr.querySelector(`input.uiOrder[name="order__${CSS.escape(name)}"]`);
        if (inp) inp.value = String((idx + 1) * step);
      });
    }

    function syncDomToModel() {
      for (const tr of allRowsDom()) {
        const name = tr.dataset.param || "";
        const ord = tr.querySelector(`input.uiOrder[name="order__${CSS.escape(name)}"]`);
        const enabled = !!tr.querySelector(`input.uiEnabled[name="enabled__${CSS.escape(name)}"]`)?.checked;
        const v = Number(ord?.value);
        const order = Number.isFinite(v) ? Math.trunc(v) : 9999;

        const m = model.find(x => x.name === name);
        if (m) { m.enabled = enabled; m.order = order; }
      }
    }

    function recomputeOrdersBoth(step = 10) {
      recomputeOrders(tbodyVis, step);
      recomputeOrders(tbodyHid, step);
      syncDomToModel();
    }

    function exportYamlFromDom() {
      const out = [];
      out.push("# config/web/parameters_ui.yaml");
      out.push("# UI-only settings (visibility + order)");
      out.push("params:");

      function emitFromTbody(tbody) {
        rowsIn(tbody).forEach(tr => {
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
      }

      emitFromTbody(tbodyVis);
      emitFromTbody(tbodyHid);

      return out.join("\n") + "\n";
    }

    function refreshExportBox() {
      if (!exportBox) return;
      exportBox.value = exportYamlFromDom();
    }

    function renderFromModel() {
      const visible = model
        .filter(x => x.enabled)
        .sort((a, b) => (a.order - b.order) || a.name.localeCompare(b.name));

      const hidden = model
        .filter(x => !x.enabled)
        .sort((a, b) => (a.order - b.order) || a.name.localeCompare(b.name));

      tbodyVis.innerHTML = visible.map(rowHtml).join("");
      tbodyHid.innerHTML = hidden.map(rowHtml).join("");

      recomputeOrdersBoth(10);
      refreshExportBox();
    }

    // ---------- MOVE BETWEEN LISTS ON CHECKBOX CHANGE ----------
    function onEnabledToggle(tr) {
      const name = tr.dataset.param || "";
      const cb = tr.querySelector("input.uiEnabled");
      const enabled = !!cb?.checked;

      const dst = enabled ? tbodyVis : tbodyHid;
      dst.appendChild(tr);

      recomputeOrdersBoth(10);
      refreshExportBox();

      const m = model.find(x => x.name === name);
      if (m) m.enabled = enabled;
    }

    function bindToggleDelegation() {
      function handler(e) {
        const inp = e.target?.closest?.("input.uiEnabled");
        if (!inp) return;
        const tr = inp.closest('tr[data-param]');
        if (!tr) return;
        onEnabledToggle(tr);
      }
      tbodyVis.addEventListener("change", handler);
      tbodyHid.addEventListener("change", handler);
    }

    // ---------- DnD (both lists, cross-list supported) ----------
    let draggingRow = null;

    function rowFromEvent(e) {
      return e.target?.closest?.('tr[data-param]') || null;
    }
    function handleFromEvent(e) {
      return e.target?.closest?.('.dragHandle[draggable="true"]') || null;
    }

    function setupDnD(tbody) {
      tbody.addEventListener("dragstart", (e) => {
        const handle = handleFromEvent(e);
        if (!handle) return;

        const tr = handle.closest('tr[data-param]');
        if (!tr) return;

        draggingRow = tr;
        tr.classList.add("dragging");

        try {
          e.dataTransfer.effectAllowed = "move";
          e.dataTransfer.setData("text/plain", tr.dataset.param || "");
        } catch (_) {}
      }, true);

      tbody.addEventListener("dragend", () => {
        if (draggingRow) draggingRow.classList.remove("dragging");
        draggingRow = null;
        allRowsDom().forEach(r => r.classList.remove("dropTarget"));
        tbodyVis.classList.remove("dropZone");
        tbodyHid.classList.remove("dropZone");
      });

      tbody.addEventListener("dragover", (e) => {
        if (!draggingRow) return;
        e.preventDefault();

        const overRow = rowFromEvent(e);
        tbody.classList.add("dropZone");

        allRowsDom().forEach(r => r.classList.remove("dropTarget"));
        if (!overRow || overRow === draggingRow) return;

        tbody.classList.remove("dropZone");
        overRow.classList.add("dropTarget");

        const rect = overRow.getBoundingClientRect();
        const before = e.clientY < rect.top + rect.height / 2;

        if (before) {
          if (overRow.previousSibling !== draggingRow) tbody.insertBefore(draggingRow, overRow);
        } else {
          if (overRow.nextSibling !== draggingRow) tbody.insertBefore(draggingRow, overRow.nextSibling);
        }
      });

      tbody.addEventListener("drop", (e) => {
        if (!draggingRow) return;
        e.preventDefault();

        const overRow = rowFromEvent(e);
        if (!overRow) tbody.appendChild(draggingRow);

        const name = draggingRow.dataset.param || "";
        const cb = draggingRow.querySelector(`input.uiEnabled[name="enabled__${CSS.escape(name)}"]`);
        const nowEnabled = (tbody === tbodyVis);
        if (cb) cb.checked = nowEnabled;

        const m = model.find(x => x.name === name);
        if (m) m.enabled = nowEnabled;

        recomputeOrdersBoth(10);
        refreshExportBox();
      });
    }

    // ---------- BUTTONS ----------
    btnExport?.addEventListener("click", async () => {
      recomputeOrdersBoth(10);
      refreshExportBox();
      exportBox?.focus();
      exportBox?.select();
      try { await navigator.clipboard.writeText(exportBox.value); } catch (_) {}
    });

    btnSelectAll?.addEventListener("click", () => {
      for (const tr of allRowsDom()) {
        const name = tr.dataset.param || "";
        const cb = tr.querySelector(`input.uiEnabled[name="enabled__${CSS.escape(name)}"]`);
        if (cb) cb.checked = true;
        tbodyVis.appendChild(tr);
        const m = model.find(x => x.name === name);
        if (m) m.enabled = true;
      }
      recomputeOrdersBoth(10);
      refreshExportBox();
    });

    btnHideAll?.addEventListener("click", () => {
      for (const tr of allRowsDom()) {
        const name = tr.dataset.param || "";
        const cb = tr.querySelector(`input.uiEnabled[name="enabled__${CSS.escape(name)}"]`);
        if (cb) cb.checked = false;
        tbodyHid.appendChild(tr);
        const m = model.find(x => x.name === name);
        if (m) m.enabled = false;
      }
      recomputeOrdersBoth(10);
      refreshExportBox();
    });

    btnResetOrder?.addEventListener("click", () => {
      const vis = model.filter(x => x.enabled).sort((a,b) => a._idx - b._idx);
      const hid = model.filter(x => !x.enabled).sort((a,b) => a._idx - b._idx);

      tbodyVis.innerHTML = vis.map((x, i) => rowHtml({ ...x, order: (i + 1) * 10 })).join("");
      tbodyHid.innerHTML = hid.map((x, i) => rowHtml({ ...x, order: (i + 1) * 10 })).join("");

      recomputeOrdersBoth(10);
      refreshExportBox();
    });

    // --- CONFIRM ON SAVE ---
    form?.addEventListener("submit", (e) => {
      recomputeOrdersBoth(10);
      refreshExportBox();

      const ok = confirm("Zapisać ustawienia? Nadpiszesz ./config/web/parameters_ui.yaml.");
      if (!ok) {
        e.preventDefault();
        e.stopPropagation();
      }
    });

    // --- LOAD CURRENT FROM BACKEND (no full reload) ---
    async function loadCurrentFromServer() {
      const r = await fetch("/api/settings/parameters_ui", { method: "GET" });
      if (!r.ok) throw new Error("HTTP " + r.status);
      return await r.json(); // { ok:true, params:[{name,enabled,order}...] }
    }

    btnReloadSettings?.addEventListener("click", async () => {
      const ok = confirm("Wczytać aktualne ustawienia z serwera? Niezapisane zmiany w Settings przepadną.");
      if (!ok) return;

      try {
        const data = await loadCurrentFromServer();
        if (!data || data.ok !== true || !Array.isArray(data.params)) {
          alert("Nie udało się wczytać ustawień (zły format odpowiedzi).");
          return;
        }

        const byName = new Map(data.params.map(p => [String(p.name || "").trim(), p]));
        for (const m of model) {
          const p = byName.get(m.name);
          if (!p) continue;
          m.enabled = (p.enabled !== undefined) ? !!p.enabled : m.enabled;
          m.order = Number.isFinite(Number(p.order)) ? Math.trunc(Number(p.order)) : m.order;
        }

        renderFromModel();
      } catch (err) {
        alert("Błąd wczytywania ustawień: " + String(err?.message || err));
      }
    });

    // live refresh (manual edits)
    tbodyVis.addEventListener("input", () => { syncDomToModel(); refreshExportBox(); });
    tbodyHid.addEventListener("input", () => { syncDomToModel(); refreshExportBox(); });

    // ---------- INIT ----------
    renderFromModel();
    bindToggleDelegation();
    setupDnD(tbodyVis);
    setupDnD(tbodyHid);
  };
})();
