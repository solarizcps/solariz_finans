"""
Solariz Planlama Sunucusu
Port: 5057
"""
from flask import Flask, jsonify, request, session, send_from_directory
from flask_cors import CORS
import subprocess, json, os, uuid, threading, time
from datetime import datetime, date, timedelta
from functools import wraps
from werkzeug.utils import secure_filename

# SMTP AYARLARI - Gmail
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "bilgi@solariz.com.tr"
SMTP_PASS = "wubfxiaifiztospd"
SMTP_FROM = "Solariz Planlama <bilgi@solariz.com.tr>"
# Acil görev bildirimi gidecek mailler (virgülle ayrı eklenebilir)
GOREV_MAIL_ALICILAR = "adem@solariz.com.tr,alpay@solariz.com.tr,bilgi@solariz.com.tr"

def gorev_mail_gonder(baslik, aciklama, atanan, birim, son_tar, olusturan):
    """Acil görev oluşturulduğunda mail gönder"""
    if not SMTP_HOST or not SMTP_USER:
        print("SMTP ayarları eksik, mail gönderilmedi")
        return
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    # Sabit alıcılar + atanan kişinin maili
    alicilar = set(a.strip() for a in GOREV_MAIL_ALICILAR.split(',') if a.strip())
    atanan_mail = KULLANICILAR.get(atanan, {}).get('mail', '')
    if atanan_mail:
        alicilar.add(atanan_mail)
    if not alicilar:
        print("Alıcı mail adresi bulunamadı")
        return
    alicilar = list(alicilar)
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🚨 ACİL GÖREV: {baslik}"
    msg['From'] = SMTP_FROM
    msg['To'] = ', '.join(alicilar)
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
      <div style="background:#1e3a8a;color:#fff;padding:20px;border-radius:8px 8px 0 0;">
        <h2 style="margin:0;">🚨 Acil Görev Atandı</h2>
      </div>
      <div style="background:#fff;border:1px solid #e2e6ec;padding:20px;border-radius:0 0 8px 8px;">
        <table style="width:100%;border-collapse:collapse;">
          <tr><td style="padding:8px;font-weight:bold;color:#6b7280;width:120px;">Başlık</td><td style="padding:8px;font-weight:700;">{baslik}</td></tr>
          <tr style="background:#f6f8fb;"><td style="padding:8px;font-weight:bold;color:#6b7280;">Birim</td><td style="padding:8px;">{birim}</td></tr>
          <tr><td style="padding:8px;font-weight:bold;color:#6b7280;">Atanan</td><td style="padding:8px;">{atanan}</td></tr>
          <tr style="background:#f6f8fb;"><td style="padding:8px;font-weight:bold;color:#6b7280;">Son Tarih</td><td style="padding:8px;color:#dc2626;font-weight:700;">{son_tar}</td></tr>
          <tr><td style="padding:8px;font-weight:bold;color:#6b7280;">Açıklama</td><td style="padding:8px;">{aciklama}</td></tr>
          <tr style="background:#f6f8fb;"><td style="padding:8px;font-weight:bold;color:#6b7280;">Atayan</td><td style="padding:8px;">{olusturan}</td></tr>
        </table>
        <div style="margin-top:16px;padding:12px;background:#fef2f2;border-radius:6px;color:#dc2626;font-size:13px;">
          Bu görev ACİL olarak işaretlenmiştir. Lütfen en kısa sürede ilgilenin.
        </div>
        <div style="margin-top:16px;text-align:center;">
          <a href="http://192.168.1.16:5057" style="background:#1e3a8a;color:#fff;padding:10px 24px;border-radius:6px;text-decoration:none;font-weight:bold;">Sisteme Git →</a>
        </div>
      </div>
    </div>
    """
    msg.attach(MIMEText(html, 'html', 'utf-8'))
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as srv:
        srv.starttls()
        srv.login(SMTP_USER, SMTP_PASS)
        srv.sendmail(SMTP_FROM, alicilar, msg.as_string())
    print(f"Acil görev maili gönderildi: {baslik} -> {alicilar}")

UPLOAD_FOLDER = r"D:\Firma_Ozel\adem\planlama cps sistemi\grafik_resimler"
ALLOWED_EXT = {'png','jpg','jpeg','gif','webp','pdf'}
app = Flask(__name__)
app.secret_key = "solariz_planlama_2024"
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 7
CORS(app, supports_credentials=True, origins=['*'])
# Resim klasörünü oluştur
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
SQLCMD=r'C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\Tools\Binn\sqlcmd.exe'
SERVER="solarizdb"
DATABASE="Solariz22"
UID="claude"
PWD="104099"
KULLANICILAR={
  "halil":      {"sifre":"232323",    "rol":"admin",     "mail":""},
  "hasan":      {"sifre":"323232",    "rol":"normal",    "mail":""},
  "admin":      {"sifre":"f7a6ua61",  "rol":"admin",     "mail":""},
  "samet":      {"sifre":"147258",    "rol":"grafik",    "mail":"grafik@solariz.com.tr"},
  "samet_kalite":{"sifre":"solariz2025","rol":"kalite",  "mail":"Kalitekontrol@solariz.com.tr"},
  "kalite":     {"sifre":"kalite1",   "rol":"kalite",    "mail":"Kalitekontrol@solariz.com.tr"},
  "satin":      {"sifre":"satin1",    "rol":"satinalma", "mail":""},
  "ibrahim":    {"sifre":"ibrahim2025","rol":"satinalma", "mail":"ibrahimkilic@solariz.com.tr"},
  "mehmet":     {"sifre":"142536",    "rol":"planlama",  "mail":"mehmet@solariz.com.tr"},
  "alpay":      {"sifre":"17531753",  "rol":"admin",     "mail":"alpay@solariz.com.tr"},
  "adem":       {"sifre":"adem2025",  "rol":"admin",     "mail":"adem@solariz.com.tr"},
  "altan":      {"sifre":"altan2025", "rol":"planlama",  "mail":"altan@solariz.com.tr"},
}
KORGUN_SERVER="solarizdb"
KORGUN_DATABASE="Solariz22"
KORGUN_UID="claude"
KORGUN_PWD="104099"

def run_query(sql, server=None, database=None, uid=None, pwd=None):
    s=server or SERVER
    db=database or DATABASE
    u=uid or UID
    p=pwd or PWD
    wrapped=f"SET NOCOUNT ON; {sql} FOR JSON PATH, INCLUDE_NULL_VALUES"
    cmd=[SQLCMD,'-S',s,'-d',db,'-U',u,'-P',p,'-Q',wrapped,'-y','0','-f','65001']
    try:
        result=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=30)
        output=result.stdout
        if result.returncode!=0:
            return None,result.stderr.strip() or 'Sorgu hatasi'
        lines=[]
        for line in output.splitlines():
            line=line.strip()
            if line and not line.startswith('(') and line not in ['','\r']:
                lines.append(line)
        if not lines:
            return [],None
        json_str=''.join(lines)
        if not json_str or json_str in ['NULL','null']:
            return [],None
        data=json.loads(json_str)
        if not isinstance(data,list):
            data=[data]
        return data,None
    except subprocess.TimeoutExpired:
        return None,"Zaman asimi (30s)"
    except json.JSONDecodeError as e:
        return None,f"JSON hatasi: {e}"
    except Exception as e:
        return None,str(e)

def run_exec(sql):
    cmd=[SQLCMD,'-S',SERVER,'-d',DATABASE,'-U',UID,'-P',PWD,'-Q',sql,'-f','65001']
    result=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=30)
    if result.returncode!=0:
        raise Exception(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()

def qry(sql):
    data,err=run_query(sql)
    if err:
        raise Exception(err)
    return data or []

def giris_gerekli(f):
    @wraps(f)
    def wrapper(*args,**kwargs):
        if 'kullanici' not in session:
            return jsonify({"hata":"Giris gerekli"}),401
        return f(*args,**kwargs)
    return wrapper

def log_yaz(siparis_id,islem,detay=""):
    try:
        kullanici=session.get('kullanici','sistem')
        rol=session.get('rol','')
        run_exec(f"INSERT INTO planlama_log (siparis_id,birim,kullanici,islem,detay) VALUES ({siparis_id or 'NULL'},N'{rol}',N'{kullanici}',N'{islem.replace(chr(39),chr(39)+chr(39))}',N'{detay.replace(chr(39),chr(39)+chr(39))}')")
    except:
        pass

def q(v):
    if v is None:
        return 'NULL'
    return "N'" + str(v).replace("'","''") + "'"

@app.route("/api/giris",methods=["POST"])
def giris():
    d=request.get_json() or {}
    k=d.get('kullanici','').strip()
    s=d.get('sifre','')
    u=KULLANICILAR.get(k)
    if u and u['sifre']==s:
        session.permanent = True
        session['kullanici']=k
        session['rol']=u['rol']
        return jsonify({"ok":True,"rol":u['rol']})
    return jsonify({"ok":False}),401

@app.route("/api/cikis",methods=["POST"])
def cikis():
    session.clear()
    return jsonify({"ok":True})

@app.route("/api/me")
def me():
    if 'kullanici' not in session:
        return jsonify({"giris":False})
    return jsonify({"giris":True,"kullanici":session['kullanici'],"rol":session['rol']})

@app.route("/api/korgun/siparisler")
@giris_gerekli
def korgun_siparisler():
    try:
        rows,err=run_query("SELECT sk.SipNo,sk.CariKod,ISNULL(cm.CName,sk.CariKod) AS CariTanim,CONVERT(varchar,sk.TeslimTar,23) AS TeslimTar,sk.Durum,sk.SipTip,sh.SKOD AS ModelKod,CASE WHEN ps.korgun_sip_no IS NOT NULL THEN 'aktarildi' ELSE 'sisteme_girilmedi' END AS plan_durumu FROM Siparis_Kay sk LEFT JOIN Siparis_Har sh ON sk.SipNo=sh.SipNo LEFT JOIN Cari_Kart cm ON sk.CariKod=cm.CKod LEFT JOIN planlama_siparis ps ON CAST(sk.SipNo AS NVARCHAR)=ps.korgun_sip_no WHERE sk.SipTip IN ('A','S','ST') ORDER BY sk.SipNo DESC",server=KORGUN_SERVER,database=KORGUN_DATABASE,uid=KORGUN_UID,pwd=KORGUN_PWD)
        if err:
            return jsonify({"hata":err}),500
        return jsonify(rows or [])
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/siparisler",methods=["GET"])
@giris_gerekli
def siparisler_listesi():
    try:
        durum=request.args.get('durum','')
        filtre=f"WHERE durum=N'{durum}'" if durum else ""
        rows=qry(f"SELECT id,korgun_sip_no,model_kod,cari_tanim AS musteri_adi,CONVERT(varchar,termin_tar,23) AS termin_tar,durum,oncelik,notlar FROM planlama_siparis {filtre} ORDER BY CASE oncelik WHEN 'yuksek' THEN 1 WHEN 'normal' THEN 2 ELSE 3 END,termin_tar")
        return jsonify(rows)
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/siparisler",methods=["POST"])
@giris_gerekli
def siparis_olustur():
    try:
        d=request.get_json() or {}
        rows=qry(f"SELECT TOP 1 id FROM planlama_siparis WHERE korgun_sip_no={q(d.get('korgun_sip_no'))}")
        if rows:
            return jsonify({"hata":"Bu siparis zaten mevcut","id":rows[0]['id']}),409
        kullanici=session.get('kullanici','sistem')
        run_exec(f"INSERT INTO planlama_siparis (korgun_sip_no,model_kod,cari_tanim,termin_tar,durum,oncelik,notlar,olusturan) VALUES ({q(d.get('korgun_sip_no'))},{q(d.get('model_kod'))},{q(d.get('musteri_adi') or d.get('cari_tanim'))},{q(d.get('termin_tar')) if d.get('termin_tar') else 'NULL'},N'bekliyor',{q(d.get('oncelik','normal'))},{q(d.get('notlar',''))},{q(kullanici)})")
        rows=qry(f"SELECT TOP 1 id FROM planlama_siparis WHERE korgun_sip_no={q(d.get('korgun_sip_no'))}")
        yeni_id=rows[0]['id'] if rows else None
        log_yaz(yeni_id,"siparis_olusturuldu",f"Model:{d.get('model_kod')}")
        return jsonify({"ok":True,"id":yeni_id})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/siparisler/<int:sid>",methods=["GET"])
@giris_gerekli
def siparis_detay(sid):
    try:
        siparis=qry(f"SELECT id,korgun_sip_no,model_kod,cari_tanim AS musteri_adi,CONVERT(varchar,termin_tar,23) AS termin_tar,durum,oncelik,notlar FROM planlama_siparis WHERE id={sid}")
        gorevler=qry(f"SELECT id,birim,gorev_tipi,atanan,durum,CONVERT(varchar,beklenen_tar,23) AS son_tar,aciklama FROM planlama_gorev WHERE siparis_id={sid} ORDER BY olusturma_tar")
        grafik=qry(f"SELECT id,talep_tipi,aciklama,durum,CONVERT(varchar,teslim_tarihi,23) AS son_tar,notlar FROM grafik_talep WHERE siparis_id={sid}")
        satinalma=qry(f"SELECT id,malzeme_tanim,miktar,birim,durum,notlar FROM satinalma_talep WHERE siparis_id={sid}")
        kalite=qry(f"SELECT id,kontrol_tipi,proses,sonuc,bulgular,CONVERT(varchar,kontrol_tar,23) AS kontrol_tar FROM kalite_kontrol WHERE siparis_id={sid}")
        loglar=qry(f"SELECT TOP 50 kullanici,islem,detay,CONVERT(varchar,islem_tar,20) AS islem_tar FROM planlama_log WHERE siparis_id={sid} ORDER BY islem_tar DESC")
        return jsonify({"siparis":siparis,"gorevler":gorevler,"grafik":grafik,"satinalma":satinalma,"kalite":kalite,"loglar":loglar})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/siparisler/<int:sid>/durum",methods=["PATCH"])
@giris_gerekli
def siparis_durum_guncelle(sid):
    try:
        d=request.get_json() or {}
        durum=d.get('durum')
        if durum not in ('bekliyor','devam','tamamlandi','iptal'):
            return jsonify({"hata":"Gecersiz durum"}),400
        run_exec(f"UPDATE planlama_siparis SET durum={q(durum)},guncelleme_tar=GETDATE() WHERE id={sid}")
        log_yaz(sid,"durum_guncellendi",durum)
        return jsonify({"ok":True})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/gorevler",methods=["POST"])
@giris_gerekli
def gorev_ekle():
    try:
        d=request.get_json() or {}
        kullanici=session.get('kullanici','sistem')
        rol=KULLANICILAR.get(kullanici,{}).get('rol','')
        if rol not in ('admin','planlama'):
            return jsonify({"hata":"Görev atama yetkiniz yok"}),403
        oncelik=d.get('oncelik','normal')
        baslik=d.get('baslik') or d.get('gorev_tipi') or d.get('aciklama') or 'Görev'
        run_exec(f"""INSERT INTO planlama_gorev
            (siparis_id,birim,gorev_tipi,atanan,durum,beklenen_tar,aciklama,olusturan)
            VALUES ({d.get('siparis_id') or 'NULL'},{q(d.get('birim',''))},
            {q(baslik)},{q(d.get('atanan',''))},N'bekliyor',
            {q(d.get('son_tar')) if d.get('son_tar') else 'NULL'},
            {q(d.get('aciklama',''))},{q(kullanici)})""")
        rows=qry("SELECT TOP 1 id FROM planlama_gorev ORDER BY id DESC")
        new_id=rows[0]['id'] if rows else None
        log_yaz(d.get('siparis_id'),"gorev_eklendi",d.get('birim',''))
        if oncelik=='acil':
            try: gorev_mail_gonder(baslik,d.get('aciklama',''),d.get('atanan',''),d.get('birim',''),d.get('son_tar',''),kullanici)
            except Exception as me: print(f"Mail gönderilemedi: {me}")
        return jsonify({"ok":True,"id":new_id})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/gorevler/<int:gid>",methods=["PATCH"])
@giris_gerekli
def gorev_guncelle(gid):
    try:
        d=request.get_json() or {}
        rows=qry(f"SELECT siparis_id FROM planlama_gorev WHERE id={gid}")
        siparis_id=rows[0]['siparis_id'] if rows else None
        parts=[]
        if 'durum' in d:
            parts.append(f"durum={q(d['durum'])}")
        if 'notlar' in d:
            parts.append(f"aciklama={q(d['notlar'])}")
        if not parts:
            return jsonify({"hata":"Alan yok"}),400
        parts.append("guncelleme_tar=GETDATE()")
        run_exec(f"UPDATE planlama_gorev SET {chr(44).join(parts)} WHERE id={gid}")
        log_yaz(siparis_id,"gorev_guncellendi",str(d))
        return jsonify({"ok":True})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/grafik",methods=["POST"])
@giris_gerekli
def grafik_talep_ekle():
    try:
        d=request.get_json() or {}
        kullanici=session.get('kullanici','sistem')
        run_exec(f"INSERT INTO grafik_talep (siparis_id,talep_tipi,aciklama,durum,teslim_tarihi,notlar,olusturan) VALUES ({d.get('siparis_id')},{q(d.get('talep_tipi','genel'))},{q(d.get('aciklama',''))},N'bekliyor',{q(d.get('son_tar')) if d.get('son_tar') else 'NULL'},{q(d.get('notlar',''))},{q(kullanici)})")
        rows=qry(f"SELECT TOP 1 id FROM grafik_talep WHERE siparis_id={d.get('siparis_id')} ORDER BY id DESC")
        log_yaz(d.get('siparis_id'),"grafik_eklendi","")
        return jsonify({"ok":True,"id":rows[0]['id'] if rows else None})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/grafik/<int:gid>",methods=["PATCH"])
@giris_gerekli
def grafik_guncelle(gid):
    try:
        d=request.get_json() or {}
        rows=qry(f"SELECT siparis_id FROM grafik_talep WHERE id={gid}")
        siparis_id=rows[0]['siparis_id'] if rows else None
        parts=[]
        if 'durum' in d:
            parts.append(f"durum={q(d['durum'])}")
        if 'notlar' in d:
            parts.append(f"notlar={q(d['notlar'])}")
        if not parts:
            return jsonify({"hata":"Alan yok"}),400
        parts.append("guncelleme_tar=GETDATE()")
        run_exec(f"UPDATE grafik_talep SET {chr(44).join(parts)} WHERE id={gid}")
        log_yaz(siparis_id,"grafik_guncellendi",str(d))
        return jsonify({"ok":True})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/satinalma",methods=["POST"])
@giris_gerekli
def satinalma_talep_ekle():
    try:
        d=request.get_json() or {}
        kullanici=session.get('kullanici','sistem')
        run_exec(f"INSERT INTO satinalma_talep (siparis_id,malzeme_tanim,miktar,birim,durum,notlar,olusturan) VALUES ({d.get('siparis_id')},{q(d.get('malzeme_tanim',''))},{d.get('miktar') or 'NULL'},{q(d.get('birim','adet'))},N'bekliyor',{q(d.get('notlar',''))},{q(kullanici)})")
        rows=qry(f"SELECT TOP 1 id FROM satinalma_talep WHERE siparis_id={d.get('siparis_id')} ORDER BY id DESC")
        log_yaz(d.get('siparis_id'),"satinalma_eklendi","")
        return jsonify({"ok":True,"id":rows[0]['id'] if rows else None})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/satinalma/<int:tid>",methods=["PATCH"])
@giris_gerekli
def satinalma_guncelle(tid):
    try:
        d=request.get_json() or {}
        rows=qry(f"SELECT siparis_id FROM satinalma_talep WHERE id={tid}")
        siparis_id=rows[0]['siparis_id'] if rows else None
        parts=[]
        if 'durum' in d:
            parts.append(f"durum={q(d['durum'])}")
        if 'notlar' in d:
            parts.append(f"notlar={q(d['notlar'])}")
        if not parts:
            return jsonify({"hata":"Alan yok"}),400
        parts.append("guncelleme_tar=GETDATE()")
        run_exec(f"UPDATE satinalma_talep SET {chr(44).join(parts)} WHERE id={tid}")
        log_yaz(siparis_id,"satinalma_guncellendi",str(d))
        return jsonify({"ok":True})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/kalite",methods=["POST"])
@giris_gerekli
def kalite_ekle():
    try:
        d=request.get_json() or {}
        kullanici=session.get('kullanici','sistem')
        run_exec(f"INSERT INTO kalite_kontrol (siparis_id,kontrol_tipi,proses,sonuc,kontrolcu,bulgular) VALUES ({d.get('siparis_id')},{q(d.get('kontrol_tipi','genel'))},{q(d.get('proses',''))},N'beklemede',{q(kullanici)},{q(d.get('bulgular',''))})")
        rows=qry(f"SELECT TOP 1 id FROM kalite_kontrol WHERE siparis_id={d.get('siparis_id')} ORDER BY id DESC")
        log_yaz(d.get('siparis_id'),"kalite_eklendi","")
        return jsonify({"ok":True,"id":rows[0]['id'] if rows else None})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/ozet")
@giris_gerekli
def ozet():
    try:
        siparis_ozet=qry("SELECT durum,COUNT(*) as adet FROM planlama_siparis GROUP BY durum")
        gorev_ozet=qry("SELECT birim,durum,COUNT(*) as adet FROM planlama_gorev GROUP BY birim,durum")
        grafik_ozet=qry("SELECT durum,COUNT(*) as adet FROM grafik_talep GROUP BY durum")
        satinalma_ozet=qry("SELECT durum,COUNT(*) as adet FROM satinalma_talep GROUP BY durum")
        kalite_ozet=qry("SELECT sonuc,COUNT(*) as adet FROM kalite_kontrol GROUP BY sonuc")
        gecmis_termin=qry("SELECT korgun_sip_no,model_kod,CONVERT(varchar,termin_tar,23) as termin_tar,oncelik FROM planlama_siparis WHERE termin_tar<CAST(GETDATE() AS DATE) AND durum NOT IN ('tamamlandi','iptal') ORDER BY termin_tar")
        return jsonify({"siparis":siparis_ozet,"gorev":gorev_ozet,"grafik":grafik_ozet,"satinalma":satinalma_ozet,"kalite":kalite_ozet,"gecmis_termin":gecmis_termin})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/")
def index():
    from flask import make_response
    import os
    path = r"D:\Firma_Ozel\adem\planlama cps sistemi"
    resp = make_response(open(os.path.join(path,"planlama_cps.html"),encoding="utf-8").read())
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp


@app.route("/api/grafik",methods=["GET"])
@giris_gerekli
def grafik_listesi():
    try:
        rol=session.get("rol","")
        filtre="" if rol=="admin" else ""
        rows=qry("SELECT g.id,g.siparis_id,g.talep_tipi,g.aciklama,g.durum,CONVERT(varchar,g.teslim_tarihi,23) AS son_tar,g.notlar,g.olusturan,s.korgun_sip_no,s.model_kod,s.cari_tanim AS musteri_adi FROM grafik_talep g LEFT JOIN planlama_siparis s ON g.siparis_id=s.id ORDER BY g.olusturma_tar DESC")
        return jsonify(rows)
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/gorevler",methods=["GET"])
@giris_gerekli
def gorevler_listesi():
    try:
        kullanici=session.get('kullanici','sistem')
        rol=KULLANICILAR.get(kullanici,{}).get('rol','')
        # Admin ve planlama tümünü görür, diğerleri sadece kendine atananları
        if rol in ('admin','planlama'):
            filtre=""
        else:
            filtre=f"WHERE g.atanan={q(kullanici)}"
        rows=qry(f"""SELECT g.id,g.siparis_id,g.birim,g.gorev_tipi,g.atanan,g.durum,
            CONVERT(varchar,g.beklenen_tar,23) AS son_tar,g.aciklama,g.olusturan,
            s.korgun_sip_no,s.model_kod,s.cari_tanim AS musteri_adi
            FROM planlama_gorev g
            LEFT JOIN planlama_siparis s ON g.siparis_id=s.id
            {filtre}
            ORDER BY g.olusturma_tar DESC""")
        return jsonify(rows)
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/kalite",methods=["GET"])
@giris_gerekli
def kalite_listesi():
    try:
        rows=qry("SELECT k.id,k.siparis_id,k.kontrol_tipi,k.proses,k.sonuc,k.kontrolcu,k.bulgular,CONVERT(varchar,k.kontrol_tar,23) AS kontrol_tar,s.korgun_sip_no,s.model_kod,s.cari_tanim AS musteri_adi FROM kalite_kontrol k LEFT JOIN planlama_siparis s ON k.siparis_id=s.id ORDER BY k.kontrol_tar DESC")
        return jsonify(rows)
    except Exception as e:
        return jsonify({"hata":str(e)}),500
@app.route("/api/mail_test")
@giris_gerekli
def mail_test():
    """Mail sistemi test endpoint'i"""
    import smtplib
    try:
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "✅ Solariz Mail Test"
        msg['From'] = SMTP_FROM
        msg['To'] = "adem@solariz.com.tr"
        msg.attach(MIMEText("<h2>Mail sistemi çalışıyor!</h2><p>Solariz Planlama CPS</p>", 'html', 'utf-8'))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as srv:
            srv.set_debuglevel(0)
            srv.ehlo()
            srv.starttls()
            srv.ehlo()
            srv.login(SMTP_USER, SMTP_PASS)
            srv.sendmail(SMTP_FROM, ["adem@solariz.com.tr"], msg.as_string())
        return jsonify({"ok": True, "mesaj": "Test maili gönderildi → adem@solariz.com.tr"})
    except smtplib.SMTPAuthenticationError as e:
        return jsonify({"hata": f"Kimlik doğrulama hatası: {str(e)}", "cozum": "Gmail App Password gerekli olabilir"})
    except smtplib.SMTPConnectError as e:
        return jsonify({"hata": f"Bağlantı hatası: {str(e)}", "cozum": "SMTP host veya port yanlış olabilir"})
    except Exception as e:
        return jsonify({"hata": str(e), "smtp_host": SMTP_HOST, "smtp_user": SMTP_USER})

