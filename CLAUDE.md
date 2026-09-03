# sapyor.com — Claude üçün qısa bələdçi

FHN Akademiyası Hərbi Kafedrası üçün tədris platforması. Canlı: https://sapyor.com
Dil: Azərbaycan dili (UI, şərhlər, cavablar). İstifadəçi ilə azərbaycanca danış.

Ətraflı sənəd: `AI_GUIDE.md`. Onu bütöv oxuma — yalnız tapşırığa aid bölməni oxu
(bölmə xəritəsi ən aşağıdadır).

## Texnologiya
- Frontend: tək-fayllı HTML + inline CSS + vanilla JS (framework yoxdur)
- Backend canlı: Flask `api/index.py` (Vercel Serverless) · lokal: `server.py` (http.server, 8080)
- Verilənlər canlı: Upstash Redis (REST) · lokal: `database.json` — eyni sxem, SİNXRON DEYİL
- Kollokvium DB: Firebase RTDB (ayrı layihə) · Fayl anbarı: Backblaze B2 (private bucket)
- Virus yoxlanışı: VirusTotal v3 · Sənəd baxışı: Office Online iframe
- Hostinq: Vercel, `main` budağından avto-deploy · Edge gate: `middleware.js` · CSP: `vercel.json`

## Fayl strukturu
```
index.html / public/index.html          Əsas SPA — lokal / deploy nüsxəsi (EYNİ olmalıdır)
kitab.html / public/kitab.html          Kitab oxuyucusu — lokal / deploy
Kollokvium/index.html / public/kollokvium/index.html   Kollokvium tətbiqi — lokal / deploy
api/index.py        Flask — BÜTÜN endpointlər (canlı)
api/_credentials.py Girişlər {ID: {hash, name, team|role}} (SHA-256)
api/_results.py     Statik kollokvium/mənimsəmə/imtahan nəticələri
api/_roster.py      Taqım/kursant idarəetmə
api/_subjects.py    Sərbəst iş fənnləri (cari fənn = semestr parametri): s1 (2 iş) / s2 (1 mövzu), seçim məntiqi
api/_fbauth.py      Firebase service-account token
api/_b2.py          B2 SigV4 imzalama (stdlib), key_prefix() → lokalda "dev/"
api/_uploads.py     Fayl yükləmə: url/confirm/link/delete/review + VT
api/_vt.py          VirusTotal
api/_backup.py      Gündəlik B2 nüsxə (cron 01:00 UTC → /api/backup)
server.py           Lokal dev server (api/index.py-ın sadə ekvivalenti)
```
Gitignore-da (heç vaxt commit etmə): `kabinet_girisleri.txt`, `admin_secret.txt`,
`firebase_secret.txt`, `firebase_service_account.json`, `b2_config.json`, `vt_secret.txt`.

## KRİTİK QAYDALAR (pozulsa sistem sınır)
1. **İki nüsxə sinxron:** `public/index.html` dəyişəndə `cp public/index.html index.html`.
   Eyni qayda kitab və kollokvium üçün. Vercel `public/`-dən, lokal server kökdən verir.
2. **Backend = iki yer:** yeni endpoint həm `api/index.py`, həm `server.py`-a yazılır.
   Müəllim əməliyyatıdırsa `role != teacher → 401` yoxlaması qoy.
3. **İstifadəçi mətni innerHTML-ə → `esc()`** (kursant/taqım/iş adı, qeydlər). XSS.
4. **Bazalar ayrıdır:** lokalda yazılan ballar/seçimlər canlıya keçmir. Real dəyişiklik
   sapyor.com-da edilir.
5. **B2 bucket paylaşılır:** lokal `b2_config.json` `"prefix": "dev/"` verir. Lokal test
   təmizliyi YALNIZ `dev/` açarlarına toxunmalıdır (2026-07-20-də canlı fayllar silinmişdi).
   Silinmiş versiyalar B2-də 7 gün qalır (`b2_copy_file` ilə bərpa).
6. **Firebase-ə birbaşa yazma yox** — həmişə `/api/kollok-write` proxy-dən.
7. **Yeni xarici resurs (CDN, font, API)** → `vercel.json` CSP-yə mənbə əlavə et.
8. **Push-dan əvvəl `git fetch origin`** — lokal repo geri qala bilər, üzərinə yazma.
9. Sirləri (şifrə, açar, JSON) heç vaxt commit etmə.
10. **C diskinə heç nə yazma.** Müvəqqəti fayl, skript, skrinşot, brauzer profili, klon — hamısı
    D:/claude-tmp/sapyor/ qovluğuna (sistem scratchpad-i C-də olsa belə istifadə etmə). Layihə
    qovluğunda müvəqqəti fayl (məs. _preview_*.html) yaradılsa iş bitəndə sil.

## Lokal işə salma
```bash
python server.py        # http://localhost:8080/  (database.json istifadə edir)
```

## Tez-tez görülən tapşırıqlar
- UI dəyişikliyi: `public/index.html` → sonra kökə kopyala.
- Statik nəticə: `api/_results.py`.
- Şifrə yeniləmə: müəllim panelindən (🔑) → bazada `cred_overrides`; `_credentials.py`-a toxunma.
- Deploy: `git push origin main` → Vercel 1-2 dəq sonra canlıdır.

## Dizayn
- Palitra: adaçayı-yaşıl `#455f51` / `#8fa69b` / `#6b8f7b`, krem-yaşıl gradient fon, Inter şrifti.
- Light default, dark `html[data-theme="dark"]` ilə. Hardcoded ağ/tünd rəng YAZMA —
  `--surface-*`, `--text`, `--text-muted`, `--accent-ink`, `--card-border`, `--bg-body` işlət.

## AI_GUIDE.md bölmə xəritəsi (lazım olanda oxu)
| Mövzu | Bölmə |
|---|---|
| Autentifikasiya, token, köməkçi funksiyalar | §5 |
| API endpointləri (tam siyahı) | §6 |
| Verilənlər sxemi, roster_version, statik nəticələr | §7 |
| Mənimsəmə balı / imtahan qiyməti düsturu | §8 |
| Roster idarəetmə (`_roster.py`) | §9 |
| Kollokvium ↔ Firebase, fənn üzrə suallar (questionsS2K1..3) və açarlar | §10 |
| Frontend axını (`index.html` daxili) | §11 |
| Təhlükəsizlik modeli | §12 |
| Vercel mühit dəyişənləri | §13 |
| Fayl təhvili (B2 + Office viewer + VT), CORS/CSP | §18 |
| Backup sistemi | §19 |
| Son tarix geri sayımı | §20 |
| Semestr sonu arxivi | §21 |
| Sərbəst iş fənnləri (subject_id, work_subjects, S2_TOPICS) | §22 |
