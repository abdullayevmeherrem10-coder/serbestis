# Sərbəst İş Platforması (sapyor.com) — Süni İntellekt üçün Tam Bələdçi

> Bu sənəd layihə üzərində işləyəcək istənilən süni intellekt (AI assistant) üçündür.
> Məqsəd: sistemin tam mənzərəsini, memarlığını, qaydalarını və təhlükəsizlik modelini
> izah etmək ki, dəyişiklik edərkən heç nə sınmasın. **Heç bir şifrə/sirr burada yoxdur.**

---

## 1. Layihə nədir?

FHN (Fövqəladə Hallar Nazirliyi) Akademiyasının Hərbi Kafedrası üçün **tədris platforması**.
Canlı ünvan: **https://sapyor.com**

İki əsas hissədən ibarətdir:

1. **Şəxsi kabinet sistemi** (`/`) — kursantlar öz nəticələrini görür, sərbəst iş seçir;
   müəllim isə bütün idarəetməni (ballar, kursantlar, taqımlar, işlər, tarixlər) aparır.
2. **Elektron Kollokvium Sistemi** (`/kollokvium/`) — müəllimin kollokvium imtahanı keçirmək
   üçün ayrı tətbiqi (suallar, taймер, avtomatik qiymətləndirmə). Yalnız müəllimə açıqdır.

Dil: **Azərbaycan dili** (bütün UI və kod şərhləri AZ dilindədir).

---

## 2. Texnologiya

| Qat | Texnologiya |
|-----|-------------|
| Frontend | Tək-fayllı HTML + inline CSS + vanilla JavaScript (framework yoxdur) |
| Backend (canlı) | Python **Flask** — `api/index.py` (Vercel Serverless Function) |
| Backend (lokal) | Python `http.server` — `server.py` (port 8080) |
| Verilənlər (canlı) | **Upstash Redis** (REST API ilə) |
| Verilənlər (lokal) | `database.json` faylı |
| Kollokvium DB | **Firebase Realtime Database** (ayrı, `kollokvium1` layihəsi) |
| Fayl anbarı | **Backblaze B2** (S3-uyğun; bucket: `sapyor-serbest-isler`, private) |
| Virus yoxlanışı | **VirusTotal v3 API** (pulsuz plan: 4 sorğu/dəq, 500/gün) |
| Sənəd baxışı | **Microsoft Office Online viewer** (iframe embed) |
| Hostinq | **Vercel** (Hobby plan), `main` budağından avtomatik deploy |
| Cron | Vercel Cron: hər gecə 01:00 UTC → `/api/backup` |
| Reverse proxy / gate | Vercel Edge **`middleware.js`** |

---

## 3. Fayl strukturu və hər faylın rolu

```
├── index.html              # Əsas SPA (kabinet + müəllim panel) — LOKAL server üçün
├── public/index.html       # EYNİ fayl — Vercel deploy üçün (İKİSİ SİNXRON OLMALIDIR!)
├── public/kitab.html       # Ədəbiyyat (kitab oxuyucusu) — deploy
├── kitab.html              # Eyni — lokal
├── public/kollokvium/index.html  # Elektron Kollokvium tətbiqi — deploy
├── Kollokvium/index.html   # Eyni — lokal (böyük "K"! NTFS-də kollokvium/=Kollokvium/)
│
├── api/index.py            # Flask backend — BÜTÜN API endpointləri (canlı)
├── api/_credentials.py     # Kabinet girişləri: {ID: {hash, name, team|role}} (SHA-256 hash)
├── api/_results.py         # Statik kollokvium/mənimsəmə/imtahan nəticələri (2 YT qrupu)
├── api/_roster.py          # Taqım/kursant idarəetmə məntiqi (əlavə/redaktə/sil/şifrə yeniləmə)
├── api/_fbauth.py          # Firebase service-account OAuth token generatoru
├── api/_b2.py              # Backblaze B2 SigV4 imzalama (stdlib, boto3 YOX): presign PUT/GET,
│                           #   server-side HEAD/GET/PUT/DELETE, key_prefix() (dev/canlı ayrımı)
├── api/_uploads.py         # Fayl yükləmə əməliyyatları: url/confirm/link/delete/review + VT
├── api/_vt.py              # VirusTotal v3 API (multipart upload + analysis sorğusu)
├── api/_backup.py          # Bazanın gündəlik B2 nüsxəsi (run_backup/read_backup/save_prerestore)
│
├── server.py               # Lokal dev server (api/index.py-ın sadələşmiş ekvivalenti)
├── database.json           # Lokal verilənlər (canlıda Upstash Redis-dədir)
├── middleware.js           # Vercel Edge: /kitab/ və /kollokvium/ giriş qapısı
├── vercel.json             # Rewrites + təhlükəsizlik başlıqları (CSP, no-store və s.)
├── requirements.txt        # flask, google-auth, requests
│
├── public/kitab/*.jpg      # Kitab səhifələri (şəkillər) — repo-da yalnız public/-də
├── public/loqo-esas.webp   # FHN Akademiya emblemi
└── .gitignore              # Sirləri qoruyur (aşağıda)
```

### Gitignore-lanan (repo-da OLMAYAN) fayllar
- `kabinet_girisleri.txt` — açıq şifrələrin paylama siyahısı (yalnız sahibin kompüterində).
  **Qeyd:** müəllim paneldən şifrə yeniləyəndən sonra bu fayl köhnəlir — əsl mənbə bazadır.