@app.route("/upload_html",methods=["POST"])
def upload_html():
    data=request.get_json()
    open(r"D:\Firma_Ozel\adem\planlama cps sistemi\planlama_cps.html","w",encoding="utf-8").write(data["html"])
    return jsonify({"ok":True,"len":len(data["html"])})

    return jsonify({"ok":True,"len":len(data["html"])})

# ─── ŞİFRE DEĞİŞTİRME ───────────────────────────────────────────────
@app.route("/api/sifre_degistir", methods=["POST"])
@giris_gerekli
def sifre_degistir():
    try:
        d = request.get_json() or {}
        kullanici = session.get('kullanici','')
        eski = d.get('eski_sifre','')
        yeni = d.get('yeni_sifre','')
        if not kullanici or not yeni:
            return jsonify({"hata":"Eksik bilgi"}), 400
        if len(yeni) < 6:
            return jsonify({"hata":"Şifre en az 6 karakter olmalı"}), 400
        if KULLANICILAR.get(kullanici,{}).get('sifre') != eski:
            return jsonify({"hata":"Mevcut şifre yanlış"}), 403
        KULLANICILAR[kullanici]['sifre'] = yeni
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"hata": str(e)}), 500

# ─── YETKİ YÖNETİMİ ──────────────────────────────────────────────────
@app.route("/api/admin/kullanicilar", methods=["GET"])
@giris_gerekli
def admin_kullanici_listesi():
    kullanici = session.get('kullanici','')
    if KULLANICILAR.get(kullanici,{}).get('rol') != 'admin':
        return jsonify({"hata":"Yetkisiz"}), 403
    liste = []
    for k, v in KULLANICILAR.items():
        liste.append({"kullanici":k, "rol":v.get('rol',''), "mail":v.get('mail',''), "sayfalar":v.get('sayfalar',[])})
    return jsonify(liste)

