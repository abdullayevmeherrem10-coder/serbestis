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
