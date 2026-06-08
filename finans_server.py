#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Finans Yönetim Konsolu - Backend Server
# Port: 5058

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3, json, os, uuid, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, 'finans.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS odemeler (
        id           TEXT PRIMARY KEY,
        entity       TEXT NOT NULL,
        aciklama     TEXT,
        tip          TEXT,
        tutar        REAL DEFAULT 0,
        para         TEXT DEFAULT 'TL',
        vade         TEXT,
        odeme_tarihi TEXT,
        durum        TEXT DEFAULT 'bekliyor',
        tekrar       TEXT DEFAULT 'tek',
        not_         TEXT,
        kaydeden     TEXT,
        kayit_tarihi TEXT,
        guncelleyen  TEXT,
        guncelleme   TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS krediler (
        id           TEXT PRIMARY KEY,
        entity       TEXT NOT NULL,
        ad           TEXT,
        tip          TEXT,
        toplam       REAL DEFAULT 0,
        taksit       REAL DEFAULT 0,
        kalan_taksit INTEGER DEFAULT 0,
        gun          TEXT,
        faiz         TEXT,
        banka        TEXT,
        baslangic    TEXT,
        not_         TEXT,
        kaydeden     TEXT,
        kayit_tarihi TEXT,
        guncelleyen  TEXT,
        guncelleme   TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS planlama (
        id           TEXT PRIMARY KEY,
        firma        TEXT,
        kategori     TEXT,
        aciklama     TEXT,
        tutar        REAL DEFAULT 0,
        para         TEXT DEFAULT 'TL',
        tarih        TEXT,
        tekrar       TEXT DEFAULT 'tek',
        durum        TEXT DEFAULT 'planli',
        kaydeden     TEXT,
        kayit_tarihi TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS kullanicilar (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        ad       TEXT,
        rol      TEXT DEFAULT 'normal'
    )''')

    # YENİ: Kasa tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS kasa (
        id           TEXT PRIMARY KEY,
        entity       TEXT NOT NULL,
        aciklama     TEXT,
        tutar        REAL DEFAULT 0,
        para         TEXT DEFAULT 'TL',
        tarih        TEXT,
        tip          TEXT DEFAULT 'giris',
        not_         TEXT,
        kaydeden     TEXT,
        kayit_tarihi TEXT
    )''')

    # YENİ: Kur cache tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS kur_cache (
        para    TEXT PRIMARY KEY,
        kur     REAL,
        tarih   TEXT
    )''')

    c.execute("INSERT OR IGNORE INTO kullanicilar VALUES ('altan','104099','Altan','admin')")
    c.execute("INSERT OR IGNORE INTO kullanicilar VALUES ('adem','f7a6ua61','Adem','admin')")

    # Migration: kredi_id alanı (mevcut DB'lerde yoksa ekle)
    try:
        c.execute("ALTER TABLE odemeler ADD COLUMN kredi_id TEXT")
        print("[DB] odemeler.kredi_id sütunu eklendi")
    except Exception:
        pass  # Zaten varsa sessizce geç

    conn.commit()
    conn.close()
    print(f"[DB] Veritabanı hazır: {DB_PATH}")

# ============================================================
# AUTH
# ============================================================

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM kullanicilar WHERE username=? AND password=?",
        (data.get('username','').lower(), data.get('password',''))
    ).fetchone()
    conn.close()
    if user:
        return jsonify({'ok': True, 'ad': user['ad'], 'rol': user['rol'], 'username': user['username']})
    return jsonify({'ok': False, 'mesaj': 'Hatalı kullanıcı adı veya şifre'}), 401

# ============================================================
# DÖVİZ KURLARI — TCMB
# ============================================================

@app.route('/api/kurlar', methods=['GET'])
def get_kurlar():
    try:
        conn = get_db()
        bugun = datetime.now().strftime('%Y-%m-%d')

        # Cache'den bak (bugünkü kur var mı)
        usd = conn.execute("SELECT kur FROM kur_cache WHERE para='USD' AND tarih=?", (bugun,)).fetchone()
        eur = conn.execute("SELECT kur FROM kur_cache WHERE para='EUR' AND tarih=?", (bugun,)).fetchone()
        altin = conn.execute("SELECT kur FROM kur_cache WHERE para='XAU' AND tarih=?", (bugun,)).fetchone()

        if usd and eur:
            conn.close()
            return jsonify({
                'ok': True,
                'USD': usd['kur'],
                'EUR': eur['kur'],
                'XAU': altin['kur'] if altin else 0,
                'tarih': bugun,
                'kaynak': 'cache'
            })

        # TCMB'den çek (HTTP — sunucu HTTPS'e erişemiyor)
        url = 'http://www.tcmb.gov.tr/kurlar/today.xml'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            xml_data = resp.read()

        root = ET.fromstring(xml_data)
        kurlar = {}
        for doviz in root.findall('Currency'):
            kod = doviz.get('Kod', '')
            try:
                satis = float(doviz.find('ForexSelling').text.replace(',','.'))
                kurlar[kod] = satis
            except:
                pass

        usd_kur   = kurlar.get('USD', 0)
        eur_kur   = kurlar.get('EUR', 0)
        altin_kur = kurlar.get('XAU', 0)

        # Cache'e kaydet
        for para, kur in [('USD', usd_kur), ('EUR', eur_kur), ('XAU', altin_kur)]:
            conn.execute("INSERT OR REPLACE INTO kur_cache VALUES (?,?,?)", (para, kur, bugun))
        conn.commit()
        conn.close()

        return jsonify({'ok': True, 'USD': usd_kur, 'EUR': eur_kur, 'XAU': altin_kur, 'tarih': bugun, 'kaynak': 'tcmb'})

    except Exception as e:
        # Cache'deki en son kuru döndür
        try:
            conn2 = get_db()
            usd2  = conn2.execute("SELECT kur, tarih FROM kur_cache WHERE para='USD' ORDER BY tarih DESC LIMIT 1").fetchone()
            eur2  = conn2.execute("SELECT kur FROM kur_cache WHERE para='EUR' ORDER BY tarih DESC LIMIT 1").fetchone()
            conn2.close()
            if usd2:
                return jsonify({'ok': True, 'USD': usd2['kur'], 'EUR': eur2['kur'] if eur2 else 0, 'XAU': 0, 'tarih': usd2['tarih'], 'kaynak': 'cache_eski'})
        except:
            pass
        return jsonify({'ok': False, 'hata': str(e), 'USD': 0, 'EUR': 0, 'XAU': 0})

# ============================================================
# KASA
# ============================================================

@app.route('/api/kasa', methods=['GET'])
def get_kasa():
    entity = request.args.get('entity', '')
    conn = get_db()
    if entity:
        rows = conn.execute(
            "SELECT * FROM kasa WHERE entity=? ORDER BY tarih DESC",
            (entity,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM kasa ORDER BY tarih DESC"
        ).fetchall()
    # Toplam bakiye hesapla
    toplam = conn.execute(
        "SELECT SUM(CASE WHEN tip='giris' THEN tutar ELSE -tutar END) FROM kasa WHERE (? = '' OR entity=?) AND para='TL'",
        (entity, entity)
    ).fetchone()[0] or 0
    conn.close()
    return jsonify({'ok': True, 'hareketler': [dict(r) for r in rows], 'bakiye': toplam})

@app.route('/api/kasa', methods=['POST'])
def add_kasa():
    d = request.json
    kid = str(uuid.uuid4())[:10]
    conn = get_db()
    conn.execute('''INSERT INTO kasa
        (id,entity,aciklama,tutar,para,tarih,tip,not_,kaydeden,kayit_tarihi,banka)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
        (kid, d.get('entity','solariz'), d.get('aciklama'),
         d.get('tutar',0), d.get('para','TL'), d.get('tarih', datetime.now().strftime('%Y-%m-%d')),
         d.get('tip','giris'), d.get('not',''),
         d.get('kaydeden'), datetime.now().isoformat(),
         d.get('banka','') or None))
    conn.commit()
    conn.close()
    return jsonify({'ok': True, 'id': kid})

