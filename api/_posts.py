# -*- coding: utf-8 -*-
"""Elanlar və materiallar — müəllim paylaşır (elan / tapşırıq / mühazirə), kursant kabinetində görür.

db["posts"] = [ {id, type, title, text, teams ([] = hamı), deadline, ts, ts_epoch, edited?,
                 files: [ {fid, key, kind, fname, size}, ... ]}, ... ]  — ən yenisi əvvəldə, ən çoxu POSTS_MAX.
(Köhnə qeydlərdə tək "file" sahəsi ola bilər — _files_of() onu siyahıya çevirir.)

Fayl əlavəsi kursant faylları kimi B2-yə presigned PUT ilə birbaşa gedir
(post-file-url → PUT → post-file-confirm: yalnız ölçü yoxlanışı, məzmun yoxlanmır — müəllimin öz faylıdır). Açar: posts/<id>-<fid><ext>.
Bir paylaşıma ən çoxu POST_FILES_MAX fayl. docx/pptx makrosuz formatlardır, .doc yalnız müəllimdən gəlir;
pdf brauzerdə yeni vərəqdə açılır (viewer iframe yalnız Office üçündür).
"""
import re
import secrets
import time

import _b2

POSTS_MAX = 60
POST_FILES_MAX = 10
POST_TYPES = ("elan", "tapsiriq", "muhazire")
_FID_RE = re.compile(r"^[0-9a-f]{8}$")

