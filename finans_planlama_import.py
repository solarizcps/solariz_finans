#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Odeme Tablo -> planlama tablosuna import
# Calistir: python "D:\Firma_Ozel\adem\solariz finans\finans_planlama_import.py"

import pandas as pd, sqlite3, uuid, re, os, math
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, 'finans.db')
XLSX_PATH = os.path.join(BASE_DIR, 'Genel Durum 20.02.2026.xlsx')

def gid(): return str(uuid.uuid4())[:10]
def fnum(v):
    try: f=float(v); return 0 if math.isnan(f) else round(f,2)
    except: return 0
def fdate(v):
    try:
        if v is None: return None
        if hasattr(v,'strftime') and str(v)!='NaT': return v.strftime('%Y-%m-%d')
        s=str(v).strip()
        if s in ('nan','NaT','None',''): return None
        m=re.search(r'(\d{4}-\d{2}-\d{2})',s)
        return m.group(1) if m else None
    except: return None

# Birim → kategori eşleştirme
def birim_to_kategori(birim):
    b = birim.lower().strip()
    if b in ('kasa','kasa','nakit tahsilat','cari tahsilat','cek tahsilat','çek tahsilat'): return 'gelir'
    if b in ('maas','maas odeme','maaş ödeme','personel','bonus'): return 'maas'
    if b in ('kredi','kredi karti','k - kart','kart','şahsi kredi','kuveyturk'): return 'kredi'
    if b in ('kira'): return 'kira'
    if b in ('vergi','kdv','sgk','ssgk','bagkur','devlet','gumruk','belediye','ruhsat'): return 'vergi'
    if b in ('fatura','elektrik','fabrika'): return 'fatura'
    if b in ('cek','çek','cek tahsilat'): return 'tedarikci'
    if b in ('nakliye','naklue'): return 'nakliye'
    return 'diger'

# Birim → firma tahmini
def birim_to_firma(aciklama, birim):
    a = aciklama.lower()
    if 'nexgen' in a: return 'nexgen'
    if 'pera' in a: return 'pera'
    if 'lcw' in a or 'lc-w' in a or 'lc w' in a: return 'solariz'
    return 'solariz'

NOW = datetime.now().isoformat()

print(f"Excel okunuyor: {XLSX_PATH}")
xl = pd.ExcelFile(XLSX_PATH)
df = pd.read_excel(xl, sheet_name='Ödeme Tablo', header=None)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Mevcut planlama verilerini temizle
mevcut = c.execute("SELECT COUNT(*) FROM planlama").fetchone()[0]
print(f"Mevcut planlama kaydı: {mevcut}")
if mevcut > 0:
    cevap = input("Mevcut planlama verilerini sil ve yeniden yükle? (e/h): ").strip().lower()
    if cevap == 'e':
        c.execute("DELETE FROM planlama")
        conn.commit()
        print("Temizlendi.")
    else:
        print("İptal edildi.")
        conn.close()
        input("Çıkmak için Enter...")
        exit()

gelir_count = 0
gider_count = 0
atla_count = 0

for i in range(3, len(df)):
    row = df.iloc[i]
    tarih  = fdate(row[0])
    birim  = str(row[1]).strip() if pd.notna(row[1]) else ''
    acik   = str(row[2]).strip() if pd.notna(row[2]) else ''
    gelir_t = fnum(row[3])  # ÖDEME sütunu (gelir için)
    gider_t = fnum(row[4])  # TUTARI sütunu (gider için)
    odenen  = fnum(row[5])  # Ödenen Tutar
    not_    = str(row[7]).strip() if pd.notna(row[7]) else ''

    if not tarih or not birim or birim in ('nan','Birim',''):
        atla_count += 1
        continue
    if not acik or acik == 'nan':
        atla_count += 1
        continue

    kategori = birim_to_kategori(birim)
    firma = birim_to_firma(acik, birim)

    if birim.upper() == 'KASA' and gelir_t > 0:
        # Gelir kaydı
        durum = 'odendi' if odenen > 0 or gelir_t > 0 else 'planli'
        c.execute('''INSERT INTO planlama
            (id, firma, kategori, aciklama, tutar, para, tarih, tekrar, durum, kaydeden, kayit_tarihi)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
            (gid(), firma, 'gelir', acik, gelir_t, 'TL', tarih, 'tek', durum, 'Excel Aktarım', NOW))
        gelir_count += 1

    elif gider_t > 0:
        # Gider kaydı
        durum = 'odendi' if odenen >= gider_t * 0.99 else ('planli' if tarih >= '2026-04-11' else 'gecikti')
        c.execute('''INSERT INTO planlama
            (id, firma, kategori, aciklama, tutar, para, tarih, tekrar, durum, kaydeden, kayit_tarihi)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
            (gid(), firma, kategori, acik, gider_t, 'TL', tarih, 'tek', durum, 'Excel Aktarım', NOW))
        gider_count += 1
    else:
        atla_count += 1

conn.commit()

print("\n" + "="*50)
print("  PLANLAMA AKTARIMI TAMAMLANDI")
print(f"  Gelir kaydı : {gelir_count}")
print(f"  Gider kaydı : {gider_count}")
print(f"  Atlanan     : {atla_count}")
print(f"  Toplam      : {gelir_count + gider_count}")

# Yıl/ay bazlı özet
print("\n  Ay bazlı özet:")
rows = c.execute("""
    SELECT substr(tarih,1,7) as ay,
           SUM(CASE WHEN kategori='gelir' THEN tutar ELSE 0 END) as gelir,
           SUM(CASE WHEN kategori!='gelir' THEN tutar ELSE 0 END) as gider
    FROM planlama
    GROUP BY ay ORDER BY ay
""").fetchall()
for r in rows:
    net = r[1] - r[2]
    print(f"    {r[0]} | Gelir: {r[1]:12,.0f} | Gider: {r[2]:12,.0f} | Net: {net:12,.0f}")

print("="*50)
conn.close()
input("\nÇıkmak için Enter'a basın...")