- `admin_secret.txt`, `firebase_secret.txt`, `firebase_service_account.json` — sirlər
- `b2_config.json` — Backblaze açarları + lokal `"prefix": "dev/"` (lokal server bunu oxuyur)
- `vt_secret.txt` — VirusTotal API açarı (lokal)
- Bunlar heç vaxt commit edilməməlidir.

---

## 4. ⚠️ KRİTİK QAYDALAR (pozulsa sistem sınır)

1. **İKİ NÜSXƏ SİNXRON:** `index.html` (kök) və `public/index.html` **eyni olmalıdır**.
   Birini dəyişdikdə mütləq o birinə kopyala:
   `cp public/index.html index.html`. Eyni qayda `kitab.html` və kollokvium üçün də.
   - Vercel `public/`-dən verir, lokal server kökdən.

2. **PUSH-DAN ƏVVƏL `git fetch`:** lokal repo uzaqdan geri qala bilər. Üzərinə yazma;
   əvvəl `git fetch origin`, sonra push.

3. **İKİ AYRI DİNAMİK BAZA:** lokal `database.json`-a, canlı Upstash Redis-ə yazır.
   **SİNXRON DEYİL.** Yəni lokalda yazılan ballar/seçimlər canlıya keçmir və əksinə.
   Real dəyişiklikləri (ballar, tarixlər, roster) **sapyor.com-da** etmək lazımdır.

4. **HTML-də istifadəçi mətni = XSS riski:** kursant/taqım/iş adları, qeydlər innerHTML-ə
   qoyulanda mütləq `esc()` funksiyasından keçirilməlidir (artıq mövcuddur).

5. **Backend dəyişikliyi = həm `api/index.py`, həm `server.py`:** yeni endpoint əlavə
   edəndə hər ikisinə eyni məntiqi yaz (biri canlı, biri lokal).

6. **LOKAL VƏ CANLI EYNİ B2 BUCKET-İ PAYLAŞIR:** fayl açarları deterministikdir
   (kursant adının hash-i), ona görə lokal test yükləmələri canlı faylların üstünə yaza
   bilər. Qoruma: lokal `b2_config.json`-da `"prefix": "dev/"` var → `_b2.key_prefix()`
   lokal açarlara `dev/` əlavə edir; canlıda (Vercel env) prefix boşdur.
   **Lokal test təmizliyi yalnız `dev/` açarlarına toxunmalıdır!** (2026-07-20-də bu
   qayda olmadığı üçün canlı fayllar təsadüfən silinmişdi — B2 versiyalarından bərpa olundu.)

7. **B2 lifecycle:** silinmiş/üstünə yazılmış faylların köhnə versiyaları 7 gün saxlanılır
   (təsadüfi silinmə bərpaolunandır — `b2_copy_file` köhnə versiyadan), sonra avtomatik təmizlənir.

---

## 5. Autentifikasiya və token sistemi

### Giriş məlumatları
- Hər istifadəçinin **ID**-si var (kursant: `Y1-01`, `Y2-05`, `H1-03`, `H2-07`; müəllim: `MUELLIM`).
  - `Y1`=YT23A1, `Y2`=YT23A2, `H1`=HFT23A1, `H2`=HFT23A2 (2023 qəbul; 2024 qəbul arxivləşdirilib).
- Şifrələr **yalnız SHA-256 hash** kimi saxlanılır (`api/_credentials.py`).
  - Hash formatı: `sha256(f"{ID_UPPERCASE}:{password}")`.
  - Açıq şifrələr heç yerdə (nə kodda, nə bazada) yoxdur — yalnız gitignore-lanmış
    `kabinet_girisleri.txt`-də. İtirilsə bərpa OLUNMUR, yeni şifrələr yaradılmalıdır.
- Kursant şifrələri 10 simvol, müəllim 12 simvol (alfabet: qarışdırıcı 0/O/1/I çıxarılıb).

### Token (sessiya)
- Giriş uğurlu olanda server **HMAC-imzalı token** verir: `base64(payload).hmac_sig`.
  - Payload: `{id, role, exp}` (exp = 12 saat sonra).
  - İmza sirri: `CABINET_SECRET` env (Vercel-də) və ya avtomatik törədilir.
- Token həm `Authorization: Bearer <token>` header-ində, həm də `kabinet` **cookie**-də
  saxlanılır (cookie kitab/kollokvium giriş qapısı üçün lazımdır).
- **Rol tokendə imzalanır**, amma server icazə yoxlayanda rolu tokendən yox,
  **bazadakı hesabdan** (`CREDENTIALS`/`credentials_dyn`) götürür — yəni tokeni saxta
  düzəldib özünü müəllim göstərmək mümkün deyil.
- **Sessiya yalnız brauzer yaddaşındadır** (sessionStorage İSTİFADƏ OLUNMUR):
  refresh (F5) → avtomatik çıxış → yenidən giriş. İstisna: kitab/kollokviumdan geri
  qayıdanda `cab_nav` bir-dəfəlik qeydlə kabinet cookie-dən bərpa olunur.

### Əsas köməkçi funksiyalar (backend)
- `raw_cred(cid, db)` → statik və ya dinamik hesab.
- `resolve_cred(cid, db)` → aktual hesab (ad/taqım dəyişmələri tətbiq edilmiş; silinibsə None).
- `token_payload(token)` / `verify_token(token)` → HMAC yoxlaması.
- `token_from_request()` → header/cookie-dən id çıxarır.
- `teacher_from_request()` → yalnız müəllim üçün True.

