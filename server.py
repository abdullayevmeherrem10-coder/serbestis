# -*- coding: utf-8 -*-
import http.server
import base64
import hashlib
import hmac
import json
import os
import re
import string
import random
import secrets
import sys
import time
import urllib.parse
import mimetypes

PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "database.json")

sys.path.insert(0, os.path.join(BASE_DIR, "api"))
from _credentials import CREDENTIALS
from _results import RESULTS
from _arxiv import (ARXIV_IMTAHAN, arxiv_entries, arxiv_clean_rows,
                    arxiv_add, arxiv_delete, arxiv_clear_semester)
from _roster import roster_action
from _subjects import (subjects_of, current_subject, set_current_subject, current_pick,
                       work_subjects, works_payload, select_works, reset_selection,
                       reset_all_selections, ensure_subject2_topics)
from _uploads import (upload_url_action, upload_confirm_action,
                      upload_link_action, upload_delete_action,
                      upload_review_action, vt_check_action, vt_status_action)
from _backup import run_backup, read_backup, save_prerestore

# Admin şifrəsi koda yazılmır: əvvəlcə ENV dəyişəni, sonra gitignore-lanmış
# admin_secret.txt faylı oxunur. Heç biri yoxdursa təsadüfi (bilinməyən)
# dəyər təyin olunur ki, admin paneli effektiv bağlı olsun.
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
if not ADMIN_PASSWORD:
    _secret_file = os.path.join(BASE_DIR, "admin_secret.txt")
    if os.path.exists(_secret_file):
        with open(_secret_file, encoding="utf-8") as f:
            ADMIN_PASSWORD = f.read().strip()
if not ADMIN_PASSWORD:
    ADMIN_PASSWORD = secrets.token_urlsafe(24)

def load_db():
    with open(DB_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)
    # İkinci fənnin (s2) mövzuları bir dəfə əlavə olunur
    if ensure_subject2_topics(db):
        save_db(db)
    return db

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def cred_hash(cid, password):
    return hashlib.sha256(f"{cid.upper()}:{password}".encode("utf-8")).hexdigest()

# Statik fayl icazə siyahısı (allowlist)
STATIC_ALLOWED_EXT = {
    ".html", ".css", ".js",
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".ico",
    ".woff", ".woff2", ".ttf",
}
STATIC_ALLOWED_FILES = {"ÜZLÜK.docx"}

# E-Kollokvium Firebase yazma proxy-si üçün gizli açar
FIREBASE_DB_URL = "https://kollokvium1-default-rtdb.firebaseio.com"
FIREBASE_SECRET = os.environ.get("FIREBASE_SECRET", "")
if not FIREBASE_SECRET:
    _fb_file = os.path.join(BASE_DIR, "firebase_secret.txt")
    if os.path.exists(_fb_file):
        with open(_fb_file, encoding="utf-8") as f:
            FIREBASE_SECRET = f.read().strip()

try:
    from _fbauth import get_access_token as _fb_access_token
except Exception:
    def _fb_access_token():
        return None

def _fb_url(path):
    url = f"{FIREBASE_DB_URL}/{path}.json"
    tok = _fb_access_token()
    if tok:
        return url + "?access_token=" + tok
    if FIREBASE_SECRET:
        return url + "?auth=" + FIREBASE_SECRET
    return url

# Kabinet token sistemi (HMAC imzalı, 12 saat etibarlı)
TOKEN_TTL = 12 * 3600
CABINET_SECRET = os.environ.get('CABINET_SECRET') or hashlib.sha256(
    ("cab|" + ADMIN_PASSWORD + "|" + "|".join(sorted(c["hash"] for c in CREDENTIALS.values()))).encode("utf-8")
).hexdigest()

def make_token(cid, role="student"):
    payload = json.dumps({"id": cid, "role": role, "exp": int(time.time()) + TOKEN_TTL})
    b = base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii").rstrip("=")
    sig = hmac.new(CABINET_SECRET.encode("utf-8"), b.encode("ascii"), hashlib.sha256).hexdigest()[:32]
    return f"{b}.{sig}"

