# -*- coding: utf-8 -*-
"""Kursant sərbəst iş fayllarının (docx + pptx) B2-yə yüklənməsi.

Axın: /api/upload-url → brauzer presigned PUT ilə birbaşa B2-yə yükləyir →
/api/upload-confirm serverdə ölçü + ZIP (PK) magic yoxlanışından sonra
metadata db["uploads"][ad][növ]-də saxlanılır. Baxış/endirmə presigned GET.

Yalnız .docx/.pptx qəbul edilir — bu formatlarda makro işləyə bilmir
(makrolular .docm/.pptm-dir), ona görə viruslu kompüterdən gələn fayl
müəllim üçün təhlükə yaratmır; üstəlik baxış saytda, endirmədən gedir.
"""
import hashlib
import time

import _b2
import _vt

KINDS = {
    "docx": {
        "ext": ".docx",
        "max": 10 * 1024 * 1024,
        "ct": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "label": "Word sənədi",
    },
    "pptx": {
        "ext": ".pptx",
        "max": 25 * 1024 * 1024,
        "ct": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "label": "Təqdimat",
    },
}


def _key_for(db, name, kind):
    existing = db.get("uploads", {}).get(name, {}).get(kind)
    if existing and existing.get("key"):
        return existing["key"]
    h = hashlib.sha256(name.encode("utf-8")).hexdigest()[:16]
    return f"{_b2.key_prefix()}uploads/{h}-{kind}{KINDS[kind]['ext']}"


def _student_in_teams(db, name):
    return any(name in members for members in db.get("teams", {}).values())


# Word (docx) elektron qəbul edilmir — Tədris şöbəsi ilə razılaşdırılmayıb; iş çap olunub müəllimə təqdim edilir.
# Təqdimat (pptx) sistemlə təhvil verilir. Razılıq alınsa True edin (frontend: DOCX_ONLINE).
DOCX_ONLINE = False


def upload_url_action(db, body, name):
    """Kursant öz faylı üçün presigned PUT URL alır. (changed, resp, status)"""
    if (body.get("kind") or "") == "docx" and not DOCX_ONLINE:
        return False, {"error": "Mətn (Word) variantı elektron qəbul edilmir — çap olunaraq fənn müəlliminə təqdim edilməlidir."}, 403
    if not _b2.is_configured():
        return False, {"error": "Fayl anbarı konfiqurasiya olunmayıb."}, 503
    kind = body.get("kind") or ""
    if kind not in KINDS:
        return False, {"error": "Fayl növü yanlışdır."}, 400
    spec = KINDS[kind]
    fname = (body.get("fname") or "").strip()[:120]
    if not fname.lower().endswith(spec["ext"]):
        return False, {"error": f"Yalnız {spec['ext']} faylı qəbul edilir."}, 400
    try:
        size = int(body.get("size"))
    except (TypeError, ValueError):
        return False, {"error": "Fayl ölçüsü göstərilməyib."}, 400
    if size <= 0:
        return False, {"error": "Fayl boşdur."}, 400
    if size > spec["max"]:
        return False, {"error": f"Fayl {spec['max'] // (1024 * 1024)} MB-dan böyük ola bilməz."}, 400
    key = _key_for(db, name, kind)
    url = _b2.presign_put(key, spec["ct"], expires=900)
    return False, {"url": url, "key": key}, 200


