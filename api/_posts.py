# -*- coding: utf-8 -*-
"""Elanlar və materiallar — müəllim paylaşır (elan / tapşırıq / mühazirə), kursant kabinetində görür.

db["posts"] = [ {id, type, title, text, teams ([] = hamı), deadline, ts, ts_epoch, edited?,
                 files: [ {fid, key, kind, fname, size}, ... ]}, ... ]  — ən yenisi əvvəldə, ən çoxu POSTS_MAX.
(Köhnə qeydlərdə tək "file" sahəsi ola bilər — _files_of() onu siyahıya çevirir.)

Fayl əlavəsi kursant faylları kimi B2-yə presigned PUT ilə birbaşa gedir
(post-file-url → PUT → post-file-confirm). İstənilən format qəbul edilir, məzmun yoxlanmır — müəllimin öz
faylıdır; yalnız say (POST_FILES_MAX) və texniki ölçü həddi (POST_FILE_MAX). Açar: posts/<id>-<fid>.<ext>.
Kursant faylı yalnız endirir (saytdaxili baxış yoxdur).
"""
import mimetypes
import re
import secrets
import time

import _b2

POSTS_MAX = 60
POST_FILES_MAX = 20                 # bir paylaşıma fayl sayı
POST_FILE_MAX = 200 * 1024 * 1024   # texniki hədd (anbar); format/məzmun yoxlanmır
POST_TYPES = ("elan", "tapsiriq", "muhazire")
_FID_RE = re.compile(r"^[0-9a-f]{8}$")



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


def _ext_of(fname):
    """Fayl uzantısı (yalnız a-z0-9, ≤10 simvol); yoxdursa boş."""
    ext = fname.rsplit(".", 1)[1].lower() if "." in fname else ""
    return "".join(ch for ch in ext if ch.isalnum())[:10]


def _ct_for(fname):
    return mimetypes.guess_type(fname)[0] or "application/octet-stream"


def _key(pid, fid, ext):
    return f"{_b2.key_prefix()}posts/{pid}-{fid}" + (f".{ext}" if ext else "")


def post_file_url_action(db, body):
    """Müəllim paylaşıma fayl əlavə etmək üçün presigned PUT alır — format/məzmun yoxlanmır
    (müəllimin öz faylıdır); yalnız say və texniki ölçü həddi. fid qaytarılır, confirm-də göndərilir."""
    if not _b2.is_configured():
        return False, {"error": "Fayl anbarı konfiqurasiya olunmayıb."}, 503
    p = _find(db, (body.get("id") or "").strip())
    if not p:
        return False, {"error": "Paylaşım tapılmadı."}, 404
    if len(_files_of(p)) >= POST_FILES_MAX:
        return False, {"error": f"Bir paylaşıma ən çoxu {POST_FILES_MAX} fayl qoymaq olar."}, 400
    fname = (body.get("fname") or "").strip()[:160] or "fayl"
    try:
        size = int(body.get("size") or 0)
    except (TypeError, ValueError):
        size = 0
    if size > POST_FILE_MAX:
        return False, {"error": f"Fayl {POST_FILE_MAX // (1024 * 1024)} MB-dan böyük ola bilməz."}, 400
    fid = secrets.token_hex(4)
    key = _key(p["id"], fid, _ext_of(fname))
    return False, {"url": _b2.presign_put(key, _ct_for(fname), expires=1800), "fid": fid}, 200


def post_file_confirm_action(db, body):
    """Yükləmə bitdi: fayl anbardadırsa siyahıya əlavə edilir (məzmun yoxlanmır)."""
    if not _b2.is_configured():
        return False, {"error": "Fayl anbarı konfiqurasiya olunmayıb."}, 503
    p = _find(db, (body.get("id") or "").strip())
    if not p:
        return False, {"error": "Paylaşım tapılmadı."}, 404
    fid = (body.get("fid") or "").strip()
    if not _FID_RE.match(fid):
        return False, {"error": "Fayl identifikatoru yanlışdır."}, 400
    fname = (body.get("fname") or "").strip()[:160] or "fayl"
    ext = _ext_of(fname)
    key = _key(p["id"], fid, ext)
    size, ok = _b2.head_object(key)
    if not ok:
        return False, {"error": "Fayl anbarda tapılmadı — yükləmə tamamlanmayıb."}, 400
    files = _files_of(p)
    if len(files) >= POST_FILES_MAX:
        _b2.delete_object(key)
        return False, {"error": f"Bir paylaşıma ən çoxu {POST_FILES_MAX} fayl qoymaq olar."}, 400
    files.append({"fid": fid, "key": key, "kind": ext or "file", "fname": fname, "size": size})
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
    fname = f.get("fname") or "fayl"
    url = _b2.presign_get(f["key"], expires=3600, filename=fname, content_type=_ct_for(fname), inline=False)
    return False, {"url": url, "fname": f.get("fname"), "kind": f.get("kind"), "size": f.get("size")}, 200
