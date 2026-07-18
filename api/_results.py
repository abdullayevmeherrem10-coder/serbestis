# -*- coding: utf-8 -*-
"""Nəticə məlumatları — yalnız autentifikasiyalı /api/cabinet-data vasitəsilə verilir."""
import json

RESULTS = json.loads(r'''{
  "YT 24A1": {
    "team": "YTF24A1",
    "kollok": {
      "Abbasov Ramal Ramil oğlu": [
        "5",
        "6",
        "5"
      ],
      "Ağabalayev Oktay Mahmud oğlu": [
        "5",
        "5",
        "9"
      ],
      "Axundzadə Onur Zəki oğlu": [
        "6",
        "8",
        "9"
      ],
      "Allahverdiyev Ümid Elmir oğlu": [
        "8",
        "8",
        "8"
      ],
      "Eldarlı Hüseyn Baba oğlu": [
        "8",
        "7",
        "9"
      ],
      "Ələkbərli Məhəmməd Elmar oğlu": [
        "8",
        "9",
        "8"
      ],
      "Əliyev Anar Alim oğlu": [
        "5",
        "6",
        "5"
      ],
      "Əliyev Vahid Surxay oğlu": [
        "3",
        "5",
        "9"
      ],
      "İsmayılov Nihad Habil oğlu": [
        "4",
        "5",
        "5"
      ],
      "Kərimli Eşqin Niyaməddin oğlu": [
        "5",
        "7",
        "8"
      ],
      "Qardiyev Nicat Elməddin oğlu": [
        "5",
        "6",
        "5"
      ],
      "Qasımov Fateh Taleh oğlu": [
        "5",
        "6",
        "6"
      ],
      "Quliyev Rəvan Soltan oğlu": [
        "5",
        "6",
        "5"
      ],
      "Qurbanov Nicat Amil oğlu": [
        "5",
        "6",
        "7"
      ],
      "Məmmədli Polad Faiq oğlu": [
        "4",
        "5",
        "5"
      ],
      "Məmmədov Bəhman Mehman oğlu": [
        "6",
        "8",
        "6"
      ],
      "Məmmədov Rəşid Rəşad oğlu": [
        "3",
        "5",
        "7"
      ],
      "Rəhimzadə Ramin Səbuhi oğlu": [
        "5",
        "5",
        "6"
      ],
      "Sadıqov Kəmaləddin Seyfəddin oğlu": [
        "8",
        "8",
        "8"
      ],
      "Tağıyev Ziya Zaur oğlu": [
        "5",
        "5",
        "5"
      ],
      "Vəliyev Qalib Cəlil oğlu": [
        "4",
        "5",
        "5"
      ],
      "Yaqubzadə Yaqub Səbuhi oğlu": [
        "5",
        "5",
        "6"
      ],
      "Yusifzadə Mahmud Natiq oğlu": [
        "6",
        "5",
        "6"
      ],
      "Zəkiyev Sadıq Mehman oğlu": [
        "5",
        "6",
        "5"
      ]
    },
    "menimseme": {
      "Abbasov Ramal Ramil oğlu": "31",
      "Ağabalayev Oktay Mahmud oğlu": "39",
      "Axundzadə Onur Zəki oğlu": "43",
      "Allahverdiyev Ümid Elmir oğlu": "44",
      "Eldarlı Hüseyn Baba oğlu": "44",
      "Ələkbərli Məhəmməd Elmar oğlu": "45",
      "Əliyev Anar Alim oğlu": "29",
      "Əliyev Vahid Surxay oğlu": "29",
      "İsmayılov Nihad Habil oğlu": "28",
      "Kərimli Eşqin Niyaməddin oğlu": "39",
      "Qardiyev Nicat Elməddin oğlu": "32",
      "Qasımov Fateh Taleh oğlu": "31",
      "Quliyev Rəvan Soltan oğlu": "31",
      "Qurbanov Nicat Amil oğlu": "37",
      "Məmmədli Polad Faiq oğlu": "29",
      "Məmmədov Bəhman Mehman oğlu": "37",
      "Məmmədov Rəşid Rəşad oğlu": "33",
      "Rəhimzadə Ramin Səbuhi oğlu": "31",
      "Sadıqov Kəmaləddin Seyfəddin oğlu": "44",
      "Tağıyev Ziya Zaur oğlu": "28",
      "Vəliyev Qalib Cəlil oğlu": "27",
      "Yaqubzadə Yaqub Səbuhi oğlu": "34",
      "Yusifzadə Mahmud Natiq oğlu": "31",
      "Zəkiyev Sadıq Mehman oğlu": "29"
    },
    "imtahan": {
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
    }
  },
  "YT 24A2": {
    "team": "YTF24A2",
    "kollok": {
      "Abdurahmanov Ziya Valeh oğlu": [
        "5",
        "6",
        "5"
      ],
      "Ağazadə Abdullah İntizam oğlu": [
        "5",
        "5",
        "5"
      ],
      "Alıyev Azin Yolçu oğlu": [
        "5",
        "5",
        "5"
      ],
      "Baxşıyev Raul Şamo oğlu": [
        "5",
        "5",
        "5"
      ],
      "Bəyişov Arif Neymət oğlu": [
        "8",
        "8",
        "8"
      ],
      "Çingizli İlçin İlham oğlu": [
        "5",
        "5",
        "4"
      ],
      "Davudov Qail Qabil oğlu": [
        "5",
        "5",
        "4"
      ],
      "Əyyubov Fərhad İlqar oğlu": [
        "5",
        "6",
        "5"
      ],
      "Həmidov İsmail Ramiz oğlu": [
        "5",
        "5",
        "5"
      ],
      "Hüseynli Fərid Şaiq oğlu": [
        "7",
        "5",
        "5"
      ],
      "Hüseynov Əbutalib Bəhram oğlu": [
        "6",
        null,
        null
      ],
      "Hüseynov Əli Çingiz oğlu": [
        "8",
        "8",
        "9"
      ],
      "Hüseynov Zaur Bəhruz oğlu": [
        "5",
        "6",
        "6"
      ],
      "Qasımov Əli Taleh oğlu": [
        "8",
        "7",
        "6"
      ],
      "Qənbərov Hüseyn İsaq oğlu": [
        "7",
        "8",
        "8"
      ],
      "Qurbanov Tuncay Turan oğlu": [
        "7",
        "7",
        "8"
      ],
      "Qurbanov Vasif Xeyrəddin oğlu": [
        "7",
        "7",
        "7"
      ],
      "Məmmədli Ənnağı Qalib oğlu": [
        "9",
        "9",
        "9"
      ],
      "Məmmədov Bəyiş Ülkər oğlu": [
        "7",
        "7",
        "7"
      ],
      "Mustafayev Adəm Səyyad oğlu": [
        "5",
        "5",
        "5"
      ],
      "Novruzov Nihat Eyvaz oğlu": [
        "5",
        "5",
        "5"
      ],
      "Səfxanlı İslam Elşən oğlu": [
        "5",
        "5",
        "5"
      ],
      "Şıxıyev Farid Ravid oğlu": [
        "5",
        "5",
        "7"
      ],
      "Vəliyev Cəlal Arzu oğlu": [
        "5",
        "7",
        "5"
      ],
      "Vəliyev Elsevər Eldəniz oğlu": [
        "6",
        "5",
        "4"
      ]
    },
    "menimseme": {
      "Abdurahmanov Ziya Valeh oğlu": "30",
      "Ağazadə Abdullah İntizam oğlu": "28",
      "Alıyev Azin Yolçu oğlu": "32",
      "Baxşıyev Raul Şamo oğlu": "31",
      "Bəyişov Arif Neymət oğlu": "44",
      "Çingizli İlçin İlham oğlu": "30",
      "Davudov Qail Qabil oğlu": "27",
      "Əyyubov Fərhad İlqar oğlu": "30",
      "Həmidov İsmail Ramiz oğlu": "29",
      "Hüseynli Fərid Şaiq oğlu": "31",
      "Hüseynov Əbutalib Bəhram oğlu": "6",
      "Hüseynov Əli Çingiz oğlu": "45",
      "Hüseynov Zaur Bəhruz oğlu": "32",
      "Qasımov Əli Taleh oğlu": "38",
      "Qənbərov Hüseyn İsaq oğlu": "42",
      "Qurbanov Tuncay Turan oğlu": "42",
      "Qurbanov Vasif Xeyrəddin oğlu": "40",
      "Məmmədli Ənnağı Qalib oğlu": "47",
      "Məmmədov Bəyiş Ülkər oğlu": "41",
      "Mustafayev Adəm Səyyad oğlu": "29",
      "Novruzov Nihat Eyvaz oğlu": "30",
      "Səfxanlı İslam Elşən oğlu": "29",
      "Şıxıyev Farid Ravid oğlu": "32",
      "Vəliyev Cəlal Arzu oğlu": "35",
      "Vəliyev Elsevər Eldəniz oğlu": "29"
    },
    "imtahan": {
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
