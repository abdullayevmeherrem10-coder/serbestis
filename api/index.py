# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
import json, os, re, sys, string, random, hashlib, hmac, base64, time
import urllib.request as urlreq

# Vercel-də funksiya qovluğu sys.path-da olmur — qonşu modulların importu üçün əlavə edilir
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from _credentials import CREDENTIALS
from _results import RESULTS
from _roster import roster_action

app = Flask(__name__)

UPSTASH_URL = os.environ.get('UPSTASH_REDIS_REST_URL', '')
UPSTASH_TOKEN = os.environ.get('UPSTASH_REDIS_REST_TOKEN', '')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')
DB_KEY = 'serbestis_db'
RATE_KEY = 'serbestis_rate'
MAX_ATTEMPTS = 7
BLOCK_MINUTES = 15

DEFAULT_DB = {
    "teams": {
        "YTF24A1": [
            "Abbasov Ramal Ramil oğlu", "Ağabalayev Oktay Mahmud oğlu",
            "Axundzadə Onur Zəki oğlu", "Allahverdiyev Ümid Elmir oğlu",
            "Eldarlı Hüseyn Baba oğlu", "Ələkbərli Məhəmməd Elmar oğlu",
            "Əliyev Anar Alim oğlu", "Əliyev Vahid Surxay oğlu",
            "İsmayılov Nihad Habil oğlu", "Kərimli Eşqin Niyaməddin oğlu",
            "Qardiyev Nicat Elməddin oğlu", "Qasımov Fateh Taleh oğlu",
            "Quliyev Rəvan Soltan oğlu", "Qurbanov Nicat Amil oğlu",
            "Məmmədli Polad Faiq oğlu", "Məmmədov Bəhman Mehman oğlu",
            "Məmmədov Rəşid Rəşad oğlu", "Rəhimzadə Ramin Səbuhi oğlu",
            "Sadıqov Kəmaləddin Seyfəddin oğlu", "Tağıyev Ziya Zaur oğlu",
            "Vəliyev Qalib Cəlil oğlu", "Yaqubzadə Yaqub Səbuhi oğlu",
            "Yusifzadə Mahmud Natiq oğlu", "Zəkiyev Sadıq Mehman oğlu"
        ],
        "YTF24A2": [
            "Abdurahmanov Ziya Valeh oğlu", "Ağazadə Abdullah İntizam oğlu",
            "Alıyev Azin Yolçu oğlu", "Baxşıyev Raul Şamo oğlu",
            "Bəyişov Arif Neymət oğlu", "Çingizli İlçin İlham oğlu",
            "Davudov Qail Qabil oğlu", "Əyyubov Fərhad İlqar oğlu",
            "Həmidov İsmail Ramiz oğlu", "Hüseynli Fərid Şaiq oğlu",
            "Hüseynov Əbutalib Bəhram oğlu", "Hüseynov Əli Çingiz oğlu",
            "Hüseynov Zaur Bəhruz oğlu", "Qasımov Əli Taleh oğlu",
            "Qənbərov Hüseyn İsaq oğlu", "Qurbanov Tuncay Turan oğlu",
            "Qurbanov Vasif Xeyrəddin oğlu", "Məmmədli Ənnağı Qalib oğlu",
            "Məmmədov Bəyiş Ülkər oğlu", "Mustafayev Adəm Səyyad oğlu",
            "Novruzov Nihat Eyvaz oğlu", "Səfxanlı İslam Elşən oğlu",
            "Şıxıyev Farid Ravid oğlu", "Vəliyev Cəlal Arzu oğlu",
            "Vəliyev Elsevər Eldəniz oğlu"
        ],
        "HFT24A1": [
            "Abdullayev Naim Elçin oğlu", "Ağayev Cahid Qoşqar oğlu",
            "Alıyev Rəvan İlqar oğlu", "Allahyarov Sübhan Ələkbər oğlu",
            "Babayev Kənan Şərif oğlu", "Cəbizadə Fikrət Qafkaz oğlu",
            "Cəfərli Məhəmməd Tofiq oğlu", "Daşdıyev Sənan Şahin oğlu",
            "Əliyev Orxan Adil oğlu", "Əzimov Aqşin Telman oğlu",
            "Fərmanov Fərman Mayis oğlu", "Həbibzadə Nəriman Təyyar oğlu",
            "Xeyirbəyov Ramil Ramiz oğlu", "İbrahimov Elgün Allahverdi oğlu",
            "İsmayılov Ayxan İsmayıl oğlu", "Qəhrəmanov Viləddin Ramin oğlu",
            "Məmmədov Uğur Aslan oğlu", "Misirov Murad Yaşar oğlu",
            "Muxtarov Vüsal Sabir oğlu", "Nəsirov Cavidan Nəsib oğlu",
            "Salmanov Seymur Müşviq oğlu", "Səmədzadə Əmənulla Mahir oğlu",
            "Tağıyev Bəhram Sənan oğlu"
        ],
        "HFT24A2": [
            "Abdulov Turan İlqar oğlu", "Alıyev Elgün Amin oğlu",
            "Allahverdiyev Allahverdi Müşviq oğlu", "Allahverdiyev Səid Həmid oğlu",
            "Bağırov Seyidəli Səməd oğlu", "Bayramov Nihad Ariz oğlu",
            "Eynalov Elmir Oktay oğlu", "Hüseynov Ayxan Seymur oğlu",
            "Hüseynov Murad Vəli oğlu", "İbrahimov Nihad Rafiq oğlu",
            "İsrafilov Murad Asəf oğlu", "Mamedov Afər Elşən oğlu",
            "Mərufov Emil Sərdar oğlu", "Məsimov Nahid Vahid oğlu",
            "Mirhüseynov Mirhüseyn Sənan oğlu", "Mirizadə Səid Pənah oğlu",
            "Ramazanov Fərid İsmayıl oğlu", "Rəhimov Firdovsi Elgiz oğlu",
            "Şirinov Ağaxan Şahin oğlu", "Talıbov Murad Qafur oğlu",
            "Umudalıyev Nail Atakişi oğlu", "Vəliyev Ramazan Qəhrəman oğlu"
        ]
    },
    "works": [
        "Mühəndis texnikalarının istismar xüsusiyyətləri",
        "Hərbi mühəndis maşınlarının istismarı üzrə ümumi müddəalar. Planlı-xəbərdarlıq sistemi",
        "Maşınların əsas nasazlıqları və texniki xidmətinə ümumi tələblər",
        "Mühəndis texnikalarına göstərilən texniki xidmətlərin növləri və işlərin məzmunu",
        "Texniki xidmətin təşkilində ümumi müddəalar və metodları",
        "Maşın parkdan çıxmazdan əvvəl və parka qayıtdıqdan sonra texniki xidmət. Texnikaya baxış",
        "Daimi parkın ümumi quruluşu. Daimi parkda texniki xidmətin texnoloji prosesi",
        "Çöl parklarının qurulması və təchizatının xüsusiyyətləri. Daxili xidmətin təşkili",
        "Yay istismar dövründə iş şəraiti və texnikanın hazırlanması xüsusiyyətləri",
        "Qış istismar dövründə iş şəraiti və texnikanın hazırlanmasının xüsusiyyətləri",
        "Texnikanın mövsümi istismara hazırlanmasının təşkili. Dağlıq ərazidə istismar",
        "SHT istismarının və təmirinin planlaşdırılması və uçotu",
        "Texniki diaqnostikanın mahiyyəti, əsas anlayışları, əlamətləri və metodları",
        "Mühərrikin, transmissiyanın, hərəkət hissəsinin, işçi və xüsusi avadanlığın diaqnostikası",
        "Saxlanma nəzəriyyəsinin əsasları, növləri və metodları",
        "Maşının tərkib hissələrinin konservasiya edilməsi. Saxlanmaya qoyarkən işlərin təşkili",
        "Mühəndis texnikasının döyüş tətbiqinə hazırlanması",
        "Maşının fərdi ehtiyat hissələr, alət və ləvazimatlar dəsti. Daimi parklarda xidmət vasitələri",
        "Çöl şəraitində maşınlara texniki xidmət vasitələri",
        "Hərbi mühəndis maşınları üçün yanacaqlar. Xüsusi mayelər",
        "Mühəndis texnikaları üçün sürtkü materialları",
        "Təmirin növləri, detalların çilingər mexaniki üsulla, təzyiqlə bərpası",
        "Təmirin növləri, detalların qaynaq və əridib tökmə üsulu ilə bərpası",
        "Təmirin növləri, detalların qaz-termik tozlama, lehimləmə, elektrolitik artırma və polimer materiallarla bərpası",
        "Maşının tərkib hissələrinin əsas nasazlıqları və cari təmiri",
        "Təmirin növləri. Cari təmir üçün avadanlıq",
        "Səyyar maşın təmiri vasitələri və onların tətbiqi",
        "Mühəndis qoşunlarında texnikanın təmir sistemi. Cari və orta təmirin təşkili",
        "Mühəndis qoşunlarında texnikanın təmir sistemi. Təmirə təhvil və təmirdən qəbul",
        "Texniki təminat üzrə əsas müddəalar. Döyüş şəraitində texniki xidmətin təşkili",
        "Maşınların təxliyyəsi və daşınmasının təşkili. Döyüş şəraitində təmirin təşkili",
        "Döyüş şəraitində material vasitələrlə təmin edilməsi. Vəzifəli şəxslərin işi",
        "Park-təsərrüfat gününün təşkili və keçirilməsi",
        "Hərbi-mühəndis texniki təminatın ümumi müddəaları",
        "Hərbi mühəndis maşınlarının idarəsi üzrə tədris. Sürücülük hazırlığı və qiymətləndirilməsi",
        "Maşinodrom (hidrodrom) və ondan istifadə qaydaları",
        "Tırtıllı bazada mühəndis maşınlarının sürülməsi. Əngəllərin və su maneələrinin dəf edilməsi",
        "Çətin şəraitlərdə maşınların sürülməsi. Platformaya, treylerə, bərəyə yüklənməsi",
        "МТУ-20, МТ-55, МТУ-72 mexanikləşdirilmiş körpülərin sürücü-mexaniklərinin hazırlanması",
        "Yolçəkən maşınların sürücü-mexanikləri üçün xüsusi çalışmalar",
        "БТМ-3 səngər qazan maşının sürücü-mexanikləri üçün xüsusi çalışmalar",
        "МДК-3 çalaqazan maşının sürücü-mexaniki üçün xüsusi çalışmalar",
        "ГМЗ-3, УР-67, УР-77 sürücü-mexanikləri və operatorlarının hazırlanması",
        "ИМР-3 mühəndis maneətəmizləyən maşının sürücü-mexanikinin hazırlanması",
        "Üzən tırtıllı mühəndis maşınlarının sürücü-mexaniklərinin hazırlanması",
        "Mühəndis maşınlarının sürülməsi üzrə təhlükəsizlik tədbirləri",
        "Döyüş əməliyyatlarında mühəndis təminatının məqsəd və vəzifələri",
        "Hərbi mühəndis təminatının tarixi və inkişaf mərhələləri",
        "Yükqaldırma vasitələri, Minalı partlayan maneələrdən keçid açan vasitələr",
        "Səyyar elektrostansiyaların əsas taktiki-texniki xüsusiyyətləri"
    ],
    "keys": {},
    "selections": {},
    "work_taken_by": {
        "YTF24A1": {},
        "YTF24A2": {},
        "HFT24A1": {},
        "HFT24A2": {}
    }
}


