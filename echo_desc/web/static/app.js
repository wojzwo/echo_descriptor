function initTabs() {
  const btns = document.querySelectorAll(".tabbtn");
  const panels = document.querySelectorAll(".panel");

  function activate(tabId) {
    btns.forEach(b => b.classList.toggle("active", b.dataset.tab === tabId));
    panels.forEach(p => p.classList.toggle("active", p.id === tabId));

    // aktualizuj URL (bez reload) żeby dało się linkować / refresh
    const map = { "tab-params": "params", "tab-template": "template", "tab-settings": "settings" };
    const tabName = map[tabId] || "params";
    const url = new URL(window.location.href);
    url.searchParams.set("tab", tabName);
    window.history.replaceState({}, "", url.toString());
  }

  btns.forEach(b => {
    b.addEventListener("click", () => activate(b.dataset.tab));
  });

  // jeśli nie ma aktywnego panelu (edge) -> params
  const anyActive = Array.from(panels).some(p => p.classList.contains("active"));
  if (!anyActive) activate("tab-params");
}

function initTemplateSwitcher() {
  const sel = document.getElementById("templateSelect");
  if (!sel) return;

  function showTemplateBlock() {
    const tid = sel.value;
    document.querySelectorAll(".templateBlock").forEach(el => {
      el.style.display = (el.dataset.templateId === tid) ? "block" : "none";
    });
  }

  sel.addEventListener("change", showTemplateBlock);
  showTemplateBlock();

  document.addEventListener("click", (e) => {
    const btn = e.target?.closest?.('button[data-action="toggle-pars"]');
    if (!btn) return;

    const on = btn.dataset.on === "1";
    const visible = Array.from(document.querySelectorAll(".templateBlock"))
      .find(el => el.style.display === "block");
    if (!visible) return;

    visible.querySelectorAll('input[type="checkbox"][name="paragraph_ids"]').forEach(cb => {
      cb.checked = on;
    });
  });
}

function initSettingsHelpers() {
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

  function collectFromTable() {
    const out = [];
    rows().forEach(tr => {
      const name = tr.dataset.param;
      const cb = tr.querySelector("input.uiEnabled");
      const ord = tr.querySelector("input.uiOrder");

      const enabled = !!cb?.checked;
      let order = 9999;
      const v = Number(ord?.value);
      if (Number.isFinite(v)) order = Math.trunc(v);

      out.push({ name, enabled, order });
    });

    // preview ładniej wygląda, gdy jest posortowane
    out.sort((a, b) => (a.order - b.order) || a.name.localeCompare(b.name));
    return out;
  }

  function exportYaml(params) {
    const out = [];
    out.push("# config/web/parameters_ui.yaml");
    out.push("# UI-only settings (visibility + order)");
    out.push("params:");
    params.forEach(p => {
      out.push(`  - name: ${p.name}`);
      out.push(`    enabled: ${p.enabled ? "true" : "false"}`);
      out.push(`    order: ${Number.isFinite(p.order) ? p.order : 9999}`);
    });
    return out.join("\n") + "\n";
  }

  function refreshExportBox() {
    if (!exportBox) return;
    exportBox.value = exportYaml(collectFromTable());
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
}

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initTemplateSwitcher();
  initSettingsHelpers();
});