@app.route("/api/admin/kullanici/<kadi>/rol", methods=["PATCH"])
@giris_gerekli
def admin_rol_guncelle(kadi):
    kullanici = session.get('kullanici','')
    if KULLANICILAR.get(kullanici,{}).get('rol') != 'admin':
        return jsonify({"hata":"Yetkisiz"}), 403
    d = request.get_json() or {}
    if kadi not in KULLANICILAR:
        return jsonify({"hata":"Kullanıcı bulunamadı"}), 404
    if 'rol' in d:
        KULLANICILAR[kadi]['rol'] = d['rol']
    if 'sayfalar' in d:
        KULLANICILAR[kadi]['sayfalar'] = d['sayfalar']
    return jsonify({"ok": True})

@app.route("/api/admin/kullanici_ekle", methods=["POST"])
@giris_gerekli
def admin_kullanici_ekle():
    kullanici = session.get('kullanici','')
    if KULLANICILAR.get(kullanici,{}).get('rol') != 'admin':
        return jsonify({"hata":"Yetkisiz"}), 403
    d = request.get_json() or {}
    kadi = d.get('kullanici_adi','').strip()
    if not kadi:
        return jsonify({"hata":"Kullanıcı adı zorunlu"}), 400
    if kadi in KULLANICILAR:
        return jsonify({"hata":"Bu kullanıcı adı zaten var"}), 400
    KULLANICILAR[kadi] = {
        "sifre": d.get('sifre','solariz2025'),
        "rol": d.get('rol','normal'),
        "mail": d.get('mail',''),
        "sayfalar": []
    }
    return jsonify({"ok": True})

# ─── SATIN ALMA MODÜLܒ ───────────────────────────────────────────────
def init_satinalma_tables():
    sqls = [
        """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='satinalma_talep_v2' AND xtype='U')
CREATE TABLE satinalma_talep_v2 (
  id              INT IDENTITY(1,1) PRIMARY KEY,
  siparis_id      INT,
  malzeme_tanim   NVARCHAR(300) NOT NULL,
  malzeme_grubu   NVARCHAR(100),
  miktar          DECIMAL(10,2),
  birim           NVARCHAR(30) NOT NULL DEFAULT 'adet',
  acil_mi         BIT NOT NULL DEFAULT 0,
  tedarikci_id    INT,
  tahmini_fiyat   DECIMAL(10,2),
  para_birimi     NVARCHAR(10) NOT NULL DEFAULT 'TL',
  durum           NVARCHAR(30) NOT NULL DEFAULT 'bekliyor',
  teslim_tarihi   DATE,
  notlar          NVARCHAR(MAX),
  olusturan       NVARCHAR(100),
  onaylayan       NVARCHAR(100),
  olusturma_tar   DATETIME NOT NULL DEFAULT GETDATE(),
  guncelleme_tar  DATETIME NOT NULL DEFAULT GETDATE()
)""",
        """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='satinalma_tedarikci' AND xtype='U')
CREATE TABLE satinalma_tedarikci (
  id              INT IDENTITY(1,1) PRIMARY KEY,
  firma_adi       NVARCHAR(200) NOT NULL,
  iletisim_kisi   NVARCHAR(100),
  telefon         NVARCHAR(50),
  email           NVARCHAR(100),
  malzeme_grubu   NVARCHAR(200),
  adres           NVARCHAR(MAX),
  notlar          NVARCHAR(MAX),
  aktif           BIT NOT NULL DEFAULT 1,
  olusturan       NVARCHAR(100),
  olusturma_tar   DATETIME NOT NULL DEFAULT GETDATE()
)""",
        """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='satinalma_siparis' AND xtype='U')
CREATE TABLE satinalma_siparis (
  id              INT IDENTITY(1,1) PRIMARY KEY,
  talep_id        INT,
  tedarikci_id    INT NOT NULL,
  malzeme_tanim   NVARCHAR(300) NOT NULL,
  miktar          DECIMAL(10,2),
  birim           NVARCHAR(30) NOT NULL DEFAULT 'adet',
  birim_fiyat     DECIMAL(10,2),
  toplam_tutar    DECIMAL(10,2),
  para_birimi     NVARCHAR(10) NOT NULL DEFAULT 'TL',
  siparis_tarihi  DATE,
  teslim_tarihi   DATE,
  durum           NVARCHAR(30) NOT NULL DEFAULT 'siparis_verildi',
  notlar          NVARCHAR(MAX),
  olusturan       NVARCHAR(100),
  olusturma_tar   DATETIME NOT NULL DEFAULT GETDATE(),
  guncelleme_tar  DATETIME NOT NULL DEFAULT GETDATE()
)""",
    ]
    for sql in sqls:
        try: run_exec(sql)
        except Exception as e: print(f"satinalma tablo: {e}")

# Satın alma talepler
@app.route("/api/satinalma/talepler", methods=["GET"])
@giris_gerekli
def satinalma_talep_listesi():
    try:
        rows = qry("""SELECT t.id,t.siparis_id,t.malzeme_tanim,t.malzeme_grubu,
            t.miktar,t.birim,t.acil_mi,t.tahmini_fiyat,t.para_birimi,
            t.durum,CONVERT(varchar,t.teslim_tarihi,23) AS teslim_tarihi,
            t.notlar,t.olusturan,t.onaylayan,
            CONVERT(varchar,t.olusturma_tar,20) AS olusturma_tar,
            s.korgun_sip_no,s.model_kod,s.cari_tanim AS musteri_adi,
            td.firma_adi AS tedarikci_adi
            FROM satinalma_talep_v2 t
            LEFT JOIN planlama_siparis s ON t.siparis_id=s.id
            LEFT JOIN satinalma_tedarikci td ON t.tedarikci_id=td.id
            ORDER BY t.acil_mi DESC, t.olusturma_tar DESC""")
        return jsonify(rows)
    except Exception as e:
        return jsonify({"hata":str(e)}), 500

@app.route("/api/satinalma/talepler", methods=["POST"])
@giris_gerekli
def satinalma_talep_ekle():
    try:
        d = request.get_json() or {}
        kullanici = session.get('kullanici','sistem')
        acil = 1 if d.get('acil_mi') else 0
        tt = d.get('teslim_tarihi')
        run_exec(f"""INSERT INTO satinalma_talep_v2
            (siparis_id,malzeme_tanim,malzeme_grubu,miktar,birim,acil_mi,
             tahmini_fiyat,para_birimi,teslim_tarihi,notlar,olusturan)
            VALUES ({d.get('siparis_id') or 'NULL'},
            {q(d.get('malzeme_tanim',''))},{q(d.get('malzeme_grubu',''))},
            {d.get('miktar') or 'NULL'},{q(d.get('birim','adet'))},{acil},
            {d.get('tahmini_fiyat') or 'NULL'},{q(d.get('para_birimi','TL'))},
            {'CAST('+q(tt)+' AS DATE)' if tt else 'NULL'},
            {q(d.get('notlar',''))},{q(kullanici)})""")
        rows = qry("SELECT TOP 1 id FROM satinalma_talep_v2 ORDER BY id DESC")
        return jsonify({"ok":True,"id":rows[0]['id'] if rows else None})
    except Exception as e:
        return jsonify({"hata":str(e)}), 500

@app.route("/api/satinalma/talepler/<int:tid>", methods=["PATCH"])
@giris_gerekli
def satinalma_talep_guncelle(tid):
    try:
        d = request.get_json() or {}
        parts = []
        for f in ('durum','notlar','malzeme_tanim','malzeme_grubu','birim','para_birimi','onaylayan'):
            if f in d: parts.append(f"{f}={q(d[f])}")
        for f in ('miktar','tahmini_fiyat','tedarikci_id','siparis_id'):
            if f in d and d[f] is not None: parts.append(f"{f}={d[f]}")
        if 'teslim_tarihi' in d:
            parts.append(f"teslim_tarihi={'CAST('+q(d['teslim_tarihi'])+' AS DATE)' if d['teslim_tarihi'] else 'NULL'}")
        if not parts: return jsonify({"hata":"Alan yok"}), 400
        parts.append("guncelleme_tar=GETDATE()")
        run_exec(f"UPDATE satinalma_talep_v2 SET {','.join(parts)} WHERE id={tid}")
        return jsonify({"ok":True})
    except Exception as e:
        return jsonify({"hata":str(e)}), 500

# Tedarikçiler
@app.route("/api/satinalma/tedarikciler", methods=["GET"])
@giris_gerekli
def tedarikci_listesi():
    try:
        rows = qry("SELECT id,firma_adi,iletisim_kisi,telefon,email,malzeme_grubu,notlar,aktif FROM satinalma_tedarikci ORDER BY firma_adi")
        return jsonify(rows)
    except Exception as e:
        return jsonify({"hata":str(e)}), 500

@app.route("/api/satinalma/tedarikciler", methods=["POST"])
@giris_gerekli
def tedarikci_ekle():
    try:
        d = request.get_json() or {}
        kullanici = session.get('kullanici','sistem')
        run_exec(f"""INSERT INTO satinalma_tedarikci
            (firma_adi,iletisim_kisi,telefon,email,malzeme_grubu,adres,notlar,olusturan)
            VALUES ({q(d.get('firma_adi',''))},{q(d.get('iletisim_kisi',''))},
            {q(d.get('telefon',''))},{q(d.get('email',''))},
            {q(d.get('malzeme_grubu',''))},{q(d.get('adres',''))},
            {q(d.get('notlar',''))},{q(kullanici)})""")
        return jsonify({"ok":True})
    except Exception as e:
        return jsonify({"hata":str(e)}), 500

@app.route("/api/satinalma/tedarikciler/<int:tid>", methods=["PATCH"])
@giris_gerekli
def tedarikci_guncelle(tid):
    try:
        d = request.get_json() or {}
        parts = []
        for f in ('firma_adi','iletisim_kisi','telefon','email','malzeme_grubu','adres','notlar'):
            if f in d: parts.append(f"{f}={q(d[f])}")
        if 'aktif' in d: parts.append(f"aktif={1 if d['aktif'] else 0}")
        if not parts: return jsonify({"hata":"Alan yok"}), 400
        run_exec(f"UPDATE satinalma_tedarikci SET {','.join(parts)} WHERE id={tid}")
        return jsonify({"ok":True})
    except Exception as e:
        return jsonify({"hata":str(e)}), 500

# Satın alma siparişleri
@app.route("/api/satinalma/siparisler", methods=["GET"])
@giris_gerekli
def satinalma_siparis_listesi():
    try:
        rows = qry("""SELECT s.id,s.talep_id,s.malzeme_tanim,s.miktar,s.birim,
            s.birim_fiyat,s.toplam_tutar,s.para_birimi,
            CONVERT(varchar,s.siparis_tarihi,23) AS siparis_tarihi,
            CONVERT(varchar,s.teslim_tarihi,23) AS teslim_tarihi,
            s.durum,s.notlar,s.olusturan,
            CONVERT(varchar,s.olusturma_tar,20) AS olusturma_tar,
            td.firma_adi AS tedarikci_adi
            FROM satinalma_siparis s
            LEFT JOIN satinalma_tedarikci td ON s.tedarikci_id=td.id
            ORDER BY s.olusturma_tar DESC""")
        return jsonify(rows)
    except Exception as e:
        return jsonify({"hata":str(e)}), 500