@app.route('/api/kasa/<kid>', methods=['DELETE'])
def delete_kasa(kid):
    conn = get_db()
    conn.execute("DELETE FROM kasa WHERE id=?", (kid,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

# ============================================================
# ÖDEMELER
# ============================================================

@app.route('/api/odemeler', methods=['GET'])
def get_odemeler():
    entity = request.args.get('entity', '')
    conn = get_db()
    if entity:
        rows = conn.execute("SELECT * FROM odemeler WHERE entity=? ORDER BY vade", (entity,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM odemeler ORDER BY entity, vade").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/odemeler', methods=['POST'])
def add_odeme():
    d = request.json
    oid = d.get('id') or str(uuid.uuid4())[:10]
    conn = get_db()
    conn.execute('''INSERT OR REPLACE INTO odemeler
        (id,entity,aciklama,tip,tutar,para,vade,odeme_tarihi,durum,tekrar,not_,kaydeden,kayit_tarihi,banka,cek_no,kredi_id)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (oid, d.get('entity'), d.get('aciklama'), d.get('tip'), d.get('tutar',0),
         d.get('para','TL'), d.get('vade'), d.get('odeme_tarihi',''),
         d.get('durum','bekliyor'), d.get('tekrar','tek'),
         d.get('not',''), d.get('kaydeden'), datetime.now().isoformat(),
         d.get('banka','') or None, d.get('cek_no','') or None,
         d.get('kredi_id') or None))
    conn.commit()
    conn.close()
    return jsonify({'ok': True, 'id': oid})

@app.route('/api/odemeler/<oid>', methods=['PUT'])
def update_odeme(oid):
    d = request.json
    conn = get_db()
    conn.execute('''UPDATE odemeler SET
        aciklama=?, tip=?, tutar=?, para=?, vade=?, odeme_tarihi=?,
        durum=?, tekrar=?, not_=?, guncelleyen=?, guncelleme=?,
        banka=?, cek_no=?, kredi_id=COALESCE(?,kredi_id)
        WHERE id=?''',
        (d.get('aciklama'), d.get('tip'), d.get('tutar',0), d.get('para','TL'),
         d.get('vade'), d.get('odeme_tarihi',''), d.get('durum','bekliyor'),
         d.get('tekrar','tek'), d.get('not',''),
         d.get('guncelleyen'), datetime.now().isoformat(),
         d.get('banka','') or None, d.get('cek_no','') or None,
         d.get('kredi_id') or None, oid))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/odemeler/<oid>', methods=['DELETE'])
def delete_odeme(oid):
    conn = get_db()
    conn.execute("DELETE FROM odemeler WHERE id=?", (oid,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/odemeler/<oid>/odendi', methods=['POST'])
def mark_odendi(oid):
    d = request.json or {}
    # Tarih ve not parametresi desteklendi
    tarih = d.get('odeme_tarihi') or d.get('tarih') or datetime.now().strftime('%Y-%m-%d')
    not_  = d.get('not') or d.get('not_') or ''
    conn = get_db()
    conn.execute(
        "UPDATE odemeler SET durum='odendi', odeme_tarihi=?, not_=CASE WHEN ? != '' THEN ? ELSE not_ END WHERE id=?",
        (tarih, not_, not_, oid)
    )
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

# ============================================================
# KREDİLER
# ============================================================

@app.route('/api/krediler', methods=['GET'])
def get_krediler():
    entity = request.args.get('entity', '')
    conn = get_db()
    if entity:
        rows = conn.execute("SELECT * FROM krediler WHERE entity=?", (entity,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM krediler ORDER BY entity").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/krediler', methods=['POST'])
def add_kredi():
    d = request.json
    kid = d.get('id') or str(uuid.uuid4())[:10]
    conn = get_db()
    conn.execute('''INSERT OR REPLACE INTO krediler
        (id,entity,ad,tip,toplam,taksit,kalan_taksit,gun,faiz,banka,baslangic,not_,kaydeden,kayit_tarihi)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (kid, d.get('entity'), d.get('ad'), d.get('tip'), d.get('toplam',0),
         d.get('taksit',0), d.get('kalan_taksit',0), d.get('gun',''),
         d.get('faiz',''), d.get('banka',''), d.get('baslangic',''),
         d.get('not',''), d.get('kaydeden'), datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({'ok': True, 'id': kid})

@app.route('/api/krediler/<kid>', methods=['PUT'])
def update_kredi(kid):
    d = request.json
    conn = get_db()
    conn.execute('''UPDATE krediler SET
        ad=?, tip=?, toplam=?, taksit=?, kalan_taksit=?,
        gun=?, faiz=?, banka=?, baslangic=?, not_=?,
        guncelleyen=?, guncelleme=? WHERE id=?''',
        (d.get('ad'), d.get('tip'), d.get('toplam',0), d.get('taksit',0),
         d.get('kalan_taksit',0), d.get('gun',''), d.get('faiz',''),
         d.get('banka',''), d.get('baslangic',''), d.get('not',''),
         d.get('guncelleyen'), datetime.now().isoformat(), kid))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/krediler/<kid>', methods=['DELETE'])
def delete_kredi(kid):
    conn = get_db()
    conn.execute("DELETE FROM krediler WHERE id=?", (kid,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

# ============================================================
# PLANLAMA
# ============================================================

@app.route('/api/planlama', methods=['GET'])
def get_planlama():
    rows = get_db().execute("SELECT * FROM planlama ORDER BY tarih").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/planlama', methods=['POST'])
def add_plan():
    d = request.json
    pid = d.get('id') or str(uuid.uuid4())[:10]
    conn = get_db()
    conn.execute('''INSERT OR REPLACE INTO planlama
        (id,firma,kategori,aciklama,tutar,para,tarih,tekrar,durum,kaydeden,kayit_tarihi)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
        (pid, d.get('firma'), d.get('kategori'), d.get('aciklama'),
         d.get('tutar',0), d.get('para','TL'), d.get('tarih'),
         d.get('tekrar','tek'), d.get('durum','planli'),
         d.get('kaydeden'), datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({'ok': True, 'id': pid})

@app.route('/api/planlama/<pid>', methods=['DELETE'])
def delete_plan(pid):
    conn = get_db()
    conn.execute("DELETE FROM planlama WHERE id=?", (pid,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/planlama/<pid>/odendi', methods=['POST'])
def plan_odendi(pid):
    conn = get_db()
    conn.execute("UPDATE planlama SET durum='odendi' WHERE id=?", (pid,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

# ============================================================
# TOPLU AKTARIM
# ============================================================

@app.route('/api/import', methods=['POST'])
def bulk_import():
    d = request.json
    conn = get_db()
    c = conn.cursor()
    odeme_count = 0
    kredi_count = 0

    for o in d.get('odemeler', []):
        oid = o.get('id') or str(uuid.uuid4())[:10]
        existing = c.execute("SELECT id FROM odemeler WHERE id=?", (oid,)).fetchone()
        if not existing:
            c.execute('''INSERT INTO odemeler
                (id,entity,aciklama,tip,tutar,para,vade,odeme_tarihi,durum,tekrar,not_,kaydeden,kayit_tarihi)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (oid, o.get('entity'), o.get('aciklama'), o.get('tip'),
                 o.get('tutar',0), o.get('para','TL'), o.get('vade'),
                 o.get('odeme_tarihi',''), o.get('durum','bekliyor'),
                 o.get('tekrar','tek'), o.get('not',''),
                 o.get('kaydeden'), o.get('kayit_tarihi',datetime.now().isoformat())))
            odeme_count += 1

    for k in d.get('krediler', []):
        kid = k.get('id') or str(uuid.uuid4())[:10]
        existing = c.execute("SELECT id FROM krediler WHERE id=?", (kid,)).fetchone()
        if not existing:
            c.execute('''INSERT INTO krediler
                (id,entity,ad,tip,toplam,taksit,kalan_taksit,gun,faiz,banka,baslangic,not_,kaydeden,kayit_tarihi)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (kid, k.get('entity'), k.get('ad'), k.get('tip'),
                 k.get('toplam',0), k.get('taksit',0), k.get('kalan_taksit',0),
                 k.get('gun',''), k.get('faiz',''), k.get('banka',''),
                 k.get('baslangic',''), k.get('not',''),
                 k.get('kaydeden'), k.get('kayit_tarihi',datetime.now().isoformat())))
            kredi_count += 1

    conn.commit()
    conn.close()
    return jsonify({'ok': True, 'odeme_count': odeme_count, 'kredi_count': kredi_count})

# ============================================================
# ÖZET
# ============================================================

@app.route('/api/ozet', methods=['GET'])
def ozet():
    entity = request.args.get('entity', '')
    conn = get_db()
    where = "WHERE entity=?" if entity else ""
    params = (entity,) if entity else ()
    bugun = datetime.now().strftime('%Y-%m-%d')
    ay_bas = datetime.now().strftime('%Y-%m-01')
    ay_son = datetime.now().strftime('%Y-%m-31')

    def q(sql, p=()):
        return conn.execute(sql, p).fetchone()[0] or 0

    base = f"FROM odemeler {where}"
    ep = params

    result = {
        'ay_odeme_bekliyor': q(f"SELECT COUNT(*) {base} AND durum='bekliyor' AND vade BETWEEN ? AND ?", ep+(ay_bas,ay_son)),
        'ay_tutar_bekliyor': q(f"SELECT SUM(tutar) {base} AND durum='bekliyor' AND vade BETWEEN ? AND ?", ep+(ay_bas,ay_son)),
        'gecikti_sayi':      q(f"SELECT COUNT(*) {base} AND durum!='odendi' AND vade < ?", ep+(bugun,)),
        'gecikti_tutar':     q(f"SELECT SUM(tutar) {base} AND durum!='odendi' AND vade < ?", ep+(bugun,)),
        'ay_odendi_sayi':    q(f"SELECT COUNT(*) {base} AND durum='odendi' AND odeme_tarihi BETWEEN ? AND ?", ep+(ay_bas,ay_son)),
        'ay_odendi_tutar':   q(f"SELECT SUM(tutar) {base} AND durum='odendi' AND odeme_tarihi BETWEEN ? AND ?", ep+(ay_bas,ay_son)),
        'kredi_toplam':      q(f"SELECT SUM(toplam) FROM krediler {where}", ep),
        'kredi_sayi':        q(f"SELECT COUNT(*) FROM krediler {where}", ep),
        'kasa_bakiye':       q(f"SELECT SUM(CASE WHEN tip='giris' THEN tutar ELSE -tutar END) FROM kasa {where}", ep),
    }
    conn.close()
    return jsonify(result)

# ============================================================
# STATIC
# ============================================================

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'finans_yonetim.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(BASE_DIR, filename)

if __name__ == '__main__':
    init_db()
    print("=" * 50)
    print("  Finans Yönetim Sistemi")
    print("  http://192.168.1.16:5058")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5058, debug=False)
