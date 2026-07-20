# -*- coding: utf-8 -*-
"""Müəllimin taqım/kursant idarəetməsi (əlavə, ad dəyişmə, silmə).

Statik məlumatlarla (credentials/_results) uyğunluq üçün ad dəyişmələri
db["renames"] / db["team_renames"] xəritələrində saxlanılır; yeni kursantların
girişləri db["credentials_dyn"]-də (yalnız hash) yaradılır.
"""
import hashlib
import secrets
import string

try:
    import _b2
except Exception:
    _b2 = None


def _delete_student_files(db, name):
    """Kursantın B2-dəki fayllarını silir (best-effort)."""
    for meta in db.get("uploads", {}).get(name, {}).values():
        if _b2 and meta.get("key"):
            _b2.delete_object(meta["key"])

PASS_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
TEAM_CODES = {"YTF24A1": "Y1", "YTF24A2": "Y2", "HFT24A1": "H1", "HFT24A2": "H2"}


def _gen_pass(n=10):
    return "".join(secrets.choice(PASS_ALPHABET) for _ in range(n))


def _cred_hash(cid, password):
    return hashlib.sha256(f"{cid.upper()}:{password}".encode("utf-8")).hexdigest()


def _gen_key(n=6):
    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(n))


def _all_names(db):
    names = set()
    for members in db.get("teams", {}).values():
        names.update(members)
    return names


def _payload(db):
    return {
        "success": True,
        "teams": db.get("teams", {}),
        "works": db.get("works", []),
        "work_taken_by": db.get("work_taken_by", {}),
        "selections": db.get("selections", {}),
        "scores": db.get("scores", {}),
        "deadlines": db.get("deadlines", {}),
        "exam_scores": db.get("exam_scores", {}),
    }