def redis_execute(cmd_list):
    data = json.dumps(cmd_list).encode('utf-8')
    req = urlreq.Request(
        UPSTASH_URL,
        data=data,
        headers={
            'Authorization': f'Bearer {UPSTASH_TOKEN}',
            'Content-Type': 'application/json'
        },
        method='POST'
    )
    with urlreq.urlopen(req) as resp:
        result = json.loads(resp.read().decode('utf-8'))
        return result.get('result')


def find_team(db, student_name):
    for team, members in db["teams"].items():
        if student_name in members:
            return team
    return None


def load_db():
    raw = redis_execute(['GET', DB_KEY])
    if raw:
        db = json.loads(raw)
        # Migrate old flat work_taken_by to per-team structure
        if db.get("work_taken_by") and not any(isinstance(v, dict) for v in db["work_taken_by"].values()):
            old = db["work_taken_by"]
            db["work_taken_by"] = {t: {} for t in db["teams"]}
            for wid, name in old.items():
                team = find_team(db, name)
                if team:
                    db["work_taken_by"][team][wid] = name
            save_db(db)
        # Ensure all teams have entries
        for t in db["teams"]:
            if t not in db.get("work_taken_by", {}):
                db.setdefault("work_taken_by", {})[t] = {}
        return db
    db = json.loads(json.dumps(DEFAULT_DB))
    save_db(db)
    return db