@app.route("/api/satinalma/siparisler", methods=["POST"])
@giris_gerekli
def satinalma_siparis_ekle():
    try:
        d = request.get_json() or {}
        kullanici = session.get('kullanici','sistem')
        st = d.get('siparis_tarihi')
        tt = d.get('teslim_tarihi')
        miktar = d.get('miktar') or 'NULL'
        bp = d.get('birim_fiyat') or 'NULL'
        top = d.get('toplam_tutar') or 'NULL'
        run_exec(f"""INSERT INTO satinalma_siparis
            (talep_id,tedarikci_id,malzeme_tanim,miktar,birim,birim_fiyat,
             toplam_tutar,para_birimi,siparis_tarihi,teslim_tarihi,notlar,olusturan)
            VALUES ({d.get('talep_id') or 'NULL'},{d.get('tedarikci_id') or 'NULL'},
            {q(d.get('malzeme_tanim',''))},{miktar},{q(d.get('birim','adet'))},
            {bp},{top},{q(d.get('para_birimi','TL'))},
            {'CAST('+q(st)+' AS DATE)' if st else 'NULL'},
            {'CAST('+q(tt)+' AS DATE)' if tt else 'NULL'},
            {q(d.get('notlar',''))},{q(kullanici)})""")
        return jsonify({"ok":True})
    except Exception as e:
        return jsonify({"hata":str(e)}), 500

@app.route("/api/satinalma/siparisler/<int:sid>", methods=["PATCH"])
@giris_gerekli
def satinalma_siparis_guncelle(sid):
    try:
        d = request.get_json() or {}
        parts = []
        for f in ('durum','notlar','malzeme_tanim','birim','para_birimi'):
            if f in d: parts.append(f"{f}={q(d[f])}")
        for f in ('miktar','birim_fiyat','toplam_tutar','tedarikci_id'):
            if f in d and d[f] is not None: parts.append(f"{f}={d[f]}")
        if 'teslim_tarihi' in d:
            parts.append(f"teslim_tarihi={'CAST('+q(d['teslim_tarihi'])+' AS DATE)' if d['teslim_tarihi'] else 'NULL'}")
        if not parts: return jsonify({"hata":"Alan yok"}), 400
        parts.append("guncelleme_tar=GETDATE()")
        run_exec(f"UPDATE satinalma_siparis SET {','.join(parts)} WHERE id={sid}")
        return jsonify({"ok":True})
    except Exception as e:
        return jsonify({"hata":str(e)}), 500

def init_grafik_table():
    sql="""IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='grafik_is_kaydi' AND xtype='U')
CREATE TABLE grafik_is_kaydi (
  id               INT IDENTITY(1,1) PRIMARY KEY,
  siparis_id       INT,
  baslik           NVARCHAR(200) NOT NULL,
  aciklama         NVARCHAR(MAX),
  gonderim_yeri    NVARCHAR(30) NOT NULL DEFAULT 'ic_uretim',
  tedarikci_adi    NVARCHAR(200),
  gonderi_tarihi   DATE,
  teslim_beklenen  DATE,
  durum            NVARCHAR(30) NOT NULL DEFAULT 'bekliyor',
  notlar           NVARCHAR(MAX),
  resim_yolu       NVARCHAR(500),
  atanan           NVARCHAR(100),
  olusturan        NVARCHAR(100),
  olusturma_tar    DATETIME NOT NULL DEFAULT GETDATE(),
  guncelleme_tar   DATETIME NOT NULL DEFAULT GETDATE()
)"""
    try:
        run_exec(sql)
    except Exception as e:
        print(f"Tablo uyarisi: {e}")

def init_numune_table():
    sql="""IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='numune_takip' AND xtype='U')
CREATE TABLE numune_takip (
  id                  INT IDENTITY(1,1) PRIMARY KEY,
  siparis_id          INT,
  musteri_adi         NVARCHAR(200),
  numune_tipi         NVARCHAR(20) NOT NULL DEFAULT 'PP',
  aciklama            NVARCHAR(MAX),
  gonderim_sekli      NVARCHAR(30) NOT NULL DEFAULT 'sofor',
  gonderim_tarihi     DATE,
  -- Beden/Size bilgileri
  size_bilgi          NVARCHAR(200),
  asorti_mi           BIT NOT NULL DEFAULT 0,
  asorti_bedenler     NVARCHAR(200),
  yapilan_adet        INT,
  gonderilen_adet     INT,
  gonderilen_size     NVARCHAR(200),
  -- Dijital baskı
  dijital_baski       BIT NOT NULL DEFAULT 0,
  dijital_detay       NVARCHAR(MAX),
  -- Onaylar
  grafik_onay         NVARCHAR(20) NOT NULL DEFAULT 'bekliyor',
  grafik_onay_tar     DATE,
  gm_onay             NVARCHAR(20) NOT NULL DEFAULT 'bekliyor',
  gm_onay_tar         DATE,
  musteri_onay        NVARCHAR(20) NOT NULL DEFAULT 'bekliyor',
  musteri_onay_tar    DATE,
  durum               NVARCHAR(30) NOT NULL DEFAULT 'hazirlaniyor',
  notlar              NVARCHAR(MAX),
  olusturan           NVARCHAR(100),
  olusturma_tar       DATETIME NOT NULL DEFAULT GETDATE(),
  guncelleme_tar      DATETIME NOT NULL DEFAULT GETDATE()
)"""
    try:
        run_exec(sql)
        # Mevcut tabloya yeni kolonlar ekle (varsa atla)
        for col_sql in [
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('numune_takip') AND name='size_bilgi') ALTER TABLE numune_takip ADD size_bilgi NVARCHAR(200)",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('numune_takip') AND name='asorti_mi') ALTER TABLE numune_takip ADD asorti_mi BIT NOT NULL DEFAULT 0",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('numune_takip') AND name='asorti_bedenler') ALTER TABLE numune_takip ADD asorti_bedenler NVARCHAR(200)",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('numune_takip') AND name='yapilan_adet') ALTER TABLE numune_takip ADD yapilan_adet INT",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('numune_takip') AND name='gonderilen_adet') ALTER TABLE numune_takip ADD gonderilen_adet INT",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('numune_takip') AND name='gonderilen_size') ALTER TABLE numune_takip ADD gonderilen_size NVARCHAR(200)",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('numune_takip') AND name='dijital_baski') ALTER TABLE numune_takip ADD dijital_baski BIT NOT NULL DEFAULT 0",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('numune_takip') AND name='dijital_detay') ALTER TABLE numune_takip ADD dijital_detay NVARCHAR(MAX)",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('numune_takip') AND name='hazirlayan') ALTER TABLE numune_takip ADD hazirlayan NVARCHAR(200)",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('numune_takip') AND name='gorsel_yolu') ALTER TABLE numune_takip ADD gorsel_yolu NVARCHAR(500)",
            "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('numune_takip') AND name='kalite_onay') ALTER TABLE numune_takip ADD kalite_onay NVARCHAR(20) NOT NULL DEFAULT 'bekliyor'",
        ]:
            try: run_exec(col_sql)
            except: pass
    except Exception as e:
        print(f"Numune tablo uyarisi: {e}")

@app.route("/api/model/cari")
@giris_gerekli
def model_cari():
    """ModelKod -> CariAdi, SipNo, BelgeNo lookup (Korgun DB)"""
    try:
        rows, err = run_query(
            """SELECT sh.SKOD AS ModelKod,
                      ISNULL(cm.Tanim, sk.CariKod) AS CariAdi,
                      sk.SipNo,
                      ISNULL(sk.BelgeNo,'') AS BelgeNo
               FROM Siparis_Kay sk
               INNER JOIN Siparis_Har sh ON sk.SipNo = sh.SipNo
               LEFT JOIN Cari_M cm ON sk.CariKod = cm.CariKod
               WHERE sk.SipTip IN ('A','S','ST')
                 AND sk.Durum NOT IN ('I','X')""",
            server=KORGUN_SERVER, database="solarizdb",
            uid=KORGUN_UID, pwd=KORGUN_PWD
        )
        if err:
            return jsonify({"hata": err}), 500
        return jsonify(rows or [])
    except Exception as e:
        return jsonify({"hata": str(e)}), 500

@app.route("/api/proxy/korgun/<path:endpoint>")
@giris_gerekli
def korgun_proxy(endpoint):
    import urllib.request as ur
    try:
        args = request.query_string.decode('utf-8')
        url = f"http://127.0.0.1:5056/api/{endpoint}"
        if args:
            url += "?" + args
        req = ur.Request(url)
        resp = ur.urlopen(req, timeout=15)
        data = resp.read()
        return app.response_class(data, mimetype='application/json')
    except Exception as e:
        return jsonify({"hata": str(e)}), 500
@app.route("/api/grafik/isler", methods=["GET"])
@giris_gerekli
def grafik_isler_listesi():
    try:
        rows=qry("""SELECT gi.id,gi.siparis_id,gi.baslik,gi.aciklama,gi.gonderim_yeri,gi.tedarikci_adi,
            CONVERT(varchar,gi.gonderi_tarihi,23) AS gonderi_tarihi,
            CONVERT(varchar,gi.teslim_beklenen,23) AS teslim_beklenen,
            gi.durum,gi.notlar,gi.resim_yolu,gi.atanan,gi.olusturan,
            CONVERT(varchar,gi.olusturma_tar,20) AS olusturma_tar,
            CONVERT(varchar,gi.guncelleme_tar,20) AS guncelleme_tar,
            ps.korgun_sip_no,ps.model_kod,ps.cari_tanim AS musteri_adi,
            DATEDIFF(day,GETDATE(),gi.teslim_beklenen) AS kalan_gun
            FROM grafik_is_kaydi gi
            LEFT JOIN planlama_siparis ps ON gi.siparis_id=ps.id
            ORDER BY gi.olusturma_tar DESC""")
        return jsonify(rows)
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/grafik/isler", methods=["POST"])
@giris_gerekli
def grafik_is_ekle():
    try:
        d=request.get_json() or {}
        kullanici=session.get('kullanici','sistem')
        rol=session.get('rol','')
        # Grafik rolü sadece kendi kaydını girebilir, atanan alanını set edemez
        atanan=q(d.get('atanan','')) if rol in ('admin','planlama') else q(kullanici)
        gonderi=f"CAST({q(d.get('gonderi_tarihi'))} AS DATE)" if d.get('gonderi_tarihi') else 'NULL'
        teslim=f"CAST({q(d.get('teslim_beklenen'))} AS DATE)" if d.get('teslim_beklenen') else 'NULL'
        siparis_id=d.get('siparis_id') or 'NULL'
        run_exec(f"""INSERT INTO grafik_is_kaydi
            (siparis_id,baslik,aciklama,gonderim_yeri,tedarikci_adi,gonderi_tarihi,teslim_beklenen,durum,notlar,atanan,olusturan)
            VALUES ({siparis_id},{q(d.get('baslik',''))},{q(d.get('aciklama',''))},
            {q(d.get('gonderim_yeri','ic_uretim'))},{q(d.get('tedarikci_adi',''))},
            {gonderi},{teslim},N'bekliyor',{q(d.get('notlar',''))},{atanan},{q(kullanici)})""")
        rows=qry("SELECT TOP 1 id FROM grafik_is_kaydi ORDER BY id DESC")
        return jsonify({"ok":True,"id":rows[0]['id'] if rows else None})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/grafik/isler/<int:gid>", methods=["PATCH"])
@giris_gerekli
def grafik_is_guncelle(gid):
    try:
        d=request.get_json() or {}
        rol=session.get('rol','')
        kullanici=session.get('kullanici','')
        # Grafik rolü sadece kendi kaydını güncelleyebilir
        if rol=='grafik':
            rows=qry(f"SELECT olusturan FROM grafik_is_kaydi WHERE id={gid}")
            if rows and rows[0].get('olusturan')!=kullanici:
                return jsonify({"hata":"Yetki yok"}),403
        parts=[]
        for field in ('baslik','aciklama','gonderim_yeri','tedarikci_adi','durum','notlar','atanan'):
            if field in d:
                parts.append(f"{field}={q(d[field])}")
        if 'gonderi_tarihi' in d and d['gonderi_tarihi']:
            parts.append(f"gonderi_tarihi=CAST({q(d['gonderi_tarihi'])} AS DATE)")
        if 'teslim_beklenen' in d and d['teslim_beklenen']:
            parts.append(f"teslim_beklenen=CAST({q(d['teslim_beklenen'])} AS DATE)")
        if not parts:
            return jsonify({"hata":"Alan yok"}),400
        parts.append("guncelleme_tar=GETDATE()")
        run_exec(f"UPDATE grafik_is_kaydi SET {','.join(parts)} WHERE id={gid}")
        return jsonify({"ok":True})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/grafik/isler/<int:gid>/resim", methods=["POST"])
