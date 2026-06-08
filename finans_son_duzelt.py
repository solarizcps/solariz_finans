#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Nakit Ihtiyaci kredi duzeltmesi - Python prefix matching
# Calistir: python "D:\Firma_Ozel\adem\solariz finans\finans_son_duzelt.py"

import sqlite3, os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, 'finans.db')

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

print("Taksitler yukleniyor...")
tum = c.execute("SELECT id, aciklama, tutar FROM odemeler WHERE tip='taksit'").fetchall()
print(f"Toplam taksit: {len(tum)}")

# Nakit gruplarini Python ile ayir
nakit1 = [r for r in tum if r[1].startswith('Nakit ') and ' - ' not in r[1]]
nakit2 = [r for r in tum if r[1].startswith('Nakit ') and ' - 2 ' in r[1]]
nakit3 = [r for r in tum if r[1].startswith('Nakit ') and ' - 3 ' in r[1]]
nakit4 = [r for r in tum if r[1].startswith('Nakit ') and ' - 4 ' in r[1]]

print(f"Nakit 1 : {len(nakit1)} taksit = {sum(r[2] for r in nakit1):.0f} TL")
print(f"Nakit -2: {len(nakit2)} taksit = {sum(r[2] for r in nakit2):.0f} TL")
print(f"Nakit -3: {len(nakit3)} taksit = {sum(r[2] for r in nakit3):.0f} TL")
print(f"Nakit -4: {len(nakit4)} taksit = {sum(r[2] for r in nakit4):.0f} TL")

c.execute("UPDATE krediler SET toplam=? WHERE ad='Nakit \u0130htiyac\u0131' AND banka='Kuveytturk'",
    (sum(r[2] for r in nakit1),))
c.execute("UPDATE krediler SET toplam=? WHERE ad='Nakit \u0130htiyac\u0131 - 2'",
    (sum(r[2] for r in nakit2),))
c.execute("UPDATE krediler SET toplam=? WHERE ad='Nakit \u0130htiyac\u0131 - 3'",
    (sum(r[2] for r in nakit3),))
c.execute("UPDATE krediler SET toplam=? WHERE ad='Nakit \u0130htiyac\u0131 - 4'",
    (sum(r[2] for r in nakit4),))

conn.commit()

print("\nGuncel kredi listesi (Python ile taksit sayimi):")
krediler = c.execute("SELECT ad, banka, toplam FROM krediler ORDER BY banka, ad").fetchall()
for k in krediler:
    tak = [r for r in tum if r[1].lower().startswith(k[0].lower() + ' ')]
    print(f"  {k[0][:35]:35} | {k[1]:15} | {k[2]:12.0f} | {len(tak)} taksit")

conn.close()
input("\nCikmak icin Enter'a basin...")