def save_db(db):
    redis_execute(['SET', DB_KEY, json.dumps(db, ensure_ascii=False)])


def get_client_ip():
    return request.headers.get('X-Forwarded-For', request.remote_addr or '').split(',')[0].strip()


def check_rate_limit(ip):
    """Returns (blocked, attempts). If blocked=True, IP is rate limited."""
    try:
        raw = redis_execute(['GET', f'{RATE_KEY}:{ip}'])
        if raw:
            data = json.loads(raw)
            if data.get('blocked') and data.get('attempts', 0) >= MAX_ATTEMPTS:
                return True, data['attempts']
            return False, data.get('attempts', 0)
    except:
        pass
    return False, 0


def record_failed_attempt(ip):
    try:
        raw = redis_execute(['GET', f'{RATE_KEY}:{ip}'])
        attempts = 1
        if raw:
            data = json.loads(raw)
            attempts = data.get('attempts', 0) + 1
        blocked = attempts >= MAX_ATTEMPTS
        redis_execute(['SET', f'{RATE_KEY}:{ip}', json.dumps({'attempts': attempts, 'blocked': blocked})])
        redis_execute(['EXPIRE', f'{RATE_KEY}:{ip}', str(BLOCK_MINUTES * 60)])
    except:
        pass


def clear_rate_limit(ip):
    try:
        redis_execute(['DEL', f'{RATE_KEY}:{ip}'])
    except:
        pass