---

## 6. API Endpointləri (hamısı `api/index.py` + `server.py`)

### Açıq (autentifikasiyasız)
- `GET /api/semester-info` → `{semester, subject}` (giriş səhifəsində göstərmək üçün).

### Autentifikasiya
- `POST /api/cabinet-login` `{id, password}` → `{token, id, name, role, team?}`.
  Rate-limitli (7 səhv → 15 dəq IP blok).
- `GET /api/cabinet-data` (token) → istifadəçinin bütün datası.
  - **Müəllim:** bütün nəticələr, seçimlər, ballar, taqımlar, işlər, tarixlər, exam_scores.
  - **Kursant:** YALNIZ öz adına aid data (başqasınınkı cavaba düşmür — server filtrləyir).

### Kursant əməliyyatları
- `GET /api/teams` (token) → taqım→kursantlar (yalnız daxil olanlara).
- `GET /api/works?team=X` (token) → işlər + kim götürüb.
- `POST /api/select` `{name, key, team, work_ids}` → sərbəst iş seçimi (təsdiq açarı yoxlanılır).
- `GET /api/student-status?name&key` → seçim statusu (rate-limitli).

### Müəllim əməliyyatları (hamısı `role != teacher → 401`)
- `POST /api/cabinet-scores` `{name, serbest, defter}` → mənimsəmə bal komponentləri (0-10).
- `POST /api/cabinet-exam` `{name, bal}` → imtahan balı (0-100); qiymət avtomatik hesablanır.
- `POST /api/cabinet-kollok` `{name, k: 1|2|3, bal: 0-10|null}` → kollokvium balının manual
  düzəlişi. `null`/boş → manual bal silinir, avtomatik (canlı/statik) bala qayıdır.
  Saxlanma: `db["kollok_scores"][ad]["1|2|3"]`. UI-də manual ballar MAVİ göstərilir.
- `POST /api/cabinet-deadline` `{name, deadline}` → fərdi son tarix (boş = silmə).
- `POST /api/cabinet-semester` `{semester, subject}` → semestr/fənn adı.
- `POST /api/cabinet-reset` `{name}` → bir kursantın seçimini sıfırla.
- `POST /api/cabinet-reset-all` → bütün seçimləri sıfırla.
- `POST /api/cabinet-roster` `{action, ...}` → taqım/kursant/iş idarəetmə (bax §9).
- `POST /api/kollok-write` `{path, data}` → Firebase-ə yazma proxy-si (bax §10).
- `POST /api/upload-review` `{name, kind, status: accepted|revise|"", note}` → fayl rəyi (bax §18).
- `POST /api/vt-check` `{name, kind}` / `POST /api/vt-status` `{name, kind}` → VirusTotal (bax §18).
- `GET /api/arxiv-imtahan` → `{semestrler: [...]}` — müəllimin yazdığı keçmiş semestrlər
  (`db["arxiv"]`, yenidən köhnəyə) + repo-dakı statik 2024 imtahan arxivi (`api/_arxiv.py`, `static: true`).
- `POST /api/arxiv-save` `{semester, subject, qruplar: {taqım: {ad: {k1,k2,k3,serbest,defter,imtahan}}}, clear}`
  → semestr sonu arxivi (bax §21). Server koll./mənimsəmə cəmini və qiyməti özü hesablayır.
  `clear=true` olsa əvvəl B2-yə qoruyucu nüsxə (`save_prerestore`), sonra scores/exam_scores/
  kollok_scores/selections/deadlines/work_taken_by təmizlənir (taqımlar, girişlər, uploads qalır).
- `POST /api/arxiv-delete` `{id}` → dinamik arxiv girişini silir (statik 2024 silinmir).
- `GET|POST /api/backup` → əl ilə ehtiyat nüsxə (cron da bunu çağırır — `vercel-cron` UA ilə).
- `POST /api/backup-restore` `{date: "YYYY-MM-DD"}` → nüsxədən bərpa (bax §19).

### Fayl yükləmə (kursant, bax §18)
- `POST /api/upload-url` `{kind: docx|pptx, fname, size}` → presigned PUT URL (kursant-only).
- `POST /api/upload-confirm` `{kind, fname}` → yükləmədən sonra yoxlama + metadata (kursant-only).
- `POST /api/upload-link` `{name?, kind, mode: view|download}` → presigned GET URL
  (kursant yalnız özününkü; müəllim hamısını).
- `POST /api/upload-delete` `{name?, kind}` → fayl silmə (kursant özününkü; müəllim hamısını).

### Köhnə admin endpointləri (hələ mövcud, `ADMIN_PASSWORD` ilə qorunur)
- `/api/status`, `/api/admin/*` — köhnə admin panel üçün idi (`admin.html` silinib),
  amma endpointlər qalıb və şifrə + rate-limit ilə qorunur. Yeni funksiya üçün istifadə etmə.

---

## 7. Verilənlər strukturu (`database.json` / Upstash Redis eyni sxem)

