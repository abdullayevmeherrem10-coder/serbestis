# -*- coding: utf-8 -*-
"""Firebase Realtime Database üçün service-account OAuth tokeni.

FIREBASE_SERVICE_ACCOUNT env dəyişəni (JSON mətn) və ya lokal
firebase_service_account.json faylından oxunur. Token proses daxilində
keşlənir və bitməyə yaxın yenilənir.
"""
import json
import os
import time

_SCOPES = [
    "https://www.googleapis.com/auth/firebase.database",
    "https://www.googleapis.com/auth/userinfo.email",
]

_creds = None
_loaded = False


def _load_creds():
    global _creds, _loaded
    if _loaded:
        return _creds
    _loaded = True
    info = None
    raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT", "").strip()
    if raw:
        try:
            info = json.loads(raw)
        except Exception:
            info = None
    if info is None:
        here = os.path.dirname(os.path.abspath(__file__))
        for path in (
            os.path.join(here, "firebase_service_account.json"),
            os.path.join(os.path.dirname(here), "firebase_service_account.json"),
        ):
            if os.path.exists(path):
                try:
                    with open(path, encoding="utf-8") as f:
                        info = json.load(f)
                    break
                except Exception:
                    pass
    if info is None:
        return None
    try:
        from google.oauth2 import service_account
        _creds = service_account.Credentials.from_service_account_info(info, scopes=_SCOPES)
    except Exception:
        _creds = None
    return _creds


def get_access_token():
    """Etibarlı OAuth tokeni qaytarır (yoxdursa None — yazma açarsız gedər)."""
    creds = _load_creds()
    if creds is None:
        return None
    try:
        if not creds.valid or (creds.expiry and creds.expiry.timestamp() - time.time() < 60):
            import google.auth.transport.requests
            creds.refresh(google.auth.transport.requests.Request())
        return creds.token
    except Exception:
        return None
