#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Excel'den finans.db'ye veri aktarım scripti
# Kullanım: python finans_import.py
# Excel dosyası: Genel_Durum_20_02_2026.xlsx (aynı klasörde olmalı)

import pandas as pd
import sqlite3
import json
import re
import uuid
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, 'finans.db')
XLSX_PATH = os.path.join(BASE_DIR, 'Genel Durum 20.02.2026.xlsx')

def gid():
    return str(uuid.uuid4())[:10]

def fdate(v):
    try:
        if v is None: return None
        if hasattr(v, 'strftime') and str(v) != 'NaT': return v.strftime('%Y-%m-%d')
        s = str(v).strip()
        if s in ('nan','NaT','None',''): return None
        m = re.search(r'(\d{4}-\d{2}-\d{2})', s)
        return m.group(1) if m else None
    except: return None

def fnum(v):
    try:
        f = float(v)
        import math
        return round(f, 2) if not math.isnan(f) else 0
    except: return 0

def get_db():
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS odemeler (
        id TEXT PRIMARY KEY, entity TEXT, aciklama TEXT, tip TEXT,
        tutar REAL DEFAULT 0, para TEXT DEFAULT 'TL', vade TEXT,
        odeme_tarihi TEXT, durum TEXT DEFAULT 'bekliyor', tekrar TEXT DEFAULT 'tek',
        not_ TEXT, kaydeden TEXT, kayit_tarihi TEXT, guncelleyen TEXT, guncelleme TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS krediler (
        id TEXT PRIMARY KEY, entity TEXT, ad TEXT, tip TEXT,
        toplam REAL DEFAULT 0, taksit REAL DEFAULT 0, kalan_taksit INTEGER DEFAULT 0,
        gun TEXT, faiz TEXT, banka TEXT, baslangic TEXT, not_ TEXT,
        kaydeden TEXT, kayit_tarihi TEXT, guncelleyen TEXT, guncelleme TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS planlama (
        id TEXT PRIMARY KEY, firma TEXT, kategori TEXT, aciklama TEXT,
        tutar REAL DEFAULT 0, para TEXT DEFAULT 'TL', tarih TEXT,
        tekrar TEXT DEFAULT 'tek', durum TEXT DEFAULT 'planli',
        kaydeden TEXT, kayit_tarihi TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS kullanicilar (
        username TEXT PRIMARY KEY, password TEXT, ad TEXT, rol TEXT DEFAULT 'normal')''')
    c.execute("INSERT OR IGNORE INTO kullanicilar VALUES ('altan','104099','Altan','admin')")
    c.execute("INSERT OR IGNORE INTO kullanicilar VALUES ('adem','f7a6ua61','Adem','admin')")
    conn.commit()
    conn.close()
    print("Veritabani hazir.")

NOW = datetime.now().isoformat()

if not os.path.exists(XLSX_PATH):
    print(f"HATA: Excel dosyası bulunamadı: {XLSX_PATH}")
    print("Excel dosyasını aynı klasöre koyun ve tekrar çalıştırın.")
    input("Çıkmak için Enter'a basın...")
    exit()

print(f"Excel okunuyor: {XLSX_PATH}")
init_db()
xl = pd.ExcelFile(XLSX_PATH)

conn = get_db()
c = conn.cursor()

odeme_count = 0
kredi_count = 0
skip_count = 0

def insert_odeme(entity, aciklama, tip, tutar, para, vade, odeme_tarihi, durum, not_, kaydeden):
    global odeme_count, skip_count
    if not aciklama or tutar == 0: 
        skip_count += 1
        return
    oid = gid()
    # Duplicate kontrolü
    existing = c.execute("SELECT id FROM odemeler WHERE entity=? AND aciklama=? AND vade=? AND tutar=?",
                        (entity, aciklama, vade, tutar)).fetchone()
    if existing:
        skip_count += 1
        return
    c.execute('''INSERT INTO odemeler
        (id,entity,aciklama,tip,tutar,para,vade,odeme_tarihi,durum,tekrar,not_,kaydeden,kayit_tarihi)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (oid, entity, aciklama, tip, tutar, para or 'TL', vade or '',
         odeme_tarihi or '', durum, 'tek', not_ or '', kaydeden, NOW))
    odeme_count += 1

def insert_kredi(entity, ad, tip, toplam, taksit, kalan_taksit, banka, not_):
    global kredi_count
    if not ad or toplam == 0: return
    existing = c.execute("SELECT id FROM krediler WHERE entity=? AND ad=?", (entity, ad)).fetchone()
    if existing: return
    kid = gid()
    c.execute('''INSERT INTO krediler
        (id,entity,ad,tip,toplam,taksit,kalan_taksit,gun,faiz,banka,baslangic,not_,kaydeden,kayit_tarihi)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (kid, entity, ad, tip, toplam, taksit, kalan_taksit,
         '', '', banka or '', '', not_ or '', 'Excel Aktarım', NOW))
    kredi_count += 1

# ──────────────────────────────────────────────
# 1. ALTAN sayfası — şahsi borçlar → Solariz
# ──────────────────────────────────────────────
print("Altan sayfası işleniyor...")
df_a = pd.read_excel(xl, sheet_name='Altan', header=0)
for _, row in df_a.iterrows():
    tarih = fdate(row.iloc[0])
    tip2  = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ''
    isim  = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ''
    not_  = str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else ''
    tip1  = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ''
    tutar = fnum(row.iloc[5])
    kalan = fnum(row.iloc[9]) if len(row) > 9 else 0
    if not isim or not tarih or tutar == 0: continue
    durum = 'odendi' if (not_ == 'Bitti' or kalan == 0) else 'bekliyor'
    if durum == 'bekliyor' and tarih < '2026-04-11': durum = 'gecikti'
    tip = 'kredi' if 'Kredi' in tip2 or 'kart' in tip2.lower() else 'diger'
    insert_odeme('solariz', isim, tip, tutar, 'TL', tarih,
                 tarih if durum=='odendi' else '', durum,
                 f"{tip1} / {not_}".strip(' /'), 'Excel Aktarım')

# ──────────────────────────────────────────────
# 2. KREDİLER sayfası
# ──────────────────────────────────────────────
print("Krediler sayfası işleniyor...")
df_k1 = pd.read_excel(xl, sheet_name='Krediler', header=None)
for i in range(2, 14):
    row = df_k1.iloc[i]
    firma = str(row[0]).strip() if pd.notna(row[0]) else ''
    ad    = str(row[2]).strip() if pd.notna(row[2]) else ''
    toplam= fnum(row[5])
    if firma and ad and toplam > 0 and 'Firma' not in firma and 'nan' not in firma:
        insert_kredi('solariz', ad, 'kobi', toplam, 0, 0, 'Kuveytturk', '')

for i in range(19, len(df_k1)):
    row = df_k1.iloc[i]
    firma = str(row[0]).strip() if pd.notna(row[0]) else ''
    tno   = str(row[1]).strip() if pd.notna(row[1]) else ''
    tarih = fdate(row[2])
    acik  = str(row[3]).strip() if pd.notna(row[3]) else ''
    banka = str(row[4]).strip() if pd.notna(row[4]) else ''
    tutar = fnum(row[5])
    odeme = fnum(row[6])
    kalan = fnum(row[7])
    if not tarih or tutar == 0 or not acik or acik == 'nan': continue
    if firma in ('Firma', 'nan', '') and tno in ('Taksit', 'nan', ''): continue  # sadece başlık satırı atla
    if 'Firma' == firma and 'Taksit' == tno: continue
    durum = 'odendi' if kalan == 0 and odeme > 0 else 'bekliyor'
    if durum == 'bekliyor' and tarih < '2026-04-11': durum = 'gecikti'
    aciklama = (acik + ' ' + tno).strip()
    insert_odeme('solariz', aciklama, 'taksit', tutar, 'TL', tarih,
                 tarih if durum=='odendi' else '', durum, banka, 'Excel Aktarım')

# ──────────────────────────────────────────────
# 3. KREDİLER (2)
# ──────────────────────────────────────────────
print("Krediler (2) sayfası işleniyor...")
df_k2 = pd.read_excel(xl, sheet_name='Krediler (2)', header=None)
for i in range(2, 9):
    row = df_k2.iloc[i]
    ad    = str(row[2]).strip() if pd.notna(row[2]) else ''
    toplam= fnum(row[6])
    if ad and toplam > 0:
        insert_kredi('solariz', ad, 'kobi', toplam, 0, 0, 'Kuveytturk', 'Aktif KGF')

for i in range(19, len(df_k2)):
    row = df_k2.iloc[i]
    firma = str(row[0]).strip() if pd.notna(row[0]) else ''
    tno   = str(row[1]).strip() if pd.notna(row[1]) else ''
    tarih = fdate(row[2])
    acik  = str(row[3]).strip() if pd.notna(row[3]) else ''
    banka = str(row[4]).strip() if pd.notna(row[4]) else ''
    tutar = fnum(row[5])
    odeme = fnum(row[6])
    kalan = fnum(row[7])
    if not tarih or tutar == 0 or not acik or acik == 'nan': continue
    if firma == 'Firma' and tno == 'Taksit': continue  # sadece başlık satırı atla
    durum = 'odendi' if kalan == 0 and odeme > 0 else 'bekliyor'
    if durum == 'bekliyor' and tarih < '2026-04-11': durum = 'gecikti'
    aciklama = (acik + ' ' + tno).strip()
    insert_odeme('solariz', aciklama, 'taksit', tutar, 'TL', tarih,
                 tarih if durum=='odendi' else '', durum, banka, 'Excel Aktarım')

# ──────────────────────────────────────────────
# 4. ÇEKLER
# ──────────────────────────────────────────────
print("Çekler sayfası işleniyor...")
df_cek = pd.read_excel(xl, sheet_name='Çekler', header=None)
for i in range(0, len(df_cek)):
    row = df_cek.iloc[i]
    tarih = fdate(row[1])
    alici = str(row[2]).strip() if pd.notna(row[2]) else ''
    tutar = fnum(row[4])
    odeme = fnum(row[5])
    kalan = fnum(row[6])
    if not tarih or tutar == 0 or not alici or alici == 'nan': continue
    durum = 'odendi' if kalan == 0 and odeme > 0 else 'bekliyor'
    if durum == 'bekliyor' and tarih < '2026-04-11': durum = 'gecikti'
    insert_odeme('solariz', f"Çek: {alici}", 'tedarikci', tutar, 'TL', tarih,
                 tarih if durum=='odendi' else '', durum, 'Çek', 'Excel Aktarım')

# ──────────────────────────────────────────────
# 5. EXTRA
# ──────────────────────────────────────────────
print("Extra sayfası işleniyor...")
df_ex = pd.read_excel(xl, sheet_name='Extra', header=None)
for i in range(2, len(df_ex)):
    row = df_ex.iloc[i]
    firma = str(row[0]).strip() if pd.notna(row[0]) else ''
    tarih = fdate(row[1])
    acik  = str(row[2]).strip() if pd.notna(row[2]) else ''
    tutar = fnum(row[5])
    odenen= fnum(row[6])
    kalan = fnum(row[7])
    if not tarih or tutar == 0 or not acik or acik == 'nan': continue
    entity = 'nexgen' if 'nexgen' in firma.lower() else 'solariz'
    durum = 'odendi' if kalan == 0 and odenen > 0 else 'bekliyor'
    if durum == 'bekliyor' and tarih < '2026-04-11': durum = 'gecikti'
    insert_odeme(entity, acik, 'tedarikci', tutar, 'TL', tarih,
                 tarih if durum=='odendi' else '', durum, '', 'Excel Aktarım')

# ──────────────────────────────────────────────
# 6. ÖDEME TABLO
# ──────────────────────────────────────────────
print("Ödeme Tablo sayfası işleniyor...")
df_ot = pd.read_excel(xl, sheet_name='Ödeme Tablo', header=None)
tip_map = {
    'Kredi':'kredi','Kredi Karti':'kredi','Kredi Kartı':'kredi',
    'Cari Odeme':'tedarikci','Vergi':'vergi','Devlet':'vergi',
    'Maas':'maas','Masraf':'diger','Avans':'diger',
    'Borc':'diger','Cin':'diger','Kmh':'diger','kmh':'diger'
}
for i in range(3, len(df_ot)):
    row = df_ot.iloc[i]
    tarih = fdate(row[0])
    birim = str(row[1]).strip() if pd.notna(row[1]) else ''
    acik  = str(row[2]).strip() if pd.notna(row[2]) else ''
    tutar = fnum(row[4])
    odenen= fnum(row[5])
    if not tarih or not acik or acik=='nan': continue
    if birim.upper() == 'KASA': continue
    if tutar == 0: continue
    durum = 'odendi' if odenen >= tutar and odenen > 0 else 'bekliyor'
    if durum == 'bekliyor' and tarih < '2026-04-11': durum = 'gecikti'
    tip = tip_map.get(birim, 'diger')
    insert_odeme('solariz', acik, tip, tutar, 'TL', tarih,
                 tarih if durum=='odendi' else '', durum, birim, 'Excel Aktarım')

conn.commit()
conn.close()

print()
print("=" * 40)
print(f"  AKTARIM TAMAMLANDI")
print(f"  Eklenen ödeme : {odeme_count}")
print(f"  Eklenen kredi : {kredi_count}")
print(f"  Atlanan kayıt : {skip_count}")
print(f"  Veritabanı    : {DB_PATH}")
print("=" * 40)
input("\nÇıkmak için Enter'a basın...")