def token_payload(token):
    try:
        b, sig = token.split(".")
        good = hmac.new(CABINET_SECRET.encode("utf-8"), b.encode("ascii"), hashlib.sha256).hexdigest()[:32]
        if not hmac.compare_digest(sig, good):
            return None
        payload = json.loads(base64.urlsafe_b64decode(b + "=" * (-len(b) % 4)))
        if payload.get("exp", 0) < time.time():
            return None
        return payload if payload.get("id") else None
    except Exception:
        return None

def verify_token(token):
    p = token_payload(token)
    return p.get("id") if p else None

def exam_grade(bal):
    if bal >= 91: return 'A “Əla”'
    if bal >= 81: return 'B “Çox yaxşı”'
    if bal >= 71: return 'C “Yaxşı”'
    if bal >= 61: return 'D “Kafi”'
    if bal >= 51: return 'E “Qənaətbəxş”'
    return 'F “Qeyri-kafi”'

def effective_results(db):
    """Statik nəticələr — ad/taqım dəyişmələri tətbiq edilmiş halda."""
    rn = db.get("renames", {})
    tr = db.get("team_renames", {})
    out = {}
    for group, data in RESULTS.items():
        out[group] = {
            "team": tr.get(data["team"], data["team"]),
            "kollok": {rn.get(n, n): v for n, v in data["kollok"].items()},
            "menimseme": {rn.get(n, n): v for n, v in data["menimseme"].items()},
            "imtahan": {rn.get(n, n): v for n, v in data["imtahan"].items()},
        }
    return out

def student_results(name, team, db):
    out = {"group": None, "kollok": None, "menimseme": None, "imtahan": None}
    for group, data in effective_results(db).items():
        if data["team"] == team:
            out = {
                "group": group,
                "kollok": data["kollok"].get(name),
                "menimseme": data["menimseme"].get(name),
                "imtahan": data["imtahan"].get(name),
            }
            break
    exam_scores = db.get("exam_scores", {})
    if name in exam_scores:
        bal = exam_scores[name]
        out["imtahan"] = [str(bal), exam_grade(bal)]
    return out

def raw_cred(cid, db):
    """Statik və ya dinamik (müəllimin əlavə etdiyi) hesab.
    Müəllim şifrəni yeniləyibsə, statik hash db["cred_overrides"] ilə əvəzlənir."""
    cred = CREDENTIALS.get(cid)
    if cred:
        ov = db.get("cred_overrides", {}).get(cid)
        return {**cred, "hash": ov} if ov else cred
    return db.get("credentials_dyn", {}).get(cid)

def resolve_cred(cid, db):
    """ID → aktual hesab (ad/taqım dəyişmələri tətbiq edilmiş); silinibsə None."""
    cred = raw_cred(cid, db)
    if not cred:
        return None
    if cred.get("role") == "teacher":
        return {"role": "teacher", "name": cred.get("name", "Müəllim")}
    name = db.get("renames", {}).get(cred["name"], cred["name"])
    if name in db.get("deleted_names", []):
        return None
    team = db.get("team_renames", {}).get(cred["team"], cred["team"])
    return {"role": "student", "name": name, "team": team}