def upload_confirm_action(db, body, name):
    """Yükləmə bitdikdən sonra faylı yoxlayıb metadata-nı yazır."""
    if not _b2.is_configured():
        return False, {"error": "Fayl anbarı konfiqurasiya olunmayıb."}, 503
    kind = body.get("kind") or ""
    if kind not in KINDS:
        return False, {"error": "Fayl növü yanlışdır."}, 400
    spec = KINDS[kind]
    fname = (body.get("fname") or "").strip()[:120] or f"serbest-is{spec['ext']}"
    key = _key_for(db, name, kind)
    size, ok = _b2.head_object(key)
    if not ok:
        return False, {"error": "Fayl anbarda tapılmadı — yükləmə tamamlanmayıb."}, 400
    if size > spec["max"]:
        _b2.delete_object(key)
        return False, {"error": f"Fayl {spec['max'] // (1024 * 1024)} MB limitini aşır — silindi."}, 400
    magic = _b2.read_head_bytes(key, 2)
    if magic != b"PK":
        _b2.delete_object(key)
        return False, {"error": f"Fayl həqiqi {spec['ext']} sənədi deyil — silindi."}, 400
    up = db.setdefault("uploads", {}).setdefault(name, {})
    up[kind] = {
        "key": key,
        "fname": fname,
        "size": size,
        "ts": time.strftime("%d.%m.%Y %H:%M"),
    }
    return True, {"success": True, "uploads": up}, 200


def upload_link_action(db, body, role, requester_name):
    """Baxış (saytda viewer) və ya endirmə üçün presigned GET URL."""
    if not _b2.is_configured():
        return False, {"error": "Fayl anbarı konfiqurasiya olunmayıb."}, 503
    kind = body.get("kind") or ""
    if kind not in KINDS:
        return False, {"error": "Fayl növü yanlışdır."}, 400
    name = (body.get("name") or "").strip() or requester_name
    if role != "teacher" and name != requester_name:
        return False, {"error": "İcazə yoxdur."}, 403
    meta = db.get("uploads", {}).get(name, {}).get(kind)
    if not meta:
        return False, {"error": "Fayl hələ yüklənməyib."}, 404
    spec = KINDS[kind]
    inline = (body.get("mode") or "view") == "view"
    url = _b2.presign_get(
        meta["key"],
        expires=3600,
        filename=meta.get("fname") or f"serbest-is{spec['ext']}",
        content_type=spec["ct"],
        inline=inline,
    )
    return False, {"url": url, "fname": meta.get("fname"), "size": meta.get("size")}, 200


def vt_check_action(db, body, role, requester_name):
    """Faylı VirusTotal-a göndərir — yalnız müəllim, öz panelindən."""
    if role != "teacher":
        return False, {"error": "İcazə yoxdur."}, 403
    if not _vt.is_configured():
        return False, {"error": "Virus yoxlanışı konfiqurasiya olunmayıb."}, 503
    kind = body.get("kind") or ""
    if kind not in KINDS:
        return False, {"error": "Fayl növü yanlışdır."}, 400
    name = (body.get("name") or "").strip()
    if not name:
        return False, {"error": "Kursant adı göstərilməyib."}, 400
    meta = db.get("uploads", {}).get(name, {}).get(kind)
    if not meta:
        return False, {"error": "Fayl hələ yüklənməyib."}, 404
    data = _b2.read_object(meta["key"])
    if data is None:
        return False, {"error": "Fayl anbardan oxuna bilmədi."}, 502
    aid = _vt.scan_bytes(data, meta.get("fname") or f"file{KINDS[kind]['ext']}")
    if not aid:
        # VT limiti/xətası — statusu dəyişmirik, sonra yenidən cəhd etmək olar
        return False, {"error": "VirusTotal hazırda qəbul etmir — bir azdan yenidən cəhd edin."}, 502
    meta["vt"] = {"id": aid, "status": "pending"}
    return True, {"success": True, "vt": meta["vt"]}, 200


def vt_status_action(db, body, role, requester_name):
    """VT nəticəsini soruşur; hazırdırsa metadata-da saxlayır — yalnız müəllim."""
    if role != "teacher":
        return False, {"error": "İcazə yoxdur."}, 403
    kind = body.get("kind") or ""
    if kind not in KINDS:
        return False, {"error": "Fayl növü yanlışdır."}, 400
    name = (body.get("name") or "").strip()
    if not name:
        return False, {"error": "Kursant adı göstərilməyib."}, 400
    meta = db.get("uploads", {}).get(name, {}).get(kind)
    if not meta:
        return False, {"error": "Fayl tapılmadı."}, 404
    vt = meta.get("vt")
    if not vt:
        return False, {"vt": None}, 200
    if vt.get("status") != "pending":
        return False, {"vt": vt}, 200
    res = _vt.get_analysis(vt.get("id"))
    if not res or res.get("status") != "completed":
        return False, {"vt": vt}, 200
    flagged = (res["malicious"] + res["suspicious"]) > 0
    vt.update({
        "status": "flagged" if flagged else "clean",
        "malicious": res["malicious"],
        "suspicious": res["suspicious"],
        "ts": time.strftime("%d.%m.%Y %H:%M"),
    })
    return True, {"vt": vt}, 200