@giris_gerekli
def grafik_resim_yukle(gid):
    try:
        if 'resim' not in request.files:
            return jsonify({"hata":"Dosya yok"}),400
        f=request.files['resim']
        ext=f.filename.rsplit('.',1)[-1].lower() if '.' in f.filename else ''
        if ext not in ALLOWED_EXT:
            return jsonify({"hata":"Geçersiz dosya tipi"}),400
        fname=f"{gid}_{uuid.uuid4().hex[:8]}.{ext}"
        fpath=os.path.join(UPLOAD_FOLDER,fname)
        f.save(fpath)
        run_exec(f"UPDATE grafik_is_kaydi SET resim_yolu={q(fname)},guncelleme_tar=GETDATE() WHERE id={gid}")
        return jsonify({"ok":True,"dosya":fname})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/grafik/resim/<fname>")
@giris_gerekli
def grafik_resim_goster(fname):
    safe=secure_filename(fname)
    return send_from_directory(UPLOAD_FOLDER, safe)


@app.route("/api/numune", methods=["GET"])
@giris_gerekli
def numune_listesi():
    try:
        rows=qry("""SELECT n.id,n.siparis_id,n.musteri_adi,n.numune_tipi,n.aciklama,
            n.gonderim_sekli,CONVERT(varchar,n.gonderim_tarihi,23) AS gonderim_tarihi,
            ISNULL(n.size_bilgi,'') AS size_bilgi,
            ISNULL(n.asorti_mi,0) AS asorti_mi,
            ISNULL(n.asorti_bedenler,'') AS asorti_bedenler,
            n.yapilan_adet,n.gonderilen_adet,
            ISNULL(n.gonderilen_size,'') AS gonderilen_size,
            ISNULL(n.dijital_baski,0) AS dijital_baski,
            ISNULL(n.dijital_detay,'') AS dijital_detay,
            ISNULL(n.hazirlayan,'') AS hazirlayan,
            ISNULL(n.gorsel_yolu,'') AS gorsel_yolu,
            ISNULL(n.kalite_onay,'bekliyor') AS kalite_onay,
            n.grafik_onay,CONVERT(varchar,n.grafik_onay_tar,23) AS grafik_onay_tar,
            n.gm_onay,CONVERT(varchar,n.gm_onay_tar,23) AS gm_onay_tar,
            n.musteri_onay,CONVERT(varchar,n.musteri_onay_tar,23) AS musteri_onay_tar,
            n.durum,n.notlar,n.olusturan,
            CONVERT(varchar,n.olusturma_tar,20) AS olusturma_tar,
            ps.korgun_sip_no,ps.model_kod,ps.cari_tanim AS musteri_sip,
            DATEDIFF(day,n.olusturma_tar,GETDATE()) AS gecen_gun
            FROM numune_takip n
            LEFT JOIN planlama_siparis ps ON n.siparis_id=ps.id
            ORDER BY n.olusturma_tar DESC""")
        return jsonify(rows)
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/numune", methods=["POST"])
@giris_gerekli
def numune_ekle():
    try:
        d=request.get_json() or {}
        kullanici=session.get('kullanici','sistem')
        siparis_id=d.get('siparis_id') or 'NULL'
        gonderim=f"CAST({q(d.get('gonderim_tarihi'))} AS DATE)" if d.get('gonderim_tarihi') else 'NULL'
        asorti=1 if d.get('asorti_mi') else 0
        dijital=1 if d.get('dijital_baski') else 0
        yapilan=d.get('yapilan_adet') or 'NULL'
        gonderilen=d.get('gonderilen_adet') or 'NULL'
        run_exec(f"""INSERT INTO numune_takip
            (siparis_id,musteri_adi,numune_tipi,aciklama,gonderim_sekli,gonderim_tarihi,
            size_bilgi,asorti_mi,asorti_bedenler,yapilan_adet,gonderilen_adet,gonderilen_size,
            dijital_baski,dijital_detay,hazirlayan,notlar,olusturan)
            VALUES ({siparis_id},{q(d.get('musteri_adi',''))},{q(d.get('numune_tipi','PP'))},
            {q(d.get('aciklama',''))},{q(d.get('gonderim_sekli','sofor'))},{gonderim},
            {q(d.get('size_bilgi',''))},{asorti},{q(d.get('asorti_bedenler',''))},
            {yapilan},{gonderilen},{q(d.get('gonderilen_size',''))},
            {dijital},{q(d.get('dijital_detay',''))},
            {q(d.get('hazirlayan',''))},
            {q(d.get('notlar',''))},{q(kullanici)})""")
        rows=qry("SELECT TOP 1 id FROM numune_takip ORDER BY id DESC")
        return jsonify({"ok":True,"id":rows[0]['id'] if rows else None})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/numune/<int:nid>/gorsel", methods=["POST"])
@giris_gerekli
def numune_gorsel_yukle(nid):
    try:
        f = request.files.get('gorsel')
        if not f: return jsonify({"hata":"Dosya yok"}),400
        klasor = r"D:\Firma_Ozel\adem\planlama cps sistemi\numune_gorseller"
        import os as _os2
        _os2.makedirs(klasor, exist_ok=True)
        ext = f.filename.rsplit('.',1)[-1].lower() if '.' in f.filename else 'jpg'
        fname = f"numune_{nid}_{int(__import__('time').time())}.{ext}"
        f.save(_os2.path.join(klasor, fname))
        run_exec(f"UPDATE numune_takip SET gorsel_yolu={q(fname)} WHERE id={nid}")
        return jsonify({"ok":True,"fname":fname})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/numune/gorsel/<fname>")
@giris_gerekli
def numune_gorsel_goster(fname):
    klasor = r"D:\Firma_Ozel\adem\planlama cps sistemi\numune_gorseller"
    return send_from_directory(klasor, fname)

@app.route("/api/numune/<int:nid>", methods=["PATCH"])
@giris_gerekli
def numune_guncelle(nid):
    try:
        d=request.get_json() or {}
        parts=[]
        for field in ('musteri_adi','numune_tipi','aciklama','gonderim_sekli','durum','notlar',
                      'musteri_onay','grafik_onay','gm_onay','kalite_onay','size_bilgi','asorti_bedenler',
                      'gonderilen_size','dijital_detay'):
            if field in d:
                parts.append(f"{field}={q(d[field])}")
        for intfield in ('yapilan_adet','gonderilen_adet'):
            if intfield in d and d[intfield] is not None:
                parts.append(f"{intfield}={d[intfield]}")
        for bitfield in ('asorti_mi','dijital_baski'):
            if bitfield in d:
                parts.append(f"{bitfield}={1 if d[bitfield] else 0}")
        if 'gonderim_tarihi' in d and d['gonderim_tarihi']:
            parts.append(f"gonderim_tarihi=CAST({q(d['gonderim_tarihi'])} AS DATE)")
        if 'musteri_onay' in d:
            parts.append(f"musteri_onay_tar=CAST(GETDATE() AS DATE)")
        if 'grafik_onay' in d:
            parts.append(f"grafik_onay_tar=CAST(GETDATE() AS DATE)")
        if 'gm_onay' in d:
            parts.append(f"gm_onay_tar=CAST(GETDATE() AS DATE)")
        if not parts:
            return jsonify({"hata":"Alan yok"}),400
        parts.append("guncelleme_tar=GETDATE()")
        run_exec(f"UPDATE numune_takip SET {','.join(parts)} WHERE id={nid}")
        return jsonify({"ok":True})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

# ═══════════════════════════════════════════════════════════
# GRAFİK DOSYA / REVİZYON SİSTEMİ
# ═══════════════════════════════════════════════════════════

def init_grafik_dosya_table():
    sqls = [
        """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='grafik_dosya' AND xtype='U')
CREATE TABLE grafik_dosya (
  id              INT IDENTITY(1,1) PRIMARY KEY,
  is_id           INT NOT NULL,
  versiyon        NVARCHAR(10) NOT NULL DEFAULT 'v1',
  dosya_adi       NVARCHAR(300) NOT NULL,
  dosya_yolu      NVARCHAR(500) NOT NULL,
  dosya_tipi      NVARCHAR(50),
  kaynak          NVARCHAR(50) NOT NULL DEFAULT 'ic',
  aciklama        NVARCHAR(MAX),
  onaylayan_kisi  NVARCHAR(200),
  onaylayan_firma NVARCHAR(200),
  onay_tarihi     DATE,
  onay_durumu     NVARCHAR(30) NOT NULL DEFAULT 'bekliyor',
  olusturan       NVARCHAR(100),
  olusturma_tar   DATETIME NOT NULL DEFAULT GETDATE()
)""",
        """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='grafik_gorev' AND xtype='U')
CREATE TABLE grafik_gorev (
  id           INT IDENTITY(1,1) PRIMARY KEY,
  is_id        INT NOT NULL,
  gorev_metni  NVARCHAR(500) NOT NULL,
  atanan       NVARCHAR(100),
  tamamlandi   BIT NOT NULL DEFAULT 0,
  olusturan    NVARCHAR(100),
  olusturma_tar DATETIME NOT NULL DEFAULT GETDATE()
)""",
    ]
    for sql in sqls:
        try: run_exec(sql)
        except Exception as e: print(f"grafik_dosya tablo: {e}")

import os as _os

UPLOAD_DIR = r"D:\Firma_Ozel\adem\planlama cps sistemi\grafik_dosyalar"

def ensure_upload_dir():
    if not _os.path.exists(UPLOAD_DIR):
        _os.makedirs(UPLOAD_DIR)

@app.route("/api/grafik/isler/<int:is_id>/dosyalar", methods=["GET"])
@giris_gerekli
def grafik_dosya_listesi(is_id):
    try:
        rows = qry(f"""SELECT id,versiyon,dosya_adi,dosya_yolu,dosya_tipi,kaynak,aciklama,
            onaylayan_kisi,onaylayan_firma,
            CONVERT(varchar,onay_tarihi,23) AS onay_tarihi,
            onay_durumu,olusturan,
            CONVERT(varchar,olusturma_tar,20) AS olusturma_tar
            FROM grafik_dosya WHERE is_id={is_id} ORDER BY olusturma_tar DESC""")
        return jsonify(rows)
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/grafik/isler/<int:is_id>/dosya_yukle", methods=["POST"])
@giris_gerekli
def grafik_dosya_yukle(is_id):
    try:
        ensure_upload_dir()
        kullanici = session.get('kullanici','sistem')
        f = request.files.get('dosya')
        if not f:
            return jsonify({"hata":"Dosya yok"}),400

        # Versiyon belirle
        mevcut = qry(f"SELECT COUNT(*) AS cnt FROM grafik_dosya WHERE is_id={is_id}")
        ver_no = (mevcut[0]['cnt'] if mevcut else 0) + 1
        versiyon = f"v{ver_no}"

        ext = _os.path.splitext(f.filename)[1].lower()
        guvli_ad = f"is{is_id}_{versiyon}_{f.filename.replace(' ','_')}"
        yol = _os.path.join(UPLOAD_DIR, guvli_ad)
        f.save(yol)

        kaynak = request.form.get('kaynak','ic')
        aciklama = request.form.get('aciklama','')
        onaylayan_kisi = request.form.get('onaylayan_kisi','')
        onaylayan_firma = request.form.get('onaylayan_firma','')

        run_exec(f"""INSERT INTO grafik_dosya
            (is_id,versiyon,dosya_adi,dosya_yolu,dosya_tipi,kaynak,aciklama,
             onaylayan_kisi,onaylayan_firma,olusturan)
            VALUES ({is_id},{q(versiyon)},{q(f.filename)},{q(guvli_ad)},{q(ext)},
            {q(kaynak)},{q(aciklama)},{q(onaylayan_kisi)},{q(onaylayan_firma)},{q(kullanici)})""")
        rows = qry("SELECT TOP 1 id FROM grafik_dosya ORDER BY id DESC")
        return jsonify({"ok":True,"id":rows[0]['id'] if rows else None,"versiyon":versiyon})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/grafik/dosya/<int:did>/onay", methods=["PATCH"])
@giris_gerekli
def grafik_dosya_onay(did):
    try:
        d = request.get_json() or {}
        durum = d.get('onay_durumu','bekliyor')
        run_exec(f"""UPDATE grafik_dosya SET
            onay_durumu={q(durum)},
            onay_tarihi=CAST(GETDATE() AS DATE),
            onaylayan_kisi={q(d.get('onaylayan_kisi',''))},
            onaylayan_firma={q(d.get('onaylayan_firma',''))}
            WHERE id={did}""")
        return jsonify({"ok":True})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/grafik/dosya/<fname>")
