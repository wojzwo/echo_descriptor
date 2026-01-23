// echo_desc/web/static/templates_ui.js
(function () {
  "use strict";

  const ID_RE = /^[a-zA-Z0-9_]+$/;

  function validateId(id) {
    if (!id) return "ID jest wymagane.";
    if (!ID_RE.test(id)) return "ID może mieć tylko litery/cyfry/_ (bez spacji).";
    return "";
  }

  function readFields(itemEl, fields) {
    const out = {};
    for (const f of fields) {
      const el = itemEl.querySelector(`[data-field="${f}"]`);
      out[f] = el && "value" in el ? String(el.value || "").trim() : "";
    }
    return out;
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

  window.initTemplateEditor = function initTemplateEditor() {
    const tplPanel = document.getElementById("tab-template");
    if (!tplPanel) return;

    if (!window.TplModel || !window.TplRender) {
      console.error("TplModel/TplRender missing. Check script include order.");
      return;
    }

    const { createFromStore, serialize, upsertParagraph, deleteParagraph, upsertReport, deleteReport, addPidToReport, removePidFromReport, movePidToEnd, normStr } =
      window.TplModel;

    const { paragraphCardHtml, reportCardHtml } = window.TplRender;

    // ---- subtabs
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

    // ---- hooks
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

    // ---- load store
    let store = { paragraphs: [], reports: [] };
    try {
      const s = document.getElementById("tplData")?.textContent || "{}";
      store = JSON.parse(s);
    } catch (e) {
      console.warn("tplData JSON parse failed", e);
    }

    const { P, R } = createFromStore(store);

    // ---- dirty
    let dirty = false;
    function setDirty(on) {
      dirty = !!on;
      if (dirtyHint1) dirtyHint1.style.display = dirty ? "inline" : "none";
      if (dirtyHint2) dirtyHint2.style.display = dirty ? "inline" : "none";
    }

    // ---- ui state
    const ui = {
      openParId: null,
      openRepId: null,
      newParOpen: false,
      newRepOpen: false,
      draftPar: { id: "", label: "", description: "", text: "" },
      draftRep: { id: "", title: "", paragraph_ids: [] },
      filterPar: "",
      filterRep: "",
    };

    function PkeysSorted() {
      return Array.from(P.keys()).sort();
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
      const pkeys = PkeysSorted();

      if (ui.newRepOpen) {
        htmlParts.push(reportCardHtml(ui.draftRep, pkeys, { editing: true, isNew: true }));
      }

      for (const id of list) {
        const r = R.get(id);
        const editing = ui.openRepId === id && !ui.newRepOpen;
        htmlParts.push(reportCardHtml(r, pkeys, { editing, isNew: false }));
      }

      repListEl.innerHTML = htmlParts.join("") || `<div class="muted">Brak raportów.</div>`;
    }

    function refreshAll() {
      renderParagraphs();
      renderReports();
    }

    // ---- actions: paragraph
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

    function doDeleteParagraph(pid) {
      if (!confirm(`Usunąć paragraf ${pid}? (Usunie też referencje w raportach)`)) return;
      deleteParagraph(P, R, pid);
      setDirty(true);
      refreshAll();
    }

    function saveParagraphFromItem(itemEl) {
      const isNew = itemEl.dataset.new === "1";
      const pidOld = isNew ? "" : normStr(itemEl.dataset.pid);

      const { id, label, description, text } = readFields(itemEl, ["id", "label", "description", "text"]);

      const errId = validateId(id);
      if (errId) return setItemError(itemEl, errId);
      if (!String(text || "").trim()) return setItemError(itemEl, "Tekst paragrafu nie może być pusty.");
      if (!String(label || "").trim()) return setItemError(itemEl, "Label nie może być pusty.");

      try {
        upsertParagraph(P, R, { id, label, description, text }, pidOld || null);
      } catch (e) {
        return setItemError(itemEl, String(e?.message || e));
      }

      setItemError(itemEl, "");
      setDirty(true);

      ui.openParId = null;
      ui.newParOpen = false;

      refreshAll(); // report selects + refs
    }

    // ---- actions: report
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

    function doDeleteReport(rid) {
      if (!confirm(`Usunąć raport ${rid}?`)) return;
      deleteReport(R, rid);
      setDirty(true);
      renderReports();
    }

    function saveReportFromItem(itemEl) {
      const isNew = itemEl.dataset.new === "1";
      const ridOld = isNew ? "" : normStr(itemEl.dataset.rid);

      const { id, title } = readFields(itemEl, ["id", "title"]);
      const errId = validateId(id);
      if (errId) return setItemError(itemEl, errId);
      if (!String(title || "").trim()) return setItemError(itemEl, "Tytuł nie może być pusty.");

      let paragraph_ids = [];
      if (!isNew && ridOld) {
        const r = R.get(ridOld);
        paragraph_ids = Array.isArray(r?.paragraph_ids) ? Array.from(r.paragraph_ids) : [];
      } else {
        paragraph_ids = Array.isArray(ui.draftRep.paragraph_ids) ? Array.from(ui.draftRep.paragraph_ids) : [];
      }

      try {
        upsertReport(R, { id, title, paragraph_ids }, ridOld || null);
      } catch (e) {
        return setItemError(itemEl, String(e?.message || e));
      }

      setItemError(itemEl, "");
      setDirty(true);

      ui.openRepId = null;
      ui.newRepOpen = false;

      renderReports();
    }

    function addParagraphToReport(rid, pid) {
      const p = normStr(pid);
      if (!p) return;

      if (ui.newRepOpen) {
        ui.draftRep.paragraph_ids = Array.isArray(ui.draftRep.paragraph_ids) ? ui.draftRep.paragraph_ids : [];
        ui.draftRep.paragraph_ids.push(p);
        setDirty(true);
        renderReports();
        return;
      }

      addPidToReport(R, rid, p);
      setDirty(true);
      renderReports();
    }

    function removeParagraphFromReport(rid, pid) {
      const p = normStr(pid);
      if (!p) return;

      if (ui.newRepOpen) {
        ui.draftRep.paragraph_ids = (ui.draftRep.paragraph_ids || []).filter((x) => x !== p);
        setDirty(true);
        renderReports();
        return;
      }

      removePidFromReport(R, rid, p);
      setDirty(true);
      renderReports();
    }

    // ---- events (delegation only inside template tab)
    function closestItem(el) {
      return el?.closest?.(".tplItem");
    }

    tplPanel.addEventListener("click", (e) => {
      const btn = e.target?.closest?.("[data-act]");
      if (!btn) return;

      const act = btn.dataset.act;
      const item = closestItem(btn);

      // Paragraph
      if (act === "par-toggle") {
        if (!item) return;
        openParagraphEditor(normStr(item.dataset.pid));
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
          ui.newParOpen = false;
          ui.draftPar = { id: "", label: "", description: "", text: "" };
          renderParagraphs();
          return;
        }
        doDeleteParagraph(normStr(item.dataset.pid));
        return;
      }

      // Report
      if (act === "rep-toggle") {
        if (!item) return;
        openReportEditor(normStr(item.dataset.rid));
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
        doDeleteReport(normStr(item.dataset.rid));
        return;
      }

      if (act === "rep-addpid") {
        const rid = btn.dataset.rid || item?.dataset?.rid || "";
        const sel = tplPanel.querySelector(`select[data-addsel="1"][data-rid="${CSS.escape(rid)}"]`);
        const pid = normStr(sel?.value);
        if (!pid) return;
        addParagraphToReport(rid, pid);
        if (sel) sel.value = "";
        return;
      }

      if (act === "rep-rmpid") {
        const rid = normStr(btn.dataset.rid);
        const pid = normStr(btn.dataset.pid);
        if (!rid || !pid) return;
        removeParagraphFromReport(rid, pid);
        return;
      }
    });

    // ---- add buttons
    btnParAdd?.addEventListener("click", () => {
      activateSubtab("sub-paragraphs");
      openNewParagraphEditor();
    });

    btnRepAdd?.addEventListener("click", () => {
      activateSubtab("sub-reports");
      openNewReportEditor();
    });

    // ---- search (optional)
    parSearchEl?.addEventListener("input", () => {
      ui.filterPar = String(parSearchEl.value || "");
      renderParagraphs();
    });

    repSearchEl?.addEventListener("input", () => {
      ui.filterRep = String(repSearchEl.value || "");
      renderReports();
    });

    // ---- save all
    async function saveAll() {
      if (ui.newParOpen || ui.newRepOpen) {
        if (!confirm("Masz otwarty szkic (nowy paragraf/raport). Zapiszę tylko istniejące dane. Kontynuować?")) return;
      }

      const payload = serialize(P, R);

      // quick client-side sanity: report refs exist
      const parSet = new Set(payload.paragraphs.map((p) => p.id));
      for (const r of payload.reports) {
        for (const pid of r.paragraph_ids || []) {
          if (!parSet.has(pid)) {
            alert(`Błąd: raport ${r.id} referencjonuje brakujący paragraf: ${pid}`);
            return;
          }
        }
      }

      const resp = await fetch("/api/templates/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
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

    // ---- drag & drop (move to end)
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

      const rid = normStr(dz.dataset.rid);
      const pid = normStr(dragPid || e.dataTransfer?.getData("text/plain") || "");
      dragPid = null;
      if (!rid || !pid) return;

      if (ui.newRepOpen) {
        ui.draftRep.paragraph_ids = (ui.draftRep.paragraph_ids || []).filter((x) => x !== pid);
        ui.draftRep.paragraph_ids.push(pid);
        setDirty(true);
        renderReports();
        return;
      }

      movePidToEnd(R, rid, pid);
      setDirty(true);
      renderReports();
    });

    // ---- init
    activateSubtab("sub-paragraphs");
    refreshAll();
  };
})();
