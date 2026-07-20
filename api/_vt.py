# -*- coding: utf-8 -*-
"""VirusTotal v3 API — yüklənən faylların virus yoxlanışı (kənar kitabxanasız).

Açar: VT_API_KEY env dəyişəni (Vercel), yoxdursa layihə kökündəki
gitignore-lanmış vt_secret.txt (lokal). Pulsuz plan: 4 sorğu/dəq, 500/gün.

Axın: fayl B2-dən endirilir → VT-yə göndərilir → analysis id qaytarılır →
nəticə sonradan get_analysis() ilə soruşulur (asinxrondur, adətən 1-2 dəq).
"""
import json
import os
import secrets
import urllib.request as urlreq

API = "https://www.virustotal.com/api/v3"


def _key():
    k = os.environ.get("VT_API_KEY", "")
    if k:
        return k
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vt_secret.txt")
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def is_configured():
    return bool(_key())


def scan_bytes(data, fname):
    """Faylı VT-yə göndərir; analysis id və ya None qaytarır."""
    key = _key()
    if not key:
        return None
    boundary = "----sapyor" + secrets.token_hex(12)
    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in fname)[:80] or "file"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{safe_name}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode("utf-8") + data + f"\r\n--{boundary}--\r\n".encode("utf-8")
    req = urlreq.Request(
        f"{API}/files",
        data=body,
        headers={
            "x-apikey": key,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    try:
        with urlreq.urlopen(req, timeout=50) as r:
            resp = json.loads(r.read())
        return resp.get("data", {}).get("id")
    except Exception:
        return None


def get_analysis(analysis_id):
    """{"status": "completed"|"queued", "malicious": n, "suspicious": n} və ya None."""
    key = _key()
    if not key or not analysis_id:
        return None
    req = urlreq.Request(f"{API}/analyses/{analysis_id}", headers={"x-apikey": key})
    try:
        with urlreq.urlopen(req, timeout=20) as r:
            resp = json.loads(r.read())
        attrs = resp.get("data", {}).get("attributes", {})
        stats = attrs.get("stats", {}) or {}
        return {
            "status": attrs.get("status", "queued"),
            "malicious": int(stats.get("malicious", 0) or 0),
            "suspicious": int(stats.get("suspicious", 0) or 0),
        }
    except Exception:
        return None
