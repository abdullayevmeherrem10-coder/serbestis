# -*- coding: utf-8 -*-
"""2024 qəbulun arxivlənmiş imtahan nəticələri — yalnız müəllimə verilir
(GET /api/arxiv-imtahan). Mənbə: arxiv/imtahan_2024.json (insan üçün nüsxə).
"""
import json

ARXIV_IMTAHAN = json.loads(r'''{
  "təsvir": "2024 qəbul — imtahan nəticələri (arxiv). Digər 2024 məlumatları sahibin istəyi ilə silinib.",
  "arxivlənmə_tarixi": "2026-07-31",
  "mənbə": "api/_results.py (commit 4fa6b69) + backups/db-2026-07-31.json (exam_scores/renames)",
  "qruplar": {
    "YT 24A1": {
      "Abbasov Ramal Ramil oğlu": [
        "74",
        "C “Yaxşı”"
      ],
      "Ağabalayev Oktay Mahmud oğlu": [
        "84",
        "B “Çox yaxşı”"
      ],
      "Axundzadə Onur Zəki oğlu": [
        "91",
        "A “Əla”"
      ],
      "Allahverdiyev Ümid Elmir oğlu": [
        "91",
        "A “Əla”"
      ],
      "Eldarlı Hüseyn Baba oğlu": [
        "92",
        "A “Əla”"
      ],
      "Ələkbərli Məhəmməd Elmar oğlu": [
        "92",
        "A “Əla”"
      ],
      "Əliyev Anar Alim oğlu": [
        "61",
        "D “Kafi”"
      ],
      "Əliyev Vahid Surxay oğlu": [
        "52",
        "E “Qənaətbəxş”"
      ],
      "İsmayılov Nihad Habil oğlu": [
        "53",
        "E “Qənaətbəxş”"
      ],
      "Kərimli Eşqin Niyaməddin oğlu": [
        "82",
        "B “Çox yaxşı”"
      ],
      "Qardiyev Nicat Elməddin oğlu": [
        "72",
        "C “Yaxşı”"
      ],
      "Qasımov Fateh Taleh oğlu": [
        "73",
        "C “Yaxşı”"
      ],
      "Quliyev Rəvan Soltan oğlu": [
        "65",
        "D “Kafi”"
      ],
      "Qurbanov Nicat Amil oğlu": [
        "72",
        "C “Yaxşı”"
      ],
      "Məmmədli Polad Faiq oğlu": [
        "59",
        "E “Qənaətbəxş”"
      ],
      "Məmmədov Bəhman Mehman oğlu": [
        "81",
        "B “Çox yaxşı”"
      ],
      "Məmmədov Rəşid Rəşad oğlu": [
        "69",
        "D “Kafi”"
      ],
      "Rəhimzadə Ramin Səbuhi oğlu": [
        "64",
        "D “Kafi”"
      ],
      "Sadıqov Kəmaləddin Seyfəddin oğlu": [
        "93",
        "A “Əla”"
      ],
      "Tağıyev Ziya Zaur oğlu": [
        "57",
        "E “Qənaətbəxş”"
      ],
      "Vəliyev Qalib Cəlil oğlu": [
        "52",
        "E “Qənaətbəxş”"
      ],
      "Yaqubzadə Yaqub Səbuhi oğlu": [
        "76",
        "C “Yaxşı”"
      ],
      "Yusifzadə Mahmud Natiq oğlu": [
        "69",
        "D “Kafi”"
      ],
      "Zəkiyev Sadıq Mehman oğlu": [
        "71",
        "C “Yaxşı”"
      ]
    },
    "YT 24A2": {
      "Abdurahmanov Ziya Valeh oğlu": [
        "72",
        "C “Yaxşı”"
      ],
      "Ağazadə Abdullah İntizam oğlu": [
        "58",
        "E “Qənaətbəxş”"
      ],
      "Alıyev Azin Yolçu oğlu": [
        "71",
        "C “Yaxşı”"
      ],
      "Baxşıyev Raul Şamo oğlu": [
        "56",
        "E “Qənaətbəxş”"
      ],
      "Bəyişov Arif Neymət oğlu": [
        "92",
        "A “Əla”"
      ],
      "Çingizli İlçin İlham oğlu": [
        "71",
        "C “Yaxşı”"
      ],
      "Davudov Qail Qabil oğlu": [
        "61",
        "D “Kafi”"
      ],
      "Əyyubov Fərhad İlqar oğlu": [
        "71",
        "C “Yaxşı”"
      ],
      "Həmidov İsmail Ramiz oğlu": [
        "53",
        "E “Qənaətbəxş”"
      ],
      "Hüseynli Fərid Şaiq oğlu": [
        "70",
        "D “Kafi”"
      ],
      "Hüseynov Əbutalib Bəhram oğlu": [
        null,
        "İştirak etmədi"
      ],
      "Hüseynov Əli Çingiz oğlu": [
        "92",
        "A “Əla”"
      ],
      "Hüseynov Zaur Bəhruz oğlu": [
        "70",
        "D “Kafi”"
      ],
      "Qasımov Əli Taleh oğlu": [
        "82",
        "B “Çox yaxşı”"
      ],
      "Qənbərov Hüseyn İsaq oğlu": [
        "91",
        "A “Əla”"
      ],
      "Qurbanov Tuncay Turan oğlu": [
        "91",
        "A “Əla”"
      ],
      "Qurbanov Vasif Xeyrəddin oğlu": [
        "87",
        "B “Çox yaxşı”"
      ],
      "Məmmədli Ənnağı Qalib oğlu": [
        "93",
        "A “Əla”"
      ],
      "Məmmədov Bəyiş Ülkər oğlu": [
        "84",
        "B “Çox yaxşı”"
      ],
      "Mustafayev Adəm Səyyad oğlu": [
        "72",
        "C “Yaxşı”"
      ],
      "Novruzov Nihat Eyvaz oğlu": [
        "55",
        "E “Qənaətbəxş”"
      ],
      "Səfxanlı İslam Elşən oğlu": [
        "54",
        "E “Qənaətbəxş”"
      ],
      "Şıxıyev Farid Ravid oğlu": [
        "72",
        "C “Yaxşı”"
      ],
      "Vəliyev Cəlal Arzu oğlu": [
        "75",
        "C “Yaxşı”"
      ],
      "Vəliyev Elsevər Eldəniz oğlu": [
        "72",
        "C “Yaxşı”"
      ]
    }
  }
}''')


