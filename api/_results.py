# -*- coding: utf-8 -*-
"""Nəticə məlumatları — yalnız autentifikasiyalı /api/cabinet-data vasitəsilə verilir.

2023 qəbul üçün statik nəticə hələ yoxdur — ballar E-Kollokvium (Firebase) və
müəllimin manual düzəlişlərindən gəlir. Semestr nəticələri hazır olanda
"kollok"/"menimseme"/"imtahan" xəritələri buraya doldurulur.
"""
import json

RESULTS = json.loads(r'''{
  "YT 23A1": {
    "team": "YT23A1",
    "kollok": {},
    "menimseme": {},
    "imtahan": {}
  },
  "YT 23A2": {
    "team": "YT23A2",
    "kollok": {},
    "menimseme": {},
    "imtahan": {}
  }
}''')
