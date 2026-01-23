// echo_desc/web/static/templates_ui.js
(function () {
  "use strict";

  window.initTemplateEditor = function initTemplateEditor() {
    const tplPanel = document.getElementById("tab-template");
    if (!tplPanel) return;

    // ---------- SUBTABS ----------
    const subBtns = Array.from(tplPanel.querySelectorAll(".subtabbtn[data-subtab]"));
    const subPanels = Array.from(tplPanel.querySelectorAll(".subpanel"));

    function activateSubtab(id) {
      subBtns.forEach((b) => b.classList.remove("active"));
      subPanels.forEach((p) => p.classList.remove("active"));
      const btn = subBtns.find((b) => b.dataset.subtab === id);
      const panel = document.getElementById(id);
      if (btn) btn.classList.add("active");
      if (panel) panel.classList.add("active");
    }

    subBtns.forEach((b) => b.addEventListener("click", () => activateSubtab(b.dataset.subtab)));

    // ---------- HOOKS ----------
    const parListEl = document.getElementById("paragraphList");
    const repListEl = document.getElementById("reportList");

    const btnParAdd = document.getElementById("btnParAdd");
    const btnRepAdd = document.getElementById("btnRepAdd");
    const btnSave1 = document.getElementById("btnTplSave1");
    const btnSave2 = document.getElementById("btnTplSave2");
    const dirtyHint1 = document.getElementById("tplDirty1");
    const dirtyHint2 = document.getElementById("tplDirty2");

    const parSearchEl = document.getElementById("tplParSearch"); // optional
    const repSearchEl = document.getElementById("tplRepSearch"); // optional

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

    (store.paragraphs || []).forEach((p) => {
      const id = String(p.id || "").trim();
      if (!id) return;
      P.set(id, {
        id,
        label: String(p.label || id).trim(),
        description: String(p.description || "").trim(),
        text: String(p.text || "").trim(),
      });
    });

    (store.reports || []).forEach((r) => {
      const id = String(r.id || "").trim();
      if (!id) return;
      R.set(id, {
        id,
        title: String(r.title || id).trim(),
        paragraph_ids: Array.isArray(r.paragraph_ids)
          ? r.paragraph_ids.map((x) => String(x).trim()).filter(Boolean)
          : [],
      });
    });

    // ---------- DIRTY ----------
    let dirty = false;
    function setDirty(on) {
      dirty = !!on;
      if (dirtyHint1) dirtyHint1.style.display = dirty ? "inline" : "none";
      if (dirtyHint2) dirtyHint2.style.display = dirty ? "inline" : "none";
    }

    // ---------- UI STATE ----------
    const ui = {
      openParId: null,     // string | null
      openRepId: null,     // string | null
      newParOpen: false,
      newRepOpen: false,
      draftPar: { id: "", label: "", description: "", text: "" },
      draftRep: { id: "", title: "", paragraph_ids: [] },
      filterPar: "",
      filterRep: "",
    };

    // ---------- HELPERS ----------
    const ID_RE = /^[a-zA-Z0-9_]+$/;

    function esc(s) {
      return String(s || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;");
    }

    function oneLinePreview(text) {
      const t = String(text || "").replaceAll("\n", " ").trim();
      return t.length <= 140 ? t : t.slice(0, 140) + "…";
    }

    function closestItem(el) {
      return el?.closest?.(".tplItem");
    }

    function setItemError(itemEl, msg) {
      const box = itemEl?.querySelector?.("[data-err]") || null;
      if (!box) return;
      if (!msg) {
        box.style.display = "none";
        box.textContent = "";
      } else {
        box.style.display = "block";
        box.textContent = String(msg);
      }
    }

    function readFields(itemEl, fields) {
      const out = {};
      for (const f of fields) {
        const el = itemEl.querySelector(`[data-field="${f}"]`);
        out[f] = el && "value" in el ? String(el.value || "").trim() : "";
      }
      return out;
    }

    function validateId(id) {
      if (!id) return "ID jest wymagane.";
      if (!ID_RE.test(id)) return "ID może mieć tylko litery/cyfry/_ (bez spacji).";
      return "";
    }

    function pillHtml(pid, rid) {
      return `
        <span class="pillBtn" draggable="true" data-rid="${esc(rid)}" data-pid="${esc(pid)}" title="Przeciągnij by zmienić kolejność">
          <span>${esc(pid)}</span>
          <span class="pillX" data-act="rep-rmpid" data-rid="${esc(rid)}" data-pid="${esc(pid)}" title="Usuń">×</span>
        </span>
      `;
    }

    // ---------- RENDER: Paragraph ----------
    function paragraphCardHtml(p, { editing = false, isNew = false } = {}) {
      const pid = p?.id || "";
      const label = p?.label || "";
      const desc = p?.description || "";
      const text = p?.text || "";

      const keyAttr = isNew ? `data-new="1"` : `data-pid="${esc(pid)}"`;
      const editClass = editing ? "1" : "0";

      return `
        <div class="tplItem" ${keyAttr} data-editing="${editClass}">
          <div class="tplRow">
            <div class="tplMeta">
              <div class="tplTitleLine">
                <span class="tplLabel">${esc(label || "(bez nazwy)")}</span>
                <span class="muted">(${esc(pid || "—")})</span>
                ${desc ? `<span class="muted">— ${esc(desc)}</span>` : ``}
              </div>
              <div class="tplPreview">${esc(oneLinePreview(text))}</div>
            </div>

            <div class="tplActions">
              ${isNew ? "" : `<button type="button" data-act="par-toggle">${editing ? "Zwiń" : "Edytuj"}</button>`}
              <button type="button" data-act="par-del">${isNew ? "Usuń szkic" : "Usuń"}</button>
            </div>
          </div>

          <div class="tplEditor" style="display:${editing ? "block" : "none"};">
            <div class="tplEditorGrid">
              <div>
                <label class="muted">ID</label>
                <input type="text" data-field="id" value="${esc(pid)}" placeholder="np. lv_dims" />
              </div>
              <div>
                <label class="muted">Nazwa (label)</label>
                <input type="text" data-field="label" value="${esc(label)}" placeholder="np. LV (LVEDD/LVST/LVPWT)" />
              </div>
              <div>
                <label class="muted">Opis (description)</label>
                <input type="text" data-field="description" value="${esc(desc)}" placeholder="" />
              </div>
            </div>

            <div class="tplEditorText">
              <label class="muted">Tekst</label>
              <textarea data-field="text" class="tplTextArea" placeholder="Treść paragrafu...">${esc(text)}</textarea>
            </div>

            <div class="inlineBtns section" style="margin-top:10px;">
              <button type="button" class="primaryBtn" data-act="par-save">Zapisz paragraf</button>
              <button type="button" data-act="par-cancel">Anuluj</button>
            </div>
            <div class="muted" data-err style="display:none; margin-top:8px; color:#b00020;"></div>
          </div>
        </div>
      `;
    }

    // ---------- RENDER: Report ----------
    function reportCardHtml(r, { editing = false, isNew = false } = {}) {
      const rid = r?.id || "";
      const title = r?.title || "";
      const pids = Array.isArray(r?.paragraph_ids) ? r.paragraph_ids : [];

      const keyAttr = isNew ? `data-new="1"` : `data-rid="${esc(rid)}"`;
      const editClass = editing ? "1" : "0";

      const options = Array.from(P.keys())
        .sort()
        .map((pid) => `<option value="${esc(pid)}">${esc(pid)}</option>`)
        .join("");

      const pills = pids.map((pid) => pillHtml(pid, rid)).join("");

      return `
        <div class="tplItem" ${keyAttr} data-editing="${editClass}">
          <div class="tplRow">
            <div class="tplMeta">
              <div class="tplTitleLine">
                <span class="tplLabel">${esc(title || "(bez tytułu)")}</span>
                <span class="muted">(${esc(rid || "—")})</span>
              </div>

              <div class="muted" style="margin-top:6px;">
                Kolejność: przeciągnij “pill” (prototyp: przenosi na koniec). Kliknij ×, żeby usunąć paragraf z raportu.
              </div>

              <div class="pills" data-dropzone="1" data-rid="${esc(rid)}">
                ${pills || `<span class="muted">Brak paragrafów w raporcie.</span>`}
              </div>

              <div class="addRow">
                <div style="flex:1;">
                  <label class="muted">Dodaj paragraf</label>
                  <select data-addsel="1" data-rid="${esc(rid)}">
                    <option value="">— wybierz —</option>
                    ${options}
                  </select>
                </div>
                <button type="button" data-act="rep-addpid" data-rid="${esc(rid)}">Dodaj</button>
              </div>
            </div>

            <div class="tplActions">
              ${isNew ? "" : `<button type="button" data-act="rep-toggle">${editing ? "Zwiń" : "Edytuj"}</button>`}
              <button type="button" data-act="rep-del">${isNew ? "Usuń szkic" : "Usuń"}</button>
            </div>
          </div>

          <div class="tplEditor" style="display:${editing ? "block" : "none"};">
            <div class="tplEditorGrid" style="grid-template-columns: 220px 1fr;">
              <div>
                <label class="muted">ID</label>
                <input type="text" data-field="id" value="${esc(rid)}" placeholder="np. default_echo" />
              </div>
              <div>
                <label class="muted">Tytuł (title)</label>
                <input type="text" data-field="title" value="${esc(title)}" placeholder="np. Domyślny (skrót)" />
              </div>
            </div>

            <div class="inlineBtns section" style="margin-top:10px;">
              <button type="button" class="primaryBtn" data-act="rep-save">Zapisz raport</button>
              <button type="button" data-act="rep-cancel">Anuluj</button>
            </div>
            <div class="muted" data-err style="display:none; margin-top:8px; color:#b00020;"></div>
          </div>
        </div>
      `;
    }

    function renderParagraphs() {
      const ids = Array.from(P.keys()).sort();

      const filter = (ui.filterPar || "").toLowerCase().trim();
      const list = filter
        ? ids.filter((id) => {
            const p = P.get(id);
            const hay = `${p.id} ${p.label} ${p.description} ${p.text}`.toLowerCase();
            return hay.includes(filter);
          })
        : ids;

      const htmlParts = [];

      if (ui.newParOpen) {
        htmlParts.push(paragraphCardHtml(ui.draftPar, { editing: true, isNew: true }));
      }

      for (const id of list) {
        const p = P.get(id);
        const editing = ui.openParId === id && !ui.newParOpen;
        htmlParts.push(paragraphCardHtml(p, { editing, isNew: false }));
      }

      parListEl.innerHTML = htmlParts.join("") || `<div class="muted">Brak paragrafów.</div>`;
    }

    function renderReports() {
      const ids = Array.from(R.keys()).sort();

      const filter = (ui.filterRep || "").toLowerCase().trim();
      const list = filter
        ? ids.filter((id) => {
            const r = R.get(id);
            const hay = `${r.id} ${r.title} ${(r.paragraph_ids || []).join(" ")}`.toLowerCase();
            return hay.includes(filter);
          })
        : ids;

      const htmlParts = [];

      if (ui.newRepOpen) {
        htmlParts.push(reportCardHtml(ui.draftRep, { editing: true, isNew: true }));
      }

      for (const id of list) {
        const r = R.get(id);
        const editing = ui.openRepId === id && !ui.newRepOpen;
        htmlParts.push(reportCardHtml(r, { editing, isNew: false }));
      }

      repListEl.innerHTML = htmlParts.join("") || `<div class="muted">Brak raportów.</div>`;
    }

    function refreshAll() {
      renderParagraphs();
      renderReports();
    }

    // ---------- ACTIONS: Paragraph ----------
    function openParagraphEditor(pid) {
      ui.newParOpen = false;
      ui.openParId = pid;
      renderParagraphs();
    }

    function openNewParagraphEditor() {
      ui.openParId = null;
      ui.newParOpen = true;
      ui.draftPar = { id: "", label: "", description: "", text: "" };
      renderParagraphs();
    }

    function cancelParagraphEdit() {
      ui.openParId = null;
      ui.newParOpen = false;
      renderParagraphs();
    }

    function deleteParagraph(pid) {
      if (!confirm(`Usunąć paragraf ${pid}? (Usunie też referencje w raportach)`)) return;
      P.delete(pid);
      R.forEach((r) => {
        r.paragraph_ids = r.paragraph_ids.filter((x) => x !== pid);
      });
      setDirty(true);
      refreshAll();
    }

    function saveParagraphFromItem(itemEl) {
      const isNew = itemEl.dataset.new === "1";
      const pidOld = isNew ? "" : String(itemEl.dataset.pid || "").trim();

      const { id, label, description, text } = readFields(itemEl, ["id", "label", "description", "text"]);

      const errId = validateId(id);
      if (errId) return setItemError(itemEl, errId);
      if (!text) return setItemError(itemEl, "Tekst paragrafu nie może być pusty.");

      if (id !== pidOld && P.has(id)) return setItemError(itemEl, "Taki ID paragrafu już istnieje.");

      // rename (if existing)
      if (!isNew && pidOld && pidOld !== id) {
        P.delete(pidOld);
        R.forEach((r) => {
          r.paragraph_ids = r.paragraph_ids.map((x) => (x === pidOld ? id : x));
        });
      }

      P.set(id, {
        id,
        label: label || id,
        description: description || "",
        text,
      });

      setItemError(itemEl, "");
      setDirty(true);

      // close editor
      ui.openParId = null;
      ui.newParOpen = false;

      // reports depend on paragraphs list + renamed ids
      refreshAll();
    }

    // ---------- ACTIONS: Report ----------
    function openReportEditor(rid) {
      ui.newRepOpen = false;
      ui.openRepId = rid;
      renderReports();
    }

    function openNewReportEditor() {
      ui.openRepId = null;
      ui.newRepOpen = true;
      ui.draftRep = { id: "", title: "", paragraph_ids: [] };
      renderReports();
    }

    function cancelReportEdit() {
      ui.openRepId = null;
      ui.newRepOpen = false;
      renderReports();
    }

    function deleteReport(rid) {
      if (!confirm(`Usunąć raport ${rid}?`)) return;
      R.delete(rid);
      setDirty(true);
      renderReports();
    }

    function saveReportFromItem(itemEl) {
      const isNew = itemEl.dataset.new === "1";
      const ridOld = isNew ? "" : String(itemEl.dataset.rid || "").trim();

      const { id, title } = readFields(itemEl, ["id", "title"]);
      const errId = validateId(id);
      if (errId) return setItemError(itemEl, errId);

      if (id !== ridOld && R.has(id)) return setItemError(itemEl, "Taki ID raportu już istnieje.");

      let paragraph_ids = [];
      if (!isNew && ridOld) {
        const r = R.get(ridOld);
        paragraph_ids = Array.isArray(r?.paragraph_ids) ? Array.from(r.paragraph_ids) : [];
      } else if (isNew) {
        paragraph_ids = Array.isArray(ui.draftRep.paragraph_ids) ? Array.from(ui.draftRep.paragraph_ids) : [];
      }

      if (!isNew && ridOld && ridOld !== id) {
        R.delete(ridOld);
      }

      R.set(id, {
        id,
        title: title || id,
        paragraph_ids,
      });

      setItemError(itemEl, "");
      setDirty(true);

      ui.openRepId = null;
      ui.newRepOpen = false;

      renderReports();
    }

    function addParagraphIdToReport(rid, pid) {
      if (!rid || !pid) return;

      // when draft report open -> modify draft
      if (ui.newRepOpen) {
        ui.draftRep.paragraph_ids = Array.isArray(ui.draftRep.paragraph_ids) ? ui.draftRep.paragraph_ids : [];
        ui.draftRep.paragraph_ids.push(pid);
        setDirty(true);
        renderReports();
        return;
      }

      const r = R.get(rid);
      if (!r) return;
      r.paragraph_ids.push(pid);
      setDirty(true);
      renderReports();
    }

    function removeParagraphIdFromReport(rid, pid) {
      if (ui.newRepOpen) {
        ui.draftRep.paragraph_ids = (ui.draftRep.paragraph_ids || []).filter((x) => x !== pid);
        setDirty(true);
        renderReports();
        return;
      }

      const r = R.get(rid);
      if (!r) return;
      r.paragraph_ids = r.paragraph_ids.filter((x) => x !== pid);
      setDirty(true);
      renderReports();
    }

    // ---------- EVENTS: local delegation (only template panel) ----------
    tplPanel.addEventListener("click", (e) => {
      const btn = e.target?.closest?.("[data-act]");
      if (!btn) return;

      const act = btn.dataset.act;
      const item = closestItem(btn);

      // Paragraph
      if (act === "par-toggle") {
        if (!item) return;
        const pid = String(item.dataset.pid || "").trim();
        openParagraphEditor(pid);
        return;
      }
      if (act === "par-save") {
        if (!item) return;
        saveParagraphFromItem(item);
        return;
      }
      if (act === "par-cancel") {
        cancelParagraphEdit();
        return;
      }
      if (act === "par-del") {
        if (!item) return;
        if (item.dataset.new === "1") {
          // drop draft
          ui.newParOpen = false;
          ui.draftPar = { id: "", label: "", description: "", text: "" };
          renderParagraphs();
          return;
        }
        const pid = String(item.dataset.pid || "").trim();
        deleteParagraph(pid);
        return;
      }

      // Report
      if (act === "rep-toggle") {
        if (!item) return;
        const rid = String(item.dataset.rid || "").trim();
        openReportEditor(rid);
        return;
      }
      if (act === "rep-save") {
        if (!item) return;
        saveReportFromItem(item);
        return;
      }
      if (act === "rep-cancel") {
        cancelReportEdit();
        return;
      }
      if (act === "rep-del") {
        if (!item) return;
        if (item.dataset.new === "1") {
          ui.newRepOpen = false;
          ui.draftRep = { id: "", title: "", paragraph_ids: [] };
          renderReports();
          return;
        }
        const rid = String(item.dataset.rid || "").trim();
        deleteReport(rid);
        return;
      }
      if (act === "rep-addpid") {
        const rid = btn.dataset.rid || item?.dataset?.rid || "";
        if (!rid && !ui.newRepOpen) return;

        const sel = tplPanel.querySelector(`select[data-addsel="1"][data-rid="${CSS.escape(rid)}"]`);
        const pid = String(sel?.value || "").trim();
        if (!pid) return;
        addParagraphIdToReport(rid, pid);
        if (sel) sel.value = "";
        return;
      }
      if (act === "rep-rmpid") {
        const rid = btn.dataset.rid;
        const pid = btn.dataset.pid;
        if (!rid || !pid) return;
        removeParagraphIdFromReport(rid, pid);
        return;
      }
    });

    // ---------- ADD BUTTONS ----------
    btnParAdd?.addEventListener("click", () => {
      activateSubtab("sub-paragraphs");
      openNewParagraphEditor();
    });

    btnRepAdd?.addEventListener("click", () => {
      activateSubtab("sub-reports");
      openNewReportEditor();
    });

    // ---------- SEARCH (optional) ----------
    parSearchEl?.addEventListener("input", () => {
      ui.filterPar = String(parSearchEl.value || "");
      renderParagraphs();
    });

    repSearchEl?.addEventListener("input", () => {
      ui.filterRep = String(repSearchEl.value || "");
      renderReports();
    });

    // ---------- SAVE ALL ----------
    async function saveAll() {
      // refuse if user has open draft editors with invalid/empty required data?
      // (we keep it permissive; you can still save global state even if draft exists, but it’s confusing)
      if (ui.newParOpen || ui.newRepOpen) {
        if (!confirm("Masz otwarty szkic (nowy paragraf/raport). Zapiszę tylko istniejące dane. Kontynuować?")) {
          return;
        }
      }

      const paragraphs = Array.from(P.values()).sort((a, b) => a.id.localeCompare(b.id));
      const reports = Array.from(R.values()).sort((a, b) => a.id.localeCompare(b.id));

      // quick client-side sanity: report refs exist
      const parSet = new Set(paragraphs.map((p) => p.id));
      for (const r of reports) {
        for (const pid of r.paragraph_ids) {
          if (!parSet.has(pid)) {
            alert(`Błąd: raport ${r.id} referencjonuje brakujący paragraf: ${pid}`);
            return;
          }
        }
      }

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

    tplPanel.addEventListener("dragstart", (e) => {
      const pill = e.target?.closest?.(".pillBtn[data-pid][data-rid]");
      if (!pill) return;
      dragPid = pill.dataset.pid;
      e.dataTransfer?.setData("text/plain", dragPid || "");
    });

    tplPanel.addEventListener("dragover", (e) => {
      const dz = e.target?.closest?.('[data-dropzone="1"][data-rid]');
      if (!dz) return;
      e.preventDefault();
    });

    tplPanel.addEventListener("drop", (e) => {
      const dz = e.target?.closest?.('[data-dropzone="1"][data-rid]');
      if (!dz) return;
      e.preventDefault();

      const rid = dz.dataset.rid;
      const pid = dragPid || e.dataTransfer?.getData("text/plain") || "";
      dragPid = null;
      if (!rid || !pid) return;

      // draft report?
      if (ui.newRepOpen) {
        ui.draftRep.paragraph_ids = (ui.draftRep.paragraph_ids || []).filter((x) => x !== pid);
        ui.draftRep.paragraph_ids.push(pid);
        setDirty(true);
        renderReports();
        return;
      }

      const r = R.get(rid);
      if (!r) return;

      r.paragraph_ids = r.paragraph_ids.filter((x) => x !== pid);
      r.paragraph_ids.push(pid);

      setDirty(true);
      renderReports();
    });

    // ---------- INIT ----------
    activateSubtab("sub-paragraphs");
    refreshAll();
  };
})();
