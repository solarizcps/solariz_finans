#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Kredi duzeltme scripti - duplike ve yanlis kayitlari duzeltir
# Calistir: python "D:\Firma_Ozel\adem\solariz finans\finans_kredi_duzelt.py"

import sqlite3, os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, 'finans.db')

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

print("Kredi kayitlari duzeltiliyor...\n")

# 1. Nakit Ihtiyaci - taksitleri duzelt
# Nakit Ihtiyaci 1.Taksit, 2.Taksit vs. sadece "Nakit Ihtiyaci " ile baslayanlar
# -2, -3, -4 olanlari harici tut
print("Nakit Ihtiyaci duzeltiliyor...")
c.execute("""UPDATE odemeler SET tip='taksit_nakit1'
    WHERE tip='taksit' AND aciklama LIKE 'Nakit %tiyac_ %.Taksit'
    AND aciklama NOT LIKE 'Nakit %tiyac_ - %'""")

# Simdi sadece "Nakit Ihtiyaci %.Taksit" ve "Nakit Ihtiyaci - 2 %.Taksit" vs. ayir
# Oncelikle tum nakit taksitlerini goster
rows = c.execute("""SELECT id, aciklama, vade, durum FROM odemeler
    WHERE aciklama LIKE 'Nakit %' AND (tip='taksit' OR tip='taksit_nakit1')
    ORDER BY aciklama, vade""").fetchall()
print(f"  Nakit taksit sayisi: {len(rows)}")
for r in rows[:5]: print(f"    {r[1][:40]:40} | {r[2]}")

# Geri al - tip duzeltmesi
c.execute("UPDATE odemeler SET tip='taksit' WHERE tip='taksit_nakit1'")

# 2. Nakit Ihtiyaci kredi kaydi - toplami duzelt
# Nakit Ihtiyaci = 9 taksit x 330.000 = 2.970.000
nakit_taksitler = c.execute("""SELECT COUNT(*), SUM(tutar) FROM odemeler
    WHERE tip='taksit' AND aciklama LIKE 'Nakit %tiyac_ %.Taksit'
    AND aciklama NOT LIKE 'Nakit %tiyac_ - %'""").fetchone()
print(f"\nNakit Ihtiyaci gercek taksit: {nakit_taksitler}")

nakit_toplam = nakit_taksitler[1] or 0
c.execute("""UPDATE krediler SET toplam=? WHERE ad='Nakit İhtiyacı' AND banka='Kuveytturk'""",
    (nakit_toplam,))

# Nakit -2,-3,-4 toplamlarini da duzelt
for suffix in [' - 2', ' - 3', ' - 4']:
    row = c.execute("""SELECT COUNT(*), SUM(tutar) FROM odemeler
        WHERE tip='taksit' AND aciklama LIKE ?""",
        (f'Nakit %tiyac%{suffix} %.Taksit',)).fetchone()
    if row and row[1]:
        c.execute("UPDATE krediler SET toplam=? WHERE ad LIKE ? AND banka='Kuveytturk'",
            (row[1], f'Nakit İhtiyacı{suffix}'))
        print(f"  Nakit{suffix}: {row[0]} taksit, toplam {row[1]:.0f}")

# 3. Duplike UGG Kuveyt kayitlarini temizle
# Kuveyt Sahin tb kredi (fazladan) ve Kuveytturk ugg kayitlarini sil
print("\nDuplike UGG kayitlari temizleniyor...")
# Hangi kayitlar var?
ugg_krediler = c.execute("""SELECT id, ad, banka, toplam FROM krediler
    WHERE ad LIKE 'UGG Kuveyt%' OR ad LIKE 'ugg sayası%'
    ORDER BY ad, banka""").fetchall()
print(f"  Mevcut UGG krediler: {len(ugg_krediler)}")
for k in ugg_krediler:
    taksit_say = c.execute("SELECT COUNT(*) FROM odemeler WHERE tip='taksit' AND aciklama LIKE ?",
                           (f"{k[1]}%",)).fetchone()[0]
    print(f"    {k[1][:35]:35} | {k[2]:20} | {k[3]:12.0f} | {taksit_say} taksit")

# Kuveyt Sahin tb kredi (4. karakter farki) - bunlari sil
c.execute("""DELETE FROM krediler WHERE banka LIKE 'Kuveyt Şahin tb kre%'""")
print("  'Kuveyt Sahin tb kre*' banka kayitlari silindi")

# Kuveytturk'teki UGG Kuveyt Sahin tb kredisi (8 taksit olan) - bu 100.000$ ile ayni
# Farkli ad var zaten (UGG Kuveyt Sahin tb 100.000$...) - sadece tekrar kaydi sil
c.execute("""DELETE FROM krediler
    WHERE ad='UGG Kuveyt Şahin tb kredisi' AND banka='Kuveytturk'""")
print("  Duplike Kuveytturk UGG kredisi silindi")

# 4. Isik kredisini ayir - Esem Isik ve LC-W Isik
# Esem Isik Alimi = sadece 5. ve 6. taksit (Esem=214742, LC-W=468967 veya 268238)
print("\nIsik kredileri ayristiriliyor...")
isik_taksitler = c.execute("""SELECT aciklama, vade, tutar FROM odemeler
    WHERE tip='taksit' AND aciklama LIKE 'Işık %'
    ORDER BY vade""").fetchall()
print(f"  Isik taksit sayisi: {len(isik_taksitler)}")

# Mevcut Isik kredi kaydini guncelle
c.execute("""UPDATE krediler SET toplam=(
    SELECT SUM(tutar) FROM odemeler WHERE tip='taksit' AND aciklama LIKE 'Işık %')
    WHERE ad='Işık' AND banka='Kuveytturk'""")

conn.commit()

# SONUC
print("\n" + "="*55)
print("  DUZELTME TAMAMLANDI")
print("  Guncel kredi listesi:")
for row in c.execute("SELECT ad, banka, toplam FROM krediler ORDER BY banka, ad").fetchall():
    taksit_say = c.execute("SELECT COUNT(*) FROM odemeler WHERE tip='taksit' AND aciklama LIKE ?",
                           (f"{row[0]}%",)).fetchone()[0]
    print(f"    {row[0][:35]:35} | {row[1]:20} | {row[2]:12.0f} | {taksit_say} taksit")
print("="*55)

conn.close()
input("\nCikmak icin Enter'a basin...")
