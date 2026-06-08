# LOGIN HATASI ANALİZ RAPORU

> **Tarih:** 5 Haziran 2026  
> **Kapsam:** `D:\finans` bağımsız finans sistemi  
> **Şikayet:** "Kullanıcı adı veya şifre hatalı" + sistem donuyor  
> **CPS'e dokunulmadı.**

---

## KÖK NEDEN (Tek Cümle)

> `finans_yonetim.html` içindeki `API_BASE = 'http://192.168.1.16:5058'` değişkeni  
> **yanlış IP adresine** işaret ediyor. Sunucu bu laptopda çalışıyor (`192.168.110.186:5058`)  
> ama tüm API çağrıları eski üretim IP'si olan `192.168.1.16:5058`'e gidiyor.  
> O adres bu ağdan **erişilemiyor** (netstat: SYN_SENT, cevap yok).

---

## DETAYLI ANALİZ

### 1. Login Sistemi

**Konum:** `finans_server.py` satır ~114  

```python
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
```

- Kullanıcılar `kullanicilar` tablosunda, `finans.db` içinde
- Session yok — sunucu taraflı oturum tutulmuyor; sadece JSON yanıtı dönüyor
- Frontend `sessionStorage`'a kullanıcı bilgisini kaydediyor
- Şifre karşılaştırması: **düz metin** (hash yok)

---

### 2. Geçerli Kullanıcılar

| Kullanıcı Adı | Ad | Rol | Şifre Tipi | Durum |
|---------------|----|-----|-----------|-------|
| `altan` | Altan | admin | Düz metin (6 karakter) | Aktif |
| `adem` | Adem | admin | Düz metin (8 karakter) | Aktif |

> **Not:** Şifreler açıklanmamıştır. Uzunluk ve format bilgisi verilmiştir.  
> Her iki şifre de düz metin (plaintext) olarak `kullanicilar` tablosunda tutulmaktadır.  
> `altan` şifresi yalnızca rakamlardan oluşuyor (6 haneli).

---

### 3. Donma Sebebi — Tam Akış

```
SAYFA AÇILIŞI:
  Browser → http://192.168.110.186:5058/
  Flask   → finans_yonetim.html gönderir ✅

INIT BLOĞU (sayfa yüklenince JS çalışır):
  localStorage.removeItem('finans_session')     → temizle
  var session = getSession()                    → sessionStorage'dan oku
  session yoksa → showLogin()                   → login ekranı göster ✅

KULLANICI GİRİŞ DENER:
  doLogin() çağrılır
  apiPost('/api/login', {username:'altan', password:'...'})
       ↓
  XMLHttpRequest.open('POST', 'http://192.168.1.16:5058/api/login', false)
                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                  YANLIŞ IP — bu laptopun IP'si DEĞİL

  false = SENKRON (blocking) XHR
       ↓
  TCP bağlantısı açılmaya çalışılır: 192.168.1.16:5058
  netstat: SYN_SENT — SYN paketi gönderildi, SYN-ACK GELMEDİ
       ↓
  TARAYICI DONUYOR (synchronous XHR timeout bekliyor ~20-120 saniye)
       ↓
  Timeout dolunca: xhr.status !== 200 → res = null
       ↓
  res.ok yok → "Kullanıcı adı veya şifre hatalı" gösteriliyor ❌
       ↓
  Hata mesajı GÖRÜNÜR — ama donma burada BİTİYOR
  (Kullanıcı önce donmayı yaşıyor, sonra mesajı görüyor)
```

**Kullanıcının algısı:** "Hata mesajı geldi, sistem dondu" — aslında: "Sistem dondu (timeout bekledi), sonra hata mesajı geldi."

---

### 4. Neden 192.168.1.16 Yazıyor?

`KURULUM.txt` ve `finans_yonetim.html` orijinal kurulumu `SolarizDB` sunucusu (`192.168.1.16`) üzerinde çalışmak üzere yapılandırılmış. Bu laptop farklı bir IP adresinde çalışıyor: `192.168.110.186`.

```
KURULUM.txt (orijinal tasarım):
  Sunucu: 192.168.1.16 (SolarizDB)
  Erişim: http://192.168.1.16:5058

Bu laptop:
  IP: 192.168.110.186
  Sunucu: 192.168.110.186:5058 (D:\finans\finans_server.py)
  API_BASE: http://192.168.1.16:5058  ← HATALI
```

---

### 5. Sunucu Log Kanıtı

```
netstat çıktısı:
  TCP  192.168.110.186:59605  192.168.1.16:5058  SYN_SENT  (cevap yok)
  TCP  192.168.110.186:62273  192.168.1.16:5058  SYN_SENT  (cevap yok)

Yorum: Bu laptop 192.168.1.16:5058'e bağlanmaya çalışıyor,
       TCP el sıkışması tamamlanamıyor → blokaj/donma.
```

---

### 6. İkincil Sorunlar (Login Sonrası)

Login başarılı olsa bile (yanlış IP erişilebilir olsa) şu sorunlar olurdu:

| Sıra | Fonksiyon | Sorun |
|------|-----------|-------|
| 1 | `reloadCache()` | `apiGet('/api/odemeler')` → 192.168.1.16 → farklı DB |
| 2 | `reloadCache()` | `apiGet('/api/krediler')` → 192.168.1.16 → senkron, donucu |
| 3 | `reloadCache()` | `apiGet('/api/planlama')` → 192.168.1.16 → senkron, donucu |
| 4 | Tüm CRUD | PUT/DELETE/POST → 192.168.1.16 → bu laptopun DB'sine yazmaz |
| 5 | INIT | Sayfa her yenilenişte `reloadCache()` → 192.168.1.16 → donma |

---

## ÖNERİLEN ÇÖZÜM

### Tek Değişiklik (1 Satır)

**Dosya:** `finans_yonetim.html`  
**Satır:** 1515  
**Mevcut:**
```javascript
var API_BASE = 'http://192.168.1.16:5058';
```

**Önerilen (En Güvenli — Relative URL):**
```javascript
var API_BASE = '';
```

**Neden `''` (boş string)?**
- Relative URL kullanır: `/api/login`, `/api/odemeler` vb.
- HTML hangi IP/hostname üzerinden açılırsa, API de aynı sunucuya gider
- IP değişse bile düzeltme gerekmez
- Başka bir makineden erişse bile çalışır

**Alternatif (Bu laptop için sabit):**
```javascript
var API_BASE = 'http://192.168.110.186:5058';
```
> Bu laptop IP değişirse tekrar düzeltmek gerekir — önerilmez.

---

## ONAY BEKLENİYOR

Kod değişikliği yapılmadı. Yukarıdaki çözüm için onayınızı bekliyorum.

Yapılacak tek işlem:
1. `finans_yonetim.html` satır 1515 güncellenmesi
2. Sunucuyu yeniden başlatmaya gerek yok (HTML statik dosya)
3. Tarayıcıda sayfayı yenilemek yeterli

---

*Rapor: `D:\finans\reports\LOGIN_HATASI_ANALIZ.md`*