```jsonc
{
  "roster_version": "2023-qebul",              // qəbul ili markeri (bax §7.1)
  "teams": { "YT23A1": ["Ad Soyad oğlu", ...], "YT23A2": [...], "HFT23A1": [...], "HFT23A2": [...] },
  "works": ["Sərbəst iş adı 1", ...],          // 50 iş
  "keys":  { "Ad Soyad": "ACAR6" },            // sərbəst iş təsdiq açarları
  "selections": { "Ad Soyad": [4, 7] },        // seçdiyi 2 işin indeksi
  "work_taken_by": { "YT23A1": { "4": "Ad Soyad" } },  // taqım→{işİndeks: kursant}
  "scores": { "Ad Soyad": { "serbest": 8, "defter": 9 } },  // mənimsəmə komponentləri
  "exam_scores": { "Ad Soyad": 74 },           // müəllimin manual imtahan balı
  "deadlines": { "Ad Soyad": "20 may 2026" },  // fərdi son tarix
  "semester": "2025/2026 yaz semestri",
  "subject": "Hərbi Mühəndis Texnikası",
  "credentials_dyn": { "Y1-25": {hash, name, team} },  // müəllimin əlavə etdiyi kursantlar
  "renames": { "Köhnə Ad": "Yeni Ad" },        // statik nəticələri yeni adla uyğunlaşdırır
  "team_renames": { "Köhnə Taqım": "Yeni Taqım" },
  "kollok_scores": { "Ad Soyad": {"1": 9, "3": 7} },   // müəllimin MANUAL kollokvium balları (mavi)
  "cred_overrides": { "Y1-02": "sha256hash" },  // şifrə yeniləməsi: statik hesabın yeni hash-i
                                                // (raw_cred() bunu CREDENTIALS-dan üstün tutur)
  "arxiv": [ {                                  // semestr sonu arxivləri (yenidən köhnəyə, maks 30; bax §21)
    "id": "20260902-130000", "semester": "2025/2026 yaz semestri", "subject": "Hərbi Mühəndis Texnikası",
    "ts": "02.09.2026 13:00",
    "qruplar": { "YT23A1": { "Ad Soyad": { "k1": 8, "k2": 7, "k3": null, "koll": 15, "serbest": 9,
                                           "defter": 8, "menimseme": 32, "imtahan": 74, "qiymet": "C “Yaxşı”" } } }
  } ],
  "uploads": {                                  // kursant faylları (fayl özü B2-dədir!)
    "Ad Soyad": {
      "docx": { "key": "uploads/<hash16>-docx.docx", "fname": "orijinal ad.docx",
                "size": 123456, "ts": "20.07.2026 09:00",
                "vt": { "id": "...", "status": "pending|clean|flagged", "malicious": 0, "suspicious": 0 },
                "review": { "status": "accepted|revise", "note": "qısa rəy", "ts": "..." } },
      "pptx": { ... }
    }
  }
}
```

### §7.1 Qəbul ili köçürməsi (`roster_version`)
- `api/index.py`-da `ROSTER_VERSION` sabiti var (hazırda `"2023-qebul"`). Canlıda `load_db()`
  bazadakı `roster_version` ilə müqayisə edir: uyğun gəlmirsə köhnə baza əvəzlənir —
  `DEFAULT_DB`-dən təzə baza yaradılır (yalnız semester/subject köhnədən saxlanılır).
- 2024 qəbulun məlumatları sahibin istəyi ilə TAM silinib (Redis arxiv açarı, B2 uploads,
  köhnə gecə nüsxələri). Saxlanan yeganə şey: **`arxiv/imtahan_2024.json`** — 2024 qəbulun
  imtahan nəticələri (repo-da).
- Firebase-dəki köhnə kollokvium sessiyaları (`K*_YT_24A1` və s.) yerində qalır —
  yeni qəbul fərqli qrup açarları (`K*_YT_23A1`) istifadə etdiyi üçün toqquşmur.

### Statik nəticələr (`api/_results.py`)
- 2 qrup: `"YT 23A1"`, `"YT 23A2"` (hər biri `team`, `kollok`, `menimseme`, `imtahan`).
  2023 qəbul üçün xəritələr hələ BOŞDUR — semestr nəticələri hazır olanda doldurulur.
- `kollok`: `{ad: ["5","6","5"]}` (K1,K2,K3 balları, 0-10).
- `imtahan`: `{ad: ["74", "C “Yaxşı”"]}` (bal, qiymət).
- **Vacib:** HTML-də cədvəllər BOŞDUR — nəticələr bu fayldan API ilə gəlir.
  Statik nəticəni dəyişmək üçün `_results.py` redaktə olunur.
- `renames`/`team_renames` bu statik məlumatı dinamik ad dəyişmələri ilə uyğunlaşdırır
  (`effective_results(db)` funksiyası tətbiq edir).

---

## 8. Mənimsəmə balı düsturu

**Mənimsəmə = Kollokvium cəmi (maks 30) + Sərbəst iş (maks 10) + Dəftər/İntizam (maks 10) = maks 50**

- **Kollokvium cəmi** = K1+K2+K3 (hərəsi maks 10). Bal mənbələrinin PRİORİTETİ:
  **manual (`kollok_scores`, mavi) > canlı E-Kollokvium (Firebase) > statik `_results.py`**.
  Frontend-də `mergedKollokFor()` bu qaydanı tətbiq edir; müəllim cədvəlində ballar redaktə
  olunan inputlardır (`saveKollokScore`). Manual bal Firebase-dəki orijinala TOXUNMUR.
- **Sərbəst iş** və **Dəftər/İntizam** — müəllim `cabinet-scores` ilə əl ilə yazır.
- Kursant kabinetində bölgü + cəm avtomatik göstərilir. Müəllimin bal yazması dərhal əks olunur.