# ───────── Dinamik arxiv: müəllim semestr sonunda yazır, db["arxiv"] siyahısında saxlanılır ─────────
# Giriş: {id, semester, subject, ts, qruplar: {taqım: {ad: {k1,k2,k3,koll,serbest,defter,menimseme,imtahan,qiymet}}}}
# Statik 2024 arxivi (yuxarıdakı ARXIV_IMTAHAN) eyni formata çevrilib siyahının sonuna əlavə olunur (static=True).
import time as _time

ARXIV_MAX = 30
_ROW_FIELDS = ("k1", "k2", "k3", "serbest", "defter", "imtahan")


def _static_entry():
    qruplar = {}
    for group, rows in (ARXIV_IMTAHAN.get("qruplar") or {}).items():
        out = {}
        for name, v in rows.items():
            try:
                bal = int(v[0])
            except (TypeError, ValueError, IndexError):
                bal = None
            out[name] = {"k1": None, "k2": None, "k3": None, "koll": None, "serbest": None, "defter": None,
                         "menimseme": None, "imtahan": bal,
                         "qiymet": v[1] if isinstance(v, (list, tuple)) and len(v) > 1 else None}
        qruplar[group] = out
    return {"id": "2024-qebul", "static": True, "semester": "2024 qəbul", "subject": "yalnız imtahan nəticələri",
            "ts": ARXIV_IMTAHAN.get("arxivlənmə_tarixi", ""), "qruplar": qruplar}


def arxiv_entries(db):
    """Bütün arxiv girişləri: dinamiklər (yenidən köhnəyə) + statik 2024."""
    return list(db.get("arxiv", [])) + [_static_entry()]


def _int_or_none(v):
    if v is None or v == "":
        return None
    return int(v)


def arxiv_clean_rows(qruplar, grade_fn):
    """Müştəridən gələn snapshot-u yoxlayır; koll./mənimsəmə cəmini və qiyməti serverdə hesablayır.
    Etibarsızdırsa None."""
    if not isinstance(qruplar, dict) or not qruplar or len(qruplar) > 20:
        return None
    out = {}
    for team, rows in qruplar.items():
        if not isinstance(team, str) or not team.strip() or not isinstance(rows, dict) or len(rows) > 200:
            return None
        clean = {}
        for name, r in rows.items():
            if not isinstance(name, str) or not name.strip() or not isinstance(r, dict):
                return None
            try:
                vals = {f: _int_or_none(r.get(f)) for f in _ROW_FIELDS}
            except (TypeError, ValueError):
                return None
            for f in ("k1", "k2", "k3", "serbest", "defter"):
                if vals[f] is not None:
                    vals[f] = max(0, min(10, vals[f]))
            if vals["imtahan"] is not None:
                vals["imtahan"] = max(0, min(100, vals["imtahan"]))
            ks = [vals["k1"], vals["k2"], vals["k3"]]
            koll = sum(v for v in ks if v is not None) if any(v is not None for v in ks) else None
            has_men = koll is not None or vals["serbest"] is not None or vals["defter"] is not None
            vals["koll"] = koll
            vals["menimseme"] = ((koll or 0) + (vals["serbest"] or 0) + (vals["defter"] or 0)) if has_men else None
            vals["qiymet"] = grade_fn(vals["imtahan"]) if vals["imtahan"] is not None else None
            clean[name.strip()[:70]] = vals
        out[team.strip()[:40]] = clean
    return out


def arxiv_add(db, semester, subject, qruplar):
    """Yeni girişi siyahının əvvəlinə qoyur (ən çoxu ARXIV_MAX saxlanılır); girişi qaytarır."""
    entry = {
        "id": _time.strftime("%Y%m%d-%H%M%S"),
        "semester": (semester or "").strip()[:60],
        "subject": (subject or "").strip()[:60],
        "ts": _time.strftime("%d.%m.%Y %H:%M"),
        "qruplar": qruplar,
    }
    arx = db.setdefault("arxiv", [])
    arx.insert(0, entry)
    del arx[ARXIV_MAX:]
    return entry


def arxiv_delete(db, eid):
    """Dinamik girişi silir (statik 2024 silinmir). Silindisə True."""
    arx = db.get("arxiv", [])
    for i, e in enumerate(arx):
        if e.get("id") == eid:
            del arx[i]
            return True
    return False


def arxiv_clear_semester(db):
    """Yeni semestr üçün cari balları və seçimləri təmizləyir; taqımlar, girişlər, fayllar qalır."""
    db["scores"] = {}
    db["exam_scores"] = {}
    db["kollok_scores"] = {}
    db["selections"] = {}
    db["deadlines"] = {}
    db["work_taken_by"] = {t: {} for t in db.get("teams", {})}
