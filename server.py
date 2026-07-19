# -*- coding: utf-8 -*-
import http.server
import base64
import hashlib
import hmac
import json
import os
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
        return json.load(f)

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

# Kabinet token sistemi (HMAC imzalı, 12 saat etibarlı)
TOKEN_TTL = 12 * 3600
CABINET_SECRET = os.environ.get('CABINET_SECRET') or hashlib.sha256(
    ("cab|" + ADMIN_PASSWORD + "|" + "|".join(sorted(c["hash"] for c in CREDENTIALS.values()))).encode("utf-8")
).hexdigest()

def make_token(cid):
    payload = json.dumps({"id": cid, "exp": int(time.time()) + TOKEN_TTL})
    b = base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii").rstrip("=")
    sig = hmac.new(CABINET_SECRET.encode("utf-8"), b.encode("ascii"), hashlib.sha256).hexdigest()[:32]
    return f"{b}.{sig}"

def verify_token(token):
    try:
        b, sig = token.split(".")
        good = hmac.new(CABINET_SECRET.encode("utf-8"), b.encode("ascii"), hashlib.sha256).hexdigest()[:32]
        if not hmac.compare_digest(sig, good):
            return None
        payload = json.loads(base64.urlsafe_b64decode(b + "=" * (-len(b) % 4)))
        if payload.get("exp", 0) < time.time():
            return None
        cid = payload.get("id", "")
        return cid if cid in CREDENTIALS else None
    except Exception:
        return None

def student_results(name, team):
    for group, data in RESULTS.items():
        if data["team"] == team:
            return {
                "group": group,
                "kollok": data["kollok"].get(name),
                "menimseme": data["menimseme"].get(name),
                "imtahan": data["imtahan"].get(name),
            }
    return {"group": None, "kollok": None, "menimseme": None, "imtahan": None}

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

        if path == "/api/teams":
            db = load_db()
            self.send_json({"teams": {t: members for t, members in db["teams"].items()}})

        elif path == "/api/works":
            params = urllib.parse.parse_qs(parsed.query)
            team = params.get("team", [""])[0]
            db = load_db()
            team_taken = db["work_taken_by"].get(team, {})
            works = []
            for i, w in enumerate(db["works"]):
                taken_by = team_taken.get(str(i))
                works.append({
                    "id": i,
                    "title": w,
                    "taken": taken_by is not None,
                    "taken_by": taken_by
                })
            self.send_json({"works": works})

        elif path == "/api/cabinet-data":
            auth = self.headers.get("Authorization", "")
            cid = verify_token(auth[7:].strip()) if auth.startswith("Bearer ") else None
            if not cid:
                self.send_json({"error": "Sessiya bitib. Yenidən daxil olun."}, 401)
                return
            cred = CREDENTIALS[cid]
            db = load_db()
            if cred.get("role") == "teacher":
                self.send_json({
                    "role": "teacher",
                    "name": cred.get("name", "Müəllim"),
                    "results": RESULTS,
                    "selections": db.get("selections", {}),
                    "scores": db.get("scores", {}),
                    "deadlines": db.get("deadlines", {}),
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
                "results": student_results(name, cred["team"]),
                "scores": db.get("scores", {}).get(name),
                "deadline": db.get("deadlines", {}).get(name),
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
            elif path == "/admin":
                path = "/admin.html"

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

            if os.path.isfile(file_path):
                mime, _ = mimetypes.guess_type(file_path)
                if mime is None:
                    mime = "application/octet-stream"
                with open(file_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", len(content))
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

        if path == "/api/cabinet-deadline":
            auth = self.headers.get("Authorization", "")
            cid = verify_token(auth[7:].strip()) if auth.startswith("Bearer ") else None
            if not cid or CREDENTIALS[cid].get("role") != "teacher":
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
            if not cid or CREDENTIALS[cid].get("role") != "teacher":
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
            cred = CREDENTIALS.get(cid)
            if not cred or cred_hash(cid, password) != cred.get("hash"):
                self.send_json({"error": "ID və ya şifrə yanlışdır!"}, 403)
                return
            resp = {"token": make_token(cid), "id": cid, "name": cred.get("name", "")}
            if cred.get("role") == "teacher":
                resp["role"] = "teacher"
            else:
                resp["role"] = "student"
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

            # Check if already selected
            if name in db["selections"] and len(db["selections"][name]) >= 2:
                self.send_json({"error": "Siz artıq 2 sərbəst iş seçmisiniz!"}, 400)
                return

            # Check work count
            if len(work_ids) != 2:
                self.send_json({"error": "Tam olaraq 2 sərbəst iş seçməlisiniz!"}, 400)
                return

            # Check availability per team
            team_taken = db["work_taken_by"].get(team, {})
            for wid in work_ids:
                taken = team_taken.get(str(wid))
                if taken and taken != name:
                    title = db["works"][wid] if wid < len(db["works"]) else "?"
                    self.send_json({"error": f"'{title}' artıq başqası tərəfindən seçilib!"}, 409)
                    return

            # Save selections
            db["selections"][name] = work_ids
            if team not in db["work_taken_by"]:
                db["work_taken_by"][team] = {}
            for wid in work_ids:
                db["work_taken_by"][team][str(wid)] = name
            save_db(db)

            selected_titles = [db["works"][wid] for wid in work_ids]
            self.send_json({"success": True, "message": "Seçimləriniz uğurla qeydə alındı!", "selected": selected_titles})

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
    server = http.server.HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Server running at http://localhost:{PORT}")
    print(f"Admin panel: http://localhost:{PORT}/admin")
    print(f"Admin password: {ADMIN_PASSWORD}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()
