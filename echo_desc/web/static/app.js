// --------------------
// Tabs (main)
// --------------------
function initTabs() {
  const btns = document.querySelectorAll(".tabbtn[data-tab]");
  const panels = document.querySelectorAll(".panel");

  btns.forEach(b => {
    b.addEventListener("click", () => {
      btns.forEach(x => x.classList.remove("active"));
      // tylko główne panele
      document.querySelectorAll("section.panel").forEach(p => p.classList.remove("active"));
      b.classList.add("active");
      const panel = document.getElementById(b.dataset.tab);
      if (panel) panel.classList.add("active");
    });
  });
}

// --------------------
// Settings (unchanged)
// --------------------
function initSettings() {
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
}

// --------------------
// Template Editor (NEW)
// --------------------
function initTemplateEditor() {
  const tplPanel = document.getElementById("tab-template");
  if (!tplPanel) return;

  // sub-tabs inside template editor
  const subBtns = tplPanel.querySelectorAll('.tabbtn[data-subtab]');
  const subPanels = [document.getElementById("sub-paragraphs"), document.getElementById("sub-reports")];

  subBtns.forEach(b => {
    b.addEventListener("click", () => {
      subBtns.forEach(x => x.classList.remove("active"));
      subPanels.forEach(p => p && p.classList.remove("active"));
      b.classList.add("active");
      const p = document.getElementById(b.dataset.subtab);
      if (p) p.classList.add("active");
    });
  });

  const parListEl = document.getElementById("paragraphsList");
  const repListEl = document.getElementById("reportsList");

  const btnParAdd = document.getElementById("btnParAdd");
  const btnRepAdd = document.getElementById("btnRepAdd");
  const btnSave1 = document.getElementById("btnTplSaveAll");
  const btnSave2 = document.getElementById("btnTplSaveAll2");
  const dirtyHint1 = document.getElementById("tplDirtyHint");
  const dirtyHint2 = document.getElementById("tplDirtyHint2");

  if (!parListEl || !repListEl) return;

  // Load initial data embedded in HTML (fast, no request needed)
  let store = { paragraphs: [], reports: [] };
  try {
    const s = document.getElementById("tplData")?.textContent || "{}";
    store = JSON.parse(s);
  } catch (_) {}

  // Normalize to maps for editing
  const P = new Map(); // id -> {id,label,description,text}
  const R = new Map(); // id -> {id,title,paragraph_ids:[]}

  (store.paragraphs || []).forEach(p => P.set(p.id, {
    id: String(p.id || "").trim(),
    label: String(p.label || p.id || "").trim(),
    description: String(p.description || "").trim(),
    text: String(p.text || "").trim(),
  }));

  (store.reports || []).forEach(r => R.set(r.id, {
    id: String(r.id || "").trim(),
    title: String(r.title || r.id || "").trim(),
    paragraph_ids: Array.isArray(r.paragraph_ids) ? r.paragraph_ids.map(x => String(x).trim()).filter(Boolean) : [],
  }));

  let dirty = false;
  function setDirty(on) {
    dirty = on;
    if (dirtyHint1) dirtyHint1.style.display = on ? "inline" : "none";
    if (dirtyHint2) dirtyHint2.style.display = on ? "inline" : "none";
  }

  function esc(s) {
    return String(s || "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
  }

  function oneLinePreview(text) {
    const t = String(text || "").replaceAll("\n", " ").trim();
    if (t.length <= 120) return t;
    return t.slice(0, 120) + "…";
  }

  function renderParagraphs() {
    const ids = Array.from(P.keys()).sort();
    const html = ids.map(id => {
      const p = P.get(id);
      const prev = esc(oneLinePreview(p.text));
      return `
        <div class="card section" data-pid="${esc(id)}" style="background:#fff;">
          <div style="display:flex; justify-content:space-between; gap:10px; align-items:flex-start;">
            <div style="flex:1; min-width:0;">
              <div style="display:flex; gap:10px; align-items:baseline; flex-wrap:wrap;">
                <strong>${esc(p.label)}</strong>
                <span class="muted">(${esc(p.id)})</span>
                ${p.description ? `<span class="muted">— ${esc(p.description)}</span>` : ``}
              </div>
              <div style="margin-top:8px; padding:10px 12px; border:1px solid #eee; border-radius:12px; background:#f7f7f7; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size:12px;">
                ${prev}
              </div>
            </div>
            <div class="inlineBtns">
              <button type="button" data-act="par-edit" data-pid="${esc(id)}">Edytuj</button>
              <button type="button" data-act="par-del" data-pid="${esc(id)}">Usuń</button>
            </div>
          </div>
        </div>
      `;
    }).join("");

    parListEl.innerHTML = html || `<div class="muted">Brak paragrafów.</div>`;
  }

  function renderReports() {
    const ids = Array.from(R.keys()).sort();
    const options = Array.from(P.keys()).sort().map(pid => `<option value="${esc(pid)}">${esc(pid)}</option>`).join("");

    const html = ids.map(id => {
      const r = R.get(id);
      const pills = r.paragraph_ids.map(pid => `<span class="pill" draggable="true" data-rid="${esc(id)}" data-pid="${esc(pid)}" style="cursor:grab;">${esc(pid)}</span>`).join(" ");
      return `
        <div class="card section" data-rid="${esc(id)}" style="background:#fff;">
          <div style="display:flex; justify-content:space-between; gap:10px; align-items:flex-start;">
            <div style="flex:1; min-width:0;">
              <div style="display:flex; gap:10px; align-items:baseline; flex-wrap:wrap;">
                <strong>${esc(r.title)}</strong>
                <span class="muted">(${esc(r.id)})</span>
              </div>

              <div class="muted" style="margin-top:6px;">Kolejność: przeciągnij “pill” albo dodaj poniżej.</div>

              <div style="margin-top:8px; display:flex; gap:8px; flex-wrap:wrap; padding:10px; border:1px solid #eee; border-radius:12px; background:#fafafa;"
                   data-dropzone="1" data-rid="${esc(id)}">
                ${pills || `<span class="muted">Brak paragrafów w raporcie.</span>`}
              </div>

              <div style="margin-top:10px; display:flex; gap:8px; align-items:flex-end;">
                <div style="flex:1;">
                  <label class="muted" style="margin:0 0 6px 0;">Dodaj paragraf</label>
                  <select data-addsel="1" data-rid="${esc(id)}">
                    <option value="">— wybierz —</option>
                    ${options}
                  </select>
                </div>
                <button type="button" data-act="rep-addpid" data-rid="${esc(id)}">Dodaj</button>
              </div>
            </div>

            <div class="inlineBtns">
              <button type="button" data-act="rep-edit" data-rid="${esc(id)}">Edytuj</button>
              <button type="button" data-act="rep-del" data-rid="${esc(id)}">Usuń</button>
            </div>
          </div>
        </div>
      `;
    }).join("");

    repListEl.innerHTML = html || `<div class="muted">Brak raportów.</div>`;
  }

  function refreshAll() {
    renderParagraphs();
    renderReports();
  }

  // ---------- Simple “modal” via prompt (prototype) ----------
  function editParagraph(pid) {
    const p = P.get(pid);
    if (!p) return;

    const idNew = prompt("ID paragrafu:", p.id);
    if (!idNew) return;

    const labelNew = prompt("Nazwa (label):", p.label) ?? p.label;
    const descNew = prompt("Opis (description):", p.description) ?? p.description;
    const textNew = prompt("Treść (text) — w tym prototypie to prompt (możesz wkleić):", p.text);
    if (textNew === null) return;

    const idNorm = String(idNew).trim();
    if (!idNorm) return;

    // rename key if needed
    if (idNorm !== pid && P.has(idNorm)) {
      alert("Taki ID już istnieje.");
      return;
    }

    P.delete(pid);
    P.set(idNorm, {
      id: idNorm,
      label: String(labelNew || idNorm).trim(),
      description: String(descNew || "").trim(),
      text: String(textNew || "").trim(),
    });

    // update references in reports
    R.forEach(r => {
      r.paragraph_ids = r.paragraph_ids.map(x => (x === pid ? idNorm : x));
    });

    setDirty(true);
    refreshAll();
  }

  function editReport(rid) {
    const r = R.get(rid);
    if (!r) return;

    const idNew = prompt("ID raportu:", r.id);
    if (!idNew) return;

    const titleNew = prompt("Tytuł:", r.title) ?? r.title;

    const idNorm = String(idNew).trim();
    if (!idNorm) return;

    if (idNorm !== rid && R.has(idNorm)) {
      alert("Taki ID raportu już istnieje.");
      return;
    }

    R.delete(rid);
    R.set(idNorm, { id: idNorm, title: String(titleNew || idNorm).trim(), paragraph_ids: Array.from(r.paragraph_ids) });

    setDirty(true);
    refreshAll();
  }

  function addParagraph() {
    const pid = prompt("Nowy paragraf ID:", "");
    if (!pid) return;
    const id = String(pid).trim();
    if (!id) return;
    if (P.has(id)) { alert("Taki ID już istnieje."); return; }

    const label = prompt("Nazwa (label):", id) ?? id;
    const desc = prompt("Opis (description):", "") ?? "";
    const text = prompt("Treść (text):", "");
    if (text === null) return;

    P.set(id, { id, label: String(label || id).trim(), description: String(desc || "").trim(), text: String(text || "").trim() });
    setDirty(true);
    refreshAll();
  }

  function addReport() {
    const rid = prompt("Nowy raport ID:", "");
    if (!rid) return;
    const id = String(rid).trim();
    if (!id) return;
    if (R.has(id)) { alert("Taki ID już istnieje."); return; }

    const title = prompt("Tytuł:", id) ?? id;
    R.set(id, { id, title: String(title || id).trim(), paragraph_ids: [] });
    setDirty(true);
    refreshAll();
  }

  // ---------- Actions ----------
  document.addEventListener("click", (e) => {
    const btn = e.target?.closest?.("button[data-act]");
    if (!btn) return;

    const act = btn.dataset.act;

    if (act === "par-edit") editParagraph(btn.dataset.pid);
    if (act === "par-del") {
      const pid = btn.dataset.pid;
      if (!confirm(`Usunąć paragraf ${pid}? (Usunie też referencje w raportach)`)) return;
      P.delete(pid);
      R.forEach(r => { r.paragraph_ids = r.paragraph_ids.filter(x => x !== pid); });
      setDirty(true);
      refreshAll();
    }

    if (act === "rep-edit") editReport(btn.dataset.rid);
    if (act === "rep-del") {
      const rid = btn.dataset.rid;
      if (!confirm(`Usunąć raport ${rid}?`)) return;
      R.delete(rid);
      setDirty(true);
      refreshAll();
    }

    if (act === "rep-addpid") {
      const rid = btn.dataset.rid;
      const sel = document.querySelector(`select[data-addsel="1"][data-rid="${CSS.escape(rid)}"]`);
      const pid = sel?.value || "";
      if (!pid) return;
      const r = R.get(rid);
      if (!r) return;
      r.paragraph_ids.push(pid);
      if (sel) sel.value = "";
      setDirty(true);
      refreshAll();
    }
  });

  btnParAdd?.addEventListener("click", addParagraph);
  btnRepAdd?.addEventListener("click", addReport);

  async function saveAll() {
    const paragraphs = Array.from(P.values()).sort((a,b) => a.id.localeCompare(b.id));
    const reports = Array.from(R.values()).sort((a,b) => a.id.localeCompare(b.id));
    const resp = await fetch("/api/templates/v2/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ paragraphs, reports }),
    });
    if (!resp.ok) {
      const txt = await resp.text();
      alert("Błąd zapisu: " + txt);
      return;
    }
    setDirty(false);
    alert("Zapisano templates.yaml");
    // odśwież by select raportów był spójny
    window.location.href = "/?tab=template";
  }

  btnSave1?.addEventListener("click", saveAll);
  btnSave2?.addEventListener("click", saveAll);

  // ---------- Drag & drop for report paragraph pills ----------
  let dragPid = null;
  document.addEventListener("dragstart", (e) => {
    const pill = e.target?.closest?.(".pill[data-pid][data-rid]");
    if (!pill) return;
    dragPid = pill.dataset.pid;
    e.dataTransfer?.setData("text/plain", dragPid || "");
  });

  document.addEventListener("dragover", (e) => {
    const dz = e.target?.closest?.('[data-dropzone="1"][data-rid]');
    if (!dz) return;
    e.preventDefault();
  });

  document.addEventListener("drop", (e) => {
    const dz = e.target?.closest?.('[data-dropzone="1"][data-rid]');
    if (!dz) return;
    e.preventDefault();

    const rid = dz.dataset.rid;
    const pid = dragPid || e.dataTransfer?.getData("text/plain") || "";
    dragPid = null;
    if (!rid || !pid) return;

    const r = R.get(rid);
    if (!r) return;

    // prosty model: przeniesienie na koniec (w prototypie). Jak chcesz precyzyjny insert -> robimy później.
    r.paragraph_ids = r.paragraph_ids.filter(x => x !== pid);
    r.paragraph_ids.push(pid);

    setDirty(true);
    refreshAll();
  });

  refreshAll();
}

// --------------------
document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initSettings();
  initTemplateEditor();
});
