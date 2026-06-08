# FİNANS BAĞIMSIZ DÜZELTME PLANI

> **Tarih:** 5 Haziran 2026  
> **Kapsam:** Yalnızca `D:\finans` — bağımsız sistem  
> **Karar:** CPS'e entegrasyon YOK. Finans kendi içinde geliştirilecek.  
> **Yedek:** `D:\finans_BACKUP_BEFORE_RUN_20260605_1224` (14 dosya)

---

## SİSTEM NASIL AÇILDI

### Ortam Kontrol Sonuçları

| Bileşen | Durum | Detay |
|---------|-------|-------|
| Python | ✅ 3.14.4 | Yüklü |
| Flask | ✅ 3.1.3 | Yüklü |
| Werkzeug | ✅ 3.1.8 | Yüklü |
| **flask-cors** | ⚠️ Eksikti | Bu oturum kuruldu: `pip install flask-cors` |
| **pandas** | ⚠️ Eksikti | Bu oturum kuruldu: `pip install pandas` (3.0.3) |
| openpyxl | ✅ 3.1.5 | Yüklü |
| xlrd | ✅ 2.0.2 | Yüklü |

> **Not:** `flask-cors` ve `pandas` başlangıçta eksikti. Sunucu flask-cors olmadan `from flask_cors import CORS` hatasıyla başlatılamazdı. Her ikisi de bu oturumda kuruldu.

### Başlatma

```
cd D:\finans
python finans_server.py
```

**Başarılı.** Sunucu log:
```
[DB] Veritabanı hazır: D:\finans\finans.db
 * Running on http://127.0.0.1:5058
 * Running on http://192.168.110.186:5058
```

---

## PORT

| Adres | Durum |
|-------|-------|
| `http://127.0.0.1:5058` | ✅ Aktif |
| `http://192.168.110.186:5058` | ✅ Aktif (ağ) |
| `http://192.168.1.16:5058` | ⚠️ KURULUM.txt'deki eski IP — Bu makine farklı IP'de |

> **Not:** `KURULUM.txt` ve `finans_yonetim.html` içinde `API_BASE = 'http://192.168.1.16:5058'` yazıyor. Bu IP mevcut makineye ait değil (`192.168.110.186`). Ağdaki diğer cihazlardan erişim için bu adres güncellenmelidir.

---

## ÇALIŞAN EKRANLAR VE API'LER

### API Smoke Test Sonuçları

| Endpoint | HTTP | Durum | Notlar |
|----------|------|-------|--------|
| `GET /` | 200 | ✅ Çalışıyor | 175.043 byte HTML, SPA kodu tam |
| `POST /api/login` | 200 | ✅ Çalışıyor | altan/104099 → `{"ok":true}` |
| `GET /api/odemeler` | 200 | ✅ Çalışıyor | 715 kayıt dönüyor |
| `GET /api/krediler` | 200 | ✅ Çalışıyor | 27 kredi dönüyor |
| `GET /api/planlama` | 200 | ✅ Çalışıyor | 454 kayıt dönüyor |
| `GET /api/kasa` | 200 | ✅ Çalışıyor | 0 kayıt (tablo boş) |
| `GET /api/kurlar` | 200 | ✅ Çalışıyor | USD=45.97, EUR=53.42, XAU=0.0 |
| `GET /api/ozet` (entity yok) | **500** | ❌ SQL HATASI | Bkz. §ÇALIŞMAYAN |
| `GET /api/ozet?entity=solariz` | 200 | ✅ Çalışıyor | Entity parametresiyle çalışıyor |

### Sekme Durumları (finans_yonetim.html)

