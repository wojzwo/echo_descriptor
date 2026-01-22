// --- Tabs
function initTabs() {
  const btns = document.querySelectorAll(".tabbtn");
  const panels = document.querySelectorAll(".panel");

  btns.forEach((b) => {
    b.addEventListener("click", () => {
      btns.forEach((x) => x.classList.remove("active"));
      panels.forEach((p) => p.classList.remove("active"));
      b.classList.add("active");
      const panel = document.getElementById(b.dataset.tab);
      if (panel) panel.classList.add("active");
    });
  });
}

// --- Template-specific checklist display
function initTemplateSwitcher() {
  const sel = document.getElementById("templateSelect");
  if (!sel) return;

  function showTemplateBlock() {
    const tid = sel.value;
    document.querySelectorAll(".templateBlock").forEach((el) => {
      el.style.display = el.dataset.templateId === tid ? "block" : "none";
    });
  }

  sel.addEventListener("change", showTemplateBlock);
  showTemplateBlock();

  // Toggle all paragraph checkboxes in currently visible template block
  document.addEventListener("click", (e) => {
    const btn = e.target?.closest?.('button[data-action="toggle-pars"]');
    if (!btn) return;

    const on = btn.dataset.on === "1";
    const visible = Array.from(document.querySelectorAll(".templateBlock")).find(
      (el) => el.style.display === "block"
    );

    if (!visible) return;

    visible
      .querySelectorAll('input[type="checkbox"][name="paragraph_ids"]')
      .forEach((cb) => {
        cb.checked = on;
      });
  });
}

// --- Settings: read table -> YAML preview + save to backend
function initSettings() {
  const table = document.getElementById("settingsTable");
  const exportBox = document.getElementById("exportBox");

  const btnSave = document.getElementById("btnSaveSettings");
  const btnExport = document.getElementById("btnExport");
  const btnSelectAll = document.getElementById("btnSelectAll");
  const btnHideAll = document.getElementById("btnHideAll");
  const btnResetOrder = document.getElementById("btnResetOrder");

  if (!table) return;

  function rows() {
    return Array.from(document.querySelectorAll("#settingsBody tr[data-param]"));
  }

  function collectParamsFromTable() {
    const out = [];
    rows().forEach((tr) => {
      const name = tr.dataset.param;
      const cb = tr.querySelector("input.uiEnabled");
      const ord = tr.querySelector("input.uiOrder");
      const enabled = !!cb?.checked;

      let order = 9999;
      const v = Number(ord?.value);
      if (Number.isFinite(v)) order = Math.trunc(v);

      out.push({ name, enabled, order });
    });

    // stable sort for UI/export (backend will normalize anyway)
    out.sort((a, b) => {
      if (a.order !== b.order) return a.order - b.order;
      return String(a.name).localeCompare(String(b.name));
    });

    return out;
  }

  function exportYaml(params) {
    const out = [];
    out.push("# config/web/parameters_ui.yaml");
    out.push("# UI-only settings (visibility + order)");
    out.push("params:");
    params.forEach((p) => {
      out.push(`  - name: ${p.name}`);
      out.push(`    enabled: ${p.enabled ? "true" : "false"}`);
      out.push(`    order: ${Number.isFinite(p.order) ? p.order : 9999}`);
    });
    return out.join("\n") + "\n";
  }

  function refreshExportBox() {
    if (!exportBox) return;
    const params = collectParamsFromTable();
    exportBox.value = exportYaml(params);
  }

  table.addEventListener("input", refreshExportBox);
  refreshExportBox();

  btnExport?.addEventListener("click", async () => {
    refreshExportBox();
    exportBox?.focus();
    exportBox?.select();
    try {
      await navigator.clipboard.writeText(exportBox.value);
    } catch (_) {}
  });

  btnSelectAll?.addEventListener("click", () => {
    rows().forEach((tr) => {
      const cb = tr.querySelector("input.uiEnabled");
      if (cb) cb.checked = true;
    });
    refreshExportBox();
  });

  btnHideAll?.addEventListener("click", () => {
    rows().forEach((tr) => {
      const cb = tr.querySelector("input.uiEnabled");
      if (cb) cb.checked = false;
    });
    refreshExportBox();
  });

  btnResetOrder?.addEventListener("click", () => {
    let i = 1;
    rows().forEach((tr) => {
      const ord = tr.querySelector("input.uiOrder");
      if (ord) ord.value = String(i * 10);
      i += 1;
    });
    refreshExportBox();
  });

  btnSave?.addEventListener("click", async () => {
    const params = collectParamsFromTable();

    const resp = await fetch("/api/settings/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ params }),
    });

    let data = null;
    try {
      data = await resp.json();
    } catch (_) {}

    if (!resp.ok || !data?.ok) {
      const msg = data?.error ? String(data.error) : "Błąd zapisu settings (backend).";
      alert(msg);
      return;
    }

    window.location.href = "/";
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initTemplateSwitcher();
  initSettings();
});
