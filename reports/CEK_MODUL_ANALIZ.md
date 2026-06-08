# ÇEK MODÜL ANALİZİ

> **Tarih:** 5 Haziran 2026  
> **Kapsam:** `D:\finans` bağımsız finans sistemi  
> **CPS:** Dokunulmadı. DB: Dokunulmadı.  

---

## 1. Çek Kayıt Yapısı

### Ayrı "çek" tablosu YOK

`finans.db` içinde tablolar:
```
kasa (0 kayıt)
krediler (27 kayıt)
kullanicilar (2 kayıt)
kur_cache (3 kayıt)
odemeler (715 kayıt)  ← çekler burada
planlama (454 kayıt)
```

Çekler ayrı bir tablo değil, `odemeler` tablosunda özel bir konvansiyonla tutuluyor.

### `odemeler` Tablo Yapısı

| # | Kolon | Tip | Zorunlu | Not |
|---|-------|-----|---------|-----|
| 0 | `id` | TEXT | — | UUID (ilk 10 karakter) |
| 1 | `entity` | TEXT | ✅ | solariz / sahsi / nexgen |
| 2 | `aciklama` | TEXT | — | Çek için `'Çek: [Firma Adı]'` |
| 3 | `tip` | TEXT | — | Çek için `'tedarikci'` |
| 4 | `tutar` | REAL | — | |
| 5 | `para` | TEXT | — | Default: TL |
| 6 | `vade` | TEXT | — | YYYY-MM-DD |
| 7 | `odeme_tarihi` | TEXT | — | Ödeme yapıldığında |
| 8 | `durum` | TEXT | — | bekliyor / odendi / gecikti |
| 9 | `tekrar` | TEXT | — | tek / aylik / 3aylik / yillik |
| 10 | `not_` | TEXT | — | Çek için `'Çek'` |
| 11 | `kaydeden` | TEXT | — | |
| 12 | `kayit_tarihi` | TEXT | — | |
| 13 | `guncelleyen` | TEXT | — | |
| 14 | `guncelleme` | TEXT | — | |

### Çek Konvansiyonu (mevcut veri standardı)

```
tip       = 'tedarikci'
aciklama  = 'Çek: [Alıcı Firma Adı]'     ← mutlaka "Çek: " prefix
not_      = 'Çek'
entity    = solariz / sahsi / nexgen
```

**Bu konvansyon dışına çıkan "çek benzeri" kayıtlar** (aciklama'da cek/CEK geçen ama filter'a yakalanmayanlar):
```
"Sahin Taban Cek odemelerimiz"   → tip=diger, prefix yok → ekranda GÖRÜNMEZ
"CEK Odemelerimiz"               → tip=tedarikci, prefix yok → ekranda GÖRÜNMEZ
"Ay Sonu Odememiz Gereken Ceklerimiz" → tip=diger → ekranda GÖRÜNMEZ
```
Bu 3 kayıt çekler listesine dahil edilmiyor.

---

## 2. Mevcut 41 Çek Kaydı Durumu

| Alan | Değer |
|------|-------|
| Toplam kayıt | 41 |
| Bekliyor | 22 |
| Ödendi | 19 |
| Gecikti | 0 |
| Entity | Tümü: `solariz` |
| Toplam tutar | 9.775.667 TL |
| Bekleyen tutar | 4.777.586 TL |
| Vade aralığı | 2025-10-30 → 2026-10-31 |

**Dikkat:** 41 çek kaydının tamamı `entity=solariz`. NexGen ve Pera için çek kaydı yok.

---

## 3. Backend API Analizi

### Mevcut endpoint'ler (`finans_server.py`)

| Endpoint | Method | Açıklama |
|----------|--------|---------|
| `GET /api/odemeler` | ✅ | Tüm ödemeler (çekler dahil) |
| `POST /api/odemeler` | ✅ | Ödeme/çek ekle (çek konvansiyonu manuel) |
| `PUT /api/odemeler/<id>` | ✅ | Ödeme/çek güncelle |
| `DELETE /api/odemeler/<id>` | ✅ | Sil |
| `POST /api/odemeler/<id>/odendi` | ✅ | Ödendi işaretle |

**Ayrı çek endpoint'i YOK.** Çekler genel `odemeler` CRUD'u üzerinden yönetiliyor.

### `POST /api/odemeler` alanları

```python
INSERT INTO odemeler
  (id, entity, aciklama, tip, tutar, para,
   vade, odeme_tarihi, durum, tekrar, not_,
   kaydeden, kayit_tarihi)
```

Çek eklemek için `tip='tedarikci'` + `aciklama='Çek: ...'` gönderilmesi gerekiyor. Backend bunu doğrulamıyor — tamamen frontend sorumluluğu.

---

## 4. Frontend Analizi (`finans_yonetim.html`)

### Çekler Sekmesi HTML'i (line 859-871)

```html
<div id="tab-cekler" class="tab-content">
  <div class="panel">
    <div class="panel-header">
      <span class="panel-title">📄 Çek Ödemeleri</span>
      <span id="cek-ozet" ...></span>
      <!-- ❌ "+ Çek Ekle" BUTONU YOK -->
    </div>
    <div id="cek-list-container">
      ...liste...
    </div>
  </div>
</div>
```

**Panel header'ında yalnızca başlık ve özet span var. "+ Çek Ekle" butonu hiç eklenmemiş.**

### `renderCekler()` Filtresi (line 1751-1753)

```javascript
var cekler = odemeler.filter(function(o) {
  return o.tip === 'tedarikci' && o.aciklama && o.aciklama.indexOf('Çek:') === 0;
});
```

Bu filtre çalışıyor — 41 kaydı doğru yakalıyor. Sıralama: `vade` artan.