def roster_action(db, body, static_credentials):
    """(changed, response, status) qaytarır. db yerində dəyişdirilir."""
    action = body.get("action") or ""
    teams = db.setdefault("teams", {})
    static_names = {c.get("name") for c in static_credentials.values() if c.get("team")}
    static_teams = {c.get("team") for c in static_credentials.values() if c.get("team")}

    if action == "add_team":
        team = (body.get("team") or "").strip()[:40]
        if not team:
            return False, {"error": "Taqım adı boş ola bilməz."}, 400
        if team in teams:
            return False, {"error": "Bu adda taqım artıq var."}, 400
        teams[team] = []
        db.setdefault("work_taken_by", {})[team] = {}
        return True, _payload(db), 200

    if action == "rename_team":
        old = (body.get("team") or "").strip()
        new = (body.get("new") or "").strip()[:40]
        if old not in teams:
            return False, {"error": "Taqım tapılmadı."}, 404
        if not new:
            return False, {"error": "Yeni ad boş ola bilməz."}, 400
        if new in teams:
            return False, {"error": "Bu adda taqım artıq var."}, 400
        teams[new] = teams.pop(old)
        wtb = db.setdefault("work_taken_by", {})
        wtb[new] = wtb.pop(old, {})
        for cred in db.get("credentials_dyn", {}).values():
            if cred.get("team") == old:
                cred["team"] = new
        tr = db.setdefault("team_renames", {})
        orig = next((o for o, c in tr.items() if c == old), None)
        if orig is None and old in static_teams:
            orig = old
        if orig is not None:
            if orig == new:
                tr.pop(orig, None)
            else:
                tr[orig] = new
        return True, _payload(db), 200

    if action == "delete_team":
        team = (body.get("team") or "").strip()
        if team not in teams:
            return False, {"error": "Taqım tapılmadı."}, 404
        # Əsas qruplar (statik girişli) silinə bilməz — yalnız sonradan yaradılanlar
        tr = db.get("team_renames", {})
        if team in static_teams or any(c == team for c in tr.values()):
            return False, {"error": "Əsas qruplar silinə bilməz — yalnız sonradan yaradılmış taqımlar silinir."}, 400
        for name in list(teams.get(team, [])):
            _delete_student_files(db, name)
            for m in ("keys", "selections", "scores", "deadlines", "exam_scores", "uploads", "kollok_scores"):
                db.get(m, {}).pop(name, None)
            dyn = db.get("credentials_dyn", {})
            for cid in [c for c, cred in dyn.items() if cred.get("name") == name]:
                del dyn[cid]
        teams.pop(team)
        db.get("work_taken_by", {}).pop(team, None)
        return True, _payload(db), 200

    if action == "add_student":
        team = (body.get("team") or "").strip()
        name = (body.get("name") or "").strip()[:70]
        if team not in teams:
            return False, {"error": "Taqım tapılmadı."}, 404
        if not name:
            return False, {"error": "Kursant adı boş ola bilməz."}, 400
        if name in _all_names(db):
            return False, {"error": "Bu adda kursant artıq var."}, 400
        dyn = db.setdefault("credentials_dyn", {})
        code = TEAM_CODES.get(team) or "".join(ch for ch in team.upper() if ch.isalnum())[:2] or "K"
        n = len(teams[team]) + 1
        cid = f"{code}-{n:02d}"
        while cid in static_credentials or cid in dyn:
            n += 1
            cid = f"{code}-{n:02d}"
        password = _gen_pass()
        teams[team].append(name)
        dyn[cid] = {"hash": _cred_hash(cid, password), "name": name, "team": team}
        db.setdefault("keys", {})[name] = _gen_key()
        # əvvəl silinmiş eyni adlı hesab bloklamasın
        if name in db.get("deleted_names", []):
            db["deleted_names"].remove(name)
        resp = _payload(db)
        resp["id"] = cid
        resp["password"] = password
        return True, resp, 200

    if action == "rename_student":
        old = (body.get("name") or "").strip()
        new = (body.get("new") or "").strip()[:70]
        if old not in _all_names(db):
            return False, {"error": "Kursant tapılmadı."}, 404
        if not new:
            return False, {"error": "Yeni ad boş ola bilməz."}, 400
        if new in _all_names(db):
            return False, {"error": "Bu adda kursant artıq var."}, 400
        for members in teams.values():
            for i, n in enumerate(members):
                if n == old:
                    members[i] = new
        for m in ("keys", "selections", "scores", "deadlines", "exam_scores", "uploads", "kollok_scores"):
            if old in db.get(m, {}):
                db[m][new] = db[m].pop(old)
        for taken in db.get("work_taken_by", {}).values():
            for wid, n in list(taken.items()):
                if n == old:
                    taken[wid] = new
        for cred in db.get("credentials_dyn", {}).values():
            if cred.get("name") == old:
                cred["name"] = new
        rn = db.setdefault("renames", {})
        orig = next((o for o, c in rn.items() if c == old), None)
        if orig is None and old in static_names:
            orig = old
        if orig is not None:
            if orig == new:
                rn.pop(orig, None)
            else:
                rn[orig] = new
        return True, _payload(db), 200

    if action == "delete_student":
        name = (body.get("name") or "").strip()
        if name not in _all_names(db):
            return False, {"error": "Kursant tapılmadı."}, 404
        _delete_student_files(db, name)
        for members in teams.values():
            if name in members:
                members.remove(name)
        for m in ("keys", "selections", "scores", "deadlines", "exam_scores", "uploads", "kollok_scores"):
            db.get(m, {}).pop(name, None)
        for taken in db.get("work_taken_by", {}).values():
            for wid, n in list(taken.items()):
                if n == name:
                    del taken[wid]
        dyn = db.get("credentials_dyn", {})
        for cid in [c for c, cred in dyn.items() if cred.get("name") == name]:
            del dyn[cid]
        # statik giriş məlumatı olan kursantın hesabı bloklanır
        rn = db.get("renames", {})
        if name in static_names or any(c == name for c in rn.values()):
            dl = db.setdefault("deleted_names", [])
            if name not in dl:
                dl.append(name)
        return True, _payload(db), 200

    if action == "add_work":
        title = (body.get("title") or "").strip()[:200]
        if not title:
            return False, {"error": "İşin adı boş ola bilməz."}, 400
        works = db.setdefault("works", [])
        if title in works:
            return False, {"error": "Bu adda iş artıq var."}, 400
        works.append(title)
        return True, _payload(db), 200

    if action == "edit_work":
        works = db.get("works", [])
        try:
            wid = int(body.get("id"))
        except (TypeError, ValueError):
            return False, {"error": "İş tapılmadı."}, 400
        if not (0 <= wid < len(works)):
            return False, {"error": "İş tapılmadı."}, 404
        title = (body.get("title") or "").strip()[:200]
        if not title:
            return False, {"error": "İşin adı boş ola bilməz."}, 400
        works[wid] = title
        return True, _payload(db), 200

    if action == "delete_work":
        works = db.get("works", [])
        try:
            wid = int(body.get("id"))
        except (TypeError, ValueError):
            return False, {"error": "İş tapılmadı."}, 400
        if not (0 <= wid < len(works)):
            return False, {"error": "İş tapılmadı."}, 404
        # seçilmiş işi silmək olmaz — əvvəl seçim sıfırlanmalıdır
        for taken in db.get("work_taken_by", {}).values():
            if str(wid) in taken:
                return False, {"error": f"Bu iş {taken[str(wid)]} tərəfindən seçilib — əvvəlcə onun seçimini sıfırlayın."}, 400
        works.pop(wid)
        # indekslər sürüşür: bütün istinadlar yenidən hesablanır
        for name, sel in db.get("selections", {}).items():
            db["selections"][name] = [i - 1 if i > wid else i for i in sel if i != wid]
        for team, taken in db.get("work_taken_by", {}).items():
            db["work_taken_by"][team] = {
                (str(int(k) - 1) if int(k) > wid else k): v for k, v in taken.items()
            }
        return True, _payload(db), 200

    return False, {"error": "Naməlum əməliyyat."}, 400