def generate_key(length=6):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def cred_hash(cid, password):
    return hashlib.sha256(f"{cid.upper()}:{password}".encode("utf-8")).hexdigest()


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
    """Etibarlıdırsa credential id-ni, əks halda None qaytarır."""
    try:
        b, sig = token.split(".")
        good = hmac.new(CABINET_SECRET.encode("utf-8"), b.encode("ascii"), hashlib.sha256).hexdigest()[:32]
        if not hmac.compare_digest(sig, good):
            return None
        payload = json.loads(base64.urlsafe_b64decode(b + "=" * (-len(b) % 4)))
        if payload.get("exp", 0) < time.time():
            return None
        cid = payload.get("id", "")
        return cid if cid else None
    except Exception:
        return None


def token_from_request():
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return verify_token(auth[7:].strip())
    return None


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
    """Kursantın öz nəticələri (yoxdursa None sahələr). Müəllimin manual imtahan balı üstündür."""
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
    """Statik və ya dinamik (müəllimin əlavə etdiyi) hesab."""
    return CREDENTIALS.get(cid) or db.get("credentials_dyn", {}).get(cid)


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


def admin_guard():
    """Rate-limit + admin şifrə yoxlaması. Uğursuzsa (response, status), uğurlu olsa None qaytarır."""
    if not ADMIN_PASSWORD:
        return jsonify({"error": "Admin paneli konfiqurasiya olunmayıb (ADMIN_PASSWORD təyin edilməyib)."}), 503
    ip = get_client_ip()
    blocked, attempts = check_rate_limit(ip)
    if blocked:
        return jsonify({"error": f"Çox sayda yanlış cəhd! {BLOCK_MINUTES} dəqiqə gözləyin."}), 429
    body = request.get_json(silent=True) or {}
    if body.get('password') != ADMIN_PASSWORD:
        record_failed_attempt(ip)
        remaining = max(0, MAX_ATTEMPTS - attempts - 1)
        return jsonify({"error": f"Admin şifrəsi yanlışdır! {remaining} cəhd qalıb."}), 403
    clear_rate_limit(ip)
    return None


# ─── Routes ───────────────────────────────────────────────

@app.route('/api/teams')
def get_teams():
    # Kursant adları yalnız daxil olmuş istifadəçilərə görünür
    db = load_db()
    cid = token_from_request()
    if not cid or not resolve_cred(cid, db):
        return jsonify({"error": "Giriş tələb olunur."}), 401
    return jsonify({"teams": db["teams"]})