### İmtahan qiyməti (baldan avtomatik)
`91+ → A "Əla"`, `81+ → B "Çox yaxşı"`, `71+ → C "Yaxşı"`, `61+ → D "Kafi"`,
`51+ → E "Qənaətbəxş"`, `<51 → F "Qeyri-kafi"`. (`exam_grade()` funksiyası.)

---

## 9. Roster idarəetmə (`api/_roster.py`, `POST /api/cabinet-roster`)

`{action}` dəyərləri:
- `add_team` `{team}` — yeni boş taqım.
- `rename_team` `{team, new}` — bütün istinadlar + statik nəticələr yenilənir.
- `delete_team` `{team}` — taqımı kursantları, balları və B2 faylları ilə birlikdə silir.
  **Əsas 4 qrup (statik girişli) silinə BİLMƏZ** — server rədd edir.
- `add_student` `{team, name}` — yeni kursant; **avtomatik ID+şifrə+açar** yaradılır,
  cavabda `{id, password}` bir dəfə qaytarılır (şifrə yalnız hash saxlanılır).
- `rename_student` `{name, new}` — bütün strukturlarda (ballar, seçimlər, tarixlər,
  girişlər, statik nəticələr, fayllar, manual kollok balları) yayılır, heç nə itmir.
- `delete_student` `{name}` — məlumatları + B2 faylları təmizlənir, girişi deaktiv olunur.
- `reset_password` `{name}` — YALNIZ bu kursanta yeni şifrə; cavabda `{id, password}` bir dəfə.
  Dinamik hesabda hash yerində yenilənir; statik hesab üçün `db["cred_overrides"]`-ə yazılır
  (`raw_cred()` override-ı `_credentials.py`-dakı hash-dən üstün tutur).
- `reset_all_passwords` `{team}` — taqımın BÜTÜN kursantlarına yeni şifrələr; cavabda
  `creds: [{name, id, password}]` (UI bunu txt fayl kimi endirir).
- `add_work` / `edit_work` / `delete_work` — iş siyahısı idarəsi.
  - Seçilmiş işi silmək **bloklanır** (əvvəl seçim sıfırlanmalı).
  - İş silinəndə bütün seçim indeksləri avtomatik yenidən hesablanır.

---

## 10. Elektron Kollokvium ↔ Firebase inteqrasiyası

- Kollokvium tətbiqi (`public/kollokvium/index.html`) imtahan nəticələrini
  **Firebase Realtime DB**-yə yazır. Yol formatı: `sessions/K{1|2|3}_{QRUP}` (məs. `K1_YT_23A1`).
- **Firebase qaydaları:** `.read: true, .write: false` — heç kim birbaşa yaza bilmir.
- Yazma yalnız **`/api/kollok-write` proxy-si** üzərindən gedir:
  - `fbWrite(path, data)` funksiyası tətbiqdə (data=null → silmə).
  - Proxy **müəllim tokeni/cookie-si** tələb edir (`teacher_from_request`).
  - Server Firebase-ə **service-account OAuth tokeni** ilə yazır (`api/_fbauth.py`).
  - Beləcə heç kim (kursant daxil) balları saxtalaşdıra bilməz.
- **Oxu açıqdır:** kursant kabineti Firebase-dən birbaşa oxuyur (`fetchLiveKollok`)
  və canlı kollokvium ballarını göstərir.
- Səslər Web Audio API (`AudioContext` + oscillator) ilə yaradılır; `unlockAudio` ilk
  istifadəçi hərəkətində konteksti aktivləşdirir (brauzer avtoplay siyasəti).

---

## 11. Frontend axını (`index.html`)

1. **Giriş ekranı** (`#cabinetLogin`) — sayt açılanda birbaşa bura düşür (semestr seçimi yoxdur).
2. **Kursant kabineti** (`#cabinetView`, 2026-09-02-dən sadələşdirilmiş) — hero (ad, taqım, ID,
   "Ədəbiyyata bax" keçidi), fərdi deadline banneri (+geri sayım, §20), **"Nəticələrim"** kartı
   (`#cabResults`, `buildPersonalCards()`: Kollokvium K1-K3 çipləri + cəm/30, Sərbəst iş/10,
   Dəftər/10, Mənimsəmə/50, İmtahan/100 + qiymət; canlı ballar yaşıl nöqtə, detallar `.cab-subrow`),
   **"Sərbəst iş"** kartı — 3 addım: 1) Mövzu seçimi (`#cabSerbest`, `renderCabSerbest()`),
   2) Hazırlıq (titul vərəqi + hazırlanma qaydası), 3) Təhvil (fayl yükləmə + müəllim rəyi, §18).
   Köhnə KPI kartları və ayrı nəticə kartları ləğv edilib — bütün məlumat "Nəticələrim"-dədir.
   - Sərbəst iş seçmək üçün `startSerbestFlow()` → `#appView` (student-mode).
