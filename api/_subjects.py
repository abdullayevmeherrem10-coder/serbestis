# -*- coding: utf-8 -*-
"""Sərbəst iş fənnləri — cari fənn semestr parametridir (Parametrlər → Fənn seçimi).

- s1 — Hərbi Mühəndis Texnikası: 50 iş, hər kursant 2 iş seçir (2-ci kurs).
- s2 — Hərbi Mühəndis Hazırlığı: hər kursant 1 mövzu seçir (4-cü kurs). Mövzular iki qrupdur:
    "new" — Yeni mövzular (S2_TOPICS, 25): hər mövzu taqım daxilində bir kursanta;
    "old" — Köhnə mövzular (S2_OLD_TOPICS): hər mövzu BÜTÜN taqımlar üzrə bir kursanta və
            cəmi OLD_LIMIT (25) kursant seçə bilər — limit dolanda qalan köhnə mövzular bağlanır.
  Qrup db["work_groups"][i] (works ilə eyni indeks; boş = qrupsuz, s1 işləri kimi).
  Hansı qrupun aktiv olduğunu MÜƏLLİM seçir (Parametrlər → "Mövzu siyahısı", db["s2_group"]);
  kursant yalnız aktiv qrupun mövzularını görür, qrup adını bilmir (current_group).

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

# Köhnə mövzular — "old" qrupu (ensure_subject2_topics ilə bir dəfə əlavə olunur).
# Müəllimin verdiyi 40 addan 2-si təkrar idi (№18=№2, №22=№6) — bir dəfə saxlanılıb (38).
S2_OLD_TOPICS = [
    "Mühəndis qoşunlarının yaranması, təyinatı, məqsədi və tapşırıqları",
    "Mühəndis kəşfiyyatının məqsədi, tapşırıqları və ona qoyulan tələblər",
    "Mühəndis kəşfiyyatının güc və vasitələri",
    "Mühəndis kəşfiyyatının orqanları və kəşfiyyatın aparılma üsulları",
    "Fortifikasiya qurğularının təyinatı, döyüşdə rolu və təsnifatı",
    "Səngərin yerinin seçilməsi",
    "Atıcı silahlar üçün səngərlər",
    "Manqa üçün səngərin qurulması, təchizatı və maskalanması",
    "Tranşey və əlaqələndirmə xəndəkləri",
    "Komanda müşahidə məntəqələri və müşahidə məntəqələri üçün açıq və örtülü qurğular",
    "Tağım dayaq məntəqəsinin elementləri və mühəndis cəhətdən qurulması ardıcıllığı",
    "Tank, PDM və ZTR üçün səngərlər",
    "Şəxsi heyətin qorunması üçün qurğular",
    "Texnika və material vasitələri üçün qurğular",
    "İdarəetmə məntəqələri üçün qurğular",
    "Ərazi relyefinin fortifikasiya qurğularının qurulmasına təsiri",
    "Xüsusi şəraitlərdə qurulan qurğular",
    "Mühəndis kəşfiyyatının güc və vasitələri, orqanları və aparılma üsulları",
    "İstehkam əl alətləri",
    "Mövqe ləvazimatları",
    "Qışda döyüş və əlaqə səngərlərinin hazırlanması",
    "Zenit vasitələri üçün səngərlər",
    "Maskalanmanın məqsədi, təşkilati və digər tədbirləri, əsas üsulları",
    "Sənayedə hazırlanan tabel maskalanma vasitələri",
    "Qoşunlarda hazırlanan maskalanma vasitələri",
    "Təqlid vasitələri və üsulları",
    "Şəxsi heyətin maskalanmasını pozan əsas əlamətləri",
    "Mühəndis maneələrinin təyinatı, təsnifatı, hazırlıq dərəcələri",
    "Tank əleyhinə minalar",
    "Piyada əleyhinə minalar",
    "Partlamayan maneələr",
    "Mina sahələri, onların qurulması və saxlanılması",
    "Su maneələrinin xüsusiyyətləri və su maneələrində keçidlərin kəşfiyyatı",
    "Su maneələrindən keçmə vasitələri",
    "Hərbi və kolon yolları təyinatı, növləri",
    "Hərbi yollara qoyulan tələblər və onun elementləri",
    "Hərbi yol nişanları, kolon yollarının saxlanılması",
    "Qoşunların su təminatı və su tələbat normaları",
]

# Mövzu qrupları (yalnız s2): id → UI adı. "old" qrupu üzrə ümumi seçim limiti.
WORK_GROUPS = {"new": "Yeni mövzular", "old": "Köhnə mövzular"}
OLD_LIMIT = 25


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


def current_group(db):
    """s2 üçün aktiv mövzu qrupu (new|old) — kursantlar yalnız bunu görür. Default "new"."""
    g = db.get("s2_group")
    return g if g in WORK_GROUPS else "new"


def set_current_group(db, g):
    """Müəllim aktiv mövzu qrupunu seçir. Uğurludursa True."""
    if g not in WORK_GROUPS:
        return False
    db["s2_group"] = g
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


def work_groups(db):
    """db.works ilə eyni uzunluqda qrup siyahısı ("new" | "old" | "" — qrupsuz)."""
    wg = [g if g in WORK_GROUPS else "" for g in (db.get("work_groups") or [])]
    n = len(db.get("works", []))
    return wg[:n] + [""] * max(0, n - len(wg))


def _old_taken(db):
    """Köhnə mövzular bütün taqımlar üzrə birdir: {iş_id(str): kursant}."""
    wg = work_groups(db)
    out = {}
    for taken in db.get("work_taken_by", {}).values():
        for k, who in taken.items():
            if k.isdigit() and int(k) < len(wg) and wg[int(k)] == "old":
                out[k] = who
    return out


def old_topics_meta(db):
    """/api/works cavabına: {"old_limit": 25, "old_used": N, "groups": {...}}."""
    return {"old_limit": OLD_LIMIT, "old_used": len(_old_taken(db)), "groups": dict(WORK_GROUPS),
            "group": current_group(db)}


# ───────────────────────── seçim ─────────────────────────

def works_payload(db, team):
    """/api/works cavabı — yalnız cari fənnə və (s2-də) aktiv qrupa aid işlər, tutulma ilə.

    id — qlobal indeks (selections/work_taken_by bununla işləyir), num — siyahı daxilində sıra (1..N).
    group — "new" | "old" | "" ; "old" mövzular bütün taqımlar üzrə tutulur, limit dolanda locked=True.
    """
    sid = current_subject(db)
    cg = current_group(db) if sid == "s2" else ""
    team_taken = db.get("work_taken_by", {}).get(team, {})
    old_taken = _old_taken(db)
    old_full = len(old_taken) >= OLD_LIMIT
    ws = work_subjects(db)
    wg = work_groups(db)
    out, nums = [], {}
    for i, title in enumerate(db.get("works", [])):
        if ws[i] != sid or wg[i] != cg:
            continue
        g = wg[i]
        nums[g] = nums.get(g, 0) + 1
        taken_by = old_taken.get(str(i)) if g == "old" else team_taken.get(str(i))
        out.append({
            "id": i,
            "num": nums[g],
            "subject": sid,
            "group": g,
            "title": title,
            "taken": taken_by is not None,
            "taken_by": taken_by,
            "locked": g == "old" and taken_by is None and old_full,
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
    wg = work_groups(db)
    cg = current_group(db) if sid == "s2" else ""
    for wid in work_ids:
        if not (0 <= wid < len(works)) or ws[wid] != sid or wg[wid] != cg:
            return False, {"error": "Seçilən mövzu cari siyahıya aid deyil."}, 400
    old_taken = _old_taken(db)
    team_taken = db.setdefault("work_taken_by", {}).setdefault(team, {})
    for wid in work_ids:
        # Köhnə mövzu: bütün taqımlar üzrə bir kursanta, cəmi OLD_LIMIT seçim
        taken = old_taken.get(str(wid)) if wg[wid] == "old" else team_taken.get(str(wid))
        if taken and taken != name:
            return False, {"error": f"'{works[wid]}' artıq başqası tərəfindən seçilib!"}, 409
        if wg[wid] == "old" and not taken and len(old_taken) >= OLD_LIMIT:
            return False, {"error": f"Köhnə mövzular üzrə limit ({OLD_LIMIT} kursant) dolub — yeni mövzulardan seçin."}, 409
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
    """İkinci fənnin mövzularını bazaya bir dəfə əlavə edir. Dəyişiklik olubsa True.

    1) S2_TOPICS → s2 (bayraq s2_topics_added);
    2) mövcud s2 işləri "new" qrupuna, S2_OLD_TOPICS → s2/"old" (bayraq s2_old_topics_added).
    """
    changed = False
    works = db.setdefault("works", [])
    if not db.get("s2_topics_added"):
        ws = work_subjects(db)
        for title in S2_TOPICS:
            if title not in works:
                works.append(title)
                ws.append("s2")
        db["work_subjects"] = ws
        db["s2_topics_added"] = True
        changed = True
    if not db.get("s2_old_topics_added"):
        ws = work_subjects(db)
        wg = work_groups(db)
        for i, sid in enumerate(ws):
            if sid == "s2" and not wg[i]:
                wg[i] = "new"
        for title in S2_OLD_TOPICS:
            if title not in works:
                works.append(title)
                ws.append("s2")
                wg.append("old")
        db["work_subjects"] = ws
        db["work_groups"] = wg
        db["s2_old_topics_added"] = True
        changed = True
    return changed
