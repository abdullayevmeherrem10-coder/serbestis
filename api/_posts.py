# -*- coding: utf-8 -*-
"""Elanlar və materiallar — müəllim paylaşır (elan / tapşırıq / mühazirə), kursant kabinetində görür.

db["posts"] = [ {id, type, title, text, team ("" = hamı), deadline, ts, ts_epoch,
                 file: {key, kind, fname, size} | None}, ... ]  — ən yenisi əvvəldə, ən çoxu POSTS_MAX.

Fayl əlavəsi kursant faylları kimi B2-yə presigned PUT ilə birbaşa gedir
(post-file-url → PUT → post-file-confirm: ölçü + magic yoxlanışı). Açar: posts/<id><ext>.
docx/pptx makrosuz formatlardır; pdf brauzerdə yeni vərəqdə açılır (viewer iframe yalnız Office üçündür).
"""
import secrets
import time

import _b2

POSTS_MAX = 60
POST_TYPES = ("elan", "tapsiriq", "muhazire")

POST_FILE_KINDS = {
    "docx": {"ext": ".docx", "max": 20 * 1024 * 1024, "magic": b"PK",
             "ct": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    "pptx": {"ext": ".pptx", "max": 50 * 1024 * 1024, "magic": b"PK",
             "ct": "application/vnd.openxmlformats-officedocument.presentationml.presentation"},
    "pdf": {"ext": ".pdf", "max": 30 * 1024 * 1024, "magic": b"%PDF",
            "ct": "application/pdf"},
}


def _posts(db):
    return db.setdefault("posts", [])


def _find(db, pid):
    for p in _posts(db):
        if p.get("id") == pid:
            return p
    return None


def _public(p):
    """Kursanta/müəllimə göndərilən nüsxə — B2 açarı gizlədilir."""
    out = {k: v for k, v in p.items() if k != "file"}
    f = p.get("file")
    out["file"] = {"kind": f.get("kind"), "fname": f.get("fname"), "size": f.get("size")} if f else None
    return out


def _visible(p, role, team):
    return role == "teacher" or not p.get("team") or p.get("team") == team


def posts_for(db, role, team):
    return [_public(p) for p in _posts(db) if _visible(p, role, team)]


def post_save_action(db, body):
    """Müəllim yeni paylaşım yaradır. (changed, resp, status)"""
    ptype = (body.get("type") or "elan").strip()
    if ptype not in POST_TYPES:
        return False, {"error": "Paylaşım növü yanlışdır."}, 400
    title = (body.get("title") or "").strip()[:120]
    text = (body.get("text") or "").strip()[:4000]
    if not title:
        return False, {"error": "Başlıq boş ola bilməz."}, 400
    team = (body.get("team") or "").strip()
    if team and team not in db.get("teams", {}):
        return False, {"error": "Taqım tapılmadı."}, 400
    deadline = (body.get("deadline") or "").strip()[:40]
    pid = time.strftime("%Y%m%d%H%M%S") + secrets.token_hex(3)
    post = {
        "id": pid, "type": ptype, "title": title, "text": text, "team": team,
        "deadline": deadline, "ts": time.strftime("%d.%m.%Y %H:%M"), "ts_epoch": int(time.time()),
        "file": None,
    }
    lst = _posts(db)
    lst.insert(0, post)
    for old in lst[POSTS_MAX:]:
        if old.get("file"):
            _b2.delete_object(old["file"]["key"])
    del lst[POSTS_MAX:]
    return True, {"success": True, "post": _public(post)}, 200


def post_delete_action(db, body):
    pid = (body.get("id") or "").strip()
    p = _find(db, pid)
    if not p:
        return False, {"error": "Paylaşım tapılmadı."}, 404
    if p.get("file"):
        _b2.delete_object(p["file"]["key"])
    _posts(db).remove(p)
    return True, {"success": True}, 200


def _spec_for(body):
    kind = (body.get("kind") or "").strip().lower()
    spec = POST_FILE_KINDS.get(kind)
    return kind, spec


def post_file_url_action(db, body):
    """Müəllim paylaşıma fayl əlavə etmək üçün presigned PUT alır."""
    if not _b2.is_configured():
        return False, {"error": "Fayl anbarı konfiqurasiya olunmayıb."}, 503
    p = _find(db, (body.get("id") or "").strip())
    if not p:
        return False, {"error": "Paylaşım tapılmadı."}, 404
    kind, spec = _spec_for(body)
    if not spec:
        return False, {"error": "Yalnız .docx, .pptx və .pdf faylı qəbul edilir."}, 400
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
    key = f"{_b2.key_prefix()}posts/{p['id']}{spec['ext']}"
    return False, {"url": _b2.presign_put(key, spec["ct"], expires=900), "key": key}, 200


def post_file_confirm_action(db, body):
    if not _b2.is_configured():
        return False, {"error": "Fayl anbarı konfiqurasiya olunmayıb."}, 503
    p = _find(db, (body.get("id") or "").strip())
    if not p:
        return False, {"error": "Paylaşım tapılmadı."}, 404
    kind, spec = _spec_for(body)
    if not spec:
        return False, {"error": "Fayl növü yanlışdır."}, 400
    key = f"{_b2.key_prefix()}posts/{p['id']}{spec['ext']}"
    size, ok = _b2.head_object(key)
    if not ok:
        return False, {"error": "Fayl anbarda tapılmadı — yükləmə tamamlanmayıb."}, 400
    if size > spec["max"]:
        _b2.delete_object(key)
        return False, {"error": f"Fayl {spec['max'] // (1024 * 1024)} MB limitini aşır — silindi."}, 400
    magic = _b2.read_head_bytes(key, len(spec["magic"]))
    if magic != spec["magic"]:
        _b2.delete_object(key)
        return False, {"error": f"Fayl həqiqi {spec['ext']} sənədi deyil — silindi."}, 400
    old = p.get("file")
    if old and old.get("key") != key:
        _b2.delete_object(old["key"])
    fname = (body.get("fname") or "").strip()[:120] or f"material{spec['ext']}"
    p["file"] = {"key": key, "kind": kind, "fname": fname, "size": size}
    return True, {"success": True, "post": _public(p)}, 200


def post_file_link_action(db, body, role, team):
    """Baxış / endirmə üçün presigned GET — yalnız görə bildiyi paylaşım."""
    if not _b2.is_configured():
        return False, {"error": "Fayl anbarı konfiqurasiya olunmayıb."}, 503
    p = _find(db, (body.get("id") or "").strip())
    if not p or not _visible(p, role, team) or not p.get("file"):
        return False, {"error": "Fayl tapılmadı."}, 404
    f = p["file"]
    spec = POST_FILE_KINDS.get(f.get("kind")) or POST_FILE_KINDS["pdf"]
    inline = (body.get("mode") or "view") == "view"
    url = _b2.presign_get(f["key"], expires=3600, filename=f.get("fname") or f"material{spec['ext']}",
                          content_type=spec["ct"], inline=inline)
    return False, {"url": url, "fname": f.get("fname"), "kind": f.get("kind"), "size": f.get("size")}, 200