3. **Müəllim paneli** (`#appView.teacher-mode`, 2026-09-02-dən sadələşdirilmiş) — bir sətirlik
   naviqasiya: 4 tab (solda) + **qlobal taqım `select`-i** (`#tpTeamSel`, `tpTeam`) + axtarış (`tpFilter`).
   Seçilən taqım bütün tablara tətbiq olunur. E-Kollokvium keçidi üst paneldə düymədir (`#ekollokBtn`).
   - **Kursantlar tabı:** sakit cədvəl (seçim, sənəd nişanları, mənimsəmə, imtahan, klik-redaktə son tarix,
     ⋯ menyusu). Kursantın adına klik → **sağdan açılan panel** (`#tpDrawer`, `openDrawer/renderDrawer`):
     seçim + sıfırla, sənədlər (Bax/Endir/Virus yoxla/Qəbul et/Düzəliş istə/Sil), bütün bal inputları,
     Hesab (ad dəyiş / yeni şifrə / sil). Əməliyyat funksiyaları kursantı `ctxName(el)` ilə
     (ən yaxın `[data-name]`) tapır — cədvəl sətri, panel və ⋯ menyusu eyni funksiyaları paylaşır.
   - **Ballar tabı:** bir cədvəl: K1 K2 K3 | Koll. | Sərbəst | Dəftər | Mənimsəmə | İmtahan | Qiymət
     (`renderBallar`, `fillScoreInputs`, `updateBalRow` yerində hesablayır, `syncScoreViews` panel/cədvəl/sətri
     sinxronlaşdırır). Manual kollokvium balı mavi (§8). Bütün taqımlar (HFT daxil) görünür.
   - **Sərbəst işlər tabı:** işlərin bölgüsü (əlavə/redaktə/sil).
   - **Parametrlər tabı:** semestr/fənn, dəftər mövzuları, taqımlar (ad dəyiş / şifrələri yenilə / sil / yeni),
     Arxiv kartı (§21), "Təhlükəli əməliyyatlar" (bütün seçimləri sıfırla).
- Əsas render funksiyaları: `showCabinet()`, `showTeacherApp()`, `buildPersonalCards()`,
  `renderTeacherPanel()`, `renderTpStudents()`, `renderBallar()`, `renderDrawer()`, `renderTeamList()`,
  `renderUploads()`.
- Tema keçidi: `toggleTheme()` / `updateThemeIcon()` (bax §16).
- İstifadəçi mətni HTML-ə qoyulanda `esc()`-dən keçir (XSS qoruması).

---

## 12. Təhlükəsizlik modeli (icmал)

| Təhdid | Müdafiə |
|--------|---------|
| İcazəsiz əməliyyat | Hər dəyişiklik endpointi serverdə rol yoxlayır (kursant → 401) |
| Başqasının datası | Server tokendəki öz adına aid data verir; başqası cavaba düşmür |
| Saxta token/rol | HMAC imza; rol bazadan oxunur, tokendən yox |
| Brute-force | 7 səhv → 15 dəq IP blok (Upstash) |
| Zəif şifrə | 10-12 simvol, SHA-256 hash |
| Firebase saxtalaşdırma | `.write:false` + müəllim-only proxy + service-account |
| Kitab açıqlığı | `kabinet` cookie + Edge middleware (giriş tələb) |
| Kollokvium açıqlığı | Middleware: yalnız `role=teacher` cookie; no-store keş |
| XSS | Bütün istifadəçi mətni `esc()`-dən keçir |
| Data sızması/inject | CSP başlığı (default-src self, object-src none və s.) |
| İnfrastruktur | Vercel idarə edir (TLS, OS, DDoS-un bir hissəsi) |
| Çıxışdan sonra giriş | Cookie silinir + no-store; refresh-də avtomatik çıxış |

---

## 13. Mühit dəyişənləri (Vercel Environment Variables — dəyərlər GİZLİ)

| Dəyişən | Rolu |
|---------|------|
| `UPSTASH_REDIS_REST_URL` / `UPSTASH_REDIS_REST_TOKEN` | Canlı verilənlər bazası |
| `CABINET_SECRET` | Token HMAC imza sirri (middleware + backend eyni istifadə edir) |
| `FIREBASE_SERVICE_ACCOUNT` | Firebase yazma üçün service-account JSON (tam mətn) |
| `ADMIN_PASSWORD` | Köhnə admin endpointləri üçün |
| `FIREBASE_SECRET` | (Köhnə/ehtiyat — database secret; adətən istifadə olunmur) |
| `B2_KEY_ID` / `B2_APP_KEY` | Backblaze B2 API açarları (bucket-scoped) |
| `B2_BUCKET` | `sapyor-serbest-isler` |
| `B2_ENDPOINT` | `s3.us-west-004.backblazeb2.com` |
| `B2_PREFIX` | (adətən təyin OLUNMUR — canlıda boş; lokalda `b2_config.json`-dan `dev/` gəlir) |
| `VT_API_KEY` | VirusTotal API açarı |

- Bu dəyişənlərdən biri dəyişsə, Vercel-də **Redeploy** lazımdır.
- `CABINET_SECRET` dəyişsə bütün mövcud tokenlər keçərsizləşir (hamı yenidən girir).

---

## 14. Lokal development

```bash
# Server (port 8080)
python server.py
# Brauzerdə: http://localhost:8080/
```

- Lokal server `database.json`-dan oxuyur/yazır (Upstash yox).
- Firebase yazması üçün lokalda `firebase_service_account.json` (gitignore) və ya açar lazımdır.
- Lokal test verilənləri canlıya təsir etmir (ayrı bazalar).

---

## 15. Tez-tez görülən tapşırıqlar