def generate_key(length=6):
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)

        if path == "/api/semester-info":
            db = load_db()
            self.send_json({
                "semester": db.get("semester", "2025/2026 yaz semestri"),
                "subject": db.get("subject", "Hərbi Mühəndis Texnikası"),
                "subject_id": current_subject(db),
                "subjects": subjects_of(db),
            })

        elif path == "/api/teams":
            # Kursant adları yalnız daxil olmuş istifadəçilərə görünür
            auth = self.headers.get("Authorization", "")
            cid = verify_token(auth[7:].strip()) if auth.startswith("Bearer ") else None
            db = load_db()
            if not cid or not resolve_cred(cid, db):
                self.send_json({"error": "Giriş tələb olunur."}, 401)
                return
            self.send_json({"teams": {t: members for t, members in db["teams"].items()}})

        elif path == "/api/works":
            # İşi götürən kursantların adları yalnız daxil olmuş istifadəçilərə görünür
            auth = self.headers.get("Authorization", "")
            cid = verify_token(auth[7:].strip()) if auth.startswith("Bearer ") else None
            db = load_db()
            if not cid or not resolve_cred(cid, db):
                self.send_json({"error": "Giriş tələb olunur."}, 401)
                return
            params = urllib.parse.parse_qs(parsed.query)
            team = params.get("team", [""])[0]
            # Yalnız cari fənnə aid işlər; subject/pick — kursant tərəfi üçün
            self.send_json({"works": works_payload(db, team), "subject": current_subject(db),
                            "pick": current_pick(db), "subjects": subjects_of(db)})

        elif path == "/api/arxiv-imtahan":
            # Köhnə qəbulların arxivlənmiş imtahan nəticələri — yalnız müəllim
            auth = self.headers.get("Authorization", "")
            cid = verify_token(auth[7:].strip()) if auth.startswith("Bearer ") else None
            if not cid or CREDENTIALS.get(cid, {}).get("role") != "teacher":
                self.send_json({"error": "İcazə yoxdur."}, 401)
                return
            self.send_json({"semestrler": arxiv_entries(load_db())})

        elif path == "/api/cabinet-data":
            auth = self.headers.get("Authorization", "")
            cid = verify_token(auth[7:].strip()) if auth.startswith("Bearer ") else None
            if not cid:
                self.send_json({"error": "Sessiya bitib. Yenidən daxil olun."}, 401)
                return
            db = load_db()
            cred = resolve_cred(cid, db)
            if not cred:
                self.send_json({"error": "Sessiya bitib. Yenidən daxil olun."}, 401)
                return
            if cred.get("role") == "teacher":
                self.send_json({
                    "role": "teacher",
                    "name": cred.get("name", "Müəllim"),
                    "results": effective_results(db),
                    "selections": db.get("selections", {}),
                    "scores": db.get("scores", {}),
                    "deadlines": db.get("deadlines", {}),
                    "teams": db.get("teams", {}),
                    "works": db.get("works", []),
                    "work_taken_by": db.get("work_taken_by", {}),
                    "work_subjects": work_subjects(db),
                    "subjects": subjects_of(db),
                    "subject_id": current_subject(db),
                    "semester": db.get("semester", "2025/2026 yaz semestri"),
                    "subject": db.get("subject", "Hərbi Mühəndis Texnikası"),
                    "exam_scores": db.get("exam_scores", {}),
                    "kollok_scores": db.get("kollok_scores", {}),
                    "uploads": db.get("uploads", {}),
                })
                return
            name = cred["name"]
            self.send_json({
                "role": "student",
                "id": cid,
                "name": name,
                "team": cred["team"],
                "key": db.get("keys", {}).get(name, ""),
                "selections": db.get("selections", {}).get(name, []),
                "subjects": subjects_of(db),
                "subject_id": current_subject(db),
                "results": student_results(name, cred["team"], db),
                "scores": db.get("scores", {}).get(name),
                "deadline": db.get("deadlines", {}).get(name),
                "semester": db.get("semester", "2025/2026 yaz semestri"),
                "subject": db.get("subject", "Hərbi Mühəndis Texnikası"),
                "uploads": db.get("uploads", {}).get(name, {}),
                "kollok_manual": db.get("kollok_scores", {}).get(name, {}),
            })

        elif path == "/api/student-status":
            params = urllib.parse.parse_qs(parsed.query)
            name = params.get("name", [""])[0]
            key = params.get("key", [""])[0]
            db = load_db()
            if name not in db["keys"]:
                self.send_json({"error": "Bu kursant üçün açar təyin edilməyib"}, 403)
                return
            if db["keys"][name] != key:
                self.send_json({"error": "Açar yanlışdır"}, 403)
                return
            selected = db["selections"].get(name, [])
            self.send_json({"name": name, "selections": selected})

        else:
            # Serve static files
            if path == "/":
                path = "/index.html"

            file_path = os.path.join(BASE_DIR, path.lstrip("/"))
            file_path = os.path.normpath(file_path)

            if not file_path.startswith(os.path.normpath(BASE_DIR)):
                self.send_response(403)
                self.end_headers()
                return

            # Qovluq üçün index.html ver (məs. /kollokvium/)
            if os.path.isdir(file_path):
                file_path = os.path.join(file_path, "index.html")

            # Təhlükəsizlik: yalnız icazəli statik fayl tipləri verilir.
            # database.json, *.py, *.txt, .git/, api/, docx sənədləri (ÜZLÜK istisna) bağlıdır.
            rel = os.path.relpath(file_path, os.path.normpath(BASE_DIR)).replace(os.sep, "/")
            segs = rel.split("/")
            ext = os.path.splitext(rel)[1].lower()
            allowed = (
                not any(s.startswith(".") or s == "__pycache__" for s in segs)
                and segs[0].lower() != "api"
                and (ext in STATIC_ALLOWED_EXT or os.path.basename(rel) in STATIC_ALLOWED_FILES)
            )
            if not allowed:
                self.send_response(404)
                self.end_headers()
                return

            # Kitab səhifələri yalnız daxil olmuş istifadəçilərə (kabinet cookie-si)
            rel_l = rel.lower()
            cookie = self.headers.get("Cookie", "")
            cm = re.search(r"(?:^|;\s*)kabinet=([^;]+)", cookie)
            tok = urllib.parse.unquote(cm.group(1)) if cm else ""
            if rel_l == "kitab.html" or rel_l.startswith("kitab/"):
                if not verify_token(tok):
                    if rel_l == "kitab.html":
                        self.send_response(302)
                        self.send_header("Location", "/")
                        self.end_headers()
                    else:
                        self.send_json({"error": "Giriş tələb olunur."}, 401)
                    return
            # Elektron Kollokvium sistemi yalnız müəllimə açıqdır
            if rel_l == "kollokvium/index.html" or rel_l.startswith("kollokvium/"):
                pl = token_payload(tok)
                if not pl or pl.get("role") != "teacher":
                    if rel_l == "kollokvium/index.html":
                        self.send_response(302)
                        self.send_header("Location", "/")
                        self.end_headers()
                    else:
                        self.send_json({"error": "Yalnız müəllim."}, 401)
                    return

            if os.path.isfile(file_path):
                mime, _ = mimetypes.guess_type(file_path)
                if mime is None:
                    mime = "application/octet-stream"
                with open(file_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", len(content))
                # Qorunan səhifələr keşlənməsin ki, çıxışdan sonra middleware yenidən yoxlasın
                if rel_l == "kitab.html" or rel_l.startswith("kitab/") or rel_l.startswith("kollokvium/"):
                    self.send_header("Cache-Control", "no-store, must-revalidate")
                if file_path.endswith(".docx"):
                    fname = os.path.basename(file_path)
                    encoded_fname = urllib.parse.quote(fname)
                    self.send_header("Content-Disposition", f"attachment; filename*=UTF-8''{encoded_fname}")
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_response(404)
                self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/kollok-write":
            # Müəllim yoxlanışı: Bearer token və ya kabinet cookie-si
            auth = self.headers.get("Authorization", "")
            cid = verify_token(auth[7:].strip()) if auth.startswith("Bearer ") else None
            if not cid:
                cm = re.search(r"(?:^|;\s*)kabinet=([^;]+)", self.headers.get("Cookie", ""))
                cid = verify_token(urllib.parse.unquote(cm.group(1))) if cm else None
            if not cid or CREDENTIALS.get(cid, {}).get("role") != "teacher":
                self.send_json({"error": "Yazmaq üçün əsas saytda müəllim kimi daxil olmalısınız."}, 401)
                return
            body = self.read_body()
            fb_path = (body.get("path") or "").strip()
            if not re.fullmatch(r"(sessions|topics)/[A-Za-z0-9_\-/]+", fb_path):
                self.send_json({"error": "Yol etibarsızdır."}, 400)
                return
            url = _fb_url(fb_path)
            data = body.get("data", None)
            try:
                import urllib.request as _urlreq
                if data is None:
                    req = _urlreq.Request(url, method="DELETE")
                else:
                    req = _urlreq.Request(url, data=json.dumps(data, ensure_ascii=False).encode("utf-8"),
                                          method="PUT", headers={"Content-Type": "application/json"})
                with _urlreq.urlopen(req, timeout=10) as resp:
                    resp.read()
                self.send_json({"success": True})
            except Exception:
                self.send_json({"error": "Firebase yazma alınmadı."}, 502)

        elif path in ("/api/arxiv-save", "/api/arxiv-delete"):
            # Semestr sonu arxivi (yaz / sil) — yalnız müəllim
            auth = self.headers.get("Authorization", "")
            cid = verify_token(auth[7:].strip()) if auth.startswith("Bearer ") else None
            if not cid or CREDENTIALS.get(cid, {}).get("role") != "teacher":
                self.send_json({"error": "İcazə yoxdur."}, 401)
                return
            body = self.read_body()
            db = load_db()
            if path == "/api/arxiv-delete":
                if not arxiv_delete(db, (body.get("id") or "").strip()):
                    self.send_json({"error": "Arxiv girişi tapılmadı."}, 404)
                    return
                save_db(db)
                self.send_json({"success": True})
                return
            qruplar = arxiv_clean_rows(body.get("qruplar"), exam_grade)
            if qruplar is None:
                self.send_json({"error": "Arxiv məlumatı etibarsızdır."}, 400)
                return
            entry = arxiv_add(db, body.get("semester") or db.get("semester", ""),
                              body.get("subject") or db.get("subject", ""), qruplar)
            cleared = False
            if body.get("clear") is True:
                try:
                    save_prerestore(db)
                except Exception:
                    pass
                arxiv_clear_semester(db)
                cleared = True
            save_db(db)
            self.send_json({"success": True, "id": entry["id"], "cleared": cleared})

        elif path == "/api/cabinet-roster":
            auth = self.headers.get("Authorization", "")
            cid = verify_token(auth[7:].strip()) if auth.startswith("Bearer ") else None
            if not cid or CREDENTIALS.get(cid, {}).get("role") != "teacher":
                self.send_json({"error": "İcazə yoxdur."}, 401)
                return
            body = self.read_body()
            db = load_db()
            changed, resp, code = roster_action(db, body, CREDENTIALS)
            if changed:
                save_db(db)
            self.send_json(resp, code)

        elif path in ("/api/backup", "/api/backup-restore"):
            auth = self.headers.get("Authorization", "")
            cid = verify_token(auth[7:].strip()) if auth.startswith("Bearer ") else None
            if not cid or CREDENTIALS.get(cid, {}).get("role") != "teacher":
                self.send_json({"error": "İcazə yoxdur."}, 401)
                return
            if path == "/api/backup":
                ok, info = run_backup(load_db())
                self.send_json({"success": True, "key": info} if ok else {"error": info}, 200 if ok else 502)
                return
            body = self.read_body()
            date = (body.get("date") or "").strip()
            snap = read_backup(date)
            if snap is None:
                self.send_json({"error": f"{date} tarixli nüsxə tapılmadı."}, 404)
                return
            save_prerestore(load_db())
            save_db(snap)
            self.send_json({"success": True, "date": date})

        elif path in ("/api/upload-url", "/api/upload-confirm", "/api/upload-link",
                      "/api/upload-delete", "/api/upload-review", "/api/vt-check", "/api/vt-status"):
            auth = self.headers.get("Authorization", "")
            cid = verify_token(auth[7:].strip()) if auth.startswith("Bearer ") else None
            db = load_db()
            cred = resolve_cred(cid, db) if cid else None
            if not cred:
                self.send_json({"error": "Giriş tələb olunur."}, 401)
                return
            body = self.read_body()
            if path in ("/api/upload-url", "/api/upload-confirm"):
                if cred.get("role") != "student":
                    self.send_json({"error": "Giriş tələb olunur."}, 401)
                    return
                action = upload_url_action if path == "/api/upload-url" else upload_confirm_action
                changed, resp, code = action(db, body, cred["name"])
            else:
                action = {
                    "/api/upload-link": upload_link_action,
                    "/api/upload-delete": upload_delete_action,
                    "/api/upload-review": upload_review_action,
                    "/api/vt-check": vt_check_action,
                    "/api/vt-status": vt_status_action,
                }[path]
                changed, resp, code = action(db, body, cred.get("role"), cred.get("name"))
            if changed:
                save_db(db)
            self.send_json(resp, code)

        elif path == "/api/cabinet-kollok":
            auth = self.headers.get("Authorization", "")
            cid = verify_token(auth[7:].strip()) if auth.startswith("Bearer ") else None
            if not cid or CREDENTIALS.get(cid, {}).get("role") != "teacher":
                self.send_json({"error": "İcazə yoxdur."}, 401)
                return
            body = self.read_body()
            name = (body.get("name") or "").strip()
            if not name:
                self.send_json({"error": "Kursant adı göstərilməyib."}, 400)
                return
            try:
                k = int(body.get("k"))
            except (TypeError, ValueError):
                k = 0
            if k not in (1, 2, 3):
                self.send_json({"error": "Kollokvium nömrəsi 1-3 olmalıdır."}, 400)
                return
            db = load_db()
            if not any(name in members for members in db.get("teams", {}).values()):
                self.send_json({"error": "Kursant tapılmadı."}, 404)
                return
            ks = db.setdefault("kollok_scores", {})
            bal = body.get("bal")
            if bal is None or bal == "":
                ks.get(name, {}).pop(str(k), None)
                if name in ks and not ks[name]:
                    del ks[name]
                save_db(db)
                self.send_json({"success": True, "name": name, "k": k, "bal": None,
                                "kollok_scores": db.get("kollok_scores", {})})
                return
            try:
                bal = max(0, min(10, int(bal)))
            except (TypeError, ValueError):
                self.send_json({"error": "Bal 0-10 arası rəqəm olmalıdır."}, 400)
                return
            ks.setdefault(name, {})[str(k)] = bal
            save_db(db)
            self.send_json({"success": True, "name": name, "k": k, "bal": bal,
                            "kollok_scores": db.get("kollok_scores", {})})

        elif path == "/api/cabinet-exam":
            auth = self.headers.get("Authorization", "")
            cid = verify_token(auth[7:].strip()) if auth.startswith("Bearer ") else None
            if not cid or CREDENTIALS.get(cid, {}).get("role") != "teacher":
                self.send_json({"error": "İcazə yoxdur."}, 401)
                return
            body = self.read_body()
            name = (body.get("name") or "").strip()
            if not name:
                self.send_json({"error": "Kursant adı göstərilməyib."}, 400)
                return
            db = load_db()
            if not any(name in members for members in db.get("teams", {}).values()):
                self.send_json({"error": "Kursant tapılmadı."}, 404)
                return
            bal = body.get("bal")
            ex = db.setdefault("exam_scores", {})
            if bal is None or bal == "":
                ex.pop(name, None)
                save_db(db)
                self.send_json({"success": True, "name": name, "bal": None})
                return
            try:
                bal = max(0, min(100, int(bal)))
            except (TypeError, ValueError):
                self.send_json({"error": "Bal 0-100 arası rəqəm olmalıdır."}, 400)
                return
            ex[name] = bal
            save_db(db)
            self.send_json({"success": True, "name": name, "bal": bal, "grade": exam_grade(bal)})

        elif path == "/api/cabinet-semester":
            auth = self.headers.get("Authorization", "")
            cid = verify_token(auth[7:].strip()) if auth.startswith("Bearer ") else None
            if not cid or CREDENTIALS.get(cid, {}).get("role") != "teacher":
                self.send_json({"error": "İcazə yoxdur."}, 401)
                return
            body = self.read_body()
            semester = (body.get("semester") or "").strip()[:60]
            subject_id = body.get("subject_id")
            subject = (body.get("subject") or "").strip()[:60]
            if not semester or not (subject_id or subject):
                self.send_json({"error": "Semestr və fənn boş ola bilməz."}, 400)
                return
            db = load_db()
            db["semester"] = semester
            if subject_id:
                # Fənn siyahıdan seçilir: adı və sərbəst iş siyahısı (s1 / s2) birlikdə dəyişir
                if not set_current_subject(db, subject_id):
                    self.send_json({"error": "Fənn tapılmadı."}, 400)
                    return
            else:
                db["subject"] = subject          # köhnə müştəri: sərbəst mətn
                db.pop("subject_id", None)
            save_db(db)
            self.send_json({"success": True, "semester": semester, "subject": db["subject"],
                            "subject_id": current_subject(db), "subjects": subjects_of(db)})

        elif path == "/api/cabinet-reset":
            auth = self.headers.get("Authorization", "")
            cid = verify_token(auth[7:].strip()) if auth.startswith("Bearer ") else None
            if not cid or CREDENTIALS.get(cid, {}).get("role") != "teacher":
                self.send_json({"error": "İcazə yoxdur."}, 401)
                return
            body = self.read_body()
            name = (body.get("name") or "").strip()
            if not name:
                self.send_json({"error": "Kursant adı göstərilməyib."}, 400)
                return
            db = load_db()
            reset_selection(db, name)
            save_db(db)
            self.send_json({"success": True, "selections": db.get("selections", {}), "work_taken_by": db.get("work_taken_by", {})})

        elif path == "/api/cabinet-reset-all":
            auth = self.headers.get("Authorization", "")
            cid = verify_token(auth[7:].strip()) if auth.startswith("Bearer ") else None
            if not cid or CREDENTIALS.get(cid, {}).get("role") != "teacher":
                self.send_json({"error": "İcazə yoxdur."}, 401)
                return
            db = load_db()
            reset_all_selections(db)
            save_db(db)
            self.send_json({"success": True, "selections": db.get("selections", {}), "work_taken_by": db["work_taken_by"]})

        elif path == "/api/cabinet-deadline":
            auth = self.headers.get("Authorization", "")
            cid = verify_token(auth[7:].strip()) if auth.startswith("Bearer ") else None
            if not cid or CREDENTIALS.get(cid, {}).get("role") != "teacher":
                self.send_json({"error": "İcazə yoxdur."}, 401)
                return
            body = self.read_body()
            deadline = (body.get("deadline") or "").strip()[:60]
            name = (body.get("name") or "").strip()
            if not name:
                self.send_json({"error": "Kursant adı göstərilməyib."}, 400)
                return
            db = load_db()
            if not any(name in members for members in db.get("teams", {}).values()):
                self.send_json({"error": "Kursant tapılmadı."}, 404)
                return
            dls = db.setdefault("deadlines", {})
            if deadline:
                dls[name] = deadline
            else:
                dls.pop(name, None)
            save_db(db)
            self.send_json({"success": True, "name": name, "deadline": deadline or None})

        elif path == "/api/cabinet-scores":
            auth = self.headers.get("Authorization", "")
            cid = verify_token(auth[7:].strip()) if auth.startswith("Bearer ") else None
            if not cid or CREDENTIALS.get(cid, {}).get("role") != "teacher":
                self.send_json({"error": "İcazə yoxdur."}, 401)
                return
            body = self.read_body()
            name = (body.get("name") or "").strip()
            if not name:
                self.send_json({"error": "Kursant adı göstərilməyib."}, 400)
                return

            def norm(v):
                if v is None or v == "":
                    return None
                try:
                    n = int(v)
                except (TypeError, ValueError):
                    return None
                return max(0, min(10, n))

            db = load_db()
            if not any(name in members for members in db.get("teams", {}).values()):
                self.send_json({"error": "Kursant tapılmadı."}, 404)
                return
            db.setdefault("scores", {})[name] = {
                "serbest": norm(body.get("serbest")),
                "defter": norm(body.get("defter")),
            }
            save_db(db)
            self.send_json({"success": True, "name": name, "scores": db["scores"][name]})

        elif path == "/api/cabinet-login":
            body = self.read_body()
            cid = (body.get("id") or "").strip().upper()
            password = body.get("password") or ""
            db = load_db()
            raw = raw_cred(cid, db)
            if not raw or cred_hash(cid, password) != raw.get("hash"):
                self.send_json({"error": "ID və ya şifrə yanlışdır!"}, 403)
                return
            cred = resolve_cred(cid, db)
            if not cred:
                self.send_json({"error": "Bu hesab deaktiv edilib."}, 403)
                return
            resp = {"token": make_token(cid, cred["role"]), "id": cid, "name": cred["name"], "role": cred["role"]}
            if cred["role"] == "student":
                resp["team"] = cred["team"]
            self.send_json(resp)

        elif path == "/api/status":
            body = self.read_body()
            if body.get("password", "") != ADMIN_PASSWORD:
                self.send_json({"error": "Admin şifrəsi yanlışdır!"}, 403)
                return
            db = load_db()
            self.send_json({
                "selections": db["selections"],
                "work_taken_by": db["work_taken_by"],
                "keys": db["keys"]
            })

        elif path == "/api/select":
            body = self.read_body()
            name = body.get("name", "")
            key = body.get("key", "")
            team = body.get("team", "")
            work_ids = body.get("work_ids", [])

            db = load_db()

            # Validate key
            if name not in db["keys"]:
                self.send_json({"error": "Bu kursant üçün açar təyin edilməyib. Müəllimlə əlaqə saxlayın."}, 403)
                return
            if db["keys"][name] != key:
                self.send_json({"error": "Açar yanlışdır!"}, 403)
                return

            # Fənn və iş sayı cari fənndən gəlir (s1 → 2 iş, s2 → 1 mövzu)
            ok, resp, code = select_works(db, name, team, work_ids)
            if ok:
                save_db(db)
            self.send_json(resp, code)

        elif path == "/api/admin/generate-keys":
            body = self.read_body()
            password = body.get("password", "")
            if password != ADMIN_PASSWORD:
                self.send_json({"error": "Admin şifrəsi yanlışdır!"}, 403)
                return

            db = load_db()
            team = body.get("team", "")
            if team and team in db["teams"]:
                for student in db["teams"][team]:
                    if student not in db["keys"]:
                        db["keys"][student] = generate_key()
            else:
                for team_members in db["teams"].values():
                    for student in team_members:
                        if student not in db["keys"]:
                            db["keys"][student] = generate_key()
            save_db(db)
            self.send_json({"success": True, "keys": db["keys"]})

        elif path == "/api/admin/set-key":
            body = self.read_body()
            password = body.get("password", "")
            if password != ADMIN_PASSWORD:
                self.send_json({"error": "Admin şifrəsi yanlışdır!"}, 403)
                return

            name = body.get("name", "")
            new_key = body.get("key", "")
            db = load_db()
            db["keys"][name] = new_key
            save_db(db)
            self.send_json({"success": True})

        elif path == "/api/admin/reset-selection":
            body = self.read_body()
            password = body.get("password", "")
            if password != ADMIN_PASSWORD:
                self.send_json({"error": "Admin şifrəsi yanlışdır!"}, 403)
                return

            name = body.get("name", "")
            db = load_db()
            if name in db["selections"]:
                # Find which team this student belongs to
                student_team = None
                for t, members in db["teams"].items():
                    if name in members:
                        student_team = t
                        break
                if student_team and student_team in db["work_taken_by"]:
                    for wid in db["selections"][name]:
                        if str(wid) in db["work_taken_by"][student_team] and db["work_taken_by"][student_team][str(wid)] == name:
                            del db["work_taken_by"][student_team][str(wid)]
                del db["selections"][name]
                save_db(db)
            self.send_json({"success": True})

        elif path == "/api/admin/reset-all":
            body = self.read_body()
            password = body.get("password", "")
            if password != ADMIN_PASSWORD:
                self.send_json({"error": "Admin şifrəsi yanlışdır!"}, 403)
                return

            db = load_db()
            db["selections"] = {}
            db["work_taken_by"] = {t: {} for t in db["teams"]}
            db["keys"] = {}
            save_db(db)
            self.send_json({"success": True})

        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    os.chdir(BASE_DIR)
    # ThreadingHTTPServer: brauzerin boş (preconnect) bağlantısı və ya asılmış sorğu bütün serveri bloklamasın
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Server running at http://localhost:{PORT}")
    print(f"Admin panel: http://localhost:{PORT}/admin")
    print(f"Admin password: {ADMIN_PASSWORD}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()
