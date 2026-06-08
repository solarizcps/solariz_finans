# KREDİ MODÜLÜ ANALİZİ — BANKA + TAKSİT DÜZELTME

> **Tarih:** 5 Haziran 2026  
> **Mevcut Stable:** `D:\finans_BACKUP_STABLE_CEK_BANKA_CEKNO_20260605`  
> **DB:** Dokunulmadı (analiz) | **CPS:** Dokunulmadı

---

## 1. DB Yapısı

### Ayrı Taksit Tablosu

**YOK.** Tüm tablolar:
```
kasa (1), krediler (26), kullanicilar (2), kur_cache (3),
odemeler (715), planlama (454)
```

Taksitler `odemeler` tablosunda `tip='taksit'` ile tutuluyor.

---

### `krediler` Tablosu (26 kayıt)

| # | Kolon | Tip | Doluluk |
|---|-------|-----|---------|
| 0 | `id` | TEXT | — |
| 1 | `entity` | TEXT | — |
| 2 | `ad` | TEXT | Kredi adı |
| 3 | `tip` | TEXT | — |
| 4 | `toplam` | REAL | Toplam tutar |
| 5 | `taksit` | REAL | Planlanan taksit tutarı |
| 6 | `kalan_taksit` | INTEGER | Kalan taksit sayısı |
| 7 | `gun` | TEXT | Taksit günü |
| 8 | `faiz` | TEXT | Faiz oranı |
| **9** | **`banka`** | **TEXT** | **✅ VAR — 25/26 dolu** |
| 10 | `baslangic` | TEXT | Başlangıç tarihi |
| 11 | `not_` | TEXT | Not |
| ... | ... | ... | ... |

**`banka` kolonu `krediler` tablosunda mevcut ve çoğunlukla dolu.**

---

### `odemeler` Tablosunda Taksit Kayıtları

| Alan | Değer |
|------|-------|
| `tip='taksit'` kayıt sayısı | 197 |
| Bekleyen taksit | 66 |
| Gecikmiş taksit | 2+ |
| `banka` kolonu (yeni eklendi) | **0 / 197 dolu** |
| `not_` kolonu | **197 / 197 dolu** |
| `not_` içeriği | **Banka adı** (Finansbank, Kuveytturk, Denizbank...) |

**Kritik Bulgu:** Taksit kayıtlarında `banka` kolonu boş, ama `not_` alanında banka adı yazılı. Bu importtan kalan bir yapı — veritabanı tasarımında `banka` `odemeler`'e (çek özelliği için) sonradan eklendiğinden taksitler `not_` kullanmış.

**Örnek:**
```
aciklama = 'İga Kredi 5.Taksit'  |  not_ = 'Finansbank'  |  banka = NULL
aciklama = 'Işık 5.Taksit'       |  not_ = 'Kuveytturk'  |  banka = NULL
```

---

### Kredi-Taksit Eşleşme Mekanizması

Frontend `eslestir()` fonksiyonu ile eşleşiyor:
```javascript
function eslestir(kredi, odeme, tumKrediler) {
  if (odeme.tip !== 'taksit') return false;
  var oAc = odeme.aciklama.toLowerCase().trim();
  var kAd = kredi.ad.toLowerCase().trim();
  return oAc.indexOf(kAd + ' ') === 0;  // prefix eşleşme
}
```

Örnek: Kredi adı `"İga Kredi"` → taksit `aciklama = "İga Kredi 5.Taksit"` → eşleşir.

**Risk:** Ad prefix eşleşmesi — kredi adı değişirse taksitler kopabilir.

---

## 2. Backend API Durumu

| Endpoint | Method | Durum |
|----------|--------|-------|
| `GET /api/krediler` | GET | ✅ Var |
| `POST /api/krediler` | POST | ✅ Var (banka alanı dahil) |
| `PUT /api/krediler/<id>` | PUT | ✅ Var (banka alanı dahil) |
| `DELETE /api/krediler/<id>` | DELETE | ✅ Var |
| **Taksit listeleme** | — | ❌ Yok (genel `/api/odemeler` kullanılıyor) |
| **Taksit güncelleme** | PUT | ⚠️ `PUT /api/odemeler/<id>` var, taksit için de çalışır |
| **Taksit ödendi** | POST | ✅ `POST /api/odemeler/<id>/odendi` var |

**Önemli:** `PUT /api/odemeler/<id>` tüm odemeler için çalışır. `vade` ve `tutar` güncellenebilir. Taksit düzenleme için **ek backend endpoint gerekmez** — mevcut çalışır.

---

## 3. Frontend Durumu

### Kredi Ekleme Modalı (`kredi-modal`)

```html
<input type="text" id="kredi-banka" placeholder="ör: Garanti Bankası">
```
**Banka alanı mevcut.** Kredi eklerken banka girilebiliyor.

### Kredi Listesi (`renderKrediler()`)

Taksit satırı mevcut HTML'i (satır 3025-3038):
```html
<td>1. Taksit</td>
<td>tarih</td>
<td>tutar</td>
<td>odeme_tarihi</td>
<td>durum</td>
<td>✓ Öde butonu</td>
<!-- ❌ DÜZENLE BUTONU YOK -->
```

**Eksikler:**
- Taksit satırında **✏ Düzenle** butonu yok
- Taksit tarih/tutar değişiklik modalı yok
- Kredi başlığında banka görünmüyor (mevcut koda bakılması gerekiyor)

### Kredi Başlığında Banka Gösterimi

`renderKrediler()` içinde kredi kartı başlığında `k.banka` gösterimi kontrol edilmeli. Analiz: banka verisi mevcut (25/26 dolu) ama başlıkta görünüp görünmediği test edilmesi gerekiyor.

---