- **Statik nəticə əlavə/dəyiş:** `api/_results.py` redaktə et (HTML-də cədvəl yoxdur).
- **Yeni endpoint:** həm `api/index.py`, həm `server.py`-a əlavə et; müəllim əməliyyatıdırsa
  `role != teacher → 401` yoxlaması qoy.
- **UI dəyişikliyi:** `public/index.html`-i dəyiş, sonra `cp public/index.html index.html`.
- **Şifrə yeniləmək (NORMAL YOL):** müəllim panelindən — kursant sətrində 🔑 (fərdi) və ya
  taqım panelində "🔑 Taqımın şifrələrini yenilə" (kütləvi, txt endirilir). Bazada
  `cred_overrides`-ə yazılır, `_credentials.py`-a toxunulmur. `kabinet_girisleri.txt` köhnəlir.
- **Bütün sistemi sıfırdan şifrələmək (nadir):** `gen_creds` tipli skript `api/_credentials.py`
  + `kabinet_girisleri.txt` yaradır — amma sonra `cred_overrides`-i də təmizləmək lazımdır.
- **Deploy:** `git add ... && git commit && git push origin main` → Vercel avtomatik deploy.
  Yoxlama: ~1-2 dəqiqə sonra sapyor.com.

---

## 16. Dizayn qeydləri

- Palitra: adaçayı-yaşıl `#455f51` / `#8fa69b` / `#6b8f7b`, açıq krem-yaşıl gradient fon.
- İmza elementlər: ofset "back-box" kölgələr, shimmer düymələr, hissəcik (particle) fon animasiyası.
- Şrift: Inter (+ bəzi başlıqlarda Playfair Display).
- Bütün sayt + kitab + kollokvium eyni dizayn dilindədir.

### Light/Dark tema
- **Default LIGHT**; sağ yuxarıdakı düymə (🌙/☀️) dark moda keçirir; seçim `localStorage.theme`-də.
- Mexanizm: `html[data-theme="dark"]` CSS dəyişənləri override edir; `<head>`-dəki kiçik
  skript yaddaşdakı temanı render-dən əvvəl tətbiq edir (ağ parıltı olmasın).
- **Yeni komponent yazanda hardcoded ağ/tünd rəng İSTİFADƏ ETMƏ** — mövcud dəyişənləri işlət:
  `--surface-85..97`, `--surface-solid`, `--text`, `--text-muted`, `--text-dim`,
  `--accent-ink` (mətn üçün yaşıl), `--input-border`, `--card-border`, `--table-head`, `--bg-body`.
- Hissəcik animasiyası tema-həssasdır (dark-da açıq yaşıl palitra).
- Manual kollokvium balları MAVİ: `.score-inp.manual-edit` / `.bal.bal-manual`
  (light: `#1565c0`, dark: `#64b5f6`).

---

## 17. Vacib xəbərdarlıqlar (dəyişiklik edərkən)

1. `index.html` ↔ `public/index.html` sinxronluğunu HƏR DƏFƏ yoxla.
2. Backend dəyişikliyini həm Flask (`api/index.py`), həm lokal (`server.py`) et.
3. İstifadəçi mətni HTML-ə → `esc()`.
4. Firebase-ə birbaşa yazma ƏLAVƏ ETMƏ — həmişə `/api/kollok-write` proxy-dən.
5. Yeni xarici resurs (CDN, font, API) əlavə edirsənsə, `vercel.json`-dakı **CSP**-yə
   müvafiq mənbəni əlavə et, yoxsa brauzer bloklayar.
6. Sirləri (şifrə, açar, JSON) heç vaxt commit etmə — `.gitignore`-a əlavə et.
7. Real məlumat dəyişikliyi sapyor.com-da edilir (lokal baza ayrıdır).
8. Lokal fayl testlərindən sonra B2 təmizliyi YALNIZ `dev/` açarlarına toxunmalıdır (bax §4.6).

---

## 18. Fayl təhvili sistemi (Backblaze B2 + Office viewer + VirusTotal)

### Memarlıq — fayllar bizim serverdən KEÇMİR
Vercel serverless funksiyaları maks ~4.5 MB sorğu qəbul edir, ona görə axın belədir:

1. Kursant kabinetində "Sərbəst işimi təhvil ver" kartından fayl seçir
   (**yalnız `.docx` ≤10MB və `.pptx` ≤25MB** — client + server yoxlayır).
2. Brauzer `POST /api/upload-url` → server presigned PUT URL verir (15 dəq etibarlı).
3. Brauzer faylı **birbaşa B2-yə** PUT edir (XHR, faiz göstəricisi ilə).
4. Brauzer `POST /api/upload-confirm` → server B2-də HEAD (ölçü) + ilk 2 bayt yoxlayır
   (`PK` = həqiqi Office/ZIP; deyilsə fayl B2-dən silinir və rədd olunur) →
   metadata `db["uploads"]`-a yazılır.
5. Baxış/endirmə: `POST /api/upload-link` → presigned GET (1 saat).
   - **Baxış:** Office Online viewer modalda —
     `https://view.officeapps.live.com/op/embed.aspx?src=<encoded presigned url>`.
     18.6MB pptx problemsiz göstərir. Müəllim faylı ENDİRMƏDƏN baxır (virus riski sıfır).
   - **Endirmə:** `response-content-disposition: attachment` ilə.

### Açar sxemi
- `{prefix}uploads/{sha256(ad)[:16]}-{docx|pptx}.{ext}` — deterministik, təkrar yükləmə
  üstünə yazır. Prefix: canlıda boş, lokalda `dev/` (bax §4.6).
