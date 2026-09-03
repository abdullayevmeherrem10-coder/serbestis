# -*- coding: utf-8 -*-
"""Sərbəst iş fənnləri — cari fənn semestr parametridir (Parametrlər → Fənn seçimi).

- s1 — Hərbi Mühəndis Texnikası: 50 iş, hər kursant 2 iş seçir (2-ci kurs).
- s2 — Hərbi Mühəndis Hazırlığı: 25 mövzu, hər kursant 1 mövzu seçir (4-cü kurs).

Cari fənn db["subject_id"] (s1|s2); yoxdursa db["subject"] adına görə tapılır, o da uyğun
gəlmirsə s2. Fənn dəyişəndə db["subject"] (başlıq/arxiv üçün ad) da dəyişir. Bütün taqımlar
cari fənnin sərbəst iş siyahısını görür. Hər işin fənni db["work_subjects"][i]
(db["works"] ilə eyni indeks; çatışmayan = s1). Hər kursantın bir sərbəst iş balı var
(db["scores"][ad]["serbest"]), mənimsəmə düsturu hər fənn üçün eynidir.
Hər iş taqım daxilində bir kursanta verilir (db["work_taken_by"]).
"""

SUBJECTS = [
    {"id": "s1", "name": "Hərbi Mühəndis Texnikası", "pick": 2},
    {"id": "s2", "name": "Hərbi Mühəndis Hazırlığı", "pick": 1},
]
SUBJECT_IDS = [s["id"] for s in SUBJECTS]
SUBJECT_NAMES = {s["id"]: s["name"] for s in SUBJECTS}
DEFAULT_SUBJECT_ID = "s2"   # parametri olmayan baza — mövcud kursantlar 4-cü kursdur

# İkinci fənnin mövzuları — bazaya bir dəfə əlavə olunur (ensure_subject2_topics)
S2_TOPICS = [
    "Hərbi mühəndis hazırlığının məqsədi, vəzifələri və əhəmiyyəti",
    "Azərbaycan Ordusunda Mühəndis Qoşunlarının yaranması və inkişafı",
    "Mühəndis qoşunlarının əsas vəzifələri və fəaliyyət istiqamətləri",
    "Müasir döyüşlərdə hərbi mühəndis təminatının rolu",
    "Fortifikasiya qurğularının növləri və əhəmiyyəti",
    "Səngər və sığınacaqların şəxsi heyətin mühafizəsində rolu",
    "Hərbi əməliyyatlarda maskalanmanın əhəmiyyəti",
    "Müasir hərbi texnikanın döyüş əməliyyatlarında rolu",
    "Pilotsuz uçuş aparatlarının müasir müharibələrdə rolu",
    "Mühəndis maneələrinin növləri və onların əhəmiyyəti",
    "Hərbi yolların salınması və bərpasında mühəndis qoşunlarının rolu",
    "Hərbi körpülərin əhəmiyyəti və mühəndis qoşunlarının fəaliyyəti",
    "Mina təhlükəsi və ondan qorunma qaydaları",
    "Minalar və partlamamış hərbi sursatların insan təhlükəsizliyi və ətraf mühit üçün yaratdığı risklər",
    "Azərbaycanda minatəmizləmə fəaliyyətinin təşkili",
    "ANAMA-nın fəaliyyəti və əsas vəzifələri",
    "İşğaldan azad edilmiş ərazilərdə minatəmizləmə işləri",
    "İşğaldan azad edilmiş ərazilərdə yolların və infrastrukturun bərpası",
    "Qarabağ və Şərqi Zəngəzurda aparılan quruculuq və bərpa işləri",
    "Mühəndis qoşunlarının sülh və müharibə dövründə fəaliyyəti",
    "PMN-2 piyada əleyhinə minası və onun ümumi xüsusiyyətləri",
    "TM-62M tank əleyhinə minası və onun təyinatı",
    "Minatəmizləmə prosesində süni intellekt texnologiyalarının tətbiqi",
    "Minatəmizləmə prosesində ən müasir və qabaqcıl texnologiyaların tətbiqi",
    "Minatəmizləmə fəaliyyətlərində xüsusi təlim keçmiş heyvanlardan istifadə",
]


def subjects_of(db):
    """[{id, name, pick}] — UI üçün fənn siyahısı."""
    return [dict(s) for s in SUBJECTS]


def subject_by_id(db, sid):
    for s in SUBJECTS:
        if s["id"] == sid:
            return dict(s)
    return None


# ───────────────────────── cari fənn ─────────────────────────

def current_subject(db):
    """Cari fənn (s1|s2): db.subject_id; yoxdursa db.subject adına görə; o da yoxdursa s2."""
    sid = db.get("subject_id")
    if sid in SUBJECT_IDS:
        return sid
    name = (db.get("subject") or "").strip().casefold()
    for s in SUBJECTS:
        if s["name"].casefold() == name:
            return s["id"]
    return DEFAULT_SUBJECT_ID