## 4. Risk Analizi

### Taksit Tarihi Değişirse

| Alan | Etki | Risk |
|------|------|------|
| Takvim (`renderCalendar`) | `vade` bazlı — otomatik güncellenir | ✅ Düşük |
| Kredi listesi (`renderKrediler`) | `vade` bazlı sıralama — otomatik | ✅ Düşük |
| Takvim sidebar | Tarih sıralı — otomatik güncellenir | ✅ Düşük |
| KPI (gecikti hesabı) | `daysUntil(vade)` — otomatik | ✅ Düşük |

### Taksit Tutarı Değişirse

| Alan | Etki | Risk |
|------|------|-------|
| Kredi toplam/kalan hesabı | `bekleyenler.reduce(tutar)` — otomatik | ✅ Düşük |
| Özet kartlar | `toplamKalan` hesabı — otomatik | ✅ Düşük |
| Takvim KPI `kpi-taksit` | `topla(taksitler)` — otomatik | ✅ Düşük |

### Mevcut 197 Taksit Etkilenir mi?

- **FAZ K1** (sadece görünürlük/banka): Sıfır etki
- **FAZ K2** (taksit düzenleme modalı, bireysel kayıt): Sadece düzenlenen taksit etkilenir
- **FAZ K3** (audit trail): DB'ye yeni tablo — mevcut veriler etkilenmez

---

## 5. Önerilen Faz Planı

---

### FAZ K1 — Banka Görünürlüğü (Düşük Risk)

**Amaç:** Krediler listesinde hangi banka görünsün.  
**Etkilenen:** Sadece `finans_yonetim.html`

| Adım | Değişiklik |
|------|-----------|
| Kredi kart başlığına banka badge | `renderKrediler()` HTML — `k.banka` göster |
| Taksit satırına banka badge | Her taksit satırında `not_` değeri (banka adı) göster |

**DB değişikliği:** Yok  
**Backend değişikliği:** Yok  
**Not:** Taksit kayıtlarında `banka=NULL`, `not_=banka_adı` — `not_` alanı banka badge için kullanılabilir (taksit için `not_=banka`).  

---

### FAZ K2 — Taksit Satırı Düzenleme (Orta Zorluk)

**Amaç:** Her taksit satırına ✏ butonu, tıklayınca tarih/tutar/not düzenlenebilsin.  
**Etkilenen:** `finans_yonetim.html` (modal + JS)  

| Adım | Değişiklik |
|------|-----------|
| Taksit satırına ✏ Düzenle butonu | `renderKrediler()` taksit HTML |
| `taksit-duzenle-modal` HTML | Tarih + Tutar + Açıklama alanları |
| `editTaksit(id)` fonksiyonu | Modal'ı doldur ve aç |
| `saveTaksit()` fonksiyonu | `PUT /api/odemeler/<id>` çağrısı |

**Backend değişikliği:** Yok — `PUT /api/odemeler/<id>` zaten çalışıyor  
**DB değişikliği:** Yok  
**Risk:** Düşük. Sadece bireysel taksit değişir, diğerleri etkilenmez.

Düzenlenebilecek alanlar:
- `vade` (vade tarihi) — ✅ `odemeler` tablosunda mevcut
- `tutar` (taksit tutarı) — ✅ `odemeler` tablosunda mevcut
- `not_` (açıklama/sebep) — ✅ `odemeler` tablosunda mevcut

---

### FAZ K3 — Düzeltme Geçmişi / Audit (Yüksek Zorluk)

**Amaç:** Hangi taksit ne zaman, kim tarafından, neden değiştirildi — kayıt altında olsun.  
**Etkilenen:** `finans.db` + `finans_server.py` + `finans_yonetim.html`

**Seçenek 3A — Mevcut kolonlarla (minimal):**
`guncelleyen` + `guncelleme` + `not_` alanları kullanılır. Eski değer `not_` alanına yazılır.

**Seçenek 3B — Yeni `odemeler_audit` tablosu:**
```sql
CREATE TABLE odemeler_audit (
  id         TEXT,
  odeme_id   TEXT,
  alan       TEXT,   -- 'vade' veya 'tutar'
  eski_deger TEXT,
  yeni_deger TEXT,
  sebep      TEXT,
  degistiren TEXT,
  tarih      TEXT
);
```

**Öneri:** Önce FAZ K1 ve K2 uygulanır, K3 ihtiyaç duyulunca eklenebilir.

---

## 6. Mevcut Kredi-Banka Durumu (26 Kredi)

| Banka | Kredi Sayısı |
|-------|-------------|
| Kuveytturk | ~15 |
| Kuveyt Şahin tb | 2 |
| Finansbank | 1 |
| Denizbank | 1 |
| Vakıf Katılım | 1 |
| TEB Bankası | 1 |
| Sallama bir banka | 1 |
| Boş | 1 |

---

## 7. Özet — Minimum Uygulama Maliyeti

| Faz | Etkilenen Dosya | DB | Süre Tahmini |
|-----|----------------|-----|------------|
| K1 — Banka badge | `finans_yonetim.html` | ❌ Yok | ~30 satır |
| K2 — Taksit düzenle modal | `finans_yonetim.html` | ❌ Yok | ~80 satır |
| K3A — Audit (not_ ile) | `finans_yonetim.html` | ❌ Yok | ~20 satır |
| K3B — Audit (yeni tablo) | 3 dosya | ✅ Yeni tablo | Büyük |

**Önerim:** K1 + K2 tek seferde, K3A ile basit audit. K3B sonraya bırakılabilir.

---

*Analiz: `D:\finans\reports\KREDI_BANKA_TAKSIT_DUZELTME_ANALIZ.md` — Kod/DB değişikliği için onay bekliyor.*
