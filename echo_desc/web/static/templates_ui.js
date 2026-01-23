// templates_ui.js (dopasowane do Twojego HTML)
(function () {
  "use strict";

  window.initTemplateEditor = function initTemplateEditor() {
    const tplPanel = document.getElementById("tab-template");
    if (!tplPanel) return;

    // ---------- SUBTABS ----------
    const subBtns = Array.from(tplPanel.querySelectorAll('.subtabbtn[data-subtab]'));
    const subPanels = Array.from(tplPanel.querySelectorAll(".subpanel"));

    function activateSubtab(id) {
      subBtns.forEach(b => b.classList.remove("active"));
      subPanels.forEach(p => p.classList.remove("active"));
      const btn = subBtns.find(b => b.dataset.subtab === id);
      const panel = document.getElementById(id);
      if (btn) btn.classList.add("active");
      if (panel) panel.classList.add("active");
    }

    subBtns.forEach(b => {
      b.addEventListener("click", () => activateSubtab(b.dataset.subtab));
    });

    // ---------- HOOKS ----------
    const parListEl = document.getElementById("paragraphList");
    const repListEl = document.getElementById("reportList");

    const btnParAdd = document.getElementById("btnParAdd");
    const btnRepAdd = document.getElementById("btnRepAdd");
    const btnSave1 = document.getElementById("btnTplSave1");
    const btnSave2 = document.getElementById("btnTplSave2");
    const dirtyHint1 = document.getElementById("tplDirty1");
    const dirtyHint2 = document.getElementById("tplDirty2");

    if (!parListEl || !repListEl) return;

    // ---------- LOAD DATA ----------
    let store = { paragraphs: [], reports: [] };
    try {
      const s = document.getElementById("tplData")?.textContent || "{}";
      store = JSON.parse(s);
    } catch (e) {
      console.warn("tplData JSON parse failed", e);
    }

    // P: id -> {id,label,description,text}
    // R: id -> {id,title,paragraph_ids:[]}
    const P = new Map();
    const R = new Map();

    (store.paragraphs || []).forEach(p => {
      const id = String(p.id || "").trim();
      if (!id) return;
      P.set(id, {
        id,
        label: String(p.label || id).trim(),
        description: String(p.description || "").trim(),
        text: String(p.text || "").trim(),
      });
    });

    (store.reports || []).forEach(r => {
      const id = String(r.id || "").trim();
      if (!id) return;
      R.set(id, {
        id,
        title: String(r.title || id).trim(),
        paragraph_ids: Array.isArray(r.paragraph_ids)
          ? r.paragraph_ids.map(x => String(x).trim()).filter(Boolean)
          : [],
      });
    });

    // ---------- DIRTY ----------
    let dirty = false;
    function setDirty(on) {
      dirty = on;
      if (dirtyHint1) dirtyHint1.style.display = on ? "inline" : "none";
      if (dirtyHint2) dirtyHint2.style.display = on ? "inline" : "none";
    }

    // ---------- RENDER HELPERS ----------
    function esc(s) {
      return String(s || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;");
    }

    function oneLinePreview(text) {
      const t = String(text || "").replaceAll("\n", " ").trim();
      return t.length <= 140 ? t : (t.slice(0, 140) + "…");
    }

    function renderParagraphs() {
      const ids = Array.from(P.keys()).sort();
      const html = ids.map(id => {
        const p = P.get(id);
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
                  ${esc(oneLinePreview(p.text))}
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
      const options = Array.from(P.keys()).sort()
        .map(pid => `<option value="${esc(pid)}">${esc(pid)}</option>`)
        .join("");

      const html = ids.map(id => {
        const r = R.get(id);
        const pills = r.paragraph_ids.map(pid =>
          `<span class="pill" draggable="true" data-rid="${esc(id)}" data-pid="${esc(pid)}" style="cursor:grab;">${esc(pid)}</span>`
        ).join(" ");

        return `
          <div class="card section" data-rid="${esc(id)}" style="background:#fff;">
            <div style="display:flex; justify-content:space-between; gap:10px; align-items:flex-start;">
              <div style="flex:1; min-width:0;">
                <div style="display:flex; gap:10px; align-items:baseline; flex-wrap:wrap;">
                  <strong>${esc(r.title)}</strong>
                  <span class="muted">(${esc(r.id)})</span>
                </div>

                <div class="muted" style="margin-top:6px;">Kolejność: przeciągnij “pill” (prototyp: przenosi na koniec).</div>

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

    // ---------- EDIT ACTIONS (prompt-only prototype) ----------
    function editParagraph(pid) {
      const p = P.get(pid);
      if (!p) return;

      const idNew = prompt("ID paragrafu:", p.id);
      if (!idNew) return;

      const labelNew = prompt("Nazwa (label):", p.label) ?? p.label;
      const descNew  = prompt("Opis (description):", p.description) ?? p.description;
      const textNew  = prompt("Treść (text):", p.text);
      if (textNew === null) return;

      const idNorm = String(idNew).trim();
      if (!idNorm) return;

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

      // update refs
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
      R.set(idNorm, {
        id: idNorm,
        title: String(titleNew || idNorm).trim(),
        paragraph_ids: Array.from(r.paragraph_ids),
      });

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
      const desc  = prompt("Opis (description):", "") ?? "";
      const text  = prompt("Treść (text):", "");
      if (text === null) return;

      P.set(id, {
        id,
        label: String(label || id).trim(),
        description: String(desc || "").trim(),
        text: String(text || "").trim(),
      });

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

    // ---------- CLICK DISPATCH ----------
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

    // ---------- SAVE ----------
    async function saveAll() {
      const paragraphs = Array.from(P.values()).sort((a, b) => a.id.localeCompare(b.id));
      const reports = Array.from(R.values()).sort((a, b) => a.id.localeCompare(b.id));

      const resp = await fetch("/api/templates/save", {
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
      window.location.href = "/?tab=template";
    }

    btnSave1?.addEventListener("click", saveAll);
    btnSave2?.addEventListener("click", saveAll);

    // ---------- DRAG & DROP (prototype: move to end) ----------
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

      r.paragraph_ids = r.paragraph_ids.filter(x => x !== pid);
      r.paragraph_ids.push(pid);

      setDirty(true);
      refreshAll();
    });

    // init
    activateSubtab("sub-paragraphs");
    refreshAll();
  };
})();
