# -*- coding: utf-8 -*-
"""Bazanın gündəlik ehtiyat nüsxəsi — B2-yə JSON kimi yazılır.

Vercel cron hər gecə /api/backup-ı çağırır; müəllim panelindən əl ilə də
alına bilir. Nüsxələr backups/db-YYYY-MM-DD.json açarında saxlanılır,
31 gündən köhnəsi avtomatik silinir. Bərpa: /api/backup-restore (müəllim,
bərpadan əvvəl cari vəziyyətin qoruyucu nüsxəsi yazılır).
"""
import json
import re
import time

import _b2

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _key(date):
    return f"{_b2.key_prefix()}backups/db-{date}.json"


def run_backup(db):
    """(ok, key_or_error). Bugünkü nüsxəni yazır, 31 gün əvvəlkini silir."""
    if not _b2.is_configured():
        return False, "Fayl anbarı konfiqurasiya olunmayıb."
    date = time.strftime("%Y-%m-%d")
    data = json.dumps(db, ensure_ascii=False).encode("utf-8")
    if not _b2.put_object(_key(date), data):
        return False, "Nüsxə anbara yazıla bilmədi."
    old = time.strftime("%Y-%m-%d", time.localtime(time.time() - 31 * 86400))
    _b2.delete_object(_key(old))
    return True, _key(date)


def read_backup(date):
    """Verilən tarixin nüsxəsi (dict) və ya None."""
    if not _DATE_RE.fullmatch(date or ""):
        return None
    data = _b2.read_object(_key(date))
    if data is None:
        return None
    try:
        return json.loads(data)
    except ValueError:
        return None


def save_prerestore(db):
    """Bərpadan əvvəl cari vəziyyətin qoruyucu nüsxəsi."""
    ts = time.strftime("%Y-%m-%d-%H%M%S")
    key = f"{_b2.key_prefix()}backups/pre-restore-{ts}.json"
    _b2.put_object(key, json.dumps(db, ensure_ascii=False).encode("utf-8"))
    return key