@app.route('/api/cabinet-login', methods=['POST'])
def cabinet_login():
    ip = get_client_ip()
    blocked, attempts = check_rate_limit(ip)
    if blocked:
        return jsonify({"error": f"Çox sayda yanlış cəhd! {BLOCK_MINUTES} dəqiqə gözləyin."}), 429
    body = request.get_json(silent=True) or {}
    cid = (body.get('id') or '').strip().upper()
    password = body.get('password') or ''
    db = load_db()
    raw = raw_cred(cid, db)
    if not raw or cred_hash(cid, password) != raw.get('hash'):
        record_failed_attempt(ip)
        remaining = max(0, MAX_ATTEMPTS - attempts - 1)
        return jsonify({"error": f"ID və ya şifrə yanlışdır! {remaining} cəhd qalıb."}), 403
    clear_rate_limit(ip)
    cred = resolve_cred(cid, db)
    if not cred:
        return jsonify({"error": "Bu hesab deaktiv edilib."}), 403
    resp = {"token": make_token(cid), "id": cid, "name": cred["name"], "role": cred["role"]}
    if cred["role"] == "student":
        resp["team"] = cred["team"]
    return jsonify(resp)


@app.route('/api/cabinet-data')
def cabinet_data():
    cid = token_from_request()
    if not cid:
        return jsonify({"error": "Sessiya bitib. Yenidən daxil olun."}), 401
    db = load_db()
    cred = resolve_cred(cid, db)
    if not cred:
        return jsonify({"error": "Sessiya bitib. Yenidən daxil olun."}), 401
    if cred.get('role') == 'teacher':
        return jsonify({
            "role": "teacher",
            "name": cred.get('name', 'Müəllim'),
            "results": effective_results(db),
            "selections": db.get('selections', {}),
            "scores": db.get('scores', {}),
            "deadlines": db.get('deadlines', {}),
            "teams": db.get('teams', {}),
            "works": db.get('works', []),
            "work_taken_by": db.get('work_taken_by', {}),
            "semester": db.get('semester', '2025/2026 yaz semestri'),
            "subject": db.get('subject', 'Hərbi Mühəndis Texnikası'),
            "exam_scores": db.get('exam_scores', {}),
        })
    name = cred['name']
    return jsonify({
        "role": "student",
        "id": cid,
        "name": name,
        "team": cred['team'],
        "key": db.get('keys', {}).get(name, ''),
        "selections": db.get('selections', {}).get(name, []),
        "results": student_results(name, cred['team'], db),
        "scores": db.get('scores', {}).get(name),
        "deadline": db.get('deadlines', {}).get(name),
        "semester": db.get('semester', '2025/2026 yaz semestri'),
        "subject": db.get('subject', 'Hərbi Mühəndis Texnikası'),
    })


@app.route('/api/semester-info')
def semester_info():
    """Giriş səhifəsi üçün açıq məlumat: semestr və fənn adı."""
    db = load_db()
    return jsonify({
        "semester": db.get('semester', '2025/2026 yaz semestri'),
        "subject": db.get('subject', 'Hərbi Mühəndis Texnikası'),
    })


@app.route('/api/cabinet-semester', methods=['POST'])
def cabinet_semester():
    """Müəllim semestr və fənn adını dəyişir."""
    cid = token_from_request()
    if not cid or CREDENTIALS.get(cid, {}).get('role') != 'teacher':
        return jsonify({"error": "İcazə yoxdur."}), 401
    body = request.get_json(silent=True) or {}
    semester = (body.get('semester') or '').strip()[:60]
    subject = (body.get('subject') or '').strip()[:60]
    if not semester or not subject:
        return jsonify({"error": "Semestr və fənn boş ola bilməz."}), 400
    db = load_db()
    db['semester'] = semester
    db['subject'] = subject
    save_db(db)
    return jsonify({"success": True, "semester": semester, "subject": subject})


@app.route('/api/cabinet-reset', methods=['POST'])
def cabinet_reset():
    """Müəllim bir kursantın sərbəst iş seçimini sıfırlayır."""
    cid = token_from_request()
    if not cid or CREDENTIALS.get(cid, {}).get('role') != 'teacher':
        return jsonify({"error": "İcazə yoxdur."}), 401
    body = request.get_json(silent=True) or {}
    name = (body.get('name') or '').strip()
    if not name:
        return jsonify({"error": "Kursant adı göstərilməyib."}), 400
    db = load_db()
    db.get('selections', {}).pop(name, None)
    for team, taken in db.get('work_taken_by', {}).items():
        db['work_taken_by'][team] = {wid: n for wid, n in taken.items() if n != name}
    save_db(db)
    return jsonify({"success": True, "selections": db.get('selections', {}), "work_taken_by": db.get('work_taken_by', {})})