@giris_gerekli
def grafik_dosya_indir(fname):
    ext = fname.rsplit('.',1)[-1].lower() if '.' in fname else ''
    if ext == 'pdf':
        from flask import make_response
        import os as _os2
        yol = _os2.path.join(UPLOAD_DIR, fname)
        if not _os2.path.exists(yol):
            return "Dosya bulunamadı", 404
        with open(yol, 'rb') as f:
            data = f.read()
        resp = make_response(data)
        resp.headers['Content-Type'] = 'application/pdf'
        resp.headers['Content-Disposition'] = f'inline; filename="{fname}"'
        return resp
    return send_from_directory(UPLOAD_DIR, fname)

# Görevler (checklist)
@app.route("/api/grafik/isler/<int:is_id>/gorevler", methods=["GET"])
@giris_gerekli
def grafik_gorev_listesi(is_id):
    try:
        rows = qry(f"""SELECT id,gorev_metni,atanan,tamamlandi,olusturan,
            CONVERT(varchar,olusturma_tar,20) AS olusturma_tar
            FROM grafik_gorev WHERE is_id={is_id} ORDER BY olusturma_tar""")
        return jsonify(rows)
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/grafik/isler/<int:is_id>/gorevler", methods=["POST"])
@giris_gerekli
def grafik_gorev_ekle(is_id):
    try:
        d = request.get_json() or {}
        kullanici = session.get('kullanici','sistem')
        run_exec(f"""INSERT INTO grafik_gorev (is_id,gorev_metni,atanan,olusturan)
            VALUES ({is_id},{q(d.get('gorev_metni',''))},{q(d.get('atanan',''))},{q(kullanici)})""")
        rows = qry("SELECT TOP 1 id FROM grafik_gorev ORDER BY id DESC")
        return jsonify({"ok":True,"id":rows[0]['id'] if rows else None})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/grafik/gorev/<int:gid>", methods=["PATCH"])
@giris_gerekli
def grafik_gorev_guncelle(gid):
    try:
        d = request.get_json() or {}
        parts = []
        if 'tamamlandi' in d:
            parts.append(f"tamamlandi={1 if d['tamamlandi'] else 0}")
        if 'gorev_metni' in d:
            parts.append(f"gorev_metni={q(d['gorev_metni'])}")
        if not parts:
            return jsonify({"hata":"Alan yok"}),400
        run_exec(f"UPDATE grafik_gorev SET {','.join(parts)} WHERE id={gid}")
        return jsonify({"ok":True})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/grafik/gorev/<int:gid>", methods=["DELETE"])
@giris_gerekli
def grafik_gorev_sil(gid):
    try:
        run_exec(f"DELETE FROM grafik_gorev WHERE id={gid}")
        return jsonify({"ok":True})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

# ═══════════════════════════════════════════════════════════
# KALİTE KONTROL
# ═══════════════════════════════════════════════════════════

def init_kalite_tables():
    sqls = [
        # AQL Inspection
        """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='kalite_aql' AND xtype='U')
CREATE TABLE kalite_aql (
  id                  INT IDENTITY(1,1) PRIMARY KEY,
  rapor_no            NVARCHAR(50),
  siparis_id          INT,
  musteri             NVARCHAR(200),
  model_adi           NVARCHAR(200),
  siparis_no          NVARCHAR(100),
  renk_adi            NVARCHAR(100),
  renk_kodu           NVARCHAR(50),
  ozel_kod            NVARCHAR(50),
  asorti_aralik       NVARCHAR(100),
  sezon               NVARCHAR(50),
  vardola_tipi        NVARCHAR(100),
  patch_bilgi         NVARCHAR(200),
  talep_miktar        INT,
  bakilan_miktar      INT,
  aql_standart        NVARCHAR(10) NOT NULL DEFAULT '2.5',
  kritik_hata         INT NOT NULL DEFAULT 0,
  major_hata          INT NOT NULL DEFAULT 0,
  minor_hata          INT NOT NULL DEFAULT 0,
  solariz_sonuc       NVARCHAR(20) NOT NULL DEFAULT 'bekliyor',
  musteri_sonuc       NVARCHAR(20) NOT NULL DEFAULT 'bekliyor',
  kontrol_eden        NVARCHAR(200),
  kontrol_tarihi      DATE,
  lokasyon            NVARCHAR(200),
  musteri_qc_kisi     NVARCHAR(200),
  musteri_qc_firma    NVARCHAR(200),
  numune_foto_yolu    NVARCHAR(500),
  genel_notlar        NVARCHAR(MAX),
  olusturan           NVARCHAR(100),
  olusturma_tar       DATETIME NOT NULL DEFAULT GETDATE(),
  guncelleme_tar      DATETIME NOT NULL DEFAULT GETDATE()
)""",
        # Hata detayları
        """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='kalite_hata' AND xtype='U')
CREATE TABLE kalite_hata (
  id          INT IDENTITY(1,1) PRIMARY KEY,
  aql_id      INT NOT NULL,
  sinif       NVARCHAR(20) NOT NULL,
  hata_kodu   NVARCHAR(50),
  tanim       NVARCHAR(500),
  adet        INT NOT NULL DEFAULT 0,
  foto_yolu   NVARCHAR(500),
  olusturma_tar DATETIME NOT NULL DEFAULT GETDATE()
)""",
        # Müşteri QC ziyaretleri
        """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='kalite_musteri_qc' AND xtype='U')
CREATE TABLE kalite_musteri_qc (
  id             INT IDENTITY(1,1) PRIMARY KEY,
  musteri_firma  NVARCHAR(200) NOT NULL,
  qc_kisi        NVARCHAR(200),
  ziyaret_tarihi DATE,
  siparis_id     INT,
  siparis_bilgi  NVARCHAR(200),
  sonuc          NVARCHAR(30) NOT NULL DEFAULT 'bekliyor',
  genel_notlar   NVARCHAR(MAX),
  olusturan      NVARCHAR(100),
  olusturma_tar  DATETIME NOT NULL DEFAULT GETDATE()
)""",
        # Müşteri QC uyarıları
        """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='kalite_qc_uyari' AND xtype='U')
CREATE TABLE kalite_qc_uyari (
  id         INT IDENTITY(1,1) PRIMARY KEY,
  qc_id      INT NOT NULL,
  uyari_tipi NVARCHAR(30) NOT NULL DEFAULT 'uyari',
  uyari_metni NVARCHAR(MAX),
  takip_durumu NVARCHAR(30) NOT NULL DEFAULT 'bekliyor',
  olusturma_tar DATETIME NOT NULL DEFAULT GETDATE()
)""",
        # Rutin kontrol
        """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='kalite_rutin' AND xtype='U')
CREATE TABLE kalite_rutin (
  id            INT IDENTITY(1,1) PRIMARY KEY,
  asama_no      INT NOT NULL,
  asama_adi     NVARCHAR(100),
  siparis_bilgi NVARCHAR(200),
  kontrol_eden  NVARCHAR(100),
  sonuc         NVARCHAR(30) NOT NULL DEFAULT 'uygun',
  notlar        NVARCHAR(MAX),
  kontrol_tarihi DATE NOT NULL DEFAULT CAST(GETDATE() AS DATE),
  olusturan     NVARCHAR(100),
  olusturma_tar DATETIME NOT NULL DEFAULT GETDATE()
)""",
        # Lisans takibi
        """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='kalite_lisans' AND xtype='U')
CREATE TABLE kalite_lisans (
  id                INT IDENTITY(1,1) PRIMARY KEY,
  marka_adi         NVARCHAR(200) NOT NULL,
  lisansci_firma    NVARCHAR(200),
  sozlesme_no       NVARCHAR(100),
  baslangic_tarihi  DATE,
  bitis_tarihi      DATE NOT NULL,
  karakterler       NVARCHAR(MAX),
  belge_yolu        NVARCHAR(500),
  notlar            NVARCHAR(MAX),
  olusturan         NVARCHAR(100),
  olusturma_tar     DATETIME NOT NULL DEFAULT GETDATE()
)""",
    ]
    for sql in sqls:
        try: run_exec(sql)
        except Exception as e: print(f"kalite tablo: {e}")
    # Mevcut tabloya yeni kolon ekle (migration)
    migrations = [
        "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('kalite_aql') AND name='gorsel_yolu') ALTER TABLE kalite_aql ADD gorsel_yolu NVARCHAR(500)",
        "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('kalite_aql') AND name='musteri_inspektor_adi') ALTER TABLE kalite_aql ADD musteri_inspektor_adi NVARCHAR(200)",
        "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('kalite_aql') AND name='musteri_inspektor_firma') ALTER TABLE kalite_aql ADD musteri_inspektor_firma NVARCHAR(200)",
        "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('kalite_aql') AND name='musteri_inspektor_sonuc') ALTER TABLE kalite_aql ADD musteri_inspektor_sonuc NVARCHAR(30)",
        "IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id=OBJECT_ID('kalite_aql') AND name='musteri_inspektor_notu') ALTER TABLE kalite_aql ADD musteri_inspektor_notu NVARCHAR(MAX)",
    ]
    for sql in migrations:
        try: run_exec(sql)
        except Exception as e: print(f"kalite migration: {e}")

KALITE_UPLOAD_DIR = r"D:\Firma_Ozel\adem\planlama cps sistemi\kalite_dosyalar"

def ensure_kalite_dir():
    if not _os.path.exists(KALITE_UPLOAD_DIR):
        _os.makedirs(KALITE_UPLOAD_DIR)

# AQL CRUD
@app.route("/api/kalite/aql", methods=["GET"])
@giris_gerekli
def kalite_aql_listesi():
    try:
        rows = qry("""SELECT a.id,a.rapor_no,a.musteri,a.model_adi,a.siparis_no,
            a.renk_adi,a.renk_kodu,a.asorti_aralik,a.sezon,a.vardola_tipi,a.patch_bilgi,
            a.talep_miktar,a.bakilan_miktar,a.aql_standart,
            a.kritik_hata,a.major_hata,a.minor_hata,
            a.solariz_sonuc,a.musteri_sonuc,a.kontrol_eden,
            CONVERT(varchar,a.kontrol_tarihi,23) AS kontrol_tarihi,
            a.lokasyon,a.musteri_qc_kisi,a.musteri_qc_firma,
            a.numune_foto_yolu,a.genel_notlar,a.olusturan,
            CONVERT(varchar,a.olusturma_tar,20) AS olusturma_tar,
            ps.korgun_sip_no, ps.model_kod,
            a.gorsel_yolu, a.musteri_inspektor_adi, a.musteri_inspektor_firma,
            a.musteri_inspektor_sonuc, a.musteri_inspektor_notu
            FROM kalite_aql a
            LEFT JOIN planlama_siparis ps ON a.siparis_id=ps.id
            ORDER BY a.olusturma_tar DESC""")
        return jsonify(rows)
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/kalite/aql", methods=["POST"])
@giris_gerekli
def kalite_aql_ekle():
    try:
        d = request.get_json() or {}
        kullanici = session.get('kullanici','sistem')
        kt = d.get('kontrol_tarihi')
        run_exec(f"""INSERT INTO kalite_aql
            (rapor_no,siparis_id,musteri,model_adi,siparis_no,renk_adi,renk_kodu,ozel_kod,
             asorti_aralik,sezon,vardola_tipi,patch_bilgi,talep_miktar,bakilan_miktar,
             aql_standart,kritik_hata,major_hata,minor_hata,
             solariz_sonuc,kontrol_eden,kontrol_tarihi,
             musteri_inspektor_adi,musteri_inspektor_firma,
             musteri_inspektor_sonuc,musteri_inspektor_notu,
             genel_notlar,olusturan)
            VALUES (
            {q(d.get('rapor_no',''))},{d.get('siparis_id') or 'NULL'},
            {q(d.get('musteri',''))},{q(d.get('model_adi',''))},{q(d.get('siparis_no',''))},
            {q(d.get('renk_adi',''))},{q(d.get('renk_kodu',''))},{q(d.get('ozel_kod',''))},
            {q(d.get('asorti_aralik',''))},{q(d.get('sezon',''))},
            {q(d.get('vardola_tipi',''))},{q(d.get('patch_bilgi',''))},
            {d.get('talep_miktar') or 0},{d.get('bakilan_miktar') or 0},
            {q(d.get('aql_standart','2.5'))},
            {d.get('kritik_hata') or 0},{d.get('major_hata') or 0},{d.get('minor_hata') or 0},
            {q(d.get('solariz_sonuc','bekliyor'))},
            {q(d.get('kontrol_eden',''))},
            {'CAST('+q(kt)+' AS DATE)' if kt else 'CAST(GETDATE() AS DATE)'},
            {q(d.get('musteri_inspektor_adi',''))},{q(d.get('musteri_inspektor_firma',''))},
            {q(d.get('musteri_inspektor_sonuc',''))},{q(d.get('musteri_inspektor_notu',''))},
            {q(d.get('genel_notlar',''))},{q(kullanici)})""")
        rows = qry("SELECT TOP 1 id FROM kalite_aql ORDER BY id DESC")
        new_id = rows[0]['id'] if rows else None
        # Hata satırlarını ekle
        for h in d.get('hatalar',[]):
            run_exec(f"""INSERT INTO kalite_hata (aql_id,sinif,hata_kodu,tanim,adet)
                VALUES ({new_id},{q(h.get('sinif','Minor'))},{q(h.get('hata_kodu',''))},
                {q(h.get('tanim',''))},{h.get('adet') or 0})""")
        return jsonify({"ok":True,"id":new_id})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/kalite/aql/<int:aid>/gorsel", methods=["POST"])
