# -*- coding: utf-8 -*-
"""Backblaze B2 (S3-uyğun API) üçün AWS SigV4 imzalama — kənar kitabxanasız.

Konfiq: B2_KEY_ID / B2_APP_KEY / B2_BUCKET / B2_ENDPOINT env dəyişənləri
(Vercel), yoxdursa layihə kökündəki b2_config.json (lokal server.py).

Fayllar brauzerdən birbaşa B2-yə presigned PUT ilə yüklənir, baxış/endirmə
presigned GET ilə gedir — fayl baytları heç vaxt bizim serverdən keçmir.
"""
import datetime
import hashlib
import hmac
import json
import os
import urllib.parse
import urllib.request as urlreq

_UNSIGNED = "UNSIGNED-PAYLOAD"


def _config():
    key_id = os.environ.get("B2_KEY_ID", "")
    app_key = os.environ.get("B2_APP_KEY", "")
    bucket = os.environ.get("B2_BUCKET", "")
    endpoint = os.environ.get("B2_ENDPOINT", "")
    if key_id and app_key and bucket and endpoint:
        return {"key_id": key_id, "app_key": app_key, "bucket": bucket, "endpoint": endpoint}
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "b2_config.json")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except OSError:
        return None


def is_configured():
    return _config() is not None


def _region(endpoint):
    # s3.us-west-004.backblazeb2.com → us-west-004
    parts = endpoint.split(".")
    return parts[1] if len(parts) >= 2 else "us-west-004"


def _quote(s, safe="-_.~"):
    return urllib.parse.quote(s, safe=safe)


def _hmac(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _signing_key(secret, date, region):
    k = _hmac(("AWS4" + secret).encode("utf-8"), date)
    k = _hmac(k, region)
    k = _hmac(k, "s3")
    return _hmac(k, "aws4_request")


def _canonical_query(params):
    pairs = []
    for k in sorted(params):
        pairs.append(_quote(k) + "=" + _quote(str(params[k])))
    return "&".join(pairs)


def presign(method, key, expires=600, extra_params=None):
    """Presigned URL (query-string auth). key ASCII olmalıdır."""
    cfg = _config()
    if not cfg:
        return None
    now = datetime.datetime.utcnow()
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date = now.strftime("%Y%m%d")
    region = _region(cfg["endpoint"])
    scope = f"{date}/{region}/s3/aws4_request"
    host = cfg["endpoint"]
    uri = "/" + cfg["bucket"] + "/" + _quote(key, safe="/-_.~")

    params = {
        "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
        "X-Amz-Credential": f"{cfg['key_id']}/{scope}",
        "X-Amz-Date": amz_date,
        "X-Amz-Expires": str(int(expires)),
        "X-Amz-SignedHeaders": "host",
    }
    if extra_params:
        params.update(extra_params)

    canonical = "\n".join([
        method,
        uri,
        _canonical_query(params),
        f"host:{host}\n",
        "host",
        _UNSIGNED,
    ])
    to_sign = "\n".join([
        "AWS4-HMAC-SHA256",
        amz_date,
        scope,
        hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    ])
    sig = hmac.new(_signing_key(cfg["app_key"], date, region), to_sign.encode("utf-8"),
                   hashlib.sha256).hexdigest()
    return f"https://{host}{uri}?{_canonical_query(params)}&X-Amz-Signature={sig}"


def presign_put(key, content_type, expires=600):
    return presign("PUT", key, expires)


def presign_get(key, expires=3600, filename=None, content_type=None, inline=False):
    extra = {}
    if content_type:
        extra["response-content-type"] = content_type
    if filename:
        disp = "inline" if inline else "attachment"
        # RFC 5987 — unicode fayl adları üçün
        extra["response-content-disposition"] = (
            f"{disp}; filename*=UTF-8''{_quote(filename)}"
        )
    elif inline:
        extra["response-content-disposition"] = "inline"
    return presign("GET", key, expires, extra)


def _signed_request(method, key, range_header=None, timeout=15):
    """Server tərəfdən imzalı sorğu (HEAD/GET/DELETE) — header-based SigV4."""
    cfg = _config()
    if not cfg:
        return None
    now = datetime.datetime.utcnow()
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date = now.strftime("%Y%m%d")
    region = _region(cfg["endpoint"])
    scope = f"{date}/{region}/s3/aws4_request"
    host = cfg["endpoint"]
    uri = "/" + cfg["bucket"] + "/" + _quote(key, safe="/-_.~")

    headers = {
        "host": host,
        "x-amz-content-sha256": _UNSIGNED,
        "x-amz-date": amz_date,
    }
    if range_header:
        headers["range"] = range_header
    signed_names = ";".join(sorted(headers))
    canonical_headers = "".join(f"{k}:{headers[k]}\n" for k in sorted(headers))
    canonical = "\n".join([method, uri, "", canonical_headers, signed_names, _UNSIGNED])
    to_sign = "\n".join([
        "AWS4-HMAC-SHA256",
        amz_date,
        scope,
        hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    ])
    sig = hmac.new(_signing_key(cfg["app_key"], date, region), to_sign.encode("utf-8"),
                   hashlib.sha256).hexdigest()
    headers["Authorization"] = (
        f"AWS4-HMAC-SHA256 Credential={cfg['key_id']}/{scope}, "
        f"SignedHeaders={signed_names}, Signature={sig}"
    )
    req_headers = {k: v for k, v in headers.items() if k != "host"}
    req = urlreq.Request(f"https://{host}{uri}", method=method, headers=req_headers)
    return urlreq.urlopen(req, timeout=timeout)


def head_object(key):
    """(size, ok) — fayl yoxdursa (None, False)."""
    try:
        with _signed_request("HEAD", key) as r:
            return int(r.headers.get("Content-Length", "0")), True
    except Exception:
        return None, False


def read_head_bytes(key, n=4):
    """Faylın ilk n baytı (magic yoxlaması üçün); alınmasa None."""
    try:
        with _signed_request("GET", key, range_header=f"bytes=0-{n - 1}") as r:
            return r.read(n)
    except Exception:
        return None


def read_object(key, timeout=45):
    """Faylın tam məzmunu (virus yoxlanışı üçün); alınmasa None."""
    try:
        with _signed_request("GET", key, timeout=timeout) as r:
            return r.read()
    except Exception:
        return None


def delete_object(key):
    try:
        with _signed_request("DELETE", key) as r:
            r.read()
        return True
    except Exception:
        return False