def upload_review_action(db, body, role, requester_name):
    """Müəllim fayla rəy qoyur: accepted / revise (+qısa qeyd); boş status rəyi silir."""
    if role != "teacher":
        return False, {"error": "İcazə yoxdur."}, 403
    kind = body.get("kind") or ""
    if kind not in KINDS:
        return False, {"error": "Fayl növü yanlışdır."}, 400
    name = (body.get("name") or "").strip()
    if not name:
        return False, {"error": "Kursant adı göstərilməyib."}, 400
    meta = db.get("uploads", {}).get(name, {}).get(kind)
    if not meta:
        return False, {"error": "Fayl tapılmadı."}, 404
    status = body.get("status") or ""
    if status and status not in ("accepted", "revise"):
        return False, {"error": "Status yanlışdır."}, 400
    if not status:
        meta.pop("review", None)
    else:
        meta["review"] = {
            "status": status,
            "note": (body.get("note") or "").strip()[:300],
            "ts": time.strftime("%d.%m.%Y %H:%M"),
        }
    return True, {"success": True, "review": meta.get("review")}, 200


def upload_delete_action(db, body, role, requester_name):
    """Kursant öz faylını, müəllim istənilən faylı silir."""
    kind = body.get("kind") or ""
    if kind not in KINDS:
        return False, {"error": "Fayl növü yanlışdır."}, 400
    name = (body.get("name") or "").strip() or requester_name
    if role != "teacher" and name != requester_name:
        return False, {"error": "İcazə yoxdur."}, 403
    meta = db.get("uploads", {}).get(name, {}).get(kind)
    if not meta:
        return False, {"error": "Fayl tapılmadı."}, 404
    _b2.delete_object(meta["key"])
    db["uploads"][name].pop(kind, None)
    if not db["uploads"][name]:
        db["uploads"].pop(name, None)
    return True, {"success": True, "uploads": db.get("uploads", {}).get(name, {})}, 200


# ===== Fayl arxivi (müəllim): semestr sonunda faylları B2-də arxiv qovluğuna köçür / həmişəlik sil =====
# db["file_arxiv"] = [ {id, label, ts, files: [{name, kind, key, fname, size, ts, review?}]}, ... ]
# Köçürmə/silmə hissə-hissə (limit) gedir — Vercel funksiyasının 60 s vaxtına sığmaq üçün;
# brauzer "remaining" 0 olana qədər təkrar çağırır.
ARXIV_BATCH_LIMIT = 15


def _arxiv_batches(db):
    return db.setdefault("file_arxiv", [])


def _arxiv_find(db, bid):
    for b in _arxiv_batches(db):
        if b.get("id") == bid:
            return b
    return None


def _arxiv_summary(db):
    cur_n, cur_sz = 0, 0
    for kinds in db.get("uploads", {}).values():
        for m in kinds.values():
            cur_n += 1
            cur_sz += int(m.get("size") or 0)
    batches = []
    for b in _arxiv_batches(db):
        files = b.get("files", [])
        batches.append({
            "id": b["id"], "label": b.get("label", ""), "ts": b.get("ts", ""),
            "count": len(files), "size": sum(int(f.get("size") or 0) for f in files),
            "files": [{"i": i, "name": f.get("name"), "kind": f.get("kind"), "fname": f.get("fname"),
                       "size": f.get("size"), "ts": f.get("ts")} for i, f in enumerate(files)],
        })
    return {"current": {"count": cur_n, "size": cur_sz}, "batches": batches}