POST_FILE_KINDS = {
    "docx": {"ext": ".docx", "max": 30 * 1024 * 1024, "magic": b"PK",
             "ct": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    # .doc (köhnə Word, OLE konteyner) — müəllimin öz faylıdır; kursant saytda Office viewer ilə baxır
    "doc": {"ext": ".doc", "max": 30 * 1024 * 1024, "magic": bytes([0xD0, 0xCF, 0x11, 0xE0]),
            "ct": "application/msword"},
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


def _files_of(p):
    """Fayl siyahısı; köhnə tək "file" sahəsi siyahıya çevrilir (fid "main")."""
    if p.get("files") is None:
        f = p.pop("file", None)
        p["files"] = [dict(f, fid="main")] if f else []
    return p["files"]


def _teams_of(p):
    """Hədəf taqımlar; köhnə qeydlərdə tək "team" sahəsi ola bilər."""
    t = p.get("teams")
    if t is None:
        t = [p["team"]] if p.get("team") else []
    return t


def _public(p):
    """Kursanta/müəllimə göndərilən nüsxə — B2 açarları gizlədilir."""
    out = {k: v for k, v in p.items() if k not in ("file", "files", "team")}
    out["teams"] = _teams_of(p)
    out["files"] = [{"fid": f.get("fid"), "kind": f.get("kind"), "fname": f.get("fname"), "size": f.get("size")}
                    for f in _files_of(p)]
    return out


def _visible(p, role, team):
    return role == "teacher" or not _teams_of(p) or team in _teams_of(p)


def _delete_files(p):
    for f in _files_of(p):
        if f.get("key"):
            _b2.delete_object(f["key"])


def posts_for(db, role, team):
    return [_public(p) for p in _posts(db) if _visible(p, role, team)]


def _fields(db, body):
    """Paylaşım sahələrini yoxlayır: (dict, None) və ya (None, xəta_mətni)."""
    ptype = (body.get("type") or "elan").strip()
    if ptype not in POST_TYPES:
        return None, "Paylaşım növü yanlışdır."
    title = (body.get("title") or "").strip()[:120]
    text = (body.get("text") or "").strip()[:4000]
    if not title:
        return None, "Başlıq boş ola bilməz."
    raw = body.get("teams")
    if raw is None:
        raw = [body.get("team")] if body.get("team") else []
    if not isinstance(raw, list):
        return None, "Taqım siyahısı yanlışdır."
    teams = []
    for t in raw:
        t = (t or "").strip() if isinstance(t, str) else ""
        if not t or t in teams:
            continue
        if t not in db.get("teams", {}):
            return None, "Taqım tapılmadı: " + t
        teams.append(t)
    if len(teams) == len(db.get("teams", {})):
        teams = []  # hamısı seçilibsə = bütün taqımlar
    deadline = (body.get("deadline") or "").strip()[:40]
    return {"type": ptype, "title": title, "text": text, "teams": teams, "deadline": deadline}, None


def post_save_action(db, body):
    """Müəllim yeni paylaşım yaradır. (changed, resp, status)"""
    fields, err = _fields(db, body)
    if err:
        return False, {"error": err}, 400
    pid = time.strftime("%Y%m%d%H%M%S") + secrets.token_hex(3)
    post = dict(fields, id=pid, ts=time.strftime("%d.%m.%Y %H:%M"), ts_epoch=int(time.time()), files=[])
    lst = _posts(db)
    lst.insert(0, post)
    for old in lst[POSTS_MAX:]:
        _delete_files(old)
    del lst[POSTS_MAX:]
    return True, {"success": True, "post": _public(post)}, 200


def post_update_action(db, body):
    """Müəllim mövcud paylaşıma düzəliş edir (növ/başlıq/mətn/taqımlar/son tarix).
    Fayllar ayrıca idarə olunur: post-file-url/confirm (əlavə), post-file-delete (sil)."""
    p = _find(db, (body.get("id") or "").strip())
    if not p:
        return False, {"error": "Paylaşım tapılmadı."}, 404
    fields, err = _fields(db, body)
    if err:
        return False, {"error": err}, 400
    p.update(fields)
    p.pop("team", None)
    p["edited"] = time.strftime("%d.%m.%Y %H:%M")
    return True, {"success": True, "post": _public(p)}, 200


def post_delete_action(db, body):
    """Paylaşım və bütün faylları silinir."""
    p = _find(db, (body.get("id") or "").strip())
    if not p:
        return False, {"error": "Paylaşım tapılmadı."}, 404
    _delete_files(p)
    _posts(db).remove(p)
    return True, {"success": True}, 200


def _spec_for(body):
    kind = (body.get("kind") or "").strip().lower()
    return kind, POST_FILE_KINDS.get(kind)


def _key(pid, fid, spec):
    return f"{_b2.key_prefix()}posts/{pid}-{fid}{spec['ext']}"


def post_file_url_action(db, body):
    """Müəllim paylaşıma fayl əlavə etmək üçün presigned PUT alır; fid qaytarılır, confirm-də göndərilir."""
    if not _b2.is_configured():
        return False, {"error": "Fayl anbarı konfiqurasiya olunmayıb."}, 503
    p = _find(db, (body.get("id") or "").strip())
    if not p:
        return False, {"error": "Paylaşım tapılmadı."}, 404
    if len(_files_of(p)) >= POST_FILES_MAX:
        return False, {"error": f"Bir paylaşıma ən çoxu {POST_FILES_MAX} fayl qoymaq olar."}, 400
    kind, spec = _spec_for(body)
    if not spec:
        return False, {"error": "Yalnız .docx, .doc, .pptx və .pdf faylı qəbul edilir."}, 400
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
    fid = secrets.token_hex(4)
    key = _key(p["id"], fid, spec)
    return False, {"url": _b2.presign_put(key, spec["ct"], expires=900), "fid": fid}, 200


def post_file_confirm_action(db, body):
    """Yükləmə bitdi: fayl anbardadır və ölçü limitdədir — siyahıya əlavə edilir."""
    if not _b2.is_configured():
        return False, {"error": "Fayl anbarı konfiqurasiya olunmayıb."}, 503
    p = _find(db, (body.get("id") or "").strip())
    if not p:
        return False, {"error": "Paylaşım tapılmadı."}, 404
    kind, spec = _spec_for(body)
    fid = (body.get("fid") or "").strip()
    if not spec or not _FID_RE.match(fid):
        return False, {"error": "Fayl növü və ya identifikatoru yanlışdır."}, 400
    key = _key(p["id"], fid, spec)
    size, ok = _b2.head_object(key)
    if not ok:
        return False, {"error": "Fayl anbarda tapılmadı — yükləmə tamamlanmayıb."}, 400
    if size > spec["max"]:
        _b2.delete_object(key)
        return False, {"error": f"Fayl {spec['max'] // (1024 * 1024)} MB limitini aşır — silindi."}, 400
    # Müəllimin öz faylıdır — məzmun (magic) yoxlaması aparılmır; yalnız mövcudluq və ölçü
    files = _files_of(p)
    if len(files) >= POST_FILES_MAX:
        _b2.delete_object(key)
        return False, {"error": f"Bir paylaşıma ən çoxu {POST_FILES_MAX} fayl qoymaq olar."}, 400
    fname = (body.get("fname") or "").strip()[:120] or f"material{spec['ext']}"
    files.append({"fid": fid, "key": key, "kind": kind, "fname": fname, "size": size})
    return True, {"success": True, "post": _public(p)}, 200


def post_file_delete_action(db, body):
    """Müəllim paylaşımdan bir faylı silir (anbardan da)."""
    p = _find(db, (body.get("id") or "").strip())
    if not p:
        return False, {"error": "Paylaşım tapılmadı."}, 404
    fid = (body.get("fid") or "").strip()
    files = _files_of(p)
    for f in files:
        if f.get("fid") == fid:
            if f.get("key"):
                _b2.delete_object(f["key"])
            files.remove(f)
            return True, {"success": True, "post": _public(p)}, 200
    return False, {"error": "Fayl tapılmadı."}, 404


def post_file_link_action(db, body, role, team):
    """Baxış / endirmə üçün presigned GET — yalnız görə bildiyi paylaşım."""
    if not _b2.is_configured():
        return False, {"error": "Fayl anbarı konfiqurasiya olunmayıb."}, 503
    p = _find(db, (body.get("id") or "").strip())
    if not p or not _visible(p, role, team):
        return False, {"error": "Fayl tapılmadı."}, 404
    fid = (body.get("fid") or "").strip()
    f = next((x for x in _files_of(p) if x.get("fid") == fid), None)
    if not f:
        return False, {"error": "Fayl tapılmadı."}, 404
    spec = POST_FILE_KINDS.get(f.get("kind")) or POST_FILE_KINDS["pdf"]
    inline = (body.get("mode") or "view") == "view"
    url = _b2.presign_get(f["key"], expires=3600, filename=f.get("fname") or f"material{spec['ext']}",
                          content_type=spec["ct"], inline=inline)
    return False, {"url": url, "fname": f.get("fname"), "kind": f.get("kind"), "size": f.get("size")}, 200