- Mövcud metadata varsa, açar oradan götürülür (`_key_for`), ona görə ad dəyişəndə köhnə açar işlək qalır.

### Təhlükəsizlik qatları
1. Yalnız `.docx`/`.pptx` — bu formatlarda makro İŞLƏYƏ BİLMİR (makrolular `.docm`/`.pptm`).
2. ZIP magic (`PK`) yoxlanışı — adı dəyişdirilmiş `.exe` və s. rədd olunur.
3. Baxış saytdaca (endirmədən) — icra riski yoxdur.
4. **VirusTotal** (yalnız müəllim, avtomatik DEYİL): cədvəldə 🛡? düyməsi → server faylı
   B2-dən endirir → VT-yə göndərir (`_vt.scan_bytes`) → `vt.status: pending` →
   ⏳ düyməsi ilə nəticə sorğulanır → `clean` (yaşıl 🛡) / `flagged` (qırmızı ⚠, hover-də
   neçə mühərrikin həyəcan verdiyi). Nəticə metadata-da saxlanılır, təkrar yoxlanmır.
   Yeni fayl yüklənəndə metadata (VT + rəy) sıfırlanır.

### Fayl rəyi (müəllim → kursant)
- Müəllim cədvəlində hər faylın yanında **✓** (qəbul et) və **✏** (düzəliş istə + qeyd prompt-u).
- Aktiv düyməyə təkrar klik rəyi ləğv edir. Endpoint: `/api/upload-review`.
- Kursant öz kabinetində görür: "⌛ Müəllim hələ baxmayıb" / "✅ Qəbul edildi" /
  "✏️ Düzəliş lazımdır — <qeyd>".
- Müəllim ✕ düyməsi ilə faylı silə də bilir (kursant yenidən yükləyə bilər).

### CORS / CSP
- B2 bucket CORS: `https://sapyor.com`, `https://*.vercel.app`, `http://localhost:8080`
  üçün `s3_put/s3_get/s3_head` (bir dəfə b2_update_bucket ilə qurulub).
- `vercel.json` CSP: `connect-src`-də `https://*.backblazeb2.com`,
  `frame-src`-də `https://view.officeapps.live.com`.

### Tutum
- Pulsuz plan 10 GB. 200 kursant × ~20 MB ≈ 4 GB. Semestr sonunda köhnə faylları silmək olar.

---

## 19. Ehtiyat nüsxə (backup) sistemi

- **Avtomatik:** Vercel Cron hər gecə 01:00 UTC → `GET /api/backup`
  (cron istəyi `User-Agent: vercel-cron/*` ilə tanınır; əl ilə çağırışda müəllim tokeni lazımdır).
- Nüsxə: bütün db JSON kimi → B2 `{prefix}backups/db-YYYY-MM-DD.json`.
  31 gün əvvəlki nüsxə hər dəfə avtomatik silinir (yer: ~200KB × 31 ≈ 6MB — cüzi).
- **Yalnız bazanı nüsxələyir** — kursant faylları onsuz da B2-dədir, təkrarlanmır.
- **Bərpa:** müəllim panelində "Ehtiyat nüsxə" kartı → tarix seç → "Bu tarixə qayıt"
  (ikiqat təsdiq). Bərpadan ƏVVƏL cari vəziyyət `backups/pre-restore-<ts>.json`-a yazılır —
  yəni bərpanın özü də geri qaytarıla biləndir.
- Kod: `api/_backup.py` (`run_backup`, `read_backup`, `save_prerestore`).

---

## 20. Son tarix geri sayımı

- Kursant kabinetindəki deadline bannerində tarixin yanında nişan: `deadlineCountdown()`
  mətndən `DD.MM.YYYY` çıxarır → "N gün qaldı".
- Rənglər: >7 gün yaşıl, 3-7 narıncı, ≤3 qırmızı (yanıb-sönən), "bu gün son gündür!",
  keçibsə "vaxt keçib". Tarix parse olunmasa nişan sadəcə göstərilmir (banner qalır).
```

---

## 21. Semestr sonu arxivi

- **UI:** Parametrlər → "Arxiv — keçmiş semestrlər" kartı. "Cari semestri arxivlə" düyməsi bütün
  taqımların cari nəticələrini (`studentTotals()`: manual > canlı > statik kollokvium, sərbəst/dəftər,
  imtahan) `POST /api/arxiv-save`-ə göndərir; iki təsdiq: (1) arxivə yaz, (2) cari balları/seçimləri
  təmizlə (istəyə görə, 3-cü təsdiqlə). "Arxivə bax" — semestr tabları → taqım tabları → cədvəl;
  dinamik girişlər "Bu arxivi sil" ilə silinir, statik 2024 silinmir.
- **Saxlanma:** `db["arxiv"]` (Redis, gecə nüsxəsinə daxildir), ən çoxu 30 giriş. Statik 2024
  (`api/_arxiv.py` → `ARXIV_IMTAHAN`) eyni formata çevrilib siyahının sonunda göstərilir.
- **Firebase-ə toxunulmur:** kollokvium sessiyaları qrup açarı ilə (`K1_YT_23A1`) saxlanır; yeni semestrdə
  müəllim yeni kollokvium keçirəndə üstünə yazılır. Arxiv snapshot-u dəyərləri artıq saxladığı üçün
  bu, arxivə təsir etmir.
