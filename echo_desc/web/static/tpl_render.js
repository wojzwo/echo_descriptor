// echo_desc/web/static/tpl_render.js
(function () {
  "use strict";

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

  function pillHtml(pid, rid) {
    return `
      <span class="pillBtn" draggable="true" data-rid="${esc(rid)}" data-pid="${esc(pid)}" title="Przeciągnij by zmienić kolejność">
        <span>${esc(pid)}</span>
        <span class="pillX" data-act="rep-rmpid" data-rid="${esc(rid)}" data-pid="${esc(pid)}" title="Usuń">×</span>
      </span>
    `;
  }

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

  function reportCardHtml(r, PkeysSorted, { editing = false, isNew = false } = {}) {
    const rid = r?.id || "";
    const title = r?.title || "";
    const pids = Array.isArray(r?.paragraph_ids) ? r.paragraph_ids : [];

    const keyAttr = isNew ? `data-new="1"` : `data-rid="${esc(rid)}"`;
    const editClass = editing ? "1" : "0";

    const options = (PkeysSorted || [])
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

  window.TplRender = {
    esc,
    oneLinePreview,
    paragraphCardHtml,
    reportCardHtml,
  };
})();