def upload_arxiv_action(db, body, role, requester_name):
    """Yalnız müəllim. op: list | move | link | delete."""
    if role != "teacher":
        return False, {"error": "İcazə yoxdur."}, 401
    op = body.get("op") or "list"
    if op == "list":
        return False, _arxiv_summary(db), 200
    if not _b2.is_configured():
        return False, {"error": "Fayl anbarı konfiqurasiya olunmayıb."}, 503
    try:
        limit = max(1, min(int(body.get("limit") or ARXIV_BATCH_LIMIT), 50))
    except (TypeError, ValueError):
        limit = ARXIV_BATCH_LIMIT

    if op == "move":
        # Cari faylları arxiv partiyasına köçür (kopyala + orijinalı sil); partiya id-si davam etdirilə bilər
        bid = (body.get("batch") or "").strip()
        batch = _arxiv_find(db, bid) if bid else None
        if not batch:
            bid = time.strftime("%Y%m%d-%H%M%S")
            batch = {"id": bid, "label": (body.get("label") or "").strip()[:80],
                     "ts": time.strftime("%d.%m.%Y %H:%M"), "files": []}
            _arxiv_batches(db).insert(0, batch)
        moved, failed = 0, 0
        ups = db.get("uploads", {})
        for name in list(ups.keys()):
            if moved + failed >= limit:
                break
            for kind in list(ups[name].keys()):
                if moved + failed >= limit:
                    break
                meta = ups[name][kind]
                src = meta.get("key")
                dst = f"{_b2.key_prefix()}arxiv/{bid}/{src.rsplit('/', 1)[-1]}" if src else None
                if not src or not _b2.copy_object(src, dst):
                    failed += 1
                    continue
                _b2.delete_object(src)
                batch["files"].append({
                    "name": name, "kind": kind, "key": dst, "fname": meta.get("fname"),
                    "size": meta.get("size"), "ts": meta.get("ts"), "review": meta.get("review"),
                })
                ups[name].pop(kind, None)
                moved += 1
            if not ups.get(name):
                ups.pop(name, None)
        remaining = sum(len(k) for k in ups.values())
        if not batch["files"] and remaining == 0 and moved == 0:
            _arxiv_batches(db).remove(batch)
            return True, {"success": True, "batch": None, "moved": 0, "failed": failed, "remaining": 0}, 200
        return True, {"success": True, "batch": bid, "moved": moved, "failed": failed,
                      "remaining": remaining, "total": len(batch["files"])}, 200

    if op == "link":
        batch = _arxiv_find(db, (body.get("batch") or "").strip())
        try:
            f = batch["files"][int(body.get("i"))] if batch else None
        except (TypeError, ValueError, IndexError):
            f = None
        if not f:
            return False, {"error": "Fayl tapılmadı."}, 404
        spec = KINDS.get(f.get("kind")) or KINDS["docx"]
        url = _b2.presign_get(f["key"], expires=3600, filename=f.get("fname") or f"serbest-is{spec['ext']}",
                              content_type=spec["ct"], inline=False)
        return False, {"url": url, "fname": f.get("fname"), "size": f.get("size")}, 200

    if op == "delete":
        # Arxiv partiyasını həmişəlik sil (B2-dən də) — hissə-hissə
        batch = _arxiv_find(db, (body.get("batch") or "").strip())
        if not batch:
            return False, {"error": "Arxiv partiyası tapılmadı."}, 404
        deleted, failed = 0, 0
        keep = []
        for f in batch["files"]:
            if deleted + failed >= limit:
                keep.append(f)
            elif _b2.delete_object(f.get("key") or ""):
                deleted += 1
            else:
                failed += 1
                keep.append(f)
        batch["files"] = keep
        remaining = len(keep)
        if remaining == 0:
            _arxiv_batches(db).remove(batch)
        return True, {"success": True, "deleted": deleted, "failed": failed, "remaining": remaining}, 200

    return False, {"error": "Əməliyyat yanlışdır."}, 400