def set_current_subject(db, sid):
    """Müəllim fənni seçir: id və ad (başlıq/arxiv üçün) birlikdə yazılır. Uğurludursa True."""
    if sid not in SUBJECT_IDS:
        return False
    db["subject_id"] = sid
    db["subject"] = SUBJECT_NAMES[sid]
    return True


def current_pick(db):
    """Hər kursantın seçməli olduğu iş sayı (cari fənnə görə)."""
    return subject_by_id(db, current_subject(db))["pick"]


# ───────────────────────── işlərin fənni ─────────────────────────

def work_subjects(db):
    """db.works ilə eyni uzunluqda fənn siyahısı (çatışmayanlar s1)."""
    ws = [w if w in SUBJECT_IDS else "s1" for w in (db.get("work_subjects") or [])]
    n = len(db.get("works", []))
    return ws[:n] + ["s1"] * max(0, n - len(ws))


def work_subject(db, wid):
    ws = work_subjects(db)
    return ws[wid] if 0 <= wid < len(ws) else "s1"


# ───────────────────────── seçim ─────────────────────────

def works_payload(db, team):
    """/api/works cavabı — yalnız cari fənnə aid işlər, taqım üzrə tutulma ilə.

    id — qlobal indeks (selections/work_taken_by bununla işləyir), num — fənn daxilində sıra (1..N).
    """
    sid = current_subject(db)
    team_taken = db.get("work_taken_by", {}).get(team, {})
    ws = work_subjects(db)
    out, n = [], 0
    for i, title in enumerate(db.get("works", [])):
        if ws[i] != sid:
            continue
        n += 1
        taken_by = team_taken.get(str(i))
        out.append({
            "id": i,
            "num": n,
            "subject": sid,
            "title": title,
            "taken": taken_by is not None,
            "taken_by": taken_by,
        })
    return out


def select_works(db, name, team, work_ids):
    """Kursantın seçimini yoxlayıb bazaya yazır (save_db çağıran tərəfdədir).

    Fənn və iş sayı cari fənndən gəlir. Qaytarır (ok, cavab, http_kod).
    Açar/şifrə yoxlanışı çağıran tərəfdə aparılır.
    """
    sid = current_subject(db)
    pick = subject_by_id(db, sid)["pick"]
    try:
        work_ids = [int(w) for w in (work_ids or [])]
    except (TypeError, ValueError):
        return False, {"error": "İş siyahısı yanlışdır."}, 400
    works = db.get("works", [])
    ws = work_subjects(db)
    if len(db.get("selections", {}).get(name, [])) >= pick:
        return False, {"error": "Siz artıq sərbəst iş seçmisiniz!"}, 400
    if len(work_ids) != pick or len(set(work_ids)) != pick:
        return False, {"error": f"Tam olaraq {pick} sərbəst iş seçməlisiniz!"}, 400
    for wid in work_ids:
        if not (0 <= wid < len(works)) or ws[wid] != sid:
            return False, {"error": "Seçilən mövzu cari fənnə aid deyil."}, 400
    team_taken = db.setdefault("work_taken_by", {}).setdefault(team, {})
    for wid in work_ids:
        taken = team_taken.get(str(wid))
        if taken and taken != name:
            return False, {"error": f"'{works[wid]}' artıq başqası tərəfindən seçilib!"}, 409
    db.setdefault("selections", {})[name] = work_ids
    for wid in work_ids:
        team_taken[str(wid)] = name
    return True, {
        "success": True,
        "message": "Seçimləriniz uğurla qeydə alındı!",
        "subject": sid,
        "selected": [works[w] for w in work_ids],
    }, 200


def reset_selection(db, name):
    """Kursantın seçimini sıfırlayır (bütün taqımlarda tutduğu işlər boşalır)."""
    db.get("selections", {}).pop(name, None)
    for team, taken in db.get("work_taken_by", {}).items():
        db["work_taken_by"][team] = {w: n for w, n in taken.items() if n != name}


def reset_all_selections(db):
    """Bütün kursantların seçimini sıfırlayır (ballara toxunmur)."""
    db["selections"] = {}
    db["work_taken_by"] = {t: {} for t in db.get("teams", {})}


# ───────────────────────── miqrasiya ─────────────────────────

def ensure_subject2_topics(db):
    """İkinci fənnin mövzularını bazaya bir dəfə əlavə edir. Dəyişiklik olubsa True."""
    if db.get("s2_topics_added"):
        return False
    works = db.setdefault("works", [])
    ws = work_subjects(db)
    for title in S2_TOPICS:
        if title not in works:
            works.append(title)
            ws.append("s2")
    db["work_subjects"] = ws
    db["s2_topics_added"] = True
    return True
