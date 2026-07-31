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
from _uploads import (upload_url_action, upload_confirm_action,
                      upload_link_action, upload_delete_action,
                      upload_review_action, vt_check_action, vt_status_action)
from _backup import run_backup, read_backup, save_prerestore

app = Flask(__name__)

UPSTASH_URL = os.environ.get('UPSTASH_REDIS_REST_URL', '')
UPSTASH_TOKEN = os.environ.get('UPSTASH_REDIS_REST_TOKEN', '')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')
DB_KEY = 'serbestis_db'
RATE_KEY = 'serbestis_rate'
MAX_ATTEMPTS = 7
BLOCK_MINUTES = 15

# Roster versiyası: dəyişəndə canlı bazadakı köhnə qəbul silinib təzə baza yaradılır
# (2024 imtahan nəticələri repo-da arxiv/imtahan_2024.json-dadır — başqa heç nə saxlanmır)
ROSTER_VERSION = "2023-qebul"
ARCHIVE_KEY = 'serbestis_db_arxiv_2024'

DEFAULT_DB = {
    "roster_version": ROSTER_VERSION,
    "teams": {
        "YT23A1": [
            "Abdullazadə Mehman Vəli oğlu", "Ağayev İzzət Süleyman oğlu",
            "Ağayev Məzahir Qəşəm oğlu", "Bayramov Kənan Elman oğlu",
            "Cahangirov Hümbət Mübariz oğlu", "Əliyev Tural Azər oğlu",
            "Hacılı Nihat Anar oğlu", "Həsənzadə Oktay Elnur oğlu",
            "Xəlilov Məhəmməd Ceyhun oğlu", "İsgəndərov Elnar Zaur oğlu",
            "İsmaylov Elnur Rövşən oğlu", "Kərimov Pərvaz Sərvər oğlu",
            "Qumaşov Cavid Vahid oğlu", "Qurbanov Tuqay Mübariz oğlu",
            "Məmmədli Sezər Anar oğlu", "Məmmədov Azay Seymur oğlu",
            "Məmmədov Sərxan Zaur oğlu", "Məmmədov Ümidvar Pərviz oğlu",
            "Mirzəyev Xəqani Elmir oğlu", "Nəcəfov Sənan Murad oğlu",
            "Tağıyev Nəsib Eldəniz oğlu", "Tuhumov Həmid Hacı oğlu",
            "Vəliyev Fəqan Elşad oğlu", "Yaqubov Ayxan Şahin oğlu",
            "Zaidov Qurban Eldəniz oğlu"
        ],
        "YT23A2": [
            "Ağakişiyev Samur İlyas oğlu", "Ağayev Elvin Elçin oğlu",
            "Bağırov Kənan Amil oğlu", "Cabbarlı İslam Yaqub oğlu",
            "Cahangirov Firqət Mübariz oğlu", "Cəbrayılov Pərvin Azər oğlu",
            "Cəfərli Emil Qəhrəman oğlu", "Əliyev Fuad Həbib oğlu",
            "Əlizadə Nihad Fuad oğlu", "Əsədullayev Çingiz Gəray oğlu",
            "Hümbətli Şəhriyar Aşur oğlu", "Hüseynov Əhməd Yaqub oğlu",
            "Kərimov Yaşar Tərlan oğlu", "Məmmədov Cavid Vasif oğlu",
            "Musayev Nadir Fəxrəddin oğlu", "Mustafayev Ziyafət Ziya oğlu",
            "Nadirov Nadir Əli oğlu", "Pirimov İbrahim Habil oğlu",
            "Putayev Emin Şəmsəddin oğlu", "Rəcəbov Afər Asif oğlu",
            "Rəsulov Nail Azad oğlu", "Sadıqov Əvəz Zaur oğlu",
            "Səfərli Emil Ceyhun oğlu", "Səfərov Mirseyid Müşfiq oğlu",
            "Vəliyev Valeh Niyaz oğlu"
        ],
        "HFT23A1": [
            "Abdullayev Məhəmməd Eltun oğlu", "Babazadə Koroğlu Tofiq oğlu",
            "Balacayev Murad Vüqar oğlu", "Bayramlı Ülvi Mənsur oğlu",
            "Cəbrayılov Amil Ramil oğlu", "Cəfərov Əkbər Rafiq oğlu",
            "Əliyev Samir Oqtay oğlu", "Əşrəfzadə Yusif Oktay oğlu",
            "Fərəcli Nicat Adəm oğlu", "Hümbətov Cavad Şöhrət oğlu",
            "İbrahimov Murad Kamal oğlu", "İbrahimzadə Tunar Müşviq oğlu",
            "İsayev Fərid Etimad oğlu", "İsmayılov Azər Murad oğlu",
            "Qulusoy Rüzgar Azər oğlu", "Mehdiyev Ülvi Səyyab oğlu",
            "Məmmədli Nihat Elşən oğlu", "Məmmədov Ağahüseyn Birgün oğlu",
            "Mikayılov Rəhman Mayis oğlu", "Mirzəşərifli Məhəmməd Rəsul oğlu",
            "Səmədov Qardaşxan Qədir oğlu", "Sultanov Məhərrəm Ülvi oğlu",
            "Şirinov Səid Natiq oğlu", "Yunusazdə Murad Habil oğlu"
        ],
        "HFT23A2": [
            "Abbasov Sənan Zaur oğlu", "Abdurəfili Kənan Cahan oğlu",
            "Balayev Murad Vüqar oğlu", "Bayramov Rəvan Rövşən oğlu",
            "Bədəlov Fərid Sərdar oğlu", "Cəbiyev Ruslan Rauf oğlu",
            "Əhmədov Nihad Eyvaz oğlu", "Əlifov Nail Natiq oğlu",
            "Əliyev Cənnətalı Vüqar oğlu", "Əliyev Nihad Abdulla oğlu",
            "Əliyev Tural Vahid oğlu", "Əlizadə Abidin Ağahüseyn oğlu",
            "Həsənli Aqil Elnur oğlu", "İbrahimov Əliş Yalçın oğlu",
            "Quliyev Sərxan Səmid oğlu", "Mehrəliyev Teymur Tofiq oğlu",
            "Məmmədov Elmar Natiq oğlu", "Paşayev Emil Azər oğlu",
            "Paşayev Həsən Cavid oğlu", "Rzayev Sənan Vüsal oğlu",
            "Rzazadə Rza İlqar oğlu", "Salmanlı Mənsur Hacıağa oğlu",
            "Süleymanov Sahib Tural oğlu", "Şahkərimov Nicat Elməddin oğlu",
            "Tağıyev Elmir Həsən oğlu"
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
    "keys": {
        "Abdullazadə Mehman Vəli oğlu": "NBMM0Z",
        "Ağayev İzzət Süleyman oğlu": "G76BD9",
        "Ağayev Məzahir Qəşəm oğlu": "YA4XUF",
        "Bayramov Kənan Elman oğlu": "659UQ4",
        "Cahangirov Hümbət Mübariz oğlu": "D7XYKX",
        "Əliyev Tural Azər oğlu": "EDAFTV",
        "Hacılı Nihat Anar oğlu": "FFHFV0",
        "Həsənzadə Oktay Elnur oğlu": "DOGFQX",
        "Xəlilov Məhəmməd Ceyhun oğlu": "IP3I02",
        "İsgəndərov Elnar Zaur oğlu": "RKPIN1",
        "İsmaylov Elnur Rövşən oğlu": "F9OSLQ",
        "Kərimov Pərvaz Sərvər oğlu": "2Y5AR7",
        "Qumaşov Cavid Vahid oğlu": "OD9EZC",
        "Qurbanov Tuqay Mübariz oğlu": "EIDEG5",
        "Məmmədli Sezər Anar oğlu": "J2IJZJ",
        "Məmmədov Azay Seymur oğlu": "B02V51",
        "Məmmədov Sərxan Zaur oğlu": "R1JC1Y",
        "Məmmədov Ümidvar Pərviz oğlu": "M1Q93R",
        "Mirzəyev Xəqani Elmir oğlu": "ZZDOCL",
        "Nəcəfov Sənan Murad oğlu": "8AQZ2I",
        "Tağıyev Nəsib Eldəniz oğlu": "5LIQE9",
        "Tuhumov Həmid Hacı oğlu": "Q422NI",
        "Vəliyev Fəqan Elşad oğlu": "SKKQC6",
        "Yaqubov Ayxan Şahin oğlu": "R011QM",
        "Zaidov Qurban Eldəniz oğlu": "RZTWS9",
        "Ağakişiyev Samur İlyas oğlu": "1NVPK9",
        "Ağayev Elvin Elçin oğlu": "S1GJM0",
        "Bağırov Kənan Amil oğlu": "SCVO8O",
        "Cabbarlı İslam Yaqub oğlu": "9KM9Z6",
        "Cahangirov Firqət Mübariz oğlu": "WAKW05",
        "Cəbrayılov Pərvin Azər oğlu": "27MEAQ",
        "Cəfərli Emil Qəhrəman oğlu": "4RQBUD",
        "Əliyev Fuad Həbib oğlu": "MOFXU8",
        "Əlizadə Nihad Fuad oğlu": "QWAWQS",
        "Əsədullayev Çingiz Gəray oğlu": "MURK3R",
        "Hümbətli Şəhriyar Aşur oğlu": "JZKH1T",
        "Hüseynov Əhməd Yaqub oğlu": "WMWV84",
        "Kərimov Yaşar Tərlan oğlu": "RJT3KO",
        "Məmmədov Cavid Vasif oğlu": "NDWF5X",
        "Musayev Nadir Fəxrəddin oğlu": "Z2QS0A",
        "Mustafayev Ziyafət Ziya oğlu": "R2JP4G",
        "Nadirov Nadir Əli oğlu": "PR6W70",
        "Pirimov İbrahim Habil oğlu": "IKIJDS",
        "Putayev Emin Şəmsəddin oğlu": "OVOHEU",
        "Rəcəbov Afər Asif oğlu": "TUF6FT",
        "Rəsulov Nail Azad oğlu": "8AQKQ3",
        "Sadıqov Əvəz Zaur oğlu": "PXLQAF",
        "Səfərli Emil Ceyhun oğlu": "T9Y77E",
        "Səfərov Mirseyid Müşfiq oğlu": "KT5AEB",
        "Vəliyev Valeh Niyaz oğlu": "3RWMVD",
        "Abdullayev Məhəmməd Eltun oğlu": "OZZY2V",
        "Babazadə Koroğlu Tofiq oğlu": "0KJNDD",
        "Balacayev Murad Vüqar oğlu": "6B8U1J",
        "Bayramlı Ülvi Mənsur oğlu": "TAKKTE",
        "Cəbrayılov Amil Ramil oğlu": "5ORCVD",
        "Cəfərov Əkbər Rafiq oğlu": "322W88",
        "Əliyev Samir Oqtay oğlu": "XPR2PE",
        "Əşrəfzadə Yusif Oktay oğlu": "LQWBGX",
        "Fərəcli Nicat Adəm oğlu": "UTQJ4A",
        "Hümbətov Cavad Şöhrət oğlu": "JVGLIO",
        "İbrahimov Murad Kamal oğlu": "EPI49P",
        "İbrahimzadə Tunar Müşviq oğlu": "GS1708",
        "İsayev Fərid Etimad oğlu": "H7F7MT",
        "İsmayılov Azər Murad oğlu": "3DOLEM",
        "Qulusoy Rüzgar Azər oğlu": "DQVLEV",
        "Mehdiyev Ülvi Səyyab oğlu": "JY9AFU",
        "Məmmədli Nihat Elşən oğlu": "4YMO82",
        "Məmmədov Ağahüseyn Birgün oğlu": "VHHIXM",
        "Mikayılov Rəhman Mayis oğlu": "EXVYSB",
        "Mirzəşərifli Məhəmməd Rəsul oğlu": "01D9B6",
        "Səmədov Qardaşxan Qədir oğlu": "VTB9T7",
        "Sultanov Məhərrəm Ülvi oğlu": "PZ6CYD",
        "Şirinov Səid Natiq oğlu": "5RNUP1",
        "Yunusazdə Murad Habil oğlu": "DSQZW8",
        "Abbasov Sənan Zaur oğlu": "P8CRYC",
        "Abdurəfili Kənan Cahan oğlu": "MAA4OL",
        "Balayev Murad Vüqar oğlu": "9YVR1V",
        "Bayramov Rəvan Rövşən oğlu": "6AIP2A",
        "Bədəlov Fərid Sərdar oğlu": "Z2Y3JC",
        "Cəbiyev Ruslan Rauf oğlu": "K8LZ4P",
        "Əhmədov Nihad Eyvaz oğlu": "VBAGDZ",
        "Əlifov Nail Natiq oğlu": "R9MTND",
        "Əliyev Cənnətalı Vüqar oğlu": "6DYJ7D",
        "Əliyev Nihad Abdulla oğlu": "W0Q7P8",
        "Əliyev Tural Vahid oğlu": "82MQF1",
        "Əlizadə Abidin Ağahüseyn oğlu": "8911IE",
        "Həsənli Aqil Elnur oğlu": "MMZUW4",
        "İbrahimov Əliş Yalçın oğlu": "GYZVGA",
        "Quliyev Sərxan Səmid oğlu": "0G13V1",
        "Mehrəliyev Teymur Tofiq oğlu": "EJAO0I",
        "Məmmədov Elmar Natiq oğlu": "JZ6PYI",
        "Paşayev Emil Azər oğlu": "M0EOTC",
        "Paşayev Həsən Cavid oğlu": "QGFZTR",
        "Rzayev Sənan Vüsal oğlu": "OF5OZI",
        "Rzazadə Rza İlqar oğlu": "ZZVX6E",
        "Salmanlı Mənsur Hacıağa oğlu": "VCPHUE",
        "Süleymanov Sahib Tural oğlu": "NZ78G7",
        "Şahkərimov Nicat Elməddin oğlu": "OFL48J",
        "Tağıyev Elmir Həsən oğlu": "Z6SE59"
    },
    "selections": {},
    "work_taken_by": {
        "YT23A1": {},
        "YT23A2": {},
        "HFT23A1": {},
        "HFT23A2": {}
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
        # Qəbul ili dəyişib: köhnə baza əvəzlənir, 2023 təzə başlayır
        if db.get("roster_version") != ROSTER_VERSION:
            new_db = json.loads(json.dumps(DEFAULT_DB))
            # cari semestr/fənn adı saxlanılır (müəllim paneldən dəyişə bilir)
            for k in ("semester", "subject"):
                if k in db:
                    new_db[k] = db[k]
            save_db(new_db)
            return new_db
        # 2024 arxiv açarı sahibin istəyi ilə lazımsızdır — bir dəfə təmizlənir
        if not db.get("arxiv_2024_silindi"):
            try:
                redis_execute(['DEL', ARCHIVE_KEY])
                db["arxiv_2024_silindi"] = True
                save_db(db)
            except Exception:
                pass
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


def make_token(cid, role="student"):
    payload = json.dumps({"id": cid, "role": role, "exp": int(time.time()) + TOKEN_TTL})
    b = base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii").rstrip("=")
    sig = hmac.new(CABINET_SECRET.encode("utf-8"), b.encode("ascii"), hashlib.sha256).hexdigest()[:32]
    return f"{b}.{sig}"


def token_payload(token):
    """Etibarlıdırsa payload-ı ({id, role, exp}), əks halda None qaytarır."""
    try:
        b, sig = token.split(".")
        good = hmac.new(CABINET_SECRET.encode("utf-8"), b.encode("ascii"), hashlib.sha256).hexdigest()[:32]
        if not hmac.compare_digest(sig, good):
            return None
        payload = json.loads(base64.urlsafe_b64decode(b + "=" * (-len(b) % 4)))
        if payload.get("exp", 0) < time.time():
            return None
        return payload if payload.get("id") else None
    except Exception:
        return None


def verify_token(token):
    """Etibarlıdırsa credential id-ni, əks halda None qaytarır."""
    p = token_payload(token)
    return p.get("id") if p else None


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
    """Statik və ya dinamik (müəllimin əlavə etdiyi) hesab.
    Müəllim şifrəni yeniləyibsə, statik hash db["cred_overrides"] ilə əvəzlənir."""
    cred = CREDENTIALS.get(cid)
    if cred:
        ov = db.get("cred_overrides", {}).get(cid)
        return {**cred, "hash": ov} if ov else cred
    return db.get("credentials_dyn", {}).get(cid)


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
    resp = {"token": make_token(cid, cred["role"]), "id": cid, "name": cred["name"], "role": cred["role"]}
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
            "kollok_scores": db.get('kollok_scores', {}),
            "uploads": db.get('uploads', {}),
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
        "uploads": db.get('uploads', {}).get(name, {}),
        "kollok_manual": db.get('kollok_scores', {}).get(name, {}),
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


@app.route('/api/kollok-write', methods=['POST'])
def kollok_write():
    if not teacher_from_request():
        return jsonify({"error": "Yazmaq üçün əsas saytda müəllim kimi daxil olmalısınız."}), 401
    body = request.get_json(silent=True) or {}
    path = (body.get('path') or '').strip()
    if not re.fullmatch(r'(sessions|topics)/[A-Za-z0-9_\-/]+', path):
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


def _upload_auth():
    """(db, cred) — daxil olmuş istifadəçi; yoxdursa (None, None)."""
    cid = token_from_request()
    if not cid:
        return None, None
    db = load_db()
    cred = resolve_cred(cid, db)
    return (db, cred) if cred else (None, None)


@app.route('/api/upload-url', methods=['POST'])
def upload_url():
    """Kursant öz sərbəst iş faylı üçün birbaşa B2-yə yükləmə linki alır."""
    db, cred = _upload_auth()
    if not cred or cred.get('role') != 'student':
        return jsonify({"error": "Giriş tələb olunur."}), 401
    changed, resp, code = upload_url_action(db, request.get_json(silent=True) or {}, cred['name'])
    if changed:
        save_db(db)
    return jsonify(resp), code


@app.route('/api/upload-confirm', methods=['POST'])
def upload_confirm():
    db, cred = _upload_auth()
    if not cred or cred.get('role') != 'student':
        return jsonify({"error": "Giriş tələb olunur."}), 401
    changed, resp, code = upload_confirm_action(db, request.get_json(silent=True) or {}, cred['name'])
    if changed:
        save_db(db)
    return jsonify(resp), code


@app.route('/api/upload-link', methods=['POST'])
def upload_link():
    db, cred = _upload_auth()
    if not cred:
        return jsonify({"error": "Giriş tələb olunur."}), 401
    changed, resp, code = upload_link_action(
        db, request.get_json(silent=True) or {}, cred.get('role'), cred.get('name'))
    if changed:
        save_db(db)
    return jsonify(resp), code


@app.route('/api/upload-delete', methods=['POST'])
def upload_delete():
    db, cred = _upload_auth()
    if not cred:
        return jsonify({"error": "Giriş tələb olunur."}), 401
    changed, resp, code = upload_delete_action(
        db, request.get_json(silent=True) or {}, cred.get('role'), cred.get('name'))
    if changed:
        save_db(db)
    return jsonify(resp), code


@app.route('/api/upload-review', methods=['POST'])
def upload_review():
    """Müəllim fayla rəy qoyur (qəbul edildi / düzəliş lazımdır)."""
    db, cred = _upload_auth()
    if not cred:
        return jsonify({"error": "Giriş tələb olunur."}), 401
    changed, resp, code = upload_review_action(
        db, request.get_json(silent=True) or {}, cred.get('role'), cred.get('name'))
    if changed:
        save_db(db)
    return jsonify(resp), code


@app.route('/api/backup', methods=['GET', 'POST'])
def backup():
    """Gündəlik ehtiyat nüsxə — Vercel cron və ya müəllim əl ilə."""
    is_cron = request.headers.get('User-Agent', '').startswith('vercel-cron')
    if not is_cron and not teacher_from_request():
        return jsonify({"error": "İcazə yoxdur."}), 401
    ok, info = run_backup(load_db())
    if not ok:
        return jsonify({"error": info}), 502
    return jsonify({"success": True, "key": info})


@app.route('/api/backup-restore', methods=['POST'])
def backup_restore():
    """Müəllim göstərilən tarixin nüsxəsindən bazanı bərpa edir."""
    if not teacher_from_request():
        return jsonify({"error": "İcazə yoxdur."}), 401
    body = request.get_json(silent=True) or {}
    date = (body.get('date') or '').strip()
    snap = read_backup(date)
    if snap is None:
        return jsonify({"error": f"{date} tarixli nüsxə tapılmadı."}), 404
    save_prerestore(load_db())
    save_db(snap)
    return jsonify({"success": True, "date": date})


@app.route('/api/vt-check', methods=['POST'])
def vt_check():
    """Yüklənmiş faylı VirusTotal yoxlanışına göndərir."""
    db, cred = _upload_auth()
    if not cred:
        return jsonify({"error": "Giriş tələb olunur."}), 401
    changed, resp, code = vt_check_action(
        db, request.get_json(silent=True) or {}, cred.get('role'), cred.get('name'))
    if changed:
        save_db(db)
    return jsonify(resp), code


@app.route('/api/vt-status', methods=['POST'])
def vt_status():
    db, cred = _upload_auth()
    if not cred:
        return jsonify({"error": "Giriş tələb olunur."}), 401
    changed, resp, code = vt_status_action(
        db, request.get_json(silent=True) or {}, cred.get('role'), cred.get('name'))
    if changed:
        save_db(db)
    return jsonify(resp), code


@app.route('/api/cabinet-kollok', methods=['POST'])
def cabinet_kollok():
    """Müəllim kollokvium balını (1-3, 0-10) manual yazır; boş → canlı/statik bala qayıdır."""
    cid = token_from_request()
    if not cid or CREDENTIALS.get(cid, {}).get('role') != 'teacher':
        return jsonify({"error": "İcazə yoxdur."}), 401
    body = request.get_json(silent=True) or {}
    name = (body.get('name') or '').strip()
    if not name:
        return jsonify({"error": "Kursant adı göstərilməyib."}), 400
    try:
        k = int(body.get('k'))
    except (TypeError, ValueError):
        k = 0
    if k not in (1, 2, 3):
        return jsonify({"error": "Kollokvium nömrəsi 1-3 olmalıdır."}), 400
    db = load_db()
    if not any(name in members for members in db.get('teams', {}).values()):
        return jsonify({"error": "Kursant tapılmadı."}), 404
    ks = db.setdefault('kollok_scores', {})
    bal = body.get('bal')
    if bal is None or bal == '':
        ks.get(name, {}).pop(str(k), None)
        if name in ks and not ks[name]:
            del ks[name]
        save_db(db)
        return jsonify({"success": True, "name": name, "k": k, "bal": None,
                        "kollok_scores": db.get('kollok_scores', {})})
    try:
        bal = max(0, min(10, int(bal)))
    except (TypeError, ValueError):
        return jsonify({"error": "Bal 0-10 arası rəqəm olmalıdır."}), 400
    ks.setdefault(name, {})[str(k)] = bal
    save_db(db)
    return jsonify({"success": True, "name": name, "k": k, "bal": bal,
                    "kollok_scores": db.get('kollok_scores', {})})


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