@app.route('/api/cabinet-reset-all', methods=['POST'])
def cabinet_reset_all():
    """Müəllim bütün sərbəst iş seçimlərini sıfırlayır (ballara toxunmur)."""
    cid = token_from_request()
    if not cid or CREDENTIALS.get(cid, {}).get('role') != 'teacher':
        return jsonify({"error": "İcazə yoxdur."}), 401
    db = load_db()
    db['selections'] = {}
    db['work_taken_by'] = {t: {} for t in db.get('teams', {})}
    save_db(db)
    return jsonify({"success": True, "selections": {}, "work_taken_by": db['work_taken_by']})


# ─── E-Kollokvium Firebase yazma proxy-si ─────────────────
# Firebase qaydaları yazmanı bağlayır; yazma yalnız buradan, müəllim girişi ilə,
# gizli açarla (FIREBASE_SECRET env) gedir. Beləcə balları heç kim saxtalaşdıra bilməz.
FIREBASE_DB_URL = 'https://kollokvium1-default-rtdb.firebaseio.com'
FIREBASE_SECRET = os.environ.get('FIREBASE_SECRET', '')

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


def teacher_from_request():
    """Bearer token və ya kabinet cookie-sindən müəllim yoxlanışı."""
    cid = token_from_request()
    if not cid:
        tok = request.cookies.get('kabinet', '')
        cid = verify_token(tok) if tok else None
    if cid and CREDENTIALS.get(cid, {}).get('role') == 'teacher':
        return cid
    return None


@app.route('/api/kollok-diag')
def kollok_diag():
    if not teacher_from_request():
        return jsonify({"error": "Yalnız müəllim."}), 401
    info = {"has_env": bool(os.environ.get('FIREBASE_SERVICE_ACCOUNT', '').strip())}
    try:
        import google.auth
        info["google_auth"] = getattr(google.auth, '__version__', 'var')
    except Exception as e:
        info["google_auth"] = f"YOX: {e.__class__.__name__}: {e}"
    try:
        import _fbauth
        creds = _fbauth._load_creds()
        info["creds_loaded"] = creds is not None
        try:
            tok = _fbauth.get_access_token()
            info["token"] = "var" if tok else "yox"
        except Exception as e:
            info["token"] = f"XƏTA: {e.__class__.__name__}: {e}"
    except Exception as e:
        info["fbauth"] = f"XƏTA: {e.__class__.__name__}: {e}"
    # birbaşa yazma sınağı — real xətanı göstər
    try:
        url = _fb_url("sessions/DIAG_TEST")
        req = urlreq.Request(url, data=b'{"t":1}', method='PUT', headers={'Content-Type': 'application/json'})
        with urlreq.urlopen(req, timeout=10) as resp:
            info["write"] = resp.status
    except Exception as e:
        info["write"] = f"{e.__class__.__name__}: {e}"
    return jsonify(info)


@app.route('/api/kollok-write', methods=['POST'])
def kollok_write():
    if not teacher_from_request():
        return jsonify({"error": "Yazmaq üçün əsas saytda müəllim kimi daxil olmalısınız."}), 401
    body = request.get_json(silent=True) or {}
    path = (body.get('path') or '').strip()
    if not re.fullmatch(r'sessions/[A-Za-z0-9_\-/]+', path):
        return jsonify({"error": "Yol etibarsızdır."}), 400
    url = _fb_url(path)
    data = body.get('data', None)
    try:
        if data is None:
            req = urlreq.Request(url, method='DELETE')
        else:
            req = urlreq.Request(url, data=json.dumps(data, ensure_ascii=False).encode('utf-8'),
                                 method='PUT', headers={'Content-Type': 'application/json'})
        with urlreq.urlopen(req, timeout=10) as resp:
            resp.read()
        return jsonify({"success": True})
    except Exception:
        return jsonify({"error": "Firebase yazma alınmadı."}), 502


@app.route('/api/cabinet-roster', methods=['POST'])
def cabinet_roster():
    """Müəllim taqım/kursant idarəetməsi: əlavə, ad dəyişmə, silmə."""
    cid = token_from_request()
    if not cid or CREDENTIALS.get(cid, {}).get('role') != 'teacher':
        return jsonify({"error": "İcazə yoxdur."}), 401
    body = request.get_json(silent=True) or {}
    db = load_db()
    changed, resp, code = roster_action(db, body, CREDENTIALS)
    if changed:
        save_db(db)
    return jsonify(resp), code


