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
| Hostinq | **Vercel** (Hobby plan), `main` budağından avtomatik deploy |
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
├── api/_roster.py          # Taqım/kursant idarəetmə məntiqi (əlavə/redaktə/sil)
├── api/_fbauth.py          # Firebase service-account OAuth token generatoru
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
- `kabinet_girisleri.txt` — açıq şifrələrin paylama siyahısı (yalnız sahibin kompüterində)
- `admin_secret.txt`, `firebase_secret.txt`, `firebase_service_account.json` — sirlər
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

---

## 5. Autentifikasiya və token sistemi

### Giriş məlumatları
- Hər istifadəçinin **ID**-si var (kursant: `Y1-01`, `Y2-05`, `H1-03`, `H2-07`; müəllim: `MUELLIM`).
  - `Y1`=YTF24A1, `Y2`=YTF24A2, `H1`=HFT24A1, `H2`=HFT24A2.
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
- `POST /api/cabinet-deadline` `{name, deadline}` → fərdi son tarix (boş = silmə).
- `POST /api/cabinet-semester` `{semester, subject}` → semestr/fənn adı.
- `POST /api/cabinet-reset` `{name}` → bir kursantın seçimini sıfırla.
- `POST /api/cabinet-reset-all` → bütün seçimləri sıfırla.
- `POST /api/cabinet-roster` `{action, ...}` → taqım/kursant/iş idarəetmə (bax §9).
- `POST /api/kollok-write` `{path, data}` → Firebase-ə yazma proxy-si (bax §10).

### Köhnə admin endpointləri (hələ mövcud, `ADMIN_PASSWORD` ilə qorunur)
- `/api/status`, `/api/admin/*` — köhnə admin panel üçün idi (`admin.html` silinib),
  amma endpointlər qalıb və şifrə + rate-limit ilə qorunur. Yeni funksiya üçün istifadə etmə.

---

## 7. Verilənlər strukturu (`database.json` / Upstash Redis eyni sxem)

```jsonc
{
  "teams": { "YTF24A1": ["Ad Soyad oğlu", ...], "YTF24A2": [...], "HFT24A1": [...], "HFT24A2": [...] },
  "works": ["Sərbəst iş adı 1", ...],          // 50 iş
  "keys":  { "Ad Soyad": "ACAR6" },            // sərbəst iş təsdiq açarları
  "selections": { "Ad Soyad": [4, 7] },        // seçdiyi 2 işin indeksi
  "work_taken_by": { "YTF24A1": { "4": "Ad Soyad" } },  // taqım→{işİndeks: kursant}
  "scores": { "Ad Soyad": { "serbest": 8, "defter": 9 } },  // mənimsəmə komponentləri
  "exam_scores": { "Ad Soyad": 74 },           // müəllimin manual imtahan balı
  "deadlines": { "Ad Soyad": "20 may 2026" },  // fərdi son tarix
  "semester": "2025/2026 yaz semestri",
  "subject": "Hərbi Mühəndis Texnikası",
  "credentials_dyn": { "Y1-25": {hash, name, team} },  // müəllimin əlavə etdiyi kursantlar
  "renames": { "Köhnə Ad": "Yeni Ad" },        // statik nəticələri yeni adla uyğunlaşdırır
  "team_renames": { "Köhnə Taqım": "Yeni Taqım" }
}
```

### Statik nəticələr (`api/_results.py`)
- 2 qrup: `"YT 24A1"`, `"YT 24A2"` (hər biri `team`, `kollok`, `menimseme`, `imtahan`).
- `kollok`: `{ad: ["5","6","5"]}` (K1,K2,K3 balları, 0-10).
- `imtahan`: `{ad: ["74", "C “Yaxşı”"]}` (bal, qiymət).
- **Vacib:** HTML-də cədvəllər BOŞDUR — nəticələr bu fayldan API ilə gəlir.
  Statik nəticəni dəyişmək üçün `_results.py` redaktə olunur.
- `renames`/`team_renames` bu statik məlumatı dinamik ad dəyişmələri ilə uyğunlaşdırır
  (`effective_results(db)` funksiyası tətbiq edir).

---

## 8. Mənimsəmə balı düsturu

**Mənimsəmə = Kollokvium cəmi (maks 30) + Sərbəst iş (maks 10) + Dəftər/İntizam (maks 10) = maks 50**

- **Kollokvium cəmi** = K1+K2+K3 (hərəsi maks 10). Bu ballar E-Kollokvium sistemindən
  (Firebase) canlı gəlir; statik `_results.py` fallback-dır. Canlı bal statiki üstələyir.
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
- `add_student` `{team, name}` — yeni kursant; **avtomatik ID+şifrə+açar** yaradılır,
  cavabda `{id, password}` bir dəfə qaytarılır (şifrə yalnız hash saxlanılır).
- `rename_student` `{name, new}` — bütün strukturlarda (ballar, seçimlər, tarixlər,
  girişlər, statik nəticələr) yayılır, heç nə itmir.
- `delete_student` `{name}` — məlumatları təmizlənir, girişi deaktiv olunur.
- `add_work` / `edit_work` / `delete_work` — iş siyahısı idarəsi.
  - Seçilmiş işi silmək **bloklanır** (əvvəl seçim sıfırlanmalı).
  - İş silinəndə bütün seçim indeksləri avtomatik yenidən hesablanır.

---

## 10. Elektron Kollokvium ↔ Firebase inteqrasiyası

- Kollokvium tətbiqi (`public/kollokvium/index.html`) imtahan nəticələrini
  **Firebase Realtime DB**-yə yazır. Yol formatı: `sessions/K{1|2|3}_{QRUP}` (məs. `K1_YT_24A1`).
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
2. **Kursant kabineti** (`#cabinetView`) — hero panel, KPI kartları, nəticə kartları,
   fərdi deadline banneri, "Sərbəst işlərim", sənəd düymələri.
   - Sərbəst iş seçmək üçün `startSerbestFlow()` → `#appView` (student-mode).
3. **Müəllim paneli** (`#appView.teacher-mode`) — tab naviqasiya + E-Kollokvium banneri:
   - **Sərbəst işlər tab:** idarəetmə paneli (xülasə, kursant cədvəli + fərdi tarixlər +
     sıfırla/redaktə/sil, işlərin bölgüsü, semestr/fənn kartı, "hamısını sıfırla").
   - **Kollokvium/Mənimsəmə/İmtahan tabları:** redaktə olunan cədvəllər (bal inputları).
- Əsas render funksiyaları: `showCabinet()`, `showTeacherApp()`, `buildPersonalCards()`,
  `renderTeacherPanel()`, `renderMenimsemeTable()`, `renderImtahanTable()`, `renderTpStudents()`.
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
- **Şifrələri yeniləmək:** `gen_creds` tipli skript `api/_credentials.py` + `kabinet_girisleri.txt`
  yaradır (ID-lər sabit qalır, şifrələr yenilənir). Köhnə şifrələr keçərsiz olur.
- **Deploy:** `git add ... && git commit && git push origin main` → Vercel avtomatik deploy.
  Yoxlama: ~1-2 dəqiqə sonra sapyor.com.

---

## 16. Dizayn qeydləri

- Palitra: adaçayı-yaşıl `#455f51` / `#8fa69b` / `#6b8f7b`, açıq krem-yaşıl gradient fon.
- İmza elementlər: ofset "back-box" kölgələr, shimmer düymələr, hissəcik (particle) fon animasiyası.
- Şrift: Inter (+ bəzi başlıqlarda Playfair Display).
- Bütün sayt + kitab + kollokvium eyni dizayn dilindədir.

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
```
