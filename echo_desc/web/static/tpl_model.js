// echo_desc/web/static/tpl_model.js
(function () {
  "use strict";

  function normStr(x) {
    return String(x == null ? "" : x).trim();
  }

  function normPidList(arr) {
    if (!Array.isArray(arr)) return [];
    return arr.map((x) => normStr(x)).filter(Boolean);
  }

  function cloneObj(o) {
    return JSON.parse(JSON.stringify(o || {}));
  }

  function createFromStore(store) {
    const P = new Map();
    const R = new Map();

    const paragraphs = Array.isArray(store?.paragraphs) ? store.paragraphs : [];
    const reports = Array.isArray(store?.reports) ? store.reports : [];

    for (const p of paragraphs) {
      if (!p || typeof p !== "object") continue;
      const id = normStr(p.id);
      if (!id) continue;
      P.set(id, {
        id,
        label: normStr(p.label) || id,
        description: normStr(p.description),
        text: String(p.text == null ? "" : p.text).trim(),
      });
    }

    for (const r of reports) {
      if (!r || typeof r !== "object") continue;
      const id = normStr(r.id);
      if (!id) continue;
      R.set(id, {
        id,
        title: normStr(r.title) || id,
        paragraph_ids: normPidList(r.paragraph_ids),
      });
    }

    // sanity: drop missing pids (UI can still show, but backend validate will catch)
    // We'll keep them (don't mutate) to avoid silent data loss. Up to you:
    // Here: keep as-is.

    return { P, R };
  }

  function serialize(P, R) {
    const paragraphs = Array.from(P.values()).map(cloneObj).sort((a, b) => a.id.localeCompare(b.id));
    const reports = Array.from(R.values()).map(cloneObj).sort((a, b) => a.id.localeCompare(b.id));
    return { paragraphs, reports };
  }

  // ---- Paragraph ops ----
  function upsertParagraph(P, R, p, pidOld /* optional */) {
    const id = normStr(p?.id);
    if (!id) throw new Error("paragraph id empty");
    const obj = {
      id,
      label: normStr(p?.label) || id,
      description: normStr(p?.description),
      text: String(p?.text == null ? "" : p.text).trim(),
    };

    if (pidOld && pidOld !== id) {
      // rename key + fix report refs
      if (P.has(id)) throw new Error("paragraph id exists");
      P.delete(pidOld);
      for (const r of R.values()) {
        r.paragraph_ids = r.paragraph_ids.map((x) => (x === pidOld ? id : x));
      }
    }

    P.set(id, obj);
  }

  function deleteParagraph(P, R, pid) {
    const id = normStr(pid);
    if (!id) return;
    P.delete(id);
    for (const r of R.values()) {
      r.paragraph_ids = r.paragraph_ids.filter((x) => x !== id);
    }
  }

  // ---- Report ops ----
  function upsertReport(R, r, ridOld /* optional */) {
    const id = normStr(r?.id);
    if (!id) throw new Error("report id empty");
    const obj = {
      id,
      title: normStr(r?.title) || id,
      paragraph_ids: normPidList(r?.paragraph_ids),
    };

    if (ridOld && ridOld !== id) {
      if (R.has(id)) throw new Error("report id exists");
      R.delete(ridOld);
    }
    R.set(id, obj);
  }

  function deleteReport(R, rid) {
    const id = normStr(rid);
    if (!id) return;
    R.delete(id);
  }

  function addPidToReport(R, rid, pid) {
    const r = R.get(normStr(rid));
    const p = normStr(pid);
    if (!r || !p) return;
    r.paragraph_ids.push(p);
  }

  function removePidFromReport(R, rid, pid) {
    const r = R.get(normStr(rid));
    const p = normStr(pid);
    if (!r || !p) return;
    r.paragraph_ids = r.paragraph_ids.filter((x) => x !== p);
  }

  function movePidToEnd(R, rid, pid) {
    const r = R.get(normStr(rid));
    const p = normStr(pid);
    if (!r || !p) return;
    r.paragraph_ids = r.paragraph_ids.filter((x) => x !== p);
    r.paragraph_ids.push(p);
  }

  window.TplModel = {
    createFromStore,
    serialize,
    upsertParagraph,
    deleteParagraph,
    upsertReport,
    deleteReport,
    addPidToReport,
    removePidFromReport,
    movePidToEnd,
    normStr,
    normPidList,
  };
})();