@app.route('/api/cabinet-exam', methods=['POST'])
def cabinet_exam():
    """Müəllim kursantın imtahan balını (0-100) manual yazır; boş → statik nəticəyə qayıdır."""
    cid = token_from_request()
    if not cid or CREDENTIALS.get(cid, {}).get('role') != 'teacher':
        return jsonify({"error": "İcazə yoxdur."}), 401
    body = request.get_json(silent=True) or {}
    name = (body.get('name') or '').strip()
    if not name:
        return jsonify({"error": "Kursant adı göstərilməyib."}), 400
    db = load_db()
    if not any(name in members for members in db.get('teams', {}).values()):
        return jsonify({"error": "Kursant tapılmadı."}), 404
    bal = body.get('bal')
    ex = db.setdefault('exam_scores', {})
    if bal is None or bal == '':
        ex.pop(name, None)
        save_db(db)
        return jsonify({"success": True, "name": name, "bal": None})
    try:
        bal = max(0, min(100, int(bal)))
    except (TypeError, ValueError):
        return jsonify({"error": "Bal 0-100 arası rəqəm olmalıdır."}), 400
    ex[name] = bal
    save_db(db)
    return jsonify({"success": True, "name": name, "bal": bal, "grade": exam_grade(bal)})


@app.route('/api/cabinet-deadline', methods=['POST'])
def cabinet_deadline():
    """Müəllim sərbəst işlərin son təhvil tarixini dəyişir."""
    cid = token_from_request()
    if not cid or CREDENTIALS.get(cid, {}).get('role') != 'teacher':
        return jsonify({"error": "İcazə yoxdur."}), 401
    body = request.get_json(silent=True) or {}
    deadline = (body.get('deadline') or '').strip()[:60]
    name = (body.get('name') or '').strip()
    if not name:
        return jsonify({"error": "Kursant adı göstərilməyib."}), 400
    db = load_db()
    if not any(name in members for members in db.get('teams', {}).values()):
        return jsonify({"error": "Kursant tapılmadı."}), 404
    dls = db.setdefault('deadlines', {})
    if deadline:
        dls[name] = deadline
    else:
        dls.pop(name, None)
    save_db(db)
    return jsonify({"success": True, "name": name, "deadline": deadline or None})


@app.route('/api/cabinet-scores', methods=['POST'])
def cabinet_scores():
    """Müəllim kursant üçün Sərbəst iş (0-10) və Dəftər/İntizam (0-10) balı yazır."""
    cid = token_from_request()
    if not cid or CREDENTIALS.get(cid, {}).get('role') != 'teacher':
        return jsonify({"error": "İcazə yoxdur."}), 401
    body = request.get_json(silent=True) or {}
    name = (body.get('name') or '').strip()
    if not name:
        return jsonify({"error": "Kursant adı göstərilməyib."}), 400

    def norm(v):
        if v is None or v == '':
            return None
        try:
            n = int(v)
        except (TypeError, ValueError):
            return None
        return max(0, min(10, n))

    db = load_db()
    if not any(name in members for members in db.get('teams', {}).values()):
        return jsonify({"error": "Kursant tapılmadı."}), 404
    db.setdefault('scores', {})[name] = {
        "serbest": norm(body.get('serbest')),
        "defter": norm(body.get('defter')),
    }
    save_db(db)
    return jsonify({"success": True, "name": name, "scores": db['scores'][name]})


@app.route('/api/works')
def get_works():
    # İşi götürən kursantların adları yalnız daxil olmuş istifadəçilərə görünür
    db = load_db()
    cid = token_from_request()
    if not cid or not resolve_cred(cid, db):
        return jsonify({"error": "Giriş tələb olunur."}), 401
    team = request.args.get('team', '')
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
    return jsonify({"works": works})


@app.route('/api/status', methods=['POST'])
def get_status():
    guard = admin_guard()
    if guard:
        return guard
    db = load_db()
    return jsonify({
        "selections": db["selections"],
        "work_taken_by": db["work_taken_by"],
        "keys": db["keys"]
    })