@giris_gerekli
def kalite_aql_gorsel(aid):
    try:
        ensure_kalite_dir()
        f = request.files.get('gorsel')
        if not f: return jsonify({"hata":"Dosya yok"}),400
        ext = f.filename.rsplit('.',1)[-1].lower() if '.' in f.filename else 'jpg'
        fname = f"aql_{aid}_{int(__import__('time').time())}.{ext}"
        f.save(_os.path.join(KALITE_UPLOAD_DIR, fname))
        run_exec(f"UPDATE kalite_aql SET gorsel_yolu={q(fname)} WHERE id={aid}")
        return jsonify({"ok":True,"fname":fname})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/kalite/aql/<int:aid>", methods=["PATCH"])
@giris_gerekli
def kalite_aql_guncelle(aid):
    try:
        d = request.get_json() or {}
        parts = []
        for f in ('rapor_no','musteri','model_adi','siparis_no','renk_adi','renk_kodu',
                  'asorti_aralik','sezon','vardola_tipi','patch_bilgi','solariz_sonuc',
                  'musteri_sonuc','kontrol_eden','lokasyon','musteri_qc_kisi',
                  'musteri_qc_firma','genel_notlar','aql_standart'):
            if f in d: parts.append(f"{f}={q(d[f])}")
        for f in ('talep_miktar','bakilan_miktar','kritik_hata','major_hata','minor_hata'):
            if f in d and d[f] is not None: parts.append(f"{f}={d[f]}")
        if 'kontrol_tarihi' in d and d['kontrol_tarihi']:
            parts.append(f"kontrol_tarihi=CAST({q(d['kontrol_tarihi'])} AS DATE)")
        if not parts:
            return jsonify({"hata":"Alan yok"}),400
        parts.append("guncelleme_tar=GETDATE()")
        run_exec(f"UPDATE kalite_aql SET {','.join(parts)} WHERE id={aid}")
        return jsonify({"ok":True})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/kalite/aql/<int:aid>/hatalar", methods=["GET"])
@giris_gerekli
def kalite_hata_listesi(aid):
    try:
        rows = qry(f"""SELECT id,sinif,hata_kodu,tanim,adet,foto_yolu,
            CONVERT(varchar,olusturma_tar,20) AS olusturma_tar
            FROM kalite_hata WHERE aql_id={aid} ORDER BY sinif,id""")
        return jsonify(rows)
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/kalite/hata/<int:hid>/foto", methods=["POST"])
@giris_gerekli
def kalite_hata_foto(hid):
    try:
        ensure_kalite_dir()
        f = request.files.get('foto')
        if not f: return jsonify({"hata":"Dosya yok"}),400
        fname = f"hata_{hid}_{f.filename.replace(' ','_')}"
        f.save(_os.path.join(KALITE_UPLOAD_DIR, fname))
        run_exec(f"UPDATE kalite_hata SET foto_yolu={q(fname)} WHERE id={hid}")
        return jsonify({"ok":True,"foto_yolu":fname})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/kalite/foto/<fname>")
@giris_gerekli
def kalite_foto_indir(fname):
    return send_from_directory(KALITE_UPLOAD_DIR, fname)

@app.route("/api/kalite/aql/<int:aid>/numune_foto", methods=["POST"])
@giris_gerekli
def kalite_numune_foto(aid):
    try:
        ensure_kalite_dir()
        f = request.files.get('foto')
        if not f: return jsonify({"hata":"Dosya yok"}),400
        fname = f"numune_aql{aid}_{f.filename.replace(' ','_')}"
        f.save(_os.path.join(KALITE_UPLOAD_DIR, fname))
        run_exec(f"UPDATE kalite_aql SET numune_foto_yolu={q(fname)} WHERE id={aid}")
        return jsonify({"ok":True,"foto_yolu":fname})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

# Müşteri QC
@app.route("/api/kalite/qc", methods=["GET"])
@giris_gerekli
def kalite_qc_listesi():
    try:
        rows = qry("""SELECT q.id,q.musteri_firma,q.qc_kisi,
            CONVERT(varchar,q.ziyaret_tarihi,23) AS ziyaret_tarihi,
            q.siparis_bilgi,q.sonuc,q.genel_notlar,q.olusturan,
            CONVERT(varchar,q.olusturma_tar,20) AS olusturma_tar
            FROM kalite_musteri_qc q ORDER BY q.ziyaret_tarihi DESC""")
        # uyarıları da ekle
        for r in rows:
            uyariler = qry(f"SELECT id,uyari_tipi,uyari_metni,takip_durumu FROM kalite_qc_uyari WHERE qc_id={r['id']} ORDER BY id")
            r['uyariler'] = uyariler
        return jsonify(rows)
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/kalite/qc", methods=["POST"])
@giris_gerekli
def kalite_qc_ekle():
    try:
        d = request.get_json() or {}
        kullanici = session.get('kullanici','sistem')
        zt = d.get('ziyaret_tarihi')
        run_exec(f"""INSERT INTO kalite_musteri_qc
            (musteri_firma,qc_kisi,ziyaret_tarihi,siparis_bilgi,sonuc,genel_notlar,olusturan)
            VALUES ({q(d.get('musteri_firma',''))},{q(d.get('qc_kisi',''))},
            {'CAST('+q(zt)+' AS DATE)' if zt else 'CAST(GETDATE() AS DATE)'},
            {q(d.get('siparis_bilgi',''))},{q(d.get('sonuc','bekliyor'))},
            {q(d.get('genel_notlar',''))},{q(kullanici)})""")
        rows = qry("SELECT TOP 1 id FROM kalite_musteri_qc ORDER BY id DESC")
        new_id = rows[0]['id'] if rows else None
        for u in d.get('uyariler',[]):
            run_exec(f"""INSERT INTO kalite_qc_uyari (qc_id,uyari_tipi,uyari_metni)
                VALUES ({new_id},{q(u.get('uyari_tipi','uyari'))},{q(u.get('uyari_metni',''))})""")
        return jsonify({"ok":True,"id":new_id})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/kalite/qc_uyari/<int:uid>", methods=["PATCH"])
@giris_gerekli
def kalite_qc_uyari_guncelle(uid):
    try:
        d = request.get_json() or {}
        run_exec(f"UPDATE kalite_qc_uyari SET takip_durumu={q(d.get('takip_durumu','bekliyor'))} WHERE id={uid}")
        return jsonify({"ok":True})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

# Rutin kontrol
@app.route("/api/kalite/rutin", methods=["GET"])
@giris_gerekli
def kalite_rutin_listesi():
    try:
        tarih = request.args.get('tarih', '')
        filtre = f"WHERE kontrol_tarihi=CAST({q(tarih)} AS DATE)" if tarih else "WHERE kontrol_tarihi=CAST(GETDATE() AS DATE)"
        rows = qry(f"""SELECT id,asama_no,asama_adi,siparis_bilgi,kontrol_eden,sonuc,notlar,
            CONVERT(varchar,kontrol_tarihi,23) AS kontrol_tarihi,olusturan,
            CONVERT(varchar,olusturma_tar,20) AS olusturma_tar
            FROM kalite_rutin {filtre} ORDER BY asama_no""")
        return jsonify(rows)
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/kalite/rutin", methods=["POST"])
@giris_gerekli
def kalite_rutin_ekle():
    try:
        d = request.get_json() or {}
        kullanici = session.get('kullanici','sistem')
        kt = d.get('kontrol_tarihi')
        run_exec(f"""INSERT INTO kalite_rutin
            (asama_no,asama_adi,siparis_bilgi,kontrol_eden,sonuc,notlar,kontrol_tarihi,olusturan)
            VALUES ({d.get('asama_no',1)},{q(d.get('asama_adi',''))},
            {q(d.get('siparis_bilgi',''))},{q(d.get('kontrol_eden',''))},
            {q(d.get('sonuc','uygun'))},{q(d.get('notlar',''))},
            {'CAST('+q(kt)+' AS DATE)' if kt else 'CAST(GETDATE() AS DATE)'},
            {q(kullanici)})""")
        return jsonify({"ok":True})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

# Lisans takibi
@app.route("/api/kalite/lisans", methods=["GET"])
@giris_gerekli
def kalite_lisans_listesi():
    try:
        rows = qry("""SELECT id,marka_adi,lisansci_firma,sozlesme_no,
            CONVERT(varchar,baslangic_tarihi,23) AS baslangic_tarihi,
            CONVERT(varchar,bitis_tarihi,23) AS bitis_tarihi,
            karakterler,belge_yolu,notlar,olusturan,
            DATEDIFF(day,GETDATE(),bitis_tarihi) AS kalan_gun
            FROM kalite_lisans ORDER BY bitis_tarihi""")
        return jsonify(rows)
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/kalite/lisans", methods=["POST"])
@giris_gerekli
def kalite_lisans_ekle():
    try:
        d = request.get_json() or {}
        kullanici = session.get('kullanici','sistem')
        bt = d.get('baslangic_tarihi')
        et = d.get('bitis_tarihi')
        run_exec(f"""INSERT INTO kalite_lisans
            (marka_adi,lisansci_firma,sozlesme_no,baslangic_tarihi,bitis_tarihi,
             karakterler,notlar,olusturan)
            VALUES ({q(d.get('marka_adi',''))},{q(d.get('lisansci_firma',''))},
            {q(d.get('sozlesme_no',''))},
            {'CAST('+q(bt)+' AS DATE)' if bt else 'NULL'},
            {'CAST('+q(et)+' AS DATE)' if et else 'NULL'},
            {q(d.get('karakterler',''))},{q(d.get('notlar',''))},{q(kullanici)})""")
        return jsonify({"ok":True})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/kalite/lisans/<int:lid>/belge", methods=["POST"])
@giris_gerekli
def kalite_lisans_belge(lid):
    try:
        ensure_kalite_dir()
        f = request.files.get('belge')
        if not f: return jsonify({"hata":"Dosya yok"}),400
        fname = f"lisans_{lid}_{f.filename.replace(' ','_')}"
        f.save(_os.path.join(KALITE_UPLOAD_DIR, fname))
        run_exec(f"UPDATE kalite_lisans SET belge_yolu={q(fname)} WHERE id={lid}")
        return jsonify({"ok":True,"belge_yolu":fname})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

# ═══════════════════════════════════════════════════════════
# HATIRLATMA / GÖREV SİSTEMİ
# ═══════════════════════════════════════════════════════════

def init_hatirlatma_tables():
    sqls = [
        """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='hatirlatma_gorev' AND xtype='U')
CREATE TABLE hatirlatma_gorev (
  id                INT IDENTITY(1,1) PRIMARY KEY,
  baslik            NVARCHAR(500) NOT NULL,
  aciklama          NVARCHAR(MAX),
  kategori          NVARCHAR(50) NOT NULL DEFAULT 'genel',
  oncelik           NVARCHAR(20) NOT NULL DEFAULT 'normal',
  atayan            NVARCHAR(100) NOT NULL,
  atanan            NVARCHAR(100) NOT NULL,
  durum             NVARCHAR(30) NOT NULL DEFAULT 'bekliyor',
  deadline          DATETIME,
  hatirlatma_baslangic NVARCHAR(50) NOT NULL DEFAULT 'hemen',
  hatirlatma_siklik NVARCHAR(50) NOT NULL DEFAULT '4_saat',
  max_hatirlatma    INT NOT NULL DEFAULT 10,
  hatirlatma_sayac  INT NOT NULL DEFAULT 0,
  mail_gonder       BIT NOT NULL DEFAULT 1,
  olusturma_tar     DATETIME NOT NULL DEFAULT GETDATE(),
  guncelleme_tar    DATETIME NOT NULL DEFAULT GETDATE()
)""",
        """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='hatirlatma_yanit' AND xtype='U')
CREATE TABLE hatirlatma_yanit (
  id           INT IDENTITY(1,1) PRIMARY KEY,
  gorev_id     INT NOT NULL,
  yazan        NVARCHAR(100) NOT NULL,
  mesaj        NVARCHAR(MAX) NOT NULL,
  olusturma_tar DATETIME NOT NULL DEFAULT GETDATE()
)""",
        """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='hatirlatma_log' AND xtype='U')
CREATE TABLE hatirlatma_log (
  id           INT IDENTITY(1,1) PRIMARY KEY,
  gorev_id     INT NOT NULL,
  log_tipi     NVARCHAR(50) NOT NULL DEFAULT 'mail',
  durum        NVARCHAR(30) NOT NULL DEFAULT 'gonderildi',
  detay        NVARCHAR(MAX),
  olusturma_tar DATETIME NOT NULL DEFAULT GETDATE()
)""",
    ]
    for sql in sqls:
        try: run_exec(sql)
        except Exception as e: print(f"hatirlatma tablo: {e}")

