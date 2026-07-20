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


def upload_url_action(db, body, name):
    """Kursant öz faylı üçün presigned PUT URL alır. (changed, resp, status)"""
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