@app.route('/api/student-status')
def student_status():
    ip = get_client_ip()
    blocked, attempts = check_rate_limit(ip)
    if blocked:
        return jsonify({"error": f"Çox sayda yanlış cəhd! {BLOCK_MINUTES} dəqiqə gözləyin."}), 429

    name = request.args.get('name', '')
    key = request.args.get('key', '')
    db = load_db()
    if name not in db["keys"]:
        record_failed_attempt(ip)
        return jsonify({"error": "Bu kursant üçün açar təyin edilməyib"}), 403
    if db["keys"][name] != key:
        record_failed_attempt(ip)
        remaining = MAX_ATTEMPTS - attempts - 1
        return jsonify({"error": f"Açar yanlışdır! {remaining} cəhd qalıb."}), 403
    clear_rate_limit(ip)
    selected = db["selections"].get(name, [])
    return jsonify({"name": name, "selections": selected})


@app.route('/api/select', methods=['POST'])
def select_works():
    ip = get_client_ip()
    blocked, attempts = check_rate_limit(ip)
    if blocked:
        return jsonify({"error": f"Çox sayda yanlış cəhd! {BLOCK_MINUTES} dəqiqə gözləyin."}), 429

    body = request.get_json()
    name = body.get('name', '')
    key = body.get('key', '')
    team = body.get('team', '')
    work_ids = body.get('work_ids', [])

    db = load_db()

    if name not in db["keys"]:
        record_failed_attempt(ip)
        return jsonify({"error": "Bu kursant üçün açar təyin edilməyib. Müəllimlə əlaqə saxlayın."}), 403
    if db["keys"][name] != key:
        record_failed_attempt(ip)
        return jsonify({"error": "Açar yanlışdır!"}), 403
    clear_rate_limit(ip)
    if name in db["selections"] and len(db["selections"][name]) >= 2:
        return jsonify({"error": "Siz artıq 2 sərbəst iş seçmisiniz!"}), 400
    if len(work_ids) != 2:
        return jsonify({"error": "Tam olaraq 2 sərbəst iş seçməlisiniz!"}), 400

    team_taken = db["work_taken_by"].get(team, {})
    for wid in work_ids:
        taken = team_taken.get(str(wid))
        if taken and taken != name:
            title = db["works"][wid] if wid < len(db["works"]) else "?"
            return jsonify({"error": f"'{title}' artıq başqası tərəfindən seçilib!"}), 409

    db["selections"][name] = work_ids
    for wid in work_ids:
        db["work_taken_by"].setdefault(team, {})[str(wid)] = name
    save_db(db)

    selected_titles = [db["works"][wid] for wid in work_ids]
    return jsonify({"success": True, "message": "Seçimləriniz uğurla qeydə alındı!", "selected": selected_titles})


@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    guard = admin_guard()
    if guard:
        return guard
    return jsonify({"success": True})


@app.route('/api/admin/generate-keys', methods=['POST'])
def admin_generate_keys():
    guard = admin_guard()
    if guard:
        return guard

    body = request.get_json()
    db = load_db()
    team = body.get('team', '')
    if team and team in db["teams"]:
        for student in db["teams"][team]:
            if student not in db["keys"]:
                db["keys"][student] = generate_key()
    else:
        for members in db["teams"].values():
            for student in members:
                if student not in db["keys"]:
                    db["keys"][student] = generate_key()
    save_db(db)
    return jsonify({"success": True, "keys": db["keys"]})


@app.route('/api/admin/set-key', methods=['POST'])
def admin_set_key():
    guard = admin_guard()
    if guard:
        return guard

    body = request.get_json()
    db = load_db()
    db["keys"][body.get('name', '')] = body.get('key', '')
    save_db(db)
    return jsonify({"success": True})


@app.route('/api/admin/reset-selection', methods=['POST'])
def admin_reset_selection():
    guard = admin_guard()
    if guard:
        return guard

    body = request.get_json()
    name = body.get('name', '')
    db = load_db()
    if name in db["selections"]:
        team = find_team(db, name)
        if team and team in db["work_taken_by"]:
            for wid in db["selections"][name]:
                if str(wid) in db["work_taken_by"][team] and db["work_taken_by"][team][str(wid)] == name:
                    del db["work_taken_by"][team][str(wid)]
        del db["selections"][name]
        save_db(db)
    return jsonify({"success": True})


@app.route('/api/admin/reset-all', methods=['POST'])
def admin_reset_all():
    guard = admin_guard()
    if guard:
        return guard

    # Delete Redis key completely and reinitialize
    redis_execute(['DEL', DB_KEY])
    db = json.loads(json.dumps(DEFAULT_DB))
    save_db(db)
    return jsonify({"success": True})
