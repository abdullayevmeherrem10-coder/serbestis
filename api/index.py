# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
import json, os, string, random
import urllib.request as urlreq

app = Flask(__name__)

UPSTASH_URL = os.environ.get('UPSTASH_REDIS_REST_URL', '')
UPSTASH_TOKEN = os.environ.get('UPSTASH_REDIS_REST_TOKEN', '')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Qmz4!')
DB_KEY = 'serbestis_db'

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


def generate_key(length=6):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


# ─── Routes ───────────────────────────────────────────────

@app.route('/api/teams')
def get_teams():
    db = load_db()
    return jsonify({"teams": db["teams"]})


@app.route('/api/works')
def get_works():
    team = request.args.get('team', '')
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
    return jsonify({"works": works})


@app.route('/api/status', methods=['POST'])
def get_status():
    body = request.get_json()
    if body.get('password') != ADMIN_PASSWORD:
        return jsonify({"error": "Admin şifrəsi yanlışdır!"}), 403
    db = load_db()
    return jsonify({
        "selections": db["selections"],
        "work_taken_by": db["work_taken_by"],
        "keys": db["keys"]
    })


@app.route('/api/student-status')
def student_status():
    name = request.args.get('name', '')
    key = request.args.get('key', '')
    db = load_db()
    if name not in db["keys"]:
        return jsonify({"error": "Bu kursant üçün açar təyin edilməyib"}), 403
    if db["keys"][name] != key:
        return jsonify({"error": "Açar yanlışdır"}), 403
    selected = db["selections"].get(name, [])
    return jsonify({"name": name, "selections": selected})


@app.route('/api/select', methods=['POST'])
def select_works():
    body = request.get_json()
    name = body.get('name', '')
    key = body.get('key', '')
    team = body.get('team', '')
    work_ids = body.get('work_ids', [])

    db = load_db()

    if name not in db["keys"]:
        return jsonify({"error": "Bu kursant üçün açar təyin edilməyib. Müəllimlə əlaqə saxlayın."}), 403
    if db["keys"][name] != key:
        return jsonify({"error": "Açar yanlışdır!"}), 403
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
    body = request.get_json()
    if body.get('password') != ADMIN_PASSWORD:
        return jsonify({"error": "Admin şifrəsi yanlışdır!"}), 403
    return jsonify({"success": True})


@app.route('/api/admin/generate-keys', methods=['POST'])
def admin_generate_keys():
    body = request.get_json()
    if body.get('password') != ADMIN_PASSWORD:
        return jsonify({"error": "Admin şifrəsi yanlışdır!"}), 403

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
    body = request.get_json()
    if body.get('password') != ADMIN_PASSWORD:
        return jsonify({"error": "Admin şifrəsi yanlışdır!"}), 403

    db = load_db()
    db["keys"][body.get('name', '')] = body.get('key', '')
    save_db(db)
    return jsonify({"success": True})


@app.route('/api/admin/reset-selection', methods=['POST'])
def admin_reset_selection():
    body = request.get_json()
    if body.get('password') != ADMIN_PASSWORD:
        return jsonify({"error": "Admin şifrəsi yanlışdır!"}), 403

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
    body = request.get_json()
    if body.get('password') != ADMIN_PASSWORD:
        return jsonify({"error": "Admin şifrəsi yanlışdır!"}), 403

    # Delete Redis key completely and reinitialize
    redis_execute(['DEL', DB_KEY])
    db = json.loads(json.dumps(DEFAULT_DB))
    save_db(db)
    return jsonify({"success": True})