| Sekme | API Kaynağı | Durum | Veri Var mı? |
|-------|------------|-------|-------------|
| Özet | `/api/ozet?entity=...` | ✅ Çalışır (entity ile) | 13 bekleyen, 49 gecikmiş |
| Ödemeler | `/api/odemeler` | ✅ Çalışıyor | 715 kayıt |
| Krediler | `/api/krediler` | ✅ Çalışıyor | 27 kredi |
| Çekler | `/api/odemeler` (filtrelenir) | ✅ Çalışıyor | 41 çek (`Çek:` prefix'li) |
| Kasa | `/api/kasa` + `/api/kurlar` | ⚠️ Açılır | Kasa: 0 kayıt — bakiye görünmez |
| Takvim | `/api/odemeler` | ✅ Çalışıyor | Vade bazlı gösterim |
| Nakit Akışı | `/api/odemeler` + bellek | ⚠️ Açılır | Hardcoded bakiye, gelir yok |
| 12 Ay Planlama | `/api/planlama` | ✅ Çalışıyor | 454 kayıt |

---

## VERİ DURUMU (5 Haziran 2026)

| Tablo | Kayıt | Özet |
|-------|-------|------|
| `odemeler` | 715 | taksit:197, tedarikci:211, kredi:119, maas:18, diger:150, vergi:20 |
| `krediler` | 27 | Kuveytturk, Finansbank, Denizbank, TEB, Vakıf Katılım vb. |
| `planlama` | 454 | gelir:36 (40.8M TL), kredi:85, diger:241 |
| `kasa` | **0** | Tablo var, kayıt **yok** |
| `kur_cache` | 3 | USD:45.97, EUR:53.42, XAU:0.0 |

**Özet KPI (entity=solariz):**
- Bu ay bekleyen ödemeler: 13 adet / 3.389.023 TL
- Gecikmiş ödemeler: 49 adet / 21.139.278 TL
- Kasa bakiyesi: **0 TL** (kayıt yok)
- Toplam kredi: 55.271.979 TL

---

## ÇALIŞMAYAN / SORUNLU EKRANLAR

### 1. /api/ozet — SQL Syntax Hatası (500)

**Konum:** `finans_server.py` satır 455–480

**Sorun:**
```python
where = "WHERE entity=?" if entity else ""   # entity boşsa where = ""
base  = f"FROM odemeler {where}"
# SQL üretilen: "SELECT COUNT(*) FROM odemeler  AND durum='bekliyor'..."
# WHERE olmadan AND → sqlite3.OperationalError: near "AND": syntax error
```

**Etki:** Özet sekmesi, ilk yüklenirken `entity` parametresi göndermeden `/api/ozet` çağırıyorsa 500 hatası alır. Entity seçildikten sonra çalışıyor.

**Çözüm (yapılacak):** `base = f"FROM odemeler WHERE 1=1 {('AND entity=?' if entity else '')}"` şeklinde güncellenmeli.

---

### 2. Kasa Tablosu Boş → Nakit Akışı Yanlış

**Konum:** `finans_yonetim.html` satır 3180

**Sorun:**
```javascript
var baslangicBakiye = 2500000; // TODO: gerçek kasa bakiyesi
```

**Etki:** Nakit akışı ekranı her zaman 2.500.000 TL bakiye ile başlar. Gerçek nakit durumu yansıtılmaz.

**Ek sorun:** `kasa` tablosu tamamen boş (0 kayıt). Kasa sekmesinde bakiye görünmez.

---

### 3. Nakit Akışı Gelir Kaynakları Bağlı Değil

**Sorun:** `planlama.kategori='gelir'` tablosunda **36 kayıt / 40.8M TL** tahsilat verisi var. Bu veri nakit akışı hesabında kullanılmıyor. Nakit akışı yalnızca kullanıcının manuel eklediği `_cfGelirler` bellek dizisine bakıyor (sayfa yenilenince sıfırlanıyor).

---

### 4. XAU (Altın) Kuru = 0

**Konum:** `/api/kurlar` → `{"XAU":0.0}`

**Sorun:** TCMB XML'inde altın kuru farklı biçimde bulunuyor olabilir; parse edilemiyor. Kasa sekmesinde TL/USD/EUR gösterilirken altın 0 görünür.

---

### 5. API_BASE IP Adresi Güncel Değil

**Konum:** `finans_yonetim.html` içinde `var API_BASE = 'http://192.168.1.16:5058'`

**Sorun:** Bu makine `192.168.110.186` IP'sinde çalışıyor. Ağdaki başka cihazdan erişilmek istenirse 192.168.1.16 adresi cevap vermez.

---

## İLK DÜZELTİLECEK 5 KONU (Öncelik Sırası)

### 1. `/api/ozet` SQL Hatası — Kritik Bug

**Dosya:** `finans_server.py` satır ~466  
**Değişiklik:** `WHERE 1=1` base pattern  
**Risk:** Düşük — tek satır değişiklik, SQL standardına uygun  
**Etki:** Özet sekmesi entity filtresi olmadan da çalışacak

---

### 2. Kasa Tablosuna Başlangıç Bakiyesi Girişi

**Durum:** Kasa tablosu boş → nakit akışı ve kasa sekmesi işlevsiz  
**Yapılacak:**
1. Kasa sekmesinde mevcut nakit bakiyesini manuel girebilmek
2. `finans_server.py` `init_db()` ya da kasa endpoint'inde `tip='bakiye'` desteği
3. `renderNakit()` → `baslangicBakiye` kasa API'den okunacak  
**Önce:** Gerçek başlangıç TL bakiyesini öğren, `kasa` tablosuna gir

---

### 3. Nakit Akışına Planlama Gelirleri Bağla

**Durum:** 40.8M TL gelir `planlama` tablosunda bekliyor ama nakit akışına yansımıyor  
**Yapılacak:**  
`cfHesaplaAylar()` içine `planlama.kategori='gelir'` verileri eklenmeli  
Veya `GET /api/planlama?kategori=gelir` çağrısı nakit ekranına eklenmeli  
**Etki:** Nakit akışı gerçek tahsilat projeksiyonunu gösterecek

---

### 4. `_cfGelirler` → DB'ye Kalıcı Kayıt

**Durum:** Kullanıcı nakit akışına manuel gelir ekliyor ama sayfa yenilenince kayboluyor  
**Yapılacak:**
- `finans_server.py`: `nakit_gelirler` tablosu + `POST /api/nakit-gelir` + `GET /api/nakit-gelir`
- `finans_yonetim.html`: `cfGelirEkle()` → API'ye yaz, sayfa açılışta API'den yükle  
**Risk:** Orta — yeni tablo + 2 endpoint

---

### 5. API_BASE IP Düzeltmesi

**Dosya:** `finans_yonetim.html` satır ~20 (ilk JS bloğu)  
**Değişiklik:** `var API_BASE = 'http://192.168.110.186:5058'`  
**Risk:** Düşük — sadece string değişikliği  
**Not:** Sunucu değişirse veya farklı makinede çalışırsa tekrar güncellenecek

---

## BAĞIMSIZ ÇALIŞTIRMA NOTU

```
# Bu sistemin çalıştığı yer (CPS değil):
D:\finans\
  finans_server.py    → python finans_server.py
  finans.db           → SQLite, D:\finans klasöründe
  finans_yonetim.html → http://127.0.0.1:5058 adresinden açılır

# Yedek alındı:
D:\finans_BACKUP_BEFORE_RUN_20260605_1224\  (14 dosya)

# CPS'e dokunulmadı.
# D:\finans dışında değişiklik yapılmadı.
```

---

*Rapor güncellendi: 5 Haziran 2026 — Smoke test sonrası*
