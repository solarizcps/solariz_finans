#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Krediler ve taksitleri temizleyip yeniden yukler
# Calistir: python "D:\Firma_Ozel\adem\solariz finans\finans_kredi_reimport.py"

import pandas as pd, sqlite3, uuid, re, os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, 'finans.db')
XLSX_PATH = os.path.join(BASE_DIR, 'Genel Durum 20.02.2026.xlsx')

def gid(): return str(uuid.uuid4())[:10]
def fnum(v):
    try:
        import math; f=float(v); return 0 if math.isnan(f) else round(f,2)
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

NOW = datetime.now().isoformat()

print(f"Excel okunuyor: {XLSX_PATH}")
xl = pd.ExcelFile(XLSX_PATH)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Mevcut kredileri ve taksitleri sil
print("Eski kredi ve taksit verileri temizleniyor...")
c.execute("DELETE FROM krediler")
c.execute("DELETE FROM odemeler WHERE tip='taksit'")
conn.commit()

kredi_map = {}  # (ad, banka) -> kredi_id

def get_or_create_kredi(ad, banka, toplam=0, odenen=0, not_=''):
    key = (ad.strip(), banka.strip())
    if key not in kredi_map:
        kid = gid()
        kredi_map[key] = kid
        c.execute('''INSERT INTO krediler
            (id,entity,ad,tip,toplam,taksit,kalan_taksit,gun,faiz,banka,baslangic,not_,kaydeden,kayit_tarihi)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (kid,'solariz',ad,'kobi',toplam,0,0,'','',banka,'',not_,'Excel Aktarım',NOW))
    elif toplam > 0:
        # Toplam güncelle
        mevcut = c.execute("SELECT toplam FROM krediler WHERE id=?", (kredi_map[key],)).fetchone()
        if mevcut and mevcut[0] == 0:
            c.execute("UPDATE krediler SET toplam=? WHERE id=?", (toplam, kredi_map[key]))
    return kredi_map[key]

taksit_count = 0
kredi_count = 0

# ================================================================
# BANKA EŞLEŞTİRME — Özet kredi adı → Gerçek taksit açıklaması
# ================================================================
# Krediler(1) özet adları ile taksit açıklamaları farklı olabilir
# Doğru eşleştirme:
ozet_eslesme = {
    'Araç Alım':                          ('Yeni Ticari Araç', 'Kuveytturk'),
    'Esem Işık Alımı':                    ('Işık',             'Kuveytturk'),  # Esem Işık = 5-6. taksit
    'Finas-iga Kredi':                    ('İga Kredi',        'Finansbank'),
    'Nexgen Hmd':                         ('Ticari Kredi',     'Kuveytturk'),
    'Lc-W ışık Alımı':                    ('Işık',             'Kuveytturk'),  # LC-W = 1-9. taksit
    'Unicorn Patch':                      ('Unicorn Patch + Haribo Patch', 'Kuveytturk'),
    'Runix Işık':                         ('Runix Işık',       'Kuveytturk'),
    'UGG 45000 Usd Kredi':               ('UGG 45000 Usd Kredi', 'Kuveytturk'),
    'UGG Kuveyt Şahin tb 100.000$ kullanımın kredisi': ('UGG Kuveyt Şahin tb kredisi', 'Kuveytturk'),
    'UGG Kuveyt Şahin tb kredisi':       ('UGG Kuveyt Şahin tb kredisi', 'Kuveyt Şahin tb'),
    'ugg sayası için çekilen kredi':     ('ugg sayası için çekilen kredi', 'Kuveyt Şahin tb'),
    'KGF  Nakit İhtiyacı':              ('KGF  Nakit İhtiyacı', 'Denizbank'),
    'Patch - ışık - Kalıp':             ('Patch - ışık - Kalıp', 'Vakıf Katılım'),
    'Kgf Kredisi':                       ('Kgf Kredisi', 'TEB Bankası'),
}

# ================================================================
# KREDİLER (1) — Özet satırları
# ================================================================
df_k1 = pd.read_excel(xl, sheet_name='Krediler', header=None)
print("Krediler(1) özet...")
for i in range(2, 14):
    row = df_k1.iloc[i]
    firma = str(row[0]).strip() if pd.notna(row[0]) else ''
    ad    = str(row[2]).strip() if pd.notna(row[2]) else ''
    toplam= fnum(row[5])
    odenen= fnum(row[6])
    if not ad or ad in ('nan','Kredi Adı') or toplam == 0: continue
    if 'Firma' in firma and len(firma) < 10: continue

    # Eşleştirme varsa gerçek banka ve ad ile kaydet
    if ad in ozet_eslesme:
        gercek_ad, banka = ozet_eslesme[ad]
        get_or_create_kredi(gercek_ad, banka, toplam, odenen)
    else:
        get_or_create_kredi(ad, 'Kuveytturk', toplam, odenen)
    kredi_count += 1

# ================================================================
# KREDİLER (1) — Taksit detayları
# ================================================================
print("Krediler(1) taksitler...")
for i in range(19, len(df_k1)):
    row = df_k1.iloc[i]
    firma = str(row[0]).strip() if pd.notna(row[0]) else ''
    tno   = str(row[1]).strip() if pd.notna(row[1]) else ''
    tarih = fdate(row[2])
    acik  = str(row[3]).strip() if pd.notna(row[3]) else ''
    banka = str(row[4]).strip() if pd.notna(row[4]) else 'Kuveytturk'
    tutar = fnum(row[5]); odeme = fnum(row[6]); kalan_t = fnum(row[7])
    if not acik or acik in ('nan','Açıklama') or not tarih or tutar == 0: continue
    if firma == 'Firma' and tno == 'Taksit': continue
    if not banka or banka == 'nan': banka = 'Kuveytturk'

    kid = get_or_create_kredi(acik, banka)
    durum = 'odendi' if kalan_t == 0 and odeme > 0 else 'bekliyor'
    if durum == 'bekliyor' and tarih < '2026-04-11': durum = 'gecikti'

    aciklama = f"{acik} {tno}".strip()
    c.execute('''INSERT OR IGNORE INTO odemeler
        (id,entity,aciklama,tip,tutar,para,vade,odeme_tarihi,durum,tekrar,not_,kaydeden,kayit_tarihi)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (gid(),'solariz',aciklama,'taksit',tutar,'TL',tarih,
         tarih if durum=='odendi' else '',durum,'tek',banka,'Excel Aktarım',NOW))
    taksit_count += 1