### Çek Ekleme Modalı

| Modal | Durum |
|-------|-------|
| `odeme-modal` (genel ödeme) | ✅ Var — Ödemeler sekmesinde `+ Ödeme Ekle` butonu |
| `plan-odeme-modal` (planlama) | ✅ Var — Planlama sekmesinde |
| `kredi-modal` | ✅ Var — Krediler sekmesinde |
| **`cek-modal`** | ❌ **YOK** |

### Genel Ödeme Modalı İnceleme

`odeme-modal` açıldığında `tip` dropdown'unda `tedarikci` seçeneği var. Açıklama alanına manuel `Çek: [Firma]` yazılırsa teknik olarak çek kaydedilebilir — ama:

1. Kullanıcı bunu bilmek zorunda (gizli konvansiyon)
2. Çekler sekmesinden açılmıyor, sadece Ödemeler sekmesinden
3. `banka`, `cek_no` gibi çeke özel alanlar yok

---

## 5. Veri Modeli Eksiklikleri

Gerçek bir çek için olması gereken — mevcut olmayan alanlar:

| Alan | Açıklama | Mevcut mi? |
|------|---------|-----------|
| `banka` | Çeki veren banka | ❌ Yok |
| `cek_no` | Çek seri/belge numarası | ❌ Yok |
| `kesen` | Çeki düzenleyen kişi/firma | ❌ Yok (aciklama'ya gömülü) |
| `lehdar` | Çekin verildiği kişi/firma | ❌ Yok (aciklama'ya gömülü) |
| `cek_turu` | Müşteri çeki / firmaya verilen çek | ❌ Yok |
| `banka` | ✅ `krediler`'de var | ❌ `odemeler`'de yok |
| `tutar` | Tutar | ✅ Var |
| `vade` | Vade tarihi | ✅ Var |
| `durum` | bekliyor / odendi / gecikti | ✅ Var |
| `entity` | Hangi firmaya ait | ✅ Var |
| `aciklama` | Alıcı firma adı | ⚠️ Var ama ham metin |

---

## 6. Ekranda Görünen/Görünmeyen Sorunlar

| Sorun | Detay |
|-------|-------|
| ❌ **Yeni çek eklenemez** | Tab'da hiç "+" butonu yok |
| ❌ **Çek modalı yok** | `cek-modal` HTML'de tanımlanmamış |
| ⚠️ **3 çek benzeri kayıt gizli** | "CEK" içeren ama "Çek:" prefix'siz kayıtlar listede çıkmıyor |
| ⚠️ **Banka bilgisi yok** | Mevcut 41 çekte banka kaydı yok |
| ⚠️ **Çek no yok** | Mevcut 41 çekte çek numarası yok |
| ⚠️ **Sadece Solariz** | NexGen ve Pera için çek kaydı girilmemiş |
| ✅ **Liste çalışıyor** | 41 çek doğru görünüyor, vadeye göre sıralı |
| ✅ **"Öde" butonu çalışıyor** | `markPaid()` + `renderCekler()` zinciri çalışıyor |
| ✅ **Özet kartlar çalışıyor** | Toplam / Ödenecek / Ödenen / Kalan |
| ✅ **Aya göre gruplama çalışıyor** | Accordion açılıyor |

---

## 7. Minimum Düzeltme Planı (Kod için Onay Bekliyor)

### SEÇENEK A — Minimum (Mevcut modeli koru)
**Etkilenen:** Sadece `finans_yonetim.html` — Backend değişiklik yok — DB şema değişiklik yok

1. `tab-cekler` panel header'ına `+ Çek Ekle` butonu ekle
2. `cek-modal` oluştur — alanlar:
   - Firma / Alıcı adı (açıklama)
   - Tutar
   - Vade
   - Entity (solariz / nexgen / pera)
   - Durum (bekliyor varsayılan)
   - Not (banka/çek no gibi serbest)
3. Modal "Kaydet" işleminde `tip='tedarikci'` + `aciklama='Çek: [firma]'` otomatik set edilsin
4. Ekran yenileme: `_cache.loaded=false; renderCekler();`

**Risk:** Sıfır — mevcut 41 kayıt etkilenmez, DB şema değişmez.

### SEÇENEK B — Orta (DB'ye banka/çek_no ekle)
`odemeler` tablosuna `ALTER TABLE ADD COLUMN banka TEXT` ve `cek_no TEXT` ekle.

- Backend POST ve PUT endpoint'lerine bu alanlar eklenir
- Çek modalında "Banka" ve "Çek No" alanları gösterilir
- **Mevcut 41 kayıt için banka/no = NULL** (veri girilmemiş)

**Risk:** Düşük. SQLite `ALTER TABLE ADD COLUMN` geri alınabilir değil, yedek zorunlu.

### SEÇENEK C — Kapsamlı (Ayrı çekler tablosu)
`CREATE TABLE cekler (...)` ayrı tablo, kendi endpoint'leri, kendi import scripti.

**Risk:** Yüksek. Mevcut 41 kaydın migrasyon edilmesi gerekir.

---

## 8. Öneri

**Seçenek A öncelikli.** Kod değişikliği minimumdur:
- 1 buton + 1 modal = ~60 satır HTML
- Mevcut çekler bozulmaz
- Backend hiç değişmez
- DB hiç değişmez
- Banka/çek no bilgisi `not_` alanına serbest metin olarak girilir (geçici çözüm)

Seçenek B daha sonra, Seçenek A çalışır hale geldikten sonra değerlendirilebilir.

---

*Analiz: `D:\finans\reports\CEK_MODUL_ANALIZ.md` — Kod değişikliği için onay bekleniyor.*