@app.route("/api/gorev/listesi", methods=["GET"])
@giris_gerekli
def hatirlatma_gorev_listesi():
    try:
        kullanici = session.get('kullanici','')
        rol = session.get('rol','')
        if rol == 'admin':
            filtre = ""
        else:
            filtre = f"WHERE atayan={q(kullanici)} OR atanan={q(kullanici)}"
        rows = qry(f"""SELECT id,baslik,aciklama,kategori,oncelik,atayan,atanan,durum,
            CONVERT(varchar,deadline,20) AS deadline,
            hatirlatma_siklik,max_hatirlatma,hatirlatma_sayac,mail_gonder,
            CONVERT(varchar,olusturma_tar,20) AS olusturma_tar,
            DATEDIFF(hour,GETDATE(),deadline) AS kalan_saat
            FROM hatirlatma_gorev {filtre}
            ORDER BY CASE oncelik WHEN 'acil' THEN 1 WHEN 'normal' THEN 2 ELSE 3 END,
            CASE durum WHEN 'bekliyor' THEN 1 WHEN 'devam' THEN 2 ELSE 3 END,
            deadline""")
        # Yanıt sayısını ekle
        for r in rows:
            cnt = qry(f"SELECT COUNT(*) AS cnt FROM hatirlatma_yanit WHERE gorev_id={r['id']}")
            r['yanit_sayisi'] = cnt[0]['cnt'] if cnt else 0
        return jsonify(rows)
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/gorev/ekle", methods=["POST"])
@giris_gerekli
def hatirlatma_gorev_ekle():
    try:
        d = request.get_json() or {}
        kullanici = session.get('kullanici','sistem')
        dl = d.get('deadline')
        run_exec(f"""INSERT INTO hatirlatma_gorev
            (baslik,aciklama,kategori,oncelik,atayan,atanan,
             deadline,hatirlatma_baslangic,hatirlatma_siklik,max_hatirlatma,mail_gonder)
            VALUES (
            {q(d.get('baslik',''))},{q(d.get('aciklama',''))},
            {q(d.get('kategori','genel'))},{q(d.get('oncelik','normal'))},
            {q(kullanici)},{q(d.get('atanan',''))},
            {'CAST('+q(dl)+' AS DATETIME)' if dl else 'NULL'},
            {q(d.get('hatirlatma_baslangic','hemen'))},
            {q(d.get('hatirlatma_siklik','4_saat'))},
            {d.get('max_hatirlatma',10)},
            {1 if d.get('mail_gonder',True) else 0})""")
        rows = qry("SELECT TOP 1 id FROM hatirlatma_gorev ORDER BY id DESC")
        new_id = rows[0]['id'] if rows else None
        # Log
        run_exec(f"""INSERT INTO hatirlatma_log (gorev_id,log_tipi,durum,detay)
            VALUES ({new_id},'olusturma','tamamlandi','Gorev olusturuldu: {q(d.get("baslik",""))[1:-1]}')""")
        return jsonify({"ok":True,"id":new_id})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/gorev/<int:gid>", methods=["PATCH"])
@giris_gerekli
def hatirlatma_gorev_guncelle(gid):
    try:
        d = request.get_json() or {}
        parts = []
        for f in ('baslik','aciklama','kategori','oncelik','atanan','durum',
                  'hatirlatma_siklik','hatirlatma_baslangic'):
            if f in d: parts.append(f"{f}={q(d[f])}")
        for f in ('max_hatirlatma','hatirlatma_sayac'):
            if f in d and d[f] is not None: parts.append(f"{f}={d[f]}")
        if 'mail_gonder' in d:
            parts.append(f"mail_gonder={1 if d['mail_gonder'] else 0}")
        if 'deadline' in d and d['deadline']:
            parts.append(f"deadline=CAST({q(d['deadline'])} AS DATETIME)")
        if not parts:
            return jsonify({"hata":"Alan yok"}),400
        parts.append("guncelleme_tar=GETDATE()")
        run_exec(f"UPDATE hatirlatma_gorev SET {','.join(parts)} WHERE id={gid}")
        # Durum değiştiyse logla
        if 'durum' in d:
            run_exec(f"""INSERT INTO hatirlatma_log (gorev_id,log_tipi,durum,detay)
                VALUES ({gid},'durum_degisim','tamamlandi','Durum: {d["durum"]}')""")
        return jsonify({"ok":True})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/gorev/<int:gid>/yanit", methods=["GET"])
@giris_gerekli
def hatirlatma_yanit_listesi(gid):
    try:
        rows = qry(f"""SELECT id,yazan,mesaj,
            CONVERT(varchar,olusturma_tar,20) AS olusturma_tar
            FROM hatirlatma_yanit WHERE gorev_id={gid} ORDER BY olusturma_tar""")
        return jsonify(rows)
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/gorev/<int:gid>/yanit", methods=["POST"])
@giris_gerekli
def hatirlatma_yanit_ekle(gid):
    try:
        d = request.get_json() or {}
        kullanici = session.get('kullanici','sistem')
        run_exec(f"""INSERT INTO hatirlatma_yanit (gorev_id,yazan,mesaj)
            VALUES ({gid},{q(kullanici)},{q(d.get('mesaj',''))})""")
        return jsonify({"ok":True})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

@app.route("/api/gorev/<int:gid>/log", methods=["GET"])
@giris_gerekli
def hatirlatma_log_listesi(gid):
    try:
        rows = qry(f"""SELECT id,log_tipi,durum,detay,
            CONVERT(varchar,olusturma_tar,20) AS olusturma_tar
            FROM hatirlatma_log WHERE gorev_id={gid} ORDER BY olusturma_tar DESC""")
        return jsonify(rows)
    except Exception as e:
        return jsonify({"hata":str(e)}),500

# Bekleyen hatırlatmaları kontrol et (arka plan görevi olarak çağrılır)
@app.route("/api/gorev/hatirlatma_kontrol", methods=["POST"])
@giris_gerekli
def hatirlatma_kontrol():
    """Zamanı gelen hatırlatmaları işle - her 30dk cron olarak çağrılabilir"""
    try:
        bekleyenler = qry("""
            SELECT id,baslik,atanan,hatirlatma_sayac,max_hatirlatma,
                   hatirlatma_siklik,deadline,mail_gonder,
                   CONVERT(varchar,olusturma_tar,20) AS olusturma_tar
            FROM hatirlatma_gorev
            WHERE durum IN ('bekliyor','devam')
            AND (max_hatirlatma=0 OR hatirlatma_sayac < max_hatirlatma)
            AND deadline IS NOT NULL
            AND deadline > GETDATE()
        """)
        gonderilen = 0
        for g in bekleyenler:
            # Basit sıklık kontrolü - şimdilik sadece sayacı artır
            run_exec(f"""UPDATE hatirlatma_gorev SET hatirlatma_sayac=hatirlatma_sayac+1,
                guncelleme_tar=GETDATE() WHERE id={g['id']}""")
            run_exec(f"""INSERT INTO hatirlatma_log (gorev_id,log_tipi,durum,detay)
                VALUES ({g['id']},'hatirlatma','gonderildi',
                'Hatirlatma #{g["hatirlatma_sayac"]+1}: {g["baslik"][:50]}')""")
            gonderilen += 1
        return jsonify({"ok":True,"gonderilen":gonderilen})
    except Exception as e:
        return jsonify({"hata":str(e)}),500

if __name__=="__main__":
    init_grafik_table()
    init_numune_table()
    init_grafik_dosya_table()
    init_kalite_tables()
    init_hatirlatma_tables()
    init_satinalma_tables()
    # Upload klasörlerini oluştur
    for d in [UPLOAD_DIR, KALITE_UPLOAD_DIR]:
        if not _os.path.exists(d):
            try: _os.makedirs(d)
            except: pass

    # Arkaplan hatırlatma zamanlayıcısını başlat
    def gorev_hatirlatma_kontrol():
        """Her gün 08:00'de çalışır, yaklaşan görevler için mail atar"""
        while True:
            try:
                simdi = datetime.now()
                hedef = simdi.replace(hour=8, minute=0, second=0, microsecond=0)
                if simdi >= hedef:
                    hedef += timedelta(days=1)
                bekle = (hedef - simdi).total_seconds()
                time.sleep(bekle)

                # Aktif görevleri çek
                gorevler, _ = run_query(
                    """SELECT g.id, g.gorev_tipi, g.atanan, g.beklenen_tar, g.aciklama
                       FROM planlama_gorev g
                       WHERE g.durum NOT IN ('tamamlandi','iptal')
                         AND g.beklenen_tar IS NOT NULL
                         AND g.atanan IS NOT NULL AND g.atanan <> ''""",
                    server=SERVER, database=DATABASE, uid=UID, pwd=PWD
                )
                if not gorevler:
                    continue

                bugun = date.today()
                for g in gorevler:
                    try:
                        tar = datetime.strptime(g['beklenen_tar'][:10], '%Y-%m-%d').date()
                        kalan = (tar - bugun).days
                        if kalan not in (1, 2, 3, 0, -1):
                            continue
                        atanan_mail = KULLANICILAR.get(g['atanan'], {}).get('mail', '')
                        alicilar = list(set(filter(None, [atanan_mail, GOREV_MAIL_ALICILAR])))
                        if not alicilar:
                            continue
                        if kalan > 0:
                            konu = f"⏰ {kalan} gün kaldı: {g['gorev_tipi']}"
                            renk = '#d97706' if kalan <= 1 else '#1e3a8a'
                            durum_mesaj = f"Son tarihe <strong>{kalan} gün</strong> kaldı."
                        elif kalan == 0:
                            konu = f"🔔 Bugün son gün: {g['gorev_tipi']}"
                            renk = '#dc2626'
                            durum_mesaj = "Bu görevin <strong>son günü bugün!</strong>"
                        else:
                            konu = f"❗ Gecikmiş görev ({abs(kalan)} gün): {g['gorev_tipi']}"
                            renk = '#dc2626'
                            durum_mesaj = f"Bu görev <strong>{abs(kalan)} gün gecikmiş!</strong>"

                        import smtplib
                        from email.mime.text import MIMEText
                        from email.mime.multipart import MIMEMultipart
                        msg = MIMEMultipart('alternative')
                        msg['Subject'] = konu
                        msg['From'] = SMTP_FROM
                        msg['To'] = ', '.join(alicilar)
                        html = f"""
                        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
                          <div style="background:{renk};color:#fff;padding:20px;border-radius:8px 8px 0 0;">
                            <h2 style="margin:0;">📋 Görev Hatırlatması</h2>
                          </div>
                          <div style="background:#fff;border:1px solid #e2e6ec;padding:20px;border-radius:0 0 8px 8px;">
                            <p style="font-size:14px;margin-bottom:16px;">{durum_mesaj}</p>
                            <table style="width:100%;border-collapse:collapse;">
                              <tr style="background:#f6f8fb;"><td style="padding:8px;font-weight:bold;color:#6b7280;width:120px;">Görev</td><td style="padding:8px;font-weight:700;">{g['gorev_tipi']}</td></tr>
                              <tr><td style="padding:8px;font-weight:bold;color:#6b7280;">Atanan</td><td style="padding:8px;">{g['atanan']}</td></tr>
                              <tr style="background:#f6f8fb;"><td style="padding:8px;font-weight:bold;color:#6b7280;">Son Tarih</td><td style="padding:8px;color:{renk};font-weight:700;">{g['beklenen_tar'][:10]}</td></tr>
                              {f'<tr><td style="padding:8px;font-weight:bold;color:#6b7280;">Açıklama</td><td style="padding:8px;">{g["aciklama"]}</td></tr>' if g.get('aciklama') else ''}
                            </table>
                            <div style="margin-top:16px;text-align:center;">
                              <a href="http://192.168.1.16:5057" style="background:{renk};color:#fff;padding:10px 24px;border-radius:6px;text-decoration:none;font-weight:bold;">Sisteme Git →</a>
                            </div>
                          </div>
                        </div>"""
                        msg.attach(MIMEText(html, 'html', 'utf-8'))
                        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as srv:
                            srv.starttls()
                            srv.login(SMTP_USER, SMTP_PASS)
                            srv.sendmail(SMTP_FROM, alicilar, msg.as_string())
                        print(f"Hatırlatma maili gönderildi: {g['gorev_tipi']} -> {alicilar} ({kalan} gün)")
                    except Exception as ge:
                        print(f"Görev {g.get('id')} hatırlatma hatası: {ge}")
            except Exception as e:
                print(f"Hatırlatma döngüsü hatası: {e}")
                time.sleep(3600)  # Hata olursa 1 saat bekle

    t = threading.Thread(target=gorev_hatirlatma_kontrol, daemon=True)
    t.start()
    print("✅ Görev hatırlatma sistemi başlatıldı (her gün 08:00)")

    print("Solariz Planlama Sunucusu -> http://192.168.1.16:5057")
    app.run(host="0.0.0.0",port=5057,debug=False)