# ================================================================
# KREDİLER (2) — Özet satırları
# ================================================================
df_k2 = pd.read_excel(xl, sheet_name='Krediler (2)', header=None)
print("Krediler(2) özet...")
for i in range(2, 9):
    row = df_k2.iloc[i]
    ad     = str(row[2]).strip() if pd.notna(row[2]) else ''
    toplam = fnum(row[6]); odenen = fnum(row[7])
    if not ad or ad == 'nan' or toplam == 0: continue
    if ad in ozet_eslesme:
        gercek_ad, banka = ozet_eslesme[ad]
        get_or_create_kredi(gercek_ad, banka, toplam, odenen)
    else:
        get_or_create_kredi(ad, 'Kuveytturk', toplam, odenen)

# ================================================================
# KREDİLER (2) — Taksit detayları
# ================================================================
print("Krediler(2) taksitler...")
for i in range(19, len(df_k2)):
    row = df_k2.iloc[i]
    firma = str(row[0]).strip() if pd.notna(row[0]) else ''
    tno   = str(row[1]).strip() if pd.notna(row[1]) else ''
    tarih = fdate(row[2])
    acik  = str(row[3]).strip() if pd.notna(row[3]) else ''
    banka = str(row[4]).strip() if pd.notna(row[4]) else 'Kuveytturk'
    tutar = fnum(row[5]); odeme = fnum(row[6]); kalan_t = fnum(row[7])
    if not acik or acik in ('nan','Açıklama') or not tarih or tutar == 0: continue
    if firma == 'Firma' and tno == 'Taksit': continue
    if not banka or banka == 'nan': banka = 'Kuveytturk'

    kid = get_or_create_kredi(acik, banka)
    durum = 'odendi' if kalan_t == 0 and odeme > 0 else 'bekliyor'
    if durum == 'bekliyor' and tarih < '2026-04-11': durum = 'gecikti'

    aciklama = f"{acik} {tno}".strip()
    c.execute('''INSERT OR IGNORE INTO odemeler
        (id,entity,aciklama,tip,tutar,para,vade,odeme_tarihi,durum,tekrar,not_,kaydeden,kayit_tarihi)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (gid(),'solariz',aciklama,'taksit',tutar,'TL',tarih,
         tarih if durum=='odendi' else '',durum,'tek',banka,'Excel Aktarım',NOW))
    taksit_count += 1

# Kredi toplamlarını taksitlerden hesapla (toplam=0 olanlar)
print("Toplamlar hesaplaniyor...")
for (ad, banka), kid in kredi_map.items():
    row = c.execute("SELECT toplam FROM krediler WHERE id=?", (kid,)).fetchone()
    if row and row[0] == 0:
        taks = c.execute("""SELECT SUM(tutar), SUM(CASE WHEN durum='odendi' THEN tutar ELSE 0 END)
                            FROM odemeler WHERE tip='taksit' AND aciklama LIKE ?""",
                        (f"{ad}%",)).fetchone()
        if taks and taks[0]:
            c.execute("UPDATE krediler SET toplam=? WHERE id=?", (taks[0], kid))

conn.commit()

# Özet
print("\n" + "="*50)
print("  KREDİ YENİDEN YÜKLEMESİ TAMAMLANDI")
print(f"  Kredi  : {len(kredi_map)}")
print(f"  Taksit : {taksit_count}")
print("\n  Krediler:")
for row in c.execute("SELECT ad, banka, toplam FROM krediler ORDER BY banka, ad").fetchall():
    taksit_say = c.execute("SELECT COUNT(*) FROM odemeler WHERE tip='taksit' AND aciklama LIKE ?",
                           (f"{row[0]}%",)).fetchone()[0]
    print(f"    {row[0][:35]:35} | {row[1]:15} | {row[2]:12.0f} | {taksit_say} taksit")
print("="*50)
conn.close()
input("\nCikmak icin Enter'a basin...")
